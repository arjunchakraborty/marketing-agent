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

        # Step 1: Retrieve similar past campaigns using RAG
        past_campaigns = []
        campaign_insights = {}
        past_campaign_references = []


        # Step 2: Build enhanced prompt with RAG insights
        prompt = self._build_email_generation_prompt_with_rag(
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
            campaign_insights=campaign_insights,
            past_campaign_text_samples=self.rag_service.get_campaign_text_samples(past_campaigns) if past_campaigns else [],
        )

        # Step 3: Generate hero image if requested (before email content generation)
        hero_image_url = None
        generate_hero_image = True
        if generate_hero_image:
            logger.info("Generating hero image with campaign insights")
            
            # Build enhanced hero image prompt using campaign insights
            hero_prompt_parts = []
            
            # Base prompt from user input or objective
            if hero_image_prompt:
                hero_prompt_parts.append(hero_image_prompt)
            else:
                hero_prompt_parts.append(f"{objective} email hero image")
            
            # Add product information
            if products:
                hero_prompt_parts.append(f"featuring {', '.join(products[:2])}")
            
            # Enhance with visual insights from past campaigns
            if campaign_insights:
                # Add color palette insights
                if campaign_insights.get("color_palettes"):
                    top_colors = campaign_insights["color_palettes"][:3]
                    hero_prompt_parts.append(f"using colors: {', '.join(top_colors)}")
                
                # Add visual element insights
                if campaign_insights.get("visual_elements"):
                    top_elements = campaign_insights["visual_elements"][:2]
                    hero_prompt_parts.append(f"with visual style: {', '.join(top_elements)}")
            
            # Add design guidance if provided
            if design_guidance:
                hero_prompt_parts.append(f"design style: {design_guidance[:100]}")
            
            # Combine all parts into final prompt
            hero_prompt = ", ".join(hero_prompt_parts)

            
            
            # Generate hero image using image generation service
            try:
                hero_image_url = self.image_service.generate_hero_image(
                    prompt=hero_prompt,
                    style=tone,
                    size="1200x600",  # Email hero image standard size
                )
                if hero_image_url:
                    logger.info(f"Successfully generated hero image: {hero_image_url}")
                else:
                    logger.warning("Hero image generation returned None, continuing without hero image")
            except Exception as e:
                logger.error(f"Failed to generate hero image: {str(e)}", exc_info=True)
                # Continue without hero image if generation fails
                hero_image_url = None

        # Step 4: Generate email content using LLM
        email_data = self._generate_email_content(prompt)

        print(email_data)

        # Generate subject line variations
        subject_line_variations = self._generate_subject_lines(
            objective=objective,
            key_message=key_message,
            products=products,
            count=subject_line_suggestions,
        )

        # Step 5: Generate design recommendations with RAG insights
        design_recommendations = self._generate_design_recommendations_with_rag(
            objective=objective,
            tone=tone,
            design_guidance=design_guidance,
            campaign_insights=campaign_insights,
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
            past_campaign_references=past_campaign_references,
            expected_metrics={
                "estimated_open_rate": "20-25%",
                "estimated_click_rate": "3-5%",
                "estimated_conversion_rate": "1-2%",
            },
        )

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
        return self._build_email_generation_prompt_with_rag(
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
            campaign_insights={},
            past_campaign_text_samples=[],
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

