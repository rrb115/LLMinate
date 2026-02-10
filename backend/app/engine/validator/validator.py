from __future__ import annotations

import logging
from dataclasses import dataclass
from difflib import SequenceMatcher

from app.core.config import settings
from app.engine.pattern_registry.ast_utils import compute_signatures, detect_language

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ValidationResult:
    passed: bool
    reason: str


class NormalizationValidator:
    def validate(self, original: str, normalized: str, language: str) -> ValidationResult:
        language = detect_language(language=language)
        original_sig = compute_signatures(original, language)
        normalized_sig = compute_signatures(normalized, language)

        if not original_sig.ast_signature or not normalized_sig.ast_signature:
            return ValidationResult(False, "Missing AST signatures.")

        similarity = SequenceMatcher(None, original_sig.ast_signature, normalized_sig.ast_signature).ratio()
        if similarity < settings.normalization_similarity_threshold:
            return ValidationResult(False, f"AST similarity {similarity:.2f} below threshold.")

        return ValidationResult(True, f"AST similarity {similarity:.2f} ok.")


class RefactorValidator:
    def validate_synthesis(self, replacement_code: str) -> ValidationResult:
        if not replacement_code.strip():
            return ValidationResult(False, "Empty replacement code.")
        if "def " not in replacement_code and "function" not in replacement_code:
            return ValidationResult(False, "Replacement lacks function definition.")
        return ValidationResult(True, "Replacement code passes basic checks.")
