from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class PatternDefinition:
    pattern_id: str
    intent: str
    language: str
    source_ast_signature: str | None = None
    control_flow_signature: str | None = None
    prompt_contract: str | None = None
    output_schema: str | None = None
    replacement_template: str | None = None
    constraints: list[str] = field(default_factory=list)
    tests: str | None = None
    source_example: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    embeddings: dict[str, list[float]] = field(default_factory=dict)


@dataclass(slots=True)
class PatternMatch:
    pattern: PatternDefinition
    score: float
    breakdown: dict[str, float]
