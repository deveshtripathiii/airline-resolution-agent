"""SkyWay Airlines Disruption Resolution Portal.

Features:
- Instant 1-tap passenger switcher (Zero dropdown popover glitches)
- Multi-Language Support (English ⇄ हिन्दी) with grounded policy translations
- Official Disruption Claim Slip & Tax Invoice PDF generator
- Flawless Night Mode & Day Mode with 100% text contrast
- 100% Mobile & Desktop Responsive (Zero horizontal scroll/overflow)
- Grounded multi-turn conversational agent
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
import importlib
import src.ui.translations as trans_mod
importlib.reload(trans_mod)
from src.ui.translations import TRANSLATIONS
from src.utils.pdf_generator import generate_claim_slip_pdf


# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SkyWay Airlines | Disruption Care Portal",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ── Theme & Language Management ────────────────────────────────────────────────
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "sky_light"

if "language" not in st.session_state:
    st.session_state.language = "en"

is_dark = st.session_state.theme_mode == "night_dark"
lang = st.session_state.language
t = TRANSLATIONS.get(lang, TRANSLATIONS['en'])


# ── Dynamic High-Contrast & Zero-Overflow CSS ──────────────────────────────────
if not is_dark:
    # ⛅ SKY DAY THEME
    st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

* {
    font-family: 'Plus Jakarta Sans', -apple-system, 'Segoe UI Emoji', 'Segoe UI Symbol', 'Noto Color Emoji', sans-serif !important;
    box-sizing: border-box !important;
}

html, body, [data-testid="stAppViewContainer"], .main, .block-container, [data-testid="stVerticalBlock"] {
    max-width: 100vw !important;
    overflow-x: hidden !important;
    box-sizing: border-box !important;
}

.block-container {
    padding: 0.75rem 0.6rem 2rem 0.6rem !important;
    max-width: 920px !important;
    margin: 0 auto !important;
}

header {visibility: hidden;}
footer {visibility: hidden;}
#MainMenu {visibility: hidden;}

.stApp {
    background: linear-gradient(180deg, #dbeafe 0%, #e0f2fe 25%, #f0f9ff 60%, #ffffff 100%) !important;
    color: #0f172a !important;
}

[data-testid="stHorizontalBlock"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    gap: 4px !important;
}
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
    min-width: 0 !important;
}

.stButton > button {
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-size: 11.5px !important;
    padding: 2px 6px !important;
    min-height: 30px !important;
    height: 30px !important;
    line-height: 1.1 !important;
    white-space: nowrap !important;
    border: 1px solid #7dd3fc !important;
    background-color: #ffffff !important;
    color: #0369a1 !important;
}
.stButton > button:hover {
    background-color: #f0f9ff !important;
    border-color: #0284c7 !important;
    color: #0284c7 !important;
}

.stTabs {
    width: 100% !important;
    max-width: 100% !important;
    overflow-x: hidden !important;
}
.stTabs [data-baseweb="tab-list"] {
    display: flex !important;
    width: 100% !important;
    gap: 4px !important;
    padding: 4px !important;
    border-radius: 10px !important;
    background-color: #ffffff !important;
    border: 2px solid #bae6fd !important;
    box-shadow: 0 2px 8px rgba(2, 132, 199, 0.08) !important;
}
.stTabs [data-baseweb="tab"] {
    flex: 1 1 0px !important;
    min-width: 0 !important;
    padding: 8px 4px !important;
    font-size: 12px !important;
    font-weight: 700 !important;
    text-align: center !important;
    justify-content: center !important;
    border-radius: 6px !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    color: #0369a1 !important;
}
.stTabs [aria-selected="true"] {
    background-color: #0284c7 !important;
    color: #ffffff !important;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #ffffff !important;
    border: 2px solid #bae6fd !important;
    border-radius: 14px !important;
    box-shadow: 0 4px 12px rgba(2, 132, 199, 0.06) !important;
    padding: 0.5rem !important;
}

p, span, div, h1, h2, h3, h4, label {
    color: #0f172a !important;
}
.stCaption, .stCaption p {
    color: #475569 !important;
    font-weight: 500 !important;
}

.stDownloadButton>button {
    border-radius: 10px !important;
    font-weight: 800 !important;
    background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
    color: #ffffff !important;
    border: none !important;
    padding: 10px 18px !important;
    box-shadow: 0 4px 14px rgba(2, 132, 199, 0.3) !important;
}
.stDownloadButton>button * {
    color: #ffffff !important;
    font-weight: 800 !important;
}

div[data-testid="stRadio"], div[role="radiogroup"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    gap: 6px !important;
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    margin-top: 2px !important;
    margin-bottom: 8px !important;
}
div[role="radiogroup"] label {
    background: #ffffff !important;
    border: 1px solid #bae6fd !important;
    padding: 5px 8px !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-size: 11px !important;
    color: #0369a1 !important;
    flex: 1 1 0px !important;
    min-width: 0 !important;
    text-align: center !important;
    justify-content: center !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    box-shadow: 0 2px 5px rgba(2, 132, 199, 0.05) !important;
    margin: 0 !important;
}

[data-testid="stChatMessage"] {
    background-color: #ffffff !important;
    border: 1px solid #e0f2fe !important;
    border-radius: 12px !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.03) !important;
}

.action-chip {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 700;
    margin: 3px 3px 3px 0;
}
.chip-rebook { background: #e0f2fe; color: #0369a1 !important; border: 1px solid #bae6fd; }
.chip-refund { background: #dcfce7; color: #15803d !important; border: 1px solid #bbf7d0; }
.chip-meal { background: #fef3c7; color: #b45309 !important; border: 1px solid #fde68a; }
.chip-lounge { background: #f3e8ff; color: #7e22ce !important; border: 1px solid #e9d5ff; }
.chip-hotel { background: #ffe4e6; color: #be123c !important; border: 1px solid #fecdd3; }
.chip-escalate { background: #fee2e2; color: #b91c1c !important; border: 1px solid #fca5a5; }
.chip-decline { background: #f1f5f9; color: #475569 !important; border: 1px solid #cbd5e1; }
</style>""", unsafe_allow_html=True)
else:
    # 🌙 STARRY NIGHT THEME
    st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

