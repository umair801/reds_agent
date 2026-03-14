"""
Test the Craigslist scraper against one city.
Runs headed (visible browser) so you can watch it work.
"""

import asyncio
import structlog
from app.utils.logger import setup_logging
from app.agents.craigslist_scraper import CraigslistScraper

log = structlog.get_logger()


async def test_scraper() -> None:
    setup_logging()

    print("\n--- Testing Craigslist FSBO Scraper ---\n")
    print("City: Houston | Max listings: 5")
    print("Watch the browser open...\n")

    # headless=False so you can SEE it working
    scraper = CraigslistScraper(headless=False)
    leads = await scraper.scrape_city(city="houston", max_listings=5)

    print(f"\nLeads scraped: {len(leads)}\n")

    for i, lead in enumerate(leads, 1):
        print(f"--- Lead {i} ---")
        print(f"Title       : {lead.title[:80]}")
        print(f"Price       : {lead.asking_price}")
        print(f"Location    : {lead.location}")
        print(f"Phone       : {lead.phone}")
        print(f"Email       : {lead.email}")
        print(f"Post Date   : {lead.post_date}")
        print(f"Description : {lead.description[:150]}...")
        print(f"URL         : {lead.source_url}")
        print()

    if leads:
        print("Scraper is working. Proceeding to Step 4.")
    else:
        print("No leads returned. Check terminal for errors.")


if __name__ == "__main__":
    asyncio.run(test_scraper())