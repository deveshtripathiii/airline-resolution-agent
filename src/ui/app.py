"""Interactive Enterprise UI for SkyWay Airlines Customer Resolution Agent.

Designed for AIONOS Assignment 3 Evaluators and Customer Simulation.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

# Ensure project root is on sys.path
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
    page_title="SkyWay Airlines — Disruption Resolution Portal",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom Styling (Modern Airline Palette) ───────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background-color: #f1f5f9;
    }
    
    /* Top Brand Header */
    .brand-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0369a1 100%);
        color: white;
        padding: 20px 24px;
        border-radius: 12px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .brand-title {
        font-size: 22px;
        font-weight: 700;
        letter-spacing: -0.5px;
        margin: 0;
    }
    
    .brand-subtitle {
        font-size: 13px;
        color: #94a3b8;
        margin-top: 4px;
    }
    
    .context-badge {
        background: rgba(255, 255, 255, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 500;
        color: #e2e8f0;
    }
    
    /* Boarding Pass Card */
    .boarding-pass {
        background: white;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        position: relative;
    }
    
    .pass-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px dashed #cbd5e1;
        padding-bottom: 10px;
        margin-bottom: 12px;
    }
    
    .route-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 10px 0;
    }
    
    .city-code {
        font-size: 20px;
        font-weight: 700;
        color: #0f172a;
    }
    
    .status-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
    }
    
    .status-cancelled {
        background-color: #fee2e2;
        color: #991b1b;
        border: 1px solid #fecaca;
    }
    
    .status-delayed {
        background-color: #ffedd5;
        color: #9a3412;
        border: 1px solid #fed7aa;
    }
    
    .status-unaffected {
        background-color: #dcfce7;
        color: #166534;
        border: 1px solid #bbf7d0;
    }
    
    /* Tier Badges */
    .tier-badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .tier-platinum { background-color: #f3e8ff; color: #6b21a8; border: 1px solid #d8b4fe; }
    .tier-gold { background-color: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
    .tier-silver { background-color: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; }
    
    /* Escalation Banner */
    .escalation-box {
        background-color: #ef4444;
        color: white;
        padding: 12px 16px;
        border-radius: 8px;
        margin: 12px 0;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 8px;
        box-shadow: 0 2px 4px rgba(239, 68, 68, 0.2);
    }
    
    /* Action Pills */
    .action-badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 12px;
        font-weight: 600;
        margin: 3px 4px;
    }
    .badge-rebook { background-color: #e0f2fe; color: #0369a1; }
    .badge-refund { background-color: #dcfce7; color: #15803d; }
    .badge-meal { background-color: #fef3c7; color: #b45309; }
    .badge-lounge { background-color: #f3e8ff; color: #7e22ce; }
    .badge-hotel { background-color: #ffe4e6; color: #be123c; }
    .badge-escalate { background-color: #fee2e2; color: #b91c1c; }
    .badge-decline { background-color: #f1f5f9; color: #64748b; border: 1px solid #cbd5e1; }
    
    /* Metrics Box */
    .metric-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
    }
    .metric-val { font-size: 18px; font-weight: 700; color: #0f172a; }
    .metric-lbl { font-size: 11px; color: #64748b; margin-top: 2px; }
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


# ── Helper Formatters ──────────────────────────────────────────────────────────
def render_tier(tier_str: str) -> str:
    css = {"Platinum": "tier-platinum", "Gold": "tier-gold", "Silver": "tier-silver"}.get(tier_str, "tier-silver")
    return f'<span class="tier-badge {css}">{tier_str} TIER</span>'


def render_action_badge(action_type: str) -> str:
    badges = {
        "rebook": ("✈️ Priority Rebooking", "badge-rebook"),
        "refund": ("💰 Full Refund (7 Days)", "badge-refund"),
        "meal_voucher": ("🍽️ Meal Voucher", "badge-meal"),
        "lounge_access": ("🛋️ Executive Lounge", "badge-lounge"),
        "hotel_accommodation": ("🏨 Hotel (Delay Duration)", "badge-hotel"),
        "escalate_to_supervisor": ("🚨 Supervisor Escalation", "badge-escalate"),
        "decline_request": ("⛔ Exceeds Policy (Declined)", "badge-decline"),
        "provide_info": ("ℹ️ Info Provided", "badge-rebook"),
    }
    label, css = badges.get(action_type, ("🔹 Action", "badge-rebook"))
    return f'<span class="action-badge {css}">{label}</span>'


# ── Top Brand Header ───────────────────────────────────────────────────────────
st.markdown(f"""
<div class="brand-header">
    <div>
        <div class="brand-title">✈️ SkyWay Airlines Disruption Resolution Portal</div>
        <div class="brand-subtitle">Autonomous Customer Resolution Agent • AIONOS Assignment 3</div>
    </div>
    <div class="context-badge">
        📅 Simulation Context: {EXERCISE_DATE}
    </div>
