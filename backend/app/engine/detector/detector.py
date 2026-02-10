from __future__ import annotations

import logging
from pathlib import Path

from app.analysis.detector import scan_for_ai_calls

logger = logging.getLogger(__name__)


def detect_ai_calls(target_path: str, rules_path: str) -> list:
    logger.info("detector.scan.start", extra={"target_path": target_path})
    hits = scan_for_ai_calls(target_path, rules_path)
    logger.info("detector.scan.complete", extra={"hits": len(hits)})
    return hits
