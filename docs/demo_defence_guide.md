# 15-Minute Demo Video Script & Defence Q&A Guide

**Project:** Customer-Facing Resolution Agent (Airline Disruption)  
**Assignment:** AIONOS Assignment 3  
**Target Duration:** 12–15 Minutes  

---

## 🎬 15-Minute Demo Video Structure & Script

### Part 1: Introduction & Architecture Overview (0:00 – 3:00)
- **Opening:**
  > "Hello everyone. Today I'm presenting my submission for Assignment 3: The Customer-Facing Resolution Agent for Airline Disruptions. 
  > In the aviation industry, flight cancellations and severe delays lead to massive operational stress, angry passengers, and potential revenue loss from unauthorized compensation claims.
  > To solve this, I built an autonomous, customer-facing resolution portal that marries the natural empathy of Large Language Models with the deterministic safety of a pure business rules engine."
- **Architecture Highlights:**
  - Show the architecture diagram from `docs/architecture.md`.
  - Explain the 6-layer separation: UI (Streamlit), Orchestrator, Deterministic Rules Engine (zero I/O), LLM Client (Gemini), Repository Data Access, and Append-only Audit Logger.
  - Emphasize: *The LLM never makes financial or policy decisions alone — all entitlements are computed deterministically by the rules engine.*

---

### Part 2: Scenario 1 — Priya Nair (Flight SK-204 Cancelled) (3:00 – 6:30)
- **Context:**
  - Priya Nair is a **Gold Tier** member booked on SK-204 (Delhi → Goa) which is cancelled due to operational reasons.
  - She contacts support expressing anger ("furious") and demands a full cash refund **plus** a free business class upgrade on her return flight.
- **Live Demo Steps:**
  1. Select Priya Nair from the passenger selector.
  2. Notice the digital boarding pass displays `🔴 CANCELLED (OPERATIONAL)` and Gold Member badge.
  3. Send customer message: *"My flight SK-204 was cancelled and I am furious! I demand a full cash refund PLUS a free upgrade to business class on my return flight for the trouble!"*
  4. **Highlight the Agent's Response:**
     - Acknowledges and de-escalates her frustration with high empathy.
     - Offers the official policy choice: **Free Priority Rebooking** (within 24h) OR **Full Refund** (within 7 business days to original payment method).
     - **Politely declines the upgrade:** Clearly states that complimentary cabin upgrades are not part of disruption compensation.
  5. Select *"💰 Request Full Refund"* to confirm resolution.

---

### Part 3: Scenario 2 — Arvind Kulkarni (Flight SK-118 Delayed 4h) (6:30 – 9:30)
- **Context:**
  - Arvind Kulkarni is a **Silver Tier** member whose flight SK-118 (Mumbai → Bengaluru) is delayed by 4 hours.
  - He is anxious about missing an important business meeting and requests hotel accommodation.
- **Live Demo Steps:**
  1. Select Arvind Kulkarni from the dropdown.
  2. Notice the boarding pass reflects `🟠 DELAYED 4H (EST: 11:10)`.
  3. Send message: *"My flight is delayed 4 hours and I'm missing an important meeting in Bengaluru. Since it's such a long delay, I need hotel accommodation!"*
  4. **Highlight the Agent's Response:**
     - Expresses sincere empathy regarding his connecting meeting.
     - Automatically issues **Dining Vouchers** and **Executive Lounge Access** (qualifying 3–5h tier).
     - **Denies hotel request:** Explains policy requires delays $> 5\text{h}$ to qualify for hotel stay.

---

### Part 4: Scenario 3 — Meher Kaur (Flight SK-305 Delayed 6h) (9:30 – 12:30)
- **Context:**
  - Meher Kaur is a **Platinum Tier** member whose flight SK-305 (Delhi → Hyderabad) is delayed by 6 hours.
  - She asks for a full night's hotel stay and wants to switch to a different flight with a ₹2,000 fare difference.
- **Live Demo Steps:**
  1. Select Meher Kaur from the dropdown.
  2. Boarding pass shows `🟠 DELAYED 6H (EST: 20:00)` and Platinum badge.
  3. Send message: *"My flight is delayed 6 hours. I want a full night's hotel stay, and I want to be moved onto a different flight where the fare difference is ₹2,000."*
  4. **Highlight the Agent's Response:**
     - Issues Meal Voucher + Lounge Pass + Transit Hotel (explaining coverage is for the **delayed-hours duration**, not full night).
     - **Authority Guardrail Triggered:** Detects ₹2,000 fare diff exceeds front-line agent limit of ₹1,500 $\rightarrow$ Triggers **🚨 Duty Supervisor Escalation Card**.
     - Applies Platinum priority rebooking queue status.

---

### Part 5: Audit Log & Defense Conclusion (12:30 – 15:00)
- **Show Tab 2 ("Policy Directory"):** Review how Allowed vs. Prohibited rules and ₹1,500 thresholds are mapped to PDF data.
- **Show Tab 3 ("Service Activity Record"):**
  - Display the live JSONL table showing intent, sentiment, actions, and escalation flags.
  - Click **"Download Service Transcript (.json)"** to show audit export.
- **Show Test Suite:** Run `pytest tests/ -v` showing 52/52 tests passing in 0.4 seconds.
- **Closing Statement:**
  > "In conclusion, this project demonstrates a robust, production-grade agentic architecture that achieves 100% compliance with airline policy, protects financial authority limits, and delivers an empathetic customer experience."

---

## 🛡️ Recruiter Defence Q&A Preparation

#### Q1: Why did you separate the rules engine from the LLM?
> **Answer:** In enterprise airline operations, financial liability and regulatory policies cannot rely on probabilistic LLM output. By isolating all policy logic into a pure, deterministic rules engine (zero I/O), we guarantee 100% policy adherence and zero hallucination, while letting the LLM focus on its core strength: empathetic natural language communication.

#### Q2: How do you prevent an angry customer from manipulating the agent into giving extra compensation?
> **Answer:** All agent responses pass through our domain rules engine. If a customer demands an upgrade (like Priya) or hotel stay for a 4h delay (like Arvind), the rules engine returns an explicit `DECLINE` action. The LLM prompt is grounded to communicate the decline with empathy and valid alternatives.

#### Q3: What happens when the agent encounters a legal threat?
> **Answer:** Our regex and intent classifier immediately flag legal keywords (`lawyer`, `legal action`, `formal complaint`). This instantly bypasses standard flows, halts front-line negotiation, logs the event, and renders a priority case handover card to the airline's Specialist Legal / Supervisor support team.

#### Q4: How is mobile responsiveness achieved?
> **Answer:** We designed a mobile-first UI using adaptive CSS grid/flexbox layouts and native Streamlit container components. Boarding passes stack into mobile wallet cards and action chips remain touch-friendly on smartphone viewports.
