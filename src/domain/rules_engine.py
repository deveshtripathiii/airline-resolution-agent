"""Rules engine — pure business logic, zero I/O.

Every public function accepts domain models and returns decisions.
No database access, no network calls, no file reads.
"""

from __future__ import annotations

import re
from typing import Optional

from src.domain.models import (
    ActionType,
    AgentAction,
    Booking,
    BookingStatus,
    Customer,
    IntentAnalysis,
    LoyaltyTier,
)


# ── Cancellation Rules ─────────────────────────────────────────────────────────

def evaluate_cancellation(booking: Booking, customer: Customer) -> list[AgentAction]:
    """Return allowed actions when a flight is cancelled by the airline."""
    if booking.status != BookingStatus.CANCELLED:
        return []

    actions: list[AgentAction] = []

    # Customer gets to CHOOSE one: rebook OR refund
    actions.append(AgentAction(
        action_type=ActionType.REBOOK,
        description="Free rebooking on next available flight within 24 hours",
        details="Airline-caused cancellation — no charge for rebooking.",
    ))
    actions.append(AgentAction(
        action_type=ActionType.REFUND,
        description="Full refund to original payment method",
        details="Processed within 7 business days to original payment method.",
    ))

    # Priority rebooking for Gold / Platinum
    if customer.loyalty_tier in (LoyaltyTier.GOLD, LoyaltyTier.PLATINUM):
        actions[0].details += " Priority rebooking — first access to next-available seats."

    return actions


# ── Delay Compensation ─────────────────────────────────────────────────────────

def evaluate_delay(booking: Booking, customer: Customer) -> list[AgentAction]:
    """Return compensation entitlements based on the delay duration."""
    if booking.status != BookingStatus.DELAYED or booking.delay_hours is None:
        return []

    hours = booking.delay_hours
    actions: list[AgentAction] = []

    if hours < 3:
        actions.append(AgentAction(
            action_type=ActionType.MEAL_VOUCHER,
            description="₹500 meal voucher",
            details=f"Delay of {hours} hour(s) — qualifies for ₹500 meal voucher.",
        ))
    elif 3 <= hours <= 5:
        actions.append(AgentAction(
            action_type=ActionType.MEAL_VOUCHER,
            description="Meal voucher",
            details=f"Delay of {hours} hour(s) — qualifies for meal voucher.",
        ))
        actions.append(AgentAction(
            action_type=ActionType.LOUNGE_ACCESS,
            description="Lounge access",
            details=f"Delay of {hours} hour(s) — qualifies for lounge access.",
        ))
    else:  # > 5 hours
        actions.append(AgentAction(
            action_type=ActionType.MEAL_VOUCHER,
            description="Meal voucher",
            details=f"Delay of {hours} hour(s) — qualifies for meal voucher.",
        ))
        actions.append(AgentAction(
            action_type=ActionType.LOUNGE_ACCESS,
            description="Lounge access",
            details=f"Delay of {hours} hour(s) — qualifies for lounge access.",
        ))
        actions.append(AgentAction(
            action_type=ActionType.HOTEL,
            description="Hotel accommodation for delayed hours only",
            details=(
                f"Delay of {hours} hour(s) — qualifies for hotel accommodation "
                f"covering the delayed hours only (not a full night's stay)."
            ),
        ))

    return actions


# ── Fare Difference ────────────────────────────────────────────────────────────

def check_fare_difference(amount_inr: float) -> AgentAction:
    """Check whether the agent can waive a fare difference or must escalate."""
    if amount_inr <= 1500:
        return AgentAction(
            action_type=ActionType.REBOOK,
            description=f"Fare difference of ₹{amount_inr:,.0f} — within agent authority",
            details="Agent can waive fare differences up to ₹1,500.",
        )
    else:
        return AgentAction(
            action_type=ActionType.ESCALATE,
            description=f"Fare difference of ₹{amount_inr:,.0f} — exceeds agent authority",
            details=(
                f"Fare difference of ₹{amount_inr:,.0f} exceeds the ₹1,500 limit. "
                "Must escalate to supervisor for approval."
            ),
        )


# ── Upgrade Eligibility ────────────────────────────────────────────────────────

def check_upgrade_eligibility(customer: Customer, booking: Booking) -> AgentAction:
    """Free upgrades are not part of standard policy — always decline."""
    return AgentAction(
        action_type=ActionType.DECLINE,
        description="Free upgrade request — not covered by policy",
        details=(
            "Free class upgrades are not part of the standard compensation policy, "
            "regardless of loyalty tier or disruption type. "
            "The agent must politely decline this request."
        ),
    )


# ── Hotel Eligibility (for specific requests) ─────────────────────────────────

def check_hotel_request(booking: Booking, full_night_requested: bool = False) -> AgentAction:
    """Evaluate a specific hotel accommodation request."""
    if booking.status != BookingStatus.DELAYED or booking.delay_hours is None:
        return AgentAction(
            action_type=ActionType.DECLINE,
            description="Hotel not applicable — flight is not delayed over 5 hours",
            details="Hotel accommodation is only for delays over 5 hours.",
        )

    if booking.delay_hours < 5:
        return AgentAction(
            action_type=ActionType.DECLINE,
            description=f"Hotel not applicable — delay is {booking.delay_hours} hours (under 5)",
            details="Hotel accommodation only qualifies for delays over 5 hours.",
        )

    if full_night_requested:
        return AgentAction(
            action_type=ActionType.DECLINE,
            description="Full night's hotel stay — exceeds policy",
            details=(
                "Policy covers hotel accommodation for the delayed hours only, "
                "not a full night's stay. Agent can arrange accommodation "
                "covering the delayed-hours portion only."
            ),
        )

    return AgentAction(
        action_type=ActionType.HOTEL,
        description="Hotel accommodation for delayed hours",
        details=f"Delay of {booking.delay_hours} hours qualifies for hotel (delayed hours only).",
    )


# ── Escalation Detection ──────────────────────────────────────────────────────

LEGAL_THREAT_PATTERNS = [
    r"legal\s*action",
    r"lawyer",
    r"sue\b",
    r"court",
    r"formal\s*complaint",
    r"consumer\s*forum",
    r"legal\s*notice",
    r"attorney",
]

_legal_regex = re.compile("|".join(LEGAL_THREAT_PATTERNS), re.IGNORECASE)


def is_escalation_required(message: str) -> Optional[AgentAction]:
    """Detect legal threats or formal complaints that require escalation."""
    if _legal_regex.search(message):
        return AgentAction(
            action_type=ActionType.ESCALATE,
            description="Legal threat / formal complaint detected — escalating",
            details=(
                "Customer mentioned legal action or a formal complaint. "
                "Policy requires immediate escalation to specialist support team."
            ),
        )
    return None


# ── Loyalty Benefits ───────────────────────────────────────────────────────────

def get_loyalty_benefits(customer: Customer) -> dict:
    """Return loyalty-tier benefits (informational, not extra compensation)."""
    if customer.loyalty_tier in (LoyaltyTier.GOLD, LoyaltyTier.PLATINUM):
        return {
            "priority_rebooking": True,
            "description": (
                f"{customer.loyalty_tier.value} tier — priority rebooking "
                "(first access to next-available seats). "
                "No additional compensation beyond standard policy."
            ),
        }
    return {
        "priority_rebooking": False,
        "description": f"{customer.loyalty_tier.value} tier — standard policy applies.",
    }
