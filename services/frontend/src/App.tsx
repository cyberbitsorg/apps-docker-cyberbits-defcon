import { useState, useEffect } from "react";
import { useTheme } from "./hooks/useTheme";
import { getToken, clearToken } from "./store/auth";
import { LoginScreen } from "./components/auth/LoginScreen";
import { useArticles } from "./hooks/useArticles";
import { useDefcon } from "./hooks/useDefcon";
import { Header } from "./components/layout/Header";
import { DefconGauge } from "./components/defcon/DefconGauge";
import { ArticleFeed } from "./components/articles/ArticleFeed";
import { triggerRefresh } from "./api/articles";
import { DEFCON_LEVELS } from "./lib/constants";
import { SeverityBreakdown } from "./components/widgets/SeverityBreakdown";
import { TopThreats } from "./components/widgets/TopThreats";
import { TrendingKeywords } from "./components/widgets/TrendingKeywords";
import { RecentCves } from "./components/widgets/RecentCves";
import { SourceDistribution } from "./components/widgets/SourceDistribution";

export default function App() {
  const [authed, setAuthed] = useState(() => !!getToken());

  useEffect(() => {
    const handleLogout = () => setAuthed(false);
    window.addEventListener("auth:logout", handleLogout);
    return () => window.removeEventListener("auth:logout", handleLogout);
  }, []);

  if (!authed) {
    return <LoginScreen onLogin={() => setAuthed(true)} />;
  }

  return <Dashboard onLogout={() => { clearToken(); setAuthed(false); }} />;
}

