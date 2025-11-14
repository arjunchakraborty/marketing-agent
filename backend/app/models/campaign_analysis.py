"""Database models for campaign analysis and image analysis results."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Float, Integer, JSON, String, Text, text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class CampaignAnalysis(Base):
    """Stored campaign analysis results from SQL queries."""
    __tablename__ = "campaign_analysis"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_run_id = Column(String, nullable=False, index=True)
    campaign_id = Column(String, nullable=True, index=True)
    campaign_name = Column(String, nullable=True)
    sql_query = Column(Text, nullable=False)
    query_results = Column(JSON, nullable=True)  # Store query results as JSON
    metrics = Column(JSON, nullable=True)  # Store computed metrics (open_rate, conversion_rate, etc.)
    products_promoted = Column(JSON, nullable=True)  # List of product IDs/names
    created_at = Column(String, default=lambda: datetime.utcnow().isoformat())
    updated_at = Column(String, default=lambda: datetime.utcnow().isoformat(), onupdate=lambda: datetime.utcnow().isoformat())


class ImageAnalysisResult(Base):
    """Stored image analysis results linked to campaigns."""
    __tablename__ = "image_analysis_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_run_id = Column(String, nullable=False, index=True)
    campaign_id = Column(String, nullable=True, index=True)
    image_id = Column(String, nullable=False, index=True)
    image_path = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    visual_elements = Column(JSON, nullable=True)  # List of visual elements
    dominant_colors = Column(JSON, nullable=True)  # List of colors
    composition_analysis = Column(Text, nullable=True)
    text_content = Column(Text, nullable=True)
    overall_description = Column(Text, nullable=True)
    marketing_relevance = Column(Text, nullable=True)
    created_at = Column(String, default=lambda: datetime.utcnow().isoformat())


class VisualElementCorrelation(Base):
    """Stored correlations between visual elements and campaign performance."""
    __tablename__ = "visual_element_correlations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_run_id = Column(String, nullable=False, index=True)
    element_type = Column(String, nullable=False, index=True)
    element_description = Column(Text, nullable=True)
    average_performance = Column(JSON, nullable=True)  # Performance metrics
    performance_impact = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    campaign_count = Column(Integer, nullable=True)
    created_at = Column(String, default=lambda: datetime.utcnow().isoformat())


class ExperimentRun(Base):
    """Track experiment runs/workflows."""
    __tablename__ = "experiment_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_run_id = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    sql_query = Column(Text, nullable=True)  # User-adjusted SQL query
    status = Column(String, default="pending")  # pending, running, completed, failed
    config = Column(JSON, nullable=True)  # Experiment configuration
    results_summary = Column(JSON, nullable=True)  # Summary of results
    created_at = Column(String, default=lambda: datetime.utcnow().isoformat())
    updated_at = Column(String, default=lambda: datetime.utcnow().isoformat(), onupdate=lambda: datetime.utcnow().isoformat())
    completed_at = Column(String, nullable=True)

