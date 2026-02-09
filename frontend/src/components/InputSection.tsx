import { FileUp, FolderOpen, GitBranch, Loader2, Play, Shield } from "lucide-react";
import { useState } from "react";

import { api } from "../api/client";

interface InputSectionProps {
  onScanStart: (scanId: number) => void;
  onError: (msg: string) => void;
  onProviderChange: (provider: string) => void;
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Unknown error";
}

export function InputSection({ onScanStart, onError, onProviderChange }: InputSectionProps) {
  const [mode, setMode] = useState<"local" | "upload" | "git">("local");
  const [path, setPath] = useState("/Users/rajatb/Developer/Random Projects/LLMinate/samples");
  const [gitUrl, setGitUrl] = useState("https://github.com/example/repo.git");
  const [apiKey, setApiKey] = useState("");
  const [provider, setProvider] = useState<"none" | "openai" | "anthropic" | "gemini">("none");
  const [loading, setLoading] = useState(false);

  const handleProviderChange = (p: typeof provider) => {
    setProvider(p);
    onProviderChange(p);
  };

  const parseProvider = (value: string): typeof provider => {
    if (value === "openai" || value === "anthropic" || value === "gemini") {
      return value;
    }
    return "none";
  };

  async function handleScan() {
    setLoading(true);
    try {
      const res = await api.scan(path, { key: apiKey, provider });
      onScanStart(res.scan_id);
    } catch (error: unknown) {
      onError(errorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  async function handleGit() {
    setLoading(true);
    try {
      const res = await api.git(gitUrl, { key: apiKey, provider });
      onScanStart(res.scan_id);
    } catch (error: unknown) {
      onError(errorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    try {
      const res = await api.upload(file, { key: apiKey, provider });
      onScanStart(res.scan_id);
    } catch (error: unknown) {
      onError(errorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel p-6">
      <div className="mb-6 panel-muted p-1 sm:p-1.5">
        <div className="flex gap-1">
          <button
            onClick={() => setMode("local")}
            className={`ui-tab flex-1 px-3 py-2.5 text-xs font-semibold uppercase tracking-wider ${mode === "local" ? "ui-tab-active" : ""}`}
            type="button"
          >
            <span className="flex items-center justify-center gap-2">
              <FolderOpen className="h-4 w-4" />
              <span className="hidden sm:inline">Local Path</span>
              <span className="sm:hidden">Local</span>
            </span>
          </button>
          <button
            onClick={() => setMode("git")}
            className={`ui-tab flex-1 px-3 py-2.5 text-xs font-semibold uppercase tracking-wider ${mode === "git" ? "ui-tab-active" : ""}`}
            type="button"
          >
            <span className="flex items-center justify-center gap-2">
              <GitBranch className="h-4 w-4" />
              <span className="hidden sm:inline">Git Repo</span>
              <span className="sm:hidden">Git</span>
            </span>
          </button>
          <button
            onClick={() => setMode("upload")}
            className={`ui-tab flex-1 px-3 py-2.5 text-xs font-semibold uppercase tracking-wider ${mode === "upload" ? "ui-tab-active" : ""}`}
            type="button"
          >
            <span className="flex items-center justify-center gap-2">
              <FileUp className="h-4 w-4" />
              <span className="hidden sm:inline">Upload Zip</span>
              <span className="sm:hidden">Upload</span>
            </span>
          </button>
        </div>
      </div>

      <div className="space-y-6">
        <div className="rounded-2xl border border-[var(--accent-border)] bg-[var(--accent-soft)] p-5 transition-all duration-500">
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Shield className="h-3.5 w-3.5 text-[var(--accent)]" />
              <label className="text-[10px] font-bold uppercase tracking-widest text-[var(--text-primary)]">AI Credentials</label>
            </div>
            <select
              value={provider}
              onChange={(e) => handleProviderChange(parseProvider(e.target.value))}
              className="cursor-pointer bg-transparent text-[11px] font-bold uppercase tracking-widest text-[var(--accent)] outline-none hover:brightness-110"
            >
              <option value="none" className="bg-[var(--surface-2)]">Default</option>
              <option value="openai" className="bg-[var(--surface-2)]">OpenAI</option>
              <option value="anthropic" className="bg-[var(--surface-2)]">Claude</option>
              <option value="gemini" className="bg-[var(--surface-2)]">Gemini</option>
            </select>
          </div>
          <div className="relative">
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              className="ui-input h-10 border-transparent bg-[var(--surface-1)]/50 pr-10 text-xs backdrop-blur-sm focus:border-[var(--accent-border)] focus:bg-[var(--surface-1)]"
              placeholder="API Key (Optional Override)"
            />
            {apiKey && (
              <div className="absolute right-3 top-1/2 -translate-y-1/2">
                <div className="h-1.5 w-1.5 rounded-full bg-[var(--accent)] shadow-sm animate-pulse" />
              </div>
            )}
          </div>
        </div>

        {mode === "local" && (
          <div className="space-y-2">
            <label className="ui-label">Filesystem Path</label>
            <input
              type="text"
              value={path}
              onChange={(e) => setPath(e.target.value)}
              className="ui-input font-mono"
              placeholder="/path/to/project"
            />
            <p className="px-1 text-[11px] text-[var(--text-muted)] italic">Enter the absolute path to your local project.</p>
          </div>
        )}

        {mode === "git" && (
          <div className="space-y-2">
            <label className="ui-label">Git Repository URL</label>
            <input
              type="text"
              value={gitUrl}
              onChange={(e) => setGitUrl(e.target.value)}
              className="ui-input font-mono"
              placeholder="https://github.com/username/repo.git"
            />
            <p className="px-1 text-[11px] text-[var(--text-muted)] italic">The repository is cloned to a temporary local directory.</p>
          </div>
        )}

        {mode === "upload" && (
          <div className="space-y-2">
            <label className="ui-label">Upload Project Archive</label>
            <div className="relative flex w-full items-center justify-center rounded-xl border-2 border-dashed border-[var(--border-subtle)] bg-[var(--surface-2)] p-10 transition-colors hover:bg-[var(--surface-3)]">
              <div className="text-center">
                <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-[var(--surface-3)]">
                  <FileUp className="h-6 w-6 text-[var(--text-muted)]" />
                </div>
                <p className="text-sm font-medium text-[var(--text-primary)]">Drop your .zip here</p>
                <p className="mt-1 text-xs text-[var(--text-muted)]">Max file size: 50MB.</p>
                <input
                  type="file"
                  accept=".zip"
                  onChange={handleUpload}
                  className="absolute inset-0 h-full w-full cursor-pointer opacity-0"
                />
              </div>
            </div>
          </div>
        )}

        <div className="pt-2">
          {mode === "local" && (
            <button
              onClick={handleScan}
              disabled={loading}
              className="btn-primary group flex w-full items-center justify-center gap-3 px-4 py-3.5 text-sm font-bold shadow-lg shadow-[var(--accent-soft)] disabled:cursor-not-allowed disabled:opacity-60"
              type="button"
            >
              {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Play className="h-5 w-5 fill-current" />}
              {loading ? "Scanning Assets..." : "Start Analysis"}
            </button>
          )}

          {mode === "git" && (
            <button
              onClick={handleGit}
              disabled={loading}
              className="btn-primary group flex w-full items-center justify-center gap-3 px-4 py-3.5 text-sm font-bold shadow-lg shadow-[var(--accent-soft)] disabled:cursor-not-allowed disabled:opacity-60"
              type="button"
            >
              {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : <GitBranch className="h-5 w-5" />}
              {loading ? "Cloning Repository..." : "Clone & Scan"}
            </button>
          )}
        </div>
      </div>
    </section>
  );
}
