"""Pydantic models for the airline resolution agent domain."""

from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel


# ── Enums ──────────────────────────────────────────────────────────────────────

class LoyaltyTier(str, Enum):
    PLATINUM = "Platinum"
    GOLD = "Gold"
    SILVER = "Silver"
    NONE = "None"


class BookingStatus(str, Enum):
    CANCELLED = "Cancelled"
    DELAYED = "Delayed"
    UNAFFECTED = "Unaffected"


class ActionType(str, Enum):
    REBOOK = "rebook"
    REFUND = "refund"
    MEAL_VOUCHER = "meal_voucher"
    LOUNGE_ACCESS = "lounge_access"
    HOTEL = "hotel_accommodation"
    ESCALATE = "escalate_to_supervisor"
    INFO = "provide_info"
    DECLINE = "decline_request"


class Intent(str, Enum):
    FLIGHT_STATUS = "flight_status"
    CANCELLATION_SUPPORT = "cancellation_support"
    DELAY_COMPENSATION = "delay_compensation"
    REFUND_REQUEST = "refund_request"
    UPGRADE_REQUEST = "upgrade_request"
    REBOOK_REQUEST = "rebook_request"
    HOTEL_REQUEST = "hotel_request"
    COMPLAINT_LEGAL = "complaint_legal"
    GENERAL_QUERY = "general_query"


class Sentiment(str, Enum):
    ANGRY = "angry"
    FRUSTRATED = "frustrated"
    NEUTRAL = "neutral"
    POLITE = "polite"


# ── Data Models ────────────────────────────────────────────────────────────────

class TravelHistory(BaseModel):
    flights_last_12_months: int
    prior_complaints: int
    complaint_details: Optional[str] = None


class Contact(BaseModel):
    email: str
    phone: str


class Customer(BaseModel):
    name: str
    loyalty_tier: LoyaltyTier
    booking_reference: str
    contact: Contact
    travel_history: TravelHistory


class Booking(BaseModel):
    customer: str
    pnr: str
    flight: str
    route: str
    date: str
    scheduled_departure: str
    status: BookingStatus
    status_reason: Optional[str] = None
    delay_hours: Optional[float] = None
    new_departure: Optional[str] = None


# ── Agent Action & Response Models ─────────────────────────────────────────────

class AgentAction(BaseModel):
    """A single action the agent takes or recommends."""
    action_type: ActionType
    description: str
    details: Optional[str] = None


class IntentAnalysis(BaseModel):
    """Parsed intent from a customer message."""
    primary_intent: Intent
    secondary_intents: list[Intent] = []
    sentiment: Sentiment = Sentiment.NEUTRAL
    mentions_legal_action: bool = False
    mentions_upgrade: bool = False
    mentions_hotel: bool = False
    mentions_refund: bool = False
    fare_difference_amount: Optional[float] = None
    extracted_entities: dict = {}


class AgentResponse(BaseModel):
    """Complete agent response with message and metadata."""
    message: str
    actions_taken: list[AgentAction] = []
    escalated: bool = False
    escalation_reason: Optional[str] = None
    requires_supervisor: bool = False
