import { Footer } from "@/components/Footer/Footer";
import { Navbar } from "@/components/Navbar/Navbar";
import { Pawny } from "@/components/Pawny/Pawny";

export function StatsPage() {
  return (
    <>
      <Navbar
        tight
        links={[
          { href: "/", label: "Try a link" },
          { href: "/stats/", label: "Check-up", current: true },
        ]}
      />
      <main style={{ display: "flex", justifyContent: "center", padding: 48 }}>
        <Pawny mood="scanning" size={210} />
      </main>
      <Footer credit="Live phishing from the OpenPhish community feed. Legit pages from Tranco and Common Crawl." />
    </>
  );
}
