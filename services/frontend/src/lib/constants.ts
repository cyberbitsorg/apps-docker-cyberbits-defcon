// Vintage / muted palette — deliberately distinct from the DEFCON warning palette
// (white / red / yellow / green / blue) so source badges don't read as severity.
export const SOURCE_COLORS: Record<string, string> = {
  bleeping_computer: "#cbd5e1",  // slate-300 — lightest
  hacker_news:       "#94a3b8",  // slate-400
  hackread:          "#64748b",  // slate-500
  security_affairs:  "#475569",  // slate-600
  the_register:      "#334155",  // slate-700 — darkest
};

export const SOURCE_LABELS: Record<string, string> = {
  bleeping_computer: "BC",
  hacker_news:       "HN",
  hackread:          "HR",
  security_affairs:  "SA",
  the_register:      "TR",
};

export const DEFCON_LEVELS = {
  1: { term: "Cocked Pistol", color: "#ffffff", bg: "bg-white/10",      border: "border-white/30",      text: "text-gray-900 dark:text-white" },
  2: { term: "Fast Pace",     color: "#dc2626", bg: "bg-red-600/10",    border: "border-red-600/30",    text: "text-red-400"     },
  3: { term: "Round House",   color: "#eab308", bg: "bg-yellow-500/10", border: "border-yellow-500/30", text: "text-yellow-400"  },
  4: { term: "Double Take",   color: "#22c55e", bg: "bg-green-500/10",  border: "border-green-500/30",  text: "text-green-400"   },
  5: { term: "Fade Out",      color: "#3b82f6", bg: "bg-blue-500/10",   border: "border-blue-500/30",   text: "text-blue-400"    },
} as const;

export function scoreToLevel(score: number): 1 | 2 | 3 | 4 | 5 {
  if (score >= 80) return 1;
  if (score >= 60) return 2;
  if (score >= 40) return 3;
  if (score >= 20) return 4;
  return 5;
}
