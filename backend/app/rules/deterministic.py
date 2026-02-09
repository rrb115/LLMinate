from __future__ import annotations

import json
import re
from difflib import SequenceMatcher


def yes_no_rule(text: str) -> str:
    lowered = text.lower()
    positives = ["allow", "pass", "success", "approved", "yes", "true"]
    negatives = ["deny", "fail", "error", "rejected", "no", "false"]
    pos = sum(1 for p in positives if p in lowered)
    neg = sum(1 for n in negatives if n in lowered)
    return "YES" if pos >= neg else "NO"


def structured_extract_rule(text: str) -> dict[str, str]:
    patterns = {
        "name": r"name[:\-]\s*([A-Za-z ]+)",
        "email": r"email[:\-]\s*([\w\.-]+@[\w\.-]+)",
        "id": r"id[:\-]\s*([A-Za-z0-9\-]+)",
    }
    out: dict[str, str] = {}
    for key, pat in patterns.items():
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            out[key] = match.group(1).strip()
    return out


def fuzzy_label_match(query: str, labels: list[str], synonyms: dict[str, str]) -> str:
    q = query.lower().strip()
    if q in synonyms:
        return synonyms[q]

    best = ""
    score = 0.0
    for label in labels:
        current = SequenceMatcher(None, q, label.lower()).ratio()
        if current > score:
            score = current
            best = label
    return best


def serialize_result(value: object) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True)
    return str(value)
