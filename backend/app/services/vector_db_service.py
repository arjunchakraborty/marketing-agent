"""Vector database service for storing and retrieving campaign analysis embeddings."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.schemas.semantic_models import CampaignSemantic, EmailAnalysisSemantic

from ..core.config import settings

logger = logging.getLogger(__name__)

# Default product collection name (used by ingestion when none provided)
DEFAULT_PRODUCT_COLLECTION_NAME = "UCO_Gear_Products"


def delete_collection_if_exists(collection_name: str) -> bool:
    """
    Delete a ChromaDB collection by name so it can be recreated (e.g. with cosine).
    Uses the same vector_db_path as VectorDBService. Returns True if deleted.
    """
    if not CHROMADB_AVAILABLE:
        return False
    vector_path = Path(settings.vector_db_path)
    if not vector_path.is_absolute():
        backend_dir = Path(__file__).parent.parent.parent
        vector_db_path = backend_dir / vector_path
    else:
        vector_db_path = vector_path
    client = chromadb.PersistentClient(
        path=str(vector_db_path),
        settings=ChromaSettings(anonymized_telemetry=False),
    )
    try:
        client.delete_collection(name=collection_name)
        logger.info(f"Deleted collection for replace: {collection_name}")
        return True
    except Exception:
        logger.debug(f"Collection {collection_name} not found or already deleted")
        return False


# Store the import error for better error messages
_CHROMADB_IMPORT_ERROR: Optional[Exception] = None

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMADB_AVAILABLE = True
except Exception as e:
    CHROMADB_AVAILABLE = False
    _CHROMADB_IMPORT_ERROR = e
    logger.warning(f"ChromaDB not available: {type(e).__name__}: {str(e)}. Install with: pip install chromadb")


class VectorDBService:
    """Service for managing vector embeddings in ChromaDB."""

    def __init__(self, collection_name: str = "campaign_analyses"):
        """Initialize vector database service."""
        if not CHROMADB_AVAILABLE:
            error_msg = "ChromaDB not available. Install with: pip install chromadb"
            if _CHROMADB_IMPORT_ERROR:
                error_msg += f"\nOriginal error: {type(_CHROMADB_IMPORT_ERROR).__name__}: {str(_CHROMADB_IMPORT_ERROR)}"
            raise RuntimeError(error_msg)
        
        self.collection_name = collection_name
        
        # Resolve vector_db_path relative to backend directory
        vector_path = Path(settings.vector_db_path)
        if not vector_path.is_absolute():
            # If relative, resolve from backend directory
            backend_dir = Path(__file__).parent.parent.parent
            self.vector_db_path = backend_dir / vector_path
        else:
            self.vector_db_path = vector_path
        
        self.vector_db_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.vector_db_path),
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        # Get or create collection (will check dimension compatibility when first used)
        try:
            # Try to get existing collection
            self.collection = self.client.get_collection(
                name=collection_name
            )
            logger.info(f"Found existing collection: {collection_name}")
        except Exception:
            # Collection doesn't exist, create it (use cosine for semantic text search)
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={
                    "description": "Campaign analysis embeddings",
                    "hnsw:space": "cosine",
                }
            )
            logger.info(f"Created new collection: {collection_name}")
        
        logger.info(f"Initialized vector database at {self.vector_db_path}")

    def _distance_to_similarity(self, distance: float) -> float:
        """
        Convert ChromaDB distance to a 0-1 similarity score.
        ChromaDB uses L2 by default; we now create collections with cosine.
        - Cosine: distance = 1 - cosine_similarity (approx), so similarity = 1 - distance, clamped to [0, 1].
        - L2: unbounded; use 1/(1+distance) so result is in (0, 1] and higher similarity = lower distance.
        """
        try:
            meta = getattr(self.collection, "metadata", None) or {}
            space = (meta or {}).get("hnsw:space", "l2")
        except Exception:
            space = "l2"
        if space == "cosine":
            # Cosine distance: 0 = identical, 2 = opposite. similarity = 1 - distance, clamp to [0,1]
            return max(0.0, min(1.0, 1.0 - float(distance)))
        # L2 or unknown: distance is non-negative, unbounded
        return 1.0 / (1.0 + float(distance))

    def _get_embedding_dimension(self) -> int:
        """Get the embedding dimension for the current embedding service."""
        # Create a test embedding to determine dimension
        test_text = "test dimension check"
        try:
            embedding = self.create_embedding(test_text)
            dimension = len(embedding)
            logger.debug(f"Detected embedding dimension: {dimension}")
            return dimension
        except Exception as e:
            logger.warning(f"Could not determine embedding dimension from test: {str(e)}")
            # Default dimensions based on service availability
            if settings.openai_api_key:
                return 1536  # OpenAI text-embedding-3-small
            else:
                return 768  # Ollama nomic-embed-text (default)
    
    def _ensure_collection_dimension(self):
        """Ensure collection has correct dimension, recreate if needed."""
        # Get current embedding dimension
        current_dimension = self._get_embedding_dimension()
        
        # Try to add a test embedding to check dimension compatibility
        try:
            test_embedding = [0.0] * current_dimension
            self.collection.add(
                ids=["__dimension_test__"],
                embeddings=[test_embedding],
                documents=["test"],
                metadatas=[{"__dimension_test__": True}]
            )
            # If successful, delete the test document
            self.collection.delete(ids=["__dimension_test__"])
            logger.debug(f"Collection dimension verified: {current_dimension}")
        except Exception as e:
            if "dimension" in str(e).lower():
                logger.warning(
                    f"Collection dimension mismatch detected. Recreating collection with dimension {current_dimension}..."
                )
                # Delete and recreate with correct dimension
                old_count = self.collection.count()
                self.client.delete_collection(name=self.collection_name)
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={
                        "description": "Campaign analysis embeddings",
                        "hnsw:space": "cosine",
                    }
                )
                logger.warning(f"Recreated collection (lost {old_count} documents). Please re-import data.")
            else:
                raise
    
    def _create_collection(self):
        """Create a new collection."""
        return self.client.create_collection(
            name=self.collection_name,
            metadata={
                "description": "Campaign analysis embeddings",
                "hnsw:space": "cosine",
            }
        )

    def create_embedding(self, text: str) -> List[float]:
        """
        Create embedding for text using OpenAI or Ollama.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        # Determine embedding provider based on settings
        # Use OpenAI if API key is set and default_llm_provider is "openai"
        use_openai = (
            settings.openai_api_key 
            and settings.openai_api_key.strip() 
            and settings.default_llm_provider.lower() == "openai"
        )
        
        if use_openai:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=settings.openai_api_key)
                response = client.embeddings.create(
                    model="text-embedding-3-small",
                    input=text
                )
                return response.data[0].embedding
            except Exception as e:
                logger.warning(f"OpenAI embedding failed: {str(e)}, trying Ollama fallback")
        
        # Fallback to Ollama
        try:
            import httpx
            
            # Check if Ollama is available
            try:
                health_response = httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=5.0)
                health_response.raise_for_status()
            except Exception:
                raise RuntimeError("Ollama server not available. Please start Ollama or configure OpenAI API key.")
            
            # Try different embedding models in order (use configured model first)
            # embedding_models = [settings.ollama_embedding_model, "nomic-embed-text", "nomic-embed", "all-minilm"]
            embedding_models = [settings.ollama_embedding_model]
            # Remove duplicates while preserving order
            embedding_models = list(dict.fromkeys(embedding_models))
            
            for model in embedding_models:
                try:
                    response = httpx.post(
                        f"{settings.ollama_base_url}/api/embeddings",
                        json={
                            "model": model,
                            "prompt": text
                        },
                        timeout=30.0
                    )
                    response.raise_for_status()
                    result = response.json()
                    embedding = result.get("embedding")
                    if embedding:
                        logger.debug(f"Successfully created embedding using Ollama model: {model}")
                        return embedding
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 404:
                        # Model not found, try next one
                        logger.debug(f"Model {model} not found, trying next model")
                        continue
                    else:
                        raise
                except Exception as e:
                    logger.debug(f"Failed to use model {model}: {str(e)}, trying next model")
                    continue
            
            raise RuntimeError(f"None of the embedding models ({', '.join(embedding_models)}) are available in Ollama. Please pull one: ollama pull nomic-embed-text")
            
        except RuntimeError:
            # Re-raise runtime errors (like Ollama not available)
            raise
        except Exception as e:
            error_msg = f"Failed to create embedding: {str(e)}. Please configure OpenAI API key or ensure Ollama is running with an embedding model installed."
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def add_campaign_analysis(
        self,
        campaign_id: str,
        analysis_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add campaign analysis to vector database.
        
        Args:
            campaign_id: Campaign ID (used as document ID)
            analysis_data: Analysis data to embed
            metadata: Additional metadata to store
        """
        # Ensure collection has correct dimension before adding
        self._ensure_collection_dimension()
        """
        # Create text representation of analysis for embedding
        text_parts = []
        
        # Extract key information for embedding
        if "campaign_id" in analysis_data:
            text_parts.append(f"Campaign: {analysis_data['campaign_id']}")

        
        # Add summary information if available
        if "summary" in analysis_data:
            summary = analysis_data["summary"]
            if "average_brightness" in summary:
                text_parts.append(f"Average brightness: {summary['average_brightness']}")
            if "color_palette" in summary:
                palette = summary["color_palette"]
                if isinstance(palette, list):
                    text_parts.append(f"Color palette: {', '.join([str(c) for c in palette[:5]])}")
    
        # Add campaign metadata (from CSV)
        if "campaign_name" in analysis_data:
            text_parts.append(f"Campaign: {analysis_data['campaign_name']}")
        if "subject" in analysis_data:
            text_parts.append(f"Subject: {analysis_data['subject']}")
        if "open_rate" in analysis_data:
            text_parts.append(f"Open rate: {analysis_data['open_rate']}")
        if "click_rate" in analysis_data:
            text_parts.append(f"Click rate: {analysis_data['click_rate']}")
        if "revenue" in analysis_data:
            text_parts.append(f"Revenue: ${analysis_data['revenue']}")
        
        # Add image information
        if "images" in analysis_data:
            images = analysis_data.get("images", [])
            text_parts.append(f"Total images: {len(images)}")
            
            # Process each image analysis
            all_colors = []
            brightness_values = []
            extracted_texts = []
            element_types = []
            products = []
            
            for img_data in images:
                # Handle both old format (direct image data) and new format (nested analysis)
                analysis = img_data.get("analysis", {}) if "analysis" in img_data else img_data
                
                # Extract colors
                if "dominant_colors" in analysis:
                    colors = analysis["dominant_colors"]
                    if isinstance(colors, list):
                        all_colors.extend([str(c) for c in colors[:3]])
                
                # Extract brightness
                if "brightness" in analysis:
                    brightness_values.append(analysis["brightness"])
                
                # Extract text
                if "text_content" in analysis and analysis["text_content"]:
                    text_content = analysis["text_content"]
                    if isinstance(text_content, str):
                        extracted_texts.append(text_content[:200])
                
                # Extract elements
                if "elements" in analysis and isinstance(analysis["visual_elements"], list):
                    for elem in analysis["elements"][:5]:
                        if isinstance(elem, dict) and "type" in elem:
                            element_types.append(elem["type"])
            
            if all_colors:
                unique_colors = list(set(all_colors))[:10]
                text_parts.append(f"Dominant colors: {', '.join(unique_colors)}")
            
            if brightness_values:
                avg_brightness = sum(brightness_values) / len(brightness_values)
                text_parts.append(f"Average image brightness: {avg_brightness:.1f}")
            
            if extracted_texts:
                text_parts.append(f"Extracted text: {' '.join(extracted_texts[:3])}")
            
            if element_types:
                unique_elements = list(set(element_types))[:10]
                text_parts.append(f"Visual elements: {', '.join(unique_elements)}")
        
        # Create combined text
        text = " ".join(text_parts)
        
        """

        campaign_semantic = CampaignSemantic.from_dict(analysis_data)
        text = campaign_semantic.to_semantic_text()

        print(f"Semantic text for campaign {campaign_id}: {text}")
        # Create embedding
        # embedding = self.create_embedding(text)
        embedding = self.create_embedding(text)
        
        # Prepare metadata
        doc_metadata = {
            "campaign_id": campaign_id,
            "total_images": len(analysis_data.get("images", [])),
            **(metadata or {}),
           # "products": campaign_semantic.products_promoted
        }
        
        # Store in vector database (upsert so re-upload replaces existing)
        self.collection.upsert(
            ids=[campaign_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[doc_metadata]
        )
        
        logger.info(f"Added/updated campaign analysis in vector DB: {campaign_id}")

    def get_campaign_analysis(
        self,
        campaign_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve campaign analysis from vector database.
        
        Args:
            campaign_id: Campaign ID to retrieve
            
        Returns:
            Analysis data dictionary or None if not found
        """
        try:
            results = self.collection.get(
                ids=[campaign_id],
                include=["documents", "metadatas"]
            )
            
            if results["ids"]:
                doc = results["documents"][0]
                return json.loads(doc)
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve campaign analysis: {str(e)}")
            return None

    def search_similar_campaigns(
        self,
        query_text: str,
        n_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar campaigns using semantic similarity.
        
        Args:
            query_text: Text query to search for
            n_results: Number of results to return
            
        Returns:
            List of similar campaign analyses
        """
        # Create embedding for query
        query_embedding = self.create_embedding(query_text)
        
        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        similar_campaigns = []
        for i, campaign_id in enumerate(results["ids"][0]):
            doc = results["documents"][0][i]
            metadata = results["metadatas"][0][i]
            distance = results["distances"][0][i]
            
            # Try to parse document as JSON if it's a string
            try:
                if isinstance(doc, str):
                    analysis = json.loads(doc)
                else:
                    analysis = doc
            except (json.JSONDecodeError, TypeError):
                # If parsing fails, use the document as-is
                analysis = doc
            
            similar_campaigns.append({
                "campaign_id": campaign_id,
                "analysis": analysis,
                "metadata": metadata,
                "similarity_score": self._distance_to_similarity(distance),
                "document": doc,  # Include raw document
            })
        
        return similar_campaigns
    
    def add_product_analysis(
        self,
        product_id: str,
        product_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add product analysis to vector database.
        
        Args:
            product_id: Product ID (used as document ID)
            product_data: Product data to embed
            metadata: Additional metadata to store
        """
        # Ensure collection has correct dimension before adding
        self._ensure_collection_dimension()
        
        # Create text representation of product for embedding
        text_parts = []
        
        # Extract key product information
        if "product_id" in product_data:
            text_parts.append(f"Product ID: {product_data['product_id']}")
        
        product = product_data.get("product", {})

        # Name
        if "name" in product:
            text_parts.append(f"Product: {product['name']}")
        elif "product_name" in product:
            text_parts.append(f"Product: {product['product_name']}")
        
        # Brand
        if "brand" in product:
            text_parts.append(f"Brand: {product['brand']}")
        elif "product_brand" in product:
            text_parts.append(f"Brand: {product['product_brand']}")
        
        # Category
        if "category" in product:
            text_parts.append(f"Category: {product['category']}")
        elif "product_category" in product:
            text_parts.append(f"Category: {product['product_category']}")
        
        # Description
        if "description" in product:
            text_parts.append(f"Description: {product['description']}")
        elif "product_description" in product:
            text_parts.append(f"Description: {product['product_description']}")
        
        # Price
        if "price" in product:
            text_parts.append(f"Price: {product['price']}")
        elif "product_price" in product:
            text_parts.append(f"Price: {product['product_price']}")
        
        # Sale price
        if "sale_price" in product:
            text_parts.append(f"Sale Price: {product['sale_price']}")
        elif "product_sale_price" in product:
            text_parts.append(f"Sale Price: {product['product_sale_price']}")
        
        # Hyperlink / URL
        if "hyperlink" in product:
            text_parts.append(f"URL: {product['hyperlink']}")
        elif "url" in product:
            text_parts.append(f"URL: {product['url']}")
        elif "product_url" in product:
            text_parts.append(f"URL: {product['product_url']}")
        
        # SKU (keep for backward compatibility)
        if "sku" in product:
            text_parts.append(f"SKU: {product['sku']}")
        elif "product_sku" in product:
            text_parts.append(f"SKU: {product['product_sku']}")
        
        # Add business name
        if "business_name" in product_data:
            text_parts.append(f"Business: {product_data['business_name']}")
        
        # Add stored images info
        if "stored_image_paths" in product_data:
            stored_count = len(product_data.get("stored_image_paths", []))
            if stored_count > 0:
                text_parts.append(f"Stored images: {stored_count}")
        
        # Create combined text
        text = " ".join(text_parts)
        
        # Create embedding
        embedding = self.create_embedding(text)
        
        # Prepare metadata — include all product columns for filtering/retrieval
        # ChromaDB metadata values must be str, int, float, or bool; coerce to str.
        _description = str(product.get("description") or product.get("product_description", ""))[:512]
        _url = str(product.get("url") or product.get("hyperlink") or product.get("product_url", ""))
        doc_metadata: Dict[str, Any] = {
            "product_id": product_id,
            "business_name": product_data.get("business_name", ""),
            "product_name": product.get("name") or product.get("product_name", ""),
            "brand": product.get("brand") or product.get("product_brand", ""),
            "category": product.get("category") or product.get("product_category", ""),
            "description": _description,
            "url": _url,
            "hyperlink": _url,
            "price": str(product.get("price") or product.get("product_price", "")),
            "sale_price": str(product.get("sale_price") or product.get("product_sale_price", "")),
            "stored_images": len(product_data.get("stored_image_paths", [])),
        }
        # Merge any extra metadata passed by the caller
        if metadata:
            doc_metadata.update(metadata)
        
        # Store in vector database (upsert so re-upload replaces existing)
        self.collection.upsert(
            ids=[product_id],
            embeddings=[embedding],
            documents=[json.dumps(product_data, default=str)],
            metadatas=[doc_metadata]
        )
        
        logger.info(f"Added/updated product analysis in vector DB: {product_id}")

    def get_product_analysis(
        self,
        product_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve product analysis from vector database.
        
        Args:
            product_id: Product ID to retrieve
            
        Returns:
            Product data dictionary or None if not found
        """
        try:
            results = self.collection.get(
                ids=[product_id],
                include=["documents", "metadatas"]
            )
            
            if results["ids"]:
                doc = results["documents"][0]
                return json.loads(doc)
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve product analysis: {str(e)}")
            return None

    def search_similar_products(
        self,
        query_text: str,
        n_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar products using semantic similarity.
        
        Args:
            query_text: Text query to search for
            n_results: Number of results to return
            
        Returns:
            List of similar product analyses
        """
        # Create embedding for query
        query_embedding = self.create_embedding(query_text)
        
        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        similar_products = []
        for i, product_id in enumerate(results["ids"][0]):
            doc = json.loads(results["documents"][0][i])
            metadata = results["metadatas"][0][i]
            distance = results["distances"][0][i]
            
            similar_products.append({
                "product_id": product_id,
                "product_data": doc,
                "metadata": metadata,
                "similarity_score": self._distance_to_similarity(distance),
            })
        
        return similar_products

    def list_all_campaigns(self) -> List[str]:
        """List all campaign IDs in the vector database."""
        try:
            results = self.collection.get(include=["metadatas"])
            return [meta.get("campaign_id", "") for meta in results["metadatas"] if meta.get("campaign_id")]
        except Exception as e:
            logger.error(f"Failed to list campaigns: {str(e)}")
            return []

    def get_all_campaigns(self) -> List[Dict[str, Any]]:
        """
        Get all campaigns from the vector database with full documents.
        
        Returns:
            List of all campaign analyses with full document data
        """
        try:
            # Get all documents from the collection
            results = self.collection.get(
                include=["documents", "metadatas"]
            )
            
            all_campaigns = []
            for i, campaign_id in enumerate(results["ids"]):
                doc = results["documents"][i]
                metadata = results["metadatas"][i]
                
                # Try to parse document as JSON if it's a string
                try:
                    if isinstance(doc, str):
                        analysis = json.loads(doc)
                    else:
                        analysis = doc
                except (json.JSONDecodeError, TypeError):
                    # If parsing fails, use the document as-is
                    analysis = doc
                
                all_campaigns.append({
                    "campaign_id": campaign_id,
                    "analysis": analysis,
                    "metadata": metadata,
                    "similarity_score": 1.0,  # No similarity score for all documents
                    "document": doc,  # Include raw document
                })
            
            logger.info(f"Retrieved {len(all_campaigns)} campaigns from vector database")
            return all_campaigns
        except Exception as e:
            logger.error(f"Failed to get all campaigns: {str(e)}", exc_info=True)
            return []

    def delete_campaign(self, campaign_id: str) -> None:
        """Delete a campaign from the vector database."""
        try:
            self.collection.delete(ids=[campaign_id])
            logger.info(f"Deleted campaign from vector DB: {campaign_id}")
        except Exception as e:
            logger.error(f"Failed to delete campaign: {str(e)}")


def list_all_collections() -> List[str]:
    """List all available collections in the vector database."""
    if not CHROMADB_AVAILABLE:
        logger.warning("ChromaDB not available, cannot list collections")
        return []
    
    try:
        # Resolve vector_db_path relative to backend directory
        vector_path = Path(settings.vector_db_path)
        if not vector_path.is_absolute():
            backend_dir = Path(__file__).parent.parent.parent
            vector_db_path = backend_dir / vector_path
        else:
            vector_db_path = vector_path
        
        # Initialize ChromaDB client
        client = chromadb.PersistentClient(
            path=str(vector_db_path),
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        # List all collections
        collections = client.list_collections()
        collection_names = [col.name for col in collections]
        logger.info(f"Found {len(collection_names)} collections: {collection_names}")
        return collection_names
    except Exception as e:
        logger.error(f"Failed to list collections: {str(e)}", exc_info=True)
        return []


def get_product_context_for_prompts(
    product_names: Optional[List[str]] = None,
    collection_name: str = DEFAULT_PRODUCT_COLLECTION_NAME,
    max_products: int = 25,
) -> str:
    """
    Build a product context string (names + descriptions) for use in hero image, CTA, and key message prompts.
    If product_names is given, only those products are included; otherwise up to max_products from the collection.
    """
    products = get_all_products(collection_name)
    if not products:
        return ""
    lookup = {p["product_name"].lower().strip(): p for p in products if p.get("product_name")}
    if product_names:
        selected = []
        seen = set()
        for name in product_names:
            n = (name or "").strip()
            if not n or n.lower() in seen:
                continue
            seen.add(n.lower())
            if n.lower() in lookup:
                selected.append(lookup[n.lower()])
            else:
                selected.append({"product_name": n, "description": ""})
    else:
        selected = products[:max_products]
    lines = []
    for p in selected:
        name = p.get("product_name", "").strip()
        desc = (p.get("description") or "").strip()
        if name:
            lines.append(f"- {name}: {desc[:500]}" if desc else f"- {name}")
    return "\n".join(lines) if lines else ""


def get_product_names(collection_name: str = DEFAULT_PRODUCT_COLLECTION_NAME) -> List[str]:
    """
    Get all product names from the product collection in the vector database.
    Uses the same VectorDBService + collection.get() pattern as get_all_campaigns().
    """
    try:
        svc = VectorDBService(collection_name=collection_name)
        # Exact same call pattern as get_all_campaigns() which is proven to work
        results = svc.collection.get(include=["documents", "metadatas"])

        names: List[str] = []
        for i, doc_id in enumerate(results["ids"]):
            metadata = results["metadatas"][i]
            name = ""

            # 1. metadata.product_name (primary)
            if isinstance(metadata, dict):
                name = (metadata.get("product_name") or "").strip()

            # 2. Fallback: parse the stored document JSON
            if not name:
                try:
                    doc = results["documents"][i]
                    data = json.loads(doc) if isinstance(doc, str) else (doc or {})
                    product = data.get("product") or data
                    name = (product.get("name") or product.get("product_name") or "").strip()
                except (json.JSONDecodeError, TypeError, AttributeError):
                    pass

            if name:
                names.append(name)

        unique = sorted(set(names))
        logger.info(f"get_product_names({collection_name}): {len(unique)} products from {len(results['ids'])} docs")
        return unique
    except RuntimeError as e:
        logger.warning(f"ChromaDB not available for {collection_name}: {e}")
        return []
    except Exception as e:
        logger.error(f"Failed to get product names from {collection_name}: {e}", exc_info=True)
        return []


def get_all_products(
    collection_name: str = DEFAULT_PRODUCT_COLLECTION_NAME,
) -> List[Dict[str, Any]]:
    """
    Get all products with full metadata from the product collection in the vector database.
    Returns a list of dicts with keys: product_name, brand, category, description,
    price, sale_price, hyperlink, stored_images.
    """
    try:
        svc = VectorDBService(collection_name=collection_name)
        results = svc.collection.get(include=["documents", "metadatas"])

        products: List[Dict[str, Any]] = []
        for i, doc_id in enumerate(results["ids"]):
            metadata = results["metadatas"][i] if isinstance(results["metadatas"][i], dict) else {}

            # Try metadata first, then fall back to document JSON
            name = (metadata.get("product_name") or "").strip()
            brand = (metadata.get("brand") or "").strip()
            category = (metadata.get("category") or "").strip()
            description = (metadata.get("description") or "").strip()
            price = (metadata.get("price") or "").strip()
            sale_price = (metadata.get("sale_price") or "").strip()
            hyperlink = (metadata.get("hyperlink") or "").strip()
            stored_images = metadata.get("stored_images", 0)

            # Fallback: parse the stored document JSON for missing fields
            if not name or not description:
                try:
                    doc = results["documents"][i]
                    data = json.loads(doc) if isinstance(doc, str) else (doc or {})
                    product = data.get("product") or data
                    if not name:
                        name = (product.get("name") or product.get("product_name") or "").strip()
                    if not brand:
                        brand = (product.get("brand") or product.get("product_brand") or "").strip()
                    if not category:
                        category = (product.get("category") or product.get("product_category") or "").strip()
                    if not description:
                        description = str(product.get("description") or product.get("product_description") or "").strip()
                    if not price:
                        price = str(product.get("price") or product.get("product_price") or "").strip()
                    if not sale_price:
                        sale_price = str(product.get("sale_price") or product.get("product_sale_price") or "").strip()
                    if not hyperlink:
                        hyperlink = str(product.get("hyperlink") or product.get("url") or product.get("product_url") or "").strip()
                except (json.JSONDecodeError, TypeError, AttributeError):
                    pass

            if name:
                products.append({
                    "product_name": name,
                    "brand": brand,
                    "category": category,
                    "description": description,
                    "price": price,
                    "sale_price": sale_price,
                    "hyperlink": hyperlink,
                    "stored_images": stored_images if isinstance(stored_images, int) else 0,
                })

        # Sort by product name and deduplicate
        seen = set()
        unique_products = []
        for p in sorted(products, key=lambda x: x["product_name"]):
            if p["product_name"] not in seen:
                seen.add(p["product_name"])
                unique_products.append(p)

        logger.info(f"get_all_products({collection_name}): {len(unique_products)} products from {len(results['ids'])} docs")
        return unique_products
    except RuntimeError as e:
        logger.warning(f"ChromaDB not available for {collection_name}: {e}")
        return []
    except Exception as e:
        logger.error(f"Failed to get all products from {collection_name}: {e}", exc_info=True)
        return []


def get_product_images_by_names(
    product_names: List[str],
    collection_name: str = DEFAULT_PRODUCT_COLLECTION_NAME,
) -> List[str]:
    """
    Look up selected products in the vector DB and return their stored image paths.
    """
    if not product_names:
        return []
    try:
        svc = VectorDBService(collection_name=collection_name)
        results = svc.collection.get(include=["documents", "metadatas"])

        lookup = {n.lower() for n in product_names}
        image_paths: List[str] = []

        for i, doc_id in enumerate(results["ids"]):
            # Resolve product name from metadata or document
            metadata = results["metadatas"][i]
            name = ""
            if isinstance(metadata, dict):
                name = (metadata.get("product_name") or "").strip()
            if not name:
                try:
                    doc = results["documents"][i]
                    data = json.loads(doc) if isinstance(doc, str) else (doc or {})
                    product = data.get("product") or data
                    name = (product.get("name") or product.get("product_name") or "").strip()
                except (json.JSONDecodeError, TypeError, AttributeError):
                    pass

            if not name or name.lower() not in lookup:
                continue

            # Extract stored_image_paths from the document JSON
            try:
                doc = results["documents"][i]
                data = json.loads(doc) if isinstance(doc, str) else (doc or {})
                paths = data.get("stored_image_paths") or []
                if isinstance(paths, list):
                    image_paths.extend([str(p) for p in paths if p])
            except (json.JSONDecodeError, TypeError, AttributeError):
                pass

        logger.info(f"get_product_images_by_names: {len(image_paths)} images for {len(product_names)} products")
        return image_paths
    except RuntimeError as e:
        logger.warning(f"ChromaDB not available for {collection_name}: {e}")
        return []
    except Exception as e:
        logger.error(f"Failed to get product images: {e}", exc_info=True)
        return []