* {
    font-family: 'Plus Jakarta Sans', -apple-system, 'Segoe UI Emoji', 'Segoe UI Symbol', 'Noto Color Emoji', sans-serif !important;
    box-sizing: border-box !important;
}

html, body, [data-testid="stAppViewContainer"], .main, .block-container, [data-testid="stVerticalBlock"] {
    max-width: 100vw !important;
    overflow-x: hidden !important;
    box-sizing: border-box !important;
}

.block-container {
    padding: 0.75rem 0.6rem 2rem 0.6rem !important;
    max-width: 920px !important;
    margin: 0 auto !important;
}

header {visibility: hidden;}
footer {visibility: hidden;}
#MainMenu {visibility: hidden;}

.stApp {
    background: radial-gradient(circle at 10% 20%, #0f172a 0%, #030712 100%) !important;
    color: #f8fafc !important;
}

[data-testid="stHorizontalBlock"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    gap: 4px !important;
}
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
    min-width: 0 !important;
}

.stButton > button {
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-size: 11.5px !important;
    padding: 2px 6px !important;
    min-height: 30px !important;
    height: 30px !important;
    line-height: 1.1 !important;
    white-space: nowrap !important;
    background-color: #1e293b !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    color: #38bdf8 !important;
}
.stButton > button:hover {
    background-color: #0284c7 !important;
    border-color: #38bdf8 !important;
    color: #ffffff !important;
}

.stTabs {
    width: 100% !important;
    max-width: 100% !important;
    overflow-x: hidden !important;
}
.stTabs [data-baseweb="tab-list"] {
    display: flex !important;
    width: 100% !important;
    gap: 4px !important;
    padding: 4px !important;
    border-radius: 10px !important;
    background-color: #1e293b !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
}
.stTabs [data-baseweb="tab"] {
    flex: 1 1 0px !important;
    min-width: 0 !important;
    padding: 8px 4px !important;
    font-size: 12px !important;
    font-weight: 700 !important;
    text-align: center !important;
    justify-content: center !important;
    border-radius: 6px !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    color: #94a3b8 !important;
}
.stTabs [aria-selected="true"] {
    background-color: #0284c7 !important;
    color: #ffffff !important;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #1e293b !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    border-radius: 14px !important;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4) !important;
    padding: 0.5rem !important;
}

