import { ExternalLink } from "lucide-react";
import { cn } from "../../lib/utils";
import type { Article } from "../../types/article";

interface TopThreatsProps {
  articles: Article[];
}

export function TopThreats({ articles }: TopThreatsProps) {
  const top = [...articles]
    .filter((a) => a.defcon_score > 0)
    .sort((a, b) => b.defcon_score - a.defcon_score)
    .slice(0, 5);

  if (top.length === 0) return null;

  return (
    <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white/60 dark:bg-gray-900/40 p-4 overflow-hidden">
      <h3 className="text-xs font-semibold tracking-widest uppercase text-gray-500 mb-3">
        Top Threats
      </h3>

      <div className="flex flex-col gap-2">
        {top.map((article) => (
          <a
            key={article.id}
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="group flex items-start gap-2 rounded-lg p-2 -mx-2 hover:bg-gray-100 dark:hover:bg-gray-800/50 transition-colors"
          >
            <span className={cn(
              "mt-0.5 text-[10px] font-bold px-1.5 py-0.5 rounded flex-shrink-0",
              article.defcon_score >= 80
                ? "text-red-600 bg-red-600/10 border border-red-600/20"
                : article.defcon_score >= 60
                  ? "text-orange-600 bg-orange-600/10 border border-orange-600/20"
                  : article.defcon_score >= 40
                    ? "text-amber-500 bg-amber-500/10 border border-amber-500/20"
                    : article.defcon_score >= 20
                      ? "text-blue-500 bg-blue-500/10 border border-blue-500/20"
                      : "text-green-500 bg-green-500/10 border border-green-500/20"
            )}>
              {Math.round(article.defcon_score)}
            </span>
            <span className="text-xs text-gray-700 dark:text-gray-300 leading-snug line-clamp-2 flex-1 group-hover:text-black dark:group-hover:text-white transition-colors">
              {article.title}
            </span>
            <ExternalLink className="w-3 h-3 mt-0.5 flex-shrink-0 text-gray-300 dark:text-gray-700 group-hover:text-gray-500 dark:group-hover:text-gray-400 transition-colors" />
          </a>
        ))}
      </div>
    </div>
  );
}
