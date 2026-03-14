"""
Pushes qualified leads from Supabase into GoHighLevel as contacts.
Handles dedup at CRM level and updates lead status after push.
"""

import structlog
from app.crm.ghl_client import GHLClient
from app.pipeline.lead_store import LeadStore
from app.models.lead import QualifiedLead, LeadStatus

log = structlog.get_logger()


class ContactPusher:
    """
    Orchestrates pushing qualified leads to GHL CRM.
    Checks for existing contacts before creating new ones.
    """

    def __init__(self) -> None:
        self.ghl = GHLClient()
        self.store = LeadStore()

    async def push_lead(self, lead: QualifiedLead) -> str | None:
        """
        Push a single qualified lead to GHL as a contact.
        Returns GHL contact_id or None on failure.
        """
        # Check if contact already exists by phone
        if lead.phone:
            existing = await self.ghl.get_contact_by_phone(lead.phone)
            if existing:
                contact_id = existing.get("id")
                log.info(
                    "ghl_contact_exists",
                    contact_id=contact_id,
                    phone=lead.phone,
                )
                self.store.update_status(
                    lead.source_url,
                    LeadStatus.PUSHED_TO_CRM,
                    contact_id,
                )
                return contact_id

        # Build payload from lead
        lead_data = {
            "first_name": lead.first_name,
            "last_name": lead.last_name,
            "phone": lead.phone,
            "email": lead.email,
            "address": lead.address,
            "city": lead.city,
            "state": lead.state,
            "source": lead.source,
            "source_url": lead.source_url,
            "asking_price": lead.asking_price,
            "distress_score": lead.distress_score,
            "distress_signals": lead.distress_signals,
            "motivation_summary": lead.motivation_summary,
        }

        contact = await self.ghl.create_contact(lead_data)

        if not contact:
            log.error("push_failed", source_url=lead.source_url)
            return None

        contact_id = contact.get("id")

        # Add motivation note to contact
        if lead.motivation_summary and contact_id:
            note = (
                f"REDS AI Analysis\n"
                f"Distress Score: {lead.distress_score}/100\n"
                f"Signals: {', '.join(lead.distress_signals)}\n"
                f"Motivation: {lead.motivation_summary}\n"
                f"Source: {lead.source_url}"
            )
            await self.ghl.add_note_to_contact(contact_id, note)

        # Update Supabase status
        self.store.update_status(
            lead.source_url,
            LeadStatus.PUSHED_TO_CRM,
            contact_id,
        )

        log.info(
            "lead_pushed_to_crm",
            contact_id=contact_id,
            distress_score=lead.distress_score,
        )
        return contact_id

    async def push_batch(
        self, leads: list[QualifiedLead]
    ) -> tuple[int, int]:
        """
        Push a list of qualified leads to GHL.
        Returns (success_count, failure_count).
        """
        success = 0
        failure = 0

        for lead in leads:
            contact_id = await self.push_lead(lead)
            if contact_id:
                success += 1
            else:
                failure += 1

        log.info(
            "batch_push_complete",
            success=success,
            failure=failure,
        )
        return success, failure