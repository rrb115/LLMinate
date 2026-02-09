from __future__ import annotations

from app.rules.deterministic import fuzzy_label_match, serialize_result, structured_extract_rule, yes_no_rule


def mock_llm(intent: str, text: str) -> str:
    if intent == "yes_no_classification":
        return yes_no_rule(text)
    if intent == "structured_extraction":
        return serialize_result(structured_extract_rule(text))
    if intent == "small_domain_label_matching":
        labels = ["billing", "support", "sales"]
        synonyms = {"invoice": "billing", "help": "support", "purchase": "sales"}
        return fuzzy_label_match(text, labels, synonyms)
    if intent == "long_form_summarization":
        return "Mock summary: this is intentionally non-deterministic in real systems."
    return "UNSURE"
