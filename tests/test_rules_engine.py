"""Tests for the rules engine — pure business logic."""

import sys
from pathlib import Path

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from src.domain.models import (
    ActionType,
    Booking,
    BookingStatus,
    Contact,
    Customer,
    LoyaltyTier,
    TravelHistory,
)
from src.domain.rules_engine import (
    check_fare_difference,
    check_hotel_request,
    check_upgrade_eligibility,
    evaluate_cancellation,
    evaluate_delay,
    get_loyalty_benefits,
    is_escalation_required,
)


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def gold_customer() -> Customer:
    return Customer(
        name="Priya Nair",
        loyalty_tier=LoyaltyTier.GOLD,
        booking_reference="SK4821X",
        contact=Contact(email="priya@example.com", phone="+91-9800000001"),
        travel_history=TravelHistory(flights_last_12_months=6, prior_complaints=1),
    )


@pytest.fixture
def silver_customer() -> Customer:
    return Customer(
        name="Arvind Kulkarni",
        loyalty_tier=LoyaltyTier.SILVER,
        booking_reference="TR1190B",
        contact=Contact(email="arvind@example.com", phone="+91-9800000002"),
        travel_history=TravelHistory(flights_last_12_months=3, prior_complaints=0),
    )


@pytest.fixture
def platinum_customer() -> Customer:
    return Customer(
        name="Meher Kaur",
        loyalty_tier=LoyaltyTier.PLATINUM,
        booking_reference="WL7742",
        contact=Contact(email="meher@example.com", phone="+91-9800000003"),
        travel_history=TravelHistory(flights_last_12_months=10, prior_complaints=1),
    )


@pytest.fixture
def cancelled_booking() -> Booking:
    return Booking(
        customer="Priya Nair", pnr="SK4821X", flight="SK-204",
        route="Delhi → Goa", date="Wed 23 Sep 2026",
        scheduled_departure="18:40", status=BookingStatus.CANCELLED,
        status_reason="operational reasons",
    )


@pytest.fixture
def delayed_4h_booking() -> Booking:
    return Booking(
        customer="Arvind Kulkarni", pnr="TR1190B", flight="SK-118",
        route="Mumbai → Bengaluru", date="Wed 23 Sep 2026",
        scheduled_departure="07:10", status=BookingStatus.DELAYED,
        delay_hours=4, new_departure="11:10",
    )


@pytest.fixture
def delayed_6h_booking() -> Booking:
    return Booking(
        customer="Meher Kaur", pnr="WL7742", flight="SK-305",
        route="Delhi → Hyderabad", date="Wed 23 Sep 2026",
        scheduled_departure="14:00", status=BookingStatus.DELAYED,
        delay_hours=6, new_departure="20:00",
    )


# ── Cancellation Tests ─────────────────────────────────────────────────────────

class TestCancellation:
    def test_cancelled_flight_offers_rebook_and_refund(self, cancelled_booking, gold_customer):
        actions = evaluate_cancellation(cancelled_booking, gold_customer)
        types = [a.action_type for a in actions]
        assert ActionType.REBOOK in types
        assert ActionType.REFUND in types

    def test_cancelled_gold_gets_priority_rebooking(self, cancelled_booking, gold_customer):
        actions = evaluate_cancellation(cancelled_booking, gold_customer)
        rebook = next(a for a in actions if a.action_type == ActionType.REBOOK)
        assert "Priority" in rebook.details or "priority" in rebook.details.lower()

    def test_non_cancelled_returns_empty(self, delayed_4h_booking, silver_customer):
        actions = evaluate_cancellation(delayed_4h_booking, silver_customer)
        assert actions == []


# ── Delay Compensation Tests ───────────────────────────────────────────────────

