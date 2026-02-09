import type { Patch } from "../types";

export function PatchViewer({ patch }: { patch: Patch | null }) {
  if (!patch) return <p className="text-sm text-slate-300">Select a candidate to preview patch.</p>;

  return (
    <div className="rounded-lg border border-sky/40 bg-slate-950/70 p-4">
      <p className="text-sm text-slate-200">{patch.explanation}</p>
      <pre className="mt-3 max-h-64 overflow-auto rounded bg-black/40 p-3 text-xs text-sand">{patch.diff || "No diff generated"}</pre>
      <p className="mt-2 text-xs text-slate-300">Tests to add: {patch.tests_to_add}</p>
    </div>
  );
}
