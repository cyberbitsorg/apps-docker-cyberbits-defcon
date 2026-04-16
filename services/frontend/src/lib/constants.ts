export const SOURCE_COLORS: Record<string, string> = {
  bleeping_computer: "#f59e0b",  // amber
  dark_reading: "#6366f1",       // indigo
  help_net_security: "#8b5cf6",  // violet
  security_week: "#10b981",      // emerald
  the_hacker_news: "#e11d48",    // rose
};

export const SOURCE_LABELS: Record<string, string> = {
  bleeping_computer: "BC",
  dark_reading: "DR",
  help_net_security: "HNS",
  security_week: "SW",
  the_hacker_news: "THN",
};

export const DEFCON_LEVELS = {
  1: { label: "LOW", color: "#22c55e", bg: "bg-green-500/10", border: "border-green-500/30", text: "text-green-400" },
  2: { label: "GUARDED", color: "#3b82f6", bg: "bg-blue-500/10", border: "border-blue-500/30", text: "text-blue-400" },
  3: { label: "ELEVATED", color: "#f59e0b", bg: "bg-amber-500/10", border: "border-amber-500/30", text: "text-amber-400" },
  4: { label: "HIGH", color: "#ea580c", bg: "bg-orange-600/10", border: "border-orange-600/30", text: "text-orange-400" },
  5: { label: "CRITICAL", color: "#dc2626", bg: "bg-red-600/10", border: "border-red-600/30", text: "text-red-400" },
} as const;
