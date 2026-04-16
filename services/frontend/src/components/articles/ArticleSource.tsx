import { SOURCE_COLORS, SOURCE_LABELS } from "../../lib/constants";

interface ArticleSourceProps {
  source: string;
  sourceDisplay: string;
}

export function ArticleSource({ source, sourceDisplay }: ArticleSourceProps) {
  const color = SOURCE_COLORS[source] || "#6b7280";
  const abbr = SOURCE_LABELS[source] || sourceDisplay.slice(0, 3).toUpperCase();

  return (
    <span
      className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase"
      style={{ backgroundColor: `${color}20`, color, border: `1px solid ${color}40` }}
      title={sourceDisplay}
    >
      {abbr}
    </span>
  );
}
