"""Workflow for loading products and images from zip files into vector database."""
from __future__ import annotations

import json
import logging
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional



from ..core.config import settings
from ..services.vector_db_service import VectorDBService
from ..services.zip_handler import extract_zip_file, cleanup_directory

logger = logging.getLogger(__name__)

# Supported image extensions
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}
# Supported product data file extensions
PRODUCT_DATA_EXTENSIONS = {".csv", ".json"}


def _find_product_data_files(extracted_dir: Path) -> List[Path]:
    """Find product data files (CSV or JSON) in the extracted directory."""
    product_files = []
    for ext in PRODUCT_DATA_EXTENSIONS:
        product_files.extend(extracted_dir.rglob(f"*{ext}"))
    return product_files


def _find_image_files(extracted_dir: Path) -> List[Path]:
    """Find image files in the extracted directory."""
    image_files = []
    for ext in IMAGE_EXTENSIONS:
        found_files = extracted_dir.rglob(f"*{ext}")
        # Filter out macOS metadata files (._* files) and other hidden/system files
        for img_file in found_files:
            # Skip macOS metadata files (._*), hidden files, and system files
            if img_file.name.startswith("._") or img_file.name.startswith("."):
                logger.debug(f"Skipping system/metadata file: {img_file.name}")
                continue
            image_files.append(img_file)
    return image_files


def _load_product_data(file_path: Path) -> List[Dict[str, Any]]:
    """Load product data from CSV or JSON file."""
    if file_path.suffix.lower() == ".csv":
        df = pd.read_csv(file_path)
        # Convert DataFrame to list of dictionaries
        products = df.to_dict("records")
        return products
    elif file_path.suffix.lower() == ".json":
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Handle both list and single object
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                # If it's a dict, check if it has a products key
                if "products" in data:
                    return data["products"]
                else:
                    return [data]
            else:
                logger.warning(f"Unexpected JSON format in {file_path}")
                return []
    else:
        logger.warning(f"Unsupported file format: {file_path.suffix}")
        return []


def _match_images_to_products(
    products: List[Dict[str, Any]], image_files: List[Path]
) -> Dict[str, List[Path]]:
    """
    Match image files to products based on filename patterns.
    
    Returns a dictionary mapping product identifiers to image paths.
    """
    product_images = {}
    used_images = set()  # Track which images have been matched to avoid duplicates
    
    # Try to identify product identifier fields
    product_id_fields = ["product_id", "id", "sku", "product_sku", "name", "product_name"]
    
    for product in products:
        # Find product identifier
        product_id = None
        for field in product_id_fields:
            if field in product and product[field]:
                product_id = str(product[field]).lower().strip()
                break
        
        if not product_id:
            # Generate ID from product name or use index
            product_name = product.get("name") or product.get("product_name", f"product_{len(product_images)}")
            product_id = product_name.lower().strip().replace(" ", "_")
        
        # Find matching images (only unused ones)
        matching_images = []
        product_id_normalized = product_id.replace("_", "").replace("-", "").replace(" ", "")
        
        for img_file in image_files:
            # Skip if this image has already been matched to another product
            if img_file in used_images:
                continue
                
            img_name = img_file.stem.lower().replace("_", "").replace("-", "").replace(" ", "")
            
            # Check if image filename contains product identifier
            if product_id_normalized in img_name or img_name in product_id_normalized:
                matching_images.append(img_file)
                used_images.add(img_file)
            # Also check if image is in a folder named after the product
            elif product_id_normalized in str(img_file.parent).lower():
                matching_images.append(img_file)
                used_images.add(img_file)
        
        if matching_images:
            product_images[product_id] = matching_images
        else:
            # If no match found, assign first unmatched image (if any)
            unmatched = [img for img in image_files if img not in used_images]
            if unmatched:
                product_images[product_id] = [unmatched[0]]
                used_images.add(unmatched[0])
    
    return product_images


