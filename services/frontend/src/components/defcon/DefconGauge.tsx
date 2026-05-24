import { AreaChart, Area, XAxis, YAxis, ResponsiveContainer, Tooltip } from "recharts";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { DEFCON_LEVELS } from "../../lib/constants";
import type { DefconStatus, DefconHistoryPoint } from "../../types/defcon";
import { formatRelativeTime } from "../../lib/utils";

interface DefconGaugeProps {
  status: DefconStatus;
  history: DefconHistoryPoint[];
}

// SVG gauge constants
// viewBox: 0 0 200 130, center (100, 90), radius 78
// Arc: 150° → 30° clockwise (240° sweep) — goes over the top like a speedometer
const CX = 100, CY = 90, R = 78, TRACK_W = 14;
const START_ANGLE = 150;  // 8 o'clock
const SWEEP = 240;

function polar(r: number, deg: number) {
  const rad = (deg * Math.PI) / 180;
  return { x: CX + r * Math.cos(rad), y: CY + r * Math.sin(rad) };
}

function arcPath(r: number, startDeg: number, endDeg: number): string {
  const s = polar(r, startDeg);
  const e = polar(r, endDeg);
  // Determine if the angular difference (CW) > 180° for large-arc-flag
  let delta = endDeg - startDeg;
  while (delta < 0) delta += 360;
  while (delta > 360) delta -= 360;
  const large = delta > 180 ? 1 : 0;
  return `M ${s.x.toFixed(2)} ${s.y.toFixed(2)} A ${r} ${r} 0 ${large} 1 ${e.x.toFixed(2)} ${e.y.toFixed(2)}`;
}

// Five coloured segments, each 48° (240 / 5)
const SEGMENTS = [
  { color: "#3b82f6", start: START_ANGLE,       end: START_ANGLE + 48  }, // DEFCON 5 Fade Out
  { color: "#22c55e", start: START_ANGLE + 48,  end: START_ANGLE + 96  }, // DEFCON 4 Double Take
  { color: "#eab308", start: START_ANGLE + 96,  end: START_ANGLE + 144 }, // DEFCON 3 Round House
  { color: "#dc2626", start: START_ANGLE + 144, end: START_ANGLE + 192 }, // DEFCON 2 Fast Pace
  { color: "#ffffff", start: START_ANGLE + 192, end: START_ANGLE + 240 }, // DEFCON 1 Cocked Pistol
];

