"""Intent analysis — bridge between LLM classification and domain models."""

from __future__ import annotations

from src.domain.models import Intent, IntentAnalysis, Sentiment


def parse_llm_intent(raw: dict) -> IntentAnalysis:
    """Convert raw LLM JSON output into a typed IntentAnalysis model."""

    # Safe enum parsing with fallback
    try:
        primary = Intent(raw.get("primary_intent", "general_query"))
    except ValueError:
        primary = Intent.GENERAL_QUERY

    secondary = []
    for s in raw.get("secondary_intents", []):
        try:
            secondary.append(Intent(s))
        except ValueError:
            pass

    try:
        sentiment = Sentiment(raw.get("sentiment", "neutral"))
    except ValueError:
        sentiment = Sentiment.NEUTRAL

    return IntentAnalysis(
        primary_intent=primary,
        secondary_intents=secondary,
        sentiment=sentiment,
        mentions_legal_action=bool(raw.get("mentions_legal_action", False)),
        mentions_upgrade=bool(raw.get("mentions_upgrade", False)),
        mentions_hotel=bool(raw.get("mentions_hotel", False)),
        mentions_refund=bool(raw.get("mentions_refund", False)),
        fare_difference_amount=raw.get("fare_difference_amount"),
        extracted_entities=raw.get("extracted_entities", {}),
    )
