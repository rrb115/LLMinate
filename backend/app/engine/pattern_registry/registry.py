from __future__ import annotations

import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from app.engine.pattern_registry.ast_utils import compute_signatures, detect_language
from app.engine.pattern_registry.models import PatternDefinition

logger = logging.getLogger(__name__)


class PatternRegistry:
    def __init__(self, base_dir: Path | None = None):
        if base_dir is None:
            base_dir = Path(__file__).resolve().parent / "patterns"
        base_dir = base_dir.resolve()
        self.public_dir = base_dir / "public"
        self.private_dir = base_dir / "private"
        self.patterns: dict[str, PatternDefinition] = {}

        self.public_dir.mkdir(parents=True, exist_ok=True)
        self.private_dir.mkdir(parents=True, exist_ok=True)
        self.refresh()

    def refresh(self) -> None:
        self.patterns.clear()
        self._load_from_dir(self.public_dir)
        self._load_from_dir(self.private_dir)
        logger.info("pattern_registry.refresh", extra={"patterns": len(self.patterns)})

    def _load_from_dir(self, directory: Path) -> None:
        if not directory.exists():
            return
        for file in directory.rglob("*.json"):
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    for item in data:
                        self._add_pattern(item)
                elif isinstance(data, dict):
                    self._add_pattern(data)
            except Exception as exc:
                logger.error("pattern_registry.load_failed", extra={"file": str(file), "error": str(exc)})

    def _add_pattern(self, item: dict) -> None:
        try:
            pattern = PatternDefinition(**item)
        except TypeError as exc:
            logger.error("pattern_registry.invalid", extra={"error": str(exc)})
            return

        if pattern.source_example and not pattern.source_ast_signature:
            language = detect_language(language=pattern.language)
            signatures = compute_signatures(pattern.source_example, language)
            pattern.source_ast_signature = signatures.ast_signature
            pattern.control_flow_signature = signatures.control_flow_signature

        self.patterns[pattern.pattern_id] = pattern

    def all_patterns(self) -> list[PatternDefinition]:
        return list(self.patterns.values())

    def find_exact_match(self, ast_signature: str, language: str) -> PatternDefinition | None:
        for pattern in self.patterns.values():
            if not pattern.source_ast_signature:
                continue
            if pattern.language not in {language, "any", "unknown"}:
                continue
            if pattern.source_ast_signature == ast_signature:
                return pattern
        return None

    def get_by_intent(self, intent: str, language: str) -> PatternDefinition | None:
        for pattern in self.patterns.values():
            if pattern.intent != intent:
                continue
            if pattern.language not in {language, "any", "unknown"}:
                continue
            return pattern
        return None

    def save_pattern(self, pattern: PatternDefinition, tenant_id: str = "default") -> None:
        tenant_dir = self.private_dir / tenant_id
        tenant_dir.mkdir(parents=True, exist_ok=True)
        file_path = tenant_dir / f"{pattern.pattern_id}.json"
        payload = asdict(pattern)
        with file_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        self.patterns[pattern.pattern_id] = pattern
        logger.info("pattern_registry.saved", extra={"pattern_id": pattern.pattern_id})


_registry: PatternRegistry | None = None


def get_registry() -> PatternRegistry:
    global _registry
    if _registry is None:
        _registry = PatternRegistry()
    return _registry