</div>
""", unsafe_allow_html=True)


# ── Sidebar Configuration ──────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🧑‍💼 Customer Profiles")
    
    customers = st.session_state.customer_repo.get_all()
    cust_options = ["— Select Customer Profile —"] + [c.name for c in customers]
    
    current_idx = 0
    if st.session_state.selected_customer:
        try:
            current_idx = cust_options.index(st.session_state.selected_customer)
        except ValueError:
            current_idx = 0
            
    selected_cust_name = st.selectbox(
        "Select Active Passenger:",
        options=cust_options,
        index=current_idx,
        help="Select one of the 3 assessment profiles to load their booking and policy state."
    )
    
    if selected_cust_name != "— Select Customer Profile —" and selected_cust_name != st.session_state.selected_customer:
        st.session_state.selected_customer = selected_cust_name
        orchestrator.set_customer(selected_cust_name)
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")

    # Display Active Customer Details
    active_cust = orchestrator.current_customer
    if active_cust:
        st.markdown(f"#### 👤 Passenger Details")
        st.markdown(f"**{active_cust.name}** &nbsp; {render_tier(active_cust.loyalty_tier.value)}", unsafe_allow_html=True)
        st.caption(f"PNR: `{active_cust.booking_reference}` • {active_cust.contact.email}")
        
        # Flight History
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-val">{active_cust.travel_history.flights_last_12_months}</div>
                <div class="metric-lbl">Flights (12M)</div>
            </div>
            """, unsafe_allow_html=True)
        with col_b:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-val">{active_cust.travel_history.prior_complaints}</div>
                <div class="metric-lbl">Prior Complaints</div>
            </div>
            """, unsafe_allow_html=True)
            
        if active_cust.travel_history.complaint_details:
            st.caption(f"ℹ️ History: *{active_cust.travel_history.complaint_details}*")
            
        st.markdown("---")
        
        # Boarding Pass Cards for Bookings
        st.markdown("#### 🎫 Active Bookings")
        for b in orchestrator.current_bookings:
            status_css = {
                BookingStatus.CANCELLED: "status-cancelled",
                BookingStatus.DELAYED: "status-delayed",
                BookingStatus.UNAFFECTED: "status-unaffected",
            }.get(b.status, "status-unaffected")
            
            cities = b.route.split("→")
            origin = cities[0].strip() if len(cities) > 0 else "DEP"
            dest = cities[1].strip() if len(cities) > 1 else "ARR"
            
            st.markdown(f"""
            <div class="boarding-pass">
                <div class="pass-header">
                    <div><strong>Flight {b.flight}</strong></div>
                    <span class="status-badge {status_css}">{b.status.value.upper()}</span>
                </div>
                <div class="route-row">
                    <div class="city-code">{origin}</div>
                    <div style="color: #94a3b8; font-size: 14px;">✈ ─── ➔</div>
                    <div class="city-code">{dest}</div>
                </div>
                <div style="font-size: 12px; color: #64748b; margin-top: 6px;">
                    📅 {b.date} • Sch: <strong>{b.scheduled_departure}</strong>
                    {f"<br/>⚠️ Delayed by {b.delay_hours}h (New: <strong>{b.new_departure}</strong>)" if b.delay_hours else ""}
                    {f"<br/>ℹ️ Reason: {b.status_reason}" if b.status_reason else ""}
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        
        # Recruiter 1-Click Evaluation Scenarios
        st.markdown("#### ⚡ 1-Click Recruiter Tests")
        st.caption("Click to test exact scenario requirements from the PDF:")
        
        if active_cust.name == "Priya Nair":
            if st.button("🔴 Test Scenario 1: Cancelled + Refund + Upgrade Ask", use_container_width=True):
                st.session_state.pending_prompt = "My flight SK-204 was cancelled and I am furious! I demand a full cash refund PLUS a free upgrade to business class on my return flight for the trouble!"
                st.rerun()
                
        elif active_cust.name == "Arvind Kulkarni":
            if st.button("🟠 Test Scenario 2: 4h Delay + Hotel Request", use_container_width=True):
                st.session_state.pending_prompt = "My flight is delayed 4 hours and I'm missing an important connecting meeting. Since it's such a long delay, I need hotel accommodation!"
                st.rerun()
                
        elif active_cust.name == "Meher Kaur":
            if st.button("🟣 Test Scenario 3: 6h Delay + ₹2k Fare Diff + Hotel", use_container_width=True):
                st.session_state.pending_prompt = "My flight is delayed 6 hours. I want a full night's hotel stay, and I want to be moved onto a different flight where the fare difference is ₹2,000."
                st.rerun()

        if st.button("⚖️ Test Legal Threat Escalation", use_container_width=True):
            st.session_state.pending_prompt = "This is completely unacceptable! I'm contacting my lawyer and filing a formal complaint against SkyWay Airlines!"
            st.rerun()

        if st.button("🔄 Reset Conversation", use_container_width=True):
            st.session_state.messages = []
            orchestrator.set_customer(active_cust.name)
            st.rerun()


