from __future__ import annotations

import re


YES_NO_RE = re.compile(r"yes\s*or\s*no|true\s*or\s*false|boolean", re.IGNORECASE)
STRUCTURED_RE = re.compile(r"json|extract|fields|schema|parse", re.IGNORECASE)
FUZZY_RE = re.compile(r"synonym|closest|label|match|categorize|classify", re.IGNORECASE)
SUMMARY_RE = re.compile(r"summari[sz]e|long-form|essay|digest", re.IGNORECASE)


def infer_intent(prompt: str, snippet: str) -> tuple[str, float]:
    text = f"{prompt}\n{snippet}"
    if YES_NO_RE.search(text):
        return "yes_no_classification", 0.94
    if STRUCTURED_RE.search(text):
        return "structured_extraction", 0.9
    if FUZZY_RE.search(text):
        return "small_domain_label_matching", 0.82
    if SUMMARY_RE.search(text):
        return "long_form_summarization", 0.3
    return "generic_generation", 0.45
