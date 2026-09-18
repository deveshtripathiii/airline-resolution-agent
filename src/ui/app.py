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


# ── Dynamic Ultra-Luxury & High-Contrast CSS (Royal Saffron & Sunset Orange) ──
if not is_dark:
    # ⛅ ROYAL SAFFRON & SUNSET ORANGE DAY THEME
    st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

* {
    font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, sans-serif !important;
    box-sizing: border-box !important;
}

html, body, [data-testid="stAppViewContainer"], .main, .block-container, [data-testid="stVerticalBlock"] {
    max-width: 100vw !important;
    overflow-x: hidden !important;
    box-sizing: border-box !important;
}

.block-container {
    padding: 1rem 0.75rem 2.5rem 0.75rem !important;
    max-width: 940px !important;
    margin: 0 auto !important;
}

header {visibility: hidden;}
footer {visibility: hidden;}
#MainMenu {visibility: hidden;}

.stApp {
    background: radial-gradient(at 10% 0%, rgba(249, 115, 22, 0.05) 0px, transparent 50%),
                radial-gradient(at 90% 0%, rgba(245, 158, 11, 0.06) 0px, transparent 50%),
                #fafaf9 !important;
    color: #1c1917 !important;
}

[data-testid="stHorizontalBlock"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    gap: 6px !important;
    overflow: visible !important;
}
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
    min-width: 0 !important;
    overflow: visible !important;
}
.stMarkdown {
    overflow: visible !important;
}

