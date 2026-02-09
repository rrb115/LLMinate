import json

def mock_llm(intent: str, text: str) -> str:
    if intent == "yes_no_classification":
        return "yes" if any(w in text.lower() for w in ["yes", "true", "y"]) else "no"
    if intent == "structured_extraction":
        import re
        m = re.search(r'(\d+)', text)
        return json.dumps({"value": m.group(1)}) if m else "{}"
    if intent == "small_domain_label_matching":
        t = text.lower()
        if "invoice" in t or "billing" in t: return "billing"
        if "help" in t or "support" in t: return "support"
        if "purchase" in t or "sales" in t: return "sales"
        return "support"
    if intent == "long_form_summarization":
        return "Mock summary: this is intentionally non-deterministic in real systems."
    return "UNSURE"
