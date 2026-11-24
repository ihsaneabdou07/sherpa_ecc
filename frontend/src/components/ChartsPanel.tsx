import { useState } from "react";
import type { ArchitectureItem } from "../types/studio";

interface ParetoPoint {
  cost: number;
  co2: number;
}

interface ChartsPanelProps {
  architectures: ArchitectureItem[];
  paretoOthers?: ParetoPoint[];
  selectedArchId?: string | null;
  onSelectArch?: (id: string) => void;
}

const AXES = [
  { key: "cost_score" as const, label: "Cost" },
  { key: "co2_score" as const, label: "CO2" },
  { key: "water_score" as const, label: "Water" },
  { key: "trl_score" as const, label: "Maturity" },
  { key: "efficiency_score" as const, label: "Efficiency" },
];

export function ChartsPanel({
  architectures,
  paretoOthers = [],
  selectedArchId,
  onSelectArch,
}: ChartsPanelProps) {
  const [hoveredArchId, setHoveredArchId] = useState<string | null>(null);
  const [hoveredPareto, setHoveredPareto] = useState<ParetoPoint | null>(null);

  if (!architectures || architectures.length === 0) {
    return null;
  }

  const unit = architectures[0]?.unit ?? "MAD/L";

  // --- 1. Configuration Pareto (SVG) ---
  const pWidth = 340;
  const pHeight = 200;
  const padLeft = 42;
  const padRight = 16;
  const padTop = 16;
  const padBottom = 34;

  const allCosts = [
    ...architectures.map((a) => a.cost),
    ...paretoOthers.map((p) => p.cost),
  ];
  const allCo2 = [
    ...architectures.map((a) => a.co2),
    ...paretoOthers.map((p) => p.co2),
  ];

  const minCost = Math.max(0, Math.min(...allCosts) * 0.9);
  const maxCost = Math.max(...allCosts) * 1.08 || 1;
  const minCo2 = 0;
  const maxCo2 = Math.max(...allCo2) * 1.12 || 1;

  const toParetoX = (cost: number) =>
    padLeft + ((cost - minCost) / (maxCost - minCost || 1)) * (pWidth - padLeft - padRight);
  const toParetoY = (co2: number) =>
    pHeight - padBottom - ((co2 - minCo2) / (maxCo2 - minCo2 || 1)) * (pHeight - padTop - padBottom);

  const activeArch =
    architectures.find((a) => a.id === hoveredArchId) ??
    architectures.find((a) => a.id === selectedArchId) ??
    null;

  // --- 2. Configuration Radar (SVG) ---
  const rSize = 220;
  const cx = rSize / 2;
  const cy = rSize / 2 + 4;
  const maxRadius = 74;
  const numAxes = AXES.length;

  const polarToCartesian = (angleIndex: number, valuePct: number) => {
    const clamped = Math.max(0, Math.min(100, valuePct));
    const r = (clamped / 100) * maxRadius;
    const angle = -Math.PI / 2 + (angleIndex * 2 * Math.PI) / numAxes;
    return {
      x: cx + r * Math.cos(angle),
      y: cy + r * Math.sin(angle),
    };
  };

  return (
    <div style={{ marginTop: 18, paddingTop: 14, borderTop: "1px solid #e2e8f0" }}>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, alignItems: "center" }}>
        {/* Graphique Pareto */}
        <div
          style={{
            background: "#f8fafc",
            borderRadius: 10,
            padding: 10,
            border: "1px solid #e2e8f0",
          }}
        >
          <div style={{ fontSize: 12, fontWeight: 600, color: "#334155", marginBottom: 6 }}>
            📉 Pareto frontier (Cost vs CO2)
          </div>

          <svg viewBox={`0 0 ${pWidth} ${pHeight}`} style={{ width: "100%", height: "auto", display: "block" }}>
            {/* Axes */}
            <line
              x1={padLeft}
              y1={padTop}
              x2={padLeft}
              y2={pHeight - padBottom}
              stroke="#cbd5e1"
              strokeWidth={1}
            />
            <line
              x1={padLeft}
              y1={pHeight - padBottom}
              x2={pWidth - padRight}
              y2={pHeight - padBottom}
              stroke="#cbd5e1"
              strokeWidth={1}
            />

            {/* Labels axes */}
            <text
              x={(padLeft + pWidth - padRight) / 2}
              y={pHeight - 6}
              textAnchor="middle"
              fontSize="10"
              fill="#64748b"
            >
              Cost ({unit})
            </text>
            <text
              x={12}
              y={(padTop + pHeight - padBottom) / 2}
              textAnchor="middle"
              fontSize="10"
              fill="#64748b"
              transform={`rotate(-90 12 ${(padTop + pHeight - padBottom) / 2})`}
            >
              CO2 (kg/u)
            </text>

            {/* Points secondaires Pareto */}
            {paretoOthers.map((pt, idx) => {
              const isHovered =
                hoveredPareto?.cost === pt.cost && hoveredPareto?.co2 === pt.co2;
              return (
                <circle
                  key={`other-${idx}`}
                  cx={toParetoX(pt.cost)}
                  cy={toParetoY(pt.co2)}
                  r={isHovered ? 4.5 : 3}
                  fill={isHovered ? "#475569" : "#94a3b8"}
                  opacity={0.65}
                  style={{ cursor: "pointer" }}
                  onMouseEnter={() => {
                    setHoveredPareto(pt);
                    setHoveredArchId(null);
                  }}
                  onMouseLeave={() => setHoveredPareto(null)}
                />
              );
            })}

            {/* Points des 3 architectures */}
            {architectures.map((arch) => {
              const isHighlighted = hoveredArchId === arch.id || selectedArchId === arch.id;
              return (
                <g
                  key={arch.id}
                  style={{ cursor: "pointer" }}
                  onMouseEnter={() => {
                    setHoveredArchId(arch.id);
                    setHoveredPareto(null);
                  }}
                  onMouseLeave={() => setHoveredArchId(null)}
                  onClick={() => onSelectArch?.(arch.id)}
                >
                  <circle
                    cx={toParetoX(arch.cost)}
                    cy={toParetoY(arch.co2)}
                    r={isHighlighted ? 8 : 6}
                    fill={arch.color}
                    stroke="#ffffff"
                    strokeWidth={2}
                  />
                  <text
                    x={toParetoX(arch.cost)}
                    y={toParetoY(arch.co2) - 10}
                    textAnchor="middle"
                    fontSize="10"
                    fontWeight="700"
                    fill={arch.color}
                  >
                    #{arch.rank}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>

        {/* Graphique Radar + Légende */}
        <div
          style={{
            background: "#f8fafc",
            borderRadius: 10,
            padding: 10,
            border: "1px solid #e2e8f0",
          }}
        >
          <div style={{ fontSize: 12, fontWeight: 600, color: "#334155", marginBottom: 4 }}>
            🕸️ Multi-criteria profile
          </div>

          <svg viewBox={`0 0 ${rSize} ${rSize}`} style={{ width: "100%", height: "auto", display: "block" }}>
            {/* Cercles concentriques */}
            {[25, 50, 75, 100].map((level) => (
              <circle
                key={level}
                cx={cx}
                cy={cy}
                r={(level / 100) * maxRadius}
                fill="none"
                stroke="#e2e8f0"
                strokeWidth={1}
              />
            ))}

            {/* Axes et étiquettes */}
            {AXES.map((axis, i) => {
              const tip = polarToCartesian(i, 100);
              const labelPos = polarToCartesian(i, 120);
              return (
                <g key={axis.key}>
                  <line x1={cx} y1={cy} x2={tip.x} y2={tip.y} stroke="#cbd5e1" strokeWidth={1} />
                  <text
                    x={labelPos.x}
                    y={labelPos.y + 3}
                    textAnchor="middle"
                    fontSize="9.5"
                    fill="#475569"
                    fontWeight="600"
                  >
                    {axis.label}
                  </text>
                </g>
              );
            })}

            {/* Polygones des architectures */}
            {architectures.map((arch) => {
              const isHighlighted = hoveredArchId === arch.id || selectedArchId === arch.id;
              const points = AXES.map((axis, i) => {
                const pt = polarToCartesian(i, arch.radar[axis.key]);
                return `${pt.x},${pt.y}`;
              }).join(" ");

              return (
                <polygon
                  key={arch.id}
                  points={points}
                  fill={arch.color}
                  fillOpacity={isHighlighted ? 0.28 : 0.12}
                  stroke={arch.color}
                  strokeWidth={isHighlighted ? 2.5 : 1.6}
                  style={{ cursor: "pointer", transition: "all 0.15s ease" }}
                  onMouseEnter={() => setHoveredArchId(arch.id)}
                  onMouseLeave={() => setHoveredArchId(null)}
                  onClick={() => onSelectArch?.(arch.id)}
                />
              );
            })}
          </svg>

          {/* Légende interactive sous le radar */}
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 6, justifyContent: "center" }}>
            {architectures.map((arch) => {
              const active = hoveredArchId === arch.id || selectedArchId === arch.id;
              return (
                <button
                  key={arch.id}
                  type="button"
                  onMouseEnter={() => setHoveredArchId(arch.id)}
                  onMouseLeave={() => setHoveredArchId(null)}
                  onClick={() => onSelectArch?.(arch.id)}
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 5,
                    fontSize: 11,
                    fontWeight: active ? 700 : 500,
                    background: active ? "#ffffff" : "transparent",
                    border: active ? `1.5px solid ${arch.color}` : "1px solid #cbd5e1",
                    borderRadius: 999,
                    padding: "2px 8px",
                    cursor: "pointer",
                    color: "#0f172a",
                  }}
                >
                  <span
                    style={{
                      width: 8,
                      height: 8,
                      borderRadius: "50%",
                      background: arch.color,
                      display: "inline-block",
                    }}
                  />
                  <span>
                    #{arch.rank} {arch.badge}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Barre d'inspection dynamique au survol / sélection */}
      <div
        style={{
          marginTop: 10,
          padding: "8px 12px",
          borderRadius: 8,
          background: "#f1f5f9",
          fontSize: 12,
          color: "#334155",
          minHeight: 34,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 10,
          flexWrap: "wrap",
        }}
      >
        {activeArch ? (
          <>
            <div>
              <strong style={{ color: activeArch.color }}>
                #{activeArch.rank} {activeArch.badge}
              </strong>{" "}
              — Coût : <strong>{activeArch.cost} {activeArch.unit}</strong> | CO2 :{" "}
              <strong>{activeArch.co2} kg CO2/u</strong> | Eau :{" "}
              <strong>{activeArch.water} L/u</strong>
            </div>
            <div style={{ fontSize: 11, color: "#64748b" }}>
              Scores : Cost {activeArch.radar.cost_score} · CO2 {activeArch.radar.co2_score} · Water{" "}
              {activeArch.radar.water_score} · Eff. {activeArch.radar.efficiency_score}
            </div>
          </>
        ) : hoveredPareto ? (
          <div>
            Point alternatif — Coût : <strong>{hoveredPareto.cost} {unit}</strong> | CO2 :{" "}
            <strong>{hoveredPareto.co2} kg CO2/u</strong>
          </div>
        ) : (
          <span style={{ color: "#64748b" }}>
            Survole ou clique sur un point, une courbe radar ou la légende pour inspecter les valeurs exactes.
          </span>
        )}
      </div>
    </div>
  );
}