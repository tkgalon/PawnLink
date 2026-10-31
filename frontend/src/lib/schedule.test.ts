import { describe, expect, it } from "vitest";
import { formatDate, monthSlots, nextRun, percent } from "./schedule";

describe("schedule", () => {
  it("formats run dates the way the page shows them", () => {
    expect(formatDate("2026-10-30")).toBe("30 Oct 2026");
  });

  it("puts the next run on the 1st of the following month", () => {
    expect(nextRun("2026-10-30")).toBe("1 Nov 2026, 02:00 WIB");
    expect(nextRun("2026-12-01")).toBe("1 Jan 2027, 02:00 WIB");
  });

  it("lays out one run and three upcoming months", () => {
    const slots = monthSlots([{ run_date: "2026-10-30", openphish_recall: 0.68 }]);
    expect(slots.map((s) => s.label)).toEqual(["Oct 2026", "Nov, next", "Dec", "Jan 2027"]);
    expect(slots.map((s) => s.recall)).toEqual([0.68, null, null, null]);
    expect(slots.map((s) => s.next)).toEqual([false, true, false, false]);
  });

  it("keeps a slot for the next run once four months exist", () => {
    const runs = ["2026-10-30", "2026-11-01", "2026-12-01", "2027-01-01"].map((run_date) => ({
      run_date,
      openphish_recall: 0.7,
    }));
    expect(monthSlots(runs)).toHaveLength(5);
  });

  it("rounds shares to one decimal", () => {
    expect(percent(0.5523809)).toBe("55.2%");
    expect(percent(0.68)).toBe("68.0%");
  });
});
