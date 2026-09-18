# Architecture — Airline Customer-Facing Resolution Agent

## Overview

This agent handles airline disruption scenarios (cancellations, delays) by combining LLM-powered natural language understanding with a deterministic rules engine for policy compliance.

## Design Principles

1. **Policy compliance is deterministic** — The rules engine (not the LLM) makes all compensation decisions
2. **LLM handles language** — Intent classification and natural response generation only
3. **Layer isolation** — Each layer has a single responsibility and clear boundaries
4. **Testable** — Rules engine has zero I/O; LLM is mockable; data access uses repository pattern

## Process Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                        CUSTOMER MESSAGE                         │
└──────────────────────────┬───────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────────┐
│  1. INTENT CLASSIFICATION (LLM)                                 │
│     - Primary intent (cancellation, delay, refund, upgrade...)  │
│     - Sentiment (angry, frustrated, neutral, polite)            │
│     - Entity extraction (flight numbers, amounts)               │
│     - Legal threat detection                                    │
└──────────────────────────┬───────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────────┐
│  2. ESCALATION CHECK                                            │
│     - Regex + LLM flag for legal threats / formal complaints    │
│     - If triggered → skip rules → generate escalation response  │
└──────────────────────────┬───────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────────┐
│  3. RULES ENGINE (Deterministic)                                │
│     - Cancellation → rebook OR refund                           │
│     - Delay < 3h → ₹500 meal voucher                           │
│     - Delay 3-5h → meal + lounge                                │
│     - Delay > 5h → meal + lounge + hotel (delayed hours only)   │
│     - Upgrade → always decline (not in policy)                  │
│     - Fare diff > ₹1,500 → escalate to supervisor              │
│     - Full-night hotel → decline (policy covers delayed hrs)    │
│     - Loyalty: Gold/Platinum → priority rebooking only          │
└──────────────────────────┬───────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────────┐
│  4. RESPONSE GENERATION (LLM)                                   │
│     - System prompt with: customer profile, booking, policies   │
│     - Decision context from rules engine                        │
│     - Tone guidelines from sample conversations                 │
│     - Produces empathetic, policy-grounded response             │
└──────────────────────────┬───────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────────┐
│  5. AUDIT LOG                                                   │
│     - Timestamp, customer, message, intent, actions, response   │
│     - Append-only JSONL file                                    │
└──────────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

### Why rules engine + LLM (not pure LLM)?
- **Compliance**: The rules engine guarantees policy adherence — the LLM never decides compensation amounts
- **Testability**: Pure functions can be unit tested without LLM calls
- **Auditability**: Every decision is traceable to a specific rule

### Why repository pattern?
- Single point of data access — easy to swap JSON for a database later
- Tests can mock the repository without touching files

### Why mock LLM client?
- Tests run without API keys or network
- Demo works out-of-the-box even without a Gemini key

## Data Flow

```
JSON Files → Repository → Domain Models → Rules Engine → Actions
                                              ↑            ↓
                                         LLM Client → Orchestrator → UI
                                                          ↓
                                                     Audit Logger
```

## Assumptions

1. Only the 3 customers and 4 bookings from the data pack exist
2. The exercise date is fixed at Wednesday, 23 September 2026
3. All policies are as stated in the data pack — no exceptions
4. The agent cannot access external flight databases or real-time data
5. Refunds are always to the original payment method
