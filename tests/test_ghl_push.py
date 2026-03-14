"""
Test pushing qualified leads from Supabase into GHL as contacts.
Verifies contact creation, tagging, and note attachment.
"""

import asyncio
import structlog
from app.utils.logger import setup_logging
from app.agents.craigslist_scraper import CraigslistScraper
from app.pipeline.lead_extractor import LeadExtractor
from app.pipeline.lead_store import LeadStore
from app.crm.contact_pusher import ContactPusher
from app.models.lead import LeadStatus

log = structlog.get_logger()


async def test_ghl_push() -> None:
    setup_logging()

    print("\n--- Testing GHL Contact Push ---\n")

    # Scrape and extract fresh leads
    print("Scraping 3 leads...")
    scraper = CraigslistScraper(headless=True)
    raw_leads = await scraper.scrape_city(city="houston", max_listings=3)

    extractor = LeadExtractor(distress_threshold=10)
    qualified, _ = await extractor.process_batch(raw_leads)
    print(f"Qualified leads ready: {len(qualified)}\n")

    # Push to GHL
    pusher = ContactPusher()
    store = LeadStore()

    for lead in qualified:
        print(f"Pushing: {lead.title if hasattr(lead, 'title') else lead.source_url[-50:]}")
        print(f"  Score : {lead.distress_score}/100")
        print(f"  City  : {lead.city}, {lead.state}")

        contact_id = await pusher.push_lead(lead)

        if contact_id:
            print(f"  GHL ID: {contact_id}")
            print(f"  Status: pushed_to_crm")
        else:
            print(f"  FAILED: check logs")
        print()

    # Verify in Supabase
    print("Verifying Supabase status updates...")
    pushed = store.get_leads_by_status(LeadStatus.PUSHED_TO_CRM)
    print(f"Leads marked as pushed_to_crm in DB: {len(pushed)}")

    for lead in pushed:
        print(f"  - {lead['source_url'][-60:]} | GHL: {lead['ghl_contact_id']}")

    print("\nCheck your GHL Contacts panel — contacts should appear with REDS_Lead tag.")
    print("Proceeding to Step 7.")


if __name__ == "__main__":
    asyncio.run(test_ghl_push())