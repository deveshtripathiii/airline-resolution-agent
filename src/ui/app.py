"""SkyWay Airlines Disruption Resolution Portal.

Features:
- Sky & Clouds theme (Aviation Aesthetic)
- 100% crystal-clear text contrast & tab visibility
- Zero HTML code-block rendering errors
- Bulletproof Day (Sky Light) & Night (Starry Dark) toggle
- Strict adherence to AIONOS Assignment 3 PDF guidelines
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
    st.session_state.theme_mode = "sky_light"  # Default to beautiful sky light theme

is_dark = st.session_state.theme_mode == "night_dark"


# ── Aviation & Sky Theme CSS ──────────────────────────────────────────────────
if not is_dark:
    # ⛅ Sky Day Theme (Blue Skies & Clouds)
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@600;700&display=swap');
        
        * {
            font-family: 'Plus Jakarta Sans', -apple-system, sans-serif !important;
        }

        /* Full page sky & soft cloud atmosphere */
        .stApp {
            background: linear-gradient(180deg, #dbeafe 0%, #e0f2fe 30%, #f0f9ff 70%, #ffffff 100%) !important;
            color: #0f172a !important;
        }

        /* Top Header */
        .sky-header {
            background: linear-gradient(135deg, #0284c7 0%, #0369a1 50%, #075985 100%);
            color: #ffffff;
            border-radius: 16px;
            padding: 16px 24px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 10px 25px rgba(2, 132, 199, 0.25);
        }

        /* Tab Navigation Bar - Super high contrast */
        .stTabs [data-baseweb="tab-list"] {
            background-color: rgba(255, 255, 255, 0.8) !important;
            border-radius: 12px !important;
            padding: 6px !important;
            border: 1px solid #bae6fd !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
        }
        
        .stTabs [data-baseweb="tab"] {
            color: #0369a1 !important;
            font-weight: 700 !important;
            font-size: 14px !important;
            border-radius: 8px !important;
            padding: 8px 18px !important;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #0284c7 !important;
            color: #ffffff !important;
            box-shadow: 0 2px 8px rgba(2, 132, 199, 0.35) !important;
        }

        /* Boarding Pass Hero Container */
        .pass-container {
            background: #ffffff;
            border: 2px solid #bae6fd;
            border-radius: 18px;
            padding: 22px;
            margin-bottom: 20px;
            box-shadow: 0 12px 30px rgba(2, 132, 199, 0.12);
        }

        /* Text colors */
        .text-dark-main { color: #0f172a !important; }
        .text-muted-main { color: #475569 !important; }

        /* Buttons */
        .stButton>button {
            border-radius: 10px !important;
            font-weight: 700 !important;
            border: 1px solid #bae6fd !important;
            box-shadow: 0 2px 6px rgba(0,0,0,0.06) !important;
        }

        /* Selectbox */
        .stSelectbox div[data-baseweb="select"] {
            background-color: #ffffff !important;
            border-radius: 10px !important;
            border: 1px solid #7dd3fc !important;
            color: #0f172a !important;
            font-weight: 600 !important;
        }

        /* Policy & Service Cards */
        .card-box {
            background: #ffffff;
            border: 1px solid #e0f2fe;
            border-radius: 14px;
            padding: 18px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.04);
            margin-bottom: 14px;
        }
    </style>
    """, unsafe_allow_html=True)
