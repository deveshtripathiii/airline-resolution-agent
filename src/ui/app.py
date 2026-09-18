"""SkyWay Airlines Disruption Resolution Portal — Luxury Responsive UI.

Strictly grounded in AIONOS Assignment 3 Data Pack & Policy Rules.
Designed for both Desktop and Mobile devices.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from src.agent.orchestrator import AgentOrchestrator
from src.config import EXERCISE_DATE, GEMINI_API_KEY
from src.data_access.repository import BookingRepository, CustomerRepository, PolicyRepository
from src.domain.models import ActionType, BookingStatus
from src.llm.client import GeminiClient, SmartDeterministicClient


# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SkyWay Airlines | Disruption Resolution",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ── Premium Responsive CSS ─────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500&display=swap');
    
    :root {
        --bg-main: #0b1120;
        --card-bg: #1e293b;
        --card-border: #334155;
        --accent-blue: #38bdf8;
        --accent-gold: #f59e0b;
        --accent-platinum: #c084fc;
        --accent-silver: #94a3b8;
        --text-primary: #f8fafc;
        --text-secondary: #94a3b8;
    }

    * {
        font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
        box-sizing: border-box;
    }

    .stApp {
        background: radial-gradient(circle at top right, #1e293b, #0f172a 50%, #020617 100%);
        color: #f8fafc;
    }

    /* Hide standard Streamlit header clutter */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}

    /* Top Navigation Bar */
    .sky-navbar {
        background: rgba(15, 23, 42, 0.75);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 14px 20px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }

    .sky-brand {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .sky-logo-icon {
        background: linear-gradient(135deg, #0284c7, #38bdf8);
        width: 42px;
        height: 42px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        box-shadow: 0 4px 12px rgba(56, 189, 248, 0.35);
    }

    .sky-brand-name {
        font-size: 20px;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.5px;
        margin: 0;
    }

    .sky-brand-tag {
        font-size: 11px;
        font-weight: 600;
        color: #38bdf8;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .sky-date-badge {
        background: rgba(56, 189, 248, 0.1);
        border: 1px solid rgba(56, 189, 248, 0.25);
        color: #bae6fd;
        padding: 6px 14px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    /* Digital Boarding Pass Mobile-First Card */
    .digital-pass {
        background: linear-gradient(145deg, #1e293b, #0f172a);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 15px 35px -10px rgba(0, 0, 0, 0.5);
        position: relative;
        overflow: hidden;
    }

    .digital-pass::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
    }

    .pass-top-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
    }

    .passenger-avatar-box {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .avatar-circle {
        width: 44px;
        height: 44px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 16px;
        color: #0f172a;
    }

    .avatar-gold {
        background: linear-gradient(135deg, #fbbf24, #d97706);
        box-shadow: 0 0 15px rgba(245, 158, 11, 0.4);
    }

    .avatar-platinum {
        background: linear-gradient(135deg, #e879f9, #a855f7);
        box-shadow: 0 0 15px rgba(168, 85, 247, 0.4);
    }

    .avatar-silver {
        background: linear-gradient(135deg, #cbd5e1, #94a3b8);
        box-shadow: 0 0 15px rgba(148, 163, 184, 0.3);
    }

    .tier-pill {
        display: inline-block;
        font-size: 10px;
        font-weight: 800;
        padding: 2px 8px;
        border-radius: 6px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .tier-gold-pill { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.4); }
    .tier-platinum-pill { background: rgba(192, 132, 252, 0.2); color: #e9d5ff; border: 1px solid rgba(192, 132, 252, 0.4); }
    .tier-silver-pill { background: rgba(148, 163, 184, 0.2); color: #e2e8f0; border: 1px solid rgba(148, 163, 184, 0.4); }

    /* Flight Route Banner */
    .route-visual {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 0;
        border-top: 1px dashed rgba(255, 255, 255, 0.1);
        border-bottom: 1px dashed rgba(255, 255, 255, 0.1);
        margin: 12px 0;
    }

    .airport-node {
        text-align: center;
    }

    .airport-code {
        font-size: 24px;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.5px;
    }

    .airport-city {
        font-size: 12px;
        color: #94a3b8;
        font-weight: 500;
    }

    .flight-path-line {
        flex-grow: 1;
        margin: 0 16px;
        display: flex;
        flex-direction: column;
        align-items: center;
        position: relative;
    }

    .path-dash {
        width: 100%;
        height: 2px;
        background: linear-gradient(90deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
        position: relative;
    }

    .path-plane {
        position: absolute;
        top: -11px;
        font-size: 16px;
        animation: flightFloat 3s ease-in-out infinite;
    }

    @keyframes flightFloat {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-4px); }
    }

    /* Status Pills */
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 14px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .pill-cancelled {
        background: rgba(244, 63, 94, 0.15);
        color: #fda4af;
        border: 1px solid rgba(244, 63, 94, 0.4);
    }

    .pill-delayed {
        background: rgba(249, 115, 22, 0.15);
        color: #fdba74;
        border: 1px solid rgba(249, 115, 22, 0.4);
    }

    .pill-unaffected {
        background: rgba(16, 185, 129, 0.15);
        color: #6ee7b7;
        border: 1px solid rgba(16, 185, 129, 0.4);
    }

    /* Escalation Alert Card */
    .alert-escalate-card {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(153, 27, 27, 0.3));
        border: 1px solid #ef4444;
        border-radius: 14px;
        padding: 14px 18px;
        margin: 14px 0;
        color: #fecaca;
        display: flex;
        align-items: flex-start;
        gap: 12px;
        box-shadow: 0 4px 15px rgba(239, 68, 68, 0.25);
    }

    /* Action Badges in Chat */
    .badge-chip {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 11px;
        font-weight: 700;
        margin: 2px 4px 2px 0;
    }

    .chip-rebook { background: rgba(56, 189, 248, 0.15); color: #7dd3fc; border: 1px solid rgba(56, 189, 248, 0.3); }
    .chip-refund { background: rgba(52, 211, 153, 0.15); color: #6ee7b7; border: 1px solid rgba(52, 211, 153, 0.3); }
    .chip-meal { background: rgba(251, 191, 36, 0.15); color: #fde68a; border: 1px solid rgba(251, 191, 36, 0.3); }
    .chip-lounge { background: rgba(192, 132, 252, 0.15); color: #e9d5ff; border: 1px solid rgba(192, 132, 252, 0.3); }
    .chip-hotel { background: rgba(244, 63, 94, 0.15); color: #fecdd3; border: 1px solid rgba(244, 63, 94, 0.3); }
    .chip-escalate { background: rgba(239, 68, 68, 0.25); color: #fca5a5; border: 1px solid #ef4444; }
    .chip-decline { background: rgba(148, 163, 184, 0.15); color: #cbd5e1; border: 1px solid rgba(148, 163, 184, 0.3); }

    /* Policy Inspection Grid */
    .policy-card {
        background: #1e293b;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 12px;
    }

    .policy-title {
        font-size: 14px;
        font-weight: 700;
        color: #38bdf8;
        margin-bottom: 8px;
    }

    /* Mobile Responsive Optimizations */
    @media (max-width: 768px) {
        .sky-navbar {
            padding: 12px;
            flex-direction: column;
            align-items: flex-start;
        }
        .route-visual {
            padding: 10px 0;
        }
        .airport-code {
            font-size: 20px;
        }
        .digital-pass {
            padding: 14px;
        }
    }
</style>
""", unsafe_allow_html=True)


