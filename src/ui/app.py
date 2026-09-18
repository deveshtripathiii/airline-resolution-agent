"""Streamlit chat UI for the Airline Customer-Facing Resolution Agent."""

import sys
from pathlib import Path

# Ensure project root is on sys.path so `src.*` imports work
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from src.config import GEMINI_API_KEY
from src.data_access.repository import CustomerRepository, BookingRepository
from src.domain.models import ActionType, BookingStatus
from src.llm.client import GeminiClient, MockLLMClient
from src.agent.orchestrator import AgentOrchestrator


# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SkyWay Airlines — Customer Support",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; }
    .status-cancelled { color: #dc3545; font-weight: bold; }
    .status-delayed { color: #fd7e14; font-weight: bold; }
    .status-unaffected { color: #28a745; font-weight: bold; }
    .escalation-banner {
        background-color: #dc3545;
        color: white;
        padding: 10px 16px;
        border-radius: 8px;
        margin-bottom: 10px;
        font-weight: bold;
    }
    .action-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.85em;
        margin: 2px 4px;
        font-weight: 500;
    }
    .badge-rebook { background-color: #cfe2ff; color: #084298; }
    .badge-refund { background-color: #d1e7dd; color: #0f5132; }
    .badge-meal { background-color: #fff3cd; color: #664d03; }
    .badge-lounge { background-color: #e2e3e5; color: #41464b; }
    .badge-hotel { background-color: #f8d7da; color: #842029; }
    .badge-escalate { background-color: #dc3545; color: white; }
    .badge-decline { background-color: #6c757d; color: white; }
    .tier-gold { color: #b8860b; font-weight: bold; }
    .tier-platinum { color: #8B008B; font-weight: bold; }
    .tier-silver { color: #708090; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


# ── Initialize session state ───────────────────────────────────────────────────
def init_session():
    if "orchestrator" not in st.session_state:
        # Use Gemini if key is available, otherwise mock
        if GEMINI_API_KEY and GEMINI_API_KEY != "your_api_key_here":
            llm = GeminiClient()
        else:
            llm = MockLLMClient(
                responses=[
                    "I completely understand your frustration, and I'm sorry for the inconvenience. "
                    "Let me look into this right away and help you with the best available options.",
                    "I've reviewed your booking details. Based on our policy, here's what I can do for you. "
                    "Would you like me to proceed with any of these options?",
                    "I've applied the eligible compensation to your account. "
                    "Is there anything else I can help you with?",
                ],
                intents=[
                    {
                        "primary_intent": "cancellation_support",
                        "secondary_intents": ["refund_request"],
                        "sentiment": "angry",
                        "mentions_legal_action": False,
                        "mentions_upgrade": False,
                        "mentions_hotel": False,
                        "mentions_refund": True,
                        "fare_difference_amount": None,
                        "extracted_entities": {},
                    },
                    {
                        "primary_intent": "delay_compensation",
                        "secondary_intents": ["hotel_request"],
                        "sentiment": "frustrated",
                        "mentions_legal_action": False,
                        "mentions_upgrade": False,
                        "mentions_hotel": True,
                        "mentions_refund": False,
                        "fare_difference_amount": None,
                        "extracted_entities": {},
                    },
                    {
                        "primary_intent": "delay_compensation",
                        "secondary_intents": ["rebook_request"],
                        "sentiment": "frustrated",
                        "mentions_legal_action": False,
                        "mentions_upgrade": False,
                        "mentions_hotel": True,
                        "mentions_refund": False,
                        "fare_difference_amount": 2000,
                        "extracted_entities": {},
                    },
                ],
            )

        st.session_state.orchestrator = AgentOrchestrator(llm_client=llm)
        st.session_state.messages = []
        st.session_state.selected_customer = None

    if "customer_repo" not in st.session_state:
        st.session_state.customer_repo = CustomerRepository()
        st.session_state.booking_repo = BookingRepository()


init_session()


# ── Helper functions ───────────────────────────────────────────────────────────
def get_tier_class(tier: str) -> str:
    return {"Gold": "tier-gold", "Platinum": "tier-platinum", "Silver": "tier-silver"}.get(tier, "")


def get_status_class(status: str) -> str:
    return {
        "Cancelled": "status-cancelled",
        "Delayed": "status-delayed",
        "Unaffected": "status-unaffected",
    }.get(status, "")


def get_action_badge(action_type: str) -> str:
    badges = {
        "rebook": ("✈️ Rebook", "badge-rebook"),
        "refund": ("💰 Refund", "badge-refund"),
        "meal_voucher": ("🍽️ Meal Voucher", "badge-meal"),
        "lounge_access": ("🛋️ Lounge", "badge-lounge"),
        "hotel_accommodation": ("🏨 Hotel", "badge-hotel"),
        "escalate_to_supervisor": ("⚠️ Escalated", "badge-escalate"),
        "decline_request": ("❌ Declined", "badge-decline"),
        "provide_info": ("ℹ️ Info", "badge-rebook"),
    }
    label, css = badges.get(action_type, ("🔹 Action", "badge-rebook"))
    return f'<span class="action-badge {css}">{label}</span>'


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ✈️ SkyWay Airlines")
    st.markdown("### Customer Support Agent")
    st.divider()

    # Customer selector
    customers = st.session_state.customer_repo.get_all()
    customer_names = [c.name for c in customers]

    selected = st.selectbox(
        "🧑‍💼 Select Customer",
        options=["— Select —"] + customer_names,
        index=0,
        help="Choose a customer scenario to begin",
    )

    if selected != "— Select —" and selected != st.session_state.selected_customer:
        st.session_state.selected_customer = selected
        st.session_state.orchestrator.set_customer(selected)
        st.session_state.messages = []
        st.rerun()

    st.divider()

    # Show customer profile
    if st.session_state.selected_customer:
        customer = st.session_state.orchestrator.current_customer
        if customer:
            st.markdown("### 👤 Customer Profile")
            tier_class = get_tier_class(customer.loyalty_tier.value)
            st.markdown(f"**Name:** {customer.name}")
            st.markdown(f'**Tier:** <span class="{tier_class}">{customer.loyalty_tier.value}</span>', unsafe_allow_html=True)
            st.markdown(f"**PNR:** `{customer.booking_reference}`")
            st.markdown(f"**Flights (12mo):** {customer.travel_history.flights_last_12_months}")
            st.markdown(f"**Prior Complaints:** {customer.travel_history.prior_complaints}")

            st.divider()

            # Show bookings
            st.markdown("### 🎫 Bookings")
            bookings = st.session_state.orchestrator.current_bookings
            for b in bookings:
                status_class = get_status_class(b.status.value)
                st.markdown(f"**{b.flight}** — {b.route}")
                st.markdown(f"📅 {b.date} at {b.scheduled_departure}")
                status_text = b.status.value
                if b.delay_hours:
                    status_text += f" ({b.delay_hours}h → {b.new_departure})"
                if b.status_reason:
                    status_text += f" [{b.status_reason}]"
                st.markdown(f'Status: <span class="{status_class}">{status_text}</span>', unsafe_allow_html=True)
                st.markdown("---")

            # Show actions taken
            actions = st.session_state.orchestrator.actions_taken
            if actions:
                st.markdown("### ✅ Actions Taken")
                for a in actions:
                    badge = get_action_badge(a.action_type.value)
                    st.markdown(f"{badge} {a.description}", unsafe_allow_html=True)


# ── Main chat area ─────────────────────────────────────────────────────────────
st.markdown("# ✈️ SkyWay Airlines — Customer Support")

if not st.session_state.selected_customer:
    st.info("👈 Please select a customer from the sidebar to begin a support conversation.")
    st.markdown("""
    ### Available Scenarios:
    | Customer | Tier | Issue |
    |----------|------|-------|
    | **Priya Nair** | Gold | Flight SK-204 (Delhi→Goa) — Cancelled |
    | **Arvind Kulkarni** | Silver | Flight SK-118 (Mumbai→Bengaluru) — Delayed 4h |
    | **Meher Kaur** | Platinum | Flight SK-305 (Delhi→Hyderabad) — Delayed 6h |
    """)
    st.stop()


# Welcome message
orchestrator = st.session_state.orchestrator
customer = orchestrator.current_customer

if not st.session_state.messages:
    active_booking = orchestrator._get_active_booking()
    if active_booking:
        if active_booking.status == BookingStatus.CANCELLED:
            welcome = (
                f"Hello {customer.name}! Thank you for contacting SkyWay Airlines support. "
                f"I can see you're a valued {customer.loyalty_tier.value} member. "
                f"I notice your flight {active_booking.flight} ({active_booking.route}) "
                f"scheduled for {active_booking.date} has been cancelled due to {active_booking.status_reason}. "
                f"I'm here to help — how can I assist you today?"
            )
        elif active_booking.status == BookingStatus.DELAYED:
            welcome = (
                f"Hello {customer.name}! Thank you for contacting SkyWay Airlines support. "
                f"I can see you're a valued {customer.loyalty_tier.value} member. "
                f"I see your flight {active_booking.flight} ({active_booking.route}) "
                f"scheduled for {active_booking.date} at {active_booking.scheduled_departure} "
                f"has been delayed by {active_booking.delay_hours} hours "
                f"(new departure: {active_booking.new_departure}). "
                f"I'm here to help — what can I do for you?"
            )
        else:
            welcome = (
                f"Hello {customer.name}! Welcome to SkyWay Airlines support. "
                f"How can I help you today?"
            )
    else:
        welcome = f"Hello {customer.name}! Welcome to SkyWay Airlines support. How can I help you today?"

    st.session_state.messages.append({"role": "assistant", "content": welcome})


# Display chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="✈️" if msg["role"] == "assistant" else "👤"):
        # Check for escalation
        if msg.get("escalated"):
            st.markdown(
                '<div class="escalation-banner">⚠️ This conversation has been escalated to the specialist support team.</div>',
                unsafe_allow_html=True,
            )
        st.markdown(msg["content"])

        # Show action badges
        if msg.get("actions"):
            badges_html = " ".join(get_action_badge(a) for a in msg["actions"])
            st.markdown(badges_html, unsafe_allow_html=True)


# Chat input
if user_input := st.chat_input("Type your message...", key="chat_input"):
    # Display user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    # Get agent response
    with st.chat_message("assistant", avatar="✈️"):
        with st.spinner("Processing your request..."):
            response = orchestrator.handle_message(user_input)

        if response.escalated:
            st.markdown(
                '<div class="escalation-banner">⚠️ This conversation has been escalated to the specialist support team.</div>',
                unsafe_allow_html=True,
            )

        st.markdown(response.message)

        if response.actions_taken:
            action_types = [a.action_type.value for a in response.actions_taken]
            badges_html = " ".join(get_action_badge(a) for a in action_types)
            st.markdown(badges_html, unsafe_allow_html=True)

    # Save assistant message
    st.session_state.messages.append({
        "role": "assistant",
        "content": response.message,
        "escalated": response.escalated,
        "actions": [a.action_type.value for a in response.actions_taken] if response.actions_taken else [],
    })
