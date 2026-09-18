"""Script to generate the official 10-slide PowerPoint presentation (.pptx) for AIONOS Assignment 3."""

from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

OUTPUT_PATH = Path("C:/Users/CENTER LAB-3/Desktop/airline-agent/presentation_10_slides.pptx")

# ── Color Palette (Aviation Sky & Navy Theme) ──────────────────────────────────
NAVY = RGBColor(15, 23, 42)       # #0f172a
SKY_BLUE = RGBColor(2, 132, 199)   # #0284c7
LIGHT_BLUE = RGBColor(224, 242, 254) # #e0f2fe
DARK_GRAY = RGBColor(51, 65, 85)   # #334155
WHITE = RGBColor(255, 255, 255)
GOLD = RGBColor(217, 119, 6)       # #d97706
EMERALD = RGBColor(16, 185, 129)   # #10b981


def create_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)  # 16:9 widescreen
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    def add_header(slide, title_text, category_text="AIONOS ASSIGNMENT 3 — AIRLINE DISRUPTION"):
        # Header banner shape
        header_box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(0.5), Inches(11.733), Inches(1.1))
        header_box.fill.solid()
        header_box.fill.fore_color.rgb = NAVY
        header_box.line.color.rgb = SKY_BLUE
        header_box.line.width = Pt(1.5)

        tf = header_box.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.3)
        tf.margin_top = Inches(0.15)

        p_cat = tf.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.size = Pt(10)
        p_cat.font.bold = True
        p_cat.font.color.rgb = SKY_BLUE

        p_title = tf.add_paragraph()
        p_title.text = title_text
        p_title.font.size = Pt(22)
        p_title.font.bold = True
        p_title.font.color.rgb = WHITE

    # ── SLIDE 1: Title Slide ───────────────────────────────────────────────────
    s1 = prs.slides.add_slide(blank_layout)
    bg1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = NAVY
    bg1.line.fill.background()

    # Title box
    tb1 = s1.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(11.333), Inches(3.5))
    tf1 = tb1.text_frame
    tf1.word_wrap = True

    p1 = tf1.paragraphs[0]
    p1.text = "Customer-Facing Resolution Agent"
    p1.font.size = Pt(40)
    p1.font.bold = True
    p1.font.color.rgb = WHITE

    p2 = tf1.add_paragraph()
    p2.text = "Airline Disruption Management with Deterministic Policy Guardrails"
    p2.font.size = Pt(22)
    p2.font.color.rgb = SKY_BLUE
    p2.font.bold = True

    p3 = tf1.add_paragraph()
    p3.text = "\nAgentic AI Factory | AIONOS • Assignment 3 Project Defence"
    p3.font.size = Pt(16)
    p3.font.color.rgb = LIGHT_BLUE

    # ── SLIDE 2: Problem Statement ─────────────────────────────────────────────
    s2 = prs.slides.add_slide(blank_layout)
    add_header(s2, "1. Business Problem & Mission Statement")
    
    tb2 = s2.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(11.733), Inches(5.2))
    tf2 = tb2.text_frame
    tf2.word_wrap = True

    bullets2 = [
        ("The Challenge:", "Airline disruptions (cancellations and multi-hour delays) cause immense customer frustration, leading to angry passengers demanding arbitrary upgrades, refunds, or threatening legal action."),
        ("The Business Risk:", "Pure LLM bots suffer from hallucination, authorizing unauthorized compensation or exceeding financial authority thresholds (e.g. fare difference waivers)."),
        ("The Objective:", "Build an autonomous customer-facing resolution agent that:"),
        ("  • Understands Intent & Sentiment:", "Detects customer emotional state and exact request."),
        ("  • Strictly Enforces Grounded Policy:", "Determines entitlements deterministically from data pack rules."),
        ("  • Protects Airline Authority:", "Escalates cases exceeding front-line limits (e.g., fare diff > ₹1,500, legal threats) to human supervisors."),
        ("  • Maintains Full Audit Trail:", "Preserves append-only immutable records of every turn and decision.")
    ]
    for title, desc in bullets2:
        p = tf2.add_paragraph()
        p.text = f"{title} {desc}"
        p.font.size = Pt(14)
        p.font.color.rgb = DARK_GRAY

    # ── SLIDE 3: System Architecture ───────────────────────────────────────────
    s3 = prs.slides.add_slide(blank_layout)
    add_header(s3, "2. End-to-End System Architecture")

    tb3 = s3.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(11.733), Inches(5.2))
    tf3 = tb3.text_frame
    tf3.word_wrap = True

    bullets3 = [
        ("Layer 1 — UI & Presentation Layer (Streamlit):", "Enterprise self-service portal with mobile-friendly boarding pass telemetry, Day/Night theme, and live action badges."),
        ("Layer 2 — Agent Orchestration Engine:", "Coordinates Intent Analysis → Repository Lookups → Rules Engine Evaluation → Response Generation → Audit Logging."),
        ("Layer 3 — Pure Rules Engine (Zero I/O):", "Deterministic business logic calculating exact entitlements for cancellations, delay tiers, fare diff limits, and escalation triggers."),
        ("Layer 4 — LLM Client (Google Gemini / Smart Fallback):", "Natural language intent extraction and empathetic tone synthesis grounded in sample conversation reference styles."),
        ("Layer 5 — Data Access Layer (Repository Pattern):", "Encapsulates all JSON data access (customers, bookings, service rules) with typed Pydantic models."),
        ("Layer 6 — Immutable Audit Logging:", "Append-only JSONL log preserving timestamps, passenger ID, intent, actions taken, and supervisor escalation state.")
    ]
    for title, desc in bullets3:
        p = tf3.add_paragraph()
        p.text = f"{title} {desc}"
        p.font.size = Pt(14)
        p.font.color.rgb = DARK_GRAY

    # ── SLIDE 4: Grounded Data & Passenger Profiles ───────────────────────────
    s4 = prs.slides.add_slide(blank_layout)
    add_header(s4, "3. Grounded Data & Passenger Context (23 Sep 2026)")

    tb4 = s4.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(11.733), Inches(5.2))
    tf4 = tb4.text_frame
    tf4.word_wrap = True

    bullets4 = [
        ("Simulation Context:", "Operational Date: Wednesday, 23 September 2026. Zero external data assumptions."),
        ("Profile 1 — Priya Nair (Gold Member | PNR: SK4821X):", "6 annual flights, 1 prior complaint (delayed baggage). Booked on SK-204 (Delhi → Goa) which is CANCELLED due to operational reasons."),
        ("Profile 2 — Arvind Kulkarni (Silver Member | PNR: TR1190B):", "3 annual flights, 0 prior complaints. Booked on SK-118 (Mumbai → Bengaluru) DELAYED 4 Hours (rescheduled to 11:10)."),
        ("Profile 3 — Meher Kaur (Platinum Member | PNR: WL7742):", "10 annual flights, 1 prior complaint (overbooking upgrade). Booked on SK-305 (Delhi → Hyderabad) DELAYED 6 Hours (rescheduled to 20:00)."),
        ("Policy Constraint:", "Gold and Platinum members receive priority rebooking access, but NO extra compensation beyond policy.")
    ]
    for title, desc in bullets4:
        p = tf4.add_paragraph()
        p.text = f"{title} {desc}"
        p.font.size = Pt(14)
        p.font.color.rgb = DARK_GRAY

    # ── SLIDE 5: Policy Rules & Compensation Engine ───────────────────────────
    s5 = prs.slides.add_slide(blank_layout)
    add_header(s5, "4. Service Rules & Compensation Entitlements")

    tb5 = s5.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(11.733), Inches(5.2))
    tf5 = tb5.text_frame
    tf5.word_wrap = True

    bullets5 = [
        ("Cancellation Rebooking Rule:", "Airline-caused cancellation entitles passenger to choose between Free Rebooking on the next available flight within 24 hours OR Full Refund (processed within 7 business days to original payment method)."),
        ("Delay Compensation Tier 1 (< 3 Hours):", "Entitles passenger to ₹500 Dining Voucher."),
        ("Delay Compensation Tier 2 (3 to 5 Hours):", "Entitles passenger to Dining Voucher + Executive Departure Lounge Access."),
        ("Delay Compensation Tier 3 (> 5 Hours):", "Entitles passenger to Dining Voucher + Executive Lounge Access + Hotel Accommodation covering the delayed-hours duration only (not a full night's stay)."),
        ("Fare Difference Rebooking Rule:", "Voluntary flight change fare differences up to ₹1,500 can be waived by front-line agent; differences > ₹1,500 REQUIRE supervisor escalation.")
    ]
    for title, desc in bullets5:
        p = tf5.add_paragraph()
        p.text = f"{title} {desc}"
        p.font.size = Pt(14)
        p.font.color.rgb = DARK_GRAY

    # ── SLIDE 6: Authority Guardrails & Escalation ─────────────────────────────
    s6 = prs.slides.add_slide(blank_layout)
    add_header(s6, "5. Authority Limits & Mandatory Escalation Guardrails")

    tb6 = s6.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(11.733), Inches(5.2))
    tf6 = tb6.text_frame
    tf6.word_wrap = True

    bullets6 = [
        ("Allowed Front-Line Agent Actions:", ""),
        ("  ✓", "Rebook passenger within 24h at zero charge for airline-caused disruptions."),
        ("  ✓", "Issue meal vouchers, lounge passes, and transit hotel accommodation per delay tiers."),
        ("  ✓", "Initiate refunds to original payment method within 7 business days."),
        ("Prohibited Actions (Enforced via Escalation Triggers):", ""),
        ("  ✗", "Approving any compensation beyond stated policy amounts."),
        ("  ✗", "Waiving fare differences exceeding ₹1,500 without supervisor authorization."),
        ("  ✗", "Making exceptions for non-airline disruptions (e.g. passenger missed flight)."),
        ("  ✗", "Handling threats of legal action or formal complaints — immediate specialist support transfer.")
    ]
    for title, desc in bullets6:
        p = tf6.add_paragraph()
        p.text = f"{title} {desc}"
        p.font.size = Pt(13.5)
        p.font.color.rgb = DARK_GRAY

    # ── SLIDE 7: Scenarios Walkthrough ─────────────────────────────────────────
    s7 = prs.slides.add_slide(blank_layout)
    add_header(s7, "6. Test Scenarios & Resolution Walkthrough")

    tb7 = s7.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(11.733), Inches(5.2))
    tf7 = tb7.text_frame
    tf7.word_wrap = True

    bullets7 = [
        ("Scenario 1 — Priya Nair (Gold | SK-204 Cancelled | Furious + Upgrade Ask):", "Agent acknowledges anger empathetically, offers choice of Free Priority Rebooking or Full Refund (7 days), and politely declines the requested complimentary business class upgrade (not covered by policy)."),
        ("Scenario 2 — Arvind Kulkarni (Silver | SK-118 Delayed 4h | Missed Meeting + Hotel Ask):", "Agent acknowledges missed meeting with empathy, issues Meal Voucher and Executive Lounge Access (3–5h tier), and politely denies the hotel accommodation request (policy requires > 5h delay)."),
        ("Scenario 3 — Meher Kaur (Platinum | SK-305 Delayed 6h | ₹2k Fare Diff + Overnight Hotel Ask):", "Agent issues Meal + Lounge + Transit Hotel (explaining coverage is for delay hours only, not full night). Agent flags ₹2,000 fare difference > ₹1,500 limit and initiates Priority Escalation to Duty Supervisor.")
    ]
    for title, desc in bullets7:
        p = tf7.add_paragraph()
        p.text = f"{title} {desc}"
        p.font.size = Pt(14)
        p.font.color.rgb = DARK_GRAY

    # ── SLIDE 8: Verification & Test Coverage ──────────────────────────────────
    s8 = prs.slides.add_slide(blank_layout)
    add_header(s8, "7. Quality Assurance & Automated Test Suite")

    tb8 = s8.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(11.733), Inches(5.2))
    tf8 = tb8.text_frame
    tf8.word_wrap = True

    bullets8 = [
        ("Test Suite Results:", "52 / 52 Unit & Integration Tests Passed (100% Pass Rate)."),
        ("1. Rules Engine Suite (22 Tests):", "Verifies cancellation choices, delay tiers (<3h, 3-5h, >5h), hotel eligibility, fare difference thresholds, upgrade rejections, and legal threat regex detection."),
        ("2. Data Access Suite (20 Tests):", "Verifies customer lookups, booking legs, PNR lookups, policy text extraction, and sample conversation formatting."),
        ("3. Orchestrator End-to-End Suite (10 Tests):", "Validates complete conversational pipelines for Priya, Arvind, and Meher scenarios with mock LLM integration."),
        ("Deterministic Safety:", "Pure business logic functions execute in under 0.5s with zero I/O and zero hallucination risk.")
    ]
    for title, desc in bullets8:
        p = tf8.add_paragraph()
        p.text = f"{title} {desc}"
        p.font.size = Pt(14)
        p.font.color.rgb = DARK_GRAY

    # ── SLIDE 9: Tech Stack & AI Integration ───────────────────────────────────
    s9 = prs.slides.add_slide(blank_layout)
    add_header(s9, "8. Technology Stack & AI Integration Strategy")

    tb9 = s9.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(11.733), Inches(5.2))
    tf9 = tb9.text_frame
    tf9.word_wrap = True

    bullets9 = [
        ("Core Language & Runtime:", "Python 3.12 with type annotations and Pydantic v2 data models."),
        ("UI Framework:", "Streamlit 1.64 — Aviation Sky Theme, Day/Night mode toggle, and mobile-responsive layouts."),
        ("LLM Integration:", "Google Gemini API (gemini-2.0-flash) with structured JSON intent classification and grounded response prompts."),
        ("Offline Evaluation Fallback:", "SmartDeterministicClient provides authentic, dynamic multi-turn dialogue without requiring API keys or network connection."),
        ("Version Control & DevOps:", "Git repository with clear layer separation, .gitignore protection for credentials, and modular package architecture.")
    ]
    for title, desc in bullets9:
        p = tf9.add_paragraph()
        p.text = f"{title} {desc}"
        p.font.size = Pt(14)
        p.font.color.rgb = DARK_GRAY

    # ── SLIDE 10: Conclusion & Key Learnings ───────────────────────────────────
    s10 = prs.slides.add_slide(blank_layout)
    add_header(s10, "9. Key Learnings, Business Impact & Future Roadmap")

    tb10 = s10.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(11.733), Inches(5.2))
    tf10 = tb10.text_frame
    tf10.word_wrap = True

    bullets10 = [
        ("Key Architectural Learning:", "Separating deterministic rule enforcement from LLM natural language generation eliminates hallucination while preserving high empathy and user engagement."),
        ("Business Impact:", "Reduces customer support wait times during mass disruption from hours to seconds, prevents financial leakage from unauthorized waivers, and guarantees regulatory compliance."),
        ("Future Roadmap & Enterprise Scaling:", ""),
        ("  • PSS API Integration:", "Connect with live Passenger Service Systems (Amadeus, Sabre, Navitaire) for automated seat reallocation."),
        ("  • Instant Payment Gateway:", "Automated refund processing and direct digital voucher dispatch to Apple/Google Wallets."),
        ("  • Multi-lingual Voice Agent:", "Extend text resolution to telephony and multilingual voice channels.")
    ]
    for title, desc in bullets10:
        p = tf10.add_paragraph()
        p.text = f"{title} {desc}"
        p.font.size = Pt(14)
        p.font.color.rgb = DARK_GRAY

    prs.save(str(OUTPUT_PATH))
    print(f"Presentation saved successfully to: {OUTPUT_PATH}")


if __name__ == "__main__":
    create_deck()
