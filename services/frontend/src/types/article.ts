export interface Article {
  id: string;
  title: string;
  summary: string;
  url: string;
  source: string;
  source_display: string;
  published_at: string;
  fetched_at: string;
  categories: string[];
  defcon_score: number;
  is_read: boolean;
  read_at?: string;
}

export interface ArticlesResponse {
  articles: Article[];
  total: number;
  last_refreshed_at: string | null;
}
