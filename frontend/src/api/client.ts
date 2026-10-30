import type { Prediction, Stats } from "./types";

export class ApiError extends Error {
  constructor(public status: number) {
    super(`API responded ${status}`);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init);
  if (!res.ok) throw new ApiError(res.status);
  return res.json() as Promise<T>;
}

export function appraise(url: string, signal?: AbortSignal): Promise<Prediction> {
  return request<Prediction>("/predict?explain=true", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
    signal,
  });
}

export function fetchStats(signal?: AbortSignal): Promise<Stats> {
  return request<Stats>("/api/stats", { signal });
}
