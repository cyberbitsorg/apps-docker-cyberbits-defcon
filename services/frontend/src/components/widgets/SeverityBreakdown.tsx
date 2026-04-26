import { cn } from "../../lib/utils";
import type { Article } from "../../types/article";

interface SeverityBreakdownProps {
  articles: Article[];
  activeSeverity: string | null;
  onSeverityClick: (label: string) => void;
}

const LEVELS = [
  { min: 80, color: "#dc2626", bg: "bg-red-600",    label: "Critical" },
  { min: 60, color: "#ea580c", bg: "bg-orange-600", label: "High"     },
  { min: 40, color: "#f59e0b", bg: "bg-amber-500",  label: "Elevated" },
  { min: 20, color: "#3b82f6", bg: "bg-blue-500",   label: "Guarded"  },
  { min: 0,  color: "#22c55e", bg: "bg-green-500",  label: "Low"      },
];

export function SeverityBreakdown({ articles, activeSeverity, onSeverityClick }: SeverityBreakdownProps) {
  const scored = articles.filter((a) => a.defcon_score > 0);
  const total = scored.length;

  const counts = LEVELS.map((level) => ({
    ...level,
    count: scored.filter((a) => {
      const s = a.defcon_score;
      if (level.min === 80) return s >= 80;
      if (level.min === 60) return s >= 60 && s < 80;
      if (level.min === 40) return s >= 40 && s < 60;
      if (level.min === 20) return s >= 20 && s < 40;
      return s > 0 && s < 20;
    }).length,
  }));

  return (
    <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white/60 dark:bg-gray-900/40 p-4">
      <h3 className="text-xs font-semibold tracking-widest uppercase text-gray-500 mb-3">
        Severity Breakdown
      </h3>

      {total > 0 && (
        <div className="flex h-2 rounded-full overflow-hidden mb-3">
          {counts.map((level) =>
            level.count > 0 ? (
              <div
                key={level.label}
                className={cn(level.bg, "transition-all")}
                style={{ width: `${(level.count / total) * 100}%` }}
              />
            ) : null
          )}
        </div>
      )}

      <div className="flex flex-col gap-1.5">
        {counts.map((level) => {
          const isActive = activeSeverity === level.label;
          return (
            <button
              key={level.label}
              onClick={() => onSeverityClick(level.label)}
              className={cn(
                "flex items-center gap-2 rounded px-1.5 py-0.5 -mx-1.5 text-left transition-colors cursor-pointer",
                isActive
                  ? "bg-gray-100 dark:bg-gray-800"
                  : "hover:bg-gray-50 dark:hover:bg-gray-800/50"
              )}
            >
              <div
                className="w-2 h-2 rounded-full flex-shrink-0 transition-all"
                style={{
                  backgroundColor: level.color,
                  outline: isActive ? `2px solid ${level.color}` : undefined,
                  outlineOffset: isActive ? "2px" : undefined,
                }}
              />
              <span className={cn(
                "text-xs",
                isActive
                  ? "text-gray-900 dark:text-gray-100 font-medium"
                  : "text-gray-600 dark:text-gray-400"
              )}>
                {level.label}
              </span>
              <span className="ml-auto text-xs text-gray-400 dark:text-gray-600">{level.count}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
