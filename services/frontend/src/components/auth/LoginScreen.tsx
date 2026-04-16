import { useState } from "react";
import { Shield, Lock, Moon, Sun } from "lucide-react";
import { login } from "../../api/auth";
import { setToken } from "../../store/auth";
import { useTheme } from "../../hooks/useTheme";

interface LoginScreenProps {
  onLogin: () => void;
}

export function LoginScreen({ onLogin }: LoginScreenProps) {
  const { theme, toggle: toggleTheme } = useTheme();
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const token = await login(password);
      setToken(token);
      onLogin();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 flex items-center justify-center px-4">
      {/* Theme toggle — top right */}
      <button
        onClick={toggleTheme}
        title="Toggle theme"
        className="fixed top-4 right-4 p-2 rounded-lg text-gray-400 dark:text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
      >
        {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
      </button>

      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="flex flex-col items-center gap-3 mb-8">
          <Shield className="w-12 h-12 text-red-500" strokeWidth={1.5} />
          <div className="text-center">
            <h1 className="text-sm font-semibold tracking-widest uppercase text-gray-900 dark:text-gray-100">
              Cybersecurity
            </h1>
            <p className="text-xs text-gray-500 tracking-widest uppercase mt-0.5">
              Defcon Dashboard
            </p>
          </div>
        </div>

        {/* Card */}
        <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900/60 p-6">
          <div className="flex items-center gap-2 mb-5">
            <Lock className="w-4 h-4 text-gray-400" />
            <span className="text-xs font-semibold tracking-widest uppercase text-gray-500">
              Authentication required
            </span>
          </div>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoFocus
              className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 px-3 py-2.5 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-red-500/50"
            />

            {error && (
              <p className="text-xs text-red-500">{error}</p>
            )}

            <button
              type="submit"
              disabled={loading || !password}
              className="w-full rounded-lg bg-red-500 hover:bg-red-600 disabled:opacity-40 text-white text-sm font-medium py-2.5 transition-colors"
            >
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
