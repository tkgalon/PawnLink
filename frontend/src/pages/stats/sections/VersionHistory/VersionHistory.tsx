import styles from "./VersionHistory.module.css";

// Gate results recorded in MLflow when v4 was promoted over v3.
const METRICS = [
  { name: "Test ROC AUC", v3: "0.9873", v4: "0.9867" },
  { name: "Test recall", v3: "98.0%", v4: "97.8%" },
  { name: "Legit URLs with a path flagged", v3: "71.8%", v4: "4.2%", highlight: true },
];

export function VersionHistory({ apiUrls }: { apiUrls: number | null }) {
  return (
    <section className={styles.history}>
      <div className={styles.main}>
        <h2 className={styles.title}>Why v4 replaced v3</h2>
        <p className={styles.note}>
          A new model only ships if AUC drops by at most 0.005, recall by at most 0.01, and fewer legit URLs get flagged.
        </p>
        <div className={styles.tableBox}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th scope="col">Metric</th>
                <th scope="col">v3</th>
                <th scope="col">v4</th>
              </tr>
            </thead>
            <tbody>
              {METRICS.map((m) => (
                <tr key={m.name}>
                  <th scope="row">{m.name}</th>
                  <td>{m.highlight ? <span className={styles.worse}>{m.v3}</span> : m.v3}</td>
                  <td>{m.highlight ? <span className={styles.better}>{m.v4}</span> : m.v4}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <dl className={styles.facts}>
        <div>
          <dt>Live traffic</dt>
          <dd>{apiUrls ?? "…"} predictions from the API and Pub/Sub in the 30 days before the last run.</dd>
        </div>
        <div>
          <dt>Where it comes from</dt>
          <dd>Cloud Scheduler starts a Cloud Run job that writes to BigQuery and saves a drift report.</dd>
        </div>
        <div>
          <dt>Next for Pawny</dt>
          <dd>v5 trains on the HTTPS phishing these runs collect.</dd>
        </div>
      </dl>
    </section>
  );
}
