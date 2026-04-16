import { useMemo } from "react";

interface SourceDistributionProps {
  articles: { source: string }[];
}

const SOURCES = [
  { id: "bleeping_computer", label: "Bleeping Computer", color: "#f59e0b" },
  { id: "dark_reading",      label: "Dark Reading",      color: "#6366f1" },
  { id: "help_net_security", label: "Help Net Security", color: "#8b5cf6" },
  { id: "security_week",     label: "Security Week",     color: "#10b981" },
  { id: "the_hacker_news",   label: "The Hacker News",   color: "#e11d48" },
];

const SIZE = 64;
const STROKE = 8;
const RADIUS = (SIZE - STROKE) / 2;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

export function SourceDistribution({ articles }: SourceDistributionProps) {
  const segments = useMemo(() => {
    const total = articles.length;
    if (total === 0) return [];
    let offset = 0;
    return SOURCES.map((s) => {
      const count = articles.filter((a) => a.source === s.id).length;
      if (count === 0) return null;
      const pct = count / total;
      const dash = pct * CIRCUMFERENCE;
      const gap = CIRCUMFERENCE - dash;
      const seg = { ...s, count, pct, dasharray: `${dash} ${gap}`, dashoffset: -offset };
      offset += dash;
      return seg;
    }).filter(Boolean);
  }, [articles]);

  if (segments.length === 0) return null;

  return (
    <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white/60 dark:bg-gray-900/40 p-4">
      <h3 className="text-xs font-semibold tracking-widest uppercase text-gray-500 mb-3">
        Source Distribution
      </h3>
      <div className="flex items-center gap-4">
        <svg
          width={SIZE}
          height={SIZE}
          viewBox={`0 0 ${SIZE} ${SIZE}`}
          className="flex-shrink-0 -rotate-90"
        >
          {segments.map((s) => (
            <circle
              key={s!.id}
              cx={SIZE / 2}
              cy={SIZE / 2}
              r={RADIUS}
              fill="none"
              stroke={s!.color}
              strokeWidth={STROKE}
              strokeDasharray={s!.dasharray}
              strokeDashoffset={s!.dashoffset}
            />
          ))}
        </svg>
        <div className="flex flex-col gap-1 flex-1 min-w-0">
          {segments.map((s) => (
            <div key={s!.id} className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: s!.color }} />
              <span className="text-[11px] text-gray-600 dark:text-gray-400 truncate">{s!.label}</span>
              <span className="ml-auto text-[11px] text-gray-400 dark:text-gray-600 flex-shrink-0">
                {Math.round(s!.pct * 100)}%
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
