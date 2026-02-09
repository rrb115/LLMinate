from pydantic import BaseModel


class MetricsResponse(BaseModel):
    total_scans: int
    total_candidates: int
    estimated_api_calls_saved: int
    avg_rule_solvability_score: float
    avg_latency_improvement_ms: float
