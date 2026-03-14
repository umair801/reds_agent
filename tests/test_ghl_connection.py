"""
Quick test to verify GoHighLevel API credentials and connection.
Run this before any CRM integration work.
"""

import asyncio
import structlog
from app.utils.logger import setup_logging
from app.crm.ghl_client import GHLClient

log = structlog.get_logger()


async def test_connection() -> None:
    setup_logging()
    client = GHLClient()

    print("\n--- Testing GoHighLevel Connection ---\n")

    try:
        data = await client.get_location()
        location = data.get("location", {})
        print(f"SUCCESS: Connected to GHL")
        print(f"Location Name : {location.get('name')}")
        print(f"Location ID   : {location.get('id')}")
        print(f"Email         : {location.get('email')}")
        print(f"Phone         : {location.get('phone')}")
        print("\nGHL is ready. Proceeding to Step 3.")
    except Exception as e:
        print(f"\nFAILED: {e}")
        print("Check your GHL_API_KEY and GHL_LOCATION_ID in .env")


if __name__ == "__main__":
    asyncio.run(test_connection())