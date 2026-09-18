"""Central configuration for the Airline Resolution Agent."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ──────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
AUDIT_LOG_DIR = PROJECT_ROOT / "audit_logs"

CUSTOMERS_FILE = DATA_DIR / "customers.json"
BOOKINGS_FILE = DATA_DIR / "bookings.json"
POLICIES_FILE = DATA_DIR / "policies.json"
SAMPLE_CONVERSATIONS_FILE = DATA_DIR / "sample_conversations.json"

# ── LLM ────────────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1024"))

# ── Exercise context ───────────────────────────────────────────────────────────
EXERCISE_DATE = "Wednesday, 23 September 2026"
AIRLINE_NAME = "SkyWay Airlines"
