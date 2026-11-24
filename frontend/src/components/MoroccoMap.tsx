import { useState } from "react";

interface MoroccoMapProps {
  selectedRegion: string;
  onSelectRegion: (region: string) => void;
}

interface MoroccoRegion {
  id: string;
  name: string;
  apiRegion: string;
  baseColor: string;
  hasDirectProfile: boolean;
  path: string;
  cx: number;
  cy: number;
  hint: string;
}

const MOROCCO_REGIONS: MoroccoRegion[] = [
  {
    id: "tanger-tetouan-al-hoceima",
    name: "Tanger-Tétouan-Al Hoceïma",
    apiRegion: "Oriental",
    baseColor: "#0e89a8",
    hasDirectProfile: false,
    path: "M 152 14 C 166 12, 182 14, 194 24 C 198 30, 192 38, 182 40 C 170 42, 156 42, 148 36 C 145 28, 147 18, 152 14 Z",
    cx: 171,
    cy: 27,
    hint: "Détroit & Nord · Éolien fort · Rattaché : Oriental",
  },
  {
    id: "oriental",
    name: "Oriental",
    apiRegion: "Oriental",
    baseColor: "#009688",
    hasDirectProfile: true,
    path: "M 194 24 C 212 22, 232 24, 240 34 C 244 48, 238 68, 224 82 C 212 92, 198 94, 190 84 C 186 70, 188 46, 194 24 Z",
    cx: 214,
    cy: 56,
    hint: "EnR mixtes · FLH ~3550 h · LCOE ~0.030 €/kWh",
  },
  {
    id: "fes-meknes",
    name: "Fès-Meknès",
    apiRegion: "Oriental",
    baseColor: "#9c2780",
    hasDirectProfile: false,
    path: "M 148 36 C 164 38, 182 38, 190 42 C 194 56, 190 72, 176 78 C 162 82, 150 74, 146 60 Z",
    cx: 169,
    cy: 58,
    hint: "Nord-Est / Atlas · Rattaché : Oriental",
  },
  {
    id: "rabat-sale-kenitra",
    name: "Rabat-Salé-Kénitra",
    apiRegion: "Casablanca-Settat",
    baseColor: "#9e1b24",
    hasDirectProfile: false,
    path: "M 134 40 C 142 36, 148 36, 152 38 C 152 50, 148 60, 138 64 C 130 60, 128 48, 134 40 Z",
    cx: 141,
    cy: 50,
    hint: "Littoral Atlantique · Rattaché : Casablanca-Settat",
  },
  {
    id: "casablanca-settat",
    name: "Casablanca-Settat",
    apiRegion: "Casablanca-Settat",
    baseColor: "#7e489c",
    hasDirectProfile: true,
    path: "M 114 62 C 124 58, 134 58, 140 62 C 142 74, 136 86, 122 88 C 110 84, 108 72, 114 62 Z",
    cx: 126,
    cy: 74,
    hint: "Pôle industriel · FLH ~2950 h · LCOE ~0.035 €/kWh",
  },
  {
    id: "beni-mellal-khenifra",
    name: "Béni Mellal-Khénifra",
    apiRegion: "Casablanca-Settat",
    baseColor: "#f39aa4",
    hasDirectProfile: false,
    path: "M 140 64 C 154 66, 168 72, 172 82 C 164 94, 148 98, 136 92 C 134 80, 136 70, 140 64 Z",
    cx: 153,
    cy: 80,
    hint: "Moyen Atlas · Rattaché : Casablanca-Settat",
  },
  {
    id: "marrakech-safi",
    name: "Marrakech-Safi",
    apiRegion: "Souss-Massa",
    baseColor: "#f5d020",
    hasDirectProfile: false,
    path: "M 92 84 C 104 82, 114 84, 122 88 C 132 90, 138 94, 138 104 C 126 114, 106 116, 90 110 C 86 100, 88 90, 92 84 Z",
    cx: 112,
    cy: 99,
    hint: "Solaire élevé · Rattaché : Souss-Massa",
  },
  {
    id: "draa-tafilalet",
    name: "Drâa-Tafilalet",
    apiRegion: "Souss-Massa",
    baseColor: "#7d4923",
    hasDirectProfile: false,
    path: "M 138 94 C 158 88, 182 84, 198 88 C 202 104, 190 124, 172 134 C 152 138, 136 130, 134 114 Z",
    cx: 166,
    cy: 111,
    hint: "Fort gisement solaire · Rattaché : Souss-Massa",
  },
  {
    id: "souss-massa",
    name: "Souss-Massa",
    apiRegion: "Souss-Massa",
    baseColor: "#f37b16",
    hasDirectProfile: true,
    path: "M 76 112 C 92 110, 114 112, 134 114 C 136 126, 128 138, 110 142 C 90 142, 76 134, 72 122 Z",
    cx: 104,
    cy: 127,
    hint: "Solaire + Dessalement · FLH ~3400 h · LCOE ~0.031 €/kWh",
  },
  {
    id: "guelmim-oued-noun",
    name: "Guelmim-Oued Noun",
    apiRegion: "Laâyoune",
    baseColor: "#c8191e",
    hasDirectProfile: false,
    path: "M 54 138 C 72 136, 94 138, 112 142 C 106 156, 88 168, 66 170 C 52 164, 48 150, 54 138 Z",
    cx: 80,
    cy: 154,
    hint: "Porte du Sahara · Rattaché : Laâyoune",
  },
  {
    id: "laayoune-sakia-el-hamra",
    name: "Laâyoune-Sakia El Hamra",
    apiRegion: "Laâyoune",
    baseColor: "#46941b",
    hasDirectProfile: true,
    path: "M 34 166 C 52 166, 76 168, 122 168 L 122 214 L 58 214 C 42 214, 30 202, 28 186 C 28 176, 30 170, 34 166 Z",
    cx: 74,
    cy: 190,
    hint: "Éolien/Solaire fort · FLH ~4050 h · LCOE ~0.026 €/kWh",
  },
  {
    id: "dakhla-oued-eddahab",
    name: "Dakhla-Oued Eddahab",
    apiRegion: "Dakhla-Oued Eddahab",
    baseColor: "#99ca63",
    hasDirectProfile: true,
    path: "M 24 214 L 96 214 C 88 238, 74 266, 56 292 L 16 292 C 18 264, 20 238, 24 214 Z",
    cx: 52,
    cy: 252,
    hint: "Référence H2/e-fuels · FLH ~4300 h · LCOE ~0.024 €/kWh",
  },
];

