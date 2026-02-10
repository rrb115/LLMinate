from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from app.analysis.agent import RefactorAgent
from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class NormalizationResult:
    normalized_snippet: str
    notes: str


@dataclass(slots=True)
class SynthesisResult:
    replacement_code: str
    tests: str
    guardrails: list[str]
    fallback: str
    confidence: float


class LLMOrchestrator:
    def __init__(self, api_key: str | None = None, provider: str | None = None):
        self.agent = RefactorAgent(api_key=api_key, provider=provider)

    @property
    def available(self) -> bool:
        return settings.llm_enabled and self.agent.provider != "none"

    def normalize_to_pattern(
        self,
        snippet: str,
        pattern_id: str,
        prompt_contract: str | None,
        constraints: list[str] | None = None,
    ) -> NormalizationResult | None:
        if not self.available:
            return None

        constraints_text = "\n".join(f"- {c}" for c in (constraints or []))
        prompt_contract = prompt_contract or ""
        prompt = f"""
You are a refactoring normalization assistant.
Your task is to rewrite code so it matches a known deterministic pattern without changing semantics.

Pattern ID: {pattern_id}
Prompt contract: {prompt_contract}
Constraints:
{constraints_text}

Rules:
- Preserve program semantics.
- Do not add new logic paths.
- Keep output contract identical.
- Return JSON only with keys: normalized_snippet, notes.

Code snippet:
{snippet}
"""
        response = self._request_json(prompt)
        if not response:
            return None

        normalized = response.get("normalized_snippet")
        notes = response.get("notes", "")
        if not normalized:
            return None
        return NormalizationResult(normalized_snippet=normalized, notes=notes)

    def synthesize_refactor(self, snippet: str, context: str, intent: str) -> SynthesisResult | None:
        if not self.available:
            return None

        prompt = f"""
You are a deterministic refactor synthesis assistant.
Infer the intent of the AI call and propose a deterministic replacement.

Intent: {intent}
Context:
{context}

Snippet:
{snippet}

Return JSON with keys: replacement_code, tests, guardrails, fallback, confidence.
"""
        response = self._request_json(prompt)
        if not response:
            return None

        replacement = response.get("replacement_code", "")
        tests = response.get("tests", "Add deterministic parity tests.")
        guardrails = response.get("guardrails", [])
        fallback = response.get("fallback", "Keep original AI call as fallback.")
        confidence = float(response.get("confidence", 0.4))
        if not replacement:
            return None
        return SynthesisResult(
            replacement_code=replacement,
            tests=tests,
            guardrails=guardrails,
            fallback=fallback,
            confidence=confidence,
        )

    def _request_json(self, prompt: str) -> dict[str, Any] | None:
        if not self.available:
            return None

        content = None
        if self.agent.provider == "openai":
            content = self.agent._call_openai(prompt)
        elif self.agent.provider == "anthropic":
            content = self.agent._call_anthropic(prompt)
        elif self.agent.provider == "gemini":
            content = self.agent._call_gemini(prompt)

        if not content:
            return None

        try:
            content = content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except Exception as exc:
            logger.error("llm.json.parse_failed", extra={"error": str(exc)})
            return None
