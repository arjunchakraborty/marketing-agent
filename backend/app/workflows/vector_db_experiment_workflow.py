"""Workflow for running experiments using vector database to identify campaigns and extract key features."""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..core.config import settings
from ..services.intelligence_service import IntelligenceService
from ..services.vector_db_service import VectorDBService

logger = logging.getLogger(__name__)


def extract_key_features_from_campaigns(
    campaigns: List[Dict[str, Any]],
    intelligence_service: IntelligenceService,
) -> Dict[str, Any]:
    """
    Extract key features and patterns from a list of campaigns using LLM.
    
    Args:
        campaigns: List of campaign analysis dictionaries from vector DB
        intelligence_service: Intelligence service for LLM operations
        
    Returns:
        Dictionary with key features, patterns, and recommendations
    """
    if not campaigns:
        return {
            "key_features": [],
            "patterns": {},
            "recommendations": [],
            "summary": "No campaigns found to analyze",
        }
    
    # Prepare campaign summaries for LLM analysis
    campaign_summaries = []
    for campaign in campaigns:
        analysis = campaign.get("analysis", {})
        campaign_id = campaign.get("campaign_id", "unknown")
        metadata = campaign.get("metadata", {})
        
        summary_parts = [f"Campaign ID: {campaign_id}"]
        
        # Add campaign name
        if "campaign_name" in analysis:
            summary_parts.append(f"Name: {analysis['campaign_name']}")
        
        # Add performance metrics
        if "open_rate" in analysis:
            summary_parts.append(f"Open Rate: {analysis['open_rate']}")
        if "click_rate" in analysis:
            summary_parts.append(f"Click Rate: {analysis['click_rate']}")
        if "revenue" in analysis:
            summary_parts.append(f"Revenue: ${analysis['revenue']}")
        
        # Add image information
        images = analysis.get("images", [])
        if images:
            summary_parts.append(f"Images: {len(images)}")
            # Extract visual elements from images
            visual_elements = []
            colors = []
            for img in images:
                img_analysis = img.get("analysis", {}) if "analysis" in img else img
                # Extract richer details from analysis JSON, following the structure in /image-analysis-extract/
                # visual_elements, header, hero_image, call_to_action_button, product_images, product_blocks, buttons, etc.
                # Collect visual elements in human-readable summaries for LLM

                # Visual elements (semantic - across both 'visual_elements' and structured blocks)
                extracted_visual_elements = []

                # Standard 'visual_elements' field, if present
                if "visual_elements" in img_analysis:
                    for elem in img_analysis["visual_elements"]:
                        if isinstance(elem, dict):
                            elem_type = elem.get("element_type")
                            desc = elem.get("description", "")
                            if elem_type and desc:
                                extracted_visual_elements.append(f"{elem_type}: {desc}")
                            elif elem_type:
                                extracted_visual_elements.append(elem_type)
                            elif desc:
                                extracted_visual_elements.append(desc)
                        else:
                            extracted_visual_elements.append(str(elem))

                # Header (logo, navigation, tagline)
                header = img_analysis.get("header", {})
                if isinstance(header, dict):
                    logo = header.get("logo", {})
                    if logo:
                        txt = logo.get("text", "")
                        tagline = logo.get("tagline", "")
                        color = logo.get("color", "")
                        extracted_visual_elements.append(f"logo: {txt} {'- ' + tagline if tagline else ''} ({color})")
                    navigation = header.get("navigation", {})
                    if navigation:
                        items = navigation.get("items", [])
                        nav_desc = f"Navigation: {', '.join(items)}" if items else "Navigation"
                        color_scheme = navigation.get("color_scheme", "")
                        extracted_visual_elements.append(f"{nav_desc} ({color_scheme})")

                # Hero image section
                hero_image = img_analysis.get("hero_image", {})
                if hero_image:
                    desc = hero_image.get("description", "")
                    elements = hero_image.get("elements", [])
                    cscheme = hero_image.get("color_scheme", "")
                    if desc:
                        extracted_visual_elements.append(f"Hero image: {desc}")
                    if elements:
                        extracted_visual_elements.append(f"Hero image elements: {', '.join(elements)}")
                    if cscheme:
                        extracted_visual_elements.append(f"Hero image color scheme: {cscheme}")

                # CTA Button
                cta = img_analysis.get("call_to_action_button", {})
                if cta:
                    text = cta.get("text", "")
                    color = cta.get("color", "")
                    pos = cta.get("position", "")
                    extracted_visual_elements.append(f"CTA button: '{text}' ({color}, {pos})")

                # Product images
                product_images = img_analysis.get("product_images", [])
                for prodimg in product_images or []:
                    desc = prodimg.get("description", "") if isinstance(prodimg, dict) else str(prodimg)
                    if desc:
                        extracted_visual_elements.append(f"Product image: {desc}")

                # Product blocks
                product_blocks = img_analysis.get("product_blocks", [])
                for prodblock in product_blocks or []:
                    title = prodblock.get("title", "") if isinstance(prodblock, dict) else ""
                    if title:
                        extracted_visual_elements.append(f"Product Block: {title}")

                # Buttons
                buttons = img_analysis.get("buttons", [])
                for btn in buttons or []:
                    text = btn.get("text", "") if isinstance(btn, dict) else str(btn)
                    if text:
                        extracted_visual_elements.append(f"Button: '{text}'")

                # Text sections, if any (e.g., extracted from analysis)
                text_sections = img_analysis.get("text_sections", [])
                for section in text_sections or []:
                    header_txt = section.get("header", "") if isinstance(section, dict) else ""
                    summary = section.get("summary", "") if isinstance(section, dict) else str(section)
                    if header_txt or summary:
                        extracted_visual_elements.append(f"Text section: {header_txt} {summary}".strip())

                # Any other keys of interest (e.g., testimonials, special banners)
                if "testimonials" in img_analysis:
                    for t in img_analysis["testimonials"] or []:
                        text = t.get("text", "") if isinstance(t, dict) else str(t)
                        if text:
                            extracted_visual_elements.append(f"Testimonial: {text}")

                # Dominant colors
                if "dominant_colors" in img_analysis:
                    for color in img_analysis["dominant_colors"]:
                        if isinstance(color, dict):
                            colors.append(color.get("color", ""))
                        else:
                            colors.append(str(color))

                # Also gather color_scheme from nested hero/header/nav/cta
                def collect_color_scheme(node):
                    if isinstance(node, dict) and "color_scheme" in node and node["color_scheme"]:
                        colors.append(str(node["color_scheme"]))
                    if isinstance(node, dict):
                        for v in node.values():
                            collect_color_scheme(v)
                    elif isinstance(node, list):
                        for v in node:
                            collect_color_scheme(v)
                collect_color_scheme(img_analysis.get("hero_image", {}))
                collect_color_scheme(img_analysis.get("header", {}))
                collect_color_scheme(img_analysis.get("call_to_action_button", {}))

                # Compile human-friendly summaries (deduplicated) for use in LLM
                if extracted_visual_elements:
                    summary_parts.append(f"Visual Elements: {', '.join(list(dict.fromkeys(extracted_visual_elements))[:7])}")
                if colors:
                    summary_parts.append(f"Colors: {', '.join(list(dict.fromkeys(colors))[:7])}")
            
            if visual_elements:
                summary_parts.append(f"Visual Elements: {', '.join(set(visual_elements)[:5])}")
            if colors:
                summary_parts.append(f"Colors: {', '.join(set(colors)[:5])}")
        
        campaign_summaries.append(" | ".join(summary_parts))
    
    # Create prompt for feature extraction
    prompt = f"""Analyze the following {len(campaigns)} marketing campaigns and identify:

1. Key Features: What are the most important features that make these campaigns effective?
2. Common Patterns: What patterns do you see across these campaigns (visual elements, messaging, design)?
3. Recommendations: Generate text that can be used to prompt for creating a new email campaign visual incorporating the text and visual elements of the campaigns passed in

Campaign Summaries:
{chr(10).join(campaign_summaries[:20])}

Provide a structured analysis with:
- Key Features (list 5-7 most important)
- Common Patterns (describe visual, messaging, and design patterns)
- Recommendations (generate text that can be used as a system prompt for generating new email campaign image incorporating the common patterns)

Return as JSON with keys: key_features (list), patterns (dict with keys: visual, messaging, design), recommendations (list)."""

    try:
        if not intelligence_service.llm_service:
            return {
                "key_features": ["LLM service not available"],
                "patterns": {},
                "recommendations": ["Configure LLM API keys to get detailed analysis"],
                "summary": "Analysis limited due to missing LLM service",
            }
        
        # Use LLM to generate analysis
        try:
            llm_service = intelligence_service.llm_service
            if not llm_service:
                raise ValueError("LLM service not available")
            
            if llm_service.provider == "openai":
                client = llm_service._get_openai_client()
                response_obj = client.chat.completions.create(
                    model=settings.openai_model,
                    messages=[
                        {"role": "system", "content": "You are a marketing analytics expert. Analyze campaigns and provide structured insights. Return JSON format."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
                    max_tokens=1500,
                )
                response = response_obj.choices[0].message.content.strip()
            elif llm_service.provider == "anthropic":
                client = llm_service._get_anthropic_client()
                response_obj = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1500,
                    system="You are a marketing analytics expert. Analyze campaigns and provide structured insights. Return JSON format.",
                    messages=[{"role": "user", "content": prompt}],
                )
                response = response_obj.content[0].text.strip()
            elif llm_service.provider == "ollama":
                client = llm_service._get_ollama_client()
                response_obj = client.post(
                    "/api/chat",
                    json={
                        "model": settings.ollama_model,
                        "messages": [
                            {"role": "system", "content": "You are a marketing analytics expert. Analyze campaigns and provide structured insights. Return JSON format."},
                            {"role": "user", "content": prompt},
                        ],
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "num_predict": 1500,
                        },
                    },
                )
                response_obj.raise_for_status()
                result = response_obj.json()
                response = result.get("message", {}).get("content", "").strip()
            else:
                raise ValueError(f"Unsupported provider: {llm_service.provider}")
        except Exception as e:
            logger.error(f"LLM generation failed: {str(e)}", exc_info=True)
            # Fallback to simple analysis
            response = json.dumps({
                "key_features": [f"Analysis of {len(campaigns)} campaigns"],
                "patterns": {"visual": "Patterns identified", "messaging": "Messaging patterns", "design": "Design patterns"},
                "recommendations": ["Review campaign performance metrics", "Analyze visual elements", "Consider audience targeting"],
            })
        
        # Try to parse JSON response
        try:
            # Extract JSON from response if wrapped in markdown
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()
            
            analysis = json.loads(response)
            return {
                "key_features": analysis.get("key_features", []),
                "patterns": analysis.get("patterns", {}),
                "recommendations": analysis.get("recommendations", []),
                "summary": f"Analyzed {len(campaigns)} campaigns and identified {len(analysis.get('key_features', []))} key features",
            }
        except json.JSONDecodeError:
            # If not JSON, create structured response from text
            return {
                "key_features": [response[:200]],
                "patterns": {"visual": response, "messaging": "", "design": ""},
                "recommendations": [response[:300]],
                "summary": f"Analyzed {len(campaigns)} campaigns",
            }
    except Exception as e:
        logger.error(f"Failed to extract key features: {str(e)}", exc_info=True)
        return {
            "key_features": [],
            "patterns": {},
            "recommendations": [],
            "summary": f"Feature extraction failed: {str(e)}",
        }


