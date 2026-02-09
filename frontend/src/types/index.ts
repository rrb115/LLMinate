export interface Candidate {
  id: number;
  file: string;
  line_start: number;
  line_end: number;
  call_snippet: string;
  provider: string;
  inferred_intent: string;
  rule_solvability_score: number;
  confidence: number;
  explanation: string;
  risk_level: "low" | "medium" | "high";
  estimated_api_calls_saved: number;
  latency_improvement_ms: number;
  fallback_behavior: string;
}

export interface Patch {
  candidate_id: number;
  diff: string;
  explanation: string;
  risk_level: string;
  tests_to_add: string;
  rule_code: string;
  synthesis_mode: string;
  synthesis_provider: string;
  reason_for_refactor: string;
  changes_summary: string;
  estimated_reply_accuracy: number;
  accuracy_note: string;
}

export interface ShadowResult {
  candidate_id: number;
  total_cases: number;
  match_rate: number;
  avg_latency_improvement_ms: number;
  notes: string;
}
