import { useState, useEffect } from "react";
import { CheckCheck, Newspaper, RotateCcw, Search, X } from "lucide-react";
import { ArticleCard } from "./ArticleCard";
import type { Article } from "../../types/article";
import type { ArticleFilters } from "../../hooks/useArticles";

const SOURCE_LABELS: Record<string, string> = {
  bleeping_computer: "Bleeping Computer",
  hacker_news:       "Hacker News",
  hackread:          "HackRead",
  security_affairs:  "Security Affairs",
  the_register:      "The Register",
};

interface ArticleFeedProps {
  articles: Article[];
  loading: boolean;
  error: string | null;
  page: number;
  totalPages: number;
  onToggleRead: (id: string, isRead: boolean) => void;
  onMarkAll: (isRead: boolean) => void;
  onGoToPage: (page: number) => void;
  activeFilters: ArticleFilters;
  onClearFilter: (key: keyof ArticleFilters) => void;
  onSearchChange: (value: string) => void;
}

function FilterChips({ activeFilters, onClearFilter }: { activeFilters: ArticleFilters; onClearFilter: (key: keyof ArticleFilters) => void }) {
  return (
    <>
      {activeFilters.severity && (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-800 text-xs text-gray-700 dark:text-gray-300">
          {activeFilters.severity}
          <button onClick={() => onClearFilter("severity")} className="ml-0.5 hover:text-gray-900 dark:hover:text-gray-100 transition-colors">
            <X className="w-3 h-3" />
          </button>
        </span>
      )}
      {activeFilters.source && (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-800 text-xs text-gray-700 dark:text-gray-300">
          {SOURCE_LABELS[activeFilters.source] ?? activeFilters.source}
          <button onClick={() => onClearFilter("source")} className="ml-0.5 hover:text-gray-900 dark:hover:text-gray-100 transition-colors">
            <X className="w-3 h-3" />
          </button>
        </span>
      )}
      {activeFilters.search && (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-800 text-xs text-gray-700 dark:text-gray-300">
          &ldquo;{activeFilters.search}&rdquo;
          <button onClick={() => onClearFilter("search")} className="ml-0.5 hover:text-gray-900 dark:hover:text-gray-100 transition-colors">
            <X className="w-3 h-3" />
          </button>
        </span>
      )}
    </>
  );
}

export function ArticleFeed({ articles, loading, error, page, totalPages, onToggleRead, onMarkAll, onGoToPage, activeFilters, onClearFilter, onSearchChange }: ArticleFeedProps) {
  const [inputValue, setInputValue] = useState(activeFilters.search ?? "");

  // Sync when the filter is cleared externally (e.g. via chip)
  useEffect(() => {
    if (activeFilters.search === null) setInputValue("");
  }, [activeFilters.search]);

  const handleSearchInput = (value: string) => {
    setInputValue(value);
    onSearchChange(value);
  };

  const unreadCount = articles.filter((a) => !a.is_read).length;
  const allRead = articles.length > 0 && unreadCount === 0;
  const hasActiveFilter = !!(activeFilters.severity || activeFilters.source || activeFilters.search);

  return (
    <div>
      {/* Search bar — always rendered at index 0 so React never unmounts the input */}
      <div className="relative mb-3">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400 pointer-events-none" />
        <input
          type="search"
          placeholder="Search articles…"
          value={inputValue}
          onChange={(e) => handleSearchInput(e.target.value)}
          className="w-full pl-8 pr-3 py-2 text-sm rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900/60 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-600 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      {/* Loading skeleton */}
      {loading && (
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
      )}

      {/* Error */}
      {!loading && error && (
        <div className="rounded-lg border border-red-200 dark:border-red-900/50 bg-red-50 dark:bg-red-950/30 p-6 text-center">
          <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>
          <p className="text-gray-500 dark:text-gray-600 text-xs mt-1">Check that the API gateway is running.</p>
        </div>
      )}

      {/* Header row — hidden during loading */}
      {!loading && !error && (
        <div className="flex items-center justify-between mb-3 min-w-0 gap-2 flex-wrap">
          <div className="flex items-center gap-2 flex-wrap min-w-0">
            <h2 className="text-xs font-semibold tracking-widest uppercase text-gray-500">
              Latest Intelligence
              {unreadCount > 0 && (
                <span className="ml-2 inline-flex items-center px-1.5 py-0.5 rounded-full bg-blue-500/20 text-blue-500 dark:text-blue-400 text-[10px] font-bold">
                  {unreadCount} new
                </span>
              )}
            </h2>
            <FilterChips activeFilters={activeFilters} onClearFilter={onClearFilter} />
          </div>
          {articles.length > 0 && (
            <button
              onClick={() => onMarkAll(!allRead)}
              className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-400 transition-colors flex-shrink-0"
            >
              {allRead ? (
                <>
                  <RotateCcw className="w-3.5 h-3.5" />
                  Mark all unread
                </>
              ) : (
                <>
                  <CheckCheck className="w-3.5 h-3.5" />
                  Mark all read
                </>
              )}
            </button>
          )}
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && articles.length === 0 && (
        <div className="rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900/40 p-10 text-center">
          <Newspaper className="w-8 h-8 text-gray-300 dark:text-gray-700 mx-auto mb-3" />
          {activeFilters.search ? (
            <p className="text-gray-500 text-sm">No articles found for &ldquo;{activeFilters.search}&rdquo;.</p>
          ) : hasActiveFilter ? (
            <p className="text-gray-500 text-sm">No articles found for the selected filters.</p>
          ) : (
            <>
              <p className="text-gray-500 text-sm">No articles yet.</p>
              <p className="text-gray-400 dark:text-gray-600 text-xs mt-1">The aggregator will fetch articles on startup.</p>
            </>
          )}
        </div>
      )}

      {/* Article grid */}
      {!loading && !error && articles.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-2.5">
          {articles.map((article) => (
            <ArticleCard key={article.id} article={article} onToggleRead={onToggleRead} />
          ))}
        </div>
      )}

      {/* Pagination */}
      {!loading && totalPages > 1 && (
        <div className="flex flex-wrap items-center justify-center gap-1.5 mt-6">
          {Array.from({ length: totalPages }).map((_, i) => {
            const p = i + 1;
            return (
              <button
                key={p}
                onClick={() => onGoToPage(p)}
                className={`w-8 h-8 rounded text-xs font-medium transition-colors ${
                  p === page
                    ? "bg-blue-500 text-white"
                    : "bg-white dark:bg-gray-900/60 border border-gray-200 dark:border-gray-800 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300 dark:hover:border-gray-700"
                }`}
              >
                {p}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
