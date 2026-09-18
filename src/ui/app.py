"""SkyWay Airlines Disruption Resolution Portal — Luxury Enterprise UI.

Features:
- Seamless Day (Light) / Night (Dark) mode toggle
- 100% crystal clear typography and high-contrast readability
- Digital Boarding Pass with dynamic status badges
- Grounded multi-turn conversational agent
- Official Policy Directory & Immutable Audit Record
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


# ── Page Configuration ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SkyWay Airlines | Disruption Care Portal",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ── Theme State Initialization ────────────────────────────────────────────────
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "dark"


def toggle_theme():
    st.session_state.theme_mode = "light" if st.session_state.theme_mode == "dark" else "dark"


is_dark = st.session_state.theme_mode == "dark"


# ── Dynamic CSS Injection for Light / Dark Mode ────────────────────────────────
if is_dark:
    theme_css = """
    <style>
        :root {
            --bg-color: #0b1120;
            --surface-color: #1e293b;
            --surface-border: rgba(255, 255, 255, 0.12);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --header-bg: rgba(15, 23, 42, 0.85);
            --pass-bg: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
            --rule-bg: #1e293b;
            --chat-user-bg: #2563eb;
            --chat-user-text: #ffffff;
            --chat-bot-bg: #1e293b;
            --chat-bot-text: #f8fafc;
            --input-bg: #1e293b;
            --input-text: #f8fafc;
            --divider: rgba(255, 255, 255, 0.1);
        }
        .stApp {
            background: radial-gradient(circle at 10% 20%, #0f172a 0%, #020617 90%) !important;
            color: #f8fafc !important;
        }
    </style>
    """
else:
    theme_css = """
    <style>
        :root {
            --bg-color: #f8fafc;
            --surface-color: #ffffff;
            --surface-border: #e2e8f0;
            --text-main: #0f172a;
            --text-muted: #64748b;
            --header-bg: rgba(255, 255, 255, 0.95);
            --pass-bg: linear-gradient(145deg, #ffffff 0%, #f1f5f9 100%);
            --rule-bg: #ffffff;
            --chat-user-bg: #0284c7;
            --chat-user-text: #ffffff;
            --chat-bot-bg: #ffffff;
            --chat-bot-text: #0f172a;
            --input-bg: #ffffff;
            --input-text: #0f172a;
            --divider: #e2e8f0;
        }
        .stApp {
            background: #f8fafc !important;
            color: #0f172a !important;
        }
    </style>
    """

st.markdown(theme_css, unsafe_allow_html=True)

# ── Main Style Definitions ─────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@600;700&display=swap');

    * {
        font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
        box-sizing: border-box;
    }

    header {visibility: hidden;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}

    /* Top Brand Header */
    .portal-nav {
        background: var(--header-bg);
        backdrop-filter: blur(20px);
        border: 1px solid var(--surface-border);
        border-radius: 18px;
        padding: 16px 24px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 16px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
    }

    .brand-group {
        display: flex;
        align-items: center;
        gap: 14px;
    }

    .brand-icon {
        background: linear-gradient(135deg, #0284c7 0%, #38bdf8 100%);
        width: 44px;
        height: 44px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        color: white;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.35);
    }

    .brand-name {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 22px;
        font-weight: 700;
        color: var(--text-main);
        letter-spacing: -0.5px;
        margin: 0;
        line-height: 1.1;
    }

    .brand-sub {
        font-size: 11px;
        color: #0284c7;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-top: 3px;
    }

    .live-badge {
        background: rgba(16, 185, 129, 0.12);
        border: 1px solid rgba(16, 185, 129, 0.3);
        color: #10b981;
        padding: 6px 14px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .live-pulse {
        width: 8px;
        height: 8px;
        background-color: #10b981;
        border-radius: 50%;
        box-shadow: 0 0 10px #10b981;
    }

    /* Boarding Pass Hero */
    .pass-card {
        background: var(--pass-bg);
        border: 1px solid var(--surface-border);
        border-radius: 20px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.08);
        position: relative;
        overflow: hidden;
    }

    .pass-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #0284c7, #6366f1, #a855f7);
    }

    .pass-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
        margin-bottom: 16px;
    }

    .passenger-block {
        display: flex;
        align-items: center;
        gap: 14px;
    }

    .avatar-circle {
        width: 48px;
        height: 48px;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 18px;
        color: #ffffff;
    }

    .avatar-gold { background: linear-gradient(135deg, #f59e0b, #d97706); }
    .avatar-platinum { background: linear-gradient(135deg, #a855f7, #7e22ce); }
    .avatar-silver { background: linear-gradient(135deg, #64748b, #475569); }

    .tag-tier-badge {
        display: inline-block;
        font-size: 11px;
        font-weight: 800;
        padding: 3px 10px;
        border-radius: 6px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .tier-gold-style { background: rgba(245, 158, 11, 0.15); color: #d97706; border: 1px solid rgba(245, 158, 11, 0.4); }
    .tier-platinum-style { background: rgba(168, 85, 247, 0.15); color: #9333ea; border: 1px solid rgba(168, 85, 247, 0.4); }
    .tier-silver-style { background: rgba(100, 116, 139, 0.15); color: #475569; border: 1px solid rgba(100, 116, 139, 0.4); }

    /* Flight Telemetry Vector */
    .flight-telemetry {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 18px 0;
        border-top: 1px dashed var(--divider);
        border-bottom: 1px dashed var(--divider);
        margin: 16px 0;
    }

    .airport-point {
        text-align: center;
    }

    .airport-iata {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 28px;
        font-weight: 800;
        color: var(--text-main);
        letter-spacing: -0.5px;
    }

    .airport-name {
        font-size: 13px;
        color: var(--text-muted);
        font-weight: 500;
        margin-top: 2px;
    }

    .flight-track-line {
        flex-grow: 1;
        margin: 0 24px;
        display: flex;
        flex-direction: column;
        align-items: center;
        position: relative;
    }

    .track-graphic {
        width: 100%;
        height: 2px;
        background: linear-gradient(90deg, #0284c7 0%, #6366f1 50%, #a855f7 100%);
        position: relative;
    }

    .track-plane-icon {
        position: absolute;
        top: -12px;
        font-size: 18px;
    }

    .status-capsule {
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

    .status-cancelled-cap { background: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; }
    .status-delayed-cap { background: #fef3c7; color: #b45309; border: 1px solid #fde68a; }
    .status-unaffected-cap { background: #dcfce7; color: #15803d; border: 1px solid #86efac; }

    /* Escalation Card */
    .escalation-box {
        background: #fee2e2;
        border: 1px solid #ef4444;
        border-radius: 14px;
        padding: 16px;
        margin: 14px 0;
        color: #7f1d1d;
        display: flex;
        gap: 14px;
        align-items: flex-start;
    }

    /* Action Badges in Chat */
    .action-chip {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 4px 12px;
        border-radius: 8px;
        font-size: 11px;
        font-weight: 700;
        margin: 4px 4px 4px 0;
    }

    .chip-rebook-c { background: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; }
    .chip-refund-c { background: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }
    .chip-meal-c { background: #fef3c7; color: #b45309; border: 1px solid #fde68a; }
    .chip-lounge-c { background: #f3e8ff; color: #7e22ce; border: 1px solid #e9d5ff; }
    .chip-hotel-c { background: #ffe4e6; color: #be123c; border: 1px solid #fecdd3; }
    .chip-escalate-c { background: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; }
    .chip-decline-c { background: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; }

    /* Policy Cards */
    .policy-box {
        background: var(--surface-color);
        border: 1px solid var(--surface-border);
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 14px;
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


# ── Action Chip Renderer ───────────────────────────────────────────────────────
def render_chip(action_type: str) -> str:
    badges = {
        "rebook": ("✈️ Priority Rebooking Authorized", "chip-rebook-c"),
        "refund": ("💰 Full Refund Authorized (7 Days)", "chip-refund-c"),
        "meal_voucher": ("🍽️ Dining Voucher Issued", "chip-meal-c"),
        "lounge_access": ("🛋️ Executive Lounge Pass Issued", "chip-lounge-c"),
        "hotel_accommodation": ("🏨 Transit Accommodation Arranged", "chip-hotel-c"),
        "escalate_to_supervisor": ("🚨 Escalated to Duty Supervisor", "chip-escalate-c"),
        "decline_request": ("⛔ Exceeds Airline Policy (Declined)", "chip-decline-c"),
        "provide_info": ("ℹ️ Flight Telemetry Provided", "chip-rebook-c"),
    }
    label, css = badges.get(action_type, ("🔹 Action Confirmed", "chip-rebook-c"))
    return f'<span class="action-chip {css}">{label}</span>'


# ── Top Navbar ─────────────────────────────────────────────────────────────────
nav_html = f"""
<div class="portal-nav">
    <div class="brand-group">
        <div class="brand-icon">✈</div>
        <div>
            <div class="brand-name">SkyWay Airlines</div>
            <div class="brand-sub">Customer Self-Service & Disruption Care Portal</div>
        </div>
    </div>
    <div class="live-badge">
        <div class="live-pulse"></div>
        <span>Live Flight Ops • {EXERCISE_DATE}</span>
    </div>
</div>
"""
st.markdown(textwrap.dedent(nav_html).strip(), unsafe_allow_html=True)


# ── Theme Toggle & Passenger Selector Controls ─────────────────────────────────
customers = st.session_state.customer_repo.get_all()
cust_map = {f"{c.name} — PNR: {c.booking_reference} ({c.loyalty_tier.value} Member)": c.name for c in customers}
options_list = ["— Enter / Select Verified Passenger Booking —"] + list(cust_map.keys())

current_idx = 0
if st.session_state.selected_customer:
    for i, label in enumerate(options_list):
        if label != options_list[0] and cust_map[label] == st.session_state.selected_customer:
            current_idx = i
            break

col_pnr, col_theme, col_reset = st.columns([3, 1, 1])

with col_pnr:
    selected_label = st.selectbox(
        "Passenger Itinerary Verification:",
        options=options_list,
        index=current_idx,
        label_visibility="collapsed",
        help="Access booking records by verified passenger itinerary."
    )

with col_theme:
    theme_btn_label = "☀️ Light Mode" if is_dark else "🌙 Dark Mode"
    if st.button(theme_btn_label, use_container_width=True):
        toggle_theme()
        st.rerun()

with col_reset:
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
    avatar_css = {"Platinum": "avatar-platinum", "Gold": "avatar-gold", "Silver": "avatar-silver"}.get(tier_val, "avatar-silver")
    tag_css = {"Platinum": "tier-platinum-style", "Gold": "tier-gold-style", "Silver": "tier-silver-style"}.get(tier_val, "tier-silver-style")
    initials = "".join([part[0] for part in active_cust.name.split() if part])

    active_booking = orchestrator._get_active_booking()

    cities = active_booking.route.split("→") if active_booking else ["DEL", "GOA"]
    origin_city = cities[0].strip() if len(cities) > 0 else "DEL"
    dest_city = cities[1].strip() if len(cities) > 1 else "GOA"

    status_pill_class = "status-unaffected-cap"
    status_label = "ON TIME"
    if active_booking:
        if active_booking.status == BookingStatus.CANCELLED:
            status_pill_class = "status-cancelled-cap"
            status_label = "CANCELLED (OPERATIONAL)"
        elif active_booking.status == BookingStatus.DELAYED:
            status_pill_class = "status-delayed-cap"
            status_label = f"DELAYED {active_booking.delay_hours}H (NEW: {active_booking.new_departure})"

    # ── Boarding Pass Card ─────────────────────────────────────────────────────
    pass_html = f"""
    <div class="pass-card">
        <div class="pass-header">
            <div class="passenger-block">
                <div class="avatar-circle {avatar_css}">{initials}</div>
                <div>
                    <div style="font-size: 18px; font-weight: 700; color: var(--text-main);">{active_cust.name}</div>
                    <div style="font-size: 12px; color: var(--text-muted); margin-top: 2px;">
                        Booking PNR: <strong style="color: #0284c7;">{active_cust.booking_reference}</strong> &nbsp;•&nbsp; 
                        <span class="tag-tier-badge {tag_css}">{tier_val} MEMBER</span>
                    </div>
                </div>
            </div>
            <div>
                <span class="status-capsule {status_pill_class}">● {status_label}</span>
            </div>
        </div>

        <div class="flight-telemetry">
            <div class="airport-point">
                <div class="airport-iata">{origin_city.upper()[:3]}</div>
                <div class="airport-name">{origin_city}</div>
            </div>
            <div class="flight-track-line">
                <div style="font-size: 12px; color: #0284c7; font-weight: 700; margin-bottom: 6px;">
                    Flight {active_booking.flight if active_booking else 'SK-204'}
                </div>
                <div class="track-graphic">
                    <div class="track-plane-icon">✈</div>
                </div>
                <div style="font-size: 11px; color: var(--text-muted); margin-top: 6px;">
                    Scheduled: {active_booking.scheduled_departure if active_booking else '18:40'}
                    {f" &nbsp;•&nbsp; <strong style='color:#d97706;'>Rescheduled: {active_booking.new_departure}</strong>" if active_booking.delay_hours else ""}
                </div>
            </div>
            <div class="airport-point">
                <div class="airport-iata">{dest_city.upper()[:3]}</div>
                <div class="airport-name">{dest_city}</div>
            </div>
        </div>

        <div style="display: flex; justify-content: space-between; font-size: 12px; color: var(--text-muted); margin-top: 8px; flex-wrap: wrap; gap: 10px;">
            <div>✈ Annual Activity: <strong style="color: var(--text-main);">{active_cust.travel_history.flights_last_12_months} flights (12M)</strong></div>
            <div>📋 Service Records: <strong style="color: var(--text-main);">{active_cust.travel_history.prior_complaints} prior log</strong></div>
            <div>✉️ Passenger Contact: <strong style="color: var(--text-main);">{active_cust.contact.email}</strong></div>
        </div>
    </div>
    """
    st.markdown(textwrap.dedent(pass_html).strip(), unsafe_allow_html=True)


# ── Tabbed View ────────────────────────────────────────────────────────────────
tab_chat, tab_policy, tab_records = st.tabs([
    "💬 Disruption Resolution Chat",
    "📜 Policy & Entitlements Directory",
    "📁 Service Activity Record"
])


# ───────────────────────────────────────────────────────────────────────────────
# TAB 1: DISRUPTION RESOLUTION CHAT
# ───────────────────────────────────────────────────────────────────────────────
with tab_chat:
    if not active_cust:
        st.info("👈 **Please select your verified passenger booking from the dropdown above to begin.**")
        
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
                    esc_html = f"""
                    <div class="escalation-box">
                        <div style="font-size: 22px;">🚨</div>
                        <div>
                            <div style="font-size: 14px; font-weight: 700;">PRIORITY CASE ESCALATED TO DUTY SUPERVISOR</div>
                            <div style="font-size: 12px; margin-top: 2px;">
                                Authority boundary reached or formal notice received. A senior specialist has taken ownership of this file.
                            </div>
                        </div>
                    </div>
                    """
                    st.markdown(textwrap.dedent(esc_html).strip(), unsafe_allow_html=True)

                st.markdown(msg["content"])

                if msg.get("actions"):
                    chips_html = "".join([render_chip(a) for a in msg["actions"]])
                    st.markdown(f"<div style='margin-top: 8px;'>{chips_html}</div>", unsafe_allow_html=True)

        # Chat Input
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
            if st.button("💰 Request Full Refund", key="btn_q_ref", use_container_width=True):
                st.session_state.pending_prompt = "I would like to request a full refund for my flight."
                st.rerun()
        with q2:
            if st.button("✈️ Request Priority Rebook", key="btn_q_reb", use_container_width=True):
                st.session_state.pending_prompt = "Please rebook me on the next available flight."
                st.rerun()
        with q3:
            if st.button("🍽️ Claim Meal & Lounge", key="btn_q_vou", use_container_width=True):
                st.session_state.pending_prompt = "What meal vouchers and lounge access am I entitled to?"
                st.rerun()
        with q4:
            if st.button("🏨 Inquire Transit Hotel", key="btn_q_hot", use_container_width=True):
                st.session_state.pending_prompt = "Can you arrange hotel accommodation for my delay?"
                st.rerun()


# ───────────────────────────────────────────────────────────────────────────────
# TAB 2: POLICY DIRECTORY
# ───────────────────────────────────────────────────────────────────────────────
with tab_policy:
    st.markdown("### 📜 SkyWay Airlines Disruption Service Rules")
    st.caption("Official grounded guidelines governing flight disruptions, passenger care, and financial limits.")

    r1, r2 = st.columns(2)
    with r1:
        pol1 = """
        <div class="policy-box">
            <h4 style="color: #0284c7; margin: 0 0 8px 0;">1. Cancellation Rebooking Policy</h4>
            <p style="font-size: 13px; color: var(--text-muted); line-height: 1.5;">
                When a flight is cancelled by SkyWay Airlines for operational reasons, passengers are entitled to choose between:
                <br/>• <strong>Free Rebooking</strong> on the next available flight within 24 hours (with priority seating for Gold/Platinum members).
                <br/>• <strong>Full Refund</strong> issued to the original payment method within 7 business days.
            </p>
        </div>

        <div class="policy-box">
            <h4 style="color: #d97706; margin: 0 0 8px 0;">2. Delay Care & Entitlements Tiers</h4>
            <p style="font-size: 13px; color: var(--text-muted); line-height: 1.5;">
                • <strong>Under 3 Hours Delay:</strong> ₹500 Dining Voucher.<br/>
                • <strong>3 to 5 Hours Delay:</strong> Meal Voucher + Executive Departure Lounge Access.<br/>
                • <strong>Over 5 Hours Delay:</strong> Meal Voucher + Lounge Access + Hotel Accommodation covering the delayed-hours duration only (not a full night's stay).
            </p>
        </div>
        """
        st.markdown(textwrap.dedent(pol1).strip(), unsafe_allow_html=True)

    with r2:
        pol2 = """
        <div class="policy-box">
            <h4 style="color: #10b981; margin: 0 0 8px 0;">3. Fare Difference & Rebooking Authority</h4>
            <p style="font-size: 13px; color: var(--text-muted); line-height: 1.5;">
                When passengers voluntarily choose alternative higher-fare flights:
                <br/>• <strong>Up to ₹1,500 difference:</strong> Front-line agent has direct waiver authority.
                <br/>• <strong>Above ₹1,500 difference:</strong> Mandatory escalation to Duty Supervisor.
            </p>
        </div>

        <div class="policy-box">
            <h4 style="color: #a855f7; margin: 0 0 8px 0;">4. Loyalty Tier Benefits</h4>
            <p style="font-size: 13px; color: var(--text-muted); line-height: 1.5;">
                • <strong>Gold & Platinum Members:</strong> Receive first-priority rebooking on replacement flights.
                <br/>• <em>Note:</em> Loyalty status does not authorize complimentary cabin upgrades or compensation beyond standard policy.
            </p>
        </div>
        """
        st.markdown(textwrap.dedent(pol2).strip(), unsafe_allow_html=True)


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