/* Saffron & Orange Buttons */
.stButton > button {
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 12px !important;
    padding: 6px 12px !important;
    min-height: 36px !important;
    height: 36px !important;
    line-height: 1.2 !important;
    white-space: nowrap !important;
    border: 1px solid #e7e5e4 !important;
    background-color: #ffffff !important;
    color: #292524 !important;
    box-shadow: 0 1px 3px rgba(28, 25, 23, 0.04) !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
.stButton > button:hover {
    background-color: #fff7ed !important;
    border-color: #fdba74 !important;
    color: #ea580c !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 10px rgba(234, 88, 12, 0.12) !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #ea580c 0%, #c2410c 100%) !important;
    color: #ffffff !important;
    border: 1px solid #c2410c !important;
    box-shadow: 0 4px 14px rgba(234, 88, 12, 0.3) !important;
}
.stButton > button[kind="primary"] * {
    color: #ffffff !important;
    font-weight: 800 !important;
}

/* Saffron Modern Tabs */
.stTabs {
    width: 100% !important;
    max-width: 100% !important;
    overflow-x: hidden !important;
}
.stTabs [data-baseweb="tab-list"] {
    display: flex !important;
    width: 100% !important;
    gap: 6px !important;
    padding: 5px !important;
    border-radius: 12px !important;
    background-color: #f5f5f4 !important;
    border: 1px solid #e7e5e4 !important;
}
.stTabs [data-baseweb="tab"] {
    flex: 1 1 0px !important;
    min-width: 0 !important;
    padding: 8px 6px !important;
    font-size: 12px !important;
    font-weight: 700 !important;
    text-align: center !important;
    justify-content: center !important;
    border-radius: 8px !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    color: #78716c !important;
    transition: all 0.2s ease !important;
}
.stTabs [aria-selected="true"] {
    background: #ffffff !important;
    color: #ea580c !important;
    box-shadow: 0 2px 8px rgba(234, 88, 12, 0.12) !important;
    border-bottom: 2px solid #ea580c !important;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #ffffff !important;
    border: 1px solid #e7e5e4 !important;
    border-radius: 16px !important;
    box-shadow: 0 4px 20px -2px rgba(28, 25, 23, 0.05), 0 2px 6px -1px rgba(28, 25, 23, 0.02) !important;
    padding: 0.85rem !important;
}

p, span, div, h1, h2, h3, h4, label {
    color: #1c1917 !important;
}
.stCaption, .stCaption p {
    color: #78716c !important;
    font-weight: 500 !important;
}

/* Saffron Luxury Download Button */
.stDownloadButton>button {
    border-radius: 12px !important;
    font-weight: 800 !important;
    background: linear-gradient(135deg, #ea580c 0%, #c2410c 100%) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    padding: 12px 20px !important;
    box-shadow: 0 4px 16px rgba(234, 88, 12, 0.3) !important;
    transition: all 0.2s ease !important;
}
.stDownloadButton>button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(234, 88, 12, 0.4) !important;
}
.stDownloadButton>button * {
    color: #ffffff !important;
    font-weight: 800 !important;
}

/* Chat Message Styling */
[data-testid="stChatMessage"] {
    background-color: #ffffff !important;
    border: 1px solid #f5f5f4 !important;
    border-radius: 16px !important;
    box-shadow: 0 2px 10px rgba(28, 25, 23, 0.03) !important;
    padding: 16px 18px 20px 18px !important;
    margin-bottom: 14px !important;
    overflow: visible !important;
    word-break: break-word !important;
}

/* Chat Input Bar */
[data-testid="stBottom"], [data-testid="stBottomBlockContainer"] {
    background: transparent !important;
}
[data-testid="stChatInput"], .stChatInput {
    background-color: transparent !important;
}
[data-testid="stChatInput"] > div, .stChatInput > div {
    background-color: #ffffff !important;
    border: 1.5px solid #d6d3d1 !important;
    border-radius: 16px !important;
    box-shadow: 0 4px 18px rgba(28, 25, 23, 0.06) !important;
    transition: all 0.2s ease !important;
}
[data-testid="stChatInput"] > div:focus-within, .stChatInput > div:focus-within {
    border-color: #ea580c !important;
    box-shadow: 0 4px 20px rgba(234, 88, 12, 0.2) !important;
}
[data-testid="stChatInput"] textarea, .stChatInput textarea {
    background-color: #ffffff !important;
    color: #1c1917 !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    caret-color: #ea580c !important;
}
[data-testid="stChatInput"] textarea::placeholder, .stChatInput textarea::placeholder {
    color: #a8a29e !important;
    font-weight: 500 !important;
}
[data-testid="stChatInput"] button, .stChatInput button {
    color: #ea580c !important;
}

/* Saffron Action Chips */
.action-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 12px;
    border-radius: 8px;
    font-size: 11.5px;
    font-weight: 700;
    margin: 4px 4px 4px 0;
    letter-spacing: 0.2px;
}
.chip-rebook { background: #fff7ed; color: #c2410c !important; border: 1px solid #ffedd5; }
.chip-refund { background: #ecfdf5; color: #047857 !important; border: 1px solid #a7f3d0; }
.chip-meal { background: #fffbeb; color: #b45309 !important; border: 1px solid #fde68a; }
.chip-lounge { background: #faf5ff; color: #7e22ce !important; border: 1px solid #e9d5ff; }
.chip-hotel { background: #fff1f2; color: #be123c !important; border: 1px solid #fecdd3; }
.chip-escalate { background: #fef2f2; color: #b91c1c !important; border: 1px solid #fca5a5; }
.chip-decline { background: #f5f5f4; color: #57534e !important; border: 1px solid #e7e5e4; }
</style>""", unsafe_allow_html=True)
else:
    # 🌙 ROYAL SAFFRON MIDNIGHT THEME
    st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

* {
    font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, sans-serif !important;
    box-sizing: border-box !important;
}

html, body, [data-testid="stAppViewContainer"], .main, .block-container, [data-testid="stVerticalBlock"] {
    max-width: 100vw !important;
    overflow-x: hidden !important;
    box-sizing: border-box !important;
}

.block-container {
    padding: 1rem 0.75rem 2.5rem 0.75rem !important;
    max-width: 940px !important;
    margin: 0 auto !important;
}

header {visibility: hidden;}
footer {visibility: hidden;}
#MainMenu {visibility: hidden;}

.stApp {
    background: radial-gradient(at 0% 0%, rgba(249, 115, 22, 0.12) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(245, 158, 11, 0.08) 0px, transparent 50%),
                #0c0a09 !important;
    color: #fafaf9 !important;
}

[data-testid="stHorizontalBlock"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    gap: 6px !important;
    overflow: visible !important;
}
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
    min-width: 0 !important;
    overflow: visible !important;
}
.stMarkdown {
    overflow: visible !important;
}

/* Premium Dark Saffron Buttons */
.stButton > button {
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 12px !important;
    padding: 6px 12px !important;
    min-height: 36px !important;
    height: 36px !important;
    line-height: 1.2 !important;
    white-space: nowrap !important;
    background-color: #1c1917 !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    color: #fb923c !important;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3) !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    background-color: #292524 !important;
    border-color: #fb923c !important;
    color: #ffffff !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(249, 115, 22, 0.25) !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #ea580c 0%, #c2410c 100%) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    box-shadow: 0 4px 16px rgba(234, 88, 12, 0.4) !important;
}
.stButton > button[kind="primary"] * {
    color: #ffffff !important;
    font-weight: 800 !important;
}

/* Dark Saffron Tabs */
.stTabs {
    width: 100% !important;
    max-width: 100% !important;
    overflow-x: hidden !important;
}
.stTabs [data-baseweb="tab-list"] {
    display: flex !important;
    width: 100% !important;
    gap: 6px !important;
    padding: 5px !important;
    border-radius: 12px !important;
    background-color: #1c1917 !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
}
.stTabs [data-baseweb="tab"] {
    flex: 1 1 0px !important;
    min-width: 0 !important;
    padding: 8px 6px !important;
    font-size: 12px !important;
    font-weight: 700 !important;
    text-align: center !important;
    justify-content: center !important;
    border-radius: 8px !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    color: #a8a29e !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #ea580c 0%, #c2410c 100%) !important;
    color: #ffffff !important;
    box-shadow: 0 4px 12px rgba(234, 88, 12, 0.35) !important;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #171412 !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 16px !important;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5) !important;
    padding: 0.85rem !important;
}

p, span, div, h1, h2, h3, h4, h5, h6, label, strong, b, li {
    color: #fafaf9 !important;
}
.stCaption, .stCaption p {
    color: #a8a29e !important;
    font-weight: 500 !important;
}

.stDownloadButton>button {
    border-radius: 12px !important;
    font-weight: 800 !important;
    background: linear-gradient(135deg, #ea580c 0%, #c2410c 100%) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    padding: 12px 20px !important;
    box-shadow: 0 4px 16px rgba(234, 88, 12, 0.35) !important;
}
.stDownloadButton>button * {
    color: #ffffff !important;
    font-weight: 800 !important;
}

[data-testid="stChatMessage"] {
    background-color: #171412 !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 16px !important;
    color: #fafaf9 !important;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4) !important;
    padding: 16px 18px 20px 18px !important;
    margin-bottom: 14px !important;
    overflow: visible !important;
    word-break: break-word !important;
}

/* Chat Input Bar - Dark */
[data-testid="stBottom"], [data-testid="stBottomBlockContainer"] {
    background: transparent !important;
}
[data-testid="stChatInput"], .stChatInput {
    background-color: transparent !important;
}
[data-testid="stChatInput"] > div, .stChatInput > div {
    background-color: #1c1917 !important;
    border: 1.5px solid rgba(255, 255, 255, 0.15) !important;
    border-radius: 16px !important;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.5) !important;
}
[data-testid="stChatInput"] textarea, .stChatInput textarea {
    background-color: #1c1917 !important;
    color: #fafaf9 !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    caret-color: #fb923c !important;
}
[data-testid="stChatInput"] textarea::placeholder, .stChatInput textarea::placeholder {
    color: #a8a29e !important;
    font-weight: 500 !important;
}
[data-testid="stChatInput"] button, .stChatInput button {
    color: #fb923c !important;
}

hr {
    border-color: rgba(255, 255, 255, 0.1) !important;
}

.action-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 12px;
    border-radius: 8px;
    font-size: 11.5px;
    font-weight: 700;
    margin: 4px 4px 4px 0;
    letter-spacing: 0.2px;
}
.chip-rebook { background: rgba(234, 88, 12, 0.2); color: #fb923c !important; border: 1px solid rgba(249, 115, 22, 0.4); }
.chip-refund { background: rgba(5, 150, 105, 0.2); color: #34d399 !important; border: 1px solid rgba(16, 185, 129, 0.4); }
.chip-meal { background: rgba(217, 119, 6, 0.2); color: #fbbf24 !important; border: 1px solid rgba(245, 158, 11, 0.4); }
.chip-lounge { background: rgba(126, 34, 206, 0.2); color: #c084fc !important; border: 1px solid rgba(168, 85, 247, 0.4); }
.chip-hotel { background: rgba(190, 18, 60, 0.2); color: #fb7185 !important; border: 1px solid rgba(244, 63, 94, 0.4); }
.chip-escalate { background: rgba(185, 28, 28, 0.2); color: #f87171 !important; border: 1px solid rgba(239, 68, 68, 0.4); }
.chip-decline { background: rgba(87, 83, 78, 0.2); color: #d6d3d1 !important; border: 1px solid rgba(120, 113, 108, 0.4); }
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


# ── Top Unified Toolbar (Luxury Brand Header + 3 Micro-Toggles in ONE row) ───
top_brand, top_lang, top_theme, top_reset = st.columns([3.4, 0.95, 0.45, 0.45])

with top_brand:
    brand_title_color = "#1c1917" if not is_dark else "#fafaf9"
    brand_sub_color = "#ea580c" if not is_dark else "#fb923c"
    icon_bg = "linear-gradient(135deg, #ea580c 0%, #c2410c 100%)"
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 10px; overflow: visible; padding: 2px 0;">
        <div style="width: 36px; height: 36px; border-radius: 10px; background: {icon_bg}; display: flex; align-items: center; justify-content: center; color: #ffffff; font-size: 17px; box-shadow: 0 3px 10px rgba(234, 88, 12, 0.25); flex-shrink: 0;">✈️</div>
        <div style="overflow: visible; white-space: nowrap;">
            <div style="font-size: 15px; font-weight: 800; letter-spacing: -0.2px; color: {brand_title_color}; line-height: 1.2;">SKYWAY AIRLINES</div>
            <div style="font-size: 9.5px; font-weight: 700; color: {brand_sub_color}; text-transform: uppercase; letter-spacing: 0.5px; line-height: 1.2;">Executive Concierge • 23 Sep 2026</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with top_lang:
    lang_btn_text = "🌐 हिन्दी" if lang == "en" else "🌐 EN"
    if st.button(lang_btn_text, key="top_lang_btn", use_container_width=True):
        st.session_state.language = "hi" if lang == "en" else "en"
        st.session_state.messages = []
        st.rerun()

with top_theme:
    theme_icon = "🌙" if not is_dark else "☀️"
    if st.button(theme_icon, key="top_theme_btn", use_container_width=True):
        st.session_state.theme_mode = "night_dark" if not is_dark else "sky_light"
        st.rerun()

with top_reset:
    if st.button("🔄", key="top_reset_btn", use_container_width=True):
        st.session_state.messages = []
        if st.session_state.selected_customer:
            orchestrator.set_customer(st.session_state.selected_customer)
        st.rerun()


# ── VIP Passenger Itinerary Selector (1-Tap Segmented Switching) ──────────────
curr_cust = st.session_state.selected_customer or "Priya Nair"
c_p1, c_p2, c_p3 = st.columns(3)

with c_p1:
    is_p1 = (curr_cust == "Priya Nair")
    if st.button("🏆 Priya (Gold VIP)", key="nav_priya", type="primary" if is_p1 else "secondary", use_container_width=True):
        if not is_p1:
            st.session_state.selected_customer = "Priya Nair"
            orchestrator.set_customer("Priya Nair")
            st.session_state.messages = []
            st.session_state.pending_prompt = None
            st.rerun()

with c_p2:
    is_p2 = (curr_cust == "Arvind Kulkarni")
    if st.button("🥈 Arvind (Silver)", key="nav_arvind", type="primary" if is_p2 else "secondary", use_container_width=True):
        if not is_p2:
            st.session_state.selected_customer = "Arvind Kulkarni"
            orchestrator.set_customer("Arvind Kulkarni")
            st.session_state.messages = []
            st.session_state.pending_prompt = None
            st.rerun()

with c_p3:
    is_p3 = (curr_cust == "Meher Kaur")
    if st.button("👑 Meher (Plat Elite)", key="nav_meher", type="primary" if is_p3 else "secondary", use_container_width=True):
        if not is_p3:
            st.session_state.selected_customer = "Meher Kaur"
            orchestrator.set_customer("Meher Kaur")
            st.session_state.messages = []
            st.session_state.pending_prompt = None
            st.rerun()


active_cust = orchestrator.current_customer

if active_cust:
    active_booking = orchestrator._get_active_booking()

    cities = active_booking.route.split("→") if active_booking else ["Delhi", "Goa"]
    origin_city = cities[0].strip() if len(cities) > 0 else "Delhi"
    dest_city = cities[1].strip() if len(cities) > 1 else "Goa"

    # Luxury Status Badge
    if active_booking:
        if active_booking.status == BookingStatus.CANCELLED:
            status_html = f"<span style='background:#fef2f2; color:#dc2626; padding:4px 12px; border-radius:8px; font-weight:800; font-size:11px; border:1px solid #fecaca; box-shadow: 0 1px 3px rgba(220, 38, 38, 0.1);'>● {t['status_cancelled']}</span>"
        elif active_booking.status == BookingStatus.DELAYED:
            status_text = t['status_delayed'].format(hours=active_booking.delay_hours, est=active_booking.new_departure)
            status_html = f"<span style='background:#fff7ed; color:#ea580c; padding:4px 12px; border-radius:8px; font-weight:800; font-size:11px; border:1px solid #fed7aa; box-shadow: 0 1px 3px rgba(234, 88, 12, 0.1);'>● {status_text}</span>"
        else:
            status_html = f"<span style='background:#ecfdf5; color:#059669; padding:4px 12px; border-radius:8px; font-weight:800; font-size:11px; border:1px solid #a7f3d0; box-shadow: 0 1px 3px rgba(5, 150, 105, 0.1);'>● {t['status_ontime']}</span>"
    else:
        status_html = ""

    tier_badge = f"🏆 {active_cust.loyalty_tier.value} Medallion" if active_cust.loyalty_tier.value == "Gold" else (
        f"👑 {active_cust.loyalty_tier.value} Elite" if active_cust.loyalty_tier.value == "Platinum" else f"🥈 {active_cust.loyalty_tier.value} Member"
    )

    card_text_primary = "#1c1917" if not is_dark else "#fafaf9"
    card_text_muted = "#78716c" if not is_dark else "#a8a29e"
    accent_orange = "#ea580c" if not is_dark else "#fb923c"
    flight_box_bg = "background: linear-gradient(135deg, #fff7ed 0%, #fffbeb 100%); border: 1px solid #fed7aa;" if not is_dark else "background: rgba(249, 115, 22, 0.04); border: 1px solid rgba(249, 115, 22, 0.15);"
    telemetry_item_bg = "background: #ffffff; border: 1px solid #e7e5e4;" if not is_dark else "background: #1c1917; border: 1px solid rgba(255, 255, 255, 0.08);"

    flight_num = active_booking.flight if active_booking else "SK-204"
    sched_str = f"Sch: <b>{active_booking.scheduled_departure}</b>" if active_booking else "Sch: 18:40"
    if active_booking and active_booking.delay_hours:
        sched_str += f" &nbsp;•&nbsp; <span style='color:#ea580c; font-weight:700;'>Est: {active_booking.new_departure}</span>"

    # ── Luxury Digital Boarding Pass Container ─────────────────────────────────
    with st.container(border=True):
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px; margin-bottom: 10px;">
            <div>
                <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                    <span style="font-size: 17px; font-weight: 800; color: {card_text_primary}; letter-spacing: -0.2px;">👤 {active_cust.name}</span>
                    <span style="font-size: 11px; background: {'#fff7ed' if not is_dark else 'rgba(249, 115, 22, 0.15)'}; color: {'#c2410c' if not is_dark else '#fb923c'}; padding: 3px 9px; border-radius: 6px; font-weight: 700; border: 1px solid {'#fed7aa' if not is_dark else 'rgba(249, 115, 22, 0.3)'};">{tier_badge}</span>
                </div>
                <div style="font-size: 11px; color: {card_text_muted}; margin-top: 3px;">
                    {t['pnr_label']}: <span style="font-family: monospace; font-weight: 800; color: {accent_orange}; background: {'#fff7ed' if not is_dark else 'rgba(249, 115, 22, 0.15)'}; padding: 1px 6px; border-radius: 4px; border: 1px solid {'#fed7aa' if not is_dark else 'rgba(249, 115, 22, 0.3)'};">{active_cust.booking_reference}</span> • {t['contact_label']}: {active_cust.contact.email}
                </div>
            </div>
            <div style="align-self: center;">
                {status_html}
            </div>
        </div>

        <div style="{flight_box_bg} border-radius: 12px; padding: 10px 14px; margin: 10px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center; text-align: center;">
                <div style="text-align: left; min-width: 55px;">
                    <div style="font-size: 24px; font-weight: 800; color: {card_text_primary}; line-height: 1; letter-spacing: -0.5px;">{origin_city.upper()[:3]}</div>
                    <div style="font-size: 10.5px; color: {card_text_muted}; font-weight: 600; margin-top: 2px;">{origin_city}</div>
                </div>
                <div style="flex: 1; padding: 0 10px; text-align: center; min-width: 0;">
                    <div style="font-size: 12px; font-weight: 800; color: {accent_orange}; letter-spacing: 0.3px;">Flight {flight_num}</div>
                    <div style="display: flex; align-items: center; justify-content: center; gap: 6px; margin: 3px 0;">
                        <span style="font-size: 13px;">✈</span>
                        <div style="flex: 1; height: 2px; border-bottom: 2px dashed {'#fdba74' if not is_dark else 'rgba(249, 115, 22, 0.4)'}; max-width: 120px;"></div>
                        <span style="font-size: 12px; font-weight: 800; color: {accent_orange};">➔</span>
                    </div>
                    <div style="font-size: 10.5px; color: {card_text_muted};">{sched_str}</div>
                </div>
                <div style="text-align: right; min-width: 55px;">
                    <div style="font-size: 24px; font-weight: 800; color: {card_text_primary}; line-height: 1; letter-spacing: -0.5px;">{dest_city.upper()[:3]}</div>
                    <div style="font-size: 10.5px; color: {card_text_muted}; font-weight: 600; margin-top: 2px;">{dest_city}</div>
                </div>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; width: 100%; box-sizing: border-box;">
            <div style="{telemetry_item_bg} border-radius: 10px; padding: 7px 6px; text-align: center; min-width: 0; overflow: hidden; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);">
                <div style="font-size: 9px; font-weight: 700; color: {card_text_muted}; text-transform: uppercase; letter-spacing: 0.3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{t['flights_12m']}</div>
                <div style="font-size: 14px; font-weight: 800; color: {card_text_primary}; margin-top: 1px;">{active_cust.travel_history.flights_last_12_months} Flights</div>
            </div>
            <div style="{telemetry_item_bg} border-radius: 10px; padding: 7px 6px; text-align: center; min-width: 0; overflow: hidden; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);">
                <div style="font-size: 9px; font-weight: 700; color: {card_text_muted}; text-transform: uppercase; letter-spacing: 0.3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{t['prior_complaints']}</div>
                <div style="font-size: 14px; font-weight: 800; color: {card_text_primary}; margin-top: 1px;">{active_cust.travel_history.prior_complaints} Incidents</div>
            </div>
            <div style="{telemetry_item_bg} border-radius: 10px; padding: 7px 6px; text-align: center; min-width: 0; overflow: hidden; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);">
                <div style="font-size: 9px; font-weight: 700; color: {card_text_muted}; text-transform: uppercase; letter-spacing: 0.3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{t['complaint_history']}</div>
                <div style="font-size: 11.5px; font-weight: 700; color: {card_text_primary}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-top: 2px;" title="{active_cust.travel_history.complaint_details or 'Clean Record'}">{active_cust.travel_history.complaint_details or 'Clean Record'}</div>
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
                    st.markdown(f"<div style='margin-top: 10px; margin-bottom: 8px; display: flex; flex-wrap: wrap; gap: 6px; line-height: 1.4;'>{chips_html}</div>", unsafe_allow_html=True)

        # ── Dynamic Context-Aware Quick Replies (Adapts strictly to user's conversation progression) ───
        user_msgs = [m["content"].lower() for m in st.session_state.messages if m.get("role") == "user"]
        all_user_text = " ".join(user_msgs)
        is_escalated = any(m.get("escalated") for m in st.session_state.messages) or any(
            kw in all_user_text for kw in ["supervisor", "lawyer", "legal", "court", "complaint", "सुपरवाइजर", "वकील", "शिकायत", "कानूनी"]
        )

        if is_escalated:
            if lang == "hi":
                dynamic_opts = [
                    ("📞 ड्यूटी सुपरवाइजर से बात करें", "कृपया मुझे तुरंत ड्यूटी सुपरवाइजर से जोड़ें।"),
                    ("📄 आधिकारिक विवाद रिकॉर्ड मांगें", "मुझे इस मामले का आधिकारिक संदर्भ रिकॉर्ड चाहिए।"),
                    ("⚖️ एयरलाइन शिकायत नीति पूछें", "कृपया मुझे एयरलाइन की औपचारिक शिकायत नीति और अधिकार बताएं।"),
                    ("🔄 अन्य विकल्प जांचें", "क्या मेरी बुकिंग से जुड़ा कोई और विकल्प उपलब्ध है?")
                ]
            else:
                dynamic_opts = [
                    ("📞 Connect to Supervisor", "Please connect me with the Duty Supervisor immediately."),
                    ("📄 Request Dispute Record", "I would like an official reference record of this escalated dispute."),
                    ("⚖️ Complaint Procedures", "Please explain the formal airline complaint and dispute procedure."),
                    ("🔄 Check Other Options", "Is there any other available alternative for my itinerary?")
                ]
        elif active_booking and active_booking.status == BookingStatus.CANCELLED:
            user_wants_refund = any(kw in all_user_text for kw in ["refund", "रिफंड", "वापसी", "money back", "reimbursement"])
            user_wants_rebook = any(kw in all_user_text for kw in ["rebook", "रीबुक", "flight within", "next flight", "उड़ान", "next available", "24h", "24 घंटे", "tomorrow"])
            user_wants_upgrade = any(kw in all_user_text for kw in ["upgrade", "business class", "अपग्रेड", "बिजनेस"])

            if user_wants_refund and not user_wants_rebook:
                if lang == "hi":
                    dynamic_opts = [
                        ("📄 रिफंड खाते में कब आएगा?", "मेरा रिफंड किस माध्यम से और कितने दिनों में खाते में आएगा?"),
                        ("💼 चेक-इन सामान की स्थिति?", "मेरी निरस्त उड़ान के चेक-इन सामान की क्या स्थिति है?"),
                        ("📄 रिफंड रसीद डाउनलोड करें", "कृपया मुझे इस रिफंड समाधान की आधिकारिक रसीद प्रदान करें।"),
                        ("✈️ रीबुकिंग नियम पूछें", "यदि मैं रिफंड के बजाय रीबुकिंग चुनना चाहूँ तो क्या नियम हैं?")
                    ]
                else:
                    dynamic_opts = [
                        ("📄 When will refund reflect?", "How and within how many days will the refund reflect in my account?"),
                        ("💼 Checked baggage status?", "What is the status of my checked baggage for the cancelled flight?"),
                        ("📄 Request Refund Receipt", "Please provide me with an official confirmation receipt of this refund resolution."),
                        ("✈️ Ask Rebooking rules", "What are the rules if I prefer rebooking instead of a refund?")
                    ]
            elif user_wants_rebook:
                if lang == "hi":
                    dynamic_opts = [
                        ("🎫 नई उड़ान का समय व गेट?", "मेरी नई रीबुक की गई उड़ान का प्रस्थान समय और टर्मिनल क्या है?"),
                        ("🍽️ क्या भोजन वाउचर मिलेगा?", "रीबुकिंग के दौरान प्रतीक्षा के लिए क्या मुझे भोजन वाउचर मिलेगा?"),
                        ("💺 पसंदीदा सीट आवंटन मांगें", "क्या मुझे मेरी नई उड़ान में खिड़की या आगे की सीट मिल सकती है?"),
                        ("📄 रीबुकिंग पुष्टि डाउनलोड करें", "कृपया मुझे नई उड़ान का आधिकारिक पुष्टिकरण विवरण दें।")
                    ]
                else:
                    dynamic_opts = [
                        ("🎫 New Flight Schedule?", "What is the departure time and terminal for my newly rebooked flight?"),
                        ("🍽️ Meal voucher eligibility?", "Am I eligible for meal vouchers while waiting for my new flight?"),
                        ("💺 Preferred Seat Assignment?", "Can I get my preferred window or aisle seat on the new flight?"),
                        ("📄 Rebooking Confirmation", "Please give me the official confirmation details for the new flight.")
                    ]
            elif user_wants_upgrade:
                if lang == "hi":
                    dynamic_opts = [
                        ("✈️ 24h में प्राथमिकता रीबुकिंग", "कृपया मुझे 24 घंटे के भीतर अगली उपलब्ध उड़ान पर रीबुक करें।"),
                        ("💰 पूरा रिफंड मांगें (7 दिन)", "मुझे अपनी निरस्त उड़ान के लिए पूरा रिफंड चाहिए।"),
                        ("📋 अपग्रेड नीति के नियम", "कृपया एयरलाइन की मानार्थ अपग्रेड नीति के नियम बताएं।"),
                        ("📞 ड्यूटी सुपरवाइजर से बात करें", "क्या इस बारे में ड्यूटी सुपरवाइजर से बात हो सकती है?")
                    ]
                else:
                    dynamic_opts = [
                        ("✈️ Request Free Rebooking", "Please rebook me on the next available flight within 24 hours."),
                        ("💰 Request Full Refund", "I would like to request a full refund for my flight."),
                        ("📋 Upgrade Policy Details", "Please explain why complimentary business class upgrades are not permitted."),
                        ("📞 Escalate to Supervisor", "Can I speak with a Duty Supervisor regarding this?")
                    ]
            else:
                if lang == "hi":
                    dynamic_opts = [
                        ("💰 पूरा रिफंड मांगें (7 दिन)", "मुझे अपनी निरस्त उड़ान के लिए पूरा रिफंड चाहिए।"),
                        ("✈️ 24h में प्राथमिकता रीबुकिंग", "कृपया मुझे 24 घंटे के भीतर अगली उपलब्ध उड़ान पर रीबुक करें।"),
                        ("👑 बिजनेस क्लास अपग्रेड पूछें", "क्या मुझे इस परेशानी के लिए बिजनेस क्लास में अपग्रेड मिल सकता है?"),
                        ("📞 सुपरवाइजर एस्केलेशन", "कृपया मुझे ड्यूटी सुपरवाइजर से जोड़ें।")
                    ]
                else:
                    dynamic_opts = [
                        ("💰 Request Full Refund", "I would like to request a full refund for my flight."),
                        ("✈️ Request Free Rebooking", "Please rebook me on the next available flight within 24 hours."),
                        ("👑 Ask Business Upgrade", "Can you provide a complimentary business class upgrade for this disruption?"),
                        ("📞 Escalate to Supervisor", "Please connect me with the Duty Supervisor.")
                    ]
        elif active_booking and active_booking.delay_hours and active_booking.delay_hours >= 5:
            user_wants_fare_diff = any(kw in all_user_text for kw in ["2000", "2,000", "fare", "difference", "switch", "किराया", "अंतर", "बदलें"])
            user_wants_hotel = any(kw in all_user_text for kw in ["hotel", "होटल", "stay", "room", "ठहरने"])
            user_wants_vouchers = any(kw in all_user_text for kw in ["meal", "lounge", "voucher", "भोजन", "लाउंज", "वाउचर"])

            if user_wants_fare_diff:
                if lang == "hi":
                    dynamic_opts = [
                        ("⏱️ सुपरवाइजर किराया स्वीकृति स्थिति", "ड्यूटी सुपरवाइजर से ₹2,000 किराया छूट की स्वीकृति में कितना समय लगेगा?"),
                        ("🏨 6h देरी के लिए होटल विवरण", "मेरी 6 घंटे की देरी के लिए ट्रांजिट होटल का विवरण प्रदान करें।"),
                        ("🍽️ भोजन व लाउंज पास सक्रिय करें", "मेरे 6 घंटे की देरी के भोजन और लाउंज वाउचर सक्रिय करें।"),
                        ("📄 आधिकारिक क्लेम स्लिप डाउनलोड", "कृपया मुझे इस संपूर्ण समाधान और सुपरवाइजर डॉसियर की रसीद दें।")
                    ]
                else:
                    dynamic_opts = [
                        ("⏱️ Track Fare Waiver Status", "How long will the Duty Supervisor take to approve the ₹2,000 fare difference waiver?"),
                        ("🏨 Hotel Info (6h Delay)", "Which transit hotel near the airport is arranged for my 6-hour delay?"),
                        ("🍽️ Activate Meal & Lounge", "Please issue my executive lounge pass and meal coupon for the 6-hour delay."),
                        ("📄 Download Official Slip", "Please generate my official resolution slip and supervisor escalation dossier.")
                    ]
            elif user_wants_hotel:
                if lang == "hi":
                    dynamic_opts = [
                        ("🏨 ट्रांजिट होटल का पता व शटल", "ट्रांजिट होटल कहाँ स्थित है और शटल सेवा की क्या व्यवस्था है?"),
                        ("🔄 ₹2,000 किराया अंतर पर उड़ान बदलें", "मैं किसी अन्य वैकल्पिक उड़ान में बदलना चाहती हूँ जिसमें ₹2,000 का किराया अंतर है।"),
                        ("🍽️ भोजन व लाउंज वाउचर लें", "मेरी 6 घंटे की देरी के लिए भोजन और लाउंज वाउचर जारी करें।"),
                        ("📄 होटल वाउचर स्लिप डाउनलोड", "कृपया मुझे आधिकारिक होटल वाउचर और क्लेम रसीद दें।")
                    ]
                else:
                    dynamic_opts = [
                        ("🏨 Hotel Location & Shuttle", "Where is the transit hotel located and is airport shuttle transfer included?"),
                        ("🔄 Switch Flight (₹2k Fare Diff)", "I want to switch to an alternative flight with a ₹2,000 fare difference."),
                        ("🍽️ Claim Meal & Lounge", "Please issue my meal and lounge access vouchers for the 6-hour delay."),
                        ("📄 Download Hotel Voucher", "Please provide me with the official hotel voucher and claim receipt.")
                    ]
            elif user_wants_vouchers:
                if lang == "hi":
                    dynamic_opts = [
                        ("🏨 ट्रांजिट होटल आवास मांगें", "मेरी 6 घंटे की देरी के लिए ट्रांजिट होटल आवास की व्यवस्था करें।"),
                        ("🔄 ₹2,000 किराया अंतर पर उड़ान बदलें", "मैं किसी अन्य वैकल्पिक उड़ान में बदलना चाहती हूँ जिसमें ₹2,000 का किराया अंतर है।"),
                        ("📍 लाउंज स्थान व सुविधाएं", "टर्मिनल पर लाउंज कहाँ स्थित है और क्या सुविधाएं उपलब्ध हैं?"),
                        ("📄 समाधान स्लिप डाउनलोड करें", "कृपया मुझे इस समाधान की आधिकारिक रसीद प्रदान करें।")
                    ]
                else:
                    dynamic_opts = [
                        ("🏨 Claim Transit Hotel", "Please arrange transit hotel accommodation for my 6-hour flight delay."),
                        ("🔄 Switch Flight (₹2k Fare Diff)", "I want to switch to an alternative flight with a ₹2,000 fare difference."),
                        ("📍 Lounge Amenities & Gate", "Where is the Platinum lounge located and what amenities are available?"),
                        ("📄 Download Claim Slip", "Please provide me with an official confirmation receipt of this resolution.")
                    ]
            else:
                if lang == "hi":
                    dynamic_opts = [
                        ("🏨 ट्रांजिट होटल आवास मांगें", "मेरी 6 घंटे की देरी के लिए ट्रांजिट होटल आवास की व्यवस्था करें।"),
                        ("🔄 ₹2,000 किराया अंतर पर उड़ान बदलें", "मैं किसी अन्य वैकल्पिक उड़ान में बदलना चाहती हूँ जिसमें ₹2,000 का किराया अंतर है।"),
                        ("🍽️ भोजन व लाउंज पास लें", "मेरी 6 घंटे की देरी के लिए भोजन और लाउंज वाउचर जारी करें।"),
                        ("👑 प्लेटिनम प्राथमिकता सहायता", "प्लेटिनम सदस्य के रूप में मुझे क्या विशेष प्राथमिकताएं प्राप्त हैं?")
                    ]
                else:
                    dynamic_opts = [
                        ("🏨 Claim Transit Hotel", "Please arrange transit hotel accommodation for my 6-hour flight delay."),
                        ("🔄 Switch Flight (₹2k Fare Diff)", "I want to switch to an alternative flight with a ₹2,000 fare difference."),
                        ("🍽️ Claim Meal & Lounge", "Please issue my meal and lounge access vouchers for the 6-hour delay."),
                        ("👑 Platinum Priority Support", "What priority disruption privileges do I have as a Platinum member?")
                    ]
        else:
            user_wants_vouchers = any(kw in all_user_text for kw in ["meal", "lounge", "voucher", "pass", "भोजन", "लाउंज", "वाउचर", "पास"])
            user_wants_hotel = any(kw in all_user_text for kw in ["hotel", "होटल", "stay", "room"])

            if user_wants_vouchers:
                if lang == "hi":
                    dynamic_opts = [
                        ("📍 एग्जीक्यूटिव लाउंज कहाँ है?", "टर्मिनल पर एग्जीक्यूटिव लाउंज कहाँ स्थित है और मैं प्रवेश कैसे करूँ?"),
                        ("🍽️ भोजन वाउचर कैसे उपयोग करूँ?", "मैं हवाई अड्डे के किन आउटलेट्स पर अपना भोजन वाउचर रिडीम कर सकता हूँ?"),
                        ("🏨 होटल आवास नियम पूछें", "होटल आवास के लिए एयरलाइन की न्यूनतम देरी नीति क्या है?"),
                        ("📄 वाउचर रसीद डाउनलोड करें", "कृपया मुझे मेरे जारी वाउचर का आधिकारिक पुष्टिकरण दें।")
                    ]
                else:
                    dynamic_opts = [
                        ("📍 Where is Executive Lounge?", "Where is the executive lounge located in the terminal and how do I enter?"),
                        ("🍽️ Redeem Meal Voucher?", "Which airport dining outlets accept this meal voucher?"),
                        ("🏨 Hotel Policy Threshold?", "What is the airline's minimum delay policy required for hotel accommodation?"),
                        ("📄 Download Claim Slip", "Please provide me with an official confirmation receipt of my issued vouchers.")
                    ]
            elif user_wants_hotel:
                if lang == "hi":
                    dynamic_opts = [
                        ("🍽️ भोजन व लाउंज पास क्लेम करें", "मेरी 4 घंटे की देरी के लिए भोजन वाउचर और लाउंज एक्सेस जारी करें।"),
                        ("⏱️ संशोधित प्रस्थान समय जांचें", "मेरी उड़ान का सटीक संशोधित प्रस्थान समय क्या है?"),
                        ("💼 कनेक्टिंग यात्रा की जानकारी", "इस देरी से मेरी आगे की यात्रा और मीटिंग पर क्या प्रभाव पड़ेगा?"),
                        ("📞 ड्यूटी सुपरवाइजर से बात करें", "क्या इस संबंध में ड्यूटी सुपरवाइजर से बात हो सकती है?")
                    ]
                else:
                    dynamic_opts = [
                        ("🍽️ Claim Meal & Lounge Pass", "Please issue my eligible meal voucher and executive lounge access for the 4-hour delay."),
                        ("⏱️ Check Departure Time", "What is the exact rescheduled departure time for flight SK-118?"),
                        ("💼 Connecting Flight Impact", "How will this delay affect my connecting plans and onward journey?"),
                        ("📞 Escalate to Supervisor", "Can I speak with a Duty Supervisor regarding my delay?")
                    ]
            else:
                if lang == "hi":
                    dynamic_opts = [
                        ("🍽️ भोजन व लाउंज पास क्लेम करें", "मेरी 4 घंटे की देरी के लिए भोजन वाउचर और लाउंज एक्सेस जारी करें।"),
                        ("🏨 होटल आवास मांगें", "क्या मुझे इस 4 घंटे की देरी के लिए होटल आवास मिल सकता है?"),
                        ("⏱️ संशोधित प्रस्थान समय जांचें", "मेरी उड़ान का सटीक संशोधित प्रस्थान समय क्या है?"),
                        ("💼 कनेक्टिंग यात्रा की जानकारी", "इस देरी से मेरी आगे की यात्रा और मीटिंग पर क्या प्रभाव पड़ेगा?")
                    ]
                else:
                    dynamic_opts = [
                        ("🍽️ Claim Meal & Lounge Pass", "Please issue my eligible meal voucher and executive lounge access for the 4-hour delay."),
                        ("🏨 Request Hotel Stay", "Can you arrange hotel accommodation for my 4-hour delay?"),
                        ("⏱️ Check Departure Time", "What is the exact rescheduled departure time for flight SK-118?"),
                        ("💼 Connecting Flight Impact", "How will this delay affect my connecting plans and onward journey?")
                    ]

        # Quick Passenger Action Chips placed directly ABOVE the input box (2x2 grid for comfortable tap)
        action_header_color = "#ea580c" if not is_dark else "#fb923c"
        st.markdown(f"<div style='margin-top: 14px; margin-bottom: 8px; font-size: 11.5px; font-weight: 800; color: {action_header_color}; letter-spacing: 0.3px;'>✦ {t['quick_actions_title']}</div>", unsafe_allow_html=True)
        q_row1_1, q_row1_2 = st.columns(2)
        with q_row1_1:
            if st.button(dynamic_opts[0][0], key="dyn_opt_1", use_container_width=True):
                st.session_state.pending_prompt = dynamic_opts[0][1]
                st.rerun()
        with q_row1_2:
            if st.button(dynamic_opts[1][0], key="dyn_opt_2", use_container_width=True):
                st.session_state.pending_prompt = dynamic_opts[1][1]
                st.rerun()

        q_row2_1, q_row2_2 = st.columns(2)
        with q_row2_1:
            if st.button(dynamic_opts[2][0], key="dyn_opt_3", use_container_width=True):
                st.session_state.pending_prompt = dynamic_opts[2][1]
                st.rerun()
        with q_row2_2:
            if st.button(dynamic_opts[3][0], key="dyn_opt_4", use_container_width=True):
                st.session_state.pending_prompt = dynamic_opts[3][1]
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
