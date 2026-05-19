import { SOURCE_COLORS, SOURCE_LABELS } from "../../lib/constants";

interface ArticleSourceProps {
  source: string;
  sourceDisplay: string;
  defconColor?: string;
}

export function ArticleSource({ source, sourceDisplay, defconColor }: ArticleSourceProps) {
  const color = SOURCE_COLORS[source] ?? SOURCE_COLORS["bleeping_computer"];
  const abbr = SOURCE_LABELS[source] || sourceDisplay.slice(0, 3).toUpperCase();
  const borderColor = defconColor ?? color;

  return (
    <span
      className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase"
      style={{ backgroundColor: `${color}20`, color, border: `1px solid ${borderColor}60` }}
      title={sourceDisplay}
    >
      {abbr}
    </span>
  );
}
