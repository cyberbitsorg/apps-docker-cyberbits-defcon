import { useState, useEffect, useCallback } from "react";
import { getDefconStatus, getDefconHistory } from "../api/defcon";
import type { DefconStatus, DefconHistoryPoint } from "../types/defcon";

const POLL_INTERVAL = 5 * 60 * 1000; // 5 minutes

export function useDefcon() {
  const [status, setStatus] = useState<DefconStatus | null>(null);
  const [history, setHistory] = useState<DefconHistoryPoint[]>([]);
  const [loading, setLoading] = useState(true);

  const fetch = useCallback(async () => {
    try {
      const [s, h] = await Promise.all([getDefconStatus(), getDefconHistory(24)]);
      setStatus(s);
      setHistory(h.history);
    } catch {
      // Keep stale data on error
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetch();
    const id = setInterval(fetch, POLL_INTERVAL);
    return () => clearInterval(id);
  }, [fetch]);

  return { status, history, loading };
}
