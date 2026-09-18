"""Orchestrator — the brain of the agent.

Flow: Customer message → Intent → Data Lookup → Rules Engine → LLM Response → Audit
"""

from __future__ import annotations

from typing import Optional

from src.config import AIRLINE_NAME, EXERCISE_DATE
from src.data_access.repository import (
    BookingRepository,
    CustomerRepository,
    PolicyRepository,
    SampleConversationRepository,
)
from src.domain.models import (
    ActionType,
    AgentAction,
    AgentResponse,
    Booking,
    BookingStatus,
    Customer,
    Intent,
    IntentAnalysis,
    Sentiment,
)
from src.domain import rules_engine
from src.llm.client import BaseLLMClient
from src.llm.prompts import INTENT_CLASSIFICATION_PROMPT, build_system_prompt
from src.agent.intent import parse_llm_intent
from src.audit.logger import AuditLogger


class AgentOrchestrator:
    """Main orchestration engine for the customer-facing resolution agent."""

    def __init__(
        self,
        llm_client: BaseLLMClient,
        customer_repo: Optional[CustomerRepository] = None,
        booking_repo: Optional[BookingRepository] = None,
        policy_repo: Optional[PolicyRepository] = None,
        sample_repo: Optional[SampleConversationRepository] = None,
        audit_logger: Optional[AuditLogger] = None,
    ) -> None:
        self.llm = llm_client
        self.customers = customer_repo or CustomerRepository()
        self.bookings = booking_repo or BookingRepository()
        self.policies = policy_repo or PolicyRepository()
        self.samples = sample_repo or SampleConversationRepository()
        self.audit = audit_logger or AuditLogger()

        # Active session state
        self._current_customer: Optional[Customer] = None
        self._current_bookings: list[Booking] = []
        self._conversation_history: list[dict] = []
        self._actions_taken: list[AgentAction] = []

    def set_customer(self, customer_name: str) -> Optional[Customer]:
        """Set the active customer for this session."""
        self._current_customer = self.customers.get_by_name(customer_name)
        if self._current_customer:
            self._current_bookings = self.bookings.get_by_customer_name(customer_name)
            self._conversation_history = []
            self._actions_taken = []
        return self._current_customer

    @property
    def current_customer(self) -> Optional[Customer]:
        return self._current_customer

    @property
    def current_bookings(self) -> list[Booking]:
        return self._current_bookings

    @property
    def conversation_history(self) -> list[dict]:
        return self._conversation_history

    @property
    def actions_taken(self) -> list[AgentAction]:
        return self._actions_taken

    def handle_message(self, message: str) -> AgentResponse:
        """Process a customer message through the full pipeline."""
        if not self._current_customer:
            return AgentResponse(
                message="I'm sorry, I need to identify your account first. Could you please provide your name or booking reference?",
                actions_taken=[],
            )

        # ── Step 1: Classify intent ────────────────────────────────────────────
        intent_analysis = self._classify_intent(message)

        # ── Step 2: Check for immediate escalation (legal threats) ─────────────
        escalation = rules_engine.is_escalation_required(message)
        if escalation or intent_analysis.mentions_legal_action:
            return self._handle_escalation(message, escalation, intent_analysis)

        # ── Step 3: Apply business rules based on intent ───────────────────────
        actions, decision_context = self._apply_rules(intent_analysis)

        # ── Step 4: Generate LLM response ──────────────────────────────────────
        response_text = self._generate_response(message, decision_context, actions)

        # ── Step 5: Build response ─────────────────────────────────────────────
        response = AgentResponse(
            message=response_text,
            actions_taken=actions,
            escalated=False,
        )

        # ── Step 6: Record ─────────────────────────────────────────────────────
        self._record_turn(message, response, intent_analysis)

        return response

    # ── Private helpers ────────────────────────────────────────────────────────

    def _classify_intent(self, message: str) -> IntentAnalysis:
        """Use LLM to classify the customer's intent."""
        # Find the most relevant booking (cancelled or delayed)
        active_booking = self._get_active_booking()
        flight_status = "Unknown"
        if active_booking:
            flight_status = f"{active_booking.status.value}"
            if active_booking.delay_hours:
                flight_status += f" ({active_booking.delay_hours}h delay)"

        intent_prompt = INTENT_CLASSIFICATION_PROMPT.format(
            customer_name=self._current_customer.name,
            pnr=self._current_customer.booking_reference,
            flight_status=flight_status,
        )

        raw_intent = self.llm.classify_intent(intent_prompt, message)
        return parse_llm_intent(raw_intent)

    def _get_active_booking(self) -> Optional[Booking]:
        """Return the most relevant booking (cancelled > delayed > other)."""
        cancelled = [b for b in self._current_bookings if b.status == BookingStatus.CANCELLED]
        if cancelled:
            return cancelled[0]

        delayed = [b for b in self._current_bookings if b.status == BookingStatus.DELAYED]
        if delayed:
            return delayed[0]

        return self._current_bookings[0] if self._current_bookings else None

    def _apply_rules(self, intent: IntentAnalysis) -> tuple[list[AgentAction], str]:
        """Apply business rules and return (actions, context_string)."""
        actions: list[AgentAction] = []
        context_parts: list[str] = []
        active_booking = self._get_active_booking()

        if not active_booking:
            return actions, "No active booking found."

        customer = self._current_customer

        # ── Cancellation ──
        if active_booking.status == BookingStatus.CANCELLED:
            cancel_actions = rules_engine.evaluate_cancellation(active_booking, customer)
            actions.extend(cancel_actions)
            context_parts.append(
                f"Flight {active_booking.flight} ({active_booking.route}) is CANCELLED. "
                f"Customer is entitled to: free rebook within 24h OR full refund (their choice)."
            )

        # ── Delay ──
        if active_booking.status == BookingStatus.DELAYED:
            delay_actions = rules_engine.evaluate_delay(active_booking, customer)
            actions.extend(delay_actions)
            context_parts.append(
                f"Flight {active_booking.flight} ({active_booking.route}) is DELAYED by "
                f"{active_booking.delay_hours} hours. New departure: {active_booking.new_departure}."
            )

        # ── Upgrade request ──
        if intent.mentions_upgrade:
            upgrade_result = rules_engine.check_upgrade_eligibility(customer, active_booking)
            actions.append(upgrade_result)
            context_parts.append("Customer requested a free upgrade — NOT covered by policy. Must decline politely.")

        # ── Hotel request ──
        if intent.mentions_hotel or intent.primary_intent == Intent.HOTEL_REQUEST:
            # Check if it's a full-night request (heuristic: if delay is being handled and they ask for hotel)
            hotel_result = rules_engine.check_hotel_request(active_booking, full_night_requested=False)
            actions.append(hotel_result)
            if active_booking.delay_hours and active_booking.delay_hours >= 5:
                context_parts.append(
                    "Hotel accommodation: ONLY for the delayed hours portion, NOT a full night's stay."
                )
            elif active_booking.delay_hours and active_booking.delay_hours < 5:
                context_parts.append(
                    f"Hotel request denied: delay is {active_booking.delay_hours}h (minimum 5h required)."
                )

        # ── Refund request ──
        if intent.mentions_refund or intent.primary_intent == Intent.REFUND_REQUEST:
            if active_booking.status == BookingStatus.CANCELLED:
                context_parts.append(
                    "Refund: available for airline-caused cancellation. "
                    "Processed within 7 business days to original payment method ONLY."
                )

        # ── Fare difference ──
        if intent.fare_difference_amount:
            fare_result = rules_engine.check_fare_difference(intent.fare_difference_amount)
            actions.append(fare_result)
            if intent.fare_difference_amount > 1500:
                context_parts.append(
                    f"Fare difference ₹{intent.fare_difference_amount:,.0f} exceeds ₹1,500 limit — MUST ESCALATE."
                )

        # ── Loyalty benefits ──
        loyalty = rules_engine.get_loyalty_benefits(customer)
        context_parts.append(f"Loyalty: {loyalty['description']}")

        return actions, "\n".join(context_parts)

    def _handle_escalation(
        self, message: str, escalation: Optional[AgentAction], intent: IntentAnalysis
    ) -> AgentResponse:
        """Handle messages that require escalation to specialist team."""
        esc_action = escalation or AgentAction(
            action_type=ActionType.ESCALATE,
            description="Escalating due to legal/complaint mention",
            details="Customer mentioned legal action or formal complaint.",
        )

        # Generate empathetic escalation response
        decision_context = (
            "ESCALATION REQUIRED: Customer has mentioned legal action or a formal complaint. "
            "You must immediately acknowledge their frustration, assure them this will get "
            "proper attention, and inform them you are escalating to the specialist support team. "
            "Do NOT try to resolve the complaint yourself — escalate."
        )
        response_text = self._generate_response(message, decision_context, [esc_action])

        response = AgentResponse(
            message=response_text,
            actions_taken=[esc_action],
            escalated=True,
            escalation_reason="Legal threat or formal complaint detected",
        )

        self._record_turn(message, response, intent)
        return response

    def _generate_response(self, message: str, decision_context: str, actions: list[AgentAction]) -> str:
        """Use LLM to generate a natural response grounded in policy decisions."""
        customer = self._current_customer
        active_booking = self._get_active_booking()

        # Build customer profile string
        customer_profile = (
            f"Name: {customer.name}\n"
            f"Loyalty Tier: {customer.loyalty_tier.value}\n"
            f"Booking Reference: {customer.booking_reference}\n"
            f"Flights (12 months): {customer.travel_history.flights_last_12_months}\n"
            f"Prior Complaints: {customer.travel_history.prior_complaints}"
        )

        # Build booking details string
        booking_lines = []
        for b in self._current_bookings:
            line = (
                f"- Flight {b.flight} | {b.route} | {b.date} {b.scheduled_departure} | "
                f"Status: {b.status.value}"
            )
            if b.delay_hours:
                line += f" (delayed {b.delay_hours}h, new departure {b.new_departure})"
            if b.status_reason:
                line += f" [{b.status_reason}]"
            booking_lines.append(line)
        booking_details = "\n".join(booking_lines)

        system_prompt = build_system_prompt(
            airline_name=AIRLINE_NAME,
            exercise_date=EXERCISE_DATE,
            customer_profile=customer_profile,
            booking_details=booking_details,
            policies_text=self.policies.get_all_policies_text(),
            sample_conversations=self.samples.get_formatted_examples(),
            decision_context=decision_context,
        )

        return self.llm.generate(system_prompt, message, self._conversation_history or None)

    def _record_turn(self, message: str, response: AgentResponse, intent: IntentAnalysis) -> None:
        """Record the conversation turn in history and audit log."""
        self._conversation_history.append({"role": "customer", "message": message})
        self._conversation_history.append({"role": "agent", "message": response.message})
        self._actions_taken.extend(response.actions_taken)

        # Audit log
        self.audit.log_turn(
            customer_name=self._current_customer.name if self._current_customer else "Unknown",
            customer_message=message,
            intent=intent.primary_intent.value,
            sentiment=intent.sentiment.value,
            actions=[a.model_dump() for a in response.actions_taken],
            agent_response=response.message,
            escalated=response.escalated,
            escalation_reason=response.escalation_reason,
        )