def run_vector_db_experiment(
    prompt_query: str,
    collection_name: Optional[str] = None,
    experiment_name: Optional[str] = None,
    num_campaigns: int = 10,
) -> Dict[str, Any]:
    """
    Run experiment using vector database to identify campaigns and extract key features.
    
    Args:
        prompt_query: Natural language prompt describing what campaigns to find
        collection_name: Optional collection name (default: searches all collections)
        experiment_name: Optional name for this experiment
        num_campaigns: Number of campaigns to retrieve and analyze
        
    Returns:
        Dictionary with experiment results including key features and recommendations
    """
    experiment_run_id = str(uuid.uuid4())
    logger.info(f"Starting vector DB experiment: experiment_run_id={experiment_run_id}, prompt_query={prompt_query[:100]}")
    
    try:
        # Initialize services
        intelligence_service = IntelligenceService()
        
        # Try to find campaigns in vector DB
        campaigns_found = []
        campaign_ids = []
        
        # Search in default collection or specified collection
        # Prioritize default_collection (matches ingestion default) over klaviyo_campaigns
        collections_to_search = [collection_name] if collection_name else ["default_collection", "klaviyo_campaigns"]
        
        for coll_name in collections_to_search:
            try:
                vector_db_service = VectorDBService(collection_name=coll_name)
                
                # Search for similar campaigns using the prompt
                similar_campaigns = vector_db_service.search_similar_campaigns(
                    query_text=prompt_query,
                    n_results=num_campaigns,
                )
                
                if similar_campaigns:
                    campaigns_found.extend(similar_campaigns)
                    campaign_ids.extend([c.get("campaign_id") for c in similar_campaigns if c.get("campaign_id")])
                    logger.info(f"Found {len(similar_campaigns)} campaigns in collection {coll_name}")
            except Exception as e:
                logger.warning(f"Failed to search collection {coll_name}: {str(e)}")
                continue
        
        if not campaigns_found:
            logger.warning("No campaigns found matching the prompt query")
            return {
                "experiment_run_id": experiment_run_id,
                "status": "completed",
                "campaigns_analyzed": 0,
                "campaign_ids": [],
                "key_features": {
                    "key_features": [],
                    "patterns": {},
                    "recommendations": ["No campaigns found matching your query. Try a different search prompt."],
                    "summary": "No campaigns found",
                },
                "error": "No campaigns found matching the prompt query",
            }
        
        # Remove duplicates based on campaign_id
        unique_campaigns = {}
        for campaign in campaigns_found:
            campaign_id = campaign.get("campaign_id")
            if campaign_id and campaign_id not in unique_campaigns:
                unique_campaigns[campaign_id] = campaign
            elif not campaign_id:
                # If no campaign_id, use similarity score as key
                unique_campaigns[f"unknown_{len(unique_campaigns)}"] = campaign
        
        campaigns_found = list(unique_campaigns.values())
        campaign_ids = list(unique_campaigns.keys())
        
        logger.info(f"Analyzing {len(campaigns_found)} unique campaigns")
        
        # Extract key features from campaigns
        key_features = extract_key_features_from_campaigns(
            campaigns_found,
            intelligence_service,
        )
        
        logger.info(f"Extracted {len(key_features.get('key_features', []))} key features")
        
        # Store experiment run in database
        try:
            from sqlalchemy import text
            from ..db.session import engine
            
            results_summary = {
                "campaigns_analyzed": len(campaigns_found),
                "campaign_ids": campaign_ids,
                "key_features": key_features.get("key_features", []),
                "patterns": key_features.get("patterns", {}),
                "recommendations": key_features.get("recommendations", []),
                "summary": key_features.get("summary", ""),
                "prompt_query": prompt_query,
                "collection_names_searched": collections_to_search,
            }
            
            config = {
                "prompt_query": prompt_query,
                "collection_name": collection_name,
                "num_campaigns": num_campaigns,
            }
            
            with engine.begin() as connection:
                connection.execute(
                    text("""
                        INSERT INTO experiment_runs 
                        (experiment_run_id, name, description, status, config, results_summary, created_at, completed_at)
                        VALUES (:run_id, :name, :description, :status, :config, :results_summary, :created_at, :completed_at)
                    """),
                    {
                        "run_id": experiment_run_id,
                        "name": experiment_name or f"Vector DB Experiment: {prompt_query[:50]}",
                        "description": f"Campaign analysis using vector database search: {prompt_query}",
                        "status": "completed",
                        "config": json.dumps(config),
                        "results_summary": json.dumps(results_summary),
                        "created_at": datetime.utcnow().isoformat(),
                        "completed_at": datetime.utcnow().isoformat(),
                    }
                )
            logger.info(f"Stored experiment run {experiment_run_id} in database")
        except Exception as e:
            logger.warning(f"Failed to store experiment run in database: {str(e)}", exc_info=True)
            # Continue anyway - results are still returned
        
        return {
            "experiment_run_id": experiment_run_id,
            "status": "completed",
            "campaigns_analyzed": len(campaigns_found),
            "campaign_ids": campaign_ids,
            "key_features": key_features,
            "prompt_query": prompt_query,
            "collection_names_searched": collections_to_search,
        }
        
    except Exception as e:
        logger.error(f"Vector DB experiment failed: {str(e)}", exc_info=True)
        return {
            "experiment_run_id": experiment_run_id,
            "status": "error",
            "campaigns_analyzed": 0,
            "campaign_ids": [],
            "key_features": {
                "key_features": [],
                "patterns": {},
                "recommendations": [],
                "summary": f"Experiment failed: {str(e)}",
            },
            "error": str(e),
        }