def _extract_business_name_from_filename(zip_file_path: str) -> str:
    """
    Extract business name from zip file filename.
    
    Examples:
    - "UCO_Gear_Products.zip" -> "UCO_Gear"
    - "UCO_Gear_Campaigns.zip" -> "UCO_Gear"
    - "acme_products.zip" -> "acme"
    - "acme_campaigns.zip" -> "acme"
    - "Acme Products.zip" -> "Acme Products"
    - "business-name_data.zip" -> "business-name"
    - "MyCompany_Products.zip" -> "MyCompany"
    - "MyCompany_Campaigns.zip" -> "MyCompany"
    
    Args:
        zip_file_path: Path to the zip file
        
    Returns:
        Business name extracted from filename (without extension)
    """
    zip_path = Path(zip_file_path)
    filename = zip_path.stem  # Get filename without extension
    
    # Remove common suffixes that might be in the filename (case-insensitive)
    # Order matters - check longer suffixes first
    suffixes_to_remove = [
        "_products", "_product", "_campaigns", "_campaign", "_data", "_items", "_images", "_files",
        "-products", "-product", "-campaigns", "-campaign", "-data", "-items", "-images", "-files",
        " products", " product", " campaigns", " campaign", " data", " items", " images", " files",
    ]
    
    business_name = filename
    for suffix in suffixes_to_remove:
        if business_name.lower().endswith(suffix.lower()):
            business_name = business_name[: -len(suffix)]
            break
    
    # If empty after processing, use the original filename
    if not business_name.strip():
        business_name = filename
    
    logger.info(f"Extracted business name '{business_name}' from zip filename '{zip_path.name}'")
    return business_name


def _store_product_images(
    image_paths: List[Path],
    product_id: str,
    business_name: str,
    storage_base: Path,
) -> List[str]:
    """
    Copy product images to a private storage folder on the server.
    
    Args:
        image_paths: List of source image paths
        product_id: Product identifier
        business_name: Business name for organization
        storage_base: Base storage directory
        
    Returns:
        List of stored image paths (server paths)
    """
    stored_paths = []
    
    # Create storage directory structure: storage/product_images/{business_name}/{product_id}/
    business_slug = business_name.lower().replace(" ", "_")
    product_storage_dir = storage_base / business_slug / product_id
    product_storage_dir.mkdir(parents=True, exist_ok=True)
    
    for img_path in image_paths:
        try:
            # Generate unique filename to avoid conflicts
            file_extension = img_path.suffix
            unique_filename = f"{uuid.uuid4().hex[:8]}_{img_path.name}"
            destination_path = product_storage_dir / unique_filename
            
            # Copy image to storage
            shutil.copy2(img_path, destination_path)
            stored_paths.append(str(destination_path))
            logger.info(f"Stored image {img_path.name} to {destination_path}")
        except Exception as e:
            logger.error(f"Failed to store image {img_path}: {str(e)}", exc_info=True)
            continue
    
    return stored_paths


