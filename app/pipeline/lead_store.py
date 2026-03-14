"""
Supabase storage layer for leads.
Handles deduplication, insertion, and status updates.
"""

import structlog
from supabase import create_client, Client
from app.models.lead import QualifiedLead, LeadStatus
from app.utils.config import settings

log = structlog.get_logger()


class LeadStore:
    """
    Manages lead persistence in Supabase.
    Prevents duplicate outreach via source_url deduplication.
    """

    def __init__(self) -> None:
        self.client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY,
        )

    def is_duplicate(self, source_url: str) -> bool:
        """
        Check if a lead with this URL already exists.
        Returns True if duplicate, False if new.
        """
        try:
            result = (
                self.client.table("leads")
                .select("id")
                .eq("source_url", source_url)
                .execute()
            )
            return len(result.data) > 0
        except Exception as e:
            log.error("dedup_check_failed", error=str(e), url=source_url)
            return False

    def save_lead(self, lead: QualifiedLead) -> str | None:
        """
        Insert a new lead into Supabase.
        Returns the new lead's UUID or None on failure.
        """
        try:
            data = {
                "source": lead.source,
                "source_url": lead.source_url,
                "scraped_at": lead.scraped_at.isoformat() if lead.scraped_at else None,
                "processed_at": lead.processed_at.isoformat() if lead.processed_at else None,
                "first_name": lead.first_name,
                "last_name": lead.last_name,
                "phone": lead.phone,
                "email": lead.email,
                "address": lead.address,
                "city": lead.city,
                "state": lead.state,
                "asking_price": lead.asking_price,
                "days_on_market": lead.days_on_market,
                "distress_score": lead.distress_score,
                "distress_signals": lead.distress_signals,
                "motivation_summary": lead.motivation_summary,
                "status": lead.status.value,
                "ghl_contact_id": lead.ghl_contact_id,
            }

            result = self.client.table("leads").insert(data).execute()

            if result.data:
                lead_id = result.data[0]["id"]
                log.info(
                    "lead_saved",
                    lead_id=lead_id,
                    source_url=lead.source_url,
                    distress_score=lead.distress_score,
                )
                return lead_id

        except Exception as e:
            log.error("lead_save_failed", error=str(e), url=lead.source_url)

        return None

    def update_status(
        self, source_url: str, status: LeadStatus, ghl_contact_id: str | None = None
    ) -> bool:
        """Update lead status and optionally set GHL contact ID."""
        try:
            update_data: dict = {"status": status.value}
            if ghl_contact_id:
                update_data["ghl_contact_id"] = ghl_contact_id

            self.client.table("leads").update(update_data).eq(
                "source_url", source_url
            ).execute()

            log.info(
                "lead_status_updated",
                source_url=source_url,
                status=status.value,
                ghl_contact_id=ghl_contact_id,
            )
            return True

        except Exception as e:
            log.error("status_update_failed", error=str(e))
            return False

    def get_leads_by_status(self, status: LeadStatus) -> list[dict]:
        """Fetch all leads with a given status."""
        try:
            result = (
                self.client.table("leads")
                .select("*")
                .eq("status", status.value)
                .order("created_at", desc=True)
                .execute()
            )
            return result.data or []
        except Exception as e:
            log.error("fetch_leads_failed", error=str(e))
            return []

    def get_metrics(self) -> dict:
        """Return basic lead counts by status."""
        try:
            result = self.client.table("leads").select("status").execute()
            counts: dict[str, int] = {}
            for row in result.data:
                s = row["status"]
                counts[s] = counts.get(s, 0) + 1
            return counts
        except Exception as e:
            log.error("metrics_fetch_failed", error=str(e))
            return {}