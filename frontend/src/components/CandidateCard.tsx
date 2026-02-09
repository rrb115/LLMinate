import type { Candidate } from "../types";

interface Props {
  candidate: Candidate;
  selected: boolean;
  onSelect: () => void;
}

export function CandidateCard({ candidate, selected, onSelect }: Props) {
  return (
    <button
      className={`w-full rounded-lg border p-3 text-left transition ${selected ? "border-mint bg-ink/80" : "border-sky/40 bg-slate-900/40"}`}
      onClick={onSelect}
      type="button"
    >
      <div className="flex items-center justify-between">
        <strong>{candidate.inferred_intent}</strong>
        <span className="text-xs uppercase">{candidate.risk_level}</span>
      </div>
      <p className="mt-2 text-xs text-slate-300">{candidate.file}:{candidate.line_start}</p>
      <p className="mt-1 text-xs">Score: {candidate.rule_solvability_score.toFixed(2)} | Confidence: {candidate.confidence.toFixed(2)}</p>
    </button>
  );
}
