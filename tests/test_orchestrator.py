"""Integration tests for the orchestrator — uses mock LLM, no network needed."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from src.domain.models import ActionType
from src.llm.client import MockLLMClient
from src.agent.orchestrator import AgentOrchestrator


class TestScenario1Priya:
    """Scenario 1: Priya Nair — cancelled flight, wants refund + upgrade."""

    def setup_method(self):
        self.llm = MockLLMClient(
            responses=[
                "I completely understand your frustration about the cancellation of flight SK-204. "
                "I can offer you a free rebooking on the next available flight within 24 hours, "
                "or a full refund. Regarding the upgrade to business class, I'm sorry but free "
                "upgrades are not part of our compensation policy. Which option would you prefer — "
                "rebooking or refund?"
            ],
            intents=[{
                "primary_intent": "cancellation_support",
                "secondary_intents": ["refund_request", "upgrade_request"],
                "sentiment": "angry",
                "mentions_legal_action": False,
                "mentions_upgrade": True,
                "mentions_hotel": False,
                "mentions_refund": True,
                "fare_difference_amount": None,
                "extracted_entities": {},
            }],
        )
        self.agent = AgentOrchestrator(llm_client=self.llm)
        self.agent.set_customer("Priya Nair")

    def test_customer_loaded(self):
        assert self.agent.current_customer is not None
        assert self.agent.current_customer.name == "Priya Nair"
        assert self.agent.current_customer.loyalty_tier.value == "Gold"

    def test_has_cancelled_booking(self):
        bookings = self.agent.current_bookings
        cancelled = [b for b in bookings if b.status.value == "Cancelled"]
        assert len(cancelled) == 1

    def test_response_not_empty(self):
        response = self.agent.handle_message(
            "My flight got cancelled! I want a full refund and a free upgrade to business class!"
        )
        assert response.message
        assert len(response.message) > 0


class TestScenario2Arvind:
    """Scenario 2: Arvind Kulkarni — 4h delay, wants hotel."""

    def setup_method(self):
        self.llm = MockLLMClient(
            responses=["I understand your frustration about the delay."],
            intents=[{
                "primary_intent": "delay_compensation",
                "secondary_intents": ["hotel_request"],
                "sentiment": "frustrated",
                "mentions_legal_action": False,
                "mentions_upgrade": False,
                "mentions_hotel": True,
                "mentions_refund": False,
                "fare_difference_amount": None,
                "extracted_entities": {},
            }],
        )
        self.agent = AgentOrchestrator(llm_client=self.llm)
        self.agent.set_customer("Arvind Kulkarni")

    def test_customer_loaded(self):
        assert self.agent.current_customer.name == "Arvind Kulkarni"

    def test_4h_delay_booking(self):
        bookings = self.agent.current_bookings
        assert len(bookings) == 1
        assert bookings[0].delay_hours == 4

    def test_response_generated(self):
        response = self.agent.handle_message(
            "My flight is delayed 4 hours! I need hotel accommodation."
        )
        assert response.message
        # Hotel should be declined (4h < 5h threshold)
        hotel_actions = [a for a in response.actions_taken if a.action_type == ActionType.HOTEL]
        decline_actions = [a for a in response.actions_taken if a.action_type == ActionType.DECLINE]
        # Either no hotel action or a decline for hotel
        assert len(hotel_actions) == 0 or len(decline_actions) > 0


class TestScenario3Meher:
    """Scenario 3: Meher Kaur — 6h delay, full night hotel + ₹2000 fare diff."""

    def setup_method(self):
        self.llm = MockLLMClient(
            responses=["I understand your concern about the long delay."],
            intents=[{
                "primary_intent": "delay_compensation",
                "secondary_intents": ["hotel_request", "rebook_request"],
                "sentiment": "frustrated",
                "mentions_legal_action": False,
                "mentions_upgrade": False,
                "mentions_hotel": True,
                "mentions_refund": False,
                "fare_difference_amount": 2000,
                "extracted_entities": {},
            }],
        )
        self.agent = AgentOrchestrator(llm_client=self.llm)
        self.agent.set_customer("Meher Kaur")

    def test_customer_loaded(self):
        assert self.agent.current_customer.name == "Meher Kaur"
        assert self.agent.current_customer.loyalty_tier.value == "Platinum"

    def test_6h_delay_booking(self):
        bookings = self.agent.current_bookings
        assert len(bookings) == 1
        assert bookings[0].delay_hours == 6

    def test_fare_difference_escalated(self):
        response = self.agent.handle_message(
            "I want to switch to a different flight, the fare difference is ₹2000. "
            "Also I need a full night hotel stay."
        )
        # Fare diff ₹2000 > ₹1500 should trigger escalation
        escalate_actions = [a for a in response.actions_taken if a.action_type == ActionType.ESCALATE]
        assert len(escalate_actions) > 0


class TestEscalationFlow:
    """Test legal threat escalation."""

    def setup_method(self):
        self.llm = MockLLMClient(
            responses=["I hear you, and I'm escalating this to our specialist team."],
            intents=[{
                "primary_intent": "complaint_legal",
                "sentiment": "angry",
                "mentions_legal_action": True,
                "mentions_upgrade": False,
                "mentions_hotel": False,
                "mentions_refund": False,
            }],
        )
        self.agent = AgentOrchestrator(llm_client=self.llm)
        self.agent.set_customer("Priya Nair")

    def test_legal_threat_escalates(self):
        response = self.agent.handle_message(
            "This is unacceptable! I'm going to take legal action!"
        )
        assert response.escalated is True
        assert any(a.action_type == ActionType.ESCALATE for a in response.actions_taken)
