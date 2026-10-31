import type { MonthlyMetrics, Stats } from "@/api/types";
import { monthSlots, percent } from "@/lib/schedule";
import styles from "./Trends.module.css";

// Held-out test set results for the model in production (see the model card).
const TEST_SET = { n: 12114, recall: 0.978 };

type Props = { months: MonthlyMetrics[]; byScheme: Stats["latest_by_scheme"] | null };

export function Trends({ months, byScheme }: Props) {
  const slots = monthSlots(months);
  const bars = [
    { label: `Held-out test set, ${TEST_SET.n.toLocaleString("en-US")} URLs`, share: TEST_SET.recall, tone: styles.test },
    { label: `Live HTTP phishing, ${byScheme?.http?.n ?? "…"} URLs`, share: byScheme?.http?.recall, tone: styles.http },
    { label: `Live HTTPS phishing, ${byScheme?.https?.n ?? "…"} URLs`, share: byScheme?.https?.recall, tone: styles.https },
  ];

  return (
    <section className={styles.trends}>
      <div className={styles.column}>
        <div className={styles.header}>
          <h2 className={styles.title}>Live phishing caught, month by month</h2>
          <p className={styles.note}>A shrinking bar means the model is going stale and needs retraining.</p>
        </div>
        <div className={styles.chart} role="img" aria-label={slots.filter((s) => s.recall != null).map((s) => `${s.label}: ${percent(s.recall!)}`).join(", ") || "No monthly runs yet"}>
          {slots.map((slot, i) => (
            <div key={slot.key} className={styles.slot}>
              {slot.recall != null ? (
                <>
                  <span className={styles.value}>{percent(slot.recall)}</span>
                  <div className={styles.bar} style={{ height: `${slot.recall * 100}%` }} />
                </>
              ) : (
                <div className={`${styles.placeholder} ${i === slots.findIndex((s) => s.next) ? styles.upcoming : ""}`} />
              )}
            </div>
          ))}
        </div>
        <div className={styles.labels} aria-hidden="true">
          {slots.map((slot) => (
            <span key={slot.key}>{slot.label}</span>
          ))}
        </div>
      </div>

      <div className={styles.column}>
        <div className={styles.header}>
          <h2 className={styles.title}>The HTTPS blind spot</h2>
          <p className={styles.note}>Only 8% of malicious URLs in the training data used HTTPS, so Pawny learned to trust the padlock.</p>
        </div>
        <div className={styles.compare}>
          {bars.map((bar) => (
            <div key={bar.label} className={styles.row}>
              <div className={styles.rowHead}>
                <span>{bar.label}</span>
                <span className={styles.rowValue}>{bar.share == null ? "…" : percent(bar.share)}</span>
              </div>
              <div className={styles.track}>
                <div className={`${styles.fill} ${bar.tone}`} style={{ width: `${(bar.share ?? 0) * 100}%` }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
