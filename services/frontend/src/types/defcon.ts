export interface DefconFactors {
  trigger?: TriggerType | null;
  trigger_article_id?: string;
  trigger_article_title?: string;
  weighted_max?: number;
  volume_bonus?: number;
  raw_level?: number;
  displayed_level?: number;
}

export type TriggerType =
  | "active_exploitation"
  | "confirmed_breach"
  | "apt_campaign"
  | "kev_addition";

export interface TriggerArticle {
  id: string;
  title: string;
  published_at?: string | null;
}

export interface DefconStatus {
  score: number;
  level: 1 | 2 | 3 | 4 | 5;
  label: string;
  color: string;
  computed_at: string | null;
  factors: DefconFactors;
  trend: "rising" | "falling" | "stable";
  // v2 fields (optional for back-compat with old rows)
  trigger?: TriggerType | null;
  trigger_article?: TriggerArticle | null;
  raw_level?: number;
  displayed_level?: number;
  sticky_until?: string | null;
}

export interface DefconHistoryPoint {
  score: number;
  level: number;
  computed_at: string;
  color: string;
}

export interface DefconHistoryResponse {
  history: DefconHistoryPoint[];
}
