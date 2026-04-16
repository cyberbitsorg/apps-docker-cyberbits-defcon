import apiFetch from "./client";
import type { DefconStatus, DefconHistoryResponse } from "../types/defcon";

export function getDefconStatus(): Promise<DefconStatus> {
  return apiFetch("/defcon");
}

export function getDefconHistory(hours = 24): Promise<DefconHistoryResponse> {
  return apiFetch(`/defcon/history?hours=${hours}`);
}
