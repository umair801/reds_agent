"""
Core data models for the REDS lead pipeline.
All data flowing through the system is validated against these models.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class LeadStatus(str, Enum):
    RAW = "raw"
    QUALIFIED = "qualified"
    DISQUALIFIED = "disqualified"
    PUSHED_TO_CRM = "pushed_to_crm"
    CONTACTED = "contacted"
    REPLIED = "replied"
    DEAD = "dead"


class RawLead(BaseModel):
    """Raw scraped data before AI processing."""

    source: str = Field(..., description="Where this lead was scraped from")
    source_url: str = Field(..., description="The listing URL")
    title: str = Field(default="", description="Listing title")
    description: str = Field(default="", description="Full listing text")
    asking_price: Optional[str] = Field(None, description="Raw price string")
    location: Optional[str] = Field(None, description="City/area from listing")
    phone: Optional[str] = Field(None, description="Phone number if visible")
    email: Optional[str] = Field(None, description="Email if visible")
    post_date: Optional[str] = Field(None, description="When listing was posted")
    scraped_at: datetime = Field(default_factory=datetime.utcnow)


class QualifiedLead(BaseModel):
    """AI-processed and scored lead ready for CRM."""

    # Source info
    source: str
    source_url: str
    scraped_at: datetime

    # Extracted contact
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

    # Property info
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    asking_price: Optional[int] = None
    days_on_market: Optional[int] = None

    # AI scoring
    distress_score: int = Field(0, ge=0, le=100)
    distress_signals: list[str] = Field(default_factory=list)
    motivation_summary: Optional[str] = None

    # Pipeline
    status: LeadStatus = LeadStatus.RAW
    ghl_contact_id: Optional[str] = None
    processed_at: Optional[datetime] = None