"""
Polls GoHighLevel conversations for replies from REDS leads.
Updates Supabase lead status when a seller replies.
"""

import asyncio
import structlog
from app.crm.ghl_client import GHLClient
from app.pipeline.lead_store import LeadStore
from app.models.lead import LeadStatus

log = structlog.get_logger()


class ReplyMonitor:
    """
    Monitors GHL conversations for inbound replies from contacted leads.
    Runs as a polling loop — checks every N seconds.
    """

    def __init__(self, poll_interval_seconds: int = 300) -> None:
        self.ghl = GHLClient()
        self.store = LeadStore()
        self.poll_interval = poll_interval_seconds

    async def check_replies(self) -> dict[str, int]:
        """
        Single pass — fetch conversations and detect replies.
        Returns counts of new replies found and updated.
        """
        stats = {"conversations_checked": 0, "replies_detected": 0, "updated": 0}

        # Get all leads currently in contacted status
        contacted_leads = self.store.get_leads_by_status(LeadStatus.CONTACTED)
        if not contacted_leads:
            log.info("no_contacted_leads_to_monitor")
            return stats

        # Build lookup: ghl_contact_id -> lead record
        contact_map: dict[str, dict] = {
            lead["ghl_contact_id"]: lead
            for lead in contacted_leads
            if lead.get("ghl_contact_id")
        }

        if not contact_map:
            log.info("no_ghl_contact_ids_found")
            return stats

        # Fetch recent conversations from GHL
        conversations = await self.ghl.get_conversations(limit=50)
        stats["conversations_checked"] = len(conversations)

        for convo in conversations:
            contact_id = convo.get("contactId")
            if contact_id not in contact_map:
                continue

            lead = contact_map[contact_id]
            last_message_type = convo.get("lastMessageType", "")
            last_message_direction = convo.get("lastMessageDirection", "")

            # Inbound = seller replied
            if last_message_direction == "inbound":
                stats["replies_detected"] += 1

                log.info(
                    "reply_detected",
                    contact_id=contact_id,
                    conversation_id=convo.get("id"),
                    last_message_type=last_message_type,
                    city=lead.get("city"),
                    distress_score=lead.get("distress_score"),
                )

                updated = self.store.update_status(
                    lead["source_url"],
                    LeadStatus.REPLIED,
                )

                if updated:
                    stats["updated"] += 1

        log.info(
            "reply_check_complete",
            conversations_checked=stats["conversations_checked"],
            replies_detected=stats["replies_detected"],
            updated=stats["updated"],
        )

        return stats

    async def run_forever(self) -> None:
        """
        Continuous polling loop.
        Checks for replies every poll_interval_seconds.
        """
        log.info(
            "reply_monitor_started",
            poll_interval_seconds=self.poll_interval,
        )

        while True:
            try:
                stats = await self.check_replies()
                log.info("poll_cycle_complete", stats=stats)
            except Exception as e:
                log.error("poll_cycle_error", error=str(e))

            await asyncio.sleep(self.poll_interval)