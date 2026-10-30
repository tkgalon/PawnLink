import { Footer } from "../../components/Footer/Footer";
import { Navbar } from "../../components/Navbar/Navbar";
import { type Mood, Pawny } from "../../components/Pawny/Pawny";

const MOODS: Mood[] = ["idle", "hit", "scanning", "safe", "phishy", "miss"];

export function MainPage() {
  return (
    <>
      <Navbar
        links={[
          { href: "#how", label: "How Pawny reads" },
          { href: "/stats/", label: "Check-up" },
        ]}
      />
      <main style={{ display: "flex", flexWrap: "wrap", gap: 24, padding: 48, justifyContent: "center" }}>
        {MOODS.map((mood) => (
          <figure key={mood} style={{ margin: 0, textAlign: "center", fontFamily: "var(--font-display)" }}>
            <Pawny mood={mood} size={150} />
            <figcaption>{mood}</figcaption>
          </figure>
        ))}
      </main>
      <Footer credit="Trained on LegitPhish (Mendeley Data, CC BY 4.0), Tranco and Common Crawl." />
    </>
  );
}
