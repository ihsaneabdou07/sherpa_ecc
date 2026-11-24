import { useMemo, useState } from "react";
import { geoMercator, geoPath } from "d3-geo";
import type { FeatureCollection, Geometry } from "geojson";
import { translations, type Lang } from "../i18n/translations";

export interface RegionProperties {
  id: string;
  code: number;
  name: string;
  apiRegion: string;
  hasDirectProfile: boolean;
  color: string;
  hint: string;
}

export interface MoroccoMapProps {
  selectedRegion: string;
  onSelectRegion: (regionName: string, apiRegion: string) => void;
  geoJsonData: FeatureCollection<Geometry, RegionProperties>;
  lang?: Lang;
}

export function MoroccoMap({
  selectedRegion,
  onSelectRegion,
  geoJsonData,
  lang = "fr",
}: MoroccoMapProps) {
  const [hoveredRegion, setHoveredRegion] = useState<RegionProperties | null>(null);
  const [showAllList, setShowAllList] = useState<boolean>(true);
  const t = translations[lang];

  const width = 320;
  const height = 380;

  const { featuresWithPaths, allRegions } = useMemo(() => {
    const projection = geoMercator().fitSize([width - 16, height - 16], geoJsonData);
    const pathGenerator = geoPath().projection(projection);

    const computed = geoJsonData.features.map((feature, index) => {
      const props = feature.properties;
      const d = pathGenerator(feature) ?? "";
      const centroid = pathGenerator.centroid(feature);
      return {
        feature,
        props,
        d,
        cx: Number.isFinite(centroid[0]) ? centroid[0] : 0,
        cy: Number.isFinite(centroid[1]) ? centroid[1] : 0,
        key: props.id || `${props.code}-${index}`,
      };
    });

    const sortedRegions = [...computed.map((item) => item.props)].sort(
      (a, b) => a.code - b.code
    );

    return { featuresWithPaths: computed, allRegions: sortedRegions };
  }, [geoJsonData]);

  const activeProps =
    hoveredRegion ??
    allRegions.find((r) => r.name === selectedRegion) ??
    null;

  const handleSelect = (props: RegionProperties) => {
    onSelectRegion(props.name, props.apiRegion);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontSize: 11,
          color: "#475569",
        }}
      >
        <span>
          <strong>{t.regionsCount}</strong> {t.regionsAccessible}
        </span>
        <button
          type="button"
          onClick={() => setShowAllList((prev) => !prev)}
          style={{
            background: "#f8fafc",
            border: "1px solid #cbd5e1",
            borderRadius: 6,
            padding: "2px 7px",
            fontSize: 10.5,
            cursor: "pointer",
            color: "#0f172a",
          }}
        >
          {showAllList ? t.hideList : t.showList}
        </button>
      </div>

      <div
        style={{
          background: "#f8fafc",
          border: "1px solid #e2e8f0",
          borderRadius: 10,
          padding: 6,
        }}
      >
        <svg
          viewBox={`0 0 ${width} ${height}`}
          role="group"
          aria-label={t.mapAriaLabel}
          style={{ width: "100%", height: "auto", display: "block" }}
        >
          <g transform="translate(8, 8)">
            {featuresWithPaths.map(({ key, props, d, cx, cy }) => {
              const isSelected = selectedRegion === props.name;
              const isHovered = hoveredRegion?.name === props.name;

              return (
                <g
                  key={key}
                  role="button"
                  tabIndex={0}
                  aria-label={`${props.code}. ${props.name} — ${props.hint}`}
                  aria-pressed={isSelected}
                  style={{ cursor: "pointer", outline: "none" }}
                  onMouseEnter={() => setHoveredRegion(props)}
                  onMouseLeave={() => setHoveredRegion(null)}
                  onFocus={() => setHoveredRegion(props)}
                  onBlur={() => setHoveredRegion(null)}
                  onClick={() => handleSelect(props)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      handleSelect(props);
                    }
                  }}
                >
                  <path
                    d={d}
                    fill={props.color}
                    fillOpacity={isHovered ? 1 : isSelected ? 0.96 : 0.76}
                    stroke={isSelected ? "#0f172a" : "#ffffff"}
                    strokeWidth={isSelected ? 2 : 1}
                    strokeLinejoin="round"
                    style={{ transition: "all 0.15s ease" }}
                  />
                  {props.hasDirectProfile && Number.isFinite(cx) && Number.isFinite(cy) && (
                    <circle
                      cx={cx}
                      cy={cy}
                      r={isSelected ? 4 : 2.6}
                      fill="#ffffff"
                      stroke="#0f172a"
                      strokeWidth={0.9}
                    />
                  )}
                </g>
              );
            })}
          </g>
        </svg>
      </div>

      {showAllList && (
        <div
          role="listbox"
          aria-label={t.listAriaLabel}
          style={{
            display: "grid",
            gridTemplateColumns: "1fr",
            gap: 4,
            maxHeight: 190,
            overflowY: "auto",
            paddingRight: 2,
          }}
        >
          {allRegions.map((reg) => {
            const isSelected = selectedRegion === reg.name;
            return (
              <button
                key={reg.id}
                type="button"
                role="option"
                aria-selected={isSelected}
                onClick={() => handleSelect(reg)}
                onMouseEnter={() => setHoveredRegion(reg)}
                onMouseLeave={() => setHoveredRegion(null)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: 6,
                  textAlign: "left",
                  background: isSelected ? "#ecfdf5" : "#ffffff",
                  border: isSelected ? "1.5px solid #059669" : "1px solid #e2e8f0",
                  borderRadius: 7,
                  padding: "5px 8px",
                  cursor: "pointer",
                  fontSize: 11,
                  fontWeight: isSelected ? 700 : 500,
                  color: "#0f172a",
                }}
              >
                <span style={{ display: "flex", alignItems: "center", gap: 6, minWidth: 0 }}>
                  <span
                    style={{
                      width: 9,
                      height: 9,
                      borderRadius: "50%",
                      background: reg.color,
                      flexShrink: 0,
                      border: "1px solid rgba(15,23,42,0.25)",
                    }}
                  />
                  <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {reg.code}. {reg.name}
                  </span>
                </span>
                <span
                  style={{
                    fontSize: 9,
                    color: reg.hasDirectProfile ? "#047857" : "#64748b",
                    background: reg.hasDirectProfile ? "#d1fae5" : "#f1f5f9",
                    padding: "1px 5px",
                    borderRadius: 999,
                    flexShrink: 0,
                  }}
                >
                  {reg.hasDirectProfile ? t.poleBadge : reg.apiRegion}
                </span>
              </button>
            );
          })}
        </div>
      )}

      <div
        role="status"
        aria-live="polite"
        style={{
          fontSize: 10.5,
          color: "#334155",
          background: "#f8fafc",
          border: "1px solid #e2e8f0",
          borderRadius: 8,
          padding: "6px 8px",
          lineHeight: 1.35,
        }}
      >
        {activeProps ? (
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 6 }}>
              <strong>
                {activeProps.code}. {activeProps.name}
              </strong>
              <span style={{ fontSize: 9.5, color: "#047857", fontWeight: 600 }}>
                {activeProps.hasDirectProfile
                  ? t.directProfile
                  : `${t.apiPolePrefix} : ${activeProps.apiRegion}`}
              </span>
            </div>
            <div style={{ color: "#475569", marginTop: 2 }}>{activeProps.hint}</div>
          </div>
        ) : (
          <span>{t.selectRegionPrompt}</span>
        )}
      </div>
    </div>
  );
}