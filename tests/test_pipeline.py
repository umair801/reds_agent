"""
Test the AI lead extraction pipeline against scraped Craigslist leads.
Verifies Claude AI correctly scores and structures raw listing data.
"""

import asyncio
import structlog
from app.utils.logger import setup_logging
from app.agents.craigslist_scraper import CraigslistScraper
from app.pipeline.lead_extractor import LeadExtractor

log = structlog.get_logger()


async def test_pipeline() -> None:
    setup_logging()

    print("\n--- Testing AI Lead Extraction Pipeline ---\n")

    # Step 1: Scrape 5 raw leads
    print("Scraping 5 listings from Houston...")
    scraper = CraigslistScraper(headless=True)
    raw_leads = await scraper.scrape_city(city="houston", max_listings=5)
    print(f"Raw leads scraped: {len(raw_leads)}\n")

    # Step 2: Run AI extraction
    print("Sending to Claude AI for extraction and scoring...\n")
    extractor = LeadExtractor(distress_threshold=30)
    qualified, disqualified = await extractor.process_batch(raw_leads)

    # Step 3: Print results
    print(f"QUALIFIED   (score >= 30): {len(qualified)}")
    print(f"DISQUALIFIED (score < 30): {len(disqualified)}")
    print()

    for i, lead in enumerate(qualified, 1):
        print(f"--- Qualified Lead {i} ---")
        print(f"Name          : {lead.first_name} {lead.last_name}")
        print(f"Phone         : {lead.phone}")
        print(f"Email         : {lead.email}")
        print(f"Address       : {lead.address}")
        print(f"City/State    : {lead.city}, {lead.state}")
        print(f"Asking Price  : ${lead.asking_price:,}" if lead.asking_price else "Asking Price  : N/A")
        print(f"Distress Score: {lead.distress_score}/100")
        print(f"Signals       : {', '.join(lead.distress_signals)}")
        print(f"Motivation    : {lead.motivation_summary}")
        print(f"Status        : {lead.status}")
        print()

    if qualified:
        print("Pipeline working. Leads are scored and structured.")
        print("Proceeding to Step 5.")
    else:
        print("All leads disqualified. Lower threshold or check AI response.")


if __name__ == "__main__":
    asyncio.run(test_pipeline())