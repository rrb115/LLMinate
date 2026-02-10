from __future__ import annotations

import json
import logging

from app.core.config import settings
from app.engine.intent_inference import summarize_prompt_intent
from app.engine.llm_orchestrator import LLMOrchestrator
from app.engine.pattern_registry.ast_utils import compute_signatures, detect_language
from app.engine.pattern_registry.models import PatternDefinition
from app.engine.pattern_registry.registry import PatternRegistry, get_registry
from app.engine.refactor_planner.types import CandidateContext, DecisionTrace, RefactorPlan
from app.engine.similarity_engine import SimilarityConfig, SimilarityEngine
from app.engine.validator import NormalizationValidator, RefactorValidator

logger = logging.getLogger(__name__)


class ProgressiveCertaintyPlanner:
    def __init__(
        self,
        registry: PatternRegistry | None = None,
        similarity_engine: SimilarityEngine | None = None,
        llm_orchestrator: LLMOrchestrator | None = None,
    ):
        self.registry = registry or get_registry()
        self.similarity_engine = similarity_engine or SimilarityEngine(
            SimilarityConfig(threshold=settings.similarity_threshold, top_k=settings.similarity_top_k)
        )
        self.similarity_engine.build_index(self.registry.all_patterns())
        self.llm_orchestrator = llm_orchestrator or LLMOrchestrator()
        self.normalizer_validator = NormalizationValidator()
        self.refactor_validator = RefactorValidator()

    def plan(self, candidate: CandidateContext) -> RefactorPlan:
        trace = DecisionTrace()
        language = detect_language(file_path=candidate.file_path, language=candidate.language)

        signatures = compute_signatures(candidate.snippet, language)
        exact_pattern = self.registry.find_exact_match(signatures.ast_signature, language)
        if exact_pattern and exact_pattern.replacement_template:
            trace.exact_match = True
            trace.stage = "exact-match"
            trace.reason = "AST signature matched deterministic pattern."
            logger.info(
                "planner.stage.exact_match",
                extra={"pattern_id": exact_pattern.pattern_id, "intent": candidate.intent},
            )
            return self._deterministic_plan(candidate, exact_pattern, trace)

        prompt_summary = summarize_prompt_intent(candidate.prompt, candidate.intent)
        matches = self.similarity_engine.score(
            prompt_summary,
            signatures.ast_signature,
            candidate.output_contract,
        )
        if matches:
            top = matches[0]
            trace.similarity_match = True
            trace.similarity_score = top.score
            trace.similarity_breakdown = top.breakdown
            logger.info(
                "planner.stage.similarity_match",
                extra={"pattern_id": top.pattern.pattern_id, "score": top.score},
            )

            if top.score >= settings.similarity_threshold:
                trace.normalization_attempted = True
                normalized = self.llm_orchestrator.normalize_to_pattern(
                    candidate.snippet,
                    top.pattern.pattern_id,
                    top.pattern.prompt_contract,
                    top.pattern.constraints,
                )
                if normalized:
                    validation = self.normalizer_validator.validate(
                        candidate.snippet, normalized.normalized_snippet, language
                    )
                    if validation.passed:
                        trace.normalization_success = True
                        trace.normalization_notes = normalized.notes or validation.reason
                        normalized_sig = compute_signatures(normalized.normalized_snippet, language)
                        pattern_after_norm = self.registry.find_exact_match(
                            normalized_sig.ast_signature, language
                        )
                        if pattern_after_norm and pattern_after_norm.replacement_template:
                            trace.stage = "similarity-normalized"
                            trace.reason = "Normalized to deterministic pattern."
                            logger.info(
                                "planner.stage.similarity_normalized",
                                extra={"pattern_id": pattern_after_norm.pattern_id},
                            )
                            return self._deterministic_plan(candidate, pattern_after_norm, trace, llm_used=True)
                    else:
                        trace.normalization_notes = validation.reason
                trace.stage = "similarity-normalized"
                trace.reason = "Normalization failed or could not match pattern."

        if settings.llm_enabled and self.llm_orchestrator.available and candidate.intent in settings.deterministic_capable_intents:
            trace.llm_synthesis_attempted = True
            synthesis = self.llm_orchestrator.synthesize_refactor(
                candidate.snippet,
                candidate.context,
                candidate.intent,
            )
            if synthesis:
                validation = self.refactor_validator.validate_synthesis(synthesis.replacement_code)
                if validation.passed:
                    trace.llm_synthesis_success = True
                    trace.stage = "llm-synthesis"
                    trace.reason = "LLM provided deterministic replacement."
                    logger.info(
                        "planner.stage.llm_synthesis",
                        extra={"intent": candidate.intent, "confidence": synthesis.confidence},
                    )
                    explanation = "LLM synthesized replacement; suggestion-only by default."
                    return RefactorPlan(
                        can_apply=False,
                        stage="llm-synthesis",
                        replacement_code=synthesis.replacement_code,
                        tests_to_add=synthesis.tests,
                        explanation=explanation,
                        decision_trace=trace,
                        llm_used=True,
                        suggestion_only=True,
                    )

        trace.stage = "no-match"
        trace.reason = "No safe deterministic refactor path found."
        return RefactorPlan(
            can_apply=False,
            stage="no-match",
            replacement_code="",
            tests_to_add="Add deterministic parity tests.",
            explanation="No deterministic refactor available.",
            decision_trace=trace,
            llm_used=False,
            suggestion_only=True,
        )

    def _deterministic_plan(
        self,
        candidate: CandidateContext,
        pattern: PatternDefinition,
        trace: DecisionTrace,
        llm_used: bool = False,
    ) -> RefactorPlan:
        replacement = pattern.replacement_template or ""
        tests = pattern.tests or "Add deterministic parity tests."
        explanation = f"Deterministic refactor applied using pattern '{pattern.pattern_id}'."
        return RefactorPlan(
            can_apply=True,
            stage=trace.stage,
            replacement_code=replacement,
            tests_to_add=tests,
            explanation=explanation,
            decision_trace=trace,
            pattern_id=pattern.pattern_id,
            similarity_score=trace.similarity_score or None,
            llm_used=llm_used,
            suggestion_only=False,
        )
