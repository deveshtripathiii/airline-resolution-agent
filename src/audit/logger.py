"""Audit logger — append-only JSON-lines conversation and action log."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.config import AUDIT_LOG_DIR


class AuditLogger:
    """Append-only logger for conversation turns and agent actions."""

    def __init__(self, log_dir: Path = AUDIT_LOG_DIR) -> None:
        self._log_dir = log_dir
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._log_file = self._log_dir / f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"

    @property
    def log_file(self) -> Path:
        return self._log_file

    def log_turn(
        self,
        customer_name: str,
        customer_message: str,
        intent: str,
        sentiment: str,
        actions: list[dict],
        agent_response: str,
        escalated: bool = False,
        escalation_reason: Optional[str] = None,
    ) -> None:
        """Append a single conversation turn to the audit log."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "customer_name": customer_name,
            "customer_message": customer_message,
            "detected_intent": intent,
            "detected_sentiment": sentiment,
            "actions_taken": actions,
            "agent_response": agent_response,
            "escalated": escalated,
            "escalation_reason": escalation_reason,
        }

        with open(self._log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def get_log_entries(self) -> list[dict]:
        """Read all entries from the current log file."""
        entries = []
        if self._log_file.exists():
            with open(self._log_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        entries.append(json.loads(line))
        return entries
