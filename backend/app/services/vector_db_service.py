"""Vector database service for storing and retrieving campaign analysis embeddings.
Supports ChromaDB (local) and MongoDB Atlas Vector Search."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..core.config import settings

logger = logging.getLogger(__name__)
DEFAULT_PRODUCT_COLLECTION_NAME = "UCO_Gear_Products"


def create_embedding_for_text(text: str) -> List[float]:
    """Create embedding for text using OpenAI or Ollama. Shared by Chroma and Atlas backends."""
    if settings.openai_api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.openai_api_key)
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=text,
            )
            return response.data[0].embedding
        except Exception as e:
            logger.warning("OpenAI embedding failed: %s, trying Ollama fallback", e)
    try:
        import httpx
        try:
            httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=5.0).raise_for_status()
        except Exception:
            raise RuntimeError("Ollama server not available. Please start Ollama or configure OpenAI API key.")
        models = list(dict.fromkeys([settings.ollama_embedding_model, "nomic-embed-text", "nomic-embed", "all-minilm"]))
        for model in models:
            try:
                r = httpx.post(
                    f"{settings.ollama_base_url}/api/embeddings",
                    json={"model": model, "prompt": text},
                    timeout=30.0,
                )
                r.raise_for_status()
                emb = r.json().get("embedding")
                if emb:
                    return emb
            except httpx.HTTPStatusError as e:
                if e.response.status_code != 404:
                    raise
            except Exception:
                continue
        raise RuntimeError(f"None of {models} available in Ollama. Try: ollama pull nomic-embed-text")
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to create embedding: {e}. Configure OpenAI or run Ollama with an embedding model.") from e

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    if not settings.use_atlas_vector_search:
        logger.warning("ChromaDB not available. Install with: pip install chromadb")
    else:
        logger.debug("ChromaDB not installed; using MongoDB Atlas for vector search.")


def _resolve_vector_db_path() -> Path:
    """Resolve the configured vector DB path relative to the backend directory."""
    vector_path = Path(settings.vector_db_path)
    if vector_path.is_absolute():
        return vector_path

    backend_dir = Path(__file__).parent.parent.parent
    return backend_dir / vector_path


def _get_chroma_client():
    """Create a Chroma client when the dependency is available."""
    if not CHROMADB_AVAILABLE:
        return None

    vector_db_path = _resolve_vector_db_path()
    vector_db_path.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(
        path=str(vector_db_path),
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def _coerce_metadata_text(value: Any, limit: int | None = None) -> str:
    """Convert metadata values to compact strings suitable for Chroma."""
    if value is None:
        text = ""
    elif isinstance(value, str):
        text = value
    else:
        text = str(value)

    text = text.strip()
    if limit is not None:
        return text[:limit]
    return text


def delete_collection_if_exists(collection_name: str) -> bool:
    """Delete a vector collection if it exists (Chroma or Atlas). Returns True when deleted."""
    if (getattr(settings, "use_atlas_vector_search", False) or not CHROMADB_AVAILABLE) and _ATLAS_AVAILABLE:
        try:
            db = get_database()
            db[collection_name].drop()
            logger.info("Dropped Atlas vector collection: %s", collection_name)
            return True
        except Exception as exc:
            logger.info("Atlas collection '%s' drop skipped: %s", collection_name, exc)
            return False
    if not CHROMADB_AVAILABLE:
        logger.warning("Skipping deletion of collection '%s' (no vector backend available).", collection_name)
        return False
    client = _get_chroma_client()
    if client is None:
        return False
    try:
        client.delete_collection(name=collection_name)
        logger.info("Deleted existing Chroma collection: %s", collection_name)
        return True
    except Exception as exc:
        if "does not exist" in str(exc).lower() or "not found" in str(exc).lower():
            logger.info("Chroma collection '%s' does not exist.", collection_name)
            return False
        raise


class VectorDBService:
    """Service for managing vector embeddings in ChromaDB."""

    def __init__(self, collection_name: str = "campaign_analyses"):
        """Initialize vector database service."""
        if not CHROMADB_AVAILABLE:
            raise RuntimeError("ChromaDB not available. Install with: pip install chromadb")
        
        self.collection_name = collection_name
        
        # Resolve vector_db_path relative to backend directory
        self.vector_db_path = _resolve_vector_db_path()
        
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
            # Collection doesn't exist, create it
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "Campaign analysis embeddings"}
            )
            logger.info(f"Created new collection: {collection_name}")
        
        logger.info(f"Initialized vector database at {self.vector_db_path}")
    
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
                    metadata={"description": "Campaign analysis embeddings"}
                )
                logger.warning(f"Recreated collection (lost {old_count} documents). Please re-import data.")
            else:
                raise
    
    def _create_collection(self):
        """Create a new collection."""
        return self.client.create_collection(
            name=self.collection_name,
            metadata={"description": "Campaign analysis embeddings"}
        )

    def create_embedding(self, text: str) -> List[float]:
        """Create embedding for text (delegates to shared helper)."""
        return create_embedding_for_text(text)

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
                if "extracted_text" in analysis and analysis["extracted_text"]:
                    text_content = analysis["extracted_text"]
                    if isinstance(text_content, str):
                        extracted_texts.append(text_content[:200])
                
                # Extract elements
                if "elements" in analysis and isinstance(analysis["elements"], list):
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
        
        # Create embedding
        embedding = self.create_embedding(text)
        
        # Prepare metadata
        doc_metadata = {
            "campaign_id": campaign_id,
            "total_images": len(analysis_data.get("images", [])),
            **(metadata or {})
        }
        
        # Store in vector database
        self.collection.add(
            ids=[campaign_id],
            embeddings=[embedding],
            documents=[json.dumps(analysis_data, default=str)],
            metadatas=[doc_metadata]
        )
        
        logger.info(f"Added campaign analysis to vector DB: {campaign_id}")

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
            doc = json.loads(results["documents"][0][i])
            metadata = results["metadatas"][0][i]
            distance = results["distances"][0][i]
            
            similar_campaigns.append({
                "campaign_id": campaign_id,
                "analysis": doc,
                "metadata": metadata,
                "similarity_score": 1.0 - distance,  # Convert distance to similarity
            })
        
        return similar_campaigns

    def list_all_campaigns(self) -> List[str]:
        """List all campaign IDs in the vector database."""
        try:
            results = self.collection.get(include=["metadatas"])
            return [meta.get("campaign_id", "") for meta in results["metadatas"] if meta.get("campaign_id")]
        except Exception as e:
            logger.error(f"Failed to list campaigns: {str(e)}")
            return []

    def delete_campaign(self, campaign_id: str) -> None:
        """Delete a campaign from the vector database."""
        try:
            self.collection.delete(ids=[campaign_id])
            logger.info(f"Deleted campaign from vector DB: {campaign_id}")
        except Exception as e:
            logger.error(f"Failed to delete campaign: {str(e)}")

    def add_product_analysis(
        self,
        product_id: str,
        product_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add product data to a vector collection."""
        self._ensure_collection_dimension()

        product = product_data.get("product", {})
        text_parts = [
            f"Product ID: {product_id}",
            f"Business: {_coerce_metadata_text(product_data.get('business_name'))}",
            f"Name: {_coerce_metadata_text(product.get('name') or product.get('product_name'))}",
            f"Brand: {_coerce_metadata_text(product.get('brand') or product.get('product_brand'))}",
            f"Category: {_coerce_metadata_text(product.get('category') or product.get('product_category'))}",
            f"Description: {_coerce_metadata_text(product.get('description') or product.get('product_description'), 2000)}",
            f"Price: {_coerce_metadata_text(product.get('price') or product.get('product_price'))}",
            f"Sale price: {_coerce_metadata_text(product.get('sale_price') or product.get('product_sale_price'))}",
            f"URL: {_coerce_metadata_text(product.get('hyperlink') or product.get('url') or product.get('product_url'))}",
        ]
        text = " ".join(part for part in text_parts if part.split(": ", 1)[1])
        embedding = self.create_embedding(text or product_id)

        doc_metadata = {
            "product_id": product_id,
            "business_name": _coerce_metadata_text(product_data.get("business_name"), 256),
            "product_name": _coerce_metadata_text(product.get("name") or product.get("product_name"), 512),
            "brand": _coerce_metadata_text(product.get("brand") or product.get("product_brand"), 256),
            "category": _coerce_metadata_text(product.get("category") or product.get("product_category"), 256),
            "description": _coerce_metadata_text(product.get("description") or product.get("product_description"), 512),
            "price": _coerce_metadata_text(product.get("price") or product.get("product_price"), 64),
            "sale_price": _coerce_metadata_text(product.get("sale_price") or product.get("product_sale_price"), 64),
            "hyperlink": _coerce_metadata_text(product.get("hyperlink") or product.get("url") or product.get("product_url"), 512),
            "stored_images": len(product_data.get("stored_image_paths") or []),
            **(metadata or {}),
        }

        self.collection.upsert(
            ids=[product_id],
            embeddings=[embedding],
            documents=[json.dumps(product_data, default=str)],
            metadatas=[doc_metadata],
        )
        logger.info("Added product to vector DB: %s", product_id)


