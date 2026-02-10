from __future__ import annotations

import logging
import re

from app.analysis.intent import infer_intent as legacy_infer_intent

logger = logging.getLogger(__name__)

YES_NO_RE = re.compile(r"yes\s*or\s*no|true\s*or\s*false|boolean", re.IGNORECASE)
JSON_RE = re.compile(r"json|schema|fields|extract", re.IGNORECASE)
ENUM_RE = re.compile(r"enum|one of|choose|label|category", re.IGNORECASE)


def infer_intent(prompt: str, snippet: str) -> tuple[str, float]:
    intent, confidence = legacy_infer_intent(prompt, snippet)
    logger.info("intent.infer", extra={"intent": intent, "confidence": confidence})
    return intent, confidence


def infer_output_contract(prompt: str, snippet: str) -> str:
    text = f"{prompt}\n{snippet}".lower()
    if YES_NO_RE.search(text):
        return "ENUM: YES|NO"
    if JSON_RE.search(text):
        return "JSON_OBJECT"
    if ENUM_RE.search(text):
        return "ENUM_OR_LABEL"
    return "FREEFORM_TEXT"


def summarize_prompt_intent(prompt: str, intent: str) -> str:
    prompt = (prompt or "").strip()
    if len(prompt) > 400:
        prompt = prompt[:400] + "..."
    return f"intent={intent} prompt={prompt}"
