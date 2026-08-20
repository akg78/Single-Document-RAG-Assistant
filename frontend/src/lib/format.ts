/** Strip server-side UUID prefix from stored upload filenames. */
export function displayFilename(filename: string): string {
  const match = filename.match(/^[0-9a-f-]{36}_(.+)$/i);
  return match ? match[1].replace(/_/g, " ") : filename;
}

export function formatRouteType(type: string): string {
  const labels: Record<string, string> = {
    single_fact: "Direct lookup",
    multi_part: "Multi-part question",
    summarization: "Summary",
  };
  return labels[type] ?? type;
}

export function scoreTone(score: number): "low" | "mid" | "high" {
  if (score >= 0.75) return "high";
  if (score >= 0.5) return "mid";
  return "low";
}

export function clamp01(n: number): number {
  return Math.min(Math.max(n, 0), 1);
}

export function formatPercent(score: number): number {
  return Math.round(clamp01(score) * 100);
}

export function getErrorMessage(err: unknown, fallback: string): string {
  return err instanceof Error ? err.message : fallback;
}