# --- MongoDB Atlas Vector Search backend ---

try:
    from ..db.mongodb import get_database
    _ATLAS_AVAILABLE = True
except Exception:
    _ATLAS_AVAILABLE = False


def _build_campaign_text_for_embedding(analysis_data: Dict[str, Any]) -> str:
    """Build text representation of campaign analysis for embedding (shared logic)."""
    text_parts = []
    if analysis_data.get("campaign_id"):
        text_parts.append(f"Campaign: {analysis_data['campaign_id']}")
    summary = analysis_data.get("summary") or {}
    if summary.get("average_brightness") is not None:
        text_parts.append(f"Average brightness: {summary['average_brightness']}")
    if summary.get("color_palette"):
        palette = summary["color_palette"]
        if isinstance(palette, list):
            text_parts.append(f"Color palette: {', '.join(str(c) for c in palette[:5])}")
    for key in ("campaign_name", "subject", "open_rate", "click_rate", "revenue"):
        if analysis_data.get(key) is not None:
            text_parts.append(f"{key}: {analysis_data[key]}")
    images = analysis_data.get("images") or []
    text_parts.append(f"Total images: {len(images)}")
    all_colors, brightness_vals, extracted, elements = [], [], [], []
    for img_data in images:
        analysis = img_data.get("analysis", {}) if "analysis" in img_data else img_data
        if analysis.get("dominant_colors") and isinstance(analysis["dominant_colors"], list):
            all_colors.extend(str(c) for c in analysis["dominant_colors"][:3])
        if analysis.get("brightness") is not None:
            brightness_vals.append(analysis["brightness"])
        if analysis.get("extracted_text"):
            extracted.append(str(analysis["extracted_text"])[:200])
        for elem in (analysis.get("elements") or [])[:5]:
            if isinstance(elem, dict) and elem.get("type"):
                elements.append(elem["type"])
    if all_colors:
        text_parts.append(f"Dominant colors: {', '.join(list(dict.fromkeys(all_colors))[:10])}")
    if brightness_vals:
        text_parts.append(f"Average image brightness: {sum(brightness_vals) / len(brightness_vals):.1f}")
    if extracted:
        text_parts.append(f"Extracted text: {' '.join(extracted[:3])}")
    if elements:
        text_parts.append(f"Visual elements: {', '.join(list(dict.fromkeys(elements))[:10])}")
    return " ".join(text_parts)


