import { Code, TestTube } from "lucide-react";

import type { Patch } from "../types";

export function PatchViewer({ patch }: { patch: Patch | null }) {
  if (!patch) {
    return <p className="text-sm text-[var(--text-muted)]">Select a candidate to preview patch.</p>;
  }

  return (
    <section className="panel overflow-hidden">
      <div className="flex items-center gap-2 border-b border-[var(--border-subtle)] bg-[var(--surface-2)]/50 px-4 py-3">
        <div className="rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-1)] p-1.5 text-[var(--accent)] shadow-sm">
          <Code className="h-4 w-4" />
        </div>
        <h2 className="text-xs font-bold uppercase tracking-wider text-[var(--text-primary)]">Proposed Patch</h2>
      </div>

      <div className="space-y-4 p-4">
        <p className="text-sm leading-relaxed text-[var(--text-secondary)]">{patch.explanation}</p>

        <div className="grid grid-cols-1 gap-3 lg:grid-cols-3">
          <div className="panel-muted p-3">
            <p className="ui-label">Refactor Reason</p>
            <p className="mt-1 text-xs text-[var(--text-secondary)]">{patch.reason_for_refactor}</p>
          </div>
          <div className="panel-muted p-3">
            <p className="ui-label">Change Summary</p>
            <p className="mt-1 text-xs text-[var(--text-secondary)]">{patch.changes_summary}</p>
          </div>
          <div className="panel-muted p-3">
            <p className="ui-label">Reply Accuracy</p>
            <p className="mt-1 text-xs font-semibold text-[var(--text-primary)]">
              {(patch.estimated_reply_accuracy * 100).toFixed(1)}%
            </p>
            <p className="mt-1 text-[10px] text-[var(--text-muted)]">{patch.accuracy_note}</p>
            <p className="mt-2 text-[10px] text-[var(--text-muted)]">
              Synthesis: {patch.synthesis_mode} ({patch.synthesis_provider})
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <div className="space-y-2">
            <span className="ui-label flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-[var(--accent)]" />
              Deterministic Rule
            </span>
            <div className="panel-muted h-[260px] min-h-[180px] max-h-[72vh] resize-y overflow-auto p-3">
              <pre className="themed-scrollbar h-full overflow-auto text-[10px] leading-relaxed text-[var(--text-secondary)]">
                {patch.rule_code || "# No logic source provided"}
              </pre>
            </div>
          </div>

          <div className="space-y-2">
            <span className="ui-label flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-[var(--accent)]" />
              Implementation Diff
            </span>
            <div className="panel-muted h-[260px] min-h-[180px] max-h-[72vh] resize-y overflow-auto p-3">
              <pre className="themed-scrollbar h-full overflow-auto text-[10px] leading-relaxed text-[var(--text-secondary)]">
                {patch.diff || "No diff generated"}
              </pre>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-[var(--accent-border)] bg-[var(--accent-soft)] p-4">
          <div className="mb-1 flex items-center gap-2 text-[var(--accent)]">
            <TestTube className="h-4 w-4" />
            <span className="text-[10px] font-black uppercase tracking-widest">Recommended Test Plan</span>
          </div>
          <p className="text-xs font-medium leading-relaxed text-[var(--text-secondary)]">{patch.tests_to_add}</p>
        </div>
      </div>
    </section>
  );
}
