// VibeQueue — Utility functions

export function formatINR(amount: number): string {
  return `₹${amount.toFixed(2)}`;
}

export function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins === 1) return "1 min ago";
  if (mins < 60) return `${mins} mins ago`;
  const hrs = Math.floor(mins / 60);
  return `${hrs}h ago`;
}

export function cn(...classes: (string | false | null | undefined)[]): string {
  return classes.filter(Boolean).join(" ");
}

export function generateTableCode(): string {
  return Math.floor(100000 + Math.random() * 900000).toString();
}

export function calculateScore(boostTotal: number, minutesSinceRequest: number): number {
  if (minutesSinceRequest <= 0) return boostTotal + 10;
  return boostTotal + 10 / minutesSinceRequest;
}

export function estimatePosition(
  currentQueue: { boost_score: number }[],
  newBoostAmount: number,
  currentScore: number
): number {
  const newScore = currentScore + newBoostAmount;
  let position = 1;
  for (const entry of currentQueue) {
    if (entry.boost_score > newScore) position++;
  }
  return position;
}
