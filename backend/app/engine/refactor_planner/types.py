from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class CandidateContext:
    file_path: str
    snippet: str
    prompt: str
    intent: str
    language: str
    output_contract: str
    context: str = ""


@dataclass(slots=True)
class DecisionTrace:
    exact_match: bool = False
    similarity_match: bool = False
    similarity_score: float = 0.0
    similarity_breakdown: dict[str, float] = field(default_factory=dict)
    normalization_attempted: bool = False
    normalization_success: bool = False
    normalization_notes: str = ""
    llm_synthesis_attempted: bool = False
    llm_synthesis_success: bool = False
    stage: str = "none"
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "exact_match": self.exact_match,
            "similarity_match": self.similarity_match,
            "similarity_score": self.similarity_score,
            "similarity_breakdown": self.similarity_breakdown,
            "normalization_attempted": self.normalization_attempted,
            "normalization_success": self.normalization_success,
            "normalization_notes": self.normalization_notes,
            "llm_synthesis_attempted": self.llm_synthesis_attempted,
            "llm_synthesis_success": self.llm_synthesis_success,
            "stage": self.stage,
            "reason": self.reason,
        }


@dataclass(slots=True)
class RefactorPlan:
    can_apply: bool
    stage: str
    replacement_code: str
    tests_to_add: str
    explanation: str
    decision_trace: DecisionTrace
    pattern_id: str | None = None
    similarity_score: float | None = None
    llm_used: bool = False
    suggestion_only: bool = False
