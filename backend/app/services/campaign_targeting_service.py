"""Service for campaign targeting and audience segmentation."""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import text

from ..db.session import engine
from ..schemas.campaigns import AudienceSegment


class CampaignTargetingService:
    """Handle campaign targeting and audience segmentation."""

    def get_available_segments(self) -> List[AudienceSegment]:
        """Get available audience segments from database."""
        # For now, return some default segments
        # In production, these would come from the database
        segments = [
            AudienceSegment(
                segment_id="high_value",
                name="High Value Customers",
                description="Customers with high lifetime value",
                criteria={"ltv": ">1000", "orders": ">5"},
                size=1250,
            ),
            AudienceSegment(
                segment_id="price_sensitive",
                name="Price Sensitive Shoppers",
                description="Customers who respond to discounts",
                criteria={"discount_usage": ">3", "avg_order_value": "<100"},
                size=3200,
            ),
            AudienceSegment(
                segment_id="frequent_buyers",
                name="Frequent Buyers",
                description="Customers who purchase regularly",
                criteria={"purchase_frequency": ">monthly"},
                size=2100,
            ),
            AudienceSegment(
                segment_id="new_customers",
                name="New Customers",
                description="Customers acquired in last 30 days",
                criteria={"first_purchase_date": ">30_days_ago"},
                size=850,
            ),
            AudienceSegment(
                segment_id="at_risk",
                name="At Risk Customers",
                description="Customers who haven't purchased recently",
                criteria={"last_purchase_date": "<90_days_ago", "ltv": ">500"},
                size=1800,
            ),
        ]
        return segments

    def create_targeted_campaign(
        self,
        campaign_name: str,
        segment_ids: List[str],
        channel: str = "email",
        objective: str = "increase_revenue",
        constraints: Optional[Dict[str, Any]] = None,
        products: Optional[List[str]] = None,
        product_images: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """Create a targeted campaign for specified segments."""
        campaign_id = f"campaign_{uuid.uuid4().hex[:8]}"
        
        # Get segments
        all_segments = self.get_available_segments()
        selected_segments = [s for s in all_segments if s.segment_id in segment_ids]
        
        # Calculate estimated reach
        estimated_reach = sum(seg.size or 0 for seg in selected_segments)

        # Store campaign in database (simplified - in production would use proper models)
        try:
            with engine.begin() as connection:
                connection.execute(
                    text("""
                        CREATE TABLE IF NOT EXISTS targeted_campaigns (
                            campaign_id TEXT PRIMARY KEY,
                            campaign_name TEXT NOT NULL,
                            channel TEXT NOT NULL,
                            objective TEXT NOT NULL,
                            segment_ids TEXT NOT NULL,
                            constraints TEXT,
                            products TEXT,
                            product_images TEXT,
                            estimated_reach INTEGER,
                            status TEXT DEFAULT 'draft',
                            created_at TEXT NOT NULL
                        )
                    """)
                )
                
                import json
                connection.execute(
                    text("""
                        INSERT INTO targeted_campaigns 
                        (campaign_id, campaign_name, channel, objective, segment_ids, constraints, products, product_images, estimated_reach, status, created_at)
                        VALUES (:campaign_id, :campaign_name, :channel, :objective, :segment_ids, :constraints, :products, :product_images, :estimated_reach, :status, :created_at)
                    """),
                    {
                        "campaign_id": campaign_id,
                        "campaign_name": campaign_name,
                        "channel": channel,
                        "objective": objective,
                        "segment_ids": json.dumps(segment_ids),
                        "constraints": json.dumps(constraints) if constraints else None,
                        "products": json.dumps(products) if products else None,
                        "product_images": json.dumps(product_images) if product_images else None,
                        "estimated_reach": estimated_reach,
                        "status": "draft",
                        "created_at": datetime.utcnow().isoformat(),
                    }
                )
        except Exception as e:
            # If table creation fails, still return the campaign data
            pass

        return {
            "campaign_id": campaign_id,
            "campaign_name": campaign_name,
            "segments": [seg.model_dump() for seg in selected_segments],
            "estimated_reach": estimated_reach,
            "status": "draft",
            "created_at": datetime.utcnow().isoformat(),
            "product_images": product_images or [],
        }

    def analyze_targeting(
        self,
        campaign_id: Optional[str] = None,
        segment_ids: Optional[List[str]] = None,
        date_range: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Analyze targeting effectiveness."""
        # Get segments
        all_segments = self.get_available_segments()
        segments_to_analyze = all_segments
        
        if segment_ids:
            segments_to_analyze = [s for s in all_segments if s.segment_id in segment_ids]

        # Simulate performance analysis
        segment_performance = []
        for segment in segments_to_analyze:
            # In production, this would query actual campaign performance data
            segment_performance.append({
                "segment_id": segment.segment_id,
                "segment_name": segment.name,
                "open_rate": 0.25 + (hash(segment.segment_id) % 20) / 100,  # Simulated
                "click_rate": 0.05 + (hash(segment.segment_id) % 10) / 100,
                "conversion_rate": 0.02 + (hash(segment.segment_id) % 5) / 100,
                "revenue": (segment.size or 0) * 50,  # Simulated
            })

        # Generate recommendations
        recommendations = []
        if segment_performance:
            avg_open_rate = sum(p["open_rate"] for p in segment_performance) / len(segment_performance)
            if avg_open_rate < 0.2:
                recommendations.append("Consider A/B testing subject lines to improve open rates")
            if avg_open_rate > 0.3:
                recommendations.append("High open rate segment - consider increasing send frequency")

            avg_conversion = sum(p["conversion_rate"] for p in segment_performance) / len(segment_performance)
            if avg_conversion < 0.01:
                recommendations.append("Low conversion rate - review offer and CTA placement")
            if avg_conversion > 0.03:
                recommendations.append("High converting segment - scale up campaign budget")

        summary = f"Analyzed {len(segments_to_analyze)} segments. Average open rate: {avg_open_rate:.1%}, Average conversion: {avg_conversion:.1%}"

        return {
            "campaign_id": campaign_id,
            "segment_performance": segment_performance,
            "recommendations": recommendations,
            "summary": summary,
        }

    def get_campaign_performance(self, campaign_id: str) -> Dict[str, Any]:
        """Get campaign performance breakdown by segment."""
        # In production, this would query actual performance data
        # For now, return simulated data
        
        try:
            with engine.begin() as connection:
                result = connection.execute(
                    text("SELECT * FROM targeted_campaigns WHERE campaign_id = :campaign_id"),
                    {"campaign_id": campaign_id}
                )
                row = result.fetchone()
                if not row:
                    return {
                        "campaign_id": campaign_id,
                        "error": "Campaign not found",
                    }
                
                import json
                segment_ids = json.loads(row._mapping.get("segment_ids", "[]"))
        except Exception:
            segment_ids = []

        # Get performance for segments
        all_segments = self.get_available_segments()
        selected_segments = [s for s in all_segments if s.segment_id in segment_ids]

        overall_performance = {
            "total_sent": sum(s.size or 0 for s in selected_segments),
            "total_opens": 0,
            "total_clicks": 0,
            "total_conversions": 0,
            "total_revenue": 0,
        }

        segment_performance = []
        for segment in selected_segments:
            # Simulated performance
            opens = int((segment.size or 0) * 0.25)
            clicks = int(opens * 0.1)
            conversions = int(clicks * 0.05)
            revenue = conversions * 50

            overall_performance["total_opens"] += opens
            overall_performance["total_clicks"] += clicks
            overall_performance["total_conversions"] += conversions
            overall_performance["total_revenue"] += revenue

            segment_performance.append({
                "segment_id": segment.segment_id,
                "segment_name": segment.name,
                "sent": segment.size or 0,
                "opens": opens,
                "clicks": clicks,
                "conversions": conversions,
                "revenue": revenue,
                "open_rate": opens / (segment.size or 1),
                "click_rate": clicks / (segment.size or 1),
                "conversion_rate": conversions / (segment.size or 1),
            })

        # Sort by performance
        segment_performance.sort(key=lambda x: x["revenue"], reverse=True)
        top_performing_segments = [p["segment_id"] for p in segment_performance[:3]]

        return {
            "campaign_id": campaign_id,
            "overall_performance": overall_performance,
            "segment_performance": segment_performance,
            "top_performing_segments": top_performing_segments,
        }

