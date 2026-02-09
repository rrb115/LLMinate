import type { Candidate } from "../types";

interface Props {
  candidate: Candidate;
  selected: boolean;
  onSelect: () => void;
}

export function CandidateCard({ candidate, selected, onSelect }: Props) {
  return (
    <button
      className={`interactive-card group w-full p-3 text-left transition-all duration-200 ${selected ? "interactive-card-selected" : ""}`}
      onClick={onSelect}
      type="button"
    >
      <div className="flex items-center justify-between gap-3">
        <strong className="truncate text-[12px] font-semibold leading-tight text-[var(--text-primary)] transition-colors group-hover:text-[var(--accent)]">
          {candidate.inferred_intent}
        </strong>
        <span className={`status-pill shrink-0 px-2 py-0.5 text-[9px] font-bold ${selected ? "status-pill-complete" : ""}`}>
          {candidate.risk_level}
        </span>
      </div>
      <div className="mt-2 flex items-center gap-2 text-[10px] text-[var(--text-muted)]">
        <span className="rounded border border-[var(--border-subtle)] bg-[var(--surface-2)] px-1.5 py-0.5">
          score {candidate.rule_solvability_score.toFixed(2)}
        </span>
        <span className="rounded border border-[var(--border-subtle)] bg-[var(--surface-2)] px-1.5 py-0.5">
          conf {candidate.confidence.toFixed(2)}
        </span>
        <span className="ml-auto truncate text-[10px]">{candidate.file.split("/").pop()}:{candidate.line_start}</span>
      </div>
    </button>
  );
}
