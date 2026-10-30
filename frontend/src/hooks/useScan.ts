import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, appraise } from "@/api/client";
import type { Prediction } from "@/api/types";
import type { Mood } from "@/components/Pawny/Pawny";
import type { Ticket } from "@/data/tickets";

// Pawny hops, hits the button and springs back before he starts reading.
export const HIT_MS = 800;
// One URL piece lights up per step.
export const STEP_MS = 420;

export type Phase = "idle" | "hit" | "scanning" | "result" | "error";
export type ScanError = "invalid" | "offline";

export type ScanState = {
  phase: Phase;
  step: number;
  prediction: Prediction | null;
  ticket: Ticket | null;
  error: ScanError | null;
};

const IDLE: ScanState = { phase: "idle", step: 0, prediction: null, ticket: null, error: null };

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

const prefersReducedMotion = () =>
  typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

export function useScan() {
  const [state, setState] = useState<ScanState>(IDLE);
  // Each scan gets an id; a newer scan makes every pending step of an older one a no-op.
  const runId = useRef(0);
  const controller = useRef<AbortController | null>(null);

  useEffect(() => () => controller.current?.abort(), []);

  const scan = useCallback(async (url: string, ticket: Ticket | null = null) => {
    const id = ++runId.current;
    controller.current?.abort();
    controller.current = new AbortController();
    const stale = () => id !== runId.current;
    const reduced = prefersReducedMotion();

    setState({ ...IDLE, phase: "hit", ticket });
    const request = appraise(url, controller.current.signal);

    let prediction: Prediction;
    try {
      [prediction] = await Promise.all([request, wait(reduced ? 0 : HIT_MS)]);
    } catch (err) {
      if (stale() || (err instanceof DOMException && err.name === "AbortError")) return;
      const error = err instanceof ApiError && err.status === 422 ? "invalid" : "offline";
      setState({ ...IDLE, phase: "error", ticket, error });
      return;
    }
    if (stale()) return;

    const steps = prediction.parts?.length ?? 0;
    if (!reduced) {
      for (let step = 0; step < steps; step++) {
        setState({ phase: "scanning", step, prediction, ticket, error: null });
        await wait(STEP_MS);
        if (stale()) return;
      }
    }
    setState({ phase: "result", step: steps, prediction, ticket, error: null });
  }, []);

  return { state, scan };
}

export function moodFor({ phase, prediction, ticket }: ScanState): Mood {
  if (phase === "hit" || phase === "scanning") return phase;
  if (phase !== "result" || !prediction) return "idle";
  if (ticket?.knownPhishing && !prediction.is_phishing) return "miss";
  return prediction.is_phishing ? "phishy" : "safe";
}
