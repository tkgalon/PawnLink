import styles from "./ReportCard.module.css";

// Measured numbers from the model card: held-out test set, the 30 Oct 2026 live check, v3 to v4.
const ROWS = [
  { title: "Held-out test set", note: "malicious URLs caught", value: "97.8%", tone: "" },
  { title: "Live phishing, 30 Oct 2026", note: "300 OpenPhish URLs. Needs work on HTTPS", value: "68.0%", tone: "risk" },
  { title: "Legit pages with a path", note: "wrongly flagged, down from 71.8% in v3", value: "4.2%", tone: "safe" },
];

export function ReportCard() {
  return (
    <section className={styles.section}>
      <div className={styles.side}>
        <h2 className={styles.title}>Pawny's report card</h2>
        <p className={styles.lead}>Good at the test, still learning in the wild. We show both.</p>
        <a href="/stats/" className={`chunky ${styles.cta}`}>
          See the full check-up
        </a>
      </div>
      <dl className={styles.card}>
        {ROWS.map((row) => (
          <div key={row.title} className={styles.row}>
            <dt className={styles.label}>
              <span className={styles.rowTitle}>{row.title}</span>
              <span className={styles.rowNote}>{row.note}</span>
            </dt>
            <dd className={`${styles.value} ${row.tone ? styles[row.tone] : ""}`}>{row.value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
