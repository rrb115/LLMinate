import { useEffect, useMemo, useState } from "react";
import { Activity, AlertTriangle, Check, Code, Search, Shield, TestTube } from "lucide-react";

import { api } from "./api/client";
import { CandidateCard } from "./components/CandidateCard";
import { InputSection } from "./components/InputSection";
import { Layout } from "./components/Layout";
import { PatchViewer } from "./components/PatchViewer";
import type { Candidate, Patch, ShadowResult } from "./types";

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Unknown error";
}

function App() {
  const [scanId, setScanId] = useState<number | null>(null);
  const [status, setStatus] = useState("idle");
  const [progress, setProgress] = useState(0);
  const [candidates, setCandidates] = useState<Record<string, Candidate[]>>({});
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [patch, setPatch] = useState<Patch | null>(null);
  const [shadow, setShadow] = useState<ShadowResult | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [logs, setLogs] = useState("");

  const [provider, setProvider] = useState("none");
  const [leftPaneMode, setLeftPaneMode] = useState<"setup" | "cases">("setup");
  const [sidebarWidth, setSidebarWidth] = useState(380);
  const [isResizing, setIsResizing] = useState(false);

  const allCandidates = useMemo(() => Object.values(candidates).flat(), [candidates]);

  const selected = useMemo(
    () => allCandidates.find((candidate) => candidate.id === selectedId) ?? null,
    [allCandidates, selectedId],
  );

  useEffect(() => {
    if (!scanId) return;
    const timer = setInterval(async () => {
      try {
        const current = await api.status(scanId);
        setStatus(current.status);
        setProgress(current.progress);
        setLogs(current.logs);

        if (current.status === "completed") {
          clearInterval(timer);
          const grouped = await api.results(scanId);
          setCandidates(grouped);
          setLeftPaneMode("cases");
          const first = Object.keys(grouped)[0];
          if (first && grouped[first].length) {
            setSelectedId(grouped[first][0].id);
          }
        }
      } catch (e) {
        console.error(e);
      }
    }, 600);

    return () => clearInterval(timer);
  }, [scanId]);

  useEffect(() => {
    const el = document.getElementById("logs-end");
    if (el) el.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  useEffect(() => {
    if (!scanId || !selectedId) return;
    api.patch(scanId, selectedId).then(setPatch).catch(() => setPatch(null));
  }, [scanId, selectedId]);

  useEffect(() => {
    if (!isResizing) return;

    const handleMove = (event: MouseEvent) => {
      const min = 300;
      const max = 560;
      const nextWidth = Math.min(max, Math.max(min, event.clientX - 24));
      setSidebarWidth(nextWidth);
    };

    const handleUp = () => setIsResizing(false);

    window.addEventListener("mousemove", handleMove);
    window.addEventListener("mouseup", handleUp);

    return () => {
      window.removeEventListener("mousemove", handleMove);
      window.removeEventListener("mouseup", handleUp);
    };
  }, [isResizing]);

  async function runShadow() {
    if (!scanId || !selectedId) return;
    try {
      setShadow(await api.shadow(scanId, selectedId));
    } catch (error: unknown) {
      setMessage(`Shadow run failed: ${errorMessage(error)}`);
    }
  }

  async function applyPatch() {
    if (!scanId || !selectedId) return;
    try {
      const out = await api.apply(scanId, selectedId);
      setMessage(`Applied on branch ${out.branch}`);
    } catch (error: unknown) {
      setMessage(`Apply failed: ${errorMessage(error)}`);
    }
  }

  async function revertPatch() {
    if (!scanId || !selectedId) return;
    try {
      const out = await api.revert(scanId, selectedId);
      setMessage(`Reverted branch ${out.branch}`);
    } catch (error: unknown) {
      setMessage(`Revert failed: ${errorMessage(error)}`);
    }
  }

  function handleScanStart(id: number) {
    setScanId(id);
    setStatus("queued");
    setLeftPaneMode("setup");
    setProgress(0);
    setCandidates({});
    setPatch(null);
    setShadow(null);
    setError("");
    setMessage("");
    setLogs("");
  }

  return (
    <div data-provider={provider} className={`theme-shift ${isResizing ? "select-none" : ""}`}>
      <Layout>
        <div className="flex flex-col gap-4 lg:flex-row lg:gap-0">
          <aside className="space-y-4 lg:pr-2" style={{ width: `min(100%, ${sidebarWidth}px)` }}>
            <div className="panel-muted p-1">
              <div className="grid grid-cols-2 gap-1">
                <button
                  type="button"
                  onClick={() => setLeftPaneMode("setup")}
                  className={`ui-tab px-2 py-2 text-[11px] font-semibold uppercase tracking-wide ${leftPaneMode === "setup" ? "ui-tab-active" : ""}`}
                >
                  Scan Setup
                </button>
                <button
                  type="button"
                  onClick={() => setLeftPaneMode("cases")}
                  className={`ui-tab px-2 py-2 text-[11px] font-semibold uppercase tracking-wide ${leftPaneMode === "cases" ? "ui-tab-active" : ""}`}
                >
                  Cases
                </button>
              </div>
            </div>

            <div className={`space-y-4 overflow-hidden transition-all duration-300 ${leftPaneMode === "setup" ? "max-h-[2200px] opacity-100 translate-y-0" : "pointer-events-none max-h-0 -translate-y-1 opacity-0"}`}>
              <InputSection onScanStart={handleScanStart} onError={setError} onProviderChange={setProvider} />

              {error && (
                <div className="panel border-red-500/20 bg-red-500/5 p-4 text-sm text-[var(--danger)]">
                  <div className="flex items-center gap-2 font-bold uppercase tracking-wider text-[10px]">
                    <AlertTriangle className="h-3.5 w-3.5" />
                    Error Detected
                  </div>
                  <p className="mt-2 text-xs font-medium leading-relaxed">{error}</p>
                </div>
              )}

              {status !== "idle" && (
                <div className="panel p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Activity className={`h-4 w-4 text-[var(--accent)] ${status === "running" ? "animate-pulse" : ""}`} />
                      <span className="ui-label">Processing Status</span>
                    </div>
                    <span className={`status-pill px-2.5 py-0.5 ${status === "completed" ? "status-pill-complete" : ""}`}>
                      {status}
                    </span>
                  </div>

                  <div className="space-y-2">
                    <div className="h-2 w-full overflow-hidden rounded-full bg-[var(--surface-3)]">
                      <div
                        className="h-full rounded-full bg-[var(--accent)] transition-all duration-500"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-tight">
                      <span>Analysis Pipeline</span>
                      <span>{progress}%</span>
                    </div>
                  </div>

                  {logs && (
                    <div className="mt-4 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-canvas)] p-3">
                      <div className="mb-2 flex items-center gap-2 text-[9px] font-black uppercase tracking-[0.2em] text-[var(--text-muted)] opacity-50">
                        <div className="h-1 w-1 rounded-full bg-[var(--accent)]" />
                        Live Activity Feed
                      </div>
                      <div className="themed-scrollbar max-h-[160px] overflow-y-auto space-y-1.5">
                        {logs.split("\n").filter(Boolean).map((log, i) => (
                          <div key={i} className="flex gap-2 text-[11px] leading-relaxed">
                            <span className="text-[var(--accent)] opacity-50 select-none">&gt;</span>
                            <span className={`font-medium ${i === logs.split("\n").filter(Boolean).length - 1 ? "text-[var(--text-primary)]" : "text-[var(--text-muted)]"}`}>
                              {log}
                            </span>
                          </div>
                        ))}
                        <div id="logs-end" />
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            <section className={`panel p-3 overflow-hidden transition-all duration-300 ${leftPaneMode === "cases" ? "max-h-[2200px] opacity-100 translate-y-0" : "pointer-events-none max-h-0 -translate-y-1 opacity-0 p-0 border-0"}`}>
              <div className="mb-3 flex items-center justify-between">
                <h3 className="text-[11px] font-bold uppercase tracking-widest text-[var(--text-muted)]">Cases</h3>
                <span className="status-pill px-2 py-0.5">{allCandidates.length}</span>
              </div>

              {Object.keys(candidates).length > 0 ? (
                <div className="themed-scrollbar max-h-[620px] space-y-3 overflow-y-auto pr-1">
                  {Object.entries(candidates).map(([file, group]) => (
                    <div key={file} className="space-y-2">
                      <p className="truncate text-[10px] font-semibold uppercase tracking-wide text-[var(--text-muted)]">
                        {file.split("/").pop()} ({group.length})
                      </p>
                      <div className="space-y-1.5">
                        {group.map((candidate) => (
                          <CandidateCard
                            key={candidate.id}
                            candidate={candidate}
                            selected={selectedId === candidate.id}
                            onSelect={() => setSelectedId(candidate.id)}
                          />
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              ) : status === "completed" ? (
                <div className="rounded-xl border border-dashed p-8 text-center">
                  <Check className="mx-auto h-7 w-7 text-[var(--accent)] opacity-50" />
                  <p className="mt-2 text-sm font-medium text-[var(--text-muted)]">All clear. No calls found.</p>
                </div>
              ) : (
                <p className="text-xs text-[var(--text-muted)]">Run a scan to populate cases.</p>
              )}
            </section>
          </aside>

          <button
            type="button"
            aria-label="Resize panels"
            aria-valuemin={300}
            aria-valuemax={560}
            aria-valuenow={sidebarWidth}
            onMouseDown={() => setIsResizing(true)}
            className={`hidden lg:flex lg:w-3 lg:cursor-col-resize lg:items-center lg:justify-center ${isResizing ? "bg-[var(--accent-soft)]" : "hover:bg-[var(--surface-2)]"}`}
          >
            <span className="h-20 w-[2px] rounded-full bg-[var(--border-subtle)]" />
          </button>

          <section className="space-y-4 lg:min-w-0 lg:flex-1 lg:pl-2">
            <div className="panel overflow-hidden">
              <div className="flex items-center gap-2 border-b border-[var(--border-subtle)] bg-[var(--surface-2)]/50 px-4 py-3">
                <div className="rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-1)] p-2 text-[var(--accent)] shadow-sm">
                  <Search className="h-4 w-4" />
                </div>
                <h2 className="text-sm font-bold uppercase tracking-wider text-[var(--text-primary)]">Inference Analysis</h2>
              </div>

              <div className="p-4">
                {selected ? (
                  <div className="space-y-4">
                    <p className="text-[15px] leading-relaxed text-[var(--text-secondary)]">{selected.explanation}</p>

                    <div className="panel-muted overflow-hidden">
                      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] bg-[var(--surface-3)]/30 px-4 py-2 text-[10px] font-bold uppercase tracking-widest text-[var(--text-muted)]">
                        <span>Source Implementation</span>
                        <code className="lowercase bg-[var(--surface-1)] px-1.5 py-0.5 rounded border border-[var(--border-subtle)]">
                          {selected.file}:{selected.line_start}
                        </code>
                      </div>
                      <pre className="themed-scrollbar min-h-[220px] max-h-[75vh] resize-y overflow-auto p-5 text-[11px] leading-relaxed text-[var(--text-secondary)]">
                        {selected.call_snippet}
                      </pre>
                    </div>

                    <div className="flex items-center gap-3 rounded-lg bg-[var(--accent-soft)] px-4 py-3 text-[11px] text-[var(--accent)] border border-[var(--accent-border)] font-medium">
                      <Shield className="h-4 w-4 flex-shrink-0" />
                      <p>
                        Safety Strategy: <span className="font-bold underline decoration-dotted">{selected.fallback_behavior}</span>
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="flex h-48 flex-col items-center justify-center gap-2 text-[var(--text-muted)] opacity-60">
                    <div className="h-10 w-10 rounded-full border border-dashed border-current flex items-center justify-center">
                      <Activity className="h-5 w-5" />
                    </div>
                    <p className="text-sm font-medium">Select a candidate to view optimization details</p>
                  </div>
                )}
              </div>
            </div>

            <PatchViewer patch={patch} />

            <div className="panel overflow-hidden">
              <div className="flex items-center justify-between border-b border-[var(--border-subtle)] bg-[var(--surface-2)]/50 px-4 py-3">
                <div className="flex items-center gap-2">
                  <div className="rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-1)] p-2 text-[var(--accent)] shadow-sm">
                    <TestTube className="h-4 w-4" />
                  </div>
                  <h2 className="text-sm font-bold uppercase tracking-wider text-[var(--text-primary)]">Validation & Deployment</h2>
                </div>
                {shadow && (
                  <div className="flex items-center gap-2">
                    <span className="status-pill status-pill-complete px-3 py-1 font-bold">
                      {Math.round(shadow.match_rate * 100)}% match
                    </span>
                  </div>
                )}
              </div>

              <div className="p-4">
                {shadow ? (
                  <div className="mb-4 grid grid-cols-2 gap-3">
                    <div className="panel-muted flex flex-col items-center justify-center p-4 text-center shadow-sm">
                      <p className="text-3xl font-bold tracking-tight text-[var(--text-primary)]">{shadow.avg_latency_improvement_ms}ms</p>
                      <p className="mt-1 text-[10px] font-bold uppercase tracking-wider text-[var(--text-muted)]">Avg Speed Gain</p>
                    </div>
                    <div className="panel-muted flex flex-col items-center justify-center p-4 text-center shadow-sm">
                      <p className="text-3xl font-bold tracking-tight text-[var(--text-primary)]">{Math.round(shadow.match_rate * 100)}%</p>
                      <p className="mt-1 text-[10px] font-bold uppercase tracking-wider text-[var(--text-muted)]">Logic Parity</p>
                    </div>
                  </div>
                ) : (
                  <div className="mb-4 flex items-start gap-3 rounded-xl border border-dashed border-[var(--border-subtle)] p-4">
                    <div className="mt-1 h-3 w-3 rounded-full bg-[var(--accent)] animate-pulse" />
                    <p className="text-sm leading-relaxed text-[var(--text-muted)]">
                      Simulate a shadow execution to verify deterministic results match AI output before applying the patch.
                      This runs the logic in parallel and compares outputs.
                    </p>
                  </div>
                )}

                <div className="flex flex-wrap items-center gap-3">
                  <button
                    className="btn-primary group flex items-center gap-2 px-6 py-2.5 text-xs font-bold uppercase tracking-widest shadow-lg shadow-[var(--accent-soft)] disabled:cursor-not-allowed disabled:opacity-40"
                    onClick={runShadow}
                    disabled={!selected}
                    type="button"
                  >
                    <Activity className="h-4 w-4 transition-transform group-hover:scale-110" />
                    Run Shadow
                  </button>
                  <button
                    className="btn-secondary group flex items-center gap-2 px-6 py-2.5 text-xs font-bold uppercase tracking-widest shadow-sm disabled:cursor-not-allowed disabled:opacity-40"
                    onClick={applyPatch}
                    disabled={!selected}
                    type="button"
                  >
                    <Code className="h-4 w-4 transition-transform group-hover:scale-110" />
                    Apply
                  </button>
                  <button
                    className="btn-ghost px-6 py-2.5 text-xs font-bold uppercase tracking-widest disabled:cursor-not-allowed disabled:opacity-40"
                    onClick={revertPatch}
                    disabled={!selected}
                    type="button"
                  >
                    Revert
                  </button>
                </div>

                {message && (
                  <div className="mt-5 rounded-xl border border-[var(--border-subtle)] bg-[var(--surface-2)] p-4 text-[11px] font-medium leading-relaxed text-[var(--text-secondary)]">
                    <span className="mr-2 text-[var(--accent)] font-bold uppercase tracking-tighter">Event:</span>
                    {message}
                  </div>
                )}
              </div>
            </div>
          </section>
        </div>
      </Layout>
    </div>
  );
}

export default App;
