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
PROMPT_RE = re.compile(
    r"(?:prompt|content|messages)(?:\s*:\s*\w+)?\s*[=:]\s*(?:f|r|b)?([\"\'`][\s\S]{0,1000}?[\"\'`])",
    re.IGNORECASE,
)


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
    prompt = match.group(1).strip('"\'`')
    return prompt[:1000]


def _is_noise(line: str) -> bool:
    s = line.strip()
    # Imports
    if s.startswith(("import ", "from ")):
        return True
    if re.search(r"=\s*require\(", s):
        return True
    
    # Class definitions
    if s.startswith("class ") and ("OpenAI" in s or "Anthropic" in s):
        return True

    # Instantiation / Setup
    # JS: new OpenAI(...)
    if "new OpenAI" in s or "new Anthropic" in s:
         return True
    
    # Python/General: client = OpenAI(...) or client = openai.OpenAI(...)
    # Heuristic: = (optional namespace.)Provider(
    if re.search(r"=\s*(\w+\.)?(OpenAI|Anthropic|Gemini|GoogleGenerativeAI)\(", s, re.IGNORECASE):
        return True
    
    # Catch simple assignment like: client = OpenAI()
    if re.match(r"^[\w\s,]+=\s*(\w+\.)?(OpenAI|Anthropic|Gemini|GoogleGenerativeAI)\(", s, re.IGNORECASE):
        return True

    # Catch bare class usage if it looks like a type hint or simple reference
    if re.match(r"^\s*(\w+\.)?(OpenAI|Anthropic|Gemini|GoogleGenerativeAI)\s*$", s, re.IGNORECASE):
        return True
        
    return False


def _get_context(file_path: str, line_start: int, window_up: int = 15, window_down: int = 5) -> str:
    try:
        path = Path(file_path)
        text = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        start = max(0, line_start - 1 - window_up)
        end = min(len(text), line_start + window_down)
        return "\n".join(text[start:end])
    except Exception:
        return ""


def _fallback_scan(path: Path) -> list[DetectionHit]:
    hits: list[DetectionHit] = []
    for file in path.rglob("*"):
        if file.suffix.lower() not in {".py", ".js", ".ts", ".tsx", ".jsx"}:
            continue
        text = file.read_text(encoding="utf-8", errors="ignore")
        ts_calls = extract_calls(file)
        for line_start, line_end, snippet in ts_calls:
            if _is_noise(snippet):
                continue
            # Use larger context for prompt extraction
            context = _get_context(str(file), line_start)
            
            hits.append(
                DetectionHit(
                    file=str(file),
                    line_start=line_start,
                    line_end=line_end,
                    snippet=snippet,
                    provider=_provider_from_snippet(snippet),
                    prompt=_extract_prompt(context),
                )
            )
        for idx, line in enumerate(text.splitlines(), start=1):
            if AI_HINT_RE.search(line):
                if _is_noise(line):
                    continue
                snippet = "\n".join(text.splitlines()[max(0, idx - 1) : idx + 3])
                # Use larger context for prompt extraction
                context = "\n".join(text.splitlines()[max(0, idx - 15) : idx + 5])
                
                hits.append(
                    DetectionHit(
                        file=str(file),
                        line_start=idx,
                        line_end=min(idx + 2, len(text.splitlines())),
                        snippet=snippet,
                        provider=_provider_from_snippet(snippet),
                        prompt=_extract_prompt(context),
                    )
                )
    return hits


import sys

def _semgrep_scan(path: Path, rules_path: Path) -> list[DetectionHit]:
    # Attempt to find semgrep in the same directory as the python executable
    semgrep_bin = "semgrep"
    try:
        potential_bin = Path(sys.executable).parent / "semgrep"
        if potential_bin.exists():
            semgrep_bin = str(potential_bin)
    except Exception:
        pass

    cmd = [
        semgrep_bin,
        "--config",
        str(rules_path),
        "--json",
        str(path),
    ]
    
    try:
        result = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        print(f"Error: semgrep timed out after 30s on {path}")
        return []
    except FileNotFoundError:
        print(f"Error: semgrep binary not found at '{semgrep_bin}' or in PATH.")
        return []
    except Exception as e:
        print(f"Error running semgrep: {e}")
        return []

    if result.returncode not in (0, 1):
        if result.stderr:
            print(f"Semgrep Error: {result.stderr}")
        return []

    payload = json.loads(result.stdout or "{}")
    findings = payload.get("results", [])
    hits: list[DetectionHit] = []
    for finding in findings:
        start = finding.get("start", {})
        end = finding.get("end", {})
        extra = finding.get("extra", {})
        file_path = finding.get("path", "")
        
        # If semgrep returns masked lines or no lines, read from file
        snippet = extra.get("lines", "").strip()
        if not snippet or snippet == "requires login":
            try:
                line_start = int(start.get("line", 1))
                line_end = int(end.get("line", line_start))
                snippet = _extract_segment(Path(file_path).read_text(encoding="utf-8", errors="ignore"), line_start - 1, line_end - 1)
            except Exception:
                snippet = extra.get("message", "")

        if _is_noise(snippet):
            continue

        local_context = _get_context(file_path, int(start.get("line", 1)))
        
        hits.append(
            DetectionHit(
                file=file_path,
                line_start=int(start.get("line", 1)),
                line_end=int(end.get("line", start.get("line", 1))),
                snippet=snippet,
                provider=_provider_from_snippet(snippet),
                prompt=_extract_prompt(local_context),
            )
        )
    return hits

def _extract_segment(text: str, start_row: int, end_row: int) -> str:
    lines = text.splitlines()
    return "\n".join(lines[start_row : min(end_row + 1, len(lines))])


def scan_for_ai_calls(target_path: str, rules_path: str) -> list[DetectionHit]:
    path = Path(target_path).resolve()
    semgrep_hits = _semgrep_scan(path, Path(rules_path).resolve())
    fallback_hits = _fallback_scan(path)

    merged: dict[tuple[str, int, str], DetectionHit] = {}
    for hit in semgrep_hits + fallback_hits:
        if _is_noise(hit.snippet):
            continue
        key = (hit.file, hit.line_start, hit.snippet[:80])
        merged[key] = hit
    return list(merged.values())