# ── Initialization ─────────────────────────────────────────────────────────────
def get_orchestrator() -> AgentOrchestrator:
    if "orchestrator" not in st.session_state:
        if GEMINI_API_KEY and GEMINI_API_KEY != "your_api_key_here":
            llm = GeminiClient(api_key=GEMINI_API_KEY)
        else:
            llm = SmartDeterministicClient()

        st.session_state.orchestrator = AgentOrchestrator(llm_client=llm)
        st.session_state.customer_repo = CustomerRepository()
        st.session_state.booking_repo = BookingRepository()
        st.session_state.policy_repo = PolicyRepository()
        st.session_state.messages = []
        st.session_state.selected_customer = None

    return st.session_state.orchestrator


orchestrator = get_orchestrator()


# ── Action Badge Renderer ──────────────────────────────────────────────────────
def render_chip(action_type: str) -> str:
    badges = {
        "rebook": ("✈️ Priority Rebooking", "chip-rebook"),
        "refund": ("💰 Full Refund (7 Days)", "chip-refund"),
        "meal_voucher": ("🍽️ Meal Voucher", "chip-meal"),
        "lounge_access": ("🛋️ Executive Lounge", "chip-lounge"),
        "hotel_accommodation": ("🏨 Hotel (Delayed Hours)", "chip-hotel"),
        "escalate_to_supervisor": ("🚨 Supervisor Escalation", "chip-escalate"),
        "decline_request": ("⛔ Exceeds Policy (Declined)", "chip-decline"),
        "provide_info": ("ℹ️ Flight Info", "chip-rebook"),
    }
    label, css = badges.get(action_type, ("🔹 Action", "chip-rebook"))
    return f'<span class="badge-chip {css}">{label}</span>'


