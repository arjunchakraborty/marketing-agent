"""Workflow for running experiments using vector database to identify campaigns and extract key features."""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..core.config import settings
from ..services.intelligence_service import IntelligenceService
from ..services.vector_db_service import (
    DEFAULT_PRODUCT_COLLECTION_NAME,
    VectorDBService,
    get_product_context_for_prompts,
)

logger = logging.getLogger(__name__)

# Only use campaign search results with similarity at or above this (0-1). Filters out low-confidence matches.
MIN_SIMILARITY_HIGH_CONFIDENCE = 0.6


def _extract_product_names_from_campaigns(campaigns: List[Dict[str, Any]]) -> List[str]:
    """Extract product names from campaign metadata or analysis for product-context lookup."""
    names = []
    for campaign in campaigns:
        metadata = campaign.get("metadata") or {}
        # Common metadata keys for products
        for key in ("products_promoted", "products", "product_names"):
            val = metadata.get(key)
            if isinstance(val, list):
                for p in val:
                    if isinstance(p, str) and p.strip() and p.strip() not in {n.strip() for n in names}:
                        names.append(p.strip())
            elif isinstance(val, str) and val.strip():
                names.append(val.strip())
        analysis = campaign.get("analysis")
        if isinstance(analysis, dict) and analysis.get("products_promoted"):
            for p in analysis["products_promoted"]:
                if isinstance(p, str) and p.strip() and p.strip() not in {n.strip() for n in names}:
                    names.append(p.strip())
    return names[:30]


