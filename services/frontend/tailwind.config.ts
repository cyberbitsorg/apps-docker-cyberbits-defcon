import type { Config } from "tailwindcss";

export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        defcon: {
          1: "#22c55e",
          2: "#3b82f6",
          3: "#f59e0b",
          4: "#ea580c",
          5: "#dc2626",
        },
      },
      fontFamily: {
        mono: ["JetBrains Mono", "Fira Code", "Consolas", "monospace"],
      },
    },
  },
  plugins: [],
} satisfies Config;
