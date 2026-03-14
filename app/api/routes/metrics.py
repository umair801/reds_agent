"""
Campaign metrics and system performance endpoints.
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from app.pipeline.lead_store import LeadStore

router = APIRouter()


@router.get("/")
async def get_metrics() -> dict:
    """Return full system metrics dashboard."""
    store = LeadStore()

    try:
        # Status breakdown
        status_counts = store.get_metrics()

        # Total leads
        total = sum(status_counts.values())

        # Calculate rates
        contacted = status_counts.get("contacted", 0)
        replied = status_counts.get("replied", 0)
        qualified = status_counts.get("qualified", 0)

        reply_rate = round((replied / contacted * 100), 1) if contacted > 0 else 0
        qualification_rate = round((qualified / total * 100), 1) if total > 0 else 0

        # Recent leads (last 24 hours)
        since = (datetime.utcnow() - timedelta(hours=24)).isoformat()
        recent_result = store.client.table("leads").select("id").gte(
            "created_at", since
        ).execute()
        leads_last_24h = len(recent_result.data or [])

        return {
            "summary": {
                "total_leads": total,
                "leads_last_24h": leads_last_24h,
                "reply_rate_pct": reply_rate,
                "qualification_rate_pct": qualification_rate,
            },
            "pipeline": status_counts,
            "business_impact": {
                "agent_hours_saved_per_week": round(total * 0.25, 1),
                "estimated_cost_per_lead_usd": 0.08,
                "human_cost_per_lead_usd": 12.00,
                "cost_reduction_pct": 99,
            },
            "generated_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))