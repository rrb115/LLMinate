import { useEffect, useMemo, useState } from "react";

import { api } from "./api/client";
import { CandidateCard } from "./components/CandidateCard";
import { PatchViewer } from "./components/PatchViewer";
import type { Candidate, Patch, ShadowResult } from "./types";

function App() {
  const [path, setPath] = useState("/workspace/samples");
  const [scanId, setScanId] = useState<number | null>(null);
  const [status, setStatus] = useState("idle");
  const [progress, setProgress] = useState(0);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [patch, setPatch] = useState<Patch | null>(null);
  const [shadow, setShadow] = useState<ShadowResult | null>(null);
  const [message, setMessage] = useState("");

  const selected = useMemo(
    () => candidates.find((c) => c.id === selectedId) ?? null,
    [candidates, selectedId],
  );

  async function runScan() {
    setMessage("");
    const result = await api.scan(path);
    setScanId(result.scan_id);
    setStatus(result.status);
    setCandidates([]);
    setPatch(null);
    setShadow(null);
  }

  useEffect(() => {
    if (!scanId) return;
    const timer = setInterval(async () => {
      const s = await api.status(scanId);
      setStatus(s.status);
      setProgress(s.progress);
      if (s.status === "completed") {
        clearInterval(timer);
        const rows = await api.results(scanId);
        setCandidates(rows);
        if (rows.length) setSelectedId(rows[0].id);
      }
    }, 600);
    return () => clearInterval(timer);
  }, [scanId]);

  useEffect(() => {
    if (!scanId || !selectedId) return;
    api.patch(scanId, selectedId).then(setPatch).catch(() => setPatch(null));
  }, [scanId, selectedId]);

  async function runShadow() {
    if (!scanId || !selectedId) return;
    setShadow(await api.shadow(scanId, selectedId));
  }

  async function applyPatch() {
    if (!scanId || !selectedId) return;
    const out = await api.apply(scanId, selectedId);
    setMessage(`Applied on branch ${out.branch}`);
  }

  async function revertPatch() {
    if (!scanId || !selectedId) return;
    const out = await api.revert(scanId, selectedId);
    setMessage(`Reverted branch ${out.branch}`);
  }

  return (
    <main className="min-h-screen p-4 text-slate-100 md:p-8">
      <div className="mx-auto grid max-w-7xl gap-4 md:grid-cols-[340px_1fr]">
        <section className="rounded-xl border border-sky/40 bg-slate-900/70 p-4">
          <h1 className="text-xl font-bold">AI Call Optimizer</h1>
          <p className="mt-1 text-sm text-slate-300">Scan, score, patch, and shadow-run AI calls locally.</p>
          <label className="mt-4 block text-sm">Target path</label>
          <input className="mt-1 w-full rounded border border-sky/40 bg-slate-950 p-2 text-sm" value={path} onChange={(e) => setPath(e.target.value)} />
          <button className="mt-3 w-full rounded bg-sky px-3 py-2 font-semibold text-white" onClick={runScan} type="button">Run scan</button>
          <p className="mt-3 text-sm">Status: {status} ({progress}%)</p>
          <div className="mt-4 space-y-2">
            {candidates.map((candidate) => (
              <CandidateCard
                key={candidate.id}
                candidate={candidate}
                selected={candidate.id === selectedId}
                onSelect={() => setSelectedId(candidate.id)}
              />
            ))}
          </div>
        </section>

        <section className="space-y-4">
          <div className="rounded-xl border border-mint/40 bg-slate-900/70 p-4">
            <h2 className="font-semibold">Candidate Detail</h2>
            {selected ? (
              <>
                <p className="mt-2 text-sm">{selected.explanation}</p>
                <pre className="mt-3 max-h-40 overflow-auto rounded bg-black/30 p-3 text-xs">{selected.call_snippet}</pre>
                <p className="mt-2 text-xs text-slate-300">Fallback: {selected.fallback_behavior}</p>
              </>
            ) : (
              <p className="text-sm text-slate-300">No candidate selected.</p>
            )}
          </div>

          <PatchViewer patch={patch} />

          <div className="rounded-xl border border-sky/30 bg-slate-900/60 p-4">
            <h2 className="font-semibold">Shadow Run</h2>
            {shadow ? (
              <p className="mt-2 text-sm">Match rate {Math.round(shadow.match_rate * 100)}%, latency gain {shadow.avg_latency_improvement_ms}ms.</p>
            ) : (
              <p className="mt-2 text-sm text-slate-300">Run a shadow comparison for selected candidate.</p>
            )}
            <div className="mt-3 flex flex-wrap gap-2">
              <button className="rounded bg-mint px-3 py-2 text-sm font-semibold text-black" onClick={runShadow} type="button">Run shadow</button>
              <button className="rounded bg-sky px-3 py-2 text-sm font-semibold text-white" onClick={applyPatch} type="button">Apply patch</button>
              <button className="rounded border border-slate-400 px-3 py-2 text-sm" onClick={revertPatch} type="button">Revert patch</button>
            </div>
            {message ? <p className="mt-2 text-xs text-sand">{message}</p> : null}
          </div>
        </section>
      </div>
    </main>
  );
}

export default App;
