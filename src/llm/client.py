"""LLM client — wraps Google Gemini API, swappable/mockable."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Optional

import google.generativeai as genai

from src.config import GEMINI_API_KEY, GEMINI_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS


class BaseLLMClient(ABC):
    """Abstract base so we can mock in tests."""

    @abstractmethod
    def generate(self, system_prompt: str, user_message: str, history: list[dict] | None = None) -> str:
        ...

    @abstractmethod
    def classify_intent(self, system_prompt: str, user_message: str) -> dict:
        ...


class GeminiClient(BaseLLMClient):
    """Production client using Google Gemini."""

    def __init__(self, api_key: str = GEMINI_API_KEY, model_name: str = GEMINI_MODEL) -> None:
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=genai.GenerationConfig(
                temperature=LLM_TEMPERATURE,
                max_output_tokens=LLM_MAX_TOKENS,
            ),
        )

    def generate(self, system_prompt: str, user_message: str, history: list[dict] | None = None) -> str:
        """Generate a response given system prompt, user message, and optional history."""
        contents = []

        # Build conversation history
        if history:
            for turn in history:
                role = "user" if turn["role"] == "customer" else "model"
                contents.append({"role": role, "parts": [turn["message"]]})

        # Add current user message
        contents.append({"role": "user", "parts": [user_message]})

        chat = self._model.start_chat(history=contents[:-1] if len(contents) > 1 else [])

        # Use system instruction via the prompt
        response = self._model.generate_content(
            contents=[
                {"role": "user", "parts": [f"[SYSTEM INSTRUCTIONS]\n{system_prompt}\n\n[CUSTOMER MESSAGE]\n{user_message}"]}
            ] if not history else contents,
        )
        return response.text

    def classify_intent(self, system_prompt: str, user_message: str) -> dict:
        """Ask the LLM to classify the customer's intent and return structured JSON."""
        prompt = f"""{system_prompt}

Analyze the following customer message and return a JSON object with these fields:
- "primary_intent": one of [flight_status, cancellation_support, delay_compensation, refund_request, upgrade_request, rebook_request, hotel_request, complaint_legal, general_query]
- "secondary_intents": list of any additional intents detected
- "sentiment": one of [angry, frustrated, neutral, polite]
- "mentions_legal_action": boolean
- "mentions_upgrade": boolean
- "mentions_hotel": boolean
- "mentions_refund": boolean
- "fare_difference_amount": number or null
- "extracted_entities": object with any flight numbers, PNRs, names found

Return ONLY valid JSON, no markdown, no explanation.

Customer message: "{user_message}"
"""
        response = self._model.generate_content(prompt)
        text = response.text.strip()

        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Fallback: return a safe default
            return {
                "primary_intent": "general_query",
                "secondary_intents": [],
                "sentiment": "neutral",
                "mentions_legal_action": False,
                "mentions_upgrade": False,
                "mentions_hotel": False,
                "mentions_refund": False,
                "fare_difference_amount": None,
                "extracted_entities": {},
            }


class MockLLMClient(BaseLLMClient):
    """Mock client for testing — returns predefined responses."""

    def __init__(self, responses: Optional[list[str]] = None, intents: Optional[list[dict]] = None):
        self._responses = responses or ["I understand your concern. Let me help you with that."]
        self._intents = intents or [{"primary_intent": "general_query", "sentiment": "neutral"}]
        self._response_idx = 0
        self._intent_idx = 0

    def generate(self, system_prompt: str, user_message: str, history: list[dict] | None = None) -> str:
        resp = self._responses[min(self._response_idx, len(self._responses) - 1)]
        self._response_idx += 1
        return resp

    def classify_intent(self, system_prompt: str, user_message: str) -> dict:
        intent = self._intents[min(self._intent_idx, len(self._intents) - 1)]
        self._intent_idx += 1
        return intent
