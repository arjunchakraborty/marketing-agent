"""MongoDB repositories for document storage (replacing PostgreSQL/SQLite when use_mongodb=True).
Each function uses the same logical data shape as the SQL tables for easier migration."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..core.config import settings
from .collections import (
    COLL_CAMPAIGN_ANALYSIS,
    COLL_CAMPAIGNS,
    COLL_DATASET_REGISTRY,
    COLL_EMAIL_CAMPAIGNS,
    COLL_EMAIL_FEATURE_CATALOG,
    COLL_EXPERIMENT_RUNS,
    COLL_IMAGE_ANALYSIS_RESULTS,
    COLL_KPI_PRECOMPUTED,
    COLL_PROMPT_SQL_CACHE,
    COLL_TARGETED_CAMPAIGNS,
    COLL_VISUAL_ELEMENT_CORRELATIONS,
)
from .mongodb import get_database


def _ensure_mongodb():
    if not getattr(settings, "use_mongodb", False):
        raise RuntimeError("MongoDB backend not enabled. Set USE_MONGODB=true.")
    return get_database()


# --- experiment_runs ---


def _doc_with_id(d: Dict[str, Any], id_key: str = "id") -> Dict[str, Any]:
    """Convert MongoDB doc to API shape: use _id as id (string)."""
    out = dict(d)
    oid = out.pop("_id", None)
    if oid is not None and id_key not in out:
        out[id_key] = str(oid)
    return out


def mongo_find_experiment_run(experiment_run_id: str) -> Optional[Dict[str, Any]]:
    db = _ensure_mongodb()
    doc = db[COLL_EXPERIMENT_RUNS].find_one({"experiment_run_id": experiment_run_id})
    if not doc:
        return None
    return _doc_with_id(doc)


def mongo_list_experiment_run_ids(limit: int = 20) -> List[str]:
    db = _ensure_mongodb()
    cursor = (
        db[COLL_EXPERIMENT_RUNS]
        .find({}, {"experiment_run_id": 1})
        .sort("created_at", -1)
        .limit(limit)
    )
    return [d["experiment_run_id"] for d in cursor]


def mongo_insert_experiment_run(
    experiment_run_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    sql_query: Optional[str] = None,
    status: str = "pending",
    config: Optional[Dict] = None,
    results_summary: Optional[Dict] = None,
    completed_at: Optional[str] = None,
) -> None:
    db = _ensure_mongodb()
    now = datetime.utcnow().isoformat()
    doc = {
        "experiment_run_id": experiment_run_id,
        "name": name,
        "description": description,
        "sql_query": sql_query,
        "status": status,
        "config": config,
        "results_summary": results_summary,
        "created_at": now,
        "updated_at": now,
        "completed_at": completed_at,
    }
    db[COLL_EXPERIMENT_RUNS].update_one(
        {"experiment_run_id": experiment_run_id}, {"$set": doc}, upsert=True
    )


# --- campaign_analysis ---


def mongo_find_campaign_analyses_by_run(experiment_run_id: str) -> List[Dict[str, Any]]:
    db = _ensure_mongodb()
    cursor = (
        db[COLL_CAMPAIGN_ANALYSIS]
        .find({"experiment_run_id": experiment_run_id})
        .sort("created_at", -1)
    )
    return [_doc_with_id(d) for d in cursor]


def mongo_insert_campaign_analysis(
    experiment_run_id: str,
    campaign_id: Optional[str],
    campaign_name: Optional[str],
    sql_query: str,
    query_results: Optional[Any] = None,
    metrics: Optional[Dict] = None,
    products_promoted: Optional[List] = None,
) -> None:
    db = _ensure_mongodb()
    now = datetime.utcnow().isoformat()
    doc = {
        "experiment_run_id": experiment_run_id,
        "campaign_id": campaign_id,
        "campaign_name": campaign_name,
        "sql_query": sql_query,
        "query_results": query_results,
        "metrics": metrics,
        "products_promoted": products_promoted,
        "created_at": now,
        "updated_at": now,
    }
    db[COLL_CAMPAIGN_ANALYSIS].insert_one(doc)


# --- image_analysis_results ---


def mongo_find_image_analysis_results_by_run(
    experiment_run_id: str,
) -> List[Dict[str, Any]]:
    db = _ensure_mongodb()
    cursor = (
        db[COLL_IMAGE_ANALYSIS_RESULTS]
        .find({"experiment_run_id": experiment_run_id})
        .sort("created_at", -1)
    )
    return [_doc_with_id(d) for d in cursor]


def mongo_find_image_analysis_results_by_campaign(
    campaign_id: str,
    experiment_run_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    db = _ensure_mongodb()
    q: Dict[str, Any] = {"campaign_id": campaign_id}
    if experiment_run_id:
        q["experiment_run_id"] = experiment_run_id
    cursor = db[COLL_IMAGE_ANALYSIS_RESULTS].find(q).sort("created_at", -1)
    return [_doc_with_id(d) for d in cursor]


def mongo_insert_image_analysis_result(
    experiment_run_id: str,
    campaign_id: Optional[str],
    image_id: str,
    image_path: Optional[str] = None,
    image_url: Optional[str] = None,
    visual_elements: Optional[List] = None,
    dominant_colors: Optional[List] = None,
    composition_analysis: Optional[str] = None,
    text_content: Optional[str] = None,
    overall_description: Optional[str] = None,
    marketing_relevance: Optional[str] = None,
    email_features: Optional[Dict] = None,
    feature_catalog: Optional[Dict] = None,
) -> None:
    db = _ensure_mongodb()
    now = datetime.utcnow().isoformat()
    doc = {
        "experiment_run_id": experiment_run_id,
        "campaign_id": campaign_id,
        "image_id": image_id,
        "image_path": image_path,
        "image_url": image_url,
        "visual_elements": visual_elements,
        "dominant_colors": dominant_colors,
        "composition_analysis": composition_analysis,
        "text_content": text_content,
        "overall_description": overall_description,
        "marketing_relevance": marketing_relevance,
        "email_features": email_features,
        "feature_catalog": feature_catalog,
        "created_at": now,
    }
    db[COLL_IMAGE_ANALYSIS_RESULTS].insert_one(doc)


# --- email_feature_catalog ---


def mongo_insert_email_feature_catalog(
    experiment_run_id: str,
    campaign_id: Optional[str],
    feature_category: str,
    feature_type: str,
    feature_description: Optional[str] = None,
    bbox: Optional[Any] = None,
    confidence: Optional[float] = None,
    position: Optional[str] = None,
    m_data: Optional[Dict] = None,
) -> None:
    db = _ensure_mongodb()
    doc = {
        "experiment_run_id": experiment_run_id,
        "campaign_id": campaign_id,
        "feature_category": feature_category,
        "feature_type": feature_type,
        "feature_description": feature_description,
        "bbox": bbox,
        "confidence": confidence,
        "position": position,
        "mData": m_data,
        "created_at": datetime.utcnow().isoformat(),
    }
    db[COLL_EMAIL_FEATURE_CATALOG].insert_one(doc)


# --- visual_element_correlations ---


def mongo_insert_visual_element_correlation(
    experiment_run_id: str,
    element_type: str,
    element_description: Optional[str] = None,
    average_performance: Optional[Dict] = None,
    performance_impact: Optional[str] = None,
    recommendation: Optional[str] = None,
    campaign_count: Optional[int] = None,
) -> None:
    db = _ensure_mongodb()
    doc = {
        "experiment_run_id": experiment_run_id,
        "element_type": element_type,
        "element_description": element_description or "",
        "average_performance": average_performance,
        "performance_impact": performance_impact or "",
        "recommendation": recommendation or "",
        "campaign_count": campaign_count,
        "created_at": datetime.utcnow().isoformat(),
    }
    db[COLL_VISUAL_ELEMENT_CORRELATIONS].insert_one(doc)


def mongo_find_visual_element_correlations_by_run(
    experiment_run_id: str,
) -> List[Dict[str, Any]]:
    db = _ensure_mongodb()
    cursor = db[COLL_VISUAL_ELEMENT_CORRELATIONS].find(
        {"experiment_run_id": experiment_run_id}
    )
    return [_doc_with_id(d) for d in cursor]


# --- campaigns (Klaviyo) ---


def mongo_find_campaign_by_id(campaign_id: str) -> Optional[Dict[str, Any]]:
    db = _ensure_mongodb()
    return db[COLL_CAMPAIGNS].find_one({"campaign_id": campaign_id})


def mongo_upsert_campaign(campaign_data: Dict[str, Any]) -> None:
    db = _ensure_mongodb()
    campaign_id = campaign_data.get("campaign_id")
    if not campaign_id:
        raise ValueError("campaign_id required")
    campaign_data.setdefault("created_at", datetime.utcnow().isoformat())
    campaign_data["updated_at"] = datetime.utcnow().isoformat()
    db[COLL_CAMPAIGNS].update_one(
        {"campaign_id": campaign_id}, {"$set": campaign_data}, upsert=True
    )


# --- email_campaigns ---


def mongo_find_email_campaign(campaign_id: str) -> Optional[Dict[str, Any]]:
    db = _ensure_mongodb()
    doc = db[COLL_EMAIL_CAMPAIGNS].find_one({"campaign_id": campaign_id})
    return _doc_with_id(doc) if doc else None


def mongo_list_email_campaigns(limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
    db = _ensure_mongodb()
    cursor = (
        db[COLL_EMAIL_CAMPAIGNS]
        .find({})
        .sort("created_at", -1)
        .skip(offset)
        .limit(limit)
    )
    return [_doc_with_id(d) for d in cursor]


def mongo_upsert_email_campaign(campaign_id: str, doc: Dict[str, Any]) -> None:
    db = _ensure_mongodb()
    doc["campaign_id"] = campaign_id
    doc.setdefault("created_at", datetime.utcnow().isoformat())
    doc["updated_at"] = datetime.utcnow().isoformat()
    db[COLL_EMAIL_CAMPAIGNS].update_one(
        {"campaign_id": campaign_id}, {"$set": doc}, upsert=True
    )


# --- dataset_registry ---


def mongo_list_datasets() -> List[Dict[str, Any]]:
    db = _ensure_mongodb()
    cursor = db[COLL_DATASET_REGISTRY].find({})
    rows = []
    for d in cursor:
        d = dict(d)
        d.pop("_id", None)
        if isinstance(d.get("columns"), str):
            try:
                d["columns"] = json.loads(d["columns"])
            except Exception:
                d["columns"] = []
        rows.append(d)
    return rows


def mongo_upsert_dataset_registry(
    table_name: str,
    business: str,
    category: str,
    dataset_name: str,
    source_file: str,
    row_count: int,
    columns: List[str],
) -> None:
    db = _ensure_mongodb()
    doc = {
        "table_name": table_name,
        "business": business,
        "category": category,
        "dataset_name": dataset_name,
        "source_file": source_file,
        "row_count": row_count,
        "columns": columns,
        "ingested_at": datetime.utcnow().isoformat(),
    }
    db[COLL_DATASET_REGISTRY].update_one(
        {"table_name": table_name}, {"$set": doc}, upsert=True
    )


# --- kpi_precomputed_sql ---


def mongo_find_precomputed_kpi(kpi_name: str, business: Optional[str] = None) -> Optional[Dict]:
    db = _ensure_mongodb()
    q = {"kpi_name": kpi_name}
    if business is not None:
        q["business"] = business
    return db[COLL_KPI_PRECOMPUTED].find_one(q)


def mongo_upsert_precomputed_kpi(
    kpi_name: str,
    prompt: str,
    sql_query: str,
    business: Optional[str] = None,
    last_executed_at: Optional[str] = None,
    execution_count: int = 0,
) -> None:
    db = _ensure_mongodb()
    now = datetime.utcnow().isoformat()
    doc = {
        "kpi_name": kpi_name,
        "prompt": prompt,
        "sql_query": sql_query,
        "business": business,
        "created_at": now,
        "updated_at": now,
        "last_executed_at": last_executed_at,
        "execution_count": execution_count,
    }
    db[COLL_KPI_PRECOMPUTED].update_one(
        {"kpi_name": kpi_name, "business": business or ""},
        {"$set": doc},
        upsert=True,
    )


def mongo_update_precomputed_kpi_execution(
    kpi_name: str,
    business: Optional[str],
    last_executed_at: str,
) -> None:
    db = _ensure_mongodb()
    db[COLL_KPI_PRECOMPUTED].update_one(
        {"kpi_name": kpi_name, "business": business or ""},
        {"$set": {"last_executed_at": last_executed_at}, "$inc": {"execution_count": 1}},
    )


# --- prompt_sql_cache ---


def mongo_find_prompt_sql_cache(prompt_hash: str) -> Optional[Dict]:
    db = _ensure_mongodb()
    return db[COLL_PROMPT_SQL_CACHE].find_one({"prompt_hash": prompt_hash})


def mongo_upsert_prompt_sql_cache(
    prompt_hash: str,
    prompt: str,
    sql_query: str,
    table_name: Optional[str] = None,
    business: Optional[str] = None,
    dataset_name: Optional[str] = None,
    columns: Optional[Any] = None,
    schema_version: Optional[str] = None,
    generated_by: Optional[str] = None,
    model: Optional[str] = None,
    last_used_at: Optional[str] = None,
    usage_count: int = 0,
    ttl_seconds: Optional[int] = None,
    expires_at: Optional[str] = None,
) -> None:
    db = _ensure_mongodb()
    now = datetime.utcnow().isoformat()
    doc = {
        "prompt_hash": prompt_hash,
        "prompt": prompt,
        "sql_query": sql_query,
        "table_name": table_name,
        "business": business,
        "dataset_name": dataset_name,
        "columns": columns,
        "schema_version": schema_version,
        "generated_by": generated_by,
        "model": model,
        "created_at": now,
        "last_used_at": last_used_at,
        "usage_count": usage_count,
        "ttl_seconds": ttl_seconds,
        "expires_at": expires_at,
    }
    db[COLL_PROMPT_SQL_CACHE].update_one(
        {"prompt_hash": prompt_hash}, {"$set": doc}, upsert=True
    )


def mongo_delete_prompt_sql_cache(prompt_hash: str) -> None:
    db = _ensure_mongodb()
    db[COLL_PROMPT_SQL_CACHE].delete_one({"prompt_hash": prompt_hash})


def mongo_update_prompt_sql_cache_usage(prompt_hash: str, last_used_at: str) -> None:
    db = _ensure_mongodb()
    db[COLL_PROMPT_SQL_CACHE].update_one(
        {"prompt_hash": prompt_hash},
        {"$set": {"last_used_at": last_used_at}, "$inc": {"usage_count": 1}},
    )


# --- targeted_campaigns ---


def mongo_upsert_targeted_campaign(
    campaign_id: str,
    campaign_name: str,
    channel: str,
    objective: str,
    segment_ids: List[str],
    constraints: Optional[Dict] = None,
    products: Optional[List] = None,
    product_images: Optional[List] = None,
    estimated_reach: Optional[int] = None,
    status: str = "draft",
) -> None:
    db = _ensure_mongodb()
    doc = {
        "campaign_id": campaign_id,
        "campaign_name": campaign_name,
        "channel": channel,
        "objective": objective,
        "segment_ids": segment_ids,
        "constraints": constraints,
        "products": products,
        "product_images": product_images or [],
        "estimated_reach": estimated_reach,
        "status": status,
        "created_at": datetime.utcnow().isoformat(),
    }
    db[COLL_TARGETED_CAMPAIGNS].update_one(
        {"campaign_id": campaign_id}, {"$set": doc}, upsert=True
    )


def mongo_find_targeted_campaign(campaign_id: str) -> Optional[Dict[str, Any]]:
    db = _ensure_mongodb()
    return db[COLL_TARGETED_CAMPAIGNS].find_one({"campaign_id": campaign_id})


# --- dynamic dataset rows (one collection per table_name) ---


def mongo_insert_dataset_rows(table_name: str, rows: List[Dict[str, Any]]) -> None:
    """Insert or replace rows for a dataset table. Uses collection name = table_name."""
    db = _ensure_mongodb()
    coll = db[table_name]
    # Replace all documents: drop and insert (simple upsert by row index would require a key)
    coll.delete_many({})
    if rows:
        # Ensure each row is a dict; add _id or leave MongoDB to add _id
        coll.insert_many(rows)
