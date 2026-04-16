import apiFetch from "./client";
import type { ArticlesResponse } from "../types/article";

export function getArticles(params?: {
  limit?: number;
  source?: string;
  unread_only?: boolean;
}): Promise<ArticlesResponse> {
  const query = new URLSearchParams();
  if (params?.limit) query.set("limit", String(params.limit));
  if (params?.source) query.set("source", params.source);
  if (params?.unread_only) query.set("unread_only", "true");
  const qs = query.toString() ? `?${query}` : "";
  return apiFetch(`/articles${qs}`);
}

export function markArticleRead(id: string, isRead: boolean): Promise<{ id: string; is_read: boolean; read_at: string }> {
  return apiFetch(`/articles/${id}/read`, {
    method: "PATCH",
    body: JSON.stringify({ is_read: isRead }),
  });
}

export function markAllRead(): Promise<{ marked_count: number }> {
  return apiFetch("/articles/read-all", { method: "PATCH" });
}

export function triggerRefresh(): Promise<{ triggered: boolean }> {
  return apiFetch("/admin/refresh", { method: "POST" });
}