# ── Main Body Tabs ─────────────────────────────────────────────────────────────
tab_chat, tab_inspector, tab_audit = st.tabs([
    "💬 Customer Support Chat",
    "⚖️ Recruiter Policy Inspector",
    "📋 Real-Time Audit Log"
])


# ───────────────────────────────────────────────────────────────────────────────
# TAB 1: CUSTOMER SUPPORT CHAT
# ───────────────────────────────────────────────────────────────────────────────
with tab_chat:
    if not st.session_state.selected_customer:
        st.info("👈 **Please select a Passenger Profile from the left sidebar to start the interactive session.**")
        
        st.markdown("### 📋 Assignment Scenarios Overview")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
            **Scenario 1 — Priya Nair (Gold)**
            - **Flight:** SK-204 (Delhi → Goa)
            - **Status:** Cancelled (Operational)
            - **Goal:** Free Rebooking / Full Refund choice + Decline Free Upgrade
            """)
        with col2:
            st.markdown("""
            **Scenario 2 — Arvind Kulkarni (Silver)**
            - **Flight:** SK-118 (Mumbai → Bengaluru)
            - **Status:** Delayed 4 Hours
            - **Goal:** Issue Meal Voucher + Lounge Access (Deny Hotel $<5\text{h}$)
            """)
        with col3:
            st.markdown("""
            **Scenario 3 — Meher Kaur (Platinum)**
            - **Flight:** SK-305 (Delhi → Hyderabad)
            - **Status:** Delayed 6 Hours
            - **Goal:** Hotel for delay hours only + Escalate ₹2,000 Fare Diff
            """)
    else:
        # Welcome message initialization
        active_booking = orchestrator._get_active_booking()
        if not st.session_state.messages:
            if active_booking and active_booking.status == BookingStatus.CANCELLED:
                welcome = (
                    f"Hello {active_cust.name}. I see you are a valued {active_cust.loyalty_tier.value} member. "
                    f"I apologize that flight {active_booking.flight} ({active_booking.route}) on {active_booking.date} "
                    f"has been cancelled due to operational reasons. Under airline policy, I can arrange **Free Priority Rebooking** "
                    f"within 24 hours or process a **Full Refund** to your original payment method. How may I assist you?"
                )
            elif active_booking and active_booking.status == BookingStatus.DELAYED:
                welcome = (
                    f"Hello {active_cust.name}. I see your flight {active_booking.flight} ({active_booking.route}) "
                    f"is currently delayed by {active_booking.delay_hours} hours (rescheduled to {active_booking.new_departure}). "
                    f"I am here to assist you with disruption compensation and available options. How can I help?"
                )
            else:
                welcome = f"Hello {active_cust.name}, welcome to SkyWay Airlines Disruption Support. How can I help you today?"

            st.session_state.messages.append({"role": "assistant", "content": welcome})

        # Render conversation
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"], avatar="✈️" if msg["role"] == "assistant" else "👤"):
                if msg.get("escalated"):
                    st.markdown(f"""
                    <div class="escalation-box">
                        🚨 <strong>CASE ESCALATED TO SUPERVISOR / SPECIALIST SUPPORT</strong><br/>
                        <span style="font-size: 12px; font-weight: normal;">Reason: {msg.get('escalation_reason', 'Exceeds front-line agent authority / Legal threat')}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                st.markdown(msg["content"])
                
                if msg.get("actions"):
                    badges = "".join([render_action_badge(a) for a in msg["actions"]])
                    st.markdown(f"<div style='margin-top: 8px;'>{badges}</div>", unsafe_allow_html=True)

        # Process Pending Recruiter Prompt or Live User Input
        user_text = None
        if "pending_prompt" in st.session_state and st.session_state.pending_prompt:
            user_text = st.session_state.pending_prompt
            st.session_state.pending_prompt = None
        else:
            user_text = st.chat_input("Type passenger message (or click 1-Click Tests in sidebar)...")

        if user_text:
            # 1. Append User Message
            st.session_state.messages.append({"role": "user", "content": user_text})
            
            # 2. Get Orchestrator Decision
            with st.spinner("Evaluating policy rules & generating response..."):
                response = orchestrator.handle_message(user_text)

            # 3. Append Assistant Response
            st.session_state.messages.append({
                "role": "assistant",
                "content": response.message,
                "escalated": response.escalated,
                "escalation_reason": response.escalation_reason,
                "actions": [a.action_type.value for a in response.actions_taken],
            })
            st.rerun()

        # Customer Quick Action Suggestions
        st.markdown("---")
        st.caption("💡 Passenger Quick Actions:")
        qcol1, qcol2, qcol3, qcol4 = st.columns(4)
        with qcol1:
            if st.button("💰 Request Full Refund", key="btn_refund", use_container_width=True):
                st.session_state.pending_prompt = "I would like to request a full refund for my flight."
                st.rerun()
        with qcol2:
            if st.button("✈️ Request Priority Rebook", key="btn_rebook", use_container_width=True):
                st.session_state.pending_prompt = "Please rebook me on the next available flight."
                st.rerun()
        with qcol3:
            if st.button("🍽️ Claim Meal & Lounge", key="btn_vouchers", use_container_width=True):
                st.session_state.pending_prompt = "What compensation and vouchers am I eligible for?"
                st.rerun()
        with qcol4:
            if st.button("🏨 Inquire Hotel Stay", key="btn_hotel", use_container_width=True):
                st.session_state.pending_prompt = "Can you arrange hotel accommodation for me?"
                st.rerun()


