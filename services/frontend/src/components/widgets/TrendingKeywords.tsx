import { useMemo } from "react";
import type { Article } from "../../types/article";

interface TrendingKeywordsProps {
  articles: Article[];
}

const KEYWORDS = [
  "zero-day", "zero day", "ransomware", "backdoor", "supply chain",
  "apt", "wiper", "botnet", "ddos", "rce", "remote code execution",
  "vulnerability", "exploit", "patch", "breach", "malware", "phishing",
  "trojan", "spyware", "credential", "data leak", "critical",
  "nation-state", "state-sponsored", "cryptominer", "skimmer",
  "rootkit", "keylogger", "brute force", "social engineering",
  "privilege escalation", "authentication bypass", "code execution",
];

function countKeywords(articles: Article[]) {
  const counts = new Map<string, number>();
  for (const a of articles) {
    const text = `${a.title} ${a.summary}`.toLowerCase();
    for (const kw of KEYWORDS) {
      if (text.includes(kw)) {
        counts.set(kw, (counts.get(kw) || 0) + 1);
      }
    }
  }
  return Array.from(counts.entries())
    .filter(([, c]) => c > 1)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10);
}

export function TrendingKeywords({ articles }: TrendingKeywordsProps) {
  const keywords = useMemo(() => countKeywords(articles), [articles]);

  if (keywords.length === 0) return null;

  return (
    <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white/60 dark:bg-gray-900/40 p-4">
      <h3 className="text-xs font-semibold tracking-widest uppercase text-gray-500 mb-3">
        Trending Keywords
      </h3>
      <div className="flex flex-wrap gap-1.5">
        {keywords.map(([kw, count]) => (
          <span
            key={kw}
            className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300"
          >
            {kw}
            <span className="text-[9px] font-bold text-gray-400 dark:text-gray-600">{count}</span>
          </span>
        ))}
      </div>
    </div>
  );
}
