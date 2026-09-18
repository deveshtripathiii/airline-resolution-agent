"""SkyWay Airlines Disruption Resolution Portal.

Native Streamlit Architecture — Zero HTML escaping bugs, high-contrast, mobile-responsive.
Strictly grounded in AIONOS Assignment 3 PDF Guidelines.
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
    page_title="SkyWay Airlines | Disruption Care Portal",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ── Theme Management ──────────────────────────────────────────────────────────
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "sky_light"

is_dark = st.session_state.theme_mode == "night_dark"


# ── Clean High-Contrast CSS ───────────────────────────────────────────────────
if not is_dark:
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
        
        * {
            font-family: 'Plus Jakarta Sans', -apple-system, sans-serif !important;
        }

        .stApp {
            background: linear-gradient(180deg, #dbeafe 0%, #e0f2fe 25%, #f0f9ff 60%, #ffffff 100%) !important;
            color: #0f172a !important;
        }

        /* Navigation Banner */
        .sky-nav-banner {
            background: linear-gradient(135deg, #0284c7 0%, #0369a1 60%, #075985 100%);
            color: #ffffff;
            border-radius: 14px;
            padding: 16px 22px;
            margin-bottom: 18px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 8px 20px rgba(2, 132, 199, 0.25);
        }

        /* Tab Navigation */
        .stTabs [data-baseweb="tab-list"] {
            background-color: #ffffff !important;
            border-radius: 12px !important;
            padding: 5px !important;
            border: 2px solid #bae6fd !important;
            box-shadow: 0 4px 12px rgba(2, 132, 199, 0.08) !important;
        }
        
        .stTabs [data-baseweb="tab"] {
            color: #0369a1 !important;
            font-weight: 700 !important;
            font-size: 14px !important;
            padding: 8px 20px !important;
            border-radius: 8px !important;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #0284c7 !important;
            color: #ffffff !important;
        }

        .stButton>button {
            border-radius: 8px !important;
            font-weight: 700 !important;
            border: 1px solid #7dd3fc !important;
            background-color: #ffffff !important;
            color: #0369a1 !important;
        }

        .stSelectbox div[data-baseweb="select"] {
            background-color: #ffffff !important;
            border-radius: 8px !important;
            border: 1px solid #7dd3fc !important;
            color: #0f172a !important;
            font-weight: 600 !important;
        }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
        
        * {
            font-family: 'Plus Jakarta Sans', -apple-system, sans-serif !important;
        }

        .stApp {
            background: radial-gradient(circle at 10% 20%, #0f172a 0%, #020617 100%) !important;
            color: #f8fafc !important;
        }

        .sky-nav-banner {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 60%, #0284c7 100%);
            color: #ffffff;
            border-radius: 14px;
            padding: 16px 22px;
            margin-bottom: 18px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .stTabs [data-baseweb="tab-list"] {
            background-color: #1e293b !important;
            border-radius: 12px !important;
            padding: 5px !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
        }
        
        .stTabs [data-baseweb="tab"] {
            color: #94a3b8 !important;
            font-weight: 700 !important;
            font-size: 14px !important;
            padding: 8px 20px !important;
            border-radius: 8px !important;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #0284c7 !important;
            color: #ffffff !important;
        }

        .stButton>button {
            border-radius: 8px !important;
            font-weight: 700 !important;
            background-color: #1e293b !important;
            color: #f8fafc !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
        }

        .stSelectbox div[data-baseweb="select"] {
            background-color: #1e293b !important;
            border-radius: 8px !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            color: #f8fafc !important;
            font-weight: 600 !important;
        }
    </style>
    """, unsafe_allow_html=True)


