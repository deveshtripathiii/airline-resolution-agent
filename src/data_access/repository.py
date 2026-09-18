"""Repository classes — only layer that reads the JSON data files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from src.config import CUSTOMERS_FILE, BOOKINGS_FILE, POLICIES_FILE, SAMPLE_CONVERSATIONS_FILE
from src.domain.models import Booking, BookingStatus, Customer, LoyaltyTier, Contact, TravelHistory


class CustomerRepository:
    """Look up customers from customers.json."""

    def __init__(self, filepath: Path = CUSTOMERS_FILE) -> None:
        with open(filepath, "r", encoding="utf-8") as f:
            self._raw: list[dict] = json.load(f)
        self._customers = self._parse_all()

    def _parse_all(self) -> list[Customer]:
        customers = []
        for raw in self._raw:
            customers.append(Customer(
                name=raw["name"],
                loyalty_tier=LoyaltyTier(raw["loyalty_tier"]),
                booking_reference=raw["booking_reference"],
                contact=Contact(**raw["contact"]),
                travel_history=TravelHistory(**raw["travel_history"]),
            ))
        return customers

    def get_by_name(self, name: str) -> Optional[Customer]:
        """Case-insensitive name lookup."""
        name_lower = name.lower()
        for c in self._customers:
            if c.name.lower() == name_lower:
                return c
        return None

    def get_by_booking_reference(self, ref: str) -> Optional[Customer]:
        ref_upper = ref.upper()
        for c in self._customers:
            if c.booking_reference.upper() == ref_upper:
                return c
        return None

    def get_all(self) -> list[Customer]:
        return list(self._customers)


class BookingRepository:
    """Look up bookings from bookings.json."""

    def __init__(self, filepath: Path = BOOKINGS_FILE) -> None:
        with open(filepath, "r", encoding="utf-8") as f:
            self._raw: list[dict] = json.load(f)
        self._bookings = self._parse_all()

    def _parse_all(self) -> list[Booking]:
        bookings = []
        for raw in self._raw:
            bookings.append(Booking(
                customer=raw["customer"],
                pnr=raw["pnr"],
                flight=raw["flight"],
                route=raw["route"],
                date=raw["date"],
                scheduled_departure=raw["scheduled_departure"],
                status=BookingStatus(raw["status"]),
                status_reason=raw.get("status_reason"),
                delay_hours=raw.get("delay_hours"),
                new_departure=raw.get("new_departure"),
            ))
        return bookings

    def get_by_pnr(self, pnr: str) -> list[Booking]:
        """Return all bookings for a PNR (may be multiple legs)."""
        pnr_upper = pnr.upper()
        return [b for b in self._bookings if b.pnr.upper() == pnr_upper]

    def get_by_customer_name(self, name: str) -> list[Booking]:
        name_lower = name.lower()
        return [b for b in self._bookings if b.customer.lower() == name_lower]

    def get_by_flight(self, flight: str) -> list[Booking]:
        flight_upper = flight.upper().replace(" ", "")
        return [
            b for b in self._bookings
            if b.flight.upper().replace(" ", "").replace("-", "") == flight_upper.replace("-", "")
        ]

    def get_all(self) -> list[Booking]:
        return list(self._bookings)


class PolicyRepository:
    """Load and query policies from policies.json."""

    def __init__(self, filepath: Path = POLICIES_FILE) -> None:
        with open(filepath, "r", encoding="utf-8") as f:
            self._policies: dict = json.load(f)

    @property
    def cancellation_rule(self) -> dict:
        return self._policies.get("cancellation_rebooking", {})

    @property
    def delay_compensation(self) -> dict:
        return self._policies.get("delay_compensation", {})

    @property
    def refund_processing(self) -> dict:
        return self._policies.get("refund_processing", {})

    @property
    def fare_difference(self) -> dict:
        return self._policies.get("fare_difference", {})

    @property
    def loyalty_tier_rule(self) -> dict:
        return self._policies.get("loyalty_tier", {})

    @property
    def allowed_actions(self) -> list[str]:
        return self._policies.get("allowed_actions", [])

    @property
    def prohibited_actions(self) -> list[str]:
        return self._policies.get("prohibited_actions", [])

    def get_all_policies_text(self) -> str:
        """Return a human-readable summary of all policies for the LLM prompt."""
        lines = []
        cr = self.cancellation_rule
        lines.append(f"CANCELLATION REBOOKING: {cr.get('description', '')}")

        dc = self.delay_compensation
        lines.append(f"DELAY COMPENSATION: {dc.get('description', '')}")
        for tier in dc.get("tiers", []):
            ents = ", ".join(tier["entitlements"])
            note = f" ({tier.get('hotel_note', '')})" if tier.get("hotel_note") else ""
            lines.append(f"  - {tier['condition']}: {ents}{note}")

        rp = self.refund_processing
        lines.append(f"REFUND PROCESSING: {rp.get('description', '')}")

        fd = self.fare_difference
        lines.append(f"FARE DIFFERENCE: {fd.get('description', '')}")

        lt = self.loyalty_tier_rule
        lines.append(f"LOYALTY TIER: {lt.get('description', '')}")

        lines.append("\nALLOWED ACTIONS:")
        for a in self.allowed_actions:
            lines.append(f"  ✓ {a}")

        lines.append("\nPROHIBITED ACTIONS (must escalate):")
        for p in self.prohibited_actions:
            lines.append(f"  ✗ {p}")

        return "\n".join(lines)


class SampleConversationRepository:
    """Load sample conversations for tone/style reference."""

    def __init__(self, filepath: Path = SAMPLE_CONVERSATIONS_FILE) -> None:
        with open(filepath, "r", encoding="utf-8") as f:
            self._samples: list[dict] = json.load(f)

    def get_all(self) -> list[dict]:
        return self._samples

    def get_formatted_examples(self) -> str:
        """Return formatted sample conversations for the LLM prompt."""
        lines = []
        for s in self._samples:
            lines.append(f"--- {s['id'].upper()} ---")
            for turn in s["conversation"]:
                role = "Customer" if turn["role"] == "customer" else "Agent"
                lines.append(f"{role}: {turn['message']}")
            lines.append("")
        return "\n".join(lines)