class VectorDBServiceAtlas:
    """Vector DB implementation using MongoDB Atlas Vector Search. Use when use_atlas_vector_search=True."""

    def __init__(self, collection_name: str = "campaign_analyses"):
        if not _ATLAS_AVAILABLE:
            raise RuntimeError("MongoDB not available. Install pymongo and set MONGODB_URI (and USE_ATLAS_VECTOR_SEARCH=true).")
        self.collection_name = collection_name
        db = get_database()
        self.collection = db[collection_name]
        self.vector_db_path = None  # Not used for Atlas
        logger.info("Initialized Atlas Vector Search collection: %s", collection_name)

    def create_embedding(self, text: str) -> List[float]:
        return create_embedding_for_text(text)

    def add_campaign_analysis(
        self,
        campaign_id: str,
        analysis_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        text = _build_campaign_text_for_embedding(analysis_data)
        embedding = self.create_embedding(text)
        doc_metadata = {
            "campaign_id": campaign_id,
            "total_images": len(analysis_data.get("images", [])),
            **(metadata or {}),
        }
        doc = {
            "_id": campaign_id,
            "embedding": embedding,
            "document": json.dumps(analysis_data, default=str),
            "metadata": doc_metadata,
        }
        self.collection.replace_one({"_id": campaign_id}, doc, upsert=True)
        logger.info("Added campaign analysis to Atlas vector DB: %s", campaign_id)

    def get_campaign_analysis(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        doc = self.collection.find_one({"_id": campaign_id})
        if not doc or "document" not in doc:
            return None
        return json.loads(doc["document"])

    def search_similar_campaigns(
        self,
        query_text: str,
        n_results: int = 5,
    ) -> List[Dict[str, Any]]:
        query_embedding = self.create_embedding(query_text)
        index_name = settings.mongodb_vector_index_name
        pipeline = [
            {
                "$vectorSearch": {
                    "index": index_name,
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": max(n_results * 20, 100),
                    "limit": n_results,
                }
            },
            {"$project": {"document": 1, "metadata": 1, "score": {"$meta": "vectorSearchScore"}}},
        ]
        cursor = self.collection.aggregate(pipeline)
        similar = []
        for hit in cursor:
            doc_str = hit.get("document")
            meta = hit.get("metadata") or {}
            score = hit.get("score") or 0.0
            similar.append({
                "campaign_id": meta.get("campaign_id", hit.get("_id", "")),
                "analysis": json.loads(doc_str) if isinstance(doc_str, str) else doc_str,
                "metadata": meta,
                "similarity_score": float(score),
            })
        return similar

    def list_all_campaigns(self) -> List[str]:
        return [doc["metadata"].get("campaign_id") or str(doc["_id"]) for doc in self.collection.find({"metadata.campaign_id": {"$exists": True}}, {"metadata.campaign_id": 1})]

    def delete_campaign(self, campaign_id: str) -> None:
        self.collection.delete_one({"_id": campaign_id})
        logger.info("Deleted campaign from Atlas vector DB: %s", campaign_id)

    def add_product_analysis(
        self,
        product_id: str,
        product_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        product = product_data.get("product", {})
        text_parts = [
            f"Product ID: {product_id}",
            f"Business: {_coerce_metadata_text(product_data.get('business_name'))}",
            f"Name: {_coerce_metadata_text(product.get('name') or product.get('product_name'))}",
            f"Brand: {_coerce_metadata_text(product.get('brand') or product.get('product_brand'))}",
            f"Category: {_coerce_metadata_text(product.get('category') or product.get('product_category'))}",
            f"Description: {_coerce_metadata_text(product.get('description') or product.get('product_description'), 2000)}",
            f"Price: {_coerce_metadata_text(product.get('price') or product.get('product_price'))}",
            f"Sale price: {_coerce_metadata_text(product.get('sale_price') or product.get('product_sale_price'))}",
            f"URL: {_coerce_metadata_text(product.get('hyperlink') or product.get('url') or product.get('product_url'))}",
        ]
        text = " ".join(p for p in text_parts if p.split(": ", 1)[-1])
        embedding = self.create_embedding(text or product_id)
        doc_metadata = {
            "product_id": product_id,
            "business_name": _coerce_metadata_text(product_data.get("business_name"), 256),
            "product_name": _coerce_metadata_text(product.get("name") or product.get("product_name"), 512),
            "brand": _coerce_metadata_text(product.get("brand") or product.get("product_brand"), 256),
            "category": _coerce_metadata_text(product.get("category") or product.get("product_category"), 256),
            "description": _coerce_metadata_text(product.get("description") or product.get("product_description"), 512),
            "price": _coerce_metadata_text(product.get("price") or product.get("product_price"), 64),
            "sale_price": _coerce_metadata_text(product.get("sale_price") or product.get("product_sale_price"), 64),
            "hyperlink": _coerce_metadata_text(product.get("hyperlink") or product.get("url") or product.get("product_url"), 512),
            "stored_images": len(product_data.get("stored_image_paths") or []),
            **(metadata or {}),
        }
        self.collection.replace_one(
            {"_id": product_id},
            {"_id": product_id, "embedding": embedding, "document": json.dumps(product_data, default=str), "metadata": doc_metadata},
            upsert=True,
        )
        logger.info("Added product to Atlas vector DB: %s", product_id)


def get_vector_db_service(collection_name: str = "campaign_analyses") -> Union["VectorDBService", "VectorDBServiceAtlas"]:
    """Return the configured vector DB implementation (Atlas preferred, Chroma fallback)."""
    if getattr(settings, "use_atlas_vector_search", False) and _ATLAS_AVAILABLE:
        return VectorDBServiceAtlas(collection_name=collection_name)
    # When ChromaDB is unavailable but Atlas is, fall back to Atlas automatically
    if not CHROMADB_AVAILABLE:
        if _ATLAS_AVAILABLE:
            logger.info("ChromaDB unavailable; falling back to MongoDB Atlas for vector search.")
            return VectorDBServiceAtlas(collection_name=collection_name)
        raise RuntimeError("No vector backend available. Install chromadb or set USE_ATLAS_VECTOR_SEARCH=true with MONGODB_URI.")
    return VectorDBService(collection_name=collection_name)


def list_all_collections() -> List[str]:
    """List available vector collection names (Atlas or Chroma)."""
    if (getattr(settings, "use_atlas_vector_search", False) or not CHROMADB_AVAILABLE) and _ATLAS_AVAILABLE:
        try:
            return get_database().list_collection_names()
        except Exception as exc:
            logger.warning("Failed to list Atlas collections: %s", exc)
            return []
    client = _get_chroma_client()
    if client is None:
        return []
    try:
        collections = client.list_collections()
    except Exception as exc:
        logger.warning("Failed to list Chroma collections: %s", exc)
        return []
    names: List[str] = []
    for collection in collections:
        name = getattr(collection, "name", None)
        if name:
            names.append(name)
        elif isinstance(collection, str):
            names.append(collection)
    return names


def _get_collection(collection_name: str):
    """Get collection from Atlas or Chroma."""
    if (getattr(settings, "use_atlas_vector_search", False) or not CHROMADB_AVAILABLE) and _ATLAS_AVAILABLE:
        return get_database()[collection_name]
    client = _get_chroma_client()
    if client is None:
        return None
    try:
        return client.get_collection(name=collection_name)
    except Exception:
        return None


def get_all_products(collection_name: str = DEFAULT_PRODUCT_COLLECTION_NAME) -> List[Dict[str, Any]]:
    """Return product metadata rows from a product vector collection (Chroma or Atlas)."""
    if (getattr(settings, "use_atlas_vector_search", False) or not CHROMADB_AVAILABLE) and _ATLAS_AVAILABLE:
        try:
            coll = get_database()[collection_name]
            products = []
            for doc in coll.find({}, {"metadata": 1}):
                meta = doc.get("metadata") or {}
                products.append({
                    "product_name": _coerce_metadata_text(meta.get("product_name")),
                    "brand": _coerce_metadata_text(meta.get("brand")),
                    "category": _coerce_metadata_text(meta.get("category")),
                    "description": _coerce_metadata_text(meta.get("description")),
                    "price": _coerce_metadata_text(meta.get("price")),
                    "sale_price": _coerce_metadata_text(meta.get("sale_price")),
                    "hyperlink": _coerce_metadata_text(meta.get("hyperlink")),
                    "stored_images": int(meta.get("stored_images") or 0),
                })
            products.sort(key=lambda p: (p.get("product_name") or "").lower())
            return products
        except Exception as exc:
            logger.warning("Failed to read products from Atlas collection '%s': %s", collection_name, exc)
            return []
    collection = _get_collection(collection_name)
    if collection is None:
        return []
    try:
        results = collection.get(include=["metadatas"]) if hasattr(collection, "get") else None
        if results is None:
            return []
    except Exception as exc:
        logger.warning("Failed to read products from collection '%s': %s", collection_name, exc)
        return []
    products = []
    for metadata in (results.get("metadatas") or []) if isinstance(results, dict) else []:
        if not metadata:
            continue
        products.append({
            "product_name": _coerce_metadata_text(metadata.get("product_name")),
            "brand": _coerce_metadata_text(metadata.get("brand")),
            "category": _coerce_metadata_text(metadata.get("category")),
            "description": _coerce_metadata_text(metadata.get("description")),
            "price": _coerce_metadata_text(metadata.get("price")),
            "sale_price": _coerce_metadata_text(metadata.get("sale_price")),
            "hyperlink": _coerce_metadata_text(metadata.get("hyperlink")),
            "stored_images": int(metadata.get("stored_images") or 0),
        })
    products.sort(key=lambda product: (product.get("product_name") or "").lower())
    return products


def get_product_names(collection_name: str = DEFAULT_PRODUCT_COLLECTION_NAME) -> List[str]:
    """Return unique product names from a product vector collection."""
    names = {
        product["product_name"].strip()
        for product in get_all_products(collection_name)
        if product.get("product_name", "").strip()
    }
    return sorted(names, key=str.lower)


def get_product_context_for_prompts(
    product_names: Optional[List[str]] = None,
    collection_name: str = DEFAULT_PRODUCT_COLLECTION_NAME,
    max_products: int = 25,
) -> str:
    """Build a compact product context block for downstream prompts."""
    products = get_all_products(collection_name)
    if not products:
        return ""

    normalized_names = {
        name.strip().lower()
        for name in (product_names or [])
        if isinstance(name, str) and name.strip()
    }
    if normalized_names:
        filtered = [
            product for product in products
            if product.get("product_name", "").strip().lower() in normalized_names
        ]
        products = filtered or products

    lines: List[str] = []
    for product in products[:max_products]:
        details = [product["product_name"]]
        if product.get("brand"):
            details.append(f"brand={product['brand']}")
        if product.get("category"):
            details.append(f"category={product['category']}")
        if product.get("price"):
            details.append(f"price={product['price']}")
        if product.get("sale_price"):
            details.append(f"sale_price={product['sale_price']}")
        if product.get("description"):
            details.append(f"description={product['description']}")
        lines.append(" | ".join(details))

    return "\n".join(lines)