# ── Action Chip Styles ─────────────────────────────────────────────────────────
st.markdown("""
<style>
    header {visibility: hidden;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}

    .action-chip {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 700;
        margin: 4px 4px 4px 0;
    }
    .chip-rebook { background: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; }
    .chip-refund { background: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }
    .chip-meal { background: #fef3c7; color: #b45309; border: 1px solid #fde68a; }
    .chip-lounge { background: #f3e8ff; color: #7e22ce; border: 1px solid #e9d5ff; }
    .chip-hotel { background: #ffe4e6; color: #be123c; border: 1px solid #fecdd3; }
    .chip-escalate { background: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; }
    .chip-decline { background: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; }
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


# ── Chip Renderer ──────────────────────────────────────────────────────────────
def render_chip(action_type: str) -> str:
    badges = {
        "rebook": ("✈️ Priority Rebooking Authorized", "chip-rebook"),
        "refund": ("💰 Full Refund Authorized (7 Days)", "chip-refund"),
        "meal_voucher": ("🍽️ Dining Voucher Issued", "chip-meal"),
        "lounge_access": ("🛋️ Executive Lounge Pass Issued", "chip-lounge"),
        "hotel_accommodation": ("🏨 Transit Accommodation Arranged", "chip-hotel"),
        "escalate_to_supervisor": ("🚨 Escalated to Duty Supervisor", "chip-escalate"),
        "decline_request": ("⛔ Exceeds Airline Policy (Declined)", "chip-decline"),
        "provide_info": ("ℹ️ Flight Telemetry Provided", "chip-rebook"),
    }
    label, css = badges.get(action_type, ("🔹 Action Confirmed", "chip-rebook"))
    return f'<span class="action-chip {css}">{label}</span>'


# ── Top Navigation Bar ─────────────────────────────────────────────────────────
st.markdown(f"""
<div class="sky-nav-banner">
    <div style="display: flex; align-items: center; gap: 12px;">
        <span style="font-size: 28px;">✈️</span>
        <div>
            <div style="font-size: 20px; font-weight: 800;">SkyWay Airlines</div>
            <div style="font-size: 11px; opacity: 0.9; font-weight: 600; letter-spacing: 1px; text-transform: uppercase;">
                Customer Self-Service & Disruption Care Portal
            </div>
        </div>
    </div>
    <div style="background: rgba(255, 255, 255, 0.2); padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 700;">
        📅 Flight Operations: <strong>{EXERCISE_DATE}</strong>
    </div>
</div>
""", unsafe_allow_html=True)


# ── Top Control Bar (Passenger Selector + Day/Night Toggle + Reset) ─────────────
customers = st.session_state.customer_repo.get_all()
cust_map = {f"{c.name} (PNR: {c.booking_reference} • {c.loyalty_tier.value} Member)": c.name for c in customers}
options_list = ["— Select Verified Passenger Itinerary —"] + list(cust_map.keys())

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
    )

with col_theme:
    theme_label = "🌙 Starry Night" if not is_dark else "☀️ Sky Day"
    if st.button(theme_label, use_container_width=True):
        st.session_state.theme_mode = "night_dark" if not is_dark else "sky_light"
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
    active_booking = orchestrator._get_active_booking()

    cities = active_booking.route.split("→") if active_booking else ["Delhi", "Goa"]
    origin_city = cities[0].strip() if len(cities) > 0 else "Delhi"
    dest_city = cities[1].strip() if len(cities) > 1 else "Goa"

    # ── Boarding Pass Card (100% Native Streamlit Container) ───────────────────
    with st.container(border=True):
        col_p1, col_p2 = st.columns([3, 1])
        with col_p1:
            st.markdown(f"### 👤 {active_cust.name} &nbsp; `{tier_val.upper()} MEMBER`")
            st.caption(f"Booking PNR: **{active_cust.booking_reference}** • Contact: {active_cust.contact.email} ({active_cust.contact.phone})")
        with col_p2:
            if active_booking:
                if active_booking.status == BookingStatus.CANCELLED:
                    st.error("● CANCELLED (OPERATIONAL)")
                elif active_booking.status == BookingStatus.DELAYED:
                    st.warning(f"● DELAYED {active_booking.delay_hours}H (EST: {active_booking.new_departure})")
                else:
                    st.success("● ON TIME")

        st.divider()

        # Flight Vector Telemetry
        c_org, c_route, c_dst = st.columns([1, 2, 1])
        with c_org:
            st.markdown(f"## {origin_city.upper()[:3]}")
            st.caption(origin_city)
        with c_route:
            flight_num = active_booking.flight if active_booking else "SK-204"
            st.markdown(f"<div style='text-align:center; font-weight:800; color:#0284c7; font-size:16px;'>Flight {flight_num}</div>", unsafe_allow_html=True)
            st.markdown("<div style='text-align:center; font-size:18px; color:#0284c7;'>✈ ─────────────── ➔</div>", unsafe_allow_html=True)
            sched_str = f"Sch: **{active_booking.scheduled_departure}**" if active_booking else "Sch: 18:40"
            if active_booking and active_booking.delay_hours:
                sched_str += f" &nbsp;•&nbsp; <span style='color:#b45309; font-weight:700;'>Rescheduled: {active_booking.new_departure}</span>"
            st.markdown(f"<div style='text-align:center; font-size:12px;'>{sched_str}</div>", unsafe_allow_html=True)
        with c_dst:
            st.markdown(f"## {dest_city.upper()[:3]}")
            st.caption(dest_city)

        st.divider()

        # History Stats
        m1, m2, m3 = st.columns(3)
        m1.metric("Annual Flights", f"{active_cust.travel_history.flights_last_12_months} (12M)")
        m2.metric("Service Complaints", f"{active_cust.travel_history.prior_complaints}")
        m3.metric("Complaint History", f"{active_cust.travel_history.complaint_details or 'None'}")


# ── Main Tabbed Experience ─────────────────────────────────────────────────────
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
            with st.container(border=True):
                st.markdown("**Flight SK-204 (DEL → GOI)**")
                st.error("● Cancelled (Operational)")
                st.caption("Passenger: **Priya Nair (Gold)**\n\nPolicy: Free Rebooking (24h) OR Full Refund (7 Days)")
        with sc2:
            with st.container(border=True):
                st.markdown("**Flight SK-118 (BOM → BLR)**")
                st.warning("● Delayed 4 Hours (11:10)")
                st.caption("Passenger: **Arvind Kulkarni (Silver)**\n\nPolicy: Meal Voucher + Lounge Access")
        with sc3:
            with st.container(border=True):
                st.markdown("**Flight SK-305 (DEL → HYD)**")
                st.warning("● Delayed 6 Hours (20:00)")
                st.caption("Passenger: **Meher Kaur (Platinum)**\n\nPolicy: Meal + Lounge + Transit Hotel + Supervisor Review")
    else:
        # Welcome message
        if not st.session_state.messages:
            if active_booking and active_booking.status == BookingStatus.CANCELLED:
                welcome = (
                    f"Hello **{active_cust.name}**. As a valued **{active_cust.loyalty_tier.value} Member**, we sincerely apologize that flight **{active_booking.flight} ({active_booking.route})** "
                    f"has been cancelled due to operational reasons.\n\n"
                    f"Under SkyWay Airlines policy, I can arrange **Free Priority Rebooking** on the next available flight within 24 hours, "
                    f"or process a **Full Refund** to your original payment method. Which option would you prefer?"
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
                    st.error("🚨 **PRIORITY CASE ESCALATED TO DUTY SUPERVISOR** — Authority threshold reached or formal legal notice received. A senior specialist has taken ownership of this file.")

                st.markdown(msg["content"])

                if msg.get("actions"):
                    chips_html = "".join([render_chip(a) for a in msg["actions"]])
                    st.markdown(f"<div style='margin-top: 8px;'>{chips_html}</div>", unsafe_allow_html=True)

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
            if st.button("💰 Request Full Refund", key="b_ref", use_container_width=True):
                st.session_state.pending_prompt = "I would like to request a full refund for my flight."
                st.rerun()
        with q2:
            if st.button("✈️ Request Priority Rebook", key="b_reb", use_container_width=True):
                st.session_state.pending_prompt = "Please rebook me on the next available flight."
                st.rerun()
        with q3:
            if st.button("🍽️ Claim Meal & Lounge", key="b_vou", use_container_width=True):
                st.session_state.pending_prompt = "What meal vouchers and lounge access am I entitled to?"
                st.rerun()
        with q4:
            if st.button("🏨 Inquire Transit Hotel", key="b_hot", use_container_width=True):
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
        with st.container(border=True):
            st.markdown("#### 1. Cancellation Rebooking Policy")
            st.markdown("""
            When a flight is cancelled by SkyWay Airlines for operational reasons, passengers are entitled to choose between:
            - **Free Rebooking** on the next available flight within 24 hours (with priority seating for Gold/Platinum members).
            - **Full Refund** issued to the original payment method within 7 business days.
            """)

        with st.container(border=True):
            st.markdown("#### 2. Delay Care & Entitlements Tiers")
            st.markdown("""
            - **Under 3 Hours Delay:** ₹500 Dining Voucher.
            - **3 to 5 Hours Delay:** Meal Voucher + Executive Departure Lounge Access.
            - **Over 5 Hours Delay:** Meal Voucher + Lounge Access + Hotel Accommodation covering the delayed-hours duration only (not a full night's stay).
            """)

    with r2:
        with st.container(border=True):
            st.markdown("#### 3. Fare Difference & Rebooking Authority")
            st.markdown("""
            When passengers voluntarily choose alternative higher-fare flights:
            - **Up to ₹1,500 difference:** Front-line agent has direct waiver authority.
            - **Above ₹1,500 difference:** Mandatory escalation to Duty Supervisor.
            """)

        with st.container(border=True):
            st.markdown("#### 4. Loyalty Tier Benefits")
            st.markdown("""
            - **Gold & Platinum Members:** Receive first-priority rebooking on replacement flights.
            - *Note:* Loyalty status does not authorize complimentary cabin upgrades or compensation beyond standard policy.
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
