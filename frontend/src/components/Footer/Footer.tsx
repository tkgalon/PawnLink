import { GITHUB_URL } from "@/components/Navbar/Navbar";
import styles from "./Footer.module.css";

export const MODEL_CARD_URL = `${GITHUB_URL}/blob/main/MODEL_CARD.md`;

export function Footer({ credit }: { credit: string }) {
  return (
    <footer className={styles.footer}>
      <div className={styles.inner}>
        <span>{credit}</span>
        <div className={styles.links}>
          <a href={MODEL_CARD_URL}>Model card</a>
          <a href={GITHUB_URL}>GitHub</a>
        </div>
      </div>
    </footer>
  );
}
