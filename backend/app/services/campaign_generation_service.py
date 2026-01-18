"""Service for generating email campaigns using AI."""
import json
import logging
from operator import truediv
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlalchemy import text

from ..core.config import settings
from ..db.session import engine
from ..schemas.campaigns import EmailCampaignResponse, EmailContent, PastCampaignReference
from .html_template_service import HTMLTemplateService
from .image_generation_service import ImageGenerationService
from .comfyui_cloud_service import ComfyUICloudService
from .intelligence_service import IntelligenceService
from .llm_service import LLMService
from .rag_campaign_service import RAGCampaignService

logger = logging.getLogger(__name__)


class CampaignGenerationService:
    """Service for generating email campaigns."""

    def __init__(self) -> None:
        """Initialize the campaign generation service."""
        self.intelligence_service = IntelligenceService()
        self.llm_service = self.intelligence_service.llm_service
        self.rag_service = RAGCampaignService()
        self.html_service = HTMLTemplateService()
        # Use ComfyUI Cloud for image generation (fallback to local if needed)
        try:
            self.comfyui_cloud_service = ComfyUICloudService()
            logger.info("ComfyUI Cloud service initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize ComfyUI Cloud service: {str(e)}. Will use local ComfyUI if available.")
            self.comfyui_cloud_service = None
        # Keep local ComfyUI service as fallback
        self.image_service = ImageGenerationService()

    def generate_email_campaign(
        self,
        campaign_name: Optional[str],
        objective: str,
        audience_segment: Optional[str] = None,
        products: Optional[List[str]] = None,
        product_images: Optional[List[str]] = None,
        tone: str = "professional",
        key_message: Optional[str] = None,
        call_to_action: Optional[str] = None,
        include_promotion: bool = False,
        promotion_details: Optional[str] = None,
        subject_line_suggestions: int = 3,
        include_preview_text: bool = True,
        design_guidance: Optional[str] = None,
        use_past_campaigns: bool = True,
        num_similar_campaigns: int = 5,
        generate_hero_image: bool = False,
        hero_image_prompt: Optional[str] = None,
    ) -> EmailCampaignResponse:
        """
        Generate a complete email campaign using AI with RAG from past campaigns.
        
        Args:
            campaign_name: Name for the campaign
            objective: Campaign objective
            audience_segment: Target audience
            products: Products to promote
            product_images: URLs/paths to product images
            tone: Email tone
            key_message: Key message/value proposition
            call_to_action: Desired CTA text
            include_promotion: Whether to include promotions
            promotion_details: Promotion details
            subject_line_suggestions: Number of subject line variations
            include_preview_text: Whether to generate preview text
            design_guidance: Design preferences
            use_past_campaigns: Whether to use RAG to retrieve past campaigns
            num_similar_campaigns: Number of similar campaigns to retrieve
            generate_hero_image: Whether to generate a hero image
            hero_image_prompt: Custom prompt for hero image generation
            
        Returns:
            EmailCampaignResponse with generated content including HTML template
        """
        if not self.llm_service:
            raise ValueError("LLM service not available. Please configure API keys.")

        campaign_id = str(uuid.uuid4())
        final_campaign_name = campaign_name or f"Campaign {campaign_id[:8]}"

        logger.info(f"Generating email campaign: id={campaign_id}, objective={objective}")

        # Stage 1: RAG for Hero Image Generation
        hero_image_url = None
        
        logger.info("Stage 1: Building RAG prompt for hero image generation")
        hero_image_prompt = self._build_hero_image_rag_prompt(
            objective=objective,
            products=products,
            product_images=product_images,
            tone=tone,
            design_guidance=design_guidance,
            hero_image_prompt=hero_image_prompt,
            use_past_campaigns=use_past_campaigns,
            num_similar_campaigns=num_similar_campaigns,
        )
        # Get settings from config
        workflow_override = None
        if settings.comfyui_workflow_path:
            workflow_override = settings.comfyui_workflow_path
            logger.info(f"Using workflow override from config: {workflow_override}")                
        
        # Generate hero image using image generation service
        try:
            hero_image_url = self.image_service.generate_hero_image(
                prompt=hero_image_prompt,
                style=tone,
                workflow_override=workflow_override,
                size=settings.comfyui_hero_image_size,
            )
            if hero_image_url:
                logger.info(f"Successfully generated hero image: {hero_image_url}")
            else:
                logger.warning("Hero image generation returned None, continuing without hero image")
        except Exception as e:
            logger.error(f"Failed to generate hero image: {str(e)}", exc_info=True)
            # Continue without hero image if generation fails
            hero_image_url = None

        # Stage 2: RAG for Email Content Generation
        logger.info("Stage 2: Building RAG prompt for email content generation")
        email_content_prompt = self._build_email_content_rag_prompt(
            objective=objective,
            audience_segment=audience_segment,
            products=products,
            tone=tone,
            key_message=key_message,
            call_to_action=call_to_action,
            include_promotion=include_promotion,
            promotion_details=promotion_details,
            subject_line_suggestions=subject_line_suggestions,
            include_preview_text=include_preview_text,
            design_guidance=design_guidance,
            use_past_campaigns=use_past_campaigns,
            num_similar_campaigns=num_similar_campaigns,
        )

        # Step 4: Generate email content using LLM
        email_data = self._generate_email_content(email_content_prompt)

        logger.debug(f"Generated email content: {email_data}")

        # Generate subject line variations
        subject_line_variations = self._generate_subject_lines(
            objective=objective,
            key_message=key_message,
            products=products,
            count=subject_line_suggestions,
        )

        # Step 5: Generate design recommendations (reuse insights from email content RAG)
        # Retrieve insights again for design recommendations
        design_campaign_insights = {}
        if use_past_campaigns:
            design_query = f"{objective} {tone} design visual style"
            design_past_campaigns = self.rag_service.retrieve_similar_campaigns(
                query=design_query,
                objective=objective,
                tone=tone,
                num_results=num_similar_campaigns,
            )
            if design_past_campaigns:
                design_campaign_insights = self.rag_service.extract_campaign_insights(design_past_campaigns)
        
        design_recommendations = self._generate_design_recommendations_with_rag(
            objective=objective,
            tone=tone,
            design_guidance=design_guidance,
            campaign_insights=design_campaign_insights,
        )

        # Step 6: Generate talking points
        talking_points = self._generate_talking_points(
            objective=objective,
            products=products,
            key_message=key_message,
        )

        # Step 7: Build email content object
        email_content = EmailContent(
            subject_line=email_data.get("subject_line", subject_line_variations[0] if subject_line_variations else "New Campaign"),
            preview_text=email_data.get("preview_text") if include_preview_text else None,
            greeting=email_data.get("greeting", "Hello,"),
            body=email_data.get("body", ""),
            call_to_action=email_data.get("call_to_action", call_to_action or "Learn More"),
            closing=email_data.get("closing", "Best regards,"),
            footer=email_data.get("footer"),
            hero_image_url=hero_image_url,
            product_image_urls=product_images,
        )

        # Step 8: Generate HTML template
        html_template = self.html_service.generate_email_template(
            subject_line=email_content.subject_line,
            preview_text=email_content.preview_text,
            greeting=email_content.greeting,
            body=email_content.body,
            call_to_action=email_content.call_to_action,
            closing=email_content.closing,
            footer=email_content.footer,
            hero_image_url=hero_image_url,
            product_image_urls=product_images,
            tone=tone,
        )
        email_content.html_template = html_template

        # Step 9: Store campaign in database
        self._store_campaign(
            campaign_id=campaign_id,
            campaign_name=final_campaign_name,
            objective=objective,
            audience_segment=audience_segment,
            email_content=email_content,
            subject_line_variations=subject_line_variations,
            design_recommendations=design_recommendations,
            talking_points=talking_points,
        )

        return EmailCampaignResponse(
            campaign_id=campaign_id,
            campaign_name=final_campaign_name,
            objective=objective,
            audience_segment=audience_segment,
            email_content=email_content,
            subject_line_variations=subject_line_variations,
            design_recommendations=design_recommendations,
            talking_points=talking_points,
            past_campaign_references=[],  # TODO: Populate from RAG results if needed
            expected_metrics={
                "estimated_open_rate": "20-25%",
                "estimated_click_rate": "3-5%",
                "estimated_conversion_rate": "1-2%",
            },
        )

    def _build_hero_image_rag_prompt(
        self,
        objective: str,
        products: Optional[List[str]],
        product_images: Optional[List[str]],
        tone: str,
        design_guidance: Optional[str],
        hero_image_prompt: Optional[str],
        use_past_campaigns: bool,
        num_similar_campaigns: int,
    ) -> str:
        """
        Build RAG-enhanced prompt for hero image generation.
        
        Stage 1: Focuses on visual/image aspects from past campaigns.
        
        Args:
            objective: Campaign objective
            products: Products to feature
            product_images: Product image URLs/paths
            tone: Visual tone/style
            design_guidance: Design preferences
            hero_image_prompt: Custom prompt override
            use_past_campaigns: Whether to use RAG
            num_similar_campaigns: Number of campaigns to retrieve
            
        Returns:
            Enhanced prompt string for hero image generation
        """
        prompt_parts = []
        
        # Base prompt from user input or objective
        if hero_image_prompt:
            prompt_parts.append(hero_image_prompt)
        else:
            prompt_parts.append(f"{objective} email hero image")
        
        # Add product information
        if products:
            prompt_parts.append(f"featuring {', '.join(products[:2])}")
        
        # Add product images context if available
        if product_images:
            prompt_parts.append(f"inspired by product images: {len(product_images)} product(s)")
        
        # Retrieve visual-focused RAG insights
        visual_insights = {}
        visual_past_campaigns = []
        if use_past_campaigns:
            # Build query focused on visual aspects
            visual_query = f"{objective} hero image visual style"
            if products:
                visual_query += f" {', '.join(products[:2])}"
            if tone:
                visual_query += f" {tone} tone"
            
            logger.info(f"Retrieving visual-focused campaigns for hero image: {visual_query}")
            visual_past_campaigns = self.rag_service.retrieve_similar_campaigns(
                query=visual_query,
                objective=objective,
                products=products,
                tone=tone,
                num_results=num_similar_campaigns,
            )
            
            if visual_past_campaigns:
                visual_insights = self.rag_service.extract_campaign_insights(visual_past_campaigns)
                logger.info(f"Extracted visual insights: {len(visual_insights.get('color_palettes', []))} colors, {len(visual_insights.get('visual_elements', []))} visual elements")
        
        # Enhance with visual insights from past campaigns
        if visual_insights:
            # Add color palette insights
            if visual_insights.get("color_palettes"):
                top_colors = visual_insights["color_palettes"][:3]
                prompt_parts.append(f"using colors: {', '.join(top_colors)}")
            
            # Add visual element insights
            if visual_insights.get("visual_elements"):
                top_elements = visual_insights["visual_elements"][:2]
                prompt_parts.append(f"with visual style: {', '.join(top_elements)}")
            
            # Add image references if available
            if visual_past_campaigns:
                image_refs = self.rag_service.get_campaign_image_references(visual_past_campaigns)
                if image_refs:
                    # Reference successful visual styles
                    prompt_parts.append("inspired by successful email hero image designs")
        
        # Add design guidance if provided
        if design_guidance:
            prompt_parts.append(f"design style: {design_guidance[:100]}")
        
        # Add standard hero image requirements
        prompt_parts.append("high quality, marketing email hero image, professional photography")
        prompt_parts.append(f"{tone} style")
        
        # Combine all parts into final prompt
        hero_prompt = ", ".join(prompt_parts)
        logger.debug(f"Hero image RAG prompt: {hero_prompt[:200]}...")
        
        return hero_prompt
    
    def _build_email_content_rag_prompt(
        self,
        objective: str,
        audience_segment: Optional[str],
        products: Optional[List[str]],
        tone: str,
        key_message: Optional[str],
        call_to_action: Optional[str],
        include_promotion: bool,
        promotion_details: Optional[str],
        subject_line_suggestions: int,
        include_preview_text: bool,
        design_guidance: Optional[str],
        use_past_campaigns: bool,
        num_similar_campaigns: int,
    ) -> str:
        """
        Build RAG-enhanced prompt for email content generation.
        
        Stage 2: Focuses on text/content aspects from past campaigns.
        
        Args:
            objective: Campaign objective
            audience_segment: Target audience
            products: Products to promote
            tone: Email tone
            key_message: Key message/value proposition
            call_to_action: Desired CTA text
            include_promotion: Whether to include promotions
            promotion_details: Promotion details
            subject_line_suggestions: Number of subject line variations
            include_preview_text: Whether to generate preview text
            design_guidance: Design preferences
            use_past_campaigns: Whether to use RAG
            num_similar_campaigns: Number of campaigns to retrieve
            
        Returns:
            Enhanced prompt string for email content generation
        """
        prompt_parts = [
            "Generate a complete email campaign with the following requirements:",
            f"Objective: {objective}",
        ]

        if audience_segment:
            prompt_parts.append(f"Target Audience: {audience_segment}")

        if products:
            prompt_parts.append(f"Products to Promote: {', '.join(products)}")

        prompt_parts.append(f"Tone: {tone}")

        if key_message:
            prompt_parts.append(f"Key Message: {key_message}")

        if call_to_action:
            prompt_parts.append(f"Call to Action: {call_to_action}")

        if include_promotion and promotion_details:
            prompt_parts.append(f"Promotion: {promotion_details}")

        if design_guidance:
            prompt_parts.append(f"Design Guidance: {design_guidance}")

        # Retrieve text-focused RAG insights
        campaign_insights = {}
        past_campaign_text_samples = []
        if use_past_campaigns:
            # Build query focused on text/content aspects
            content_query = f"{objective} email content copywriting"
            if products:
                content_query += f" {', '.join(products[:2])}"
            if tone:
                content_query += f" {tone} tone"
            
            logger.info(f"Retrieving content-focused campaigns for email: {content_query}")
            content_past_campaigns = self.rag_service.retrieve_similar_campaigns(
                query=content_query,
                objective=objective,
                products=products,
                tone=tone,
                num_results=num_similar_campaigns,
            )
            
            if content_past_campaigns:
                campaign_insights = self.rag_service.extract_campaign_insights(content_past_campaigns)
                past_campaign_text_samples = self.rag_service.get_campaign_text_samples(
                    content_past_campaigns,
                    max_samples=5
                )
                logger.info(f"Extracted content insights: {len(past_campaign_text_samples)} text samples, {len(campaign_insights.get('text_patterns', []))} text patterns")

        # Add RAG insights
        if campaign_insights:
            prompt_parts.append("\n--- Insights from Past Successful Campaigns ---")
            
            if campaign_insights.get("color_palettes"):
                prompt_parts.append(f"Successful color palettes used: {', '.join(campaign_insights['color_palettes'][:5])}")
            
            if campaign_insights.get("text_patterns"):
                prompt_parts.append(f"Text patterns from successful campaigns:")
                for pattern in campaign_insights["text_patterns"][:3]:
                    prompt_parts.append(f"  - {pattern[:100]}")
            
            if campaign_insights.get("cta_styles"):
                prompt_parts.append("CTA styles that worked well:")
                for cta in campaign_insights["cta_styles"][:3]:
                    prompt_parts.append(f"  - {cta.get('text', '')} ({cta.get('color', '')})")
            
            if campaign_insights.get("subject_line_patterns"):
                prompt_parts.append("Subject line patterns that performed well:")
                for pattern in campaign_insights["subject_line_patterns"][:3]:
                    prompt_parts.append(f"  - {pattern[:100]}")

        if past_campaign_text_samples:
            prompt_parts.append("\n--- Text Samples from Past Campaigns (for inspiration) ---")
            for sample in past_campaign_text_samples[:3]:
                prompt_parts.append(f"  - {sample[:150]}")

        prompt_parts.append("\nGenerate the following components:")
        prompt_parts.append("- Subject line (compelling and clear, inspired by successful patterns)")
        if include_preview_text:
            prompt_parts.append("- Preview text (engaging, 50-100 characters)")
        prompt_parts.append("- Greeting (personalized if possible)")
        prompt_parts.append("- Body (2-3 paragraphs, engaging and clear, incorporating successful text patterns)")
        prompt_parts.append("- Call to action (clear and action-oriented, using proven CTA styles)")
        prompt_parts.append("- Closing (professional)")
        prompt_parts.append("- Footer (optional, with unsubscribe info)")

        prompt_parts.append("\nReturn the response as a JSON object with keys: subject_line, preview_text (if requested), greeting, body, call_to_action, closing, footer.")

        final_prompt = "\n".join(prompt_parts)
        logger.debug(f"Email content RAG prompt length: {len(final_prompt)} characters")
        
        return final_prompt

    def _build_email_generation_prompt_with_rag(
        self,
        objective: str,
        audience_segment: Optional[str],
        products: Optional[List[str]],
        tone: str,
        key_message: Optional[str],
        call_to_action: Optional[str],
        include_promotion: bool,
        promotion_details: Optional[str],
        subject_line_suggestions: int,
        include_preview_text: bool,
        design_guidance: Optional[str],
        campaign_insights: Dict[str, str],
        past_campaign_text_samples: List[str],
    ) -> str:
        """Build the prompt for email generation with RAG insights."""
        prompt_parts = [
            "Generate a complete email campaign with the following requirements:",
            f"Objective: {objective}",
        ]

        if audience_segment:
            prompt_parts.append(f"Target Audience: {audience_segment}")

        if products:
            prompt_parts.append(f"Products to Promote: {', '.join(products)}")

        prompt_parts.append(f"Tone: {tone}")

        if key_message:
            prompt_parts.append(f"Key Message: {key_message}")

        if call_to_action:
            prompt_parts.append(f"Call to Action: {call_to_action}")

        if include_promotion and promotion_details:
            prompt_parts.append(f"Promotion: {promotion_details}")

        if design_guidance:
            prompt_parts.append(f"Design Guidance: {design_guidance}")

        # Add RAG insights
        if campaign_insights:
            prompt_parts.append("\n--- Insights from Past Successful Campaigns ---")
            
            if campaign_insights.get("color_palettes"):
                prompt_parts.append(f"Successful color palettes used: {', '.join(campaign_insights['color_palettes'][:5])}")
            
            if campaign_insights.get("text_patterns"):
                prompt_parts.append(f"Text patterns from successful campaigns:")
                for pattern in campaign_insights["text_patterns"][:3]:
                    prompt_parts.append(f"  - {pattern[:100]}")
            
            if campaign_insights.get("cta_styles"):
                prompt_parts.append("CTA styles that worked well:")
                for cta in campaign_insights["cta_styles"][:3]:
                    prompt_parts.append(f"  - {cta.get('text', '')} ({cta.get('color', '')})")

        if past_campaign_text_samples:
            prompt_parts.append("\n--- Text Samples from Past Campaigns (for inspiration) ---")
            for sample in past_campaign_text_samples[:3]:
                prompt_parts.append(f"  - {sample[:150]}")

        prompt_parts.append("\nGenerate the following components:")
        prompt_parts.append("- Subject line (compelling and clear, inspired by successful patterns)")
        if include_preview_text:
            prompt_parts.append("- Preview text (engaging, 50-100 characters)")
        prompt_parts.append("- Greeting (personalized if possible)")
        prompt_parts.append("- Body (2-3 paragraphs, engaging and clear, incorporating successful text patterns)")
        prompt_parts.append("- Call to action (clear and action-oriented, using proven CTA styles)")
        prompt_parts.append("- Closing (professional)")
        prompt_parts.append("- Footer (optional, with unsubscribe info)")

        prompt_parts.append("\nReturn the response as a JSON object with keys: subject_line, preview_text (if requested), greeting, body, call_to_action, closing, footer.")

        return "\n".join(prompt_parts)

    def _generate_hero_image_cloud(
        self,
        prompt: str,
        style: str,
        size: str,
        workflow_override: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate a hero image using ComfyUI Cloud.
        
        Args:
            prompt: Text prompt for image generation
            style: Style preference (e.g., "professional", "modern", "vibrant")
            size: Image size (format: "WIDTHxHEIGHT")
            workflow_override: Optional path to workflow JSON file
            
        Returns:
            Path to the generated image, or None if generation failed
        """
        if not self.comfyui_cloud_service or not self.comfyui_cloud_service.api_key:
            logger.warning("ComfyUI Cloud service not available")
            return None
        
        try:
            # Parse size
            width, height = 1024, 1024
            if size:
                try:
                    parts = size.split("x")
                    if len(parts) == 2:
                        width = int(parts[0])
                        height = int(parts[1])
                except (ValueError, IndexError):
                    logger.warning(f"Invalid size format '{size}', using default 1024x1024")
            
            # Enhance prompt with style
            enhanced_prompt = prompt
            if style:
                enhanced_prompt = f"{prompt}, {style} style, high quality, marketing email hero image, professional photography"
            
            # Load workflow if provided
            workflow = None
            if workflow_override:
                import json
                from pathlib import Path
                workflow_path = Path(workflow_override)
                if workflow_path.exists():
                    logger.info(f"Loading workflow from {workflow_path}")
                    with open(workflow_path, "r") as f:
                        workflow_data = json.load(f)
                        # Handle different workflow formats
                        if isinstance(workflow_data, dict):
                            if "workflow" in workflow_data:
                                workflow = workflow_data["workflow"]
                            else:
                                workflow = workflow_data
                else:
                    logger.warning(f"Workflow file not found: {workflow_path}, using default workflow")
            
            # If no workflow provided, use a simple default workflow structure
            # Note: For ComfyUI Cloud, you'll need to provide a workflow that matches available nodes
            # This is a simplified example - you may need to adjust based on your workflow
            if not workflow:
                logger.info("No workflow provided, ComfyUI Cloud requires a workflow file. Skipping image generation.")
                return None
            
            # Modify workflow to use our prompt
            # Find text encode node and update prompt
            # This assumes the workflow has a CLIPTextEncode node (adjust node IDs as needed)
            workflow = self._modify_workflow_prompt(workflow, enhanced_prompt, width, height)
            
            # Submit workflow to ComfyUI Cloud
            logger.info(f"Submitting workflow to ComfyUI Cloud with prompt: {enhanced_prompt[:100]}...")
            submit_result = self.comfyui_cloud_service.submit_workflow(workflow)
            prompt_id = submit_result["prompt_id"]
            logger.info(f"Workflow submitted, prompt_id: {prompt_id}")
            
            # Wait for completion
            logger.info("Waiting for image generation to complete...")
            status_info = self.comfyui_cloud_service.wait_for_completion(prompt_id, timeout=settings.comfyui_cloud_timeout)
            
            if status_info["status"] != "success":
                raise RuntimeError(f"Workflow did not complete successfully: {status_info}")
            
            # Extract and download generated images
            history_entry = status_info.get("history")
            if not history_entry:
                raise ValueError("No history found in completed workflow")
            
            output_files = self.comfyui_cloud_service.extract_outputs_from_history(history_entry)
            if not output_files:
                raise ValueError("No output files found in completed workflow")
            
            # Download the first output image
            output_info = output_files[0]
            logger.info(f"Downloading generated image: {output_info['filename']}")
            downloaded_path = self.comfyui_cloud_service.download_output(
                filename=output_info["filename"],
                subfolder=output_info["subfolder"],
                output_type=output_info["type"],
            )
            
            logger.info(f"Successfully generated and downloaded hero image: {downloaded_path}")
            return downloaded_path
            
        except Exception as e:
            logger.error(f"Failed to generate hero image with ComfyUI Cloud: {str(e)}", exc_info=True)
            return None

    def _modify_workflow_prompt(self, workflow: Dict, prompt: str, width: int, height: int) -> Dict:
        """
        Modify a ComfyUI workflow to use the specified prompt and size.
        
        Args:
            workflow: ComfyUI workflow dictionary
            prompt: Text prompt for image generation
            width: Image width
            height: Image height
            
        Returns:
            Modified workflow dictionary
        """
        # Try to find and update text encode nodes
        # This is a basic implementation - you may need to adjust based on your workflow structure
        for node_id, node_data in workflow.items():
            if isinstance(node_data, dict) and node_data.get("class_type") == "CLIPTextEncode":
                # Update positive prompt (usually node with text input)
                if "text" in node_data.get("inputs", {}):
                    # Check if this looks like a positive prompt node
                    # You might want to be more specific about which node to update
                    node_data["inputs"]["text"] = prompt
                    logger.debug(f"Updated CLIPTextEncode node {node_id} with prompt")
            
            # Update image size if EmptyLatentImage node found
            if isinstance(node_data, dict) and node_data.get("class_type") in ["EmptyLatentImage", "EmptySD3LatentImage"]:
                if "inputs" in node_data:
                    node_data["inputs"]["width"] = width
                    node_data["inputs"]["height"] = height
                    logger.debug(f"Updated size in node {node_id} to {width}x{height}")
        
        return workflow

    def _build_email_generation_prompt(
        self,
        objective: str,
        audience_segment: Optional[str],
        products: Optional[List[str]],
        tone: str,
        key_message: Optional[str],
        call_to_action: Optional[str],
        include_promotion: bool,
        promotion_details: Optional[str],
        subject_line_suggestions: int,
        include_preview_text: bool,
        design_guidance: Optional[str],
    ) -> str:
        """Build the prompt for email generation (without RAG)."""
        return self._build_email_content_rag_prompt(
            objective=objective,
            audience_segment=audience_segment,
            products=products,
            tone=tone,
            key_message=key_message,
            call_to_action=call_to_action,
            include_promotion=include_promotion,
            promotion_details=promotion_details,
            subject_line_suggestions=subject_line_suggestions,
            include_preview_text=include_preview_text,
            design_guidance=design_guidance,
            use_past_campaigns=False,
            num_similar_campaigns=0,
        )

    def _generate_email_content(self, prompt: str) -> Dict[str, str]:
        """Generate email content using LLM."""
        if not self.llm_service:
            raise ValueError("LLM service not available")

        try:
            if self.llm_service.provider == "openai":
                return self._generate_email_content_openai(prompt)
            elif self.llm_service.provider == "anthropic":
                return self._generate_email_content_anthropic(prompt)
            elif self.llm_service.provider == "ollama":
                return self._generate_email_content_ollama(prompt)
            else:
                raise ValueError(f"Unsupported LLM provider: {self.llm_service.provider}")
        except Exception as e:
            logger.error(f"Failed to generate email content: {str(e)}", exc_info=True)
            # Return fallback content
            return {
                "subject_line": "New Campaign",
                "preview_text": "Check out our latest offer",
                "greeting": "Hello,",
                "body": "We're excited to share something special with you.",
                "call_to_action": "Learn More",
                "closing": "Best regards,",
                "footer": None,
            }

    def _generate_email_content_openai(self, prompt: str) -> Dict[str, str]:
        """Generate email content using OpenAI."""
        client = self.llm_service._get_openai_client()

        system_prompt = "You are an expert email marketing copywriter. Generate compelling email content that drives engagement and conversions."

        try:
            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.8,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content.strip()
            data = json.loads(content)
            return data
        except Exception as e:
            logger.error(f"OpenAI email generation failed: {str(e)}")
            raise

    def _generate_email_content_anthropic(self, prompt: str) -> Dict[str, str]:
        """Generate email content using Anthropic."""
        client = self.llm_service._get_anthropic_client()

        system_prompt = "You are an expert email marketing copywriter. Generate compelling email content that drives engagement and conversions. Return your response as valid JSON."

        try:
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
            )
            content = response.content[0].text.strip()
            # Try to extract JSON if wrapped in markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            data = json.loads(content)
            return data
        except Exception as e:
            logger.error(f"Anthropic email generation failed: {str(e)}")
            raise

    def _generate_email_content_ollama(self, prompt: str) -> Dict[str, str]:
        """Generate email content using Ollama."""
        client = self.llm_service._get_ollama_client()

        full_prompt = f"{prompt}\n\nReturn ONLY valid JSON, no markdown formatting."

        try:
            response = client.post(
                "/api/chat",
                json={
                    "model": settings.ollama_model,
                    "messages": [{"role": "user", "content": full_prompt}],
                    "stream": False,
                    "options": {
                        "temperature": 0.8,
                        "num_predict": 2000,
                    },
                },
            )
            response.raise_for_status()
            result = response.json()
            content = result["message"]["content"].strip()
            # Try to extract JSON if wrapped in markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            data = json.loads(content)
            return data
        except Exception as e:
            logger.error(f"Ollama email generation failed: {str(e)}")
            raise

    def _generate_subject_lines(
        self,
        objective: str,
        key_message: Optional[str],
        products: Optional[List[str]],
        count: int,
    ) -> List[str]:
        """Generate subject line variations."""
        if not self.llm_service:
            return ["New Campaign", "Special Offer", "Don't Miss Out"][:count]

        prompt = f"Generate {count} compelling email subject lines for a campaign with:\n"
        prompt += f"Objective: {objective}\n"
        if key_message:
            prompt += f"Key Message: {key_message}\n"
        if products:
            prompt += f"Products: {', '.join(products)}\n"
        prompt += "\nReturn as a JSON object with a 'subject_lines' key containing an array of strings. Each subject line should be 30-60 characters and compelling."

        try:
            if self.llm_service.provider == "openai":
                client = self.llm_service._get_openai_client()
                response = client.chat.completions.create(
                    model=settings.openai_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.9,
                    response_format={"type": "json_object"},
                )
                content = response.choices[0].message.content.strip()
                data = json.loads(content)
                subject_lines = data.get("subject_lines", [])
                if isinstance(subject_lines, list):
                    return subject_lines[:count]
                return ["New Campaign", "Special Offer", "Don't Miss Out"][:count]
            elif self.llm_service.provider == "anthropic":
                client = self.llm_service._get_anthropic_client()
                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=300,
                    messages=[{"role": "user", "content": prompt}],
                )
                content = response.content[0].text.strip()
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                data = json.loads(content)
                subject_lines = data.get("subject_lines", [])
                if isinstance(subject_lines, list):
                    return subject_lines[:count]
                return ["New Campaign", "Special Offer", "Don't Miss Out"][:count]
            else:
                # Fallback for other providers
                return ["New Campaign", "Special Offer", "Don't Miss Out"][:count]
        except Exception as e:
            logger.warning(f"Failed to generate subject lines: {str(e)}")
            return ["New Campaign", "Special Offer", "Don't Miss Out"][:count]

    def _generate_design_recommendations_with_rag(
        self,
        objective: str,
        tone: str,
        design_guidance: Optional[str],
        campaign_insights: Dict[str, Any],
    ) -> List[str]:
        """Generate design recommendations with RAG insights."""
        recommendations = []

        # Add recommendations based on RAG insights
        if campaign_insights.get("color_palettes"):
            top_colors = campaign_insights["color_palettes"][:3]
            recommendations.append(f"Use color palette from successful campaigns: {', '.join(top_colors)}")

        if campaign_insights.get("visual_elements"):
            top_elements = campaign_insights["visual_elements"][:3]
            recommendations.append(f"Incorporate successful visual elements: {', '.join(top_elements)}")

        # Tone-based recommendations
        if tone == "urgent":
            recommendations.append("Use bold, high-contrast colors (red, orange) to create urgency")
        elif tone == "professional":
            recommendations.append("Use clean, minimalist design with plenty of white space")
        elif tone == "casual":
            recommendations.append("Use friendly, approachable colors and playful fonts")

        if design_guidance:
            recommendations.append(f"Follow guidance: {design_guidance}")

        recommendations.extend([
            "Include clear, prominent call-to-action button",
            "Use mobile-responsive design",
            "Include high-quality product images",
            "Ensure text is readable with sufficient contrast",
        ])

        return recommendations[:7]

    def _generate_talking_points(
        self,
        objective: str,
        products: Optional[List[str]],
        key_message: Optional[str],
    ) -> List[str]:
        """Generate talking points for the campaign."""
        points = []

        if key_message:
            points.append(key_message)

        if products:
            points.append(f"Highlight products: {', '.join(products[:3])}")

        points.append(f"Focus on: {objective}")

        return points

    def _store_campaign(
        self,
        campaign_id: str,
        campaign_name: str,
        objective: str,
        audience_segment: Optional[str],
        email_content: EmailContent,
        subject_line_variations: List[str],
        design_recommendations: List[str],
        talking_points: List[str],
    ) -> None:
        """Store the generated campaign in the database."""
        try:
            # Ensure table exists
            with engine.begin() as connection:
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS email_campaigns (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        campaign_id TEXT UNIQUE NOT NULL,
                        campaign_name TEXT NOT NULL,
                        objective TEXT NOT NULL,
                        audience_segment TEXT,
                        subject_line TEXT NOT NULL,
                        preview_text TEXT,
                        greeting TEXT,
                        body TEXT NOT NULL,
                        call_to_action TEXT,
                        closing TEXT,
                        footer TEXT,
                        html_template TEXT,
                        hero_image_url TEXT,
                        product_image_urls TEXT,
                        subject_line_variations TEXT,
                        design_recommendations TEXT,
                        talking_points TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT
                    )
                """))
                
                # Insert campaign
                connection.execute(
                    text("""
                        INSERT INTO email_campaigns
                        (campaign_id, campaign_name, objective, audience_segment,
                         subject_line, preview_text, greeting, body, call_to_action,
                         closing, footer, html_template, hero_image_url, product_image_urls,
                         subject_line_variations, design_recommendations,
                         talking_points, created_at)
                        VALUES (:campaign_id, :campaign_name, :objective, :audience_segment,
                                :subject_line, :preview_text, :greeting, :body, :call_to_action,
                                :closing, :footer, :html_template, :hero_image_url, :product_image_urls,
                                :subject_line_variations, :design_recommendations,
                                :talking_points, :created_at)
                    """),
                    {
                        "campaign_id": campaign_id,
                        "campaign_name": campaign_name,
                        "objective": objective,
                        "audience_segment": audience_segment,
                        "subject_line": email_content.subject_line,
                        "preview_text": email_content.preview_text,
                        "greeting": email_content.greeting,
                        "body": email_content.body,
                        "call_to_action": email_content.call_to_action,
                        "closing": email_content.closing,
                        "footer": email_content.footer,
                        "html_template": email_content.html_template,
                        "hero_image_url": email_content.hero_image_url,
                        "product_image_urls": json.dumps(email_content.product_image_urls) if email_content.product_image_urls else None,
                        "subject_line_variations": json.dumps(subject_line_variations),
                        "design_recommendations": json.dumps(design_recommendations),
                        "talking_points": json.dumps(talking_points),
                        "created_at": datetime.utcnow().isoformat(),
                    }
                )
            logger.info(f"Stored campaign in database: campaign_id={campaign_id}")
        except Exception as e:
            logger.warning(f"Failed to store campaign in database: {str(e)}", exc_info=True)
            # Don't fail the request if storage fails

    def list_campaigns(self, limit: int = 20, offset: int = 0) -> List[EmailCampaignResponse]:
        """List all generated campaigns."""
        try:
            with engine.begin() as connection:
                result = connection.execute(
                    text("""
                        SELECT * FROM email_campaigns
                        ORDER BY created_at DESC
                        LIMIT :limit OFFSET :offset
                    """),
                    {"limit": limit, "offset": offset}
                )
                campaigns = []
                for row in result:
                    data = dict(row._mapping)
                    campaigns.append(self._row_to_campaign_response(data))
                return campaigns
        except Exception as e:
            logger.error(f"Failed to list campaigns: {str(e)}", exc_info=True)
            return []

    def get_campaign(self, campaign_id: str) -> Optional[EmailCampaignResponse]:
        """Get a specific campaign by ID."""
        try:
            with engine.begin() as connection:
                result = connection.execute(
                    text("SELECT * FROM email_campaigns WHERE campaign_id = :campaign_id"),
                    {"campaign_id": campaign_id}
                )
                row = result.fetchone()
                if not row:
                    return None
                return self._row_to_campaign_response(dict(row._mapping))
        except Exception as e:
            logger.error(f"Failed to get campaign: {str(e)}", exc_info=True)
            return None

    def _row_to_campaign_response(self, row: Dict) -> EmailCampaignResponse:
        """Convert database row to EmailCampaignResponse."""
        # Parse JSON fields
        subject_line_variations = []
        if row.get("subject_line_variations"):
            try:
                subject_line_variations = json.loads(row["subject_line_variations"])
            except:
                pass

        design_recommendations = []
        if row.get("design_recommendations"):
            try:
                design_recommendations = json.loads(row["design_recommendations"])
            except:
                pass

        talking_points = []
        if row.get("talking_points"):
            try:
                talking_points = json.loads(row["talking_points"])
            except:
                pass

        product_image_urls = None
        if row.get("product_image_urls"):
            try:
                product_image_urls = json.loads(row["product_image_urls"])
            except:
                pass

        email_content = EmailContent(
            subject_line=row.get("subject_line", ""),
            preview_text=row.get("preview_text"),
            greeting=row.get("greeting", ""),
            body=row.get("body", ""),
            call_to_action=row.get("call_to_action", ""),
            closing=row.get("closing", ""),
            footer=row.get("footer"),
            html_template=row.get("html_template"),
            hero_image_url=row.get("hero_image_url"),
            product_image_urls=product_image_urls,
        )

        return EmailCampaignResponse(
            campaign_id=row.get("campaign_id", ""),
            campaign_name=row.get("campaign_name", ""),
            objective=row.get("objective", ""),
            audience_segment=row.get("audience_segment"),
            email_content=email_content,
            subject_line_variations=subject_line_variations,
            design_recommendations=design_recommendations,
            talking_points=talking_points,
            expected_metrics={
                "estimated_open_rate": "20-25%",
                "estimated_click_rate": "3-5%",
                "estimated_conversion_rate": "1-2%",
            },
        )

