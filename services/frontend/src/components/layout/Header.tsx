import { useEffect, useState } from "react";
import { Shield, Moon, Sun, RefreshCw, LogOut } from "lucide-react";
import { cn, formatRelativeTime } from "../../lib/utils";

interface HeaderProps {
  theme: "dark" | "light";
  onToggleTheme: () => void;
  onRefresh: () => void;
  lastRefreshed: string | null;
  refreshing?: boolean;
  onLogout: () => void;
}

export function Header({ theme, onToggleTheme, onRefresh, lastRefreshed, refreshing, onLogout }: HeaderProps) {
  // Tick every 30 s so the relative timestamp stays accurate
  const [, setTick] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setTick((n) => n + 1), 30_000);
    return () => clearInterval(id);
  }, []);

  return (
    <header className="sticky top-0 z-10 border-b border-gray-200 dark:border-gray-800 bg-white/90 dark:bg-gray-950/90 backdrop-blur-sm">
      <div className="max-w-screen-2xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-4">

        {/* Logo */}
        <div className="flex items-center gap-3">
          <Shield className="w-7 h-7 text-red-500" strokeWidth={1.5} />
          <div>
            <h1 className="text-sm font-semibold tracking-widest uppercase text-gray-900 dark:text-gray-100 leading-none">
              Cybersecurity
            </h1>
            <p className="text-xs text-gray-500 tracking-widest uppercase leading-none mt-0.5">
              Defcon Dashboard
            </p>
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-3">
          {lastRefreshed && (
            <span className="hidden sm:block text-xs text-gray-400 dark:text-gray-600">
              updated {formatRelativeTime(lastRefreshed)}
            </span>
          )}

          <button
            onClick={onRefresh}
            disabled={refreshing}
            title="Trigger refresh"
            className="p-2 rounded-lg text-gray-400 dark:text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors disabled:opacity-40"
          >
            <RefreshCw className={cn("w-4 h-4", refreshing && "animate-spin")} />
          </button>

          <button
            onClick={onToggleTheme}
            title="Toggle theme"
            className="p-2 rounded-lg text-gray-400 dark:text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>

          <button
            onClick={onLogout}
            title="Sign out"
            className="p-2 rounded-lg text-gray-400 dark:text-gray-500 hover:text-red-500 dark:hover:text-red-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
