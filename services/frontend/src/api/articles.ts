import apiFetch from "./client";
import type { ArticlesResponse } from "../types/article";

export function getArticles(params?: {
  limit?: number;
  offset?: number;
  source?: string;
  unread_only?: boolean;
  min_score?: number;
  max_score?: number;
  search?: string;
}): Promise<ArticlesResponse> {
  const query = new URLSearchParams();
  if (params?.limit) query.set("limit", String(params.limit));
  if (params?.offset) query.set("offset", String(params.offset));
  if (params?.source) query.set("source", params.source);
  if (params?.unread_only) query.set("unread_only", "true");
  if (params?.min_score != null) query.set("min_score", String(params.min_score));
  if (params?.max_score != null) query.set("max_score", String(params.max_score));
  if (params?.search) query.set("search", params.search);
  const qs = query.toString() ? `?${query}` : "";
  return apiFetch(`/articles${qs}`);
}

export function markArticleRead(id: string, isRead: boolean): Promise<{ id: string; is_read: boolean; read_at: string }> {
  return apiFetch(`/articles/${id}/read`, {
    method: "PATCH",
    body: JSON.stringify({ is_read: isRead }),
  });
}

export function markAllRead(isRead = true): Promise<{ marked_count: number }> {
  return apiFetch("/articles/read-all", {
    method: "PATCH",
    body: JSON.stringify({ is_read: isRead }),
  });
}

export function triggerRefresh(): Promise<{ triggered: boolean }> {
  return apiFetch("/admin/refresh", { method: "POST" });
}
