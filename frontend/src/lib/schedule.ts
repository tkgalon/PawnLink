const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** "2026-10-30" as a calendar date, without the local timezone shifting the day. */
function parse(isoDate: string) {
  const [year, month, day] = isoDate.split("-").map(Number);
  return { year, month: month - 1, day };
}

export function formatDate(isoDate: string): string {
  const { year, month, day } = parse(isoDate);
  return `${day} ${MONTHS[month]} ${year}`;
}

/** Cloud Scheduler starts the monthly job at 02:00 WIB on the 1st. */
export function nextRun(lastRun: string): string {
  const { year, month } = parse(lastRun);
  const next = new Date(Date.UTC(year, month + 1, 1));
  return `1 ${MONTHS[next.getUTCMonth()]} ${next.getUTCFullYear()}, 02:00 WIB`;
}

export type MonthSlot = { key: string; label: string; recall: number | null; next: boolean };

/**
 * Columns for the month-by-month chart: every run so far, then empty slots for the
 * coming months up to `columns`. The year is shown on the first column and on January.
 */
export function monthSlots(runs: { run_date: string; openphish_recall: number }[], columns = 4): MonthSlot[] {
  if (runs.length === 0) return [];
  const first = parse(runs[0].run_date);
  const count = Math.max(columns, runs.length + 1);
  return Array.from({ length: count }, (_, i) => {
    const date = new Date(Date.UTC(first.year, first.month + i, 1));
    const m = date.getUTCMonth();
    const run = runs[i];
    const isNext = i === runs.length;
    const name = i === 0 || m === 0 ? `${MONTHS[m]} ${date.getUTCFullYear()}` : MONTHS[m];
    return {
      key: `${date.getUTCFullYear()}-${m}`,
      label: isNext ? `${name}, next` : name,
      recall: run ? run.openphish_recall : null,
      next: isNext,
    };
  });
}

export const percent = (share: number) => `${(share * 100).toFixed(1)}%`;
