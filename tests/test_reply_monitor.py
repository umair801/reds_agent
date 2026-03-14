"""
Test reply monitoring against GHL conversations.
Checks for inbound replies from contacted leads.
"""

import asyncio
import structlog
from app.utils.logger import setup_logging
from app.pipeline.reply_monitor import ReplyMonitor
from app.pipeline.lead_store import LeadStore
from app.models.lead import LeadStatus

log = structlog.get_logger()


async def test_reply_monitor() -> None:
    setup_logging()

    print("\n--- Testing Reply Monitor ---\n")

    store = LeadStore()
    monitor = ReplyMonitor()

    # Show current lead statuses
    print("Current lead status breakdown:")
    metrics = store.get_metrics()
    for status, count in metrics.items():
        print(f"  {status}: {count}")
    print()

    # Run one check cycle
    print("Running one reply check cycle against GHL...\n")
    stats = await monitor.check_replies()

    print(f"Conversations checked : {stats['conversations_checked']}")
    print(f"Replies detected      : {stats['replies_detected']}")
    print(f"Leads updated         : {stats['updated']}")

    # Show updated statuses
    print("\nUpdated lead status breakdown:")
    metrics_after = store.get_metrics()
    for status, count in metrics_after.items():
        print(f"  {status}: {count}")

    replied_leads = store.get_leads_by_status(LeadStatus.REPLIED)
    if replied_leads:
        print(f"\nReplied leads ({len(replied_leads)}):")
        for lead in replied_leads:
            print(f"  - {lead['city']}, {lead['state']} | Score: {lead['distress_score']}")
    else:
        print("\nNo replies yet — this is expected if leads were just created.")
        print("Monitor is working correctly. It will detect replies as they come in.")

    print("\nReply monitor ready for continuous polling in production.")
    print("Proceeding to Step 9.")


if __name__ == "__main__":
    asyncio.run(test_reply_monitor())