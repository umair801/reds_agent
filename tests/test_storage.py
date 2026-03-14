"""
Test Supabase connection, deduplication, and lead storage.
"""

import asyncio
import structlog
from app.utils.logger import setup_logging
from app.agents.craigslist_scraper import CraigslistScraper
from app.pipeline.lead_extractor import LeadExtractor
from app.pipeline.lead_store import LeadStore
from app.models.lead import LeadStatus

log = structlog.get_logger()


async def test_storage() -> None:
    setup_logging()

    print("\n--- Testing Supabase Lead Storage ---\n")

    store = LeadStore()

    # Step 1: Scrape and extract
    print("Scraping 3 leads from Houston...")
    scraper = CraigslistScraper(headless=True)
    raw_leads = await scraper.scrape_city(city="houston", max_listings=3)

    extractor = LeadExtractor(distress_threshold=10)
    qualified, _ = await extractor.process_batch(raw_leads)
    print(f"Leads to store: {len(qualified)}\n")

    # Step 2: Save leads with dedup check
    saved = 0
    skipped = 0

    for lead in qualified:
        if store.is_duplicate(lead.source_url):
            print(f"DUPLICATE — skipped: {lead.source_url[-50:]}")
            skipped += 1
        else:
            lead_id = store.save_lead(lead)
            if lead_id:
                print(f"SAVED — ID: {lead_id}")
                print(f"         Score: {lead.distress_score} | {lead.city}, {lead.state}")
                saved += 1

    print(f"\nSaved: {saved} | Skipped (duplicates): {skipped}")

    # Step 3: Run test again to confirm dedup works
    print("\nRunning again to verify deduplication...")
    saved2 = 0
    skipped2 = 0
    for lead in qualified:
        if store.is_duplicate(lead.source_url):
            skipped2 += 1
        else:
            store.save_lead(lead)
            saved2 += 1

    print(f"Second run — Saved: {saved2} | Skipped: {skipped2}")

    # Step 4: Show metrics
    print(f"\nDatabase metrics: {store.get_metrics()}")

    if saved > 0 and skipped2 == len(qualified):
        print("\nStorage + deduplication working correctly.")
        print("Proceeding to Step 6.")


if __name__ == "__main__":
    asyncio.run(test_storage())