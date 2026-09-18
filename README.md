# ✈️ SkyWay Airlines — Customer-Facing Resolution Agent
Link is --- https://skyway-airline-agent.streamlit.app/
An AI-powered customer support agent for handling airline disruptions (cancellations, delays) following strict policy rules.

**Assignment 3** — Agentic AI Factory / AIONOS

## 🚀 Quick Start

```bash
# 1. Clone the repo
git clone <repo-url>
cd airline-agent

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up your Gemini API key
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# 4. Run the app
streamlit run src/ui/app.py
```

> **Note:** The app works without an API key using a mock LLM for demo purposes. Add a Gemini API key for full LLM-powered conversations.

## 📐 Architecture

```
Customer Message
       ↓
┌─────────────────┐
│  Streamlit UI   │  ← Chat interface + sidebar
└───────┬─────────┘
        ↓
┌─────────────────┐
│  Orchestrator   │  ← Intent → Decision → Action → Response
└───────┬─────────┘
        ↓
┌─────────┬──────────────┬──────────────┐
│  LLM    │ Rules Engine │ Data Access  │
│ (Gemini)│ (Pure Logic) │ (Repository) │
└─────────┴──────────────┴──────────────┘
        ↓
┌─────────────────┐
│  Audit Logger   │  ← Append-only JSON-lines log
└─────────────────┘
```

### Layer Separation
| Layer | Responsibility | I/O |
|-------|---------------|-----|
| `src/ui/` | Streamlit chat interface | UI only |
| `src/agent/` | Orchestration pipeline | Coordinates layers |
| `src/domain/` | Models + rules engine | **Zero I/O** (pure logic) |
| `src/llm/` | Gemini API client | Network (mockable) |
| `src/data_access/` | Repository pattern | File reads (JSON) |
| `src/audit/` | Conversation logging | File writes (JSONL) |

## 🎯 Scenarios

| # | Customer | Tier | Issue | Key Decision |
|---|----------|------|-------|-------------|
| 1 | Priya Nair | Gold | SK-204 cancelled | Rebook OR refund. Decline free upgrade. |
| 2 | Arvind Kulkarni | Silver | SK-118 delayed 4h | Meal + lounge. Deny hotel (< 5h). |
| 3 | Meher Kaur | Platinum | SK-305 delayed 6h | Meal + lounge + hotel (delayed hrs). Fare diff ₹2,000 → escalate. |

## 🧪 Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_rules_engine.py -v
```

## 🛠️ Tech Stack

- **Python 3.11+**
- **Streamlit** — Chat UI
- **Google Gemini API** — LLM (intent classification + response generation)
- **Pydantic** — Data models
- **pytest** — Testing

## 📁 Project Structure

```
airline-agent/
├── data/                      # JSON data files
│   ├── customers.json
│   ├── bookings.json
│   ├── policies.json
│   └── sample_conversations.json
├── src/
│   ├── config.py              # Central configuration
│   ├── data_access/           # Repository pattern (JSON → models)
│   ├── domain/                # Models + rules engine (pure logic)
│   ├── llm/                   # Gemini client (swappable/mockable)
│   ├── agent/                 # Orchestrator + intent analysis
│   ├── audit/                 # Append-only JSONL logger
│   └── ui/                    # Streamlit chat app
├── tests/                     # Unit + integration tests
├── docs/architecture.md       # Architecture documentation
├── requirements.txt
├── .env.example
└── README.md
```

## 📝 AI Tools Used

| Tool | Purpose |
|------|---------|
| Google Gemini (gemini-2.0-flash) | Intent classification + natural language response generation |
| Streamlit | Rapid UI prototyping for chat interface |
| Pydantic | Data validation and structured model definitions |

## 📄 License

Built for Agentic AI Factory / AIONOS — Assignment 3.