const CORE_REGIONS = [
  "Oriental",
  "Casablanca-Settat",
  "Souss-Massa",
  "Laâyoune",
  "Dakhla-Oued Eddahab",
];

export function MoroccoMap({ selectedRegion, onSelectRegion }: MoroccoMapProps) {
  const [hovered, setHovered] = useState<MoroccoRegion | null>(null);

  return (
    <div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "136px 1fr",
          gap: 8,
          alignItems: "center",
          background: "#f1f3f5",
          border: "1px solid #e2e8f0",
          borderRadius: 10,
          padding: 8,
        }}
      >
        <svg viewBox="4 6 244 294" style={{ width: "100%", height: "auto", display: "block" }}>
          {MOROCCO_REGIONS.map((reg) => {
            const isSelected = selectedRegion === reg.apiRegion && reg.hasDirectProfile;
            const isHovered = hovered?.id === reg.id;

            return (
              <g
                key={reg.id}
                style={{ cursor: "pointer" }}
                onMouseEnter={() => setHovered(reg)}
                onMouseLeave={() => setHovered(null)}
                onClick={() => onSelectRegion(reg.apiRegion)}
              >
                <path
                  d={reg.path}
                  fill={reg.baseColor}
                  fillOpacity={isHovered ? 1 : isSelected ? 0.96 : 0.86}
                  stroke={isSelected ? "#0f172a" : "#ffffff"}
                  strokeWidth={isSelected ? 2 : 1.1}
                  strokeLinejoin="round"
                  style={{ transition: "all 0.15s ease" }}
                />
                {reg.hasDirectProfile && (
                  <circle
                    cx={reg.cx}
                    cy={reg.cy}
                    r={isSelected ? 3.5 : 2.3}
                    fill="#ffffff"
                    stroke="#0f172a"
                    strokeWidth={0.8}
                  />
                )}
              </g>
            );
          })}
        </svg>

        <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
          {CORE_REGIONS.map((label) => {
            const isSelected = selectedRegion === label;
            const matchingRegion = MOROCCO_REGIONS.find(
              (r) => r.apiRegion === label && r.hasDirectProfile
            );
            return (
              <button
                key={label}
                type="button"
                onClick={() => onSelectRegion(label)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                  textAlign: "left",
                  background: isSelected ? "#ecfdf5" : "#ffffff",
                  border: isSelected ? "1.5px solid #059669" : "1px solid #cbd5e1",
                  borderRadius: 7,
                  padding: "4px 7px",
                  cursor: "pointer",
                  fontSize: 11,
                  fontWeight: isSelected ? 700 : 500,
                  color: "#0f172a",
                }}
              >
                <span
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: "50%",
                    flexShrink: 0,
                    background: matchingRegion?.baseColor ?? "#059669",
                    border: isSelected ? "2px solid #0f172a" : "1px solid #ffffff",
                    boxShadow: "0 0 0 1px rgba(15,23,42,0.2)",
                  }}
                />
                <span style={{ lineHeight: 1.15 }}>{label}</span>
              </button>
            );
          })}
        </div>
      </div>

      <div style={{ fontSize: 10.5, color: "#475569", marginTop: 6, minHeight: 28, lineHeight: 1.3 }}>
        {hovered ? (
          <>
            <strong>{hovered.name}</strong> — {hovered.hint}
          </>
        ) : (
          <>
            Pôle actif : <strong>{selectedRegion}</strong>
          </>
        )}
      </div>
    </div>
  );
}