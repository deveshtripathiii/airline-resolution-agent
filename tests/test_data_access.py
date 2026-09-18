"""Tests for the data access layer."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from src.data_access.repository import (
    BookingRepository,
    CustomerRepository,
    PolicyRepository,
    SampleConversationRepository,
)


class TestCustomerRepository:
    def setup_method(self):
        self.repo = CustomerRepository()

    def test_get_all_returns_3_customers(self):
        customers = self.repo.get_all()
        assert len(customers) == 3

    def test_get_priya_by_name(self):
        c = self.repo.get_by_name("Priya Nair")
        assert c is not None
        assert c.loyalty_tier.value == "Gold"
        assert c.booking_reference == "SK4821X"

    def test_get_arvind_by_name(self):
        c = self.repo.get_by_name("Arvind Kulkarni")
        assert c is not None
        assert c.loyalty_tier.value == "Silver"

    def test_get_meher_by_name(self):
        c = self.repo.get_by_name("Meher Kaur")
        assert c is not None
        assert c.loyalty_tier.value == "Platinum"

    def test_get_by_booking_reference(self):
        c = self.repo.get_by_booking_reference("WL7742")
        assert c is not None
        assert c.name == "Meher Kaur"

    def test_case_insensitive_lookup(self):
        c = self.repo.get_by_name("priya nair")
        assert c is not None

    def test_unknown_returns_none(self):
        c = self.repo.get_by_name("Nobody")
        assert c is None


class TestBookingRepository:
    def setup_method(self):
        self.repo = BookingRepository()

    def test_get_all_returns_4_bookings(self):
        bookings = self.repo.get_all()
        assert len(bookings) == 4

    def test_priya_has_2_bookings(self):
        bookings = self.repo.get_by_customer_name("Priya Nair")
        assert len(bookings) == 2

    def test_cancelled_flight_status(self):
        bookings = self.repo.get_by_customer_name("Priya Nair")
        cancelled = [b for b in bookings if b.status.value == "Cancelled"]
        assert len(cancelled) == 1
        assert cancelled[0].flight == "SK-204"

    def test_arvind_delayed_4h(self):
        bookings = self.repo.get_by_customer_name("Arvind Kulkarni")
        assert len(bookings) == 1
        assert bookings[0].delay_hours == 4

    def test_meher_delayed_6h(self):
        bookings = self.repo.get_by_customer_name("Meher Kaur")
        assert len(bookings) == 1
        assert bookings[0].delay_hours == 6

    def test_get_by_pnr(self):
        bookings = self.repo.get_by_pnr("TR1190B")
        assert len(bookings) == 1
        assert bookings[0].customer == "Arvind Kulkarni"


class TestPolicyRepository:
    def setup_method(self):
        self.repo = PolicyRepository()

    def test_allowed_actions_not_empty(self):
        assert len(self.repo.allowed_actions) > 0

    def test_prohibited_actions_not_empty(self):
        assert len(self.repo.prohibited_actions) > 0

    def test_fare_difference_limit(self):
        fd = self.repo.fare_difference
        assert fd["agent_waive_limit_inr"] == 1500

    def test_delay_compensation_has_3_tiers(self):
        dc = self.repo.delay_compensation
        assert len(dc["tiers"]) == 3

    def test_policies_text_is_readable(self):
        text = self.repo.get_all_policies_text()
        assert "CANCELLATION" in text
        assert "DELAY" in text
        assert "ALLOWED" in text
        assert "PROHIBITED" in text


class TestSampleConversationRepository:
    def setup_method(self):
        self.repo = SampleConversationRepository()

    def test_has_3_samples(self):
        assert len(self.repo.get_all()) == 3

    def test_formatted_examples_contains_agent(self):
        text = self.repo.get_formatted_examples()
        assert "Agent:" in text
        assert "Customer:" in text
