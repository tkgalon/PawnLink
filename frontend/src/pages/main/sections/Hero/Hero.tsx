import type { CSSProperties, FormEvent } from "react";
import { type Mood, Pawny } from "@/components/Pawny/Pawny";
import styles from "./Hero.module.css";
import { TICKETS, type Ticket } from "@/data/tickets";
import type { ScanState } from "@/hooks/useScan";

type Bubble = { title: string; body: string; fill: string };

const CREAM = "#F9F8F3";

function bubbleFor(state: ScanState, mood: Mood): Bubble {
  if (state.phase === "error") {
    return state.error === "invalid"
      ? { title: "That is not a link I can read.", body: "Try a full URL, like https://example.com/login.", fill: CREAM }
      : { title: "My appraisal desk is closed.", body: "I could not reach the model just now. Try again in a moment.", fill: CREAM };
  }
  switch (mood) {
    case "hit":
      return { title: "Pawn it!", body: "Got it. Let me take a closer look.", fill: CREAM };
    case "scanning":
      return { title: "Hmm, let me look...", body: "Reading it piece by piece, the same way the model does.", fill: CREAM };
    case "safe":
      return { title: "Looks clean to me!", body: "Nothing in this URL worries me much. Still, trust your gut.", fill: "#EAF6DD" };
    case "phishy":
      return {
        title: "Yikes. Do not click that.",
        body: state.ticket?.remark ?? "Parts of this URL look like the phishing I was trained on.",
        fill: "#FFE1E1",
      };
    case "miss":
      return { title: "Looks safe... I was wrong.", body: "This is real phishing from OpenPhish. The HTTPS padlock fooled me.", fill: "#FFF3DC" };
    default:
      return { title: "Hello, I'm Pawny...", body: "Hand me a link! I appraise it from the URL alone and never open the page.", fill: CREAM };
  }
}

type Props = {
  state: ScanState;
  mood: Mood;
  url: string;
  onUrlChange: (url: string) => void;
  onSubmit: () => void;
  onPick: (ticket: Ticket) => void;
};

export function Hero({ state, mood, url, onUrlChange, onSubmit, onPick }: Props) {
  const bubble = bubbleFor(state, mood);
  const busy = state.phase === "hit" || state.phase === "scanning";
  const hitting = state.phase === "hit";

  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (!busy) onSubmit();
  };

  return (
    <section id="top" className={styles.hero}>
      <div className={styles.inner}>
        <div className={styles.stage}>
          <div
            key={bubble.title}
            className={`bubble-in ${styles.bubble}`}
            style={{ "--bubble-fill": bubble.fill } as CSSProperties}
            aria-live="polite"
          >
            <p className={styles.bubbleTitle}>{bubble.title}</p>
            <p className={styles.bubbleBody}>{bubble.body}</p>
          </div>
          <div className={`${styles.pawny} ${hitting ? "pw-slam" : ""}`}>
            <Pawny mood={mood} size={290} />
          </div>
        </div>

        <form className={styles.form} onSubmit={submit}>
          <div className={`${styles.field} ${hitting ? "shake" : ""}`}>
            <label htmlFor="url" className="visually-hidden">
              Link to appraise
            </label>
            <input
              id="url"
              type="url"
              inputMode="url"
              autoComplete="off"
              spellCheck={false}
              required
              value={url}
              onChange={(e) => onUrlChange(e.target.value)}
              placeholder="Paste a link for Pawny"
              className={styles.input}
            />
            <button type="submit" className={`chunky ${styles.button}`} disabled={busy}>
              {busy ? "Reading..." : "Pawn it!"}
            </button>
          </div>
          <div className={styles.tickets}>
            <span className={styles.ticketsLabel}>Or pick a ticket:</span>
            {TICKETS.map((ticket) => {
              const picked = state.phase !== "idle" && state.ticket?.url === ticket.url;
              return (
                <button
                  key={ticket.url}
                  type="button"
                  className={`ticket ${styles.ticket} ${picked ? styles.picked : ""} ${ticket.url.length > 25 ? styles.long : ""}`}
                  onClick={() => onPick(ticket)}
                  disabled={busy}
                  title={ticket.hint}
                  aria-label={`Appraise ${ticket.url}, ${ticket.hint}`}
                >
                  <span className={styles.dot} aria-hidden="true" />
                  <span className={styles.ticketLabel}>{ticket.label}</span>
                </button>
              );
            })}
          </div>
        </form>
      </div>
      <div className={styles.board} aria-hidden="true" />
    </section>
  );
}