export function DefconGauge({ status, history }: DefconGaugeProps) {
  const level = DEFCON_LEVELS[status.level];
  const score = Math.round(status.score);

  // Needle angle: score 0 → 150°, score 100 → 30° (= 150 + 240 = 390 = 30 mod 360)
  const needleAngle = START_ANGLE + (score / 100) * SWEEP;
  const needleTip  = polar(R * 0.55, needleAngle);
  const needleL    = polar(4, needleAngle + 90);
  const needleR    = polar(4, needleAngle - 90);

  const TrendIcon  = status.trend === "rising" ? TrendingUp : status.trend === "falling" ? TrendingDown : Minus;
  const trendColor = status.trend === "rising" ? "text-red-400" : status.trend === "falling" ? "text-green-400" : "text-gray-500";

  const trigger = status.trigger ?? null;
  const triggerArticle = status.trigger_article ?? null;
  const triggerAge = triggerArticle?.published_at ? formatRelativeTime(triggerArticle.published_at) : null;

  const TRIGGER_LABELS: Record<string, string> = {
    active_exploitation: "Active exploitation",
    confirmed_breach:    "Confirmed breach",
    apt_campaign:        "Nation-state activity",
    kev_addition:        "CISA KEV update",
  };

  let causalSentence: { label: string; title: string | null } | null = null;
  if (trigger && triggerArticle) {
    causalSentence = { label: TRIGGER_LABELS[trigger] ?? "Elevated", title: triggerArticle.title };
  } else if (status.score === 0) {
    causalSentence = { label: "No notable threats", title: null };
  } else {
    causalSentence = { label: "Elevated", title: "by recent activity" };
  }

  // Sticky cooldown subtitle: shown when displayed_level > raw_level (less severe raw, holding)
  const showSticky =
    status.sticky_until &&
    typeof status.raw_level === "number" &&
    typeof status.displayed_level === "number" &&
    status.displayed_level < status.raw_level;
  const stickyHoursLeft = showSticky
    ? Math.max(0, Math.ceil((new Date(status.sticky_until!).getTime() - Date.now()) / 3_600_000))
    : 0;

  const sparkScores = history.map(h => h.score);
  const minScore = sparkScores.length ? Math.min(...sparkScores) : 0;
  const maxScore = sparkScores.length ? Math.max(...sparkScores) : 100;
  const yPad = Math.max((maxScore - minScore) * 0.15, 1);
  const yDomain: [number, number] = [minScore - yPad, maxScore + yPad];
  const midIdx = Math.floor((history.length - 1) / 2);
  const gradId = `areaGrad-${status.level}`;

  return (
    <div className={`rounded-xl border ${level.border} ${level.bg} p-5 flex flex-col gap-4`}>

      {/* Title row */}
      <div className="flex items-center justify-between">
        <h2 className="text-xs font-semibold tracking-widest uppercase text-gray-500 dark:text-gray-500">
          Cybersecurity Defcon
        </h2>
        <div className={`flex items-center gap-1 text-xs ${trendColor}`}>
          <TrendIcon className="w-3 h-3" />
          <span className="capitalize">{status.trend}</span>
        </div>
      </div>

      {/* SVG Gauge */}
      <div className="flex justify-center">
        <svg viewBox="0 0 200 155" className="w-full max-w-[240px]" aria-label={`DEFCON ${status.level}: ${level.term}`}>

          {/* Background track */}
          <path
            d={arcPath(R, START_ANGLE, START_ANGLE + SWEEP)}
            fill="none"
            stroke="#1f2937"
            strokeWidth={TRACK_W}
            strokeLinecap="round"
          />

          {/* Coloured segments */}
          {SEGMENTS.map((seg) => (
            <path
              key={seg.start}
              d={arcPath(R, seg.start, seg.end)}
              fill="none"
              stroke={seg.color}
              strokeWidth={TRACK_W}
              opacity={0.85}
            />
          ))}

          {/* Score fill overlay — bright arc from start to needle */}
          <path
            d={arcPath(R, START_ANGLE, needleAngle)}
            fill="none"
            stroke={level.color}
            strokeWidth={TRACK_W}
            strokeLinecap="round"
            opacity={0.3}
          />

          {/* Needle */}
          <polygon
            points={`${needleTip.x.toFixed(2)},${needleTip.y.toFixed(2)} ${needleL.x.toFixed(2)},${needleL.y.toFixed(2)} ${needleR.x.toFixed(2)},${needleR.y.toFixed(2)}`}
            className="fill-black dark:fill-white"
            opacity={0.9}
          />
          {/* Needle pivot */}
          <circle cx={CX} cy={CY} r={5} className="fill-black dark:fill-white" opacity={0.9} />
          <circle cx={CX} cy={CY} r={3} fill={level.color} />

          {/* Level number, term, score — glow only these at DEFCON 1 */}
          <g className={status.level === 1 ? "defcon1-glow-svg" : undefined}>
            <text
              x={CX} y={CY + 32}
              textAnchor="middle"
              fontSize="28"
              fontWeight="bold"
              fontFamily="monospace"
              fill={level.color}
            >
              {status.level}
            </text>
            <text
              x={CX} y={CY + 46}
              textAnchor="middle"
              fontSize="9"
              fontWeight="600"
              letterSpacing="1"
              fill={level.color}
              opacity={0.8}
            >
              {level.term}
            </text>
            <text
              x={CX} y={CY + 58}
              textAnchor="middle"
              fontSize="8"
              fill="#6b7280"
            >
              {score} / 100
            </text>
          </g>
        </svg>
      </div>

      {/* Causal sentence */}
      <div className="flex flex-col gap-1">
        <p className="text-xs text-gray-500 dark:text-gray-500 uppercase tracking-wider">
          Driver
        </p>
        <p className="text-sm text-gray-100">
          <span className="font-semibold" style={{ color: level.color }}>
            {causalSentence.label}
          </span>
          {causalSentence.title && (
            <>
              {": "}
              <span className="text-gray-300">{causalSentence.title}</span>
            </>
          )}
          {triggerAge && (
            <span className="text-gray-500 dark:text-gray-500"> · {triggerAge}</span>
          )}
        </p>
        {showSticky && (
          <p className="text-xs text-gray-500 italic">
            Holding at level {status.displayed_level} — recovering from earlier event
            {stickyHoursLeft > 0 ? ` (${stickyHoursLeft}h until reassessment)` : " (reassessing soon)"}
          </p>
        )}
      </div>

      {/* 24h sparkline */}
      {history.length > 1 && (
        <div>
          <p className="text-xs text-gray-500 dark:text-gray-600 mb-1">24h trend</p>
          <div style={{ height: 56 }} className="min-w-0 overflow-hidden">
            <ResponsiveContainer width="99%" height={56}>
              <AreaChart data={history} margin={{ top: 4, bottom: 0, left: 0, right: 2 }}>
                <defs>
                  <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={level.color} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={level.color} stopOpacity={0.05} />
                  </linearGradient>
                </defs>
                <XAxis
                  ticks={[0, midIdx, history.length - 1]}
                  tickFormatter={(i: number) =>
                    i === 0 ? "24h ago" : i === midIdx ? "12h" : "now"
                  }
                  tick={{ fontSize: 8, fill: "#4b5563" }}
                  axisLine={{ stroke: "#374151" }}
                  tickLine={false}
                  height={14}
                />
                <YAxis
                  domain={yDomain}
                  ticks={[minScore, maxScore]}
                  tickFormatter={(v: number) => v.toFixed(0)}
                  tick={{ fontSize: 8, fill: "#4b5563" }}
                  axisLine={false}
                  tickLine={false}
                  width={22}
                />
                <Tooltip
                  contentStyle={{ background: "#111827", border: "1px solid #374151", borderRadius: 6, fontSize: 11 }}
                  formatter={(v: number) => [v.toFixed(1), "Score"]}
                  labelFormatter={(idx: number) => {
                    const point = history[idx];
                    if (!point) return "";
                    return new Date(point.computed_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="score"
                  stroke={level.color}
                  strokeWidth={1.5}
                  fill={`url(#${gradId})`}
                  dot={(props: any) =>
                    props.index === history.length - 1
                      ? <circle key="now" cx={props.cx} cy={props.cy} r={2.5} fill={level.color} />
                      : <g key={props.index} />
                  }
                  isAnimationActive={false}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}
