import { cn } from "../../lib/utils";
import { DEFCON_LEVELS, scoreToLevel } from "../../lib/constants";
import type { Article } from "../../types/article";

interface SeverityBreakdownProps {
  articles: Article[];
  activeSeverity: string | null;
  onSeverityClick: (label: string) => void;
}

const SEVERITY_LEVELS = [
  { defcon: 1 as const },
  { defcon: 2 as const },
  { defcon: 3 as const },
  { defcon: 4 as const },
  { defcon: 5 as const },
];

export function SeverityBreakdown({ articles, activeSeverity, onSeverityClick }: SeverityBreakdownProps) {
  const total = articles.length;

  const counts = SEVERITY_LEVELS.map(({ defcon }) => ({
    defcon,
    ...DEFCON_LEVELS[defcon],
    count: articles.filter((a) => scoreToLevel(a.defcon_score) === defcon).length,
  }));

  return (
    <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white/60 dark:bg-gray-900/40 p-4">
      <h3 className="text-xs font-semibold tracking-widest uppercase text-gray-500 mb-3">
        Severity Breakdown
      </h3>

      {total > 0 && (
        <div className="flex h-2 rounded-full overflow-hidden mb-3">
          {counts.map((lvl) =>
            lvl.count > 0 ? (
              <div
                key={lvl.defcon}
                className="transition-all"
                style={{
                  width: `${(lvl.count / total) * 100}%`,
                  backgroundColor: lvl.color,
                }}
              />
            ) : null
          )}
        </div>
      )}

      <div className="flex flex-col gap-1.5">
        {counts.map((lvl) => {
          const isActive = activeSeverity === lvl.term;
          return (
            <button
              key={lvl.defcon}
              onClick={() => onSeverityClick(lvl.term)}
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
                  backgroundColor: lvl.color,
                  outline: isActive ? `2px solid ${lvl.color}` : undefined,
                  outlineOffset: isActive ? "2px" : undefined,
                  boxShadow: lvl.defcon === 1 ? "0 0 0 1px #dc2626" : undefined,
                }}
              />
              <span className={cn(
                "text-xs",
                isActive
                  ? "text-gray-900 dark:text-gray-100 font-medium"
                  : "text-gray-600 dark:text-gray-400"
              )}>
                {lvl.defcon} {lvl.term}
              </span>
              <span className="ml-auto text-xs text-gray-400 dark:text-gray-600">{lvl.count}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
