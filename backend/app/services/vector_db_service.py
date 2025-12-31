"""Vector database service for storing and retrieving campaign analysis embeddings."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.config import settings

logger = logging.getLogger(__name__)

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("ChromaDB not available. Install with: pip install chromadb")


class VectorDBService:
    """Service for managing vector embeddings in ChromaDB."""

    def __init__(self, collection_name: str = "campaign_analyses"):
        """Initialize vector database service."""
        if not CHROMADB_AVAILABLE:
            raise RuntimeError("ChromaDB not available. Install with: pip install chromadb")
        
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
        """
        Create embedding for text using OpenAI or Ollama.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        # Try OpenAI first if available
        if settings.openai_api_key:
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
            embedding_models = [settings.ollama_embedding_model, "nomic-embed-text", "nomic-embed", "all-minilm"]
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
        if "name" in product:
            text_parts.append(f"Product: {product['name']}")
        elif "product_name" in product:
            text_parts.append(f"Product: {product['product_name']}")
        
        if "description" in product:
            text_parts.append(f"Description: {product['description']}")
        elif "product_description" in product:
            text_parts.append(f"Description: {product['product_description']}")
        
        if "category" in product:
            text_parts.append(f"Category: {product['category']}")
        elif "product_category" in product:
            text_parts.append(f"Category: {product['product_category']}")
        
        if "price" in product:
            text_parts.append(f"Price: ${product['price']}")
        elif "product_price" in product:
            text_parts.append(f"Price: ${product['product_price']}")
        
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
        
        # Prepare metadata
        doc_metadata = {
            "product_id": product_id,
            "business_name": product_data.get("business_name", ""),
            "product_name": product.get("name") or product.get("product_name", ""),
            "stored_images": len(product_data.get("stored_image_paths", [])),
            **(metadata or {})
        }
        
        # Store in vector database
        self.collection.add(
            ids=[product_id],
            embeddings=[embedding],
            documents=[json.dumps(product_data, default=str)],
            metadatas=[doc_metadata]
        )
        
        logger.info(f"Added product analysis to vector DB: {product_id}")

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
                "similarity_score": 1.0 - distance,  # Convert distance to similarity
            })
        
        return similar_products

