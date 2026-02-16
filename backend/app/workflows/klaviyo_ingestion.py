"""Workflow for ingesting Klaviyo campaign data from CSV files."""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.engine import Engine

from ..core.config import settings
from ..db.session import engine


def _normalize_identifier(raw: str) -> str:
    """Normalize column names to valid SQL identifiers."""
    cleaned = re.sub(r"[^\w\s-]", " ", raw).lower()
    cleaned = re.sub(r"[\s-]+", "_", cleaned).strip("_")
    return cleaned or "column"


def _normalize_klaviyo_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize Klaviyo CSV columns to standard names."""
    column_mapping = {}
    
    # Common Klaviyo column name variations
    mappings = {
        "campaign_id": ["campaign id", "campaign_id", "id", "campaign identifier", "campaign id"],
        "campaign_name": ["campaign name", "campaign_name", "name", "campaign"],
        "subject": ["subject", "email subject", "subject line"],
        "sent_at": ["sent at", "sent_at", "date sent", "send date", "created at", "send time"],
        "sent_count": ["sent", "sent count", "sent_count", "emails sent", "total sent", "total recipients", "successful deliveries"],
        "delivered_count": ["delivered", "delivered count", "delivered_count", "emails delivered", "successful deliveries"],
        "bounced_count": ["bounced", "bounced count", "bounced_count", "bounces"],
        "opened_count": ["opened", "opened count", "opened_count", "opens", "unique opens", "unique opens"],
        "clicked_count": ["clicked", "clicked count", "clicked_count", "clicks", "unique clicks", "unique clicks"],
        "converted_count": ["converted", "converted count", "converted_count", "conversions", "purchases", "unique placed order"],
        "revenue": ["revenue", "total revenue", "revenue generated", "sales"],
        "open_rate": ["open rate", "open_rate", "open %", "open percentage"],
        "click_rate": ["click rate", "click_rate", "click %", "click percentage", "ctr"],
        "conversion_rate": ["conversion rate", "conversion_rate", "conversion %", "conversion percentage", "placed order rate"],
        "unsubscribed_count": ["unsubscribed", "unsubscribed count", "unsubscribed_count", "unsubscribes"],
        "spam_count": ["spam", "spam count", "spam_count", "spam reports", "spam complaints"],
    }
    
    df_columns_lower = {col.lower(): col for col in df.columns}
    
    for standard_name, variations in mappings.items():
        for variation in variations:
            if variation.lower() in df_columns_lower:
                column_mapping[df_columns_lower[variation.lower()]] = standard_name
                break
    
    # Rename columns
    df = df.rename(columns=column_mapping)
    
    # Calculate rates if not present
    if "open_rate" not in df.columns and "opened_count" in df.columns and "sent_count" in df.columns:
        df["open_rate"] = df["opened_count"] / df["sent_count"].replace(0, 1)
    elif "open_rate" in df.columns:
        # Convert percentage strings to decimals (e.g., "40.34%" -> 0.4034)
        df["open_rate"] = df["open_rate"].apply(lambda x: float(str(x).replace("%", "")) / 100 if pd.notna(x) and "%" in str(x) else (float(x) if pd.notna(x) else None))
    
    if "click_rate" not in df.columns and "clicked_count" in df.columns and "sent_count" in df.columns:
        df["click_rate"] = df["clicked_count"] / df["sent_count"].replace(0, 1)
    elif "click_rate" in df.columns:
        df["click_rate"] = df["click_rate"].apply(lambda x: float(str(x).replace("%", "")) / 100 if pd.notna(x) and "%" in str(x) else (float(x) if pd.notna(x) else None))
    
    if "conversion_rate" not in df.columns and "converted_count" in df.columns and "sent_count" in df.columns:
        df["conversion_rate"] = df["converted_count"] / df["sent_count"].replace(0, 1)
    elif "conversion_rate" in df.columns:
        df["conversion_rate"] = df["conversion_rate"].apply(lambda x: float(str(x).replace("%", "")) / 100 if pd.notna(x) and "%" in str(x) else (float(x) if pd.notna(x) else None))
    
    return df


def _ensure_campaigns_table(db_engine: Engine) -> None:
    """Ensure the campaigns table exists with proper schema."""
    create_stmt = text("""
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id TEXT NOT NULL,
            campaign_name TEXT,
            subject TEXT,
            sent_at TEXT,
            sent_count INTEGER DEFAULT 0,
            delivered_count INTEGER DEFAULT 0,
            bounced_count INTEGER DEFAULT 0,
            opened_count INTEGER DEFAULT 0,
            clicked_count INTEGER DEFAULT 0,
            converted_count INTEGER DEFAULT 0,
            revenue REAL DEFAULT 0.0,
            open_rate REAL,
            click_rate REAL,
            conversion_rate REAL,
            unsubscribed_count INTEGER DEFAULT 0,
            spam_count INTEGER DEFAULT 0,
            products TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(campaign_id)
        )
    """)
    
    with db_engine.begin() as connection:
        connection.execute(create_stmt)
        
        # Create index for faster queries
        try:
            connection.execute(text("CREATE INDEX IF NOT EXISTS idx_campaigns_campaign_id ON campaigns(campaign_id)"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS idx_campaigns_sent_at ON campaigns(sent_at)"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS idx_campaigns_conversion_rate ON campaigns(conversion_rate)"))
        except:
            pass  # Indexes might already exist


def ingest_klaviyo_csv(
    csv_file_path: str,
    table_name: str = "campaigns",
    db_engine: Optional[Engine] = None,
) -> Dict[str, any]:
    """
    Ingest Klaviyo campaign CSV file into the campaigns table.
    
    Args:
        csv_file_path: Path to the Klaviyo CSV file
        table_name: Name of the table to create/update (default: "campaigns")
        db_engine: Optional database engine override
    
    Returns:
        Dictionary with ingestion results
    """
    work_engine = db_engine or engine
    csv_path = Path(csv_file_path)
    
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
    
    # Load and normalize CSV
    df = pd.read_csv(csv_path)
    df = _normalize_klaviyo_columns(df)
    
    # Ensure campaigns table exists
    _ensure_campaigns_table(work_engine)
    
    # Prepare data for insertion
    now = datetime.utcnow().isoformat()
    inserted_count = 0
    updated_count = 0
    errors = []
    
    with work_engine.begin() as connection:
        for _, row in df.iterrows():
            try:
                # Extract campaign_id (required)
                campaign_id = str(row.get("campaign_id", "")).strip()
                if not campaign_id:
                    # Try to generate from campaign_name if available
                    campaign_name = str(row.get("campaign_name", "")).strip()
                    if campaign_name:
                        campaign_id = _normalize_identifier(campaign_name)
                    else:
                        errors.append(f"Row {len(errors) + 1}: Missing campaign_id and campaign_name")
                        continue
                
                # Prepare data
                campaign_data = {
                    "campaign_id": campaign_id,
                    "campaign_name": str(row.get("campaign_name", "")).strip() or None,
                    "subject": str(row.get("subject", "")).strip() or None,
                    "sent_at": str(row.get("sent_at", "")).strip() or None,
                    "sent_count": int(row.get("sent_count", 0)) if pd.notna(row.get("sent_count")) else 0,
                    "delivered_count": int(row.get("delivered_count", 0)) if pd.notna(row.get("delivered_count")) else 0,
                    "bounced_count": int(row.get("bounced_count", 0)) if pd.notna(row.get("bounced_count")) else 0,
                    "opened_count": int(row.get("opened_count", 0)) if pd.notna(row.get("opened_count")) else 0,
                    "clicked_count": int(row.get("clicked_count", 0)) if pd.notna(row.get("clicked_count")) else 0,
                    "converted_count": int(row.get("converted_count", 0)) if pd.notna(row.get("converted_count")) else 0,
                    "revenue": float(row.get("revenue", 0.0)) if pd.notna(row.get("revenue")) else 0.0,
                    "open_rate": float(row.get("open_rate", 0.0)) if pd.notna(row.get("open_rate")) else None,
                    "click_rate": float(row.get("click_rate", 0.0)) if pd.notna(row.get("click_rate")) else None,
                    "conversion_rate": float(row.get("conversion_rate", 0.0)) if pd.notna(row.get("conversion_rate")) else None,
                    "unsubscribed_count": int(row.get("unsubscribed_count", 0)) if pd.notna(row.get("unsubscribed_count")) else 0,
                    "spam_count": int(row.get("spam_count", 0)) if pd.notna(row.get("spam_count")) else 0,
                    "products": json.dumps(row.get("products", [])) if "products" in row and pd.notna(row.get("products")) else None,
                    "created_at": now,
                    "updated_at": now,
                }
                
                # Check if campaign exists
                check_query = text("SELECT campaign_id FROM campaigns WHERE campaign_id = :campaign_id")
                existing = connection.execute(check_query, {"campaign_id": campaign_id}).fetchone()
                
                if existing:
                    # Update existing campaign
                    update_query = text("""
                        UPDATE campaigns SET
                            campaign_name = :campaign_name,
                            subject = :subject,
                            sent_at = :sent_at,
                            sent_count = :sent_count,
                            delivered_count = :delivered_count,
                            bounced_count = :bounced_count,
                            opened_count = :opened_count,
                            clicked_count = :clicked_count,
                            converted_count = :converted_count,
                            revenue = :revenue,
                            open_rate = :open_rate,
                            click_rate = :click_rate,
                            conversion_rate = :conversion_rate,
                            unsubscribed_count = :unsubscribed_count,
                            spam_count = :spam_count,
                            products = :products,
                            updated_at = :updated_at
                        WHERE campaign_id = :campaign_id
                    """)
                    connection.execute(update_query, campaign_data)
                    updated_count += 1
                else:
                    # Insert new campaign
                    insert_query = text("""
                        INSERT INTO campaigns (
                            campaign_id, campaign_name, subject, sent_at,
                            sent_count, delivered_count, bounced_count,
                            opened_count, clicked_count, converted_count,
                            revenue, open_rate, click_rate, conversion_rate,
                            unsubscribed_count, spam_count, products,
                            created_at, updated_at
                        ) VALUES (
                            :campaign_id, :campaign_name, :subject, :sent_at,
                            :sent_count, :delivered_count, :bounced_count,
                            :opened_count, :clicked_count, :converted_count,
                            :revenue, :open_rate, :click_rate, :conversion_rate,
                            :unsubscribed_count, :spam_count, :products,
                            :created_at, :updated_at
                        )
                    """)
                    connection.execute(insert_query, campaign_data)
                    inserted_count += 1
                    
            except Exception as e:
                errors.append(f"Row {len(errors) + inserted_count + updated_count + 1}: {str(e)}")
                continue
    
    # Also register in dataset registry for prompt-to-SQL discovery
    from ..workflows.local_csv_ingestion import _ensure_registry, _record_dataset, IngestedDataset
    
    _ensure_registry(work_engine)
    dataset = IngestedDataset(
        table_name=table_name,
        business="Klaviyo",
        category="campaigns",
        dataset_name="klaviyo_campaigns",
        source_file=str(csv_path),
        row_count=len(df),
        columns=list(df.columns),
    )
    _record_dataset(work_engine, dataset)
    
    return {
        "status": "completed",
        "table_name": table_name,
        "total_rows": len(df),
        "inserted": inserted_count,
        "updated": updated_count,
        "errors": errors if errors else None,
        "columns": list(df.columns),
    }

