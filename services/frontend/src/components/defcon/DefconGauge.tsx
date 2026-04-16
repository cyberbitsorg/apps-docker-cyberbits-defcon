import { LineChart, Line, ResponsiveContainer, Tooltip } from "recharts";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { DEFCON_LEVELS } from "../../lib/constants";
import type { DefconStatus, DefconHistoryPoint } from "../../types/defcon";

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
  { color: "#22c55e", start: START_ANGLE,       end: START_ANGLE + 48       }, // LOW
  { color: "#3b82f6", start: START_ANGLE + 48,  end: START_ANGLE + 96       }, // GUARDED
  { color: "#f59e0b", start: START_ANGLE + 96,  end: START_ANGLE + 144      }, // ELEVATED
  { color: "#ea580c", start: START_ANGLE + 144, end: START_ANGLE + 192      }, // HIGH
  { color: "#dc2626", start: START_ANGLE + 192, end: START_ANGLE + 240      }, // CRITICAL
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

  const factors = status.factors;
  const factorItems = factors ? [
    { label: "Volume",   value: factors.volume_score   },
    { label: "CVE",      value: factors.cve_score      },
    { label: "Impact",   value: factors.impact_score   },
    { label: "Keywords", value: factors.keyword_score  },
  ] : [];

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
        <svg viewBox="0 0 200 155" className="w-full max-w-[240px]" aria-label={`Defcon level ${status.level}: ${level.label}`}>

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
            fill="white"
            opacity={0.9}
          />
          {/* Needle pivot */}
          <circle cx={CX} cy={CY} r={5} fill="white" opacity={0.9} />
          <circle cx={CX} cy={CY} r={3} fill={level.color} />

          {/* Level number — placed below the arc, not overlapping it */}
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
            letterSpacing="3"
            fill={level.color}
            opacity={0.8}
          >
            {level.label}
          </text>
          <text
            x={CX} y={CY + 58}
            textAnchor="middle"
            fontSize="8"
            fill="#6b7280"
          >
            {score} / 100
          </text>
        </svg>
      </div>

      {/* Factor bars */}
      {factorItems.length > 0 && (
        <div className="grid grid-cols-2 gap-2">
          {factorItems.map((f) => (
            <div key={f.label} className="flex flex-col gap-0.5">
              <div className="flex justify-between text-xs text-gray-500 dark:text-gray-500">
                <span>{f.label}</span>
                <span>{f.value.toFixed(1)}</span>
              </div>
              <div className="h-1 rounded-full bg-gray-200 dark:bg-gray-800 overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{ width: `${(f.value / 25) * 100}%`, backgroundColor: level.color }}
                />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 24h sparkline */}
      {history.length > 1 && (
        <div>
          <p className="text-xs text-gray-500 dark:text-gray-600 mb-1">24h trend</p>
          <div style={{ height: 40 }} className="min-w-0 overflow-hidden">
            <ResponsiveContainer width="99%" height={40}>
              <LineChart data={history} margin={{ top: 4, bottom: 4, left: 0, right: 0 }}>
                <Tooltip
                  contentStyle={{ background: "#111827", border: "1px solid #374151", borderRadius: 6, fontSize: 11 }}
                  formatter={(v: number) => [v.toFixed(1), "Score"]}
                  labelFormatter={() => ""}
                />
                <Line
                  type="monotone"
                  dataKey="score"
                  stroke={level.color}
                  strokeWidth={1.5}
                  dot={false}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}
