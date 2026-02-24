import type { DimensionScore } from "../types/api";

const DIMENSIONS = [
  { key: "semantic",   label: "Semantic",   labelKo: "의미",  color: "#3b82f6" },
  { key: "contextual", label: "Contextual", labelKo: "문맥",  color: "#10b981" },
  { key: "form",       label: "Form",       labelKo: "형태",  color: "#f59e0b" },
  { key: "relational", label: "Relational", labelKo: "관계",  color: "#ef4444" },
  { key: "pragmatic",  label: "Pragmatic",  labelKo: "화용",  color: "#8b5cf6" },
];

interface Props {
  scores: DimensionScore[];
  size?: number;
}

export default function RadarChart({ scores, size = 300 }: Props) {
  const center = size / 2;
  const radius = size * 0.38;
  const levels = [20, 40, 60, 80, 100];
  const dims = DIMENSIONS;
  const angleStep = (2 * Math.PI) / dims.length;
  const startAngle = -Math.PI / 2;

  function polarToXY(angle: number, r: number) {
    return {
      x: center + r * Math.cos(angle),
      y: center + r * Math.sin(angle),
    };
  }

  // Grid pentagons
  const gridPaths = levels.map((level) => {
    const r = (level / 100) * radius;
    return dims
      .map((_, i) => {
        const { x, y } = polarToXY(startAngle + i * angleStep, r);
        return `${x},${y}`;
      })
      .join(" ");
  });

  // Data polygon
  const dataPoints = dims.map((dim, i) => {
    const score = scores.find((s) => s.dimension === dim.key)?.score ?? 0;
    const r = (score / 100) * radius;
    return polarToXY(startAngle + i * angleStep, r);
  });
  const dataPath = dataPoints.map((p) => `${p.x},${p.y}`).join(" ");

  // Axis lines + labels
  const axes = dims.map((dim, i) => {
    const angle = startAngle + i * angleStep;
    const outerPoint = polarToXY(angle, radius + 8);
    const labelPoint = polarToXY(angle, radius + 28);
    const score = scores.find((s) => s.dimension === dim.key)?.score;
    return { dim, outerPoint, labelPoint, score };
  });

  return (
    <svg viewBox={`0 0 ${size} ${size}`} className="radar-chart">
      {/* Grid pentagons */}
      {gridPaths.map((points, i) => (
        <polygon
          key={i}
          points={points}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth="1"
        />
      ))}

      {/* Level labels */}
      {levels.map((level) => {
        const r = (level / 100) * radius;
        const { x, y } = polarToXY(startAngle, r);
        return (
          <text key={level} x={x + 4} y={y - 4} fontSize="9" fill="#9ca3af" textAnchor="start">
            {level}
          </text>
        );
      })}

      {/* Axis lines */}
      {axes.map(({ dim, outerPoint }) => (
        <line
          key={dim.key}
          x1={center} y1={center}
          x2={outerPoint.x} y2={outerPoint.y}
          stroke="#d1d5db" strokeWidth="1"
        />
      ))}

      {/* Data polygon */}
      <polygon
        points={dataPath}
        fill="rgba(59, 130, 246, 0.2)"
        stroke="#3b82f6"
        strokeWidth="2"
      />

      {/* Data points */}
      {dataPoints.map((p, i) => (
        <circle
          key={i}
          cx={p.x} cy={p.y} r="4"
          fill={dims[i].color}
          stroke="white" strokeWidth="2"
        />
      ))}

      {/* Dimension labels */}
      {axes.map(({ dim, labelPoint, score }) => (
        <g key={dim.key}>
          <text
            x={labelPoint.x} y={labelPoint.y - 6}
            fontSize="11" fontWeight="600" fill="#374151"
            textAnchor="middle" dominantBaseline="middle"
          >
            {dim.labelKo}
          </text>
          <text
            x={labelPoint.x} y={labelPoint.y + 8}
            fontSize="10" fill={dim.color} fontWeight="700"
            textAnchor="middle" dominantBaseline="middle"
          >
            {score != null ? `${score}%` : "-"}
          </text>
        </g>
      ))}
    </svg>
  );
}
