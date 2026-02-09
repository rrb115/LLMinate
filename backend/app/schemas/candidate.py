from pydantic import BaseModel


class CandidateOut(BaseModel):
    id: int
    file: str
    line_start: int
    line_end: int
    call_snippet: str
    provider: str
    inferred_intent: str
    rule_solvability_score: float
    confidence: float
    explanation: str
    risk_level: str
    estimated_api_calls_saved: int
    latency_improvement_ms: int
    fallback_behavior: str

    model_config = {"from_attributes": True}


class PatchResponse(BaseModel):
    candidate_id: int
    diff: str
    explanation: str
    risk_level: str
    tests_to_add: str
    rule_code: str


class ShadowRunResponse(BaseModel):
    candidate_id: int
    total_cases: int
    match_rate: float
    avg_latency_improvement_ms: float
    notes: str
