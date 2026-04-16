import { useState, useEffect, useCallback, useRef } from "react";
import { getArticles, markArticleRead, markAllRead } from "../api/articles";
import type { Article, ArticlesResponse } from "../types/article";

const POLL_INTERVAL = 5 * 60 * 1000;
const TICK_INTERVAL = 60 * 1000;

export function useArticles() {
  const [data, setData] = useState<ArticlesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);
  const intervalRef = useRef<ReturnType<typeof setInterval>>();
  const tickRef = useRef<ReturnType<typeof setInterval>>();

  const fetchArticles = useCallback(async (resetTimer?: boolean) => {
    try {
      const result = await getArticles({ limit: 20 });
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
  }, []);

  useEffect(() => {
    fetchArticles();
    intervalRef.current = setInterval(fetchArticles, POLL_INTERVAL);
    tickRef.current = setInterval(() => setTick((n) => n + 1), TICK_INTERVAL);
    return () => {
      clearInterval(intervalRef.current);
      clearInterval(tickRef.current);
    };
  }, [fetchArticles]);

  const toggleRead = useCallback(async (id: string, isRead: boolean) => {
    // Optimistic update
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
      // Revert on failure
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

  const markAllAsRead = useCallback(async () => {
    setData((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        articles: prev.articles.map((a) => ({ ...a, is_read: true })),
      };
    });
    try {
      await markAllRead();
    } catch {
      // If fails, refresh from server
      fetchArticles();
    }
  }, [fetchArticles]);

  return {
    articles: data?.articles ?? [],
    lastRefreshed: data?.last_refreshed_at ?? null,
    loading,
    error,
    refresh: fetchArticles,
    toggleRead,
    markAllAsRead,
  };
}
