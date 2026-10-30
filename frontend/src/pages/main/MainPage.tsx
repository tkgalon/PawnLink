import { useState } from "react";
import { Footer } from "@/components/Footer/Footer";
import { Navbar } from "@/components/Navbar/Navbar";
import { Hero } from "./sections/Hero/Hero";
import { HowItReads } from "./sections/HowItReads/HowItReads";
import styles from "./MainPage.module.css";
import { ReportCard } from "./sections/ReportCard/ReportCard";
import { ScanResult } from "./sections/ScanResult/ScanResult";
import type { Ticket } from "@/data/tickets";
import { moodFor, useScan } from "@/hooks/useScan";

export function MainPage() {
  const { state, scan } = useScan();
  const [url, setUrl] = useState("");
  const mood = moodFor(state);

  const pick = (ticket: Ticket) => {
    setUrl(ticket.url);
    scan(ticket.url, ticket);
  };

  return (
    <>
      <Navbar
        links={[
          { href: "#how", label: "How Pawny reads", hideOnMobile: true },
          { href: "/stats/", label: "Check-up" },
        ]}
      />
      <Hero
        state={state}
        mood={mood}
        url={url}
        onUrlChange={setUrl}
        onSubmit={() => scan(url.trim())}
        onPick={pick}
      />
      <main className={styles.main}>
        <ScanResult state={state} miss={mood === "miss"} />
        <HowItReads />
        <ReportCard />
      </main>
      <Footer credit="Trained on LegitPhish (Mendeley Data, CC BY 4.0), Tranco and Common Crawl." />
    </>
  );
}