class TestDelayCompensation:
    def test_4h_delay_gives_meal_and_lounge(self, delayed_4h_booking, silver_customer):
        actions = evaluate_delay(delayed_4h_booking, silver_customer)
        types = [a.action_type for a in actions]
        assert ActionType.MEAL_VOUCHER in types
        assert ActionType.LOUNGE_ACCESS in types
        assert ActionType.HOTEL not in types  # 4h < 5h threshold

    def test_6h_delay_gives_meal_lounge_hotel(self, delayed_6h_booking, platinum_customer):
        actions = evaluate_delay(delayed_6h_booking, platinum_customer)
        types = [a.action_type for a in actions]
        assert ActionType.MEAL_VOUCHER in types
        assert ActionType.LOUNGE_ACCESS in types
        assert ActionType.HOTEL in types

    def test_6h_hotel_delayed_hours_only(self, delayed_6h_booking, platinum_customer):
        actions = evaluate_delay(delayed_6h_booking, platinum_customer)
        hotel = next(a for a in actions if a.action_type == ActionType.HOTEL)
        assert "delayed hours only" in hotel.description.lower() or "delayed hours only" in hotel.details.lower()

    def test_under_3h_delay_gives_500_voucher_only(self):
        booking = Booking(
            customer="Test", pnr="TEST", flight="SK-999",
            route="A → B", date="2026-09-23",
            scheduled_departure="10:00", status=BookingStatus.DELAYED,
            delay_hours=2, new_departure="12:00",
        )
        customer = Customer(
            name="Test", loyalty_tier=LoyaltyTier.SILVER,
            booking_reference="TEST",
            contact=Contact(email="t@e.com", phone="0"),
            travel_history=TravelHistory(flights_last_12_months=1, prior_complaints=0),
        )
        actions = evaluate_delay(booking, customer)
        assert len(actions) == 1
        assert actions[0].action_type == ActionType.MEAL_VOUCHER
        assert "500" in actions[0].description


# ── Fare Difference Tests ──────────────────────────────────────────────────────

class TestFareDifference:
    def test_within_limit_ok(self):
        result = check_fare_difference(1000)
        assert result.action_type == ActionType.REBOOK

    def test_at_limit_ok(self):
        result = check_fare_difference(1500)
        assert result.action_type == ActionType.REBOOK

    def test_above_limit_escalates(self):
        result = check_fare_difference(2000)
        assert result.action_type == ActionType.ESCALATE
        assert "supervisor" in result.details.lower()


# ── Upgrade Tests ──────────────────────────────────────────────────────────────

class TestUpgrade:
    def test_upgrade_always_declined(self, gold_customer, cancelled_booking):
        result = check_upgrade_eligibility(gold_customer, cancelled_booking)
        assert result.action_type == ActionType.DECLINE
        assert "not part of" in result.details.lower() or "not covered" in result.details.lower()


# ── Hotel Tests ────────────────────────────────────────────────────────────────

class TestHotelRequest:
    def test_4h_delay_hotel_denied(self, delayed_4h_booking):
        result = check_hotel_request(delayed_4h_booking)
        assert result.action_type == ActionType.DECLINE

    def test_6h_delay_hotel_approved(self, delayed_6h_booking):
        result = check_hotel_request(delayed_6h_booking)
        assert result.action_type == ActionType.HOTEL

    def test_full_night_request_declined(self, delayed_6h_booking):
        result = check_hotel_request(delayed_6h_booking, full_night_requested=True)
        assert result.action_type == ActionType.DECLINE
        assert "full night" in result.description.lower() or "full night" in result.details.lower()


# ── Escalation Tests ───────────────────────────────────────────────────────────

class TestEscalation:
    def test_legal_action_detected(self):
        result = is_escalation_required("I will take legal action over this!")
        assert result is not None
        assert result.action_type == ActionType.ESCALATE

    def test_formal_complaint_detected(self):
        result = is_escalation_required("I'm filing a formal complaint")
        assert result is not None
        assert result.action_type == ActionType.ESCALATE

    def test_lawyer_detected(self):
        result = is_escalation_required("I'm contacting my lawyer about this")
        assert result is not None

    def test_normal_message_no_escalation(self):
        result = is_escalation_required("I want a refund for my cancelled flight")
        assert result is None

    def test_angry_but_no_legal_no_escalation(self):
        result = is_escalation_required("This is unacceptable! I'm furious!")
        assert result is None


# ── Loyalty Tests ──────────────────────────────────────────────────────────────

class TestLoyalty:
    def test_gold_gets_priority(self, gold_customer):
        benefits = get_loyalty_benefits(gold_customer)
        assert benefits["priority_rebooking"] is True

    def test_platinum_gets_priority(self, platinum_customer):
        benefits = get_loyalty_benefits(platinum_customer)
        assert benefits["priority_rebooking"] is True

    def test_silver_no_priority(self, silver_customer):
        benefits = get_loyalty_benefits(silver_customer)
        assert benefits["priority_rebooking"] is False
