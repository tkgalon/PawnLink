import { Pawny } from "@/components/Pawny/Pawny";
import styles from "./Navbar.module.css";

export const GITHUB_URL = "https://github.com/tkgalon/PawnLink";

type Link = { href: string; label: string; current?: boolean; hideOnMobile?: boolean };

type Props = {
  links: Link[];
  /** Smaller type on phones, for pages with more links. */
  tight?: boolean;
};

export function Navbar({ links, tight = false }: Props) {
  return (
    <header className={`${styles.header} ${tight ? styles.tight : ""}`}>
      <nav className={styles.nav} aria-label="Main">
        <a href="/" className={styles.logo}>
          <span className={styles.logoPawny}>
            <Pawny mood="idle" size={36} decorative />
          </span>
          pawnlink
        </a>
        <div className={styles.links}>
          {links.map((link) => (
            <a
              key={link.href}
              href={link.href}
              aria-current={link.current ? "page" : undefined}
              className={`${link.current ? styles.current : styles.link} ${link.hideOnMobile ? styles.hideOnMobile : ""}`}
            >
              {link.label}
            </a>
          ))}
          <a href={GITHUB_URL} className={`chunky ${styles.github}`}>
            GitHub
          </a>
        </div>
      </nav>
    </header>
  );
}
