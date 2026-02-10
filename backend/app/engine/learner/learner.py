from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from app.engine.pattern_registry.ast_utils import compute_signatures, detect_language
from app.engine.pattern_registry.models import PatternDefinition
from app.engine.pattern_registry.registry import PatternRegistry

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PromotionDecision:
    eligible: bool
    reason: str
    pattern: PatternDefinition | None = None


class PatternLearner:
    def __init__(self, registry: PatternRegistry):
        self.registry = registry

    def evaluate_promotion(
        self,
        snippet: str,
        replacement_code: str,
        intent: str,
        language: str,
        tests: str | None,
        passed_tests: bool,
    ) -> PromotionDecision:
        if not passed_tests:
            return PromotionDecision(False, "Tests did not pass.")
        if not replacement_code.strip():
            return PromotionDecision(False, "Missing replacement code.")

        signatures = compute_signatures(snippet, detect_language(language=language))
        pattern_id = f"learned_{intent}_{int(time.time())}"
        pattern = PatternDefinition(
            pattern_id=pattern_id,
            intent=intent,
            language=language,
            source_ast_signature=signatures.ast_signature,
            control_flow_signature=signatures.control_flow_signature,
            prompt_contract=None,
            output_schema=None,
            replacement_template=replacement_code,
            constraints=["learned-from-success"],
            tests=tests or "Add parity tests.",
            source_example=snippet,
        )
        return PromotionDecision(True, "Eligible for promotion.", pattern=pattern)

    def promote(self, decision: PromotionDecision, tenant_id: str = "default") -> bool:
        if not decision.eligible or not decision.pattern:
            return False
        self.registry.save_pattern(decision.pattern, tenant_id=tenant_id)
        logger.info("learner.promoted", extra={"pattern_id": decision.pattern.pattern_id})
        return True
