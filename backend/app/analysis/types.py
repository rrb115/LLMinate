from dataclasses import dataclass


@dataclass(slots=True)
class DetectionHit:
    file: str
    line_start: int
    line_end: int
    snippet: str
    provider: str
    prompt: str
