import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { type Mood, Pawny } from "./Pawny";

const MOODS: Mood[] = ["idle", "hit", "scanning", "safe", "phishy", "miss"];

describe("Pawny", () => {
  it.each(MOODS)("names the %s mood for screen readers", (mood) => {
    const html = renderToStaticMarkup(<Pawny mood={mood} />);
    expect(html).toContain('role="img"');
    expect(html).toMatch(/aria-label="Pawny, /);
  });

  it("hides the decorative logo copy", () => {
    const html = renderToStaticMarkup(<Pawny decorative size={36} />);
    expect(html).toContain('aria-hidden="true"');
    expect(html).not.toContain("role=");
  });

  it("keeps the 5:6 frame at any size", () => {
    const html = renderToStaticMarkup(<Pawny size={290} />);
    expect(html).toContain('width="290"');
    expect(html).toContain('height="348"');
  });

  it("parks the loupe on his head in every mood but hit", () => {
    for (const mood of MOODS) {
      const html = renderToStaticMarkup(<Pawny mood={mood} />);
      expect(html.includes('cx="152" cy="34"')).toBe(mood !== "hit");
    }
  });
});