p, span, div, h1, h2, h3, h4, h5, h6, label, strong, b, li {
    color: #f8fafc !important;
}
.stCaption, .stCaption p {
    color: #94a3b8 !important;
    font-weight: 500 !important;
}

.stDownloadButton>button {
    border-radius: 10px !important;
    font-weight: 800 !important;
    background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    padding: 10px 18px !important;
}
.stDownloadButton>button * {
    color: #ffffff !important;
    font-weight: 800 !important;
}

div[data-testid="stRadio"], div[role="radiogroup"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    gap: 6px !important;
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    margin-top: 2px !important;
    margin-bottom: 8px !important;
}
div[role="radiogroup"] label {
    background: #1e293b !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    padding: 5px 8px !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-size: 11px !important;
    color: #f8fafc !important;
    flex: 1 1 0px !important;
    min-width: 0 !important;
    text-align: center !important;
    justify-content: center !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2) !important;
    margin: 0 !important;
}

[data-testid="stChatMessage"] {
    background-color: #1e293b !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 12px !important;
    color: #f8fafc !important;
}

hr {
    border-color: rgba(255, 255, 255, 0.15) !important;
}

.action-chip {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 700;
    margin: 3px 3px 3px 0;
}
.chip-rebook { background: #e0f2fe; color: #0369a1 !important; border: 1px solid #bae6fd; }
.chip-refund { background: #dcfce7; color: #15803d !important; border: 1px solid #bbf7d0; }
.chip-meal { background: #fef3c7; color: #b45309 !important; border: 1px solid #fde68a; }
.chip-lounge { background: #f3e8ff; color: #7e22ce !important; border: 1px solid #e9d5ff; }
.chip-hotel { background: #ffe4e6; color: #be123c !important; border: 1px solid #fecdd3; }
.chip-escalate { background: #fee2e2; color: #b91c1c !important; border: 1px solid #fca5a5; }
.chip-decline { background: #f1f5f9; color: #475569 !important; border: 1px solid #cbd5e1; }
</style>""", unsafe_allow_html=True)


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
        st.session_state.selected_customer = "Priya Nair"
        st.session_state.orchestrator.set_customer("Priya Nair")

    return st.session_state.orchestrator


orchestrator = get_orchestrator()
if not orchestrator.current_customer and st.session_state.selected_customer:
    orchestrator.set_customer(st.session_state.selected_customer)


# ── Chip Renderer ──────────────────────────────────────────────────────────────
def render_chip(action_type: str, language: str = "en") -> str:
    if language == "hi":
        badges = {
            "rebook": ("✈️ प्राथमिकता रीबुकिंग स्वीकृत", "chip-rebook"),
            "refund": ("💰 पूर्ण धनवापसी (7 दिन)", "chip-refund"),
            "meal_voucher": ("🍽️ भोजन वाउचर जारी", "chip-meal"),
            "lounge_access": ("🛋️ एग्जीक्यूटिव लाउंज पास", "chip-lounge"),
            "hotel_accommodation": ("🏨 ट्रांजिट आवास स्वीकृत", "chip-hotel"),
            "escalate_to_supervisor": ("🚨 ड्यूटी सुपरवाइजर को अग्रेषित", "chip-escalate"),
            "decline_request": ("⛔ नीति से परे (अस्वीकृत)", "chip-decline"),
            "provide_info": ("ℹ️ उड़ान सूचना प्रेषित", "chip-rebook"),
        }
    else:
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


# ── Top Unified Toolbar (Header + 3 Micro-Toggles in ONE neat row) ────────────
top_brand, top_lang, top_theme, top_reset = st.columns([2.2, 0.9, 0.9, 0.8])

with top_brand:
    title_color = "#0369a1" if not is_dark else "#38bdf8"
    sub_color = "#64748b" if not is_dark else "#94a3b8"
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 8px; padding-top: 2px;">
        <span style="font-size: 22px;">✈️</span>
        <div>
            <div style="font-size: 15px; font-weight: 800; color: {title_color}; line-height: 1.1;">SkyWay Care</div>
            <div style="font-size: 9px; color: {sub_color}; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">23 Sep 2026 • Ops Portal</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with top_lang:
    lang_btn_text = "🌐 हिन्दी" if lang == "en" else "🌐 Eng"
    if st.button(lang_btn_text, use_container_width=True):
        st.session_state.language = "hi" if lang == "en" else "en"
        st.session_state.messages = []
        st.rerun()

with top_theme:
    theme_label = "🌙 Night" if not is_dark else "☀️ Day"
    if st.button(theme_label, use_container_width=True):
        st.session_state.theme_mode = "night_dark" if not is_dark else "sky_light"
        st.rerun()

with top_reset:
    if st.button("🔄 Reset", use_container_width=True):
        st.session_state.messages = []
        if st.session_state.selected_customer:
            orchestrator.set_customer(st.session_state.selected_customer)
        st.rerun()


# ── 1-Tap Passenger Itinerary Switcher (Compact Segmented Chips) ───────────────
customers = st.session_state.customer_repo.get_all()
tier_icons = {"Gold": "🏆", "Silver": "🥈", "Platinum": "👑"}
cust_map = {
    f"👤 {c.name} ({tier_icons.get(c.loyalty_tier.value, '')} {c.loyalty_tier.value} • {c.booking_reference})": c.name 
    for c in customers
}
radio_options = list(cust_map.keys())

current_idx = 0
if st.session_state.selected_customer:
    for i, (label_key, name) in enumerate(cust_map.items()):
        if name == st.session_state.selected_customer:
            current_idx = i
            break

selected_label = st.radio(
    "Select Passenger Itinerary:",
    options=radio_options,
    index=current_idx,
    horizontal=True,
    label_visibility="collapsed",
)

chosen_name = cust_map[selected_label]
if (
    not orchestrator.current_customer
    or chosen_name != st.session_state.selected_customer
    or orchestrator.current_customer.name != chosen_name
):
    st.session_state.selected_customer = chosen_name
    orchestrator.set_customer(chosen_name)
    st.session_state.messages = []
    st.rerun()


active_cust = orchestrator.current_customer

if active_cust:
    active_booking = orchestrator._get_active_booking()

    cities = active_booking.route.split("→") if active_booking else ["Delhi", "Goa"]
    origin_city = cities[0].strip() if len(cities) > 0 else "Delhi"
    dest_city = cities[1].strip() if len(cities) > 1 else "Goa"

    # Status Badge Styling
    if active_booking:
        if active_booking.status == BookingStatus.CANCELLED:
            status_html = f"<span style='background:#fee2e2; color:#b91c1c; padding:4px 10px; border-radius:6px; font-weight:800; font-size:11px; border:1px solid #fca5a5;'>● {t['status_cancelled']}</span>"
        elif active_booking.status == BookingStatus.DELAYED:
            status_text = t['status_delayed'].format(hours=active_booking.delay_hours, est=active_booking.new_departure)
            status_html = f"<span style='background:#fef3c7; color:#b45309; padding:4px 10px; border-radius:6px; font-weight:800; font-size:11px; border:1px solid #fde68a;'>● {status_text}</span>"
        else:
            status_html = f"<span style='background:#dcfce7; color:#15803d; padding:4px 10px; border-radius:6px; font-weight:800; font-size:11px; border:1px solid #bbf7d0;'>● {t['status_ontime']}</span>"
    else:
        status_html = ""

    tier_badge = f"🏆 {active_cust.loyalty_tier.value} Tier" if active_cust.loyalty_tier.value == "Gold" else (
        f"👑 {active_cust.loyalty_tier.value} Tier" if active_cust.loyalty_tier.value == "Platinum" else f"🥈 {active_cust.loyalty_tier.value} Tier"
    )

    telemetry_bg = "background: rgba(2, 132, 199, 0.04); border: 1px solid #bae6fd;" if not is_dark else "background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.12);"
    stat_card_bg = "background: #f0f9ff; border: 1px solid #bae6fd;" if not is_dark else "background: #0f172a; border: 1px solid rgba(255, 255, 255, 0.12);"
    city_color = "#0284c7" if not is_dark else "#38bdf8"
    text_sub = "#64748b" if not is_dark else "#94a3b8"
    tier_bg = "#e0f2fe" if not is_dark else "#1e293b"
    tier_color = "#0369a1" if not is_dark else "#38bdf8"

    flight_num = active_booking.flight if active_booking else "SK-204"
    sched_str = f"Sch: <b>{active_booking.scheduled_departure}</b>" if active_booking else "Sch: 18:40"
    if active_booking and active_booking.delay_hours:
        sched_str += f" &nbsp;•&nbsp; <span style='color:#f59e0b; font-weight:700;'>New: {active_booking.new_departure}</span>"

    # ── Boarding Pass Card (Clean Zero-Overflow Container) ─────────────────────
    with st.container(border=True):
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px; margin-bottom: 8px;">
            <div>
                <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                    <span style="font-size: 17px; font-weight: 800; color: {city_color};">👤 {active_cust.name}</span>
                    <span style="font-size: 11px; background: {tier_bg}; color: {tier_color}; padding: 2px 8px; border-radius: 6px; font-weight: 700; border: 1px solid #bae6fd;">{tier_badge}</span>
                </div>
                <div style="font-size: 11px; color: {text_sub}; margin-top: 3px;">
                    {t['pnr_label']}: <b>{active_cust.booking_reference}</b> • {t['contact_label']}: {active_cust.contact.email}
                </div>
            </div>
            <div style="align-self: center;">
                {status_html}
            </div>
        </div>

        <div style="{telemetry_bg} border-radius: 10px; padding: 8px 12px; margin: 8px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center; text-align: center;">
                <div style="text-align: left; min-width: 50px;">
                    <div style="font-size: 22px; font-weight: 800; color: {city_color}; line-height: 1;">{origin_city.upper()[:3]}</div>
                    <div style="font-size: 10px; color: {text_sub}; font-weight: 600;">{origin_city}</div>
                </div>
                <div style="flex: 1; padding: 0 6px; text-align: center; min-width: 0;">
                    <div style="font-size: 12px; font-weight: 800; color: {city_color};">Flight {flight_num}</div>
                    <div style="display: flex; align-items: center; justify-content: center; gap: 4px; margin: 2px 0;">
                        <span style="font-size: 12px;">✈</span>
                        <div style="flex: 1; height: 2px; border-bottom: 2px dashed {city_color}; max-width: 110px;"></div>
                        <span style="font-size: 12px; font-weight: 800; color: {city_color};">➔</span>
                    </div>
                    <div style="font-size: 10px; color: {text_sub};">{sched_str}</div>
                </div>
                <div style="text-align: right; min-width: 50px;">
                    <div style="font-size: 22px; font-weight: 800; color: {city_color}; line-height: 1;">{dest_city.upper()[:3]}</div>
                    <div style="font-size: 10px; color: {text_sub}; font-weight: 600;">{dest_city}</div>
                </div>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 6px; width: 100%; box-sizing: border-box;">
            <div style="{stat_card_bg} border-radius: 8px; padding: 6px 4px; text-align: center; min-width: 0; overflow: hidden;">
                <div style="font-size: 9px; font-weight: 700; color: {text_sub}; text-transform: uppercase; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{t['flights_12m']}</div>
                <div style="font-size: 14px; font-weight: 800; color: {city_color};">{active_cust.travel_history.flights_last_12_months} (12M)</div>
            </div>
            <div style="{stat_card_bg} border-radius: 8px; padding: 6px 4px; text-align: center; min-width: 0; overflow: hidden;">
                <div style="font-size: 9px; font-weight: 700; color: {text_sub}; text-transform: uppercase; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{t['prior_complaints']}</div>
                <div style="font-size: 14px; font-weight: 800; color: {city_color};">{active_cust.travel_history.prior_complaints}</div>
            </div>
            <div style="{stat_card_bg} border-radius: 8px; padding: 6px 4px; text-align: center; min-width: 0; overflow: hidden;">
                <div style="font-size: 9px; font-weight: 700; color: {text_sub}; text-transform: uppercase; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{t['complaint_history']}</div>
                <div style="font-size: 11px; font-weight: 700; color: {city_color}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{active_cust.travel_history.complaint_details or 'None'}">{active_cust.travel_history.complaint_details or 'None'}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ── Main Tabbed Experience ─────────────────────────────────────────────────────
tab_chat, tab_policy, tab_records = st.tabs([
    t['tab_chat'],
    t['tab_policy'],
    t['tab_records'],
])


# ───────────────────────────────────────────────────────────────────────────────
# TAB 1: DISRUPTION RESOLUTION CHAT
# ───────────────────────────────────────────────────────────────────────────────
with tab_chat:
    if not active_cust:
        st.info("👈 Please select a passenger itinerary above.")
    else:
        # Welcome message (Language Aware)
        if not st.session_state.messages:
            if lang == "hi":
                if active_booking and active_booking.status == BookingStatus.CANCELLED:
                    welcome = (
                        f"नमस्ते **{active_cust.name}**। परिचालन कारणों से आपकी उड़ान **{active_booking.flight} ({active_booking.route})** "
                        f"के निरस्त होने पर हमें गहरा खेद है।\n\n"
                        f"स्काईवे एयरलाइंस नीति के तहत, हम 24 घंटे में **निःशुल्क प्राथमिकता रीबुकिंग** या आपके मूल खाते में "
                        f"**पूर्ण धनवापसी (Full Refund)** प्रदान कर सकते हैं। आप कौन सा विकल्प चुनना चाहेंगे?"
                    )
                elif active_booking and active_booking.status == BookingStatus.DELAYED:
                    welcome = (
                        f"नमस्ते **{active_cust.name}**। हमें सूचित करते हुए खेद है कि उड़ान **{active_booking.flight} ({active_booking.route})** "
                        f"**{active_booking.delay_hours} घंटे विलंबित** है (नया समय: **{active_booking.new_departure}**).\n\n"
                        f"मैंने आपका आरक्षण सत्यापित कर लिया है और आपके पात्र भोजन व लाउंज वाउचर जारी करने के लिए तैयार हूँ। मैं आपकी क्या सहायता कर सकता हूँ?"
                    )
                else:
                    welcome = f"नमस्ते {active_cust.name}, स्काईवे सहायता सेवा में आपका स्वागत है। मैं आपकी क्या सहायता कर सकता हूँ?"
            else:
                if active_booking and active_booking.status == BookingStatus.CANCELLED:
                    welcome = (
                        f"Hello **{active_cust.name}**. We sincerely apologize that flight **{active_booking.flight} ({active_booking.route})** "
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
                    st.error(t['supervisor_escalation_banner'])

                st.markdown(msg["content"])

                if msg.get("actions"):
                    chips_html = "".join([render_chip(a, language=lang) for a in msg["actions"]])
                    st.markdown(f"<div style='margin-top: 6px;'>{chips_html}</div>", unsafe_allow_html=True)

        # Quick Passenger Action Chips placed directly ABOVE the input box (2x2 grid for comfortable tap)
        st.markdown(f"<div style='margin-top: 14px; margin-bottom: 6px; font-size: 11px; font-weight: 700; color: #0284c7;'>{t['quick_actions_title']}</div>", unsafe_allow_html=True)
        q_row1_1, q_row1_2 = st.columns(2)
        with q_row1_1:
            if st.button(t['quick_refund'], key="b_ref_top", use_container_width=True):
                st.session_state.pending_prompt = "मुझे अपनी निरस्त उड़ान के लिए पूरा रिफंड चाहिए।" if lang == "hi" else "I would like to request a full refund for my flight."
                st.rerun()
        with q_row1_2:
            if st.button(t['quick_rebook'], key="b_reb_top", use_container_width=True):
                st.session_state.pending_prompt = "कृपया मुझे अगली उपलब्ध उड़ान पर रीबुक करें।" if lang == "hi" else "Please rebook me on the next available flight."
                st.rerun()

        q_row2_1, q_row2_2 = st.columns(2)
        with q_row2_1:
            if st.button(t['quick_vouchers'], key="b_vou_top", use_container_width=True):
                st.session_state.pending_prompt = "मेरी देरी के लिए भोजन वाउचर और लाउंज की क्या पात्रता है?" if lang == "hi" else "What meal vouchers and lounge access am I entitled to?"
                st.rerun()
        with q_row2_2:
            if st.button(t['quick_hotel'], key="b_hot_top", use_container_width=True):
                st.session_state.pending_prompt = "क्या आप मेरी देरी के लिए होटल आवास की व्यवस्था कर सकते हैं?" if lang == "hi" else "Can you arrange hotel accommodation for my delay?"
                st.rerun()

        # Chat Input Bar
        user_input = None
        if "pending_prompt" in st.session_state and st.session_state.pending_prompt:
            user_input = st.session_state.pending_prompt
            st.session_state.pending_prompt = None
        else:
            user_input = st.chat_input(t['chat_placeholder'])

        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})

            with st.spinner(t['evaluating']):
                resp = orchestrator.handle_message(user_input, language=lang)

            st.session_state.messages.append({
                "role": "assistant",
                "content": resp.message,
                "escalated": resp.escalated,
                "escalation_reason": resp.escalation_reason,
                "actions": [a.action_type.value for a in resp.actions_taken],
            })
            st.rerun()

        # ── Download Official Claim Slip PDF Section ───────────────────────────
        st.markdown("<div style='margin-top: 18px;'></div>", unsafe_allow_html=True)
        all_actions = [a.action_type.value for a in orchestrator.actions_taken]
        if not all_actions:
            all_actions = [a for m in st.session_state.messages for a in m.get("actions", [])]

        pdf_bytes = generate_claim_slip_pdf(
            customer_name=active_cust.name,
            pnr=active_cust.booking_reference,
            contact_email=active_cust.contact.email,
            contact_phone=active_cust.contact.phone,
            flight_number=active_booking.flight if active_booking else "SK-204",
            route=active_booking.route if active_booking else "Delhi → Goa",
            flight_status=active_booking.status.value if active_booking else "CANCELLED",
            delay_info=f"Delayed {active_booking.delay_hours}h (New departure: {active_booking.new_departure})" if active_booking and active_booking.delay_hours else "Operational Cancellation",
            actions_taken=all_actions,
            loyalty_tier=active_cust.loyalty_tier.value,
            exercise_date=EXERCISE_DATE,
        )

        st.download_button(
            label=t['download_claim_pdf'],
            data=pdf_bytes,
            file_name=f"SkyWay_Resolution_Slip_{active_cust.booking_reference}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )


# ───────────────────────────────────────────────────────────────────────────────
# TAB 2: POLICY DIRECTORY & 3 OFFICIAL BENCHMARK SCENARIOS (PDF SECTION 6)
# ───────────────────────────────────────────────────────────────────────────────
with tab_policy:
    st.markdown(f"### {t['sec6_title']}")
    st.caption(t['sec6_subtitle'])

    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        with st.container(border=True):
            st.markdown(f"#### 🏆 {t['scen1_title']}")
            st.markdown(t['scen1_body'])
    with sc2:
        with st.container(border=True):
            st.markdown(f"#### 🥈 {t['scen2_title']}")
            st.markdown(t['scen2_body'])
    with sc3:
        with st.container(border=True):
            st.markdown(f"#### 👑 {t['scen3_title']}")
            st.markdown(t['scen3_body'])

    st.divider()

    st.markdown(f"### 📜 {t['portal_title']} Service Policies")
    st.caption("Official grounded guidelines governing flight disruptions, passenger care, and financial limits.")

    r1, r2 = st.columns(2)
    with r1:
        with st.container(border=True):
            st.markdown(f"#### {t['policy_h1']}")
            st.markdown(t['policy_p1'])

        with st.container(border=True):
            st.markdown(f"#### {t['policy_h2']}")
            st.markdown(t['policy_p2'])

    with r2:
        with st.container(border=True):
            st.markdown(f"#### {t['policy_h3']}")
            st.markdown(t['policy_p3'])

        with st.container(border=True):
            st.markdown(f"#### {t['policy_h4']}")
            st.markdown(t['policy_p4'])


# ───────────────────────────────────────────────────────────────────────────────
# TAB 3: SERVICE ACTIVITY RECORD
# ───────────────────────────────────────────────────────────────────────────────
with tab_records:
    st.markdown(f"### 📁 {t['tab_records']}")
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