else:
    # 🌙 Starry Night Theme (Aviation Midnight)
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@600;700&display=swap');
        
        * {
            font-family: 'Plus Jakarta Sans', -apple-system, sans-serif !important;
        }

        .stApp {
            background: radial-gradient(circle at 10% 20%, #0f172a 0%, #030712 100%) !important;
            color: #f8fafc !important;
        }

        .sky-header {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0369a1 100%);
            color: #ffffff;
            border-radius: 16px;
            padding: 16px 24px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        }

        /* Tab Navigation Bar */
        .stTabs [data-baseweb="tab-list"] {
            background-color: #1e293b !important;
            border-radius: 12px !important;
            padding: 6px !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
        }
        
        .stTabs [data-baseweb="tab"] {
            color: #94a3b8 !important;
            font-weight: 700 !important;
            font-size: 14px !important;
            border-radius: 8px !important;
            padding: 8px 18px !important;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #0284c7 !important;
            color: #ffffff !important;
            box-shadow: 0 2px 10px rgba(2, 132, 199, 0.4) !important;
        }

        .pass-container {
            background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 18px;
            padding: 22px;
            margin-bottom: 20px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.6);
        }

        .text-dark-main { color: #f8fafc !important; }
        .text-muted-main { color: #94a3b8 !important; }

        .stButton>button {
            border-radius: 10px !important;
            font-weight: 700 !important;
            background-color: #1e293b !important;
            color: #f8fafc !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
        }

        .stSelectbox div[data-baseweb="select"] {
            background-color: #1e293b !important;
            border-radius: 10px !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            color: #f8fafc !important;
            font-weight: 600 !important;
        }

        .card-box {
            background: #1e293b;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 14px;
            padding: 18px;
            margin-bottom: 14px;
        }
    </style>
    """, unsafe_allow_html=True)


# ── General Clean UI Elements ──────────────────────────────────────────────────
st.markdown("""
<style>
    header {visibility: hidden;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}

    /* Flight Vector Display */
    .route-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 14px 0;
        padding: 12px 0;
        border-top: 1px dashed rgba(125, 211, 252, 0.4);
        border-bottom: 1px dashed rgba(125, 211, 252, 0.4);
    }
    
    .city-label {
        font-size: 26px;
        font-weight: 800;
        letter-spacing: -0.5px;
    }

    .status-badge {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    
    .status-red { background: #fee2e2; color: #b91c1c; border: 1px solid #f87171; }
    .status-amber { background: #fef3c7; color: #b45309; border: 1px solid #fbbf24; }
    .status-green { background: #dcfce7; color: #15803d; border: 1px solid #4ade80; }

    .tier-tag {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 800;
        text-transform: uppercase;
    }
    .tier-gold-c { background: #fef3c7; color: #b45309; border: 1px solid #fde68a; }
    .tier-platinum-c { background: #f3e8ff; color: #7e22ce; border: 1px solid #e9d5ff; }
    .tier-silver-c { background: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; }

    .action-pill {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 700;
        margin: 2px 4px 2px 0;
    }
    .pill-rebook { background: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; }
    .pill-refund { background: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }
    .pill-voucher { background: #fef3c7; color: #b45309; border: 1px solid #fde68a; }
    .pill-lounge { background: #f3e8ff; color: #7e22ce; border: 1px solid #e9d5ff; }
    .pill-hotel { background: #ffe4e6; color: #be123c; border: 1px solid #fecdd3; }
    .pill-escalate { background: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; }
    .pill-decline { background: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; }
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


# ── Chip Formatter ─────────────────────────────────────────────────────────────
def render_pill(action_type: str) -> str:
    badges = {
        "rebook": ("✈️ Priority Rebooking Authorized", "pill-rebook"),
        "refund": ("💰 Full Refund Authorized (7 Days)", "pill-refund"),
        "meal_voucher": ("🍽️ Dining Voucher Issued", "pill-voucher"),
        "lounge_access": ("🛋️ Executive Lounge Pass Issued", "pill-lounge"),
        "hotel_accommodation": ("🏨 Transit Accommodation Arranged", "pill-hotel"),
        "escalate_to_supervisor": ("🚨 Escalated to Duty Supervisor", "pill-escalate"),
        "decline_request": ("⛔ Exceeds Airline Policy (Declined)", "pill-decline"),
        "provide_info": ("ℹ️ Flight Telemetry Provided", "pill-rebook"),
    }
    label, css = badges.get(action_type, ("🔹 Action Confirmed", "pill-rebook"))
    return f'<span class="action-pill {css}">{label}</span>'


# ── Sky Header ─────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="sky-header">
    <div style="display: flex; align-items: center; gap: 12px;">
        <div style="font-size: 28px;">✈️</div>
        <div>
            <div style="font-size: 22px; font-weight: 800; letter-spacing: -0.5px;">SkyWay Airlines</div>
            <div style="font-size: 11px; opacity: 0.9; font-weight: 600; letter-spacing: 1px; text-transform: uppercase;">
                Customer Self-Service & Disruption Care Portal
            </div>
        </div>
    </div>
    <div style="background: rgba(255, 255, 255, 0.2); padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 700;">
        📅 Flight Operations Date: {EXERCISE_DATE}
    </div>
</div>
""", unsafe_allow_html=True)


# ── Top Control Bar (Passenger Selector + Day/Night Toggle + Reset) ─────────────
customers = st.session_state.customer_repo.get_all()
cust_map = {f"{c.name} (PNR: {c.booking_reference} • {c.loyalty_tier.value} Tier)": c.name for c in customers}
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
    tier_css = {"Platinum": "tier-platinum-c", "Gold": "tier-gold-c", "Silver": "tier-silver-c"}.get(tier_val, "tier-silver-c")
    active_booking = orchestrator._get_active_booking()

    cities = active_booking.route.split("→") if active_booking else ["Delhi", "Goa"]
    origin_city = cities[0].strip() if len(cities) > 0 else "Delhi"
    dest_city = cities[1].strip() if len(cities) > 1 else "Goa"

    status_pill_class = "status-green"
    status_label = "ON TIME"
    if active_booking:
        if active_booking.status == BookingStatus.CANCELLED:
            status_pill_class = "status-red"
            status_label = "CANCELLED (OPERATIONAL)"
        elif active_booking.status == BookingStatus.DELAYED:
            status_pill_class = "status-amber"
            status_label = f"DELAYED {active_booking.delay_hours}H (EST: {active_booking.new_departure})"

    # ── Boarding Pass Hero Card (Clean Multi-Column Native Structure) ───────────
    st.markdown(f"""
    <div class="pass-container">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
            <div>
                <span style="font-size: 20px; font-weight: 800;" class="text-dark-main">{active_cust.name}</span>
                &nbsp; <span class="tier-tag {tier_css}">{tier_val} MEMBER</span>
                <div style="font-size: 12px; margin-top: 2px;" class="text-muted-main">
                    PNR: <strong style="color: #0284c7;">{active_cust.booking_reference}</strong> • Contact: {active_cust.contact.email}
                </div>
            </div>
            <div>
                <span class="status-badge {status_pill_class}">● {status_label}</span>
            </div>
        </div>

        <div class="route-bar">
            <div style="text-align: left;">
                <div class="city-label text-dark-main">{origin_city.upper()[:3]}</div>
                <div style="font-size: 13px;" class="text-muted-main">{origin_city}</div>
            </div>
            <div style="text-align: center; flex-grow: 1; padding: 0 20px;">
                <div style="font-size: 13px; font-weight: 700; color: #0284c7;">
                    Flight {active_booking.flight if active_booking else 'SK-204'}
                </div>
                <div style="color: #0284c7; font-size: 16px; margin: 2px 0;">✈ ────────── ➔</div>
                <div style="font-size: 11px;" class="text-muted-main">
                    Sch: {active_booking.scheduled_departure if active_booking else '18:40'}
                    {f" • <strong style='color:#b45309;'>Rescheduled: {active_booking.new_departure}</strong>" if active_booking.delay_hours else ""}
                </div>
            </div>
            <div style="text-align: right;">
                <div class="city-label text-dark-main">{dest_city.upper()[:3]}</div>
                <div style="font-size: 13px;" class="text-muted-main">{dest_city}</div>
            </div>
        </div>

        <div style="display: flex; justify-content: space-between; font-size: 12px; flex-wrap: wrap; gap: 8px;" class="text-muted-main">
            <div>✈ Annual Flights: <strong>{active_cust.travel_history.flights_last_12_months} (Last 12M)</strong></div>
            <div>📋 Service Complaints: <strong>{active_cust.travel_history.prior_complaints}</strong></div>
            <div>ℹ️ Details: <strong>{active_cust.travel_history.complaint_details or 'None'}</strong></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


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
            st.markdown("""
            <div class="card-box">
                <strong style="color: #b91c1c;">Flight SK-204 (DEL → GOI)</strong><br/>
                • <strong>Status:</strong> Cancelled (Operational)<br/>
                • <strong>Passenger:</strong> Priya Nair (Gold)<br/>
                • <strong>Policy:</strong> Free Rebooking (24h) OR Full Refund (7 Days)
            </div>
            """, unsafe_allow_html=True)
        with sc2:
            st.markdown("""
            <div class="card-box">
                <strong style="color: #b45309;">Flight SK-118 (BOM → BLR)</strong><br/>
                • <strong>Status:</strong> Delayed 4 Hours (11:10)<br/>
                • <strong>Passenger:</strong> Arvind Kulkarni (Silver)<br/>
                • <strong>Policy:</strong> Meal Voucher + Lounge Access
            </div>
            """, unsafe_allow_html=True)
        with sc3:
            st.markdown("""
            <div class="card-box">
                <strong style="color: #7e22ce;">Flight SK-305 (DEL → HYD)</strong><br/>
                • <strong>Status:</strong> Delayed 6 Hours (20:00)<br/>
                • <strong>Passenger:</strong> Meher Kaur (Platinum)<br/>
                • <strong>Policy:</strong> Meal + Lounge + Transit Hotel + Supervisor Review
            </div>
            """, unsafe_allow_html=True)
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
                    chips_html = "".join([render_pill(a) for a in msg["actions"]])
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
            if st.button("💰 Request Full Refund", key="btn_p_ref", use_container_width=True):
                st.session_state.pending_prompt = "I would like to request a full refund for my flight."
                st.rerun()
        with q2:
            if st.button("✈️ Request Priority Rebook", key="btn_p_reb", use_container_width=True):
                st.session_state.pending_prompt = "Please rebook me on the next available flight."
                st.rerun()
        with q3:
            if st.button("🍽️ Claim Meal & Lounge", key="btn_p_vou", use_container_width=True):
                st.session_state.pending_prompt = "What meal vouchers and lounge access am I entitled to?"
                st.rerun()
        with q4:
            if st.button("🏨 Inquire Transit Hotel", key="btn_p_hot", use_container_width=True):
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
        st.markdown("""
        <div class="card-box">
            <h4 style="color: #0284c7; margin: 0 0 8px 0;">1. Cancellation Rebooking Policy</h4>
            <p style="font-size: 13px; line-height: 1.5;" class="text-muted-main">
                When a flight is cancelled by SkyWay Airlines for operational reasons, passengers are entitled to choose between:
                <br/>• <strong>Free Rebooking</strong> on the next available flight within 24 hours (with priority seating for Gold/Platinum members).
                <br/>• <strong>Full Refund</strong> issued to the original payment method within 7 business days.
            </p>
        </div>

        <div class="card-box">
            <h4 style="color: #d97706; margin: 0 0 8px 0;">2. Delay Care & Entitlements Tiers</h4>
            <p style="font-size: 13px; line-height: 1.5;" class="text-muted-main">
                • <strong>Under 3 Hours Delay:</strong> ₹500 Dining Voucher.<br/>
                • <strong>3 to 5 Hours Delay:</strong> Meal Voucher + Executive Departure Lounge Access.<br/>
                • <strong>Over 5 Hours Delay:</strong> Meal Voucher + Lounge Access + Hotel Accommodation covering the delayed-hours duration only (not a full night's stay).
            </p>
        </div>
        """, unsafe_allow_html=True)

    with r2:
        st.markdown("""
        <div class="card-box">
            <h4 style="color: #10b981; margin: 0 0 8px 0;">3. Fare Difference & Rebooking Authority</h4>
            <p style="font-size: 13px; line-height: 1.5;" class="text-muted-main">
                When passengers voluntarily choose alternative higher-fare flights:
                <br/>• <strong>Up to ₹1,500 difference:</strong> Front-line agent has direct waiver authority.
                <br/>• <strong>Above ₹1,500 difference:</strong> Mandatory escalation to Duty Supervisor.
            </p>
        </div>

        <div class="card-box">
            <h4 style="color: #a855f7; margin: 0 0 8px 0;">4. Loyalty Tier Benefits</h4>
            <p style="font-size: 13px; line-height: 1.5;" class="text-muted-main">
                • <strong>Gold & Platinum Members:</strong> Receive first-priority rebooking on replacement flights.
                <br/>• <em>Note:</em> Loyalty status does not authorize complimentary cabin upgrades or compensation beyond standard policy.
            </p>
        </div>
        """, unsafe_allow_html=True)


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
