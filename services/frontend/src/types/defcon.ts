export interface DefconFactors {
  volume_score: number;
  cve_score: number;
  impact_score: number;
  keyword_score: number;
}

export interface DefconStatus {
  score: number;
  level: 1 | 2 | 3 | 4 | 5;
  label: string;
  color: string;
  computed_at: string | null;
  factors: DefconFactors;
  trend: "rising" | "falling" | "stable";
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
