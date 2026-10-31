import { Footer } from "@/components/Footer/Footer";
import { Navbar } from "@/components/Navbar/Navbar";
import { useStats } from "@/hooks/useStats";
import { CheckupHero } from "./sections/CheckupHero/CheckupHero";
import { Headline } from "./sections/Headline/Headline";
import styles from "./StatsPage.module.css";
import { Trends } from "./sections/Trends/Trends";
import { VersionHistory } from "./sections/VersionHistory/VersionHistory";

export function StatsPage() {
  const state = useStats();
  const stats = state.status === "ready" ? state.stats : null;
  const latest = stats?.months.at(-1) ?? null;

  return (
    <>
      <Navbar
        tight
        links={[
          { href: "/", label: "Try a link", hideOnSmall: true },
          { href: "/stats/", label: "Check-up", current: true },
        ]}
      />
      <main className={styles.main}>
        <CheckupHero latest={latest} modelVersion={stats?.model_version ?? null} />
        {state.status === "error" && (
          <p className={styles.notice} role="status">
            Live numbers are unavailable right now. The model facts below are still current.
          </p>
        )}
        <Headline latest={latest} />
        <Trends months={stats?.months ?? []} byScheme={stats?.latest_by_scheme ?? null} />
        <VersionHistory apiUrls={latest?.api_urls ?? null} />
      </main>
      <Footer credit="Live phishing from the OpenPhish community feed. Legit pages from Tranco and Common Crawl." />
    </>
  );
}
