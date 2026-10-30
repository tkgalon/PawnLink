import { MODEL_CARD_URL } from "@/components/Footer/Footer";
import { Pawny } from "@/components/Pawny/Pawny";
import { describe } from "@/lib/reasons";
import styles from "./ScanResult.module.css";
import type { ScanState } from "@/hooks/useScan";

// The model reads these parts; each kind keeps one brick color.
const BRICK: Record<string, string> = {
  scheme: "var(--brick-scheme)",
  userinfo: "var(--brick-subdomain)",
  subdomain: "var(--brick-subdomain)",
  domain: "var(--brick-domain)",
  host: "var(--brick-domain)",
  TLD: "var(--brick-tld)",
  port: "var(--brick-tld)",
  path: "var(--brick-path)",
  query: "var(--brick-query)",
  fragment: "var(--brick-query)",
};

// SHAP bars are drawn on a fixed scale so lengths compare across URLs.
const FULL_PULL = 4;
const REASONS_SHOWN = 4;

function LoupeIcon() {
  return (
    <svg className={styles.loupe} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" aria-hidden="true">
      <circle cx="10" cy="10" r="6.5" fill="var(--honey)" />
      <path d="M15 15l5.5 5.5" />
    </svg>
  );
}

export function ScanResult({ state, miss }: { state: ScanState; miss: boolean }) {
  const { phase, step, prediction } = state;
  if (!prediction || (phase !== "scanning" && phase !== "result")) return null;

  const parts = prediction.parts ?? [];
  const reasons = (prediction.reasons ?? []).slice(0, REASONS_SHOWN);
  const flagLine = `${prediction.threshold * 100}%`;

  return (
    <section className={styles.card} aria-live="polite">
      <div className={styles.read}>
        <h2 className={styles.heading}>What Pawny read</h2>
        <div className={styles.bricks}>
          {parts.map((part, i) => {
            const lit = phase === "result" || i < step;
            const current = phase === "scanning" && i === step;
            return (
              <div key={`${i}-${part.text}`} className={styles.brickSlot}>
                {current ? <LoupeIcon /> : <span className={styles.loupeSpace} />}
                <span
                  className={`${styles.brick} ${lit ? `brick-in ${styles.lit}` : ""}`}
                  style={lit ? { background: BRICK[part.kind] ?? "var(--white)" } : undefined}
                >
                  {part.text}
                </span>
                <span className={styles.kind}>{part.kind}</span>
              </div>
            );
          })}
        </div>
      </div>

      {phase === "result" && (
        <div className={styles.verdict}>
          <div className={styles.meterColumn}>
            <h2 className={styles.heading}>Risk meter</h2>
            <div className={styles.scoreRow}>
              <span className={styles.score}>{prediction.score.toFixed(2)}</span>
              <span className={`${styles.badge} ${prediction.is_phishing ? styles.risky : styles.safe}`}>
                {prediction.is_phishing ? "Sketchy" : "Looks safe"}
              </span>
            </div>
            <div className={styles.meter}>
              <div className={`needle ${styles.needle}`} style={{ left: `${prediction.score * 100}%` }}>
                <span className={styles.pin}>{prediction.score.toFixed(2)}</span>
                <span className={styles.pinTip} />
              </div>
              <div className={styles.track}>
                <div className={styles.safeZone} style={{ width: flagLine }} />
                <div className={styles.riskZone} />
              </div>
              <div className={styles.scale}>
                <span>0 · safe</span>
                <span className={styles.flag} style={{ left: flagLine }}>
                  flag line {prediction.threshold.toFixed(2)}
                </span>
                <span>sketchy · 1</span>
              </div>
            </div>
            <p className={styles.url}>{prediction.url}</p>
            {miss && (
              <div className={styles.miss}>
                <span className={styles.missPawny}>
                  <Pawny mood="miss" size={64} decorative />
                </span>
                <p>
                  <strong>Known miss.</strong> Real phishing from the OpenPhish feed. v4 trusts HTTPS too much
                  and catches only 55% of HTTPS phishing. <a href={MODEL_CARD_URL}>Model card</a>
                </p>
              </div>
            )}
          </div>

          <div className={styles.tugColumn}>
            <h2 className={styles.heading}>Who pulled the score?</h2>
            <div className={styles.legend}>
              <span>
                <i className={styles.safeKey} />
                toward safe
              </span>
              <span>
                toward sketchy
                <i className={styles.riskKey} />
              </span>
            </div>
            <ul className={styles.tug}>
              {reasons.map((reason) => {
                const width = `${Math.min(Math.abs(reason.contribution) / FULL_PULL, 1) * 100}%`;
                const towardSafe = reason.contribution < 0;
                return (
                  <li key={reason.feature} className={styles.reason}>
                    <span className={towardSafe ? styles.labelSafe : styles.labelRisk}>{describe(reason)}</span>
                    <span className={styles.bars}>
                      <span className={styles.half} style={{ justifyContent: "flex-end" }}>
                        {towardSafe && <span className={`${styles.bar} ${styles.barSafe}`} style={{ width }} />}
                      </span>
                      <span className={styles.rope} aria-hidden="true" />
                      <span className={styles.half}>
                        {!towardSafe && <span className={`${styles.bar} ${styles.barRisk}`} style={{ width }} />}
                      </span>
                    </span>
                  </li>
                );
              })}
            </ul>
            <p className={styles.note}>Bar length is each feature's SHAP contribution for this URL. Longer pulls harder.</p>
          </div>
        </div>
      )}
    </section>
  );
}
