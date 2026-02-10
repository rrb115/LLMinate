from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.engine.pattern_registry.models import PatternDefinition, PatternMatch

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class SimilarityConfig:
    threshold: float = 0.78
    top_k: int = 3
    weights: dict[str, float] = None

    def __post_init__(self) -> None:
        if self.weights is None:
            self.weights = {"prompt": 0.34, "ast": 0.38, "output": 0.28}


class SimilarityEngine:
    def __init__(self, config: SimilarityConfig | None = None):
        self.config = config or SimilarityConfig()
        self._patterns: list[PatternDefinition] = []
        self._vectorizers: dict[str, TfidfVectorizer] = {}
        self._matrices: dict[str, np.ndarray] = {}

    def build_index(self, patterns: list[PatternDefinition]) -> None:
        self._patterns = patterns
        if not patterns:
            self._vectorizers = {}
            self._matrices = {}
            logger.info("similarity.index.empty")
            return
        prompt_texts = [self._prompt_text(p) for p in patterns]
        ast_texts = [p.source_ast_signature or "" for p in patterns]
        output_texts = [self._output_text(p) for p in patterns]

        self._vectorizers = {
            "prompt": TfidfVectorizer(min_df=1),
            "ast": TfidfVectorizer(min_df=1),
            "output": TfidfVectorizer(min_df=1),
        }

        self._matrices = {
            "prompt": self._vectorizers["prompt"].fit_transform(prompt_texts).toarray(),
            "ast": self._vectorizers["ast"].fit_transform(ast_texts).toarray(),
            "output": self._vectorizers["output"].fit_transform(output_texts).toarray(),
        }
        logger.info("similarity.index.built", extra={"patterns": len(patterns)})

    def score(self, prompt_text: str, ast_signature: str, output_text: str) -> list[PatternMatch]:
        if not self._patterns:
            return []

        candidate_vectors = {
            "prompt": self._vectorizers["prompt"].transform([prompt_text]).toarray(),
            "ast": self._vectorizers["ast"].transform([ast_signature]).toarray(),
            "output": self._vectorizers["output"].transform([output_text]).toarray(),
        }

        total_scores = np.zeros(len(self._patterns))
        breakdowns: list[dict[str, float]] = [
            {"prompt": 0.0, "ast": 0.0, "output": 0.0} for _ in self._patterns
        ]

        for key, weight in self.config.weights.items():
            if weight <= 0:
                continue
            matrix = self._matrices[key]
            scores = cosine_similarity(candidate_vectors[key], matrix)[0]
            total_scores += scores * weight
            for idx, score in enumerate(scores):
                breakdowns[idx][key] = float(score)

        top_indices = np.argsort(total_scores)[::-1][: self.config.top_k]
        matches: list[PatternMatch] = []
        for idx in top_indices:
            matches.append(
                PatternMatch(
                    pattern=self._patterns[idx],
                    score=float(total_scores[idx]),
                    breakdown=breakdowns[idx],
                )
            )
        return matches

    def _prompt_text(self, pattern: PatternDefinition) -> str:
        contract = pattern.prompt_contract or ""
        return f"{pattern.intent} {contract}"

    def _output_text(self, pattern: PatternDefinition) -> str:
        output_schema = pattern.output_schema or ""
        replacement = pattern.replacement_template or ""
        return f"{output_schema} {replacement[:200]}"
