"""SkyWay Airlines Disruption Resolution Portal — Official Production UI.

Authentic, customer-facing self-service resolution system.
Built with enterprise design standards and strict policy adherence.
"""

from __future__ import annotations

import json
import sys
import textwrap
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
    page_title="SkyWay Airlines | Disruption Care & Self-Service",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ── Custom HTML helper to avoid markdown 4-space code block traps ─────────────
def render_html(html_str: str) -> None:
    st.markdown(textwrap.dedent(html_str).strip(), unsafe_allow_html=True)


# ── Production-Grade Luxury Airline CSS ───────────────────────────────────────
render_html("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@600;700&display=swap');
    
    * {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        box-sizing: border-box;
    }

    .stApp {
        background: radial-gradient(circle at 10% 20%, #0f172a 0%, #020617 90%);
        color: #f8fafc;
    }

    header {visibility: hidden;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}

    /* Enterprise Navigation Header */
    .portal-header {
        background: rgba(15, 23, 42, 0.85);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 18px;
        padding: 16px 24px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 16px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
    }

    .brand-cluster {
        display: flex;
        align-items: center;
        gap: 14px;
    }

    .brand-emblem {
        background: linear-gradient(135deg, #0284c7 0%, #38bdf8 100%);
        width: 44px;
        height: 44px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        box-shadow: 0 4px 15px rgba(56, 189, 248, 0.4);
    }

    .brand-title-main {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 22px;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: -0.5px;
        margin: 0;
        line-height: 1.1;
    }

    .brand-subtitle-main {
        font-size: 11px;
        color: #38bdf8;
        font-weight: 600;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        margin-top: 3px;
    }

    .system-status-badge {
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.3);
        color: #6ee7b7;
        padding: 6px 14px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .live-dot {
        width: 8px;
        height: 8px;
        background-color: #10b981;
        border-radius: 50%;
        box-shadow: 0 0 10px #10b981;
        animation: livePulse 2s infinite;
    }

    @keyframes livePulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.4; transform: scale(1.2); }
    }

    /* Boarding Pass Hero Card */
    .flight-pass-hero {
        background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.6);
        position: relative;
        overflow: hidden;
    }

    .flight-pass-hero::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
    }

    .pass-profile-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
        margin-bottom: 18px;
    }

    .passenger-info-block {
        display: flex;
        align-items: center;
        gap: 14px;
    }

    .p-avatar {
        width: 48px;
        height: 48px;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 18px;
        color: #0f172a;
    }

    .avatar-gold-tier {
        background: linear-gradient(135deg, #fbbf24, #d97706);
        box-shadow: 0 0 20px rgba(245, 158, 11, 0.4);
    }

    .avatar-platinum-tier {
        background: linear-gradient(135deg, #e879f9, #a855f7);
        box-shadow: 0 0 20px rgba(168, 85, 247, 0.4);
    }

    .avatar-silver-tier {
        background: linear-gradient(135deg, #e2e8f0, #94a3b8);
        box-shadow: 0 0 20px rgba(148, 163, 184, 0.3);
    }

    .tag-tier {
        display: inline-block;
        font-size: 11px;
        font-weight: 800;
        padding: 3px 10px;
        border-radius: 6px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .tag-gold { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.4); }
    .tag-platinum { background: rgba(192, 132, 252, 0.2); color: #e9d5ff; border: 1px solid rgba(192, 132, 252, 0.4); }
    .tag-silver { background: rgba(148, 163, 184, 0.2); color: #e2e8f0; border: 1px solid rgba(148, 163, 184, 0.4); }

    /* Flight Route Telemetry */
    .telemetry-route {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 18px 0;
        border-top: 1px dashed rgba(255, 255, 255, 0.1);
        border-bottom: 1px dashed rgba(255, 255, 255, 0.1);
        margin: 16px 0;
    }

    .city-block {
        text-align: center;
    }

    .city-iata {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 28px;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.5px;
    }

    .city-full {
        font-size: 13px;
        color: #94a3b8;
        font-weight: 500;
        margin-top: 2px;
    }

    .vector-track {
        flex-grow: 1;
        margin: 0 24px;
        display: flex;
        flex-direction: column;
        align-items: center;
        position: relative;
    }

    .track-line {
        width: 100%;
        height: 2px;
        background: linear-gradient(90deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
        position: relative;
    }

    .track-jet {
        position: absolute;
        top: -12px;
        font-size: 18px;
        filter: drop-shadow(0 0 8px rgba(56, 189, 248, 0.8));
    }

    .disruption-pill {
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

    .pill-red {
        background: rgba(239, 68, 68, 0.15);
        color: #fca5a5;
        border: 1px solid rgba(239, 68, 68, 0.4);
    }

    .pill-amber {
        background: rgba(245, 158, 11, 0.15);
        color: #fde68a;
        border: 1px solid rgba(245, 158, 11, 0.4);
    }

    .pill-green {
        background: rgba(16, 185, 129, 0.15);
        color: #6ee7b7;
        border: 1px solid rgba(16, 185, 129, 0.4);
    }

    .escalation-handover-card {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.25), rgba(153, 27, 27, 0.35));
        border: 1px solid #ef4444;
        border-radius: 14px;
        padding: 16px;
        margin: 12px 0;
        color: #ffffff;
        display: flex;
        gap: 14px;
        box-shadow: 0 4px 20px rgba(239, 68, 68, 0.3);
    }

    .chip-tag {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 4px 12px;
        border-radius: 8px;
        font-size: 11px;
        font-weight: 700;
        margin: 3px 4px 3px 0;
    }

    .c-rebook { background: rgba(56, 189, 248, 0.15); color: #7dd3fc; border: 1px solid rgba(56, 189, 248, 0.35); }
    .c-refund { background: rgba(52, 211, 153, 0.15); color: #6ee7b7; border: 1px solid rgba(52, 211, 153, 0.35); }
    .c-meal { background: rgba(251, 191, 36, 0.15); color: #fde68a; border: 1px solid rgba(251, 191, 36, 0.35); }
    .c-lounge { background: rgba(192, 132, 252, 0.15); color: #e9d5ff; border: 1px solid rgba(192, 132, 252, 0.35); }
    .c-hotel { background: rgba(244, 63, 94, 0.15); color: #fecdd3; border: 1px solid rgba(244, 63, 94, 0.35); }
    .c-escalate { background: rgba(239, 68, 68, 0.25); color: #fca5a5; border: 1px solid #ef4444; }
    .c-decline { background: rgba(148, 163, 184, 0.15); color: #cbd5e1; border: 1px solid rgba(148, 163, 184, 0.35); }

    .rule-box {
        background: #1e293b;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 12px;
    }

    @media (max-width: 768px) {
        .portal-header {
            padding: 12px 16px;
            flex-direction: column;
            align-items: flex-start;
        }
        .telemetry-route {
            padding: 12px 0;
        }
        .city-iata {
            font-size: 22px;
        }
        .flight-pass-hero {
            padding: 16px;
        }
    }
</style>
""")


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


# ── Chip Formatter ─────────────────────────────────────────────────────────────
def render_chip(action_type: str) -> str:
    badges = {
        "rebook": ("✈️ Priority Rebooking Confirmed", "c-rebook"),
        "refund": ("💰 Full Refund Authorized (7 Days)", "c-refund"),
        "meal_voucher": ("🍽️ Dining Voucher Activated", "c-meal"),
        "lounge_access": ("🛋️ Executive Lounge Pass Issued", "c-lounge"),
        "hotel_accommodation": ("🏨 Transit Accommodation Arranged", "c-hotel"),
        "escalate_to_supervisor": ("🚨 Escalated to Duty Supervisor", "c-escalate"),
        "decline_request": ("⛔ Exceeds Airline Policy", "c-decline"),
        "provide_info": ("ℹ️ Booking Telemetry Provided", "c-rebook"),
    }
    label, css = badges.get(action_type, ("🔹 Action Confirmed", "c-rebook"))
    return f'<span class="chip-tag {css}">{label}</span>'


# ── Top Navigation Header ──────────────────────────────────────────────────────
render_html(f"""
<div class="portal-header">
    <div class="brand-cluster">
        <div class="brand-emblem">✈</div>
        <div>
            <div class="brand-title-main">SkyWay Airlines</div>
            <div class="brand-subtitle-main">Customer Self-Service & Disruption Care Portal</div>
        </div>
    </div>
    <div class="system-status-badge">
        <div class="live-dot"></div>
        <span>Live Operational System • {EXERCISE_DATE}</span>
    </div>
</div>
""")


# ── Passenger Verification & Selection Bar ─────────────────────────────────────
customers = st.session_state.customer_repo.get_all()
cust_map = {f"{c.name} — PNR: {c.booking_reference} ({c.loyalty_tier.value} Member)": c.name for c in customers}
options_list = ["— Enter / Select Verified Passenger Booking —"] + list(cust_map.keys())

current_idx = 0
if st.session_state.selected_customer:
    for i, label in enumerate(options_list):
        if label != options_list[0] and cust_map[label] == st.session_state.selected_customer:
            current_idx = i
            break

col_pnr, col_btn = st.columns([4, 1])
with col_pnr:
    selected_label = st.selectbox(
        "Passenger Itinerary Verification:",
        options=options_list,
        index=current_idx,
        label_visibility="collapsed",
        help="Access booking records by passenger itinerary."
    )

with col_btn:
    if st.button("🔄 New Session", use_container_width=True):
        st.session_state.messages = []
        if st.session_state.selected_customer:
            orchestrator.set_customer(st.session_state.selected_customer)
        st.rerun()

if selected_label != options_list[0]:
    chosen_name = cust_map[selected_label]
    if chosen_name != st.session_state.selected_customer:
        st.session_state.selected_customer = chosen_name
        orchestrator.set_customer(chosen_name)
        st.session_state.messages = []
        st.rerun()


active_cust = orchestrator.current_customer

if active_cust:
    tier_val = active_cust.loyalty_tier.value
    avatar_css = {"Platinum": "avatar-platinum-tier", "Gold": "avatar-gold-tier", "Silver": "avatar-silver-tier"}.get(tier_val, "avatar-silver-tier")
    tag_css = {"Platinum": "tag-platinum", "Gold": "tag-gold", "Silver": "tag-silver"}.get(tier_val, "tag-silver")
    initials = "".join([part[0] for part in active_cust.name.split() if part])

    active_booking = orchestrator._get_active_booking()

    cities = active_booking.route.split("→") if active_booking else ["DEL", "GOA"]
    origin_city = cities[0].strip() if len(cities) > 0 else "DEL"
    dest_city = cities[1].strip() if len(cities) > 1 else "GOA"

    status_pill_class = "pill-green"
    status_label = "ON TIME"
    if active_booking:
        if active_booking.status == BookingStatus.CANCELLED:
            status_pill_class = "pill-red"
            status_label = "CANCELLED (OPERATIONAL)"
        elif active_booking.status == BookingStatus.DELAYED:
            status_pill_class = "pill-amber"
            status_label = f"DELAYED {active_booking.delay_hours}H (EST: {active_booking.new_departure})"

    # ── Boarding Pass Visual ───────────────────────────────────────────────────
    render_html(f"""
<div class="flight-pass-hero">
    <div class="pass-profile-header">
        <div class="passenger-info-block">
            <div class="p-avatar {avatar_css}">{initials}</div>
            <div>
                <div style="font-size: 18px; font-weight: 700; color: #ffffff;">{active_cust.name}</div>
                <div style="font-size: 12px; color: #94a3b8; margin-top: 2px;">
                    PNR: <strong style="color: #38bdf8;">{active_cust.booking_reference}</strong> &nbsp;•&nbsp; 
                    <span class="tag-tier {tag_css}">{tier_val} TIER</span>
                </div>
            </div>
        </div>
        <div>
            <span class="disruption-pill {status_pill_class}">● {status_label}</span>
        </div>
    </div>
    <div class="telemetry-route">
        <div class="city-block">
            <div class="city-iata">{origin_city.upper()[:3]}</div>
            <div class="city-full">{origin_city}</div>
        </div>
        <div class="vector-track">
            <div style="font-size: 12px; color: #38bdf8; font-weight: 700; margin-bottom: 6px;">
                Flight {active_booking.flight if active_booking else 'SK-204'}
            </div>
            <div class="track-line">
                <div class="track-jet">✈</div>
            </div>
            <div style="font-size: 11px; color: #94a3b8; margin-top: 6px;">
                Scheduled: {active_booking.scheduled_departure if active_booking else '18:40'}
                {f" &nbsp;•&nbsp; <strong style='color:#fdba74;'>Rescheduled: {active_booking.new_departure}</strong>" if active_booking.delay_hours else ""}
            </div>
        </div>
        <div class="city-block">
            <div class="city-iata">{dest_city.upper()[:3]}</div>
            <div class="city-full">{dest_city}</div>
        </div>
    </div>
    <div style="display: flex; justify-content: space-between; font-size: 12px; color: #94a3b8; margin-top: 8px; flex-wrap: wrap; gap: 10px;">
        <div>✈ Annual Travel: <strong style="color: #f8fafc;">{active_cust.travel_history.flights_last_12_months} flights (12M)</strong></div>
        <div>📋 Service Records: <strong style="color: #f8fafc;">{active_cust.travel_history.prior_complaints} logged</strong></div>
        <div>✉️ Registered: <strong style="color: #f8fafc;">{active_cust.contact.email}</strong></div>
    </div>
</div>
""")


# ── Main Tabbed Experience ─────────────────────────────────────────────────────
tab_chat, tab_policy, tab_records = st.tabs([
    "💬 Support Chat Assistant",
    "📜 Policy & Entitlements Directory",
    "📁 Service Activity Record"
])


# ───────────────────────────────────────────────────────────────────────────────
# TAB 1: SUPPORT CHAT ASSISTANT
# ───────────────────────────────────────────────────────────────────────────────
with tab_chat:
    if not active_cust:
        render_html("""
        <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 20px; text-align: center; margin-bottom: 20px;">
            <div style="font-size: 24px; margin-bottom: 8px;">✈️</div>
            <div style="font-size: 16px; font-weight: 700; color: #ffffff;">Please select your verified passenger booking above to access care services.</div>
            <div style="font-size: 13px; color: #94a3b8; margin-top: 4px;">Self-service options for cancellations, flight delays, meal vouchers, and lounge passes.</div>
        </div>
        """)
        
        st.markdown("#### ✈️ Flight Disruption Network Status")
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            st.markdown("""
            **Flight SK-204 (DEL → GOI)**
            - **Status:** Cancelled (Operational)
            - **Passenger:** Priya Nair (Gold)
            - **Policy:** Free Rebooking (24h) OR Full Refund (7 Days)
            """)
        with sc2:
            st.markdown("""
            **Flight SK-118 (BOM → BLR)**
            - **Status:** Delayed 4 Hours (11:10)
            - **Passenger:** Arvind Kulkarni (Silver)
            - **Policy:** Meal Voucher + Lounge Access
            """)
        with sc3:
            st.markdown("""
            **Flight SK-305 (DEL → HYD)**
            - **Status:** Delayed 6 Hours (20:00)
            - **Passenger:** Meher Kaur (Platinum)
            - **Policy:** Meal + Lounge + Transit Hotel + Supervisor Fare Review
            """)
    else:
        # Welcome message
        if not st.session_state.messages:
            if active_booking and active_booking.status == BookingStatus.CANCELLED:
                welcome = (
                    f"Hello **{active_cust.name}**. As a valued **{active_cust.loyalty_tier.value} Member**, we sincerely apologize that flight **{active_booking.flight} ({active_booking.route})** "
                    f"has been cancelled due to operational reasons.\n\n"
                    f"Under SkyWay Airlines policy, I can arrange **Free Priority Rebooking** on the next available flight within 24 hours, "
                    f"or process a **Full Refund** to your original payment method. Which would you prefer?"
                )
            elif active_booking and active_booking.status == BookingStatus.DELAYED:
                welcome = (
                    f"Hello **{active_cust.name}**. We regret to inform you that flight **{active_booking.flight} ({active_booking.route})** "
                    f"is delayed by **{active_booking.delay_hours} hours** (rescheduled departure: **{active_booking.new_departure}**).\n\n"
                    f"I have verified your reservation and am ready to issue your eligible disruption vouchers and assist you with next steps. How can I help you today?"
                )
            else:
                welcome = f"Hello {active_cust.name}, welcome to SkyWay Airlines Disruption Support. How can I assist you today?"

            st.session_state.messages.append({"role": "assistant", "content": welcome})

        # Render conversation history
        for msg in st.session_state.messages:
            is_assistant = msg["role"] == "assistant"
            with st.chat_message(msg["role"], avatar="✈️" if is_assistant else "👤"):
                if msg.get("escalated"):
                    render_html("""
                    <div class="escalation-handover-card">
                        <div style="font-size: 24px;">🚨</div>
                        <div>
                            <div style="font-size: 14px; font-weight: 700;">PRIORITY CASE ESCALATED TO DUTY SUPERVISOR</div>
                            <div style="font-size: 12px; color: #fecaca; margin-top: 3px;">
                                Action: Front-line authority threshold reached or formal legal notice received. A senior specialist has taken ownership of this file.
                            </div>
                        </div>
                    </div>
                    """)

                st.markdown(msg["content"])

                if msg.get("actions"):
                    chips_html = "".join([render_chip(a) for a in msg["actions"]])
                    render_html(f"<div style='margin-top: 10px;'>{chips_html}</div>")

        # Chat Input Bar
        user_input = None
        if "pending_prompt" in st.session_state and st.session_state.pending_prompt:
            user_input = st.session_state.pending_prompt
            st.session_state.pending_prompt = None
        else:
            user_input = st.chat_input("Type your message to the SkyWay Disruption Agent...")

        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})

            with st.spinner("Evaluating disruption policies & generating resolution..."):
                resp = orchestrator.handle_message(user_input)

            st.session_state.messages.append({
                "role": "assistant",
                "content": resp.message,
                "escalated": resp.escalated,
                "escalation_reason": resp.escalation_reason,
                "actions": [a.action_type.value for a in resp.actions_taken],
            })
            st.rerun()

        # Passenger Quick Options
        st.markdown("---")
        st.caption("⚡ Quick Passenger Requests:")
        q1, q2, q3, q4 = st.columns(4)
        with q1:
            if st.button("💰 Request Full Refund", key="p_ref", use_container_width=True):
                st.session_state.pending_prompt = "I would like to request a full refund for my flight."
                st.rerun()
        with q2:
            if st.button("✈️ Request Priority Rebook", key="p_reb", use_container_width=True):
                st.session_state.pending_prompt = "Please rebook me on the next available flight."
                st.rerun()
        with q3:
            if st.button("🍽️ Claim Meal & Lounge", key="p_vou", use_container_width=True):
                st.session_state.pending_prompt = "What meal vouchers and lounge access am I entitled to?"
                st.rerun()
        with q4:
            if st.button("🏨 Inquire Transit Hotel", key="p_hot", use_container_width=True):
                st.session_state.pending_prompt = "Can you arrange hotel accommodation for my delay?"
                st.rerun()


# ───────────────────────────────────────────────────────────────────────────────
# TAB 2: POLICY DIRECTORY
# ───────────────────────────────────────────────────────────────────────────────
with tab_policy:
    st.markdown("### 📜 SkyWay Airlines Disruption Service Rules & Conditions")
    st.caption("Official grounded guidelines governing flight disruptions, passenger care, and financial limits.")

    r1, r2 = st.columns(2)
    with r1:
        render_html("""
        <div class="rule-box">
            <h4 style="color: #38bdf8; margin: 0 0 8px 0;">1. Cancellation Rebooking Policy</h4>
            <p style="font-size: 13px; color: #cbd5e1; line-height: 1.5;">
                When a flight is cancelled by SkyWay Airlines for operational reasons, passengers are entitled to choose between:
                <br/>• <strong>Free Rebooking</strong> on the next available flight within 24 hours (with priority seating for Gold/Platinum members).
                <br/>• <strong>Full Refund</strong> issued to the original payment method within 7 business days.
            </p>
        </div>

        <div class="rule-box">
            <h4 style="color: #fbbf24; margin: 0 0 8px 0;">2. Delay Care & Entitlements Tiers</h4>
            <p style="font-size: 13px; color: #cbd5e1; line-height: 1.5;">
                • <strong>Under 3 Hours Delay:</strong> ₹500 Dining Voucher.<br/>
                • <strong>3 to 5 Hours Delay:</strong> Meal Voucher + Executive Departure Lounge Access.<br/>
                • <strong>Over 5 Hours Delay:</strong> Meal Voucher + Lounge Access + Hotel Accommodation covering the delayed-hours duration only (not a full night's stay).
            </p>
        </div>
        """)

    with r2:
        render_html("""
        <div class="rule-box">
            <h4 style="color: #34d399; margin: 0 0 8px 0;">3. Fare Difference & Rebooking Authority</h4>
            <p style="font-size: 13px; color: #cbd5e1; line-height: 1.5;">
                When passengers voluntarily choose alternative higher-fare flights:
                <br/>• <strong>Up to ₹1,500 difference:</strong> Front-line agent has direct waiver authority.
                <br/>• <strong>Above ₹1,500 difference:</strong> Mandatory escalation to Duty Supervisor.
            </p>
        </div>

        <div class="rule-box">
            <h4 style="color: #c084fc; margin: 0 0 8px 0;">4. Loyalty Tier Benefits</h4>
            <p style="font-size: 13px; color: #cbd5e1; line-height: 1.5;">
                • <strong>Gold & Platinum Members:</strong> Receive first-priority rebooking on replacement flights.
                <br/>• <em>Note:</em> Loyalty status does not authorize complimentary cabin upgrades or compensation beyond standard policy.
            </p>
        </div>
        """)


# ───────────────────────────────────────────────────────────────────────────────
# TAB 3: SERVICE ACTIVITY RECORD
# ───────────────────────────────────────────────────────────────────────────────
with tab_records:
    st.markdown("### 📁 Passenger Service Record & Case History")
    st.caption("Immutable append-only activity log preserving all customer interactions, policy evaluations, and supervisor actions.")

    entries = orchestrator.audit.get_log_entries()

    if not entries:
        st.info("No active service interactions logged in this session yet.")
    else:
        st.dataframe(
            entries,
            column_config={
                "timestamp": "Timestamp (UTC)",
                "customer_name": "Passenger Name",
                "detected_intent": "Service Intent",
                "detected_sentiment": "Sentiment",
                "escalated": "Supervisor Escalation?",
                "agent_response": "Agent Resolution",
            },
            use_container_width=True,
        )

        log_json = json.dumps(entries, indent=2, ensure_ascii=False)
        st.download_button(
            label="📥 Download Service Transcript (.json)",
            data=log_json,
            file_name=f"skyway_service_record_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True,
        )
