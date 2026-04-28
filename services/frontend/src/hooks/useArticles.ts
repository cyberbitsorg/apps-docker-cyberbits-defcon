import { useState, useEffect, useCallback, useRef } from "react";
import { getArticles, markArticleRead, markAllRead } from "../api/articles";
import type { Article, ArticlesResponse } from "../types/article";

const POLL_INTERVAL = 5 * 60 * 1000;
const TICK_INTERVAL = 60 * 1000;
const PAGE_SIZE = 20;

const SEVERITY_RANGES: Record<string, { min: number; max: number }> = {
  Critical: { min: 80, max: 100 },
  High:     { min: 60, max: 79 },
  Elevated: { min: 40, max: 59 },
  Guarded:  { min: 20, max: 39 },
  Low:      { min: 1,  max: 19 },
};

export interface ArticleFilters {
  severity: string | null;
  source: string | null;
  search: string | null;
}

export function useArticles(filters: ArticleFilters = { severity: null, source: null, search: null }) {
  const [data, setData] = useState<ArticlesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);
  const [page, setPage] = useState(1);
  const [debouncedSearch, setDebouncedSearch] = useState(filters.search);
  const intervalRef = useRef<ReturnType<typeof setInterval>>();
  const tickRef = useRef<ReturnType<typeof setInterval>>();

  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(filters.search), 400);
    return () => clearTimeout(t);
  }, [filters.search]);

  const fetchArticles = useCallback(async (resetTimer?: boolean, targetPage?: number) => {
    const currentPage = targetPage ?? page;
    const severityRange = filters.severity ? SEVERITY_RANGES[filters.severity] : null;
    try {
      const result = await getArticles({
        limit: PAGE_SIZE,
        offset: (currentPage - 1) * PAGE_SIZE,
        ...(filters.source ? { source: filters.source } : {}),
        ...(severityRange ? { min_score: severityRange.min, max_score: severityRange.max } : {}),
        ...(debouncedSearch ? { search: debouncedSearch } : {}),
      });
      if (resetTimer) {
        result.last_refreshed_at = new Date().toISOString();
      }
      setData(result);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load articles");
    } finally {
      setLoading(false);
    }
  }, [page, filters.severity, filters.source, debouncedSearch]);

  // Reset to page 1 when filters change
  useEffect(() => {
    setPage(1);
  }, [filters.severity, filters.source, debouncedSearch]);

  useEffect(() => {
    setLoading(true);
    fetchArticles();
    intervalRef.current = setInterval(fetchArticles, POLL_INTERVAL);
    tickRef.current = setInterval(() => setTick((n) => n + 1), TICK_INTERVAL);
    return () => {
      clearInterval(intervalRef.current);
      clearInterval(tickRef.current);
    };
  }, [fetchArticles]);

  const goToPage = useCallback((newPage: number) => {
    setPage(newPage);
    setLoading(true);
    fetchArticles(false, newPage);
  }, [fetchArticles]);

  const toggleRead = useCallback(async (id: string, isRead: boolean) => {
    setData((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        articles: prev.articles.map((a) =>
          a.id === id ? { ...a, is_read: isRead } : a
        ),
      };
    });

    try {
      await markArticleRead(id, isRead);
    } catch {
      setData((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          articles: prev.articles.map((a) =>
            a.id === id ? { ...a, is_read: !isRead } : a
          ),
        };
      });
    }
  }, []);

  const markAll = useCallback(async (isRead: boolean) => {
    setData((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        articles: prev.articles.map((a) => ({ ...a, is_read: isRead })),
      };
    });
    try {
      await markAllRead(isRead);
    } catch {
      fetchArticles();
    }
  }, [fetchArticles]);

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return {
    articles: data?.articles ?? [],
    total: data?.total ?? 0,
    lastRefreshed: data?.last_refreshed_at ?? null,
    loading,
    error,
    page,
    totalPages,
    goToPage,
    refresh: fetchArticles,
    toggleRead,
    markAll,
  };
}
