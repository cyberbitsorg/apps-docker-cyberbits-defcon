import { ExternalLink, CheckCircle2, Circle } from "lucide-react";
import { ArticleSource } from "./ArticleSource";
import { cn, formatRelativeTime } from "../../lib/utils";
import type { Article } from "../../types/article";

interface ArticleCardProps {
  article: Article;
  onToggleRead: (id: string, isRead: boolean) => void;
}

export function ArticleCard({ article, onToggleRead }: ArticleCardProps) {
  const { id, title, summary, url, source, source_display, published_at, is_read, defcon_score } = article;

  return (
    <article
      className={cn(
        "group relative rounded-lg border transition-all duration-200",
        is_read
          ? "bg-gray-50 dark:bg-gray-900/40 border-gray-200 dark:border-gray-800 opacity-60 hover:opacity-80"
          : "bg-white dark:bg-gray-900/60 border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 hover:shadow-sm dark:hover:shadow-none"
      )}
    >
      {/* Unread indicator strip */}
      {!is_read && (
        <div className="absolute left-0 top-3 bottom-3 w-0.5 rounded-full bg-blue-500" />
      )}

      <div className="p-4 pl-5">
        {/* Source + time + score badge */}
        <div className="flex items-center gap-2 mb-2">
          <ArticleSource source={source} sourceDisplay={source_display} />
          <span className="text-xs text-gray-400 dark:text-gray-600">{formatRelativeTime(published_at)}</span>
          {defcon_score > 0 && (
            <span className={cn(
              "ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded",
              defcon_score >= 80
                ? "text-red-600 bg-red-600/10 border border-red-600/20"
                : defcon_score >= 60
                  ? "text-orange-600 bg-orange-600/10 border border-orange-600/20"
                  : defcon_score >= 40
                    ? "text-amber-500 bg-amber-500/10 border border-amber-500/20"
                    : defcon_score >= 20
                      ? "text-blue-500 bg-blue-500/10 border border-blue-500/20"
                      : "text-green-500 bg-green-500/10 border border-green-500/20"
            )}>
              {Math.round(defcon_score)}
            </span>
          )}
        </div>

        {/* Title */}
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className={cn(
            "group/link flex items-start gap-1.5 mb-2",
            is_read
              ? "text-gray-400 dark:text-gray-500"
              : "text-gray-900 dark:text-gray-100 hover:text-black dark:hover:text-white"
          )}
          onClick={() => !is_read && onToggleRead(id, true)}
        >
          <span className="text-sm font-medium leading-snug flex-1">{title}</span>
          <ExternalLink className="w-3 h-3 mt-0.5 flex-shrink-0 opacity-0 group-hover/link:opacity-60 transition-opacity" />
        </a>

        {/* Summary */}
        {summary && (
          <p className={cn(
            "text-xs leading-relaxed line-clamp-3",
            is_read ? "text-gray-400 dark:text-gray-600" : "text-gray-500 dark:text-gray-400"
          )}>
            {summary}
          </p>
        )}

        {/* Read toggle */}
        <button
          onClick={() => onToggleRead(id, !is_read)}
          className={cn(
            "mt-3 flex items-center gap-1.5 text-xs transition-colors",
            is_read
              ? "text-gray-400 dark:text-gray-600 hover:text-gray-600 dark:hover:text-gray-400"
              : "text-gray-400 dark:text-gray-600 hover:text-blue-500 dark:hover:text-blue-400"
          )}
        >
          {is_read ? (
            <><CheckCircle2 className="w-3.5 h-3.5 text-green-500" /><span>Read</span></>
          ) : (
            <><Circle className="w-3.5 h-3.5" /><span>Mark as read</span></>
          )}
        </button>
      </div>
    </article>
  );
}
