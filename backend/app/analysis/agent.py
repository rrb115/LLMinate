from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

from app.core.config import settings
from app.rules.store import Rule

logger = logging.getLogger(__name__)

class RefactorAgent:
    def __init__(self, api_key: str | None = None, provider: str | None = None):
        self.provider = "none"
        self.client: Any = None
        
        # Clean inputs
        api_key = api_key.strip() if api_key else None
        
        # Helper to check if key is a real key (not a placeholder)
        def is_real(k: str | None) -> bool:
            return bool(k and len(k) > 10 and not k.startswith("sk-...") and not k.endswith("..."))

        # Use provided credentials only if BOTH are present, valid, and provider != "none"
        use_provided = api_key and is_real(api_key) and provider and provider != "none"
        
        if use_provided:
            logger.info(f"Using provided {provider} credentials")
            self._setup_provider(provider, api_key)
        else:
            # Fallback to settings
            logger.debug(f"Falling back to settings. OpenAI: {is_real(settings.openai_api_key)}, Anthropic: {is_real(settings.anthropic_api_key)}, Gemini: {is_real(settings.google_api_key)}")
            if is_real(settings.openai_api_key):
                logger.info("Using OpenAI from settings")
                self._setup_provider("openai", settings.openai_api_key)
            elif is_real(settings.anthropic_api_key):
                logger.info("Using Anthropic from settings")
                self._setup_provider("anthropic", settings.anthropic_api_key)
            elif is_real(settings.google_api_key):
                logger.info("Using Gemini from settings")
                self._setup_provider("gemini", settings.google_api_key)
            else:
                logger.warning("No valid AI API keys detected in settings or request.")

    def _setup_provider(self, provider: str, api_key: str):
        if not api_key:
            return
            
        self.provider = provider
        try:
            if provider == "openai":
                from openai import OpenAI
                self.client = OpenAI(api_key=api_key)
            elif provider == "anthropic":
                import anthropic
                self.client = anthropic.Anthropic(api_key=api_key)
            elif provider == "gemini":
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                self.client = genai.GenerativeModel("gemini-1.5-flash")
        except Exception as e:
            logger.error(f"Failed to setup provider {provider}: {e}")
            self.provider = "none"

    def _call_openai(self, prompt: str) -> str | None:
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a code refactoring assistant. Output valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return None

    def _call_anthropic(self, prompt: str) -> str | None:
        try:
            response = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=2048,
                system="You are a code refactoring assistant. Output valid JSON only.",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic error: {e}")
            return None

    def _call_gemini(self, prompt: str) -> str | None:
        try:
            response = self.client.generate_content(
                f"You are a code refactoring assistant. Output valid JSON only.\n\n{prompt}",
                generation_config={"response_mime_type": "application/json"}
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return None

    def generate_rule(self, snippet: str, context: str, inferred_intent: str) -> Rule | None:
        if self.provider == "none":
            logger.warning("No AI API keys found. Skipping refactor.")
            return None

        prompt = f"""
You are an expert Python Refactoring Agent.
Your goal is to replace a specific LLM/AI call with a deterministic, rule-based Python function.

CONTEXT:
{context}

TARGET SNIPPET (The AI call to replace):
{snippet}

INFERRED INTENT: {inferred_intent}

TASK:
1. Analyze what the AI call is doing.
2. Write a standalone Python function that achieves the same goal using standard libraries (re, json, difflib, etc.) or simple logic.
3. The function must be deterministic and fast.
4. If the logic is too complex for a simple rule (e.g. "write a poem", "summarize text"), return NULL.

OUTPUT FORMAT (JSON):
{{
  "id": "generated_expected_unique_id",
  "intent": "{inferred_intent}",
  "patterns": ["unique_substring_to_match"],
  "language": "python",
  "replacement_code": "def replacement_function(): ...",
  "test_case": "assert replacement_function() == ..."
}}

Return ONLY the raw JSON. No markdown formatting.
"""
        content = None
        if self.provider == "openai":
            content = self._call_openai(prompt)
        elif self.provider == "anthropic":
            content = self._call_anthropic(prompt)
        elif self.provider == "gemini":
            content = self._call_gemini(prompt)

        if not content:
            return None
            
        try:
            # Clean up markdown code blocks if any (Gemini tends to add ```json)
            content = content.replace("```json", "").replace("```", "").strip()
            data = json.loads(content)
            
            # Basic validation
            if "replacement_code" not in data:
                return None
            
            # Force the intent to match what we requested to ensure store lookup works
            data["intent"] = inferred_intent
            
            if "id" not in data:
                data["id"] = f"gen_{inferred_intent}_{int(time.time())}"
            if "language" not in data:
                data["language"] = "python"
            if "test_case" not in data:
                data["test_case"] = "Add parity tests."

            return Rule(**data)

        except Exception as e:
            logger.error(f"AI Refactor parsing failed: {e}")
            return None


def get_agent(api_key: str | None = None, provider: str | None = None) -> RefactorAgent:
    return RefactorAgent(api_key=api_key, provider=provider)
