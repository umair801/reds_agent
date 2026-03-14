"""
AI-powered lead extraction and distress scoring.
Sends raw scraped listings to Claude AI for structured data extraction.
"""

import json
import structlog
from datetime import datetime
from anthropic import AsyncAnthropic
from app.models.lead import RawLead, QualifiedLead, LeadStatus
from app.utils.config import settings

log = structlog.get_logger()

EXTRACTION_PROMPT = """You are a real estate lead analyst. Analyze this property listing and extract structured data.

LISTING TITLE: {title}
LISTING DESCRIPTION: {description}
ASKING PRICE (raw): {asking_price}
LOCATION: {location}
SOURCE URL: {source_url}

Extract the following and respond ONLY with a valid JSON object, no markdown, no explanation:

{{
  "first_name": "seller first name or null",
  "last_name": "seller last name or null",
  "phone": "phone number digits only or null",
  "email": "email address or null",
  "address": "property street address or null",
  "city": "city name or null",
  "state": "2-letter state code or null",
  "asking_price": price as integer with no symbols or null,
  "days_on_market": estimated days listed as integer or null,
  "distress_score": integer 0-100 based on distress signals below,
  "distress_signals": ["list", "of", "signals", "found"],
  "motivation_summary": "1-2 sentence summary of seller motivation"
}}

DISTRESS SCORING GUIDE (add points for each signal found):
- "must sell", "need to sell", "motivated seller" → +25
- "price reduced", "below appraisal", "below market" → +20
- "divorce", "estate sale", "probate" → +25
- "foreclosure", "pre-foreclosure", "behind on payments" → +30
- "relocating", "job transfer", "moving out of state" → +15
- "vacant", "empty", "tenant moved out" → +15
- "repairs needed", "as-is", "fixer upper", "needs work" → +20
- "cash only", "no realtor", "FSBO" → +10
- "owner finance" → +10
- days on market over 60 → +15
- asking below $150,000 → +10

Cap score at 100. Return 0 if no signals found."""


class LeadExtractor:
    """
    Uses Claude AI to extract structured lead data from raw listing text.
    Qualifies leads based on distress score threshold.
    """

    def __init__(self, distress_threshold: int = 30) -> None:
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.distress_threshold = distress_threshold

    async def extract(self, raw_lead: RawLead) -> QualifiedLead | None:
        """
        Send a raw lead to Claude AI for extraction and scoring.
        Returns a QualifiedLead or None if extraction fails.
        """
        prompt = EXTRACTION_PROMPT.format(
            title=raw_lead.title,
            description=raw_lead.description[:2000],
            asking_price=raw_lead.asking_price or "unknown",
            location=raw_lead.location or "unknown",
            source_url=raw_lead.source_url,
        )

        try:
            response = await self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}],
            )

            raw_json = response.content[0].text.strip()

            # Strip markdown fences if present
            if raw_json.startswith("```"):
                raw_json = raw_json.split("```")[1]
                if raw_json.startswith("json"):
                    raw_json = raw_json[4:]
                raw_json = raw_json.strip()

            data = json.loads(raw_json)

            qualified = QualifiedLead(
                source=raw_lead.source,
                source_url=raw_lead.source_url,
                scraped_at=raw_lead.scraped_at,
                first_name=data.get("first_name"),
                last_name=data.get("last_name"),
                phone=data.get("phone") or raw_lead.phone,
                email=data.get("email") or raw_lead.email,
                address=data.get("address"),
                city=data.get("city"),
                state=data.get("state"),
                asking_price=data.get("asking_price"),
                days_on_market=data.get("days_on_market"),
                distress_score=int(data.get("distress_score", 0)),
                distress_signals=data.get("distress_signals", []),
                motivation_summary=data.get("motivation_summary"),
                status=LeadStatus.RAW,
                processed_at=datetime.utcnow(),
            )

            log.info(
                "lead_extracted",
                title=raw_lead.title[:50],
                distress_score=qualified.distress_score,
                signals=qualified.distress_signals,
            )

            return qualified

        except json.JSONDecodeError as e:
            log.error("json_parse_failed", error=str(e), url=raw_lead.source_url)
            return None
        except Exception as e:
            log.error("extraction_failed", error=str(e), url=raw_lead.source_url)
            return None

    async def process_batch(
        self, raw_leads: list[RawLead]
    ) -> tuple[list[QualifiedLead], list[QualifiedLead]]:
        """
        Process a batch of raw leads.
        Returns (qualified_leads, disqualified_leads) tuple.
        """
        qualified: list[QualifiedLead] = []
        disqualified: list[QualifiedLead] = []

        for raw in raw_leads:
            lead = await self.extract(raw)
            if lead is None:
                continue

            if lead.distress_score >= self.distress_threshold:
                lead.status = LeadStatus.QUALIFIED
                qualified.append(lead)
            else:
                lead.status = LeadStatus.DISQUALIFIED
                disqualified.append(lead)

        log.info(
            "batch_processed",
            total=len(raw_leads),
            qualified=len(qualified),
            disqualified=len(disqualified),
        )

        return qualified, disqualified