def extract_key_features_from_campaigns(
    campaigns: List[Dict[str, Any]],
    intelligence_service: IntelligenceService,
    product_collection_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Extract key features and patterns from a list of campaigns using LLM.
    Incorporates product descriptions so hero_image_prompts, text_prompts, and
    call_to_action_prompts include product details in addition to RAG patterns.
    
    Args:
        campaigns: List of campaign analysis dictionaries from vector DB
        intelligence_service: Intelligence service for LLM operations
        product_collection_name: Optional product collection for description lookup (default UCO_Gear_Products)
        
    Returns:
        Dictionary with key features, patterns, and recommendations
    """
    if not campaigns:
        return {
            "key_features": [],
            "patterns": {},
            "recommendations": [],
            "hero_image_prompts": [],
            "text_prompts": [],
            "call_to_action_prompts": [],
            "summary": "No campaigns found to analyze",
        }
    
    # Prepare campaign summaries for LLM analysis
    campaign_summaries = []
    for campaign in campaigns:
        analysis = campaign.get("analysis", {})
        campaign_id = campaign.get("campaign_id", "unknown")
        metadata = campaign.get("metadata", {})
        
        summary_parts = [str(analysis) if not isinstance(analysis, dict) else json.dumps(analysis)]
        summary_parts.append(f"Metadata: {json.dumps(metadata)}")
        campaign_summaries.append(f"[Campaign {campaign_id}]\n" + "\n".join(summary_parts))
    
    # Product context: names + descriptions for prompt generation
    product_names = _extract_product_names_from_campaigns(campaigns)
    collection = product_collection_name or DEFAULT_PRODUCT_COLLECTION_NAME
    product_context = get_product_context_for_prompts(
        product_names=product_names if product_names else None,
        collection_name=collection,
        max_products=25,
    )
    product_context_block = ""
    if product_context:
        product_context_block = f"""
Product context (incorporate these product details into hero image, text, and call-to-action prompts below):
{product_context}

"""
    
    # Create prompt for feature extraction
    prompt = f"""Analyze the following {len(campaigns)} marketing campaigns and identify:

1. Key Features: What are the most important features that make these campaigns effective?
2. Common Patterns: What patterns do you see across these campaigns (visual elements, messaging, design)?
3. Recommendations: Generate hero image, text, and call-to-action prompts that incorporate both (a) these campaign patterns and (b) the product details below. Each generated prompt should reference specific product names and descriptions where relevant.
{product_context_block}
Campaign Summaries:
{chr(10).join(campaign_summaries)}

Provide a structured analysis with:
- Key Features (list 5-7 most important)
- Common Patterns (describe visual, messaging, and design patterns)
- You can assume that each email would have this structure: logo, navigation, Hero Image, Text, and Call to Action.
- Generate recommendations for each content section. For hero_image_prompts, text_prompts, and call_to_action_prompts: each prompt must incorporate product details (names/descriptions) from the Product context above in addition to the campaign patterns. The final prompts should be usable as system prompts for generating new campaign content.

Return as JSON with keys: key_features (list), patterns (dict with keys: visual, messaging, design), hero_image_prompts (list of strings), text_prompts (list of strings), call_to_action_prompts (list of strings)."""

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
                logger.info(response)
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
            
            # Extract structured recommendations if available
            hero_image_prompts = []
            text_prompts = []
            call_to_action_prompts = []
            
            # Check for structured recommendations
            if "hero_image_prompts" in analysis:
                hero_image_prompts = analysis.get("hero_image_prompts", [])
            elif "hero_image" in analysis:
                hero_image_prompts = analysis.get("hero_image", [])
                if not isinstance(hero_image_prompts, list):
                    hero_image_prompts = [hero_image_prompts] if hero_image_prompts else []
            
            if "text_prompts" in analysis:
                text_prompts = analysis.get("text_prompts", [])
            elif "text" in analysis:
                text_prompts = analysis.get("text", [])
                if not isinstance(text_prompts, list):
                    text_prompts = [text_prompts] if text_prompts else []
            
            if "call_to_action_prompts" in analysis:
                call_to_action_prompts = analysis.get("call_to_action_prompts", [])
            elif "call_to_action" in analysis:
                call_to_action_prompts = analysis.get("call_to_action", [])
                if not isinstance(call_to_action_prompts, list):
                    call_to_action_prompts = [call_to_action_prompts] if call_to_action_prompts else []
            
            # Fallback to flat recommendations if structured ones don't exist
            flat_recommendations = analysis.get("recommendations", [])
            
            return {
                "key_features": analysis.get("key_features", []),
                "patterns": analysis.get("patterns", {}),
                "recommendations": flat_recommendations,
                "hero_image_prompts": hero_image_prompts,
                "text_prompts": text_prompts,
                "call_to_action_prompts": call_to_action_prompts,
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
        
        # Search in specified collection or default to UCO_Gear_Campaigns
        collections_to_search = [collection_name] if collection_name else ["UCO_Gear_Campaigns"]
        
        for coll_name in collections_to_search:
            try:
                vector_db_service = VectorDBService(collection_name=coll_name)
                
                # Search for similar campaigns using the prompt (at least 3 for useful analysis)
                n_results = max(3, num_campaigns)
                similar_campaigns = vector_db_service.search_similar_campaigns(
                    query_text=prompt_query,
                    n_results=n_results,
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
                unique_campaigns[campaign.get("similarity_score")] = campaign
        
        campaigns_found = list(unique_campaigns.values())
        campaign_ids = list(unique_campaigns.keys())
        
        # Keep only high-confidence results (similarity_score >= threshold)
        campaigns_found = [
            c for c in campaigns_found
            if (c.get("similarity_score") or 0) >= MIN_SIMILARITY_HIGH_CONFIDENCE
        ]
        campaign_ids = [c.get("campaign_id") for c in campaigns_found if c.get("campaign_id")]
        if not campaigns_found:
            logger.warning(
                f"No campaigns met high-confidence threshold (similarity >= {MIN_SIMILARITY_HIGH_CONFIDENCE}). "
                "Try a more specific query or lower the threshold."
            )
            return {
                "experiment_run_id": experiment_run_id,
                "status": "completed",
                "campaigns_analyzed": 0,
                "campaign_ids": [],
                "key_features": {
                    "key_features": [],
                    "patterns": {},
                    "recommendations": [
                        f"No campaigns matched with high confidence (score >= {MIN_SIMILARITY_HIGH_CONFIDENCE}). "
                        "Try a more specific search prompt."
                    ],
                    "summary": "No high-confidence matches",
                },
                "error": "No campaigns met high-confidence similarity threshold",
            }
        
        logger.info(f"Analyzing {len(campaigns_found)} unique high-confidence campaigns")
        
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
                "hero_image_prompts": key_features.get("hero_image_prompts", []),
                "text_prompts": key_features.get("text_prompts", []),
                "call_to_action_prompts": key_features.get("call_to_action_prompts", []),
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

