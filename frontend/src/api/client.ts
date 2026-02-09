import type { Candidate, Patch, ShadowResult } from "../types";

const BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";
const AUTH = import.meta.env.VITE_LOCAL_AUTH_TOKEN ?? "local-dev";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-Local-Auth": AUTH,
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) {
    throw new Error(await res.text());
  }
  return (await res.json()) as T;
}

export const api = {
  scan: (path: string) => req<{ scan_id: number; status: string }>("/api/scan", { method: "POST", body: JSON.stringify({ path }) }),
  status: (scanId: number) => req<{ scan_id: number; status: string; progress: number; logs: string }>(`/api/status/${scanId}`),
  results: (scanId: number) => req<Candidate[]>(`/api/results/${scanId}`),
  patch: (scanId: number, candidateId: number) => req<Patch>(`/api/patch/${scanId}/${candidateId}`),
  shadow: (scanId: number, candidateId: number) => req<ShadowResult>(`/api/shadow-run/${scanId}/${candidateId}`, { method: "POST" }),
  apply: (scanId: number, candidateId: number) => req<{ status: string; branch: string }>(`/api/apply/${scanId}/${candidateId}?safety_flag=true`, { method: "POST" }),
  revert: (scanId: number, candidateId: number) => req<{ status: string; branch: string }>(`/api/revert/${scanId}/${candidateId}`, { method: "POST" }),
};
