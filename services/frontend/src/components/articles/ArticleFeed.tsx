import { CheckCheck, Newspaper } from "lucide-react";
import { ArticleCard } from "./ArticleCard";
import type { Article } from "../../types/article";

interface ArticleFeedProps {
  articles: Article[];
  loading: boolean;
  error: string | null;
  onToggleRead: (id: string, isRead: boolean) => void;
  onMarkAllRead: () => void;
}

export function ArticleFeed({ articles, loading, error, onToggleRead, onMarkAllRead }: ArticleFeedProps) {
  const unreadCount = articles.filter((a) => !a.is_read).length;

  if (loading) {
    return (
      <div className="flex flex-col gap-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900/60 p-4 animate-pulse">
            <div className="flex gap-2 mb-3">
              <div className="h-4 w-10 rounded bg-gray-200 dark:bg-gray-800" />
              <div className="h-4 w-16 rounded bg-gray-200 dark:bg-gray-800" />
            </div>
            <div className="h-4 rounded bg-gray-200 dark:bg-gray-800 mb-2" />
            <div className="h-4 w-3/4 rounded bg-gray-200 dark:bg-gray-800 mb-3" />
            <div className="h-3 rounded bg-gray-100 dark:bg-gray-800/60 mb-1" />
            <div className="h-3 w-4/5 rounded bg-gray-100 dark:bg-gray-800/60" />
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 dark:border-red-900/50 bg-red-50 dark:bg-red-950/30 p-6 text-center">
        <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>
        <p className="text-gray-500 dark:text-gray-600 text-xs mt-1">Check that the API gateway is running.</p>
      </div>
    );
  }

  if (!articles.length) {
    return (
      <div className="rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900/40 p-10 text-center">
        <Newspaper className="w-8 h-8 text-gray-300 dark:text-gray-700 mx-auto mb-3" />
        <p className="text-gray-500 text-sm">No articles yet.</p>
        <p className="text-gray-400 dark:text-gray-600 text-xs mt-1">The aggregator will fetch articles on startup.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-xs font-semibold tracking-widest uppercase text-gray-500">
          Latest Intelligence
          {unreadCount > 0 && (
            <span className="ml-2 inline-flex items-center px-1.5 py-0.5 rounded-full bg-blue-500/20 text-blue-500 dark:text-blue-400 text-[10px] font-bold">
              {unreadCount} new
            </span>
          )}
        </h2>
        {unreadCount > 0 && (
          <button
            onClick={onMarkAllRead}
            className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-400 transition-colors"
          >
            <CheckCheck className="w-3.5 h-3.5" />
            Mark all read
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-2.5">
        {articles.map((article) => (
          <ArticleCard key={article.id} article={article} onToggleRead={onToggleRead} />
        ))}
      </div>
    </div>
  );
}
