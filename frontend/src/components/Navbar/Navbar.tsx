import { Pawny } from "../Pawny/Pawny";
import styles from "./Navbar.module.css";

export const GITHUB_URL = "https://github.com/tkgalon/PawnLink";

type Link = { href: string; label: string; current?: boolean };

export function Navbar({ links }: { links: Link[] }) {
  return (
    <header className={styles.header}>
      <nav className={styles.nav} aria-label="Main">
        <a href="/" className={styles.logo}>
          <Pawny mood="idle" size={36} decorative />
          pawnlink
        </a>
        <div className={styles.links}>
          {links.map((link) => (
            <a
              key={link.href}
              href={link.href}
              aria-current={link.current ? "page" : undefined}
              className={link.current ? styles.current : styles.link}
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