# ── Header Navbar ──────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="sky-navbar">
    <div class="sky-brand">
        <div class="sky-logo-icon">✈</div>
        <div>
            <div class="sky-brand-name">SkyWay Airlines</div>
            <div class="sky-brand-tag">Disruption Resolution Portal • AIONOS Assignment 3</div>
        </div>
    </div>
    <div class="sky-date-badge">
        📅 Operational Context: <strong>{EXERCISE_DATE}</strong>
    </div>
</div>
""", unsafe_allow_html=True)


# ── Passenger Selector & Quick Launcher ────────────────────────────────────────
customers = st.session_state.customer_repo.get_all()
cust_options = ["— Choose Passenger Profile —"] + [c.name for c in customers]

current_idx = 0
if st.session_state.selected_customer:
    try:
        current_idx = cust_options.index(st.session_state.selected_customer)
    except ValueError:
        current_idx = 0

col_sel, col_reset = st.columns([4, 1])
with col_sel:
    selected_name = st.selectbox(
        "Select Passenger Profile:",
        options=cust_options,
        index=current_idx,
        label_visibility="collapsed",
        help="Choose one of the 3 assessment passengers to load their disruption context."
    )

with col_reset:
    if st.button("🔄 Reset Chat", use_container_width=True):
        st.session_state.messages = []
        if st.session_state.selected_customer:
            orchestrator.set_customer(st.session_state.selected_customer)
        st.rerun()

if selected_name != "— Choose Passenger Profile —" and selected_name != st.session_state.selected_customer:
    st.session_state.selected_customer = selected_name
    orchestrator.set_customer(selected_name)
    st.session_state.messages = []
    st.rerun()


active_cust = orchestrator.current_customer

if active_cust:
    # Determine avatar color
    tier_val = active_cust.loyalty_tier.value
    avatar_css = {"Platinum": "avatar-platinum", "Gold": "avatar-gold", "Silver": "avatar-silver"}.get(tier_val, "avatar-silver")
    pill_css = {"Platinum": "tier-platinum-pill", "Gold": "tier-gold-pill", "Silver": "tier-silver-pill"}.get(tier_val, "tier-silver-pill")
    initials = "".join([part[0] for part in active_cust.name.split() if part])

    active_booking = orchestrator._get_active_booking()
    
    # ── Digital Boarding Pass ──────────────────────────────────────────────────
    cities = active_booking.route.split("→") if active_booking else ["DEL", "GOA"]
    origin_city = cities[0].strip() if len(cities) > 0 else "DEL"
    dest_city = cities[1].strip() if len(cities) > 1 else "GOA"

    status_pill_class = "pill-unaffected"
    status_label = "UNAFFECTED"
    if active_booking:
        if active_booking.status == BookingStatus.CANCELLED:
            status_pill_class = "pill-cancelled"
            status_label = "CANCELLED (OPERATIONAL)"
        elif active_booking.status == BookingStatus.DELAYED:
            status_pill_class = "pill-delayed"
            status_label = f"DELAYED {active_booking.delay_hours}H (NEW: {active_booking.new_departure})"

    st.markdown(f"""
    <div class="digital-pass">
        <div class="pass-top-row">
            <div class="passenger-avatar-box">
                <div class="avatar-circle {avatar_css}">{initials}</div>
                <div>
                    <div style="font-size: 16px; font-weight: 700; color: #ffffff;">{active_cust.name}</div>
                    <div style="font-size: 12px; color: #94a3b8;">
                        PNR: <strong style="color: #38bdf8;">{active_cust.booking_reference}</strong> • 
                        <span class="tier-pill {pill_css}">{tier_val} TIER</span>
                    </div>
                </div>
            </div>
            <div>
                <span class="status-pill {status_pill_class}">● {status_label}</span>
            </div>
        </div>

        <div class="route-visual">
            <div class="airport-node">
                <div class="airport-code">{origin_city.upper()[:3]}</div>
                <div class="airport-city">{origin_city}</div>
            </div>
            <div class="flight-path-line">
                <div style="font-size: 11px; color: #38bdf8; font-weight: 600; margin-bottom: 4px;">
                    Flight {active_booking.flight if active_booking else 'SK-204'}
                </div>
                <div class="path-dash">
                    <div class="path-plane">✈</div>
                </div>
                <div style="font-size: 11px; color: #64748b; margin-top: 4px;">
                    Sch: {active_booking.scheduled_departure if active_booking else '18:40'}
                </div>
            </div>
            <div class="airport-node">
                <div class="airport-code">{dest_city.upper()[:3]}</div>
                <div class="airport-city">{dest_city}</div>
            </div>
        </div>

        <div style="display: flex; justify-content: space-between; font-size: 12px; color: #94a3b8; margin-top: 8px; flex-wrap: wrap; gap: 8px;">
            <div>✈ 12M Flights: <strong style="color: #f8fafc;">{active_cust.travel_history.flights_last_12_months}</strong></div>
            <div>⚠️ Prior Complaints: <strong style="color: #f8fafc;">{active_cust.travel_history.prior_complaints}</strong></div>
            <div>✉️ {active_cust.contact.email}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


    # ── 1-Click Recruiter Scenario Action Chips ────────────────────────────────
    st.markdown("##### ⚡ 1-Click Recruiter Assessment Scenarios:")
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        if st.button("🔴 Scenario 1: Priya (Cancelled + Upgrade Ask)", use_container_width=True):
            st.session_state.pending_prompt = "My flight SK-204 was cancelled and I am furious! I demand a full cash refund PLUS a free upgrade to business class on my return flight for the trouble!"
            st.rerun()

    with c2:
        if st.button("🟠 Scenario 2: Arvind (4h Delay + Hotel Ask)", use_container_width=True):
            st.session_state.pending_prompt = "My flight is delayed 4 hours and I'm missing an important meeting. Since it's such a long delay, I need hotel accommodation!"
            st.rerun()

    with c3:
        if st.button("🟣 Scenario 3: Meher (6h Delay + ₹2k Fare Diff)", use_container_width=True):
            st.session_state.pending_prompt = "My flight is delayed 6 hours. I want a full night hotel stay, and I want to be moved onto a different flight where the fare difference is ₹2,000."
            st.rerun()

    with c4:
        if st.button("⚖️ Test Legal Threat Escalation", use_container_width=True):
            st.session_state.pending_prompt = "This is unacceptable! I will file a formal complaint and take legal action with my attorney!"
            st.rerun()


