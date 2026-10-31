import { useEffect, useState } from "react";
import { fetchStats } from "@/api/client";
import type { Stats } from "@/api/types";

export type StatsState =
  | { status: "loading" }
  | { status: "ready"; stats: Stats }
  | { status: "error" };

export function useStats(): StatsState {
  const [state, setState] = useState<StatsState>({ status: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    fetchStats(controller.signal)
      .then((stats) => setState({ status: "ready", stats }))
      .catch((err) => {
        if (!(err instanceof DOMException && err.name === "AbortError")) setState({ status: "error" });
      });
    return () => controller.abort();
  }, []);

  return state;
}
