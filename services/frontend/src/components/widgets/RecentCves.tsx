import { useMemo } from "react";
import type { Article } from "../../types/article";

interface RecentCvesProps {
  articles: Article[];
}

const CVE_RE = /\bCVE-\d{4}-\d{4,}\b/gi;

function extractCves(articles: Article[]) {
  const seen = new Map<string, number>();
  for (const a of articles) {
    const text = `${a.title} ${a.summary}`;
    const matches = text.matchAll(CVE_RE);
    for (const m of matches) {
      const id = m[0].toUpperCase();
      seen.set(id, (seen.get(id) || 0) + 1);
    }
  }
  return Array.from(seen.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 12);
}

export function RecentCves({ articles }: RecentCvesProps) {
  const cves = useMemo(() => extractCves(articles), [articles]);

  if (cves.length === 0) return null;

  return (
    <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white/60 dark:bg-gray-900/40 p-4">
      <h3 className="text-xs font-semibold tracking-widest uppercase text-gray-500 mb-3">
        Recent CVE Mentions
      </h3>
      <div className="flex flex-wrap gap-1.5">
        {cves.map(([id, count]) => (
          <a
            key={id}
            href={`https://nvd.nist.gov/vuln/detail/${id}`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-blue-50 dark:hover:bg-blue-900/30 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
          >
            {id}
            {count > 1 && (
              <span className="text-[9px] font-bold text-gray-400 dark:text-gray-600">{count}</span>
            )}
          </a>
        ))}
      </div>
    </div>
  );
}