# ── Tabs Navigation ────────────────────────────────────────────────────────────
tab_chat, tab_inspector, tab_audit = st.tabs([
    "💬 Passenger Support Chat",
    "⚖️ Policy Engine & Authority Inspector",
    "📋 Immutable Audit Log (JSONL)"
])


# ───────────────────────────────────────────────────────────────────────────────
# TAB 1: PASSENGER CHAT
# ───────────────────────────────────────────────────────────────────────────────
with tab_chat:
    if not active_cust:
        st.info("👈 **Please select a Passenger Profile from the dropdown above to start.**")
    else:
        # Welcome message
        if not st.session_state.messages:
            if active_booking and active_booking.status == BookingStatus.CANCELLED:
                welcome = (
                    f"Hello **{active_cust.name}**. As a valued **{active_cust.loyalty_tier.value} Member**, we sincerely apologize that flight **{active_booking.flight} ({active_booking.route})** "
                    f"has been cancelled due to operational reasons.\n\n"
                    f"Under airline policy, I am ready to arrange **Free Priority Rebooking** on the next available flight within 24 hours, "
                    f"or process a **Full Refund** to your original payment method. Which would you prefer?"
                )
            elif active_booking and active_booking.status == BookingStatus.DELAYED:
                welcome = (
                    f"Hello **{active_cust.name}**. We regret to inform you that flight **{active_booking.flight} ({active_booking.route})** "
                    f"is delayed by **{active_booking.delay_hours} hours** (rescheduled departure: **{active_booking.new_departure}**).\n\n"
                    f"I have reviewed your booking and am here to immediately assist you with eligible disruption compensation and care vouchers."
                )
            else:
                welcome = f"Hello {active_cust.name}, welcome to SkyWay Airlines Disruption Support. How can I assist you?"

            st.session_state.messages.append({"role": "assistant", "content": welcome})

        # Render conversation history
        for msg in st.session_state.messages:
            is_assistant = msg["role"] == "assistant"
            with st.chat_message(msg["role"], avatar="✈️" if is_assistant else "👤"):
                if msg.get("escalated"):
                    st.markdown(f"""
                    <div class="alert-escalate-card">
                        <div style="font-size: 20px;">🚨</div>
                        <div>
                            <strong>SUPERVISOR / SPECIALIST ESCALATION TRIGGERED</strong><br/>
                            <span style="font-size: 12px; color: #fecaca;">Reason: {msg.get('escalation_reason', 'Exceeds front-line authority or legal/complaint clause')}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown(msg["content"])

                if msg.get("actions"):
                    chips_html = "".join([render_chip(a) for a in msg["actions"]])
                    st.markdown(f"<div style='margin-top: 8px;'>{chips_html}</div>", unsafe_allow_html=True)

        # Handle user input from Chat Box or 1-Click Tests
        user_input = None
        if "pending_prompt" in st.session_state and st.session_state.pending_prompt:
            user_input = st.session_state.pending_prompt
            st.session_state.pending_prompt = None
        else:
            user_input = st.chat_input("Type your message here...")

        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            with st.spinner("Processing request via Rules Engine & LLM..."):
                resp = orchestrator.handle_message(user_input)

            st.session_state.messages.append({
                "role": "assistant",
                "content": resp.message,
                "escalated": resp.escalated,
                "escalation_reason": resp.escalation_reason,
                "actions": [a.action_type.value for a in resp.actions_taken],
            })
            st.rerun()

        # Passenger Quick Response Chips
        st.markdown("---")
        st.caption("📱 Passenger Quick Actions:")
        qc1, qc2, qc3, qc4 = st.columns(4)
        with qc1:
            if st.button("💰 Choose Full Refund", key="m_btn_ref", use_container_width=True):
                st.session_state.pending_prompt = "I would like to choose the full refund option."
                st.rerun()
        with qc2:
            if st.button("✈️ Choose Free Rebook", key="m_btn_reb", use_container_width=True):
                st.session_state.pending_prompt = "Please rebook me on the next available flight within 24 hours."
                st.rerun()
        with qc3:
            if st.button("🍽️ Claim Meal & Lounge", key="m_btn_vou", use_container_width=True):
                st.session_state.pending_prompt = "Please apply my eligible meal vouchers and lounge access."
                st.rerun()
        with qc4:
            if st.button("🏨 Inquire Hotel Stay", key="m_btn_hot", use_container_width=True):
                st.session_state.pending_prompt = "Can you provide hotel accommodation for my delay?"
                st.rerun()


# ───────────────────────────────────────────────────────────────────────────────
# TAB 2: RECRUITER POLICY INSPECTOR
# ───────────────────────────────────────────────────────────────────────────────
with tab_inspector:
    st.markdown("### ⚖️ Rules Engine & Guardrails Verification")
    st.caption("AIONOS Evaluators can verify strict adherence to Data Pack service rules & authority boundaries.")

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.markdown("""
        <div class="policy-card">
            <div class="policy-title">🟢 Allowed Actions (Front-line Agent Authority)</div>
            <ul style="font-size: 13px; color: #cbd5e1; margin-left: -15px;">
                <li>Rebook passenger on next available flight within 24h at zero charge (airline-caused)</li>
                <li>Issue ₹500 voucher (&lt;3h), Meal + Lounge (3–5h), Meal + Lounge + Hotel (&gt;5h)</li>
                <li>Arrange hotel accommodation for delayed-hours portion only (delays &gt;5h)</li>
                <li>Initiate refund request for airline cancellations (7 business days to original method)</li>
                <li>Provide passenger's own booking and flight status</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col_g2:
        st.markdown("""
        <div class="policy-card">
            <div class="policy-title" style="color: #f87171;">🔴 Prohibited Actions (Mandatory Escalation)</div>
            <ul style="font-size: 13px; color: #cbd5e1; margin-left: -15px;">
                <li>Approving compensation beyond stated policy amounts</li>
                <li>Waiving a fare difference above ₹1,500 without supervisor approval</li>
                <li>Making exceptions for non-airline-caused disruptions</li>
                <li>Handling threats of legal action or formal complaints (immediate specialist escalation)</li>
                <li>Processing refunds to a different payment method than original</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("#### ⏱️ Delay Compensation Tiers (PDF Ground Truth)")
    t1, t2, t3 = st.columns(3)
    with t1:
        st.markdown("""
        <div class="policy-card" style="border-left: 4px solid #38bdf8;">
            <strong>&lt; 3 Hours Delay</strong><br/>
            <span style="font-size: 13px; color: #94a3b8;">• ₹500 Meal Voucher</span>
        </div>
        """, unsafe_allow_html=True)
    with t2:
        st.markdown("""
        <div class="policy-card" style="border-left: 4px solid #fbbf24;">
            <strong>3 to 5 Hours Delay</strong><br/>
            <span style="font-size: 13px; color: #94a3b8;">• Meal Voucher<br/>• Executive Lounge Access</span>
        </div>
        """, unsafe_allow_html=True)
    with t3:
        st.markdown("""
        <div class="policy-card" style="border-left: 4px solid #f87171;">
            <strong>&gt; 5 Hours Delay</strong><br/>
            <span style="font-size: 13px; color: #94a3b8;">• Meal Voucher + Lounge<br/>• Hotel (Delayed hours only)</span>
        </div>
        """, unsafe_allow_html=True)


# ───────────────────────────────────────────────────────────────────────────────
# TAB 3: AUDIT LOG (JSONL)
# ───────────────────────────────────────────────────────────────────────────────
with tab_audit:
    st.markdown("### 📋 Immutable Audit Log & Traceability")
    st.caption("Preserving a clear, append-only conversation and action record per Assignment Brief Requirement 7.")

    entries = orchestrator.audit.get_log_entries()

    if not entries:
        st.info("No conversation records logged yet in this session.")
    else:
        st.dataframe(
            entries,
            column_config={
                "timestamp": "Timestamp (UTC)",
                "customer_name": "Passenger",
                "detected_intent": "Detected Intent",
                "detected_sentiment": "Sentiment",
                "escalated": "Escalated?",
                "agent_response": "Agent Output",
            },
            use_container_width=True,
        )

        log_json = json.dumps(entries, indent=2, ensure_ascii=False)
        st.download_button(
            label="📥 Download Audit Record (.json)",
            data=log_json,
            file_name=f"skyway_audit_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True,
        )
