import styles from "./HowItReads.module.css";

function Ruler() {
  return (
    <svg className={styles.illo} viewBox="0 0 180 150" role="img" aria-label="A URL ribbon laid along a ruler">
      <circle cx="90" cy="75" r="70" fill="#7CB5F8" />
      <rect x="22" y="58" width="136" height="34" rx="10" fill="#F9F8F3" stroke="#2B2350" strokeWidth="3" />
      <rect x="30" y="66" width="24" height="18" rx="5" fill="#F7B951" />
      <rect x="58" y="66" width="44" height="18" rx="5" fill="#2B2350" />
      <rect x="106" y="66" width="18" height="18" rx="5" fill="#97D65B" />
      <rect x="128" y="66" width="22" height="18" rx="5" fill="#FF8585" />
      <rect x="28" y="100" width="124" height="20" rx="5" fill="#F7B951" stroke="#2B2350" strokeWidth="3" />
      <path d="M44 100v8M60 100v12M76 100v8M92 100v12M108 100v8M124 100v12M140 100v8" stroke="#2B2350" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  );
}

function Trees() {
  return (
    <svg className={styles.illo} viewBox="0 0 180 150" role="img" aria-label="Three little trees holding up ballots">
      <circle cx="90" cy="75" r="70" fill="#97D65B" />
      <rect x="48" y="96" width="8" height="26" rx="3" fill="#2B2350" />
      <circle cx="52" cy="84" r="20" fill="#F9F8F3" stroke="#2B2350" strokeWidth="3" />
      <rect x="86" y="88" width="8" height="34" rx="3" fill="#2B2350" />
      <circle cx="90" cy="70" r="26" fill="#F9F8F3" stroke="#2B2350" strokeWidth="3" />
      <rect x="124" y="96" width="8" height="26" rx="3" fill="#2B2350" />
      <circle cx="128" cy="84" r="20" fill="#F9F8F3" stroke="#2B2350" strokeWidth="3" />
      <rect x="80" y="28" width="22" height="16" rx="3" fill="#FF8585" stroke="#2B2350" strokeWidth="2.5" />
      <rect x="116" y="50" width="20" height="14" rx="3" fill="#F7B951" stroke="#2B2350" strokeWidth="2.5" />
      <path d="M28 124h124" stroke="#2B2350" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}

function Logbook() {
  return (
    <svg className={styles.illo} viewBox="0 0 180 150" role="img" aria-label="An open logbook with a stamp">
      <circle cx="90" cy="75" r="70" fill="#FF8585" />
      <path d="M30 46 Q60 38 90 48 Q120 38 150 46 L150 118 Q120 110 90 120 Q60 110 30 118 Z" fill="#F9F8F3" stroke="#2B2350" strokeWidth="3" strokeLinejoin="round" />
      <path d="M90 48 L90 120" stroke="#2B2350" strokeWidth="3" />
      <path d="M42 62h36M42 74h30M42 86h34M102 62h36M102 74h24" stroke="#2B2350" strokeWidth="2.5" strokeLinecap="round" />
      <circle cx="122" cy="96" r="14" fill="#7CB5F8" stroke="#2B2350" strokeWidth="3" />
      <path d="M116 96l4 4 8-8" fill="none" stroke="#2B2350" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

const STOPS = [
  {
    Illustration: Ruler,
    title: "1. Measure it",
    text: "The URL becomes 23 numbers: length, digits, entropy, HTTPS, subdomains, TLD and file type. Training and the API share this exact code.",
  },
  {
    Illustration: Trees,
    title: "2. Let 172 trees vote",
    text: "A LightGBM model trained on 62,343 URLs adds up the votes into one risk score between 0 and 1.",
  },
  {
    Illustration: Logbook,
    title: "3. Stamp and log it",
    text: "0.38 or above gets flagged. Every verdict lands in BigQuery, where a monthly job checks whether the world has drifted.",
  },
];

export function HowItReads() {
  return (
    <section id="how" className={styles.section}>
      <div className={styles.intro}>
        <h2 className={styles.title}>How Pawny reads a link</h2>
        <p className={styles.lead}>No page visits, no screenshots. Just the characters in the URL, in about a millisecond.</p>
      </div>
      <div className={styles.path}>
        <svg className={styles.road} aria-hidden="true" viewBox="0 0 1100 120" preserveAspectRatio="none">
          <path d="M60 60 C260 -20 360 140 550 60 S 860 -20 1040 60" fill="none" stroke="#2B2350" strokeWidth="4" strokeDasharray="2 14" strokeLinecap="round" />
        </svg>
        <ol className={styles.stops}>
          {STOPS.map(({ Illustration, title, text }, i) => (
            <li key={title} className={styles.stop}>
              {i > 0 && <span className={styles.connector} aria-hidden="true" />}
              <Illustration />
              <div className={styles.text}>
                <h3 className={styles.stopTitle}>{title}</h3>
                <p className={styles.stopText}>{text}</p>
              </div>
            </li>
          ))}
        </ol>
      </div>
      <p className={styles.ways}>
        <span>Ask Pawny three ways:</span>{" "}
        <span className={styles.chips}>
          <span className={styles.chip}>REST API</span> <span className={styles.chip}>Pub/Sub stream</span>{" "}
          <span className={styles.chip}>monthly batch</span>
        </span>
      </p>
    </section>
  );
}
