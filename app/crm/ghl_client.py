"""
GoHighLevel API v2 client.
Handles contact creation, tagging, and workflow triggers.
"""

import httpx
import structlog
from typing import Any
from app.utils.config import settings

log = structlog.get_logger()


class GHLClient:
    """Async HTTP client for GoHighLevel API v2."""

    def __init__(self) -> None:
        self.base_url: str = settings.GHL_BASE_URL
        self.headers: dict[str, str] = {
            "Authorization": f"Bearer {settings.GHL_API_KEY}",
            "Version": "2021-07-28",
            "Content-Type": "application/json",
        }

    async def get_location(self) -> dict[str, Any]:
        """Verify API connection by fetching location info."""
        url = f"{self.base_url}/locations/{settings.GHL_LOCATION_ID}"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                log.info(
                    "ghl_connection_verified",
                    location_name=data.get("location", {}).get("name"),
                    location_id=settings.GHL_LOCATION_ID,
                )
                return data
            except httpx.HTTPStatusError as e:
                log.error("ghl_auth_failed", status_code=e.response.status_code)
                raise
            except httpx.RequestError as e:
                log.error("ghl_connection_error", error=str(e))
                raise

    async def create_contact(
        self, lead_data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """
        Create a new contact in GHL from qualified lead data.
        Returns the created contact dict or None on failure.
        """
        url = f"{self.base_url}/contacts/"

        payload: dict[str, Any] = {
            "locationId": settings.GHL_LOCATION_ID,
            "firstName": lead_data.get("first_name") or "Unknown",
            "lastName": lead_data.get("last_name") or "Seller",
            "phone": lead_data.get("phone"),
            "email": lead_data.get("email"),
            "address1": lead_data.get("address"),
            "city": lead_data.get("city"),
            "state": lead_data.get("state"),
            "source": lead_data.get("source", "craigslist"),
            "tags": self._build_tags(lead_data),
            "customFields": self._build_custom_fields(lead_data),
        }

        # Remove None values — GHL rejects null fields
        payload = {k: v for k, v in payload.items() if v is not None}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url, headers=self.headers, json=payload, timeout=15.0
                )
                response.raise_for_status()
                data = response.json()
                contact = data.get("contact", {})
                contact_id = contact.get("id")

                log.info(
                    "ghl_contact_created",
                    contact_id=contact_id,
                    name=f"{payload.get('firstName')} {payload.get('lastName')}",
                    distress_score=lead_data.get("distress_score"),
                )
                return contact

            except httpx.HTTPStatusError as e:
                log.error(
                    "ghl_contact_creation_failed",
                    status_code=e.response.status_code,
                    detail=e.response.text[:300],
                )
                return None
            except httpx.RequestError as e:
                log.error("ghl_request_error", error=str(e))
                return None

    async def get_contact_by_phone(
        self, phone: str
    ) -> dict[str, Any] | None:
        """Look up an existing contact by phone number."""
        url = f"{self.base_url}/contacts/search/duplicate"
        params = {"locationId": settings.GHL_LOCATION_ID, "phone": phone}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    url, headers=self.headers, params=params, timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                contacts = data.get("contacts", [])
                return contacts[0] if contacts else None
            except Exception as e:
                log.error("contact_lookup_failed", error=str(e))
                return None

    async def add_note_to_contact(
        self, contact_id: str, note_body: str
    ) -> bool:
        """Add a note to an existing GHL contact."""
        url = f"{self.base_url}/contacts/{contact_id}/notes"
        payload = {"body": note_body, "userId": ""}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url, headers=self.headers, json=payload, timeout=10.0
                )
                response.raise_for_status()
                log.info("note_added", contact_id=contact_id)
                return True
            except Exception as e:
                log.error("note_add_failed", error=str(e))
                return False

    def _build_tags(self, lead_data: dict[str, Any]) -> list[str]:
        """Build GHL contact tags from lead data."""
        tags = ["REDS_Lead", lead_data.get("source", "craigslist").upper()]
        score = lead_data.get("distress_score", 0)

        if score >= 70:
            tags.append("High_Distress")
        elif score >= 40:
            tags.append("Medium_Distress")
        else:
            tags.append("Low_Distress")

        for signal in lead_data.get("distress_signals", []):
            clean = signal.replace(" ", "_").replace(",", "").title()
            tags.append(clean[:50])

        return tags

    def _build_custom_fields(
        self, lead_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Build GHL custom field entries from lead data.
        Field keys must match custom fields created in your GHL account.
        """
        fields = []

        if lead_data.get("asking_price"):
            fields.append({
                "key": "asking_price",
                "field_value": str(lead_data["asking_price"]),
            })
        if lead_data.get("distress_score") is not None:
            fields.append({
                "key": "distress_score",
                "field_value": str(lead_data["distress_score"]),
            })
        if lead_data.get("source_url"):
            fields.append({
                "key": "listing_url",
                "field_value": lead_data["source_url"],
            })
        if lead_data.get("motivation_summary"):
            fields.append({
                "key": "motivation_summary",
                "field_value": lead_data["motivation_summary"],
            })

        return fields
    
    async def get_conversations(
        self, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Fetch recent conversations from GHL."""
        url = f"{self.base_url}/conversations/search"
        params = {
            "locationId": settings.GHL_LOCATION_ID,
            "limit": limit,
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    url, headers=self.headers, params=params, timeout=15.0
                )
                response.raise_for_status()
                data = response.json()
                conversations = data.get("conversations", [])
                log.info("conversations_fetched", count=len(conversations))
                return conversations
            except httpx.HTTPStatusError as e:
                log.error(
                    "conversations_fetch_failed",
                    status_code=e.response.status_code,
                    detail=e.response.text[:300],
                )
                return []
            except httpx.RequestError as e:
                log.error("conversations_request_error", error=str(e))
                return []

    async def get_messages_for_conversation(
        self, conversation_id: str
    ) -> list[dict[str, Any]]:
        """Fetch all messages for a specific conversation."""
        url = f"{self.base_url}/conversations/{conversation_id}/messages"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    url, headers=self.headers, timeout=15.0
                )
                response.raise_for_status()
                data = response.json()
                return data.get("messages", {}).get("messages", [])
            except Exception as e:
                log.error(
                    "messages_fetch_failed",
                    conversation_id=conversation_id,
                    error=str(e),
                )
                return []