"""
Lead management endpoints.
Returns lead data from Supabase by status.
"""

from fastapi import APIRouter, HTTPException, Query
from app.pipeline.lead_store import LeadStore
from app.models.lead import LeadStatus

router = APIRouter()


@router.get("/")
async def get_leads(
    status: str = Query(default=None, description="Filter by lead status"),
    limit: int = Query(default=50, ge=1, le=500),
) -> dict:
    """Return leads filtered by status."""
    store = LeadStore()

    try:
        if status:
            try:
                lead_status = LeadStatus(status)
            except ValueError:
                valid = [s.value for s in LeadStatus]
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status. Valid values: {valid}",
                )
            leads = store.get_leads_by_status(lead_status)
        else:
            # Return all leads
            result = store.client.table("leads").select("*").order(
                "created_at", desc=True
            ).limit(limit).execute()
            leads = result.data or []

        return {
            "count": len(leads),
            "status_filter": status,
            "leads": leads,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{lead_id}")
async def get_lead(lead_id: str) -> dict:
    """Return a single lead by ID."""
    store = LeadStore()

    try:
        result = store.client.table("leads").select("*").eq(
            "id", lead_id
        ).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Lead not found")

        return result.data[0]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))