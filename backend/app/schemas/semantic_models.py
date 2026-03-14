"""Pydantic models for Campaign and EmailAnalysis with semantic text conversion.

These models provide structured representations of campaign and email analysis data
that can be converted to semantic text for use in vector databases, embeddings, and LLM processing.

Example usage:
    ```python
    from app.schemas.semantic_models import CampaignSemantic, EmailAnalysisSemantic
    
    # Create from dictionary (e.g., from database or API response)
    campaign_data = {
        "campaign_id": "camp_123",
        "campaign_name": "Summer Sale",
        "subject": "50% Off Summer Collection",
        "open_rate": "25.5%",
        "click_rate": "5.2%",
        "revenue": 15000.0,
        "products_promoted": ["product_1", "product_2"],
        "email_analyses": [...]
    }
    
    campaign = CampaignSemantic.from_dict(campaign_data)
    
    # Convert to semantic text for embeddings
    semantic_text = campaign.to_semantic_text()
    
    # Use with vector database
    embedding = vector_db_service.create_embedding(semantic_text)
    ```
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EmailAnalysisSemantic(BaseModel):
    """Email analysis data for semantic representation with visual element properties."""
    image_id: str = Field(..., description="Unique image identifier")
    campaign_id: Optional[str] = Field(None, description="Associated campaign ID")
    image_path: Optional[str] = Field(None, description="Path to image file")
    image_url: Optional[str] = Field(None, description="URL to image")
    
    # Visual element properties
    header: Optional[Dict[str, Any]] = Field(None, description="Header section with logo and navigation")
    hero_image: Optional[Dict[str, Any]] = Field(None, description="Hero image section")
    call_to_action_button: Optional[Dict[str, Any]] = Field(None, description="Call to action button")
    product_images: Optional[List[Dict[str, Any]]] = Field(None, description="Product images")
    footer: Optional[Dict[str, Any]] = Field(None, description="Footer section")
    background: Optional[Dict[str, Any]] = Field(None, description="Background colors and typography")
    layout_structure: Optional[List[str]] = Field(None, description="Layout structure description")
    
    # General analysis fields
    dominant_colors: Optional[List[str]] = Field(None, description="Dominant colors")
    composition_analysis: Optional[str] = Field(None, description="Composition analysis")
    text_content: Optional[str] = Field(None, description="Extracted text")
    overall_description: Optional[str] = Field(None, description="Overall description")
    marketing_relevance: Optional[str] = Field(None, description="Marketing insights")
    design_tone: Optional[str] = Field(None, description="Design tone/style")
    products: Optional[List[str]] = Field(None, description="Products shown in email")
    brightness: Optional[float] = Field(None, description="Image brightness")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmailAnalysisSemantic":
        """Create EmailAnalysisSemantic from dictionary."""
        # Handle nested analysis structure

        email_visual_elements = data.get("visual_elements", {}) if data else {}
        
        # Extract visual elements from structured format
        header = next((item for item in email_visual_elements if item["element_type"] == "logo"), None)
        hero_image = next((item for item in email_visual_elements if item["element_type"] == "hero_image"), None)
        call_to_action_button = next((item for item in email_visual_elements if item["element_type"] == "cta_button"), None)
        footer = next((item for item in email_visual_elements if item["element_type"] == "footer"), None)
        product_images = [item for item in email_visual_elements if item["element_type"] == "product_image"]
        
        layout_structure = next((item for item in email_visual_elements if item["element_type"] == "layout_structure"), None)
        background = next((item for item in email_visual_elements if item["element_type"] == "background"), None)
        design_tone =next((item for item in email_visual_elements if item["element_type"] == "design_tone"), None)
                
        
        # Extract products from various possible locations
        products = data.get("products") or []
        if isinstance(products, str):
            products = [products]
        elif not isinstance(products, list):
            products = []
        
        # Also check hero_image for products
        if hero_image and isinstance(hero_image, dict):
            hero_products = hero_image.get("products", [])
            if hero_products:
                if isinstance(hero_products, list):
                    products.extend([str(p) for p in hero_products])
                else:
                    products.append(str(hero_products))
        
        if product_images and isinstance(product_images, dict):
            product_images_products = product_images.get("products", [])
            if product_images_products:
                if isinstance(product_images_products, list):
                    products.extend([str(p) for p in product_images_products])
                else:
                    products.append(str(product_images_products))


        return cls(
            image_id=data.get("image_id", ""),
            campaign_id=data.get("campaign_id"),
            image_path=data.get("image_path"),
            image_url=data.get("image_url"),
            header=header,
            hero_image=hero_image,
            call_to_action_button=call_to_action_button,
            product_images=product_images,
            footer=footer,
            background=background,
            layout_structure=layout_structure,
            dominant_colors=data.get("dominant_colors"),
            composition_analysis=data.get("composition_analysis"),
            text_content=data.get("text_content"),
            overall_description=data.get("overall_description"),
            marketing_relevance=data.get("marketing_relevance") or data.get("design_tone"),
            design_tone=design_tone,
            products=list(set(products)) if products else None,  # Remove duplicates
            brightness=data.get("brightness"),
            created_at=data.get("created_at"),
        )
    
    def _dict_to_semantic_text(self, data: Dict[str, Any], prefix: str = "") -> List[str]:
        """Recursively convert dictionary to semantic text, including all fields."""
        parts = []
        for key, value in data.items():
            if value is None or value == "":
                continue
            
            field_name = f"{prefix}.{key}" if prefix else key
            field_name = field_name.replace("_", " ").title()
            
            if isinstance(value, dict):
                # Recursively process nested dictionaries
                nested_parts = self._dict_to_semantic_text(value, f"{prefix}.{key}" if prefix else key)
                parts.extend(nested_parts)
            elif isinstance(value, list):
                if value:
                    # Format lists appropriately
                    if all(isinstance(item, (str, int, float)) for item in value):
                        parts.append(f"{field_name}: {', '.join([str(v) for v in value])}")
                    elif all(isinstance(item, dict) for item in value):
                        # List of dictionaries - process each one
                        for i, item in enumerate(value):
                            item_parts = self._dict_to_semantic_text(item, f"{prefix}.{key}[{i}]" if prefix else f"{key}[{i}]")
                            parts.extend(item_parts)
                    else:
                        parts.append(f"{field_name}: {', '.join([str(v) for v in value])}")
            else:
                # Simple value
                parts.append(f"{field_name}: {value}")
        
        return parts
    
    def to_semantic_text(self, include_metadata: bool = True) -> str:
        """
        Convert email analysis to semantic text for embeddings.
        Includes ALL details from the analysis, not just summaries.
        
        Args:
            include_metadata: Whether to include metadata fields like image_id, path, etc.
            
        Returns:
            Semantic text representation with all analysis details
        """
        parts = []
        
        if include_metadata:
            if self.image_id:
                parts.append(f"Image ID: {self.image_id}")
            if self.campaign_id:
                parts.append(f"Campaign: {self.campaign_id}")
        
        # Overall description
        if self.overall_description:
            parts.append(f"Description: {self.overall_description}")
        
        # Marketing relevance / Design tone
        if self.marketing_relevance:
            parts.append(f"Marketing Insights: {self.marketing_relevance}")
        if self.design_tone:
            parts.append(f"Design Tone: {self.design_tone}")
        
        # Header section - include ALL fields
        if self.header:
            parts.append("Header Section:")
            if isinstance(self.header, dict):
                header_parts = self._dict_to_semantic_text(self.header, "header")
                # Indent header details
                parts.extend([f"  {p}" for p in header_parts])
            else:
                parts.append(f"  {self.header}")
        
        # Hero image section - include ALL fields
        if self.hero_image:
            parts.append("Hero Image Section:")
            if isinstance(self.hero_image, dict):
                hero_parts = self._dict_to_semantic_text(self.hero_image, "hero_image")
                # Indent hero image details
                parts.extend([f"  {p}" for p in hero_parts])
            else:
                parts.append(f"  {self.hero_image}")
        
        # Call to action button - include ALL fields
        if self.call_to_action_button:
            parts.append("Call To Action Button:")
            if isinstance(self.call_to_action_button, dict):
                cta_parts = self._dict_to_semantic_text(self.call_to_action_button, "call_to_action_button")
                # Indent CTA details
                parts.extend([f"  {p}" for p in cta_parts])
            else:
                parts.append(f"  {self.call_to_action_button}")
        
        # Product images - include ALL fields for each
        if self.product_images:
            parts.append("Product Images:")
            for i, prod_img in enumerate(self.product_images[:20]):  # Limit to top 20
                if isinstance(prod_img, dict):
                    parts.append(f"  Product Image {i + 1}:")
                    prod_parts = self._dict_to_semantic_text(prod_img, f"product_images[{i}]")
                    # Double indent product image details
                    parts.extend([f"    {p}" for p in prod_parts])
                else:
                    parts.append(f"  Product Image {i + 1}: {prod_img}")
        
        # Footer - include ALL fields
        if self.footer:
            parts.append("Footer Section:")
            if isinstance(self.footer, dict):
                footer_parts = self._dict_to_semantic_text(self.footer, "footer")
                # Indent footer details
                parts.extend([f"  {p}" for p in footer_parts])
            else:
                parts.append(f"  {self.footer}")
        
        # Background - include ALL fields
        if self.background:
            parts.append("Background:")
            if isinstance(self.background, dict):
                background_parts = self._dict_to_semantic_text(self.background, "background")
                # Indent background details
                parts.extend([f"  {p}" for p in background_parts])
            else:
                parts.append(f"  {self.background}")
        
        # Layout structure
        if self.layout_structure:
            if isinstance(self.layout_structure, list):
                layout_str = "; ".join([str(item) for item in self.layout_structure])
                parts.append(f"Layout Structure: {layout_str}")
            else:
                parts.append(f"Layout Structure: {self.layout_structure}")
        
        # Composition analysis
        if self.composition_analysis:
            parts.append(f"Composition Analysis: {self.composition_analysis}")
        
        # Dominant colors
        if self.dominant_colors:
            colors_str = ", ".join([str(c) for c in self.dominant_colors])
            parts.append(f"Dominant Colors: {colors_str}")
        
        # Products (general)
        if self.products:
            products_str = ", ".join([str(p) for p in self.products])
            parts.append(f"Products: {products_str}")
        
        # Text content
        if self.text_content:
            # Truncate very long text but keep more than before
            text = self.text_content[:1000] if len(self.text_content) > 1000 else self.text_content
            parts.append(f"Text Content: {text}")
        
        # Brightness
        if self.brightness is not None:
            parts.append(f"Image Brightness: {self.brightness:.1f}")
        
        return "\n".join(parts)


class CampaignSemantic(BaseModel):
    """Campaign data for semantic representation."""
    campaign_id: str = Field(..., description="Unique campaign identifier")
    campaign_name: Optional[str] = Field(None, description="Campaign name")
    subject: Optional[str] = Field(None, description="Email subject line")
    tags: Optional[str] = Field(None, description="Campaign tags")
    list: Optional[str] = Field(None, description="Email list")
    send_time: Optional[str] = Field(None, description="Send time")
    send_weekday: Optional[str] = Field(None, description="Send weekday")
    campaign_channel: Optional[str] = Field(None, description="Campaign channel")
    
    # Performance metrics
    open_rate: Optional[str] = Field(None, description="Open rate percentage")
    click_rate: Optional[str] = Field(None, description="Click rate percentage")
    revenue: Optional[float] = Field(None, description="Revenue generated")
    total_recipients: Optional[float] = Field(None, description="Total recipients")
    unique_opens: Optional[float] = Field(None, description="Unique opens")
    unique_clicks: Optional[float] = Field(None, description="Unique clicks")
    placed_order_rate: Optional[str] = Field(None, description="Placed order rate")
    unique_placed_order: Optional[float] = Field(None, description="Unique orders placed")
    unsubscribes: Optional[float] = Field(None, description="Unsubscribes")
    spam_complaints: Optional[float] = Field(None, description="Spam complaints")
    bounce_rate: Optional[str] = Field(None, description="Bounce rate")
    
    # Related data
    products_promoted: Optional[List[str]] = Field(None, description="Products promoted")
    email_analyses: List[EmailAnalysisSemantic] = Field(default_factory=list, description="Email analyses")
    total_email_analyses: int = Field(0, description="Total number of email analyses")
    experiment_run_id: Optional[str] = Field(None, description="Experiment run ID")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CampaignSemantic":
        """Create CampaignSemantic from dictionary."""
        # Convert email analyses (from "images" or "email_analyses" key)
        email_analyses = []
        images_data = data.get("images") or data.get("email_analyses", [])
        
        for img_data in images_data:
            if isinstance(img_data, dict):
                email_analyses.append(EmailAnalysisSemantic.from_dict(img_data))
            elif isinstance(img_data, EmailAnalysisSemantic):
                email_analyses.append(img_data)
        
        # Extract products from various possible locations
        products = data.get("products_promoted") or data.get("products") or []
        if isinstance(products, str):
            products = [products]
        elif not isinstance(products, list):
            products = []
        else:
            # Flatten nested lists (e.g., [['product1'], ['product2']] -> ['product1', 'product2'])
            flattened = []
            for item in products:
                if isinstance(item, list):
                    flattened.extend([str(p) for p in item if p])
                elif item:
                    flattened.append(str(item))
            products = flattened
        
        return cls(
            campaign_id=data.get("campaign_id", ""),
            campaign_name=data.get("campaign_name"),
            subject=data.get("subject"),
            tags=data.get("tags"),
            list=data.get("list"),
            send_time=data.get("send_time"),
            send_weekday=data.get("send_weekday"),
            campaign_channel=data.get("campaign_channel"),
            open_rate=data.get("open_rate"),
            click_rate=data.get("click_rate"),
            revenue=data.get("revenue"),
            total_recipients=data.get("total_recipients"),
            unique_opens=data.get("unique_opens"),
            unique_clicks=data.get("unique_clicks"),
            placed_order_rate=data.get("placed_order_rate"),
            unique_placed_order=data.get("unique_placed_order"),
            unsubscribes=data.get("unsubscribes"),
            spam_complaints=data.get("spam_complaints"),
            bounce_rate=data.get("bounce_rate"),
            products_promoted=products,
            email_analyses=email_analyses,
            total_email_analyses=len(email_analyses) or data.get("total_email_analyses", 0),
            experiment_run_id=data.get("experiment_run_id"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
    
    def to_semantic_text(self, include_metadata: bool = True, include_emails: bool = True) -> str:
        """
        Convert campaign to semantic text for embeddings.
        
        Args:
            include_metadata: Whether to include metadata fields like campaign_id, timestamps, etc.
            include_emails: Whether to include detailed email analysis information
            
        Returns:
            Semantic text representation
        """
        parts = []
        
        if include_metadata:
            if self.campaign_id:
                parts.append(f"Campaign ID: {self.campaign_id}")
        
        # Campaign name
        if self.campaign_name:
            parts.append(f"Campaign: {self.campaign_name}")
        
        # Subject line
        if self.subject:
            parts.append(f"Subject: {self.subject}")
        
        # Campaign metadata
        metadata_parts = []
        if self.tags:
            metadata_parts.append(f"tags: {self.tags}")
        if self.list:
            metadata_parts.append(f"list: {self.list}")
        if self.send_time:
            metadata_parts.append(f"sent: {self.send_time}")
        if self.send_weekday:
            metadata_parts.append(f"weekday: {self.send_weekday}")
        if self.campaign_channel:
            metadata_parts.append(f"channel: {self.campaign_channel}")
        if metadata_parts:
            parts.append(f"Campaign details: {', '.join(metadata_parts)}")
        
        # Performance metrics
        metrics_parts = []
        if self.open_rate:
            metrics_parts.append(f"Open rate: {self.open_rate}")
        if self.click_rate:
            metrics_parts.append(f"Click rate: {self.click_rate}")
        if self.revenue is not None:
            metrics_parts.append(f"Revenue: ${self.revenue:,.2f}")
        if self.placed_order_rate:
            metrics_parts.append(f"Order rate: {self.placed_order_rate}")
        if self.unique_placed_order:
            metrics_parts.append(f"Orders: {self.unique_placed_order}")
        if self.total_recipients:
            metrics_parts.append(f"Recipients: {self.total_recipients:,.0f}")
        if self.unique_opens:
            metrics_parts.append(f"Opens: {self.unique_opens:,.0f}")
        if self.unique_clicks:
            metrics_parts.append(f"Clicks: {self.unique_clicks:,.0f}")
        if self.bounce_rate:
            metrics_parts.append(f"Bounce rate: {self.bounce_rate}")
        
        if metrics_parts:
            parts.append(f"Performance: {'. '.join(metrics_parts)}")
        
        # Products promoted
        if self.products_promoted:
            products_str = ", ".join([str(p) for p in self.products_promoted[:20]])
            parts.append(f"Products promoted: {products_str}")
        
        # Email analyses
        if self.email_analyses and include_emails:
            parts.append(f"Email analyses ({len(self.email_analyses)} emails):")
            for i, email_analysis in enumerate(self.email_analyses[:5], 1):  # Limit to top 5
                parts.append(f"\nEmail {i}:")
                email_text = email_analysis.to_semantic_text(include_metadata=False)
                # Indent email analysis
                indented_lines = ["  " + line for line in email_text.split("\n")]
                parts.extend(indented_lines)
        
        # Summary of email characteristics if many emails
        if self.email_analyses and len(self.email_analyses) > 5:
            # Aggregate information from all emails
            all_colors = []
            all_products = []
            design_tones = []
            cta_texts = []
            
            for email in self.email_analyses:
                if email.dominant_colors:
                    all_colors.extend(email.dominant_colors)
                if email.products:
                    all_products.extend(email.products)
                if email.design_tone:
                    design_tones.append(email.design_tone)
                if email.call_to_action_button and isinstance(email.call_to_action_button, dict):
                    cta_text = email.call_to_action_button.get("text")
                    if cta_text:
                        cta_texts.append(cta_text)
            
            if all_colors:
                unique_colors = list(set(all_colors))[:10]
                parts.append(f"Overall color palette: {', '.join(unique_colors)}")
            if all_products:
                unique_products = list(set([str(p) for p in all_products]))[:10]
                parts.append(f"All products shown: {', '.join(unique_products)}")
            if design_tones:
                unique_tones = list(set(design_tones))
                parts.append(f"Design tones: {', '.join(unique_tones)}")
            if cta_texts:
                unique_ctas = list(set(cta_texts))[:5]
                parts.append(f"CTA buttons: {', '.join(unique_ctas)}")
        
        return "\n".join(parts)