def load_product_zip_to_vector_db(
    zip_file_path: str,
    business_name: Optional[str] = None,
    collection_name: Optional[str] = None,
    cleanup_extracted: bool = True,
) -> Dict[str, Any]:
    """
    Load products and images from a zip file into vector database.
    
    Images are stored in a private folder on the server: storage/product_images/{business_name}/{product_id}/
    
    Args:
        zip_file_path: Path to the zip file containing products and images
        business_name: Optional name of the business. If not provided, extracted from zip filename.
        collection_name: Optional custom collection name (default: "products_{business_name}")
        cleanup_extracted: Whether to cleanup extracted files after processing
        
    Returns:
        Dictionary with ingestion results
    """
    logger.info(f"Starting product zip ingestion: {zip_file_path}")
    
    # Extract business name from zip filename if not provided
    if not business_name:
        business_name = _extract_business_name_from_filename(zip_file_path)
    
    if not business_name or not business_name.strip():
        logger.error("Could not determine business name from zip filename and none provided")
        return {
            "status": "error",
            "error": "Business name is required. Provide it as parameter or ensure zip filename contains business name.",
            "products_processed": 0,
            "images_stored": 0,
        }
    
    logger.info(f"Using business name: {business_name}")
    
    # Extract zip file
    try:
        extracted_dir = Path(extract_zip_file(zip_file_path))
        logger.info(f"Extracted zip to: {extracted_dir}")
    except Exception as e:
        logger.error(f"Failed to extract zip file: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": f"Failed to extract zip file: {str(e)}",
            "products_processed": 0,
            "images_stored": 0,
        }
    
    try:
        # Find product data files
        product_data_files = _find_product_data_files(extracted_dir)
        if not product_data_files:
            logger.warning("No product data files (CSV/JSON) found in zip")
            return {
                "status": "error",
                "error": "No product data files found in zip",
                "products_processed": 0,
                "images_stored": 0,
            }
        
        logger.info(f"Found {len(product_data_files)} product data file(s)")
        
        # Find image files
        image_files = _find_image_files(extracted_dir)
        logger.info(f"Found {len(image_files)} image file(s)")
        
        # Load products from all data files
        all_products = []
        for data_file in product_data_files:
            try:
                products = _load_product_data(data_file)
                all_products.extend(products)
                logger.info(f"Loaded {len(products)} products from {data_file.name}")
            except Exception as e:
                logger.error(f"Failed to load products from {data_file}: {str(e)}", exc_info=True)
                continue
        
        if not all_products:
            logger.warning("No products loaded from data files")
            return {
                "status": "error",
                "error": "No products loaded from data files",
                "products_processed": 0,
                "images_stored": 0,
            }
        
        logger.info(f"Total products loaded: {len(all_products)}")
        
        # Match images to products
        product_images_map = _match_images_to_products(all_products, image_files)
        logger.info(f"Matched images to {len(product_images_map)} products")
        
        # Initialize services
        try:
            vector_db_service = VectorDBService(
                collection_name=collection_name or f"products_{business_name.lower().replace(' ', '_')}"
            )
            
            # Set up product images storage directory
            backend_dir = Path(__file__).parent.parent.parent
            storage_base = backend_dir / "storage" / "product_images"
            storage_base.mkdir(parents=True, exist_ok=True)
            
            # Clear previous images for this business before uploading new ones
            business_slug = business_name.lower().replace(" ", "_")
            business_storage_dir = storage_base / business_slug
            if business_storage_dir.exists() and business_storage_dir.is_dir():
                logger.info(f"Clearing previous images folder for business: {business_name} ({business_storage_dir})")
                try:
                    shutil.rmtree(business_storage_dir)
                    logger.info(f"Cleared previous images folder: {business_storage_dir}")
                except Exception as e:
                    logger.warning(f"Failed to clear previous images folder {business_storage_dir}: {str(e)}")
                    # Continue anyway - we'll overwrite files as needed
        except Exception as e:
            logger.error(f"Failed to initialize services: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": f"Service initialization failed: {str(e)}",
                "products_processed": 0,
                "images_stored": 0,
            }
        
        # Process each product
        products_processed = 0
        images_stored = 0
        processed_product_ids = []
        
        for product in all_products:
            try:
                # Get product identifier
                product_id = None
                for field in ["product_id", "id", "sku", "product_sku"]:
                    if field in product and product[field]:
                        product_id = str(product[field])
                        break
                
                if not product_id:
                    product_name = product.get("name") or product.get("product_name", f"product_{products_processed}")
                    product_id = product_name.lower().strip().replace(" ", "_")
                
                # Get images for this product
                product_image_paths = product_images_map.get(product_id, [])
                
                # Store images to private folder
                stored_image_paths = []
                if product_image_paths:
                    stored_image_paths = _store_product_images(
                        product_image_paths,
                        product_id,
                        business_name,
                        storage_base,
                    )
                    images_stored += len(stored_image_paths)
                
                # Prepare product data for vector DB
                product_data = {
                    "product_id": product_id,
                    "business_name": business_name,
                    "product": product,
                    "stored_image_paths": stored_image_paths,  # Server paths to stored images
                    "ingested_at": datetime.utcnow().isoformat(),
                }
                
                # Store in vector database
                try:
                    vector_db_service.add_product_analysis(
                        product_id=product_id,
                        product_data=product_data,
                        metadata={
                            "business_name": business_name,
                            "product_name": product.get("name") or product.get("product_name", ""),
                            "category": product.get("category") or product.get("product_category", ""),
                            "stored_images": len(stored_image_paths),
                        },
                    )
                    products_processed += 1
                    processed_product_ids.append(product_id)
                    logger.info(f"Stored product {product_id} in vector DB with {len(stored_image_paths)} images")
                except Exception as e:
                    logger.error(f"Failed to store product {product_id} in vector DB: {str(e)}", exc_info=True)
                    continue
                    
            except Exception as e:
                logger.error(f"Failed to process product: {str(e)}", exc_info=True)
                continue
        
        logger.info(
            f"Ingestion complete: {products_processed} products processed, "
            f"{images_stored} images stored"
        )
        
        return {
            "status": "success",
            "products_processed": products_processed,
            "images_stored": images_stored,
            "collection_name": vector_db_service.collection_name,
            "product_ids": processed_product_ids,
        }
        
    finally:
        # Cleanup extracted directory if requested
        if cleanup_extracted:
            try:
                cleanup_directory(str(extracted_dir))
                logger.info(f"Cleaned up extracted directory: {extracted_dir}")
            except Exception as e:
                logger.warning(f"Failed to cleanup extracted directory: {str(e)}")