# ───────────────────────────────────────────────────────────────────────────────
# TAB 2: RECRUITER POLICY INSPECTOR
# ───────────────────────────────────────────────────────────────────────────────
with tab_inspector:
    st.markdown("### ⚖️ Rules Engine & Guardrails Evaluation Matrix")
    st.caption("This tab allows AIONOS evaluators to inspect how the deterministic domain engine enforces PDF policies.")
    
    col_p1, col_p2 = st.columns(2)
    
    with col_p1:
        st.markdown("#### ✅ Allowed Actions (Front-line Agent)")
        allowed_list = [
            "Rebook customer within 24h at zero charge (airline-caused)",
            "Issue meal vouchers & lounge access per delay tiers",
            "Arrange hotel for delayed-hours portion (delays > 5h)",
            "Initiate refund to original payment method (7 business days)",
            "Provide passenger's own flight and booking details"
        ]
        for item in allowed_list:
            st.markdown(f"- 🟢 **{item}**")

    with col_p2:
        st.markdown("#### ⛔ Prohibited Actions (Mandatory Escalation)")
        prohibited_list = [
            "Approving compensation beyond stated policy amounts",
            "Waiving a fare difference above ₹1,500 without supervisor",
            "Making exceptions for non-airline-caused disruptions",
            "Handling legal threats or formal complaints (immediate escalation)",
            "Processing refunds to a different payment method"
        ]
        for item in prohibited_list:
            st.markdown(f"- 🔴 **{item}**")

    st.markdown("---")
    
    # Financial Limit Gauge
    st.markdown("#### 💵 Fare Difference Authority Meter")
    f_col1, f_col2, f_col3 = st.columns([1, 2, 1])
    with f_col2:
        st.markdown("""
        | Fare Difference Amount | Authority Level | Action |
        | :--- | :--- | :--- |
        | **$\le$ ₹1,500** | Front-line Agent | ✅ **Waive Allowed** |
        | **> ₹1,500** (e.g. Meher ₹2,000) | Duty Supervisor | 🚨 **Must Escalate** |
        """)

    st.markdown("---")
    
    # Delay Compensation Tier Grid
    st.markdown("#### ⏱️ Delay Compensation Tiers (PDF Ground Truth)")
    t1, t2, t3 = st.columns(3)
    with t1:
        st.info("**< 3 Hours Delay**\n\n• ₹500 Meal Voucher")
    with t2:
        st.warning("**3 to 5 Hours Delay**\n\n• Meal Voucher\n• Executive Lounge Access")
    with t3:
        st.error("**> 5 Hours Delay**\n\n• Meal Voucher\n• Lounge Access\n• Hotel (*Delayed hours only*)")


# ───────────────────────────────────────────────────────────────────────────────
# TAB 3: AUDIT LOG & TRANSCRIPT EXPORTER
# ───────────────────────────────────────────────────────────────────────────────
with tab_audit:
    st.markdown("### 📋 Immutable Audit Log & Decision Trace")
    st.caption("Every customer turn, extracted intent, applied policy decision, and supervisor escalation is recorded in append-only JSONL.")
    
    entries = orchestrator.audit.get_log_entries()
    
    if not entries:
        st.info("No conversation turns logged yet. Select a passenger and send a message to view the real-time audit record.")
    else:
        st.dataframe(
            entries,
            column_config={
                "timestamp": "Timestamp (UTC)",
                "customer_name": "Customer",
                "detected_intent": "Intent",
                "detected_sentiment": "Sentiment",
                "escalated": "Escalated?",
                "agent_response": "Agent Output",
            },
            use_container_width=True,
        )
        
        # Download Button for Evaluator
        log_json = json.dumps(entries, indent=2, ensure_ascii=False)
        st.download_button(
            label="📥 Download Complete Audit Transcript (.json)",
            data=log_json,
            file_name=f"audit_transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True,
        )
