"""
Craigslist FSBO listing scraper using Playwright.
Targets real estate for-sale-by-owner listings.
Uses verified selectors from live Craigslist HTML (March 2026).
"""

import asyncio
import re
import structlog
from playwright.async_api import async_playwright, Page, Browser
from app.models.lead import RawLead

log = structlog.get_logger()

CRAIGSLIST_CITIES = [
    "houston",
    "dallas",
    "phoenix",
    "atlanta",
    "chicago",
]

FSBO_SEARCH_URL = (
    "https://{city}.craigslist.org/search/rea"
    "?query=by+owner&sort=date"
)


class CraigslistScraper:
    """
    Playwright-based scraper for Craigslist real estate FSBO listings.
    Selectors verified against live Craigslist HTML March 2026.
    """

    def __init__(self, headless: bool = True) -> None:
        self.headless = headless
        self.scraped_count = 0

    async def scrape_city(
        self, city: str, max_listings: int = 20
    ) -> list[RawLead]:
        """Scrape FSBO listings from one Craigslist city."""
        leads: list[RawLead] = []
        url = FSBO_SEARCH_URL.format(city=city)

        log.info("scraper_starting", city=city, url=url)

        async with async_playwright() as p:
            browser: Browser = await p.chromium.launch(headless=self.headless)
            page: Page = await browser.new_page()

            await page.route(
                "**/*.{png,jpg,jpeg,gif,svg,woff,woff2}",
                lambda route: route.abort(),
            )

            try:
                await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                await page.wait_for_timeout(3000)

                links = await self._collect_listing_links(page, max_listings)
                log.info("links_found", city=city, count=len(links))

                for link in links:
                    try:
                        lead = await self._scrape_listing(page, link, city)
                        if lead:
                            leads.append(lead)
                            self.scraped_count += 1
                        await asyncio.sleep(1.5)
                    except Exception as e:
                        log.warning("listing_scrape_failed", url=link, error=str(e))
                        continue

            except Exception as e:
                log.error("city_scrape_failed", city=city, error=str(e))
            finally:
                await browser.close()

        log.info("city_scrape_complete", city=city, leads_found=len(leads))
        return leads

    async def _collect_listing_links(
        self, page: Page, max_listings: int
    ) -> list[str]:
        """Extract listing URLs using verified Craigslist selectors."""
        links: list[str] = []

        try:
            # Wait for listing cards to appear
            await page.wait_for_selector("div.cl-search-result", timeout=15000)

            # Get all listing anchor tags
            anchors = await page.query_selector_all(
                "div.cl-search-result a.cl-app-anchor.cl-search-anchor"
            )

            for anchor in anchors[:max_listings]:
                href = await anchor.get_attribute("href")
                if href:
                    # Make absolute URL if relative
                    if href.startswith("/"):
                        href = f"https://{page.url.split('/')[2]}{href}"
                    if href not in links:
                        links.append(href)

        except Exception as e:
            log.warning("link_collection_failed", error=str(e))

        return links

    async def _scrape_listing(
        self, page: Page, url: str, city: str
    ) -> RawLead | None:
        """Visit a single listing page and extract all available data."""
        await page.goto(url, timeout=20000, wait_until="domcontentloaded")
        await page.wait_for_timeout(1500)

        try:
            # Title
            title = ""
            title_el = await page.query_selector("#titletextonly")
            if not title_el:
                title_el = await page.query_selector("span.postingtitletext")
            if title_el:
                title = (await title_el.inner_text()).strip()

            # Price
            price = ""
            price_el = await page.query_selector("span.price")
            if not price_el:
                price_el = await page.query_selector(".priceinfo")
            if price_el:
                price = (await price_el.inner_text()).strip()

            # Body text
            body = ""
            body_el = await page.query_selector("#postingbody")
            if body_el:
                body = (await body_el.inner_text()).strip()
                body = body.replace("QR Code Link to This Post", "").strip()

            # Location
            location = city
            loc_el = await page.query_selector(".mapaddress")
            if not loc_el:
                loc_el = await page.query_selector("div.posting-location")
            if loc_el:
                location = (await loc_el.inner_text()).strip()

            # Post date
            post_date = None
            date_el = await page.query_selector("time.date.timeago")
            if not date_el:
                date_el = await page.query_selector("time[datetime]")
            if date_el:
                post_date = await date_el.get_attribute("datetime")

            # Extract phone and email from body
            phone = self._extract_phone(body)
            email = self._extract_email(body)

            log.info(
                "listing_scraped",
                title=title[:60],
                price=price,
                city=city,
                has_phone=bool(phone),
            )

            return RawLead(
                source="craigslist",
                source_url=url,
                title=title,
                description=body,
                asking_price=price,
                location=location,
                phone=phone,
                email=email,
                post_date=post_date,
            )

        except Exception as e:
            log.warning("listing_parse_failed", url=url, error=str(e))
            return None

    def _extract_phone(self, text: str) -> str | None:
        """Extract first phone number found in listing text."""
        pattern = r"(\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4})"
        match = re.search(pattern, text)
        return match.group(1) if match else None

    def _extract_email(self, text: str) -> str | None:
        """Extract first email address found in listing text."""
        pattern = r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
        match = re.search(pattern, text)
        return match.group(0) if match else None

    async def scrape_all_cities(
        self, cities: list[str] | None = None, max_per_city: int = 10
    ) -> list[RawLead]:
        """Scrape multiple cities and return combined lead list."""
        target_cities = cities or CRAIGSLIST_CITIES
        all_leads: list[RawLead] = []

        for city in target_cities:
            leads = await self.scrape_city(city, max_listings=max_per_city)
            all_leads.extend(leads)
            await asyncio.sleep(3)

        log.info(
            "multi_city_scrape_complete",
            cities=len(target_cities),
            total_leads=len(all_leads),
        )
        return all_leads