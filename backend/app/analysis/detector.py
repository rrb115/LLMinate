from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from app.analysis.types import DetectionHit
from app.analysis.treesitter_extractor import extract_calls

AI_HINT_RE = re.compile(
    r"openai|anthropic|gemini|chat\.completions|generate(Content)?\(|\.messages\.create\(|\.generate\(",
    re.IGNORECASE,
)
PROMPT_RE = re.compile(r"(?:prompt|content|messages)\s*[=:]\s*([\"\'][\s\S]{0,400}?[\"\'])")


def _provider_from_snippet(snippet: str) -> str:
    s = snippet.lower()
    if "anthropic" in s or "messages.create" in s:
        return "anthropic"
    if "gemini" in s or "generatecontent" in s:
        return "gemini"
    if "openai" in s or "chat.completions" in s:
        return "openai"
    return "generic_llm"


def _extract_prompt(snippet: str) -> str:
    match = PROMPT_RE.search(snippet)
    if not match:
        return snippet[:300]
    prompt = match.group(1).strip('"\'')
    return prompt[:1000]


def _fallback_scan(path: Path) -> list[DetectionHit]:
    hits: list[DetectionHit] = []
    for file in path.rglob("*"):
        if file.suffix.lower() not in {".py", ".js", ".ts", ".tsx", ".jsx"}:
            continue
        text = file.read_text(encoding="utf-8", errors="ignore")
        ts_calls = extract_calls(file)
        for line_start, line_end, snippet in ts_calls:
            hits.append(
                DetectionHit(
                    file=str(file),
                    line_start=line_start,
                    line_end=line_end,
                    snippet=snippet,
                    provider=_provider_from_snippet(snippet),
                    prompt=_extract_prompt(snippet),
                )
            )
        for idx, line in enumerate(text.splitlines(), start=1):
            if AI_HINT_RE.search(line):
                snippet = "\n".join(text.splitlines()[max(0, idx - 1) : idx + 3])
                hits.append(
                    DetectionHit(
                        file=str(file),
                        line_start=idx,
                        line_end=min(idx + 2, len(text.splitlines())),
                        snippet=snippet,
                        provider=_provider_from_snippet(snippet),
                        prompt=_extract_prompt(snippet),
                    )
                )
    return hits


def _semgrep_scan(path: Path, rules_path: Path) -> list[DetectionHit]:
    cmd = [
        "semgrep",
        "--config",
        str(rules_path),
        "--json",
        str(path),
    ]
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode not in (0, 1):
        return []

    payload = json.loads(result.stdout or "{}")
    findings = payload.get("results", [])
    hits: list[DetectionHit] = []
    for finding in findings:
        start = finding.get("start", {})
        end = finding.get("end", {})
        extra = finding.get("extra", {})
        snippet = extra.get("lines", "").strip() or extra.get("message", "")
        file_path = finding.get("path", "")
        hits.append(
            DetectionHit(
                file=file_path,
                line_start=int(start.get("line", 1)),
                line_end=int(end.get("line", start.get("line", 1))),
                snippet=snippet,
                provider=_provider_from_snippet(snippet),
                prompt=_extract_prompt(snippet),
            )
        )
    return hits


def scan_for_ai_calls(target_path: str, rules_path: str) -> list[DetectionHit]:
    path = Path(target_path).resolve()
    semgrep_hits = _semgrep_scan(path, Path(rules_path).resolve())
    fallback_hits = _fallback_scan(path)

    merged: dict[tuple[str, int, str], DetectionHit] = {}
    for hit in semgrep_hits + fallback_hits:
        key = (hit.file, hit.line_start, hit.snippet[:80])
        merged[key] = hit
    return list(merged.values())
