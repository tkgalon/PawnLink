import type { MonthlyMetrics } from "@/api/types";
import { percent } from "@/lib/schedule";
import styles from "./Headline.module.css";

// The monthly job samples legit pages from this many Tranco sites, ranked past the training set.
const LEGIT_SITES = 150;

export function Headline({ latest }: { latest: MonthlyMetrics | null }) {
  const value = (share: number | null | undefined) => (share == null ? "…" : percent(share));
  return (
    <section className={styles.card}>
      <p className={styles.sentence}>
        In the wild, Pawny caught <span className={styles.honey}>{value(latest?.openphish_recall)}</span> of live
        phishing. On HTTPS links that drops to{" "}
        <span className={styles.coral}>{value(latest?.openphish_https_recall)}</span>, while only{" "}
        <span className={styles.lime}>{value(latest?.legit_fpr)}</span> of legit pages got a false alarm.
      </p>
      <p className={styles.source}>
        {latest ? latest.openphish_n : "…"} phishing URLs from the OpenPhish feed and {latest ? latest.legit_n : "…"} legit
        URLs from {LEGIT_SITES} Tranco sites ranked 1,001 to 10,000.
      </p>
    </section>
  );
}