function Dashboard({ onLogout }: { onLogout: () => void }) {
  const { theme, toggle: toggleTheme } = useTheme();
  const { status: defconStatus, history: defconHistory, loading: defconLoading } = useDefcon();
  const [refreshing, setRefreshing] = useState(false);

  const [activeFilters, setActiveFilters] = useState<{ severity: string | null; source: string | null; search: string | null }>({
    severity: null,
    source: null,
    search: null,
  });

  const handleSeverityClick = (label: string) => {
    setActiveFilters((f) => ({ ...f, severity: f.severity === label ? null : label }));
  };

  const handleSourceClick = (id: string) => {
    setActiveFilters((f) => ({ ...f, source: f.source === id ? null : id }));
  };

  const handleClearFilter = (key: "severity" | "source" | "search") => {
    setActiveFilters((f) => ({ ...f, [key]: null }));
  };

  const handleSearchChange = (value: string) => {
    setActiveFilters((f) => ({ ...f, search: value || null }));
  };

  const { articles, lastRefreshed, loading, error, refresh, toggleRead, markAll, page, totalPages, goToPage } = useArticles(activeFilters);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await triggerRefresh();
      refresh(true);
      setRefreshing(false);
    } catch {
      setRefreshing(false);
      refresh();
    }
  };

  const defconLevel = defconStatus?.level ?? 1;
  const levelStyle = DEFCON_LEVELS[defconLevel];

  return (
    // useTheme adds/removes "dark" on <html>; components use dark: variants
    <div className="min-h-screen overflow-x-hidden bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100">
      <Header
        theme={theme}
        onToggleTheme={toggleTheme}
        onRefresh={handleRefresh}
        lastRefreshed={lastRefreshed}
        refreshing={refreshing}
        onLogout={onLogout}
      />

      <main className="max-w-screen-2xl mx-auto px-4 sm:px-6 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-6">

          {/* Sidebar */}
          <aside className="flex flex-col gap-5 pt-7 order-1 lg:order-none min-w-0">
            {defconLoading ? (
              <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900/60 p-5 animate-pulse h-[420px]" />
            ) : defconStatus ? (
              <DefconGauge status={defconStatus} history={defconHistory} />
            ) : null}

            {/* Threat indicators */}
            {defconStatus && (
              <div className={`rounded-xl border ${levelStyle.border} ${levelStyle.bg} p-4`}>
                <h3 className="text-xs font-semibold tracking-widest uppercase text-gray-500 mb-3">
                  Threat Indicators
                </h3>
                <div className="grid grid-cols-2 gap-3">
                  <StatCard label="Threat Level" value={`DEFCON ${defconStatus.level}`} color={levelStyle.color} />
                  <StatCard label="Score"        value={`${Math.round(defconStatus.score)}/100`} color={levelStyle.color} />
                  <StatCard label="Trend"        value={defconStatus.trend} color={
                    defconStatus.trend === "rising"  ? "#ef4444" :
                    defconStatus.trend === "falling" ? "#22c55e" : "#6b7280"
                  } />
                  <StatCard label="Articles" value={String(articles.length)} color="#6b7280" />
                </div>
              </div>
            )}

            {/* Severity breakdown */}
            <SeverityBreakdown
              articles={articles}
              activeSeverity={activeFilters.severity}
              onSeverityClick={handleSeverityClick}
            />

            {/* Source legend */}
            <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white/60 dark:bg-gray-900/40 p-4">
              <h3 className="text-xs font-semibold tracking-widest uppercase text-gray-500 mb-3">
                Sources
              </h3>
              <div className="flex flex-col gap-2">
                {[
                  { id: "bleeping_computer", label: "Bleeping Computer", color: "#f97316" },
                  { id: "hacker_news",       label: "Hacker News",       color: "#8b5cf6" },
                  { id: "hackread",          label: "HackRead",          color: "#ec4899" },
                  { id: "security_affairs",  label: "Security Affairs",  color: "#e11d48" },
                  { id: "the_register",      label: "The Register",      color: "#06b6d4" },
                ].map((s) => {
                  const isActive = activeFilters.source === s.id;
                  return (
                    <button
                      key={s.id}
                      onClick={() => handleSourceClick(s.id)}
                      className={`flex items-center gap-2 rounded px-1.5 py-0.5 -mx-1.5 text-left transition-colors cursor-pointer w-full ${
                        isActive
                          ? "bg-gray-100 dark:bg-gray-800"
                          : "hover:bg-gray-50 dark:hover:bg-gray-800/50"
                      }`}
                    >
                      <div
                        className="w-2 h-2 rounded-full flex-shrink-0 transition-all"
                        style={{
                          backgroundColor: s.color,
                          outline: isActive ? `2px solid ${s.color}` : undefined,
                          outlineOffset: isActive ? "2px" : undefined,
                        }}
                      />
                      <span className={`text-xs ${isActive ? "text-gray-900 dark:text-gray-100 font-medium" : "text-gray-600 dark:text-gray-400"}`}>
                        {s.label}
                      </span>
                      <span className="ml-auto text-xs text-gray-400 dark:text-gray-600">
                        {articles.filter((a) => a.source === s.id).length}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Source distribution donut */}
            <SourceDistribution
              articles={articles}
              activeSource={activeFilters.source}
              onSourceClick={handleSourceClick}
            />

            {/* Top threats */}
            <TopThreats articles={articles} />

            {/* Trending keywords */}
            <TrendingKeywords articles={articles} />

            {/* Recent CVE mentions */}
            <RecentCves articles={articles} />
          </aside>

          {/* Article feed */}
          <section className="order-2 lg:order-none min-w-0">
            <ArticleFeed
              articles={articles}
              loading={loading}
              error={error}
              page={page}
              totalPages={totalPages}
              onToggleRead={toggleRead}
              onMarkAll={markAll}
              onGoToPage={goToPage}
              activeFilters={activeFilters}
              onClearFilter={handleClearFilter}
              onSearchChange={handleSearchChange}
            />
          </section>
        </div>
      </main>
    </div>
  );
}

function StatCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="rounded-lg bg-white dark:bg-gray-900/60 border border-gray-200 dark:border-gray-800 p-2.5">
      <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">{label}</p>
      <p className="text-sm font-semibold capitalize" style={{ color }}>{value}</p>
    </div>
  );
}
