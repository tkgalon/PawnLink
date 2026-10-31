import { Pawny } from "@/components/Pawny/Pawny";
import type { MonthlyMetrics } from "@/api/types";
import { formatDate, nextRun } from "@/lib/schedule";
import styles from "./CheckupHero.module.css";

const PENDING = "…";

export function CheckupHero({ latest, modelVersion }: { latest: MonthlyMetrics | null; modelVersion: string | null }) {
  return (
    <section className={styles.hero}>
      <div className={styles.text}>
        <h1 className={styles.title}>Pawny's monthly check-up</h1>
        <p className={styles.lead}>
          On the 1st of every month, Pawny is tested on phishing that is live that day and on legit pages from
          sites he has never seen.
        </p>
        <div className={styles.chips}>
          <span className={styles.chip}>Last run {latest ? formatDate(latest.run_date) : PENDING}</span>
          <span className={`${styles.chip} ${styles.next}`}>Next run {latest ? nextRun(latest.run_date) : PENDING}</span>
          <span className={styles.chip}>Model v{modelVersion ?? PENDING}</span>
        </div>
      </div>
      <div className={styles.portrait}>
        <div className={styles.circle}>
          <Pawny mood="scanning" size={210} />
        </div>
      </div>
    </section>
  );
}
