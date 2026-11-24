import { useEffect, useState } from "react";
import type { FeatureCollection, Geometry } from "geojson";
import moroccoGeoJson from "./data/morocco-12-regions.geo.json";
import { MoroccoMap, type RegionProperties } from "./components/MoroccoMap";
import { ChartsPanel, type SensitivityPoint } from "./components/ChartsPanel";
import { translations, type Lang } from "./i18n/translations";

const API_BASE = "http://127.0.0.1:8000";

const typedGeoJson = moroccoGeoJson as FeatureCollection<Geometry, RegionProperties>;

const CITIES_BY_REGION: Record<string, string[]> = {
  "Dakhla-Oued Eddahab": ["Dakhla"],
  "Laâyoune-Sakia El Hamra": ["Laâyoune", "Boujdour"],
  "Guelmim-Oued Noun": ["Tan-Tan", "Guelmim"],
  "Souss-Massa": ["Agadir"],
  "Marrakech-Safi": ["Safi", "Essaouira", "Marrakech"],
  "Drâa-Tafilalet": ["Ouarzazate"],
  "Casablanca-Settat": ["Jorf Lasfar", "Casablanca", "Mohammedia"],
  "Rabat-Salé-Kénitra": ["Kénitra", "Rabat"],
  "Tanger-Tétouan-Al Hoceïma": ["Tanger"],
  "Oriental": ["Nador", "Oujda"],
  "Fès-Meknès": ["Fès"],
  "Béni Mellal-Khénifra": ["Béni Mellal"],
};

interface RadarScores {
  cost_score: number;
  co2_score: number;
  water_score: number;
  trl_score: number;
  efficiency_score: number;
}

interface ArchitectureItem {
  id: string;
  rank: number;
  badge: string;
  color: string;
  cost: number;
  unit: string;
  co2: number;
  water: number;
  trl: string;
  radar: RadarScores;
  assumptions?: Record<string, string | number>;
}

interface ParetoPoint {
  cost: number;
  co2: number;
}

interface StudioRecommendResponse {
  architectures: ArchitectureItem[];
  pareto_others?: ParetoPoint[];
  sensitivity_curve?: SensitivityPoint[];
}

interface ChatMessage {
  role: "user" | "assistant";
  text: string;
  sources?: string[];
}

export function App() {
  const [lang, setLang] = useState<Lang>("fr");
  const t = translations[lang];

  const [regionName, setRegionName] = useState("Dakhla-Oued Eddahab");
  const [apiRegion, setApiRegion] = useState("Dakhla-Oued Eddahab");
  const [selectedCity, setSelectedCity] = useState<string>("");
  const [targetProduct, setTargetProduct] = useState("e-Methanol");
  const [production, setProduction] = useState(100000);
  const [studioData, setStudioData] = useState<StudioRecommendResponse | null>(null);
  const [selectedArchId, setSelectedArchId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);

  async function askAssistant(
    question: string,
    architectures: ArchitectureItem[],
    pole = apiRegion,
    prod = targetProduct,
    resetHistory = false,
    currentLang = lang,
    qty = production,
    city = selectedCity
  ) {
    const activeT = translations[currentLang];
    setChatLoading(true);
    const historyPayload = resetHistory
      ? []
      : messages.map((m) => ({ role: m.role, content: m.text }));

    if (resetHistory) {
      setMessages([{ role: "user", text: question }]);
    } else {
      setMessages((prev) => [...prev, { role: "user", text: question }]);
    }

    try {
      const chatRes = await fetch(`${API_BASE}/studio/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question,
          region: pole,
          city: city || undefined,
          target_product: prod,
          architectures,
          annual_production_tonnes: qty,
          lang: currentLang,
          history: historyPayload,
        }),
      });
      if (!chatRes.ok) {
        throw new Error(`HTTP ${chatRes.status}`);
      }
      const chatJson = await chatRes.json();
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: chatJson.reply, sources: chatJson.sources },
      ]);
    } catch (err) {
      console.error("Erreur Chat:", err);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: activeT.chatError,
        },
      ]);
    } finally {
      setChatLoading(false);
    }
  }

  async function fetchRecommendations(
    displayLocation = regionName,
    pole = apiRegion,
    prod = targetProduct,
    qty = production,
    currentLang = lang,
    city = selectedCity
  ) {
    const activeT = translations[currentLang];
    setLoading(true);
    setApiError(null);
    try {
      const res = await fetch(`${API_BASE}/studio/recommend`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          region: pole,
          city: city || undefined,
          target_product: prod,
          annual_production_tonnes: qty,
        }),
      });
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      const data: StudioRecommendResponse = await res.json();
      setStudioData(data);

      const firstArch = data.architectures?.[0] ?? null;
      setSelectedArchId(firstArch ? firstArch.id : null);

      const defaultQ = activeT.defaultQuestion(displayLocation);
      await askAssistant(defaultQ, data.architectures ?? [], pole, prod, true, currentLang, qty, city);
    } catch (err) {
      console.error("Erreur API:", err);
      setApiError(activeT.apiRecommendError);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchRecommendations();
  }, []);

  async function handleSendChat(customQuestion?: string) {
    const q = (customQuestion ?? chatInput).trim();
    if (!q || !studioData || chatLoading) return;
    if (!customQuestion) {
      setChatInput("");
    }
    await askAssistant(q, studioData.architectures, apiRegion, targetProduct, false, lang, production, selectedCity);
  }

  function triggerDownload(blob: Blob, filename: string) {
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  function getExportSlug() {
    const raw = selectedCity ? `${selectedCity}_${regionName}` : regionName;
    return raw
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-zA-Z0-9_-]+/g, "_")
      .toLowerCase();
  }

  function handleExportJson() {
    if (!studioData) return;
    const payload = {
      exported_at: new Date().toISOString(),
      project: {
        region: regionName,
        city: selectedCity || null,
        target_product: targetProduct,
        annual_production_tonnes: production,
      },
      architectures: studioData.architectures,
      sensitivity_curve: studioData.sensitivity_curve ?? [],
      pareto_others: studioData.pareto_others ?? [],
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json;charset=utf-8" });
    triggerDownload(blob, `sherpa_h2_${getExportSlug()}_${targetProduct.toLowerCase()}.json`);
  }

  async function handleExportExcel() {
    if (!studioData) return;
    try {
      const res = await fetch(`${API_BASE}/studio/export-excel`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          region: apiRegion,
          city: selectedCity || undefined,
          target_product: targetProduct,
          annual_production_tonnes: production,
          lang,
        }),
      });
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      const blob = await res.blob();
      triggerDownload(blob, `sherpa_h2_${getExportSlug()}_${targetProduct.toLowerCase()}.xlsx`);
    } catch (err) {
      console.error("Erreur Export Excel:", err);
      setApiError(t.apiRecommendError);
    }
  }

  const selectedArch =
    studioData?.architectures.find((a) => a.id === selectedArchId) ??
    studioData?.architectures[0] ??
    null;

  const currentDisplayLocation = selectedCity ? `${selectedCity} (${regionName})` : regionName;

  return (
    <div style={{ minHeight: "100vh", background: "#f1f5f9", fontFamily: "Inter, system-ui, sans-serif", color: "#0f172a" }}>
      <style>{`
        .studio-grid {
          display: grid;
          grid-template-columns: 290px minmax(0, 1fr) 340px;
          gap: 16px;
          padding: 16px;
          align-items: start;
        }
        .studio-col {
          min-width: 0;
        }
        .arch-cards-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(215px, 1fr));
          gap: 12px;
        }
        @media (max-width: 1220px) {
          .studio-grid {
            grid-template-columns: 280px minmax(0, 1fr);
          }
          .studio-assistant {
            grid-column: 1 / -1;
          }
        }
        @media (max-width: 760px) {
          .studio-grid {
            grid-template-columns: minmax(0, 1fr);
            padding: 12px;
          }
          .studio-assistant {
            grid-column: auto;
          }
        }
      `}</style>

      {/* Barre supérieure */}
      <header
        style={{
          background: "#fff",
          borderBottom: "1px solid #e2e8f0",
          padding: "10px 20px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 10,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ background: "#059669", color: "#fff", padding: "4px 8px", borderRadius: 8, fontSize: 16 }}>
            🌱
          </div>
          <strong style={{ fontSize: 16 }}>
            <span style={{ color: "#047857" }}>H2-Maroc</span> Decision Studio
          </strong>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 12 }}>
          {/* Sélecteur interactif FR | EN */}
          <div
            role="group"
            aria-label="Language switcher"
            style={{
              display: "inline-flex",
              alignItems: "center",
              background: "#f1f5f9",
              padding: 3,
              borderRadius: 999,
              border: "1px solid #e2e8f0",
            }}
          >
            <button
              type="button"
              onClick={() => setLang("fr")}
              aria-pressed={lang === "fr"}
              style={{
                border: "none",
                borderRadius: 999,
                padding: "3px 9px",
                fontSize: 11.5,
                fontWeight: lang === "fr" ? 700 : 500,
                background: lang === "fr" ? "#ffffff" : "transparent",
                color: lang === "fr" ? "#047857" : "#64748b",
                boxShadow: lang === "fr" ? "0 1px 2px rgba(15,23,42,0.08)" : "none",
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
            >
              FR
            </button>
            <button
              type="button"
              onClick={() => setLang("en")}
              aria-pressed={lang === "en"}
              style={{
                border: "none",
                borderRadius: 999,
                padding: "3px 9px",
                fontSize: 11.5,
                fontWeight: lang === "en" ? 700 : 500,
                background: lang === "en" ? "#ffffff" : "transparent",
                color: lang === "en" ? "#047857" : "#64748b",
                boxShadow: lang === "en" ? "0 1px 2px rgba(15,23,42,0.08)" : "none",
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
            >
              EN
            </button>
          </div>

          <span style={{ background: "#0f172a", color: "#fff", padding: "5px 10px", borderRadius: 999 }}>
            SHERPA ECC
          </span>
        </div>
      </header>

      {/* Grille responsive */}
      <div className="studio-grid">
        {/* Colonne 1 : Projet */}
        <aside className="studio-col" style={{ background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", padding: 16 }}>
          <h3 style={{ margin: "0 0 14px", fontSize: 15 }}>🎯 {t.yourProject}</h3>

          <div style={{ fontSize: 12, fontWeight: 600, color: "#475569", marginBottom: 8 }}>🗺️ {t.targetRegion}</div>
          <MoroccoMap
            selectedRegion={regionName}
            geoJsonData={typedGeoJson}
            lang={lang}
            onSelectRegion={(name, pole) => {
              setRegionName(name);
              setApiRegion(pole);
              setSelectedCity("");
              fetchRecommendations(name, pole, targetProduct, production, lang, "");
            }}
          />

          <div style={{ fontSize: 12, fontWeight: 600, color: "#475569", margin: "12px 0 6px" }}>
            🏙️ {lang === "en" ? "City / Industrial hub (optional)" : "Ville / Pôle industriel (optionnel)"}
          </div>
          <select
            value={selectedCity}
            onChange={(e) => {
              const nextCity = e.target.value;
              setSelectedCity(nextCity);
              const foundRegion =
                Object.entries(CITIES_BY_REGION).find(([, cities]) => cities.includes(nextCity))?.[0] ??
                regionName;
              setRegionName(foundRegion);
              setApiRegion(foundRegion);
              const label = nextCity ? `${nextCity} (${foundRegion})` : foundRegion;
              fetchRecommendations(label, foundRegion, targetProduct, production, lang, nextCity);
            }}
            style={{ width: "100%", padding: "8px 10px", borderRadius: 8, border: "1px solid #cbd5e1", fontSize: 13 }}
          >
            <option value="">
              {lang === "en" ? `All region (${regionName})` : `Toute la région (${regionName})`}
            </option>
            {Object.entries(CITIES_BY_REGION).map(([reg, cities]) => (
              <optgroup key={reg} label={reg}>
                {cities.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </optgroup>
            ))}
          </select>

          <div style={{ fontSize: 12, fontWeight: 600, color: "#475569", margin: "16px 0 6px" }}>🧪 {t.targetProduct}</div>
          <select
            value={targetProduct}
            onChange={(e) => {
              const nextProd = e.target.value;
              setTargetProduct(nextProd);
              fetchRecommendations(currentDisplayLocation, apiRegion, nextProd, production, lang, selectedCity);
            }}
            style={{ width: "100%", padding: "8px 10px", borderRadius: 8, border: "1px solid #cbd5e1", fontSize: 13 }}
          >
            <option value="e-Methanol">{t.products["e-Methanol"]}</option>
            <option value="Green hydrogen">{t.products["Green hydrogen"]}</option>
            <option value="e-Diesel">{t.products["e-Diesel"]}</option>
            <option value="e-Methane">{t.products["e-Methane"]}</option>
          </select>

          <div style={{ fontSize: 12, fontWeight: 600, color: "#475569", margin: "16px 0 6px" }}>📊 {t.annualProduction}</div>
          <div style={{ display: "flex", border: "1px solid #cbd5e1", borderRadius: 8, overflow: "hidden" }}>
            <input
              type="number"
              min={1}
              value={production}
              onChange={(e) => setProduction(Math.max(1, Number(e.target.value)))}
              style={{ width: "100%", minWidth: 0, border: "none", padding: "8px 10px", fontSize: 13 }}
            />
            <span style={{ background: "#f8fafc", padding: "8px 10px", fontSize: 11, color: "#64748b", whiteSpace: "nowrap" }}>
              {t.tonnesPerYear}
            </span>
          </div>

          <button
            type="button"
            onClick={() => fetchRecommendations(currentDisplayLocation, apiRegion, targetProduct, production, lang, selectedCity)}
            disabled={loading}
            style={{
              marginTop: 18,
              width: "100%",
              background: loading ? "#6ee7b7" : "#059669",
              color: "#fff",
              border: "none",
              borderRadius: 10,
              padding: "10px 14px",
              fontWeight: 600,
              cursor: loading ? "not-allowed" : "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 8,
            }}
          >
            <span>🔍</span>
            {loading ? t.calculating : t.findArchitectures}
          </button>
        </aside>

        {/* Colonne 2 : Architectures recommandées + Graphiques */}
        <main className="studio-col">
          <div style={{ background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", padding: 16 }}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                flexWrap: "wrap",
                gap: 8,
                marginBottom: 14,
              }}
            >
              <h3 style={{ margin: 0, fontSize: 15, lineHeight: 1.35 }}>
                ⚡ {t.recommendedTitle} — <span style={{ color: "#047857" }}>{currentDisplayLocation}</span>
              </h3>

              <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                {selectedArch && (
                  <span
                    style={{
                      fontSize: 11.5,
                      color: "#334155",
                      background: "#f8fafc",
                      border: "1px solid #e2e8f0",
                      padding: "3px 9px",
                      borderRadius: 999,
                    }}
                  >
                    {t.focusLabel} : <strong style={{ color: selectedArch.color }}>#{selectedArch.rank} {selectedArch.badge}</strong>
                  </span>
                )}

                {studioData && (
                  <div style={{ display: "inline-flex", gap: 6 }}>
                    <button
                      type="button"
                      onClick={handleExportExcel}
                      title={lang === "en" ? "Export detailed styled workbook (.xlsx)" : "Exporter le classeur Excel détaillé (.xlsx)"}
                      style={{
                        fontSize: 11.5,
                        fontWeight: 600,
                        color: "#047857",
                        background: "#ecfdf5",
                        border: "1px solid #a7f3d0",
                        padding: "3px 9px",
                        borderRadius: 8,
                        cursor: "pointer",
                      }}
                    >
                      📊 {lang === "en" ? "Export Excel (.xlsx)" : "Exporter Excel (.xlsx)"}
                    </button>
                    <button
                      type="button"
                      onClick={handleExportJson}
                      title={lang === "en" ? "Export full analysis as JSON" : "Exporter l'analyse complète en JSON"}
                      style={{
                        fontSize: 11.5,
                        fontWeight: 600,
                        color: "#334155",
                        background: "#f8fafc",
                        border: "1px solid #cbd5e1",
                        padding: "3px 9px",
                        borderRadius: 8,
                        cursor: "pointer",
                      }}
                    >
                      📥 JSON
                    </button>
                  </div>
                )}
              </div>
            </div>

            {apiError && (
              <div
                style={{
                  background: "#fef2f2",
                  border: "1px solid #fecaca",
                  color: "#991b1b",
                  borderRadius: 10,
                  padding: "10px 12px",
                  fontSize: 12.5,
                  marginBottom: 12,
                }}
              >
                {apiError}
              </div>
            )}

            {!studioData && !apiError && (
              <p style={{ fontSize: 13, color: "#64748b" }}>{t.loadingArchitectures}</p>
            )}

            {studioData && (
              <>
                <div className="arch-cards-grid">
                  {studioData.architectures.map((arch) => {
                    const isSelected = selectedArch?.id === arch.id;
                    return (
                      <div
                        key={arch.id}
                        role="button"
                        tabIndex={0}
                        onClick={() => setSelectedArchId(arch.id)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter" || e.key === " ") setSelectedArchId(arch.id);
                        }}
                        style={{
                          minWidth: 0,
                          border: `${isSelected ? 2 : 1.5}px solid ${arch.color}`,
                          borderRadius: 12,
                          padding: 14,
                          background: isSelected ? "#f8fafc" : "#ffffff",
                          boxShadow: isSelected ? "0 6px 16px rgba(15, 23, 42, 0.08)" : "0 1px 2px rgba(15, 23, 42, 0.03)",
                          cursor: "pointer",
                          transition: "all 0.15s ease",
                          display: "flex",
                          flexDirection: "column",
                          justifyContent: "space-between",
                        }}
                      >
                        <div>
                          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8, marginBottom: 10 }}>
                            <div style={{ display: "flex", alignItems: "center", gap: 8, minWidth: 0 }}>
                              <span
                                style={{
                                  background: arch.color,
                                  color: "#fff",
                                  width: 24,
                                  height: 24,
                                  borderRadius: "50%",
                                  display: "inline-flex",
                                  alignItems: "center",
                                  justifyContent: "center",
                                  fontSize: 12,
                                  fontWeight: 700,
                                  flexShrink: 0,
                                }}
                              >
                                {arch.rank}
                              </span>
                              <span style={{ fontWeight: 700, fontSize: 13.5, color: arch.color, lineHeight: 1.25 }}>
                                {arch.badge}
                              </span>
                            </div>
                            {isSelected && (
                              <span
                                style={{
                                  fontSize: 10,
                                  fontWeight: 600,
                                  color: arch.color,
                                  background: "#fff",
                                  border: `1px solid ${arch.color}`,
                                  borderRadius: 999,
                                  padding: "1px 6px",
                                  flexShrink: 0,
                                }}
                              >
                                {t.activeBadge}
                              </span>
                            )}
                          </div>

                          <div
                            style={{
                              display: "flex",
                              justifyContent: "space-around",
                              alignItems: "center",
                              background: "#f1f5f9",
                              padding: "7px 8px",
                              borderRadius: 8,
                              marginBottom: 12,
                              fontSize: 13,
                              color: "#475569",
                            }}
                          >
                            <span title={t.chainSolarWind}>☀️🌬️</span>
                            <span style={{ fontSize: 11, color: "#94a3b8" }}>→</span>
                            <span title={t.chainDesalination}>💧</span>
                            <span style={{ fontSize: 11, color: "#94a3b8" }}>→</span>
                            <span title={t.chainElectrolyzer}>🏭</span>
                          </div>

                          <div style={{ display: "flex", flexDirection: "column", gap: 9, fontSize: 13 }}>
                            <div style={{ display: "flex", alignItems: "center", gap: 9 }}>
                              <span style={{ fontSize: 15 }}>💰</span>
                              <div style={{ minWidth: 0 }}>
                                <div style={{ fontWeight: 700, color: "#0f172a" }}>
                                  {arch.cost} <span style={{ fontWeight: 600, fontSize: 12 }}>{arch.unit}</span>
                                </div>
                                <div style={{ fontSize: 11, color: "#64748b" }}>{t.productionCost}</div>
                              </div>
                            </div>

                            <div style={{ display: "flex", alignItems: "center", gap: 9 }}>
                              <span style={{ fontSize: 15 }}>🌱</span>
                              <div style={{ minWidth: 0 }}>
                                <div style={{ fontWeight: 700, color: "#0f172a" }}>{arch.co2} kg CO2/unit</div>
                                <div style={{ fontSize: 11, color: "#64748b" }}>{t.co2Emissions}</div>
                              </div>
                            </div>

                            <div style={{ display: "flex", alignItems: "center", gap: 9 }}>
                              <span style={{ fontSize: 15 }}>💧</span>
                              <div style={{ minWidth: 0 }}>
                                <div style={{ fontWeight: 700, color: "#0f172a" }}>{arch.water} L/unit</div>
                                <div style={{ fontSize: 11, color: "#64748b" }}>{t.waterUse}</div>
                              </div>
                            </div>
                          </div>
                        </div>

                        <div
                          style={{
                            marginTop: 12,
                            paddingTop: 8,
                            borderTop: "1px dashed #e2e8f0",
                            display: "flex",
                            justifyContent: "space-between",
                            alignItems: "center",
                            fontSize: 11.5,
                            color: "#334155",
                          }}
                        >
                          <span style={{ color: "#64748b" }}>⚙️ {t.maturity}</span>
                          <strong>{arch.trl}</strong>
                        </div>
                      </div>
                    );
                  })}
                </div>

                <ChartsPanel
                  architectures={studioData.architectures}
                  paretoOthers={studioData.pareto_others}
                  sensitivityCurve={studioData.sensitivity_curve}
                  selectedArchId={selectedArch?.id ?? null}
                  onSelectArch={(id) => setSelectedArchId(id)}
                  lang={lang}
                />
              </>
            )}
          </div>
        </main>

        {/* Colonne 3 : Assistant IA */}
        <aside
          className="studio-col studio-assistant"
          style={{
            background: "#fff",
            borderRadius: 14,
            border: "1px solid #e2e8f0",
            padding: 16,
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
          }}
        >
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
              <span>✨</span>
              <h3 style={{ margin: 0, fontSize: 15 }}>{t.aiAssistant}</h3>
            </div>

            {studioData && (
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 10 }}>
                {t.quickPrompts.map((prompt) => (
                  <button
                    key={prompt}
                    type="button"
                    onClick={() => handleSendChat(prompt)}
                    disabled={chatLoading}
                    style={{
                      fontSize: 10.5,
                      textAlign: "left",
                      background: "#f8fafc",
                      border: "1px solid #cbd5e1",
                      color: "#334155",
                      borderRadius: 8,
                      padding: "5px 8px",
                      cursor: "pointer",
                    }}
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            )}

            <div style={{ display: "flex", flexDirection: "column", gap: 10, maxHeight: 420, overflowY: "auto" }}>
              {messages.map((m, idx) => (
                <div
                  key={idx}
                  style={{
                    background: m.role === "user" ? "#f1f5f9" : "#eff6ff",
                    borderRadius: 10,
                    padding: 10,
                    fontSize: 12.5,
                    lineHeight: 1.45,
                    whiteSpace: "pre-line",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4, fontWeight: 600 }}>
                    <span>{m.role === "assistant" ? "🤖" : "👤"}</span>
                    <span>{m.role === "user" ? t.you : t.assistantName}</span>
                  </div>
                  {m.text}
                  {m.sources && m.sources.length > 0 && (
                    <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 8 }}>
                      {m.sources.map((s) => (
                        <span
                          key={s}
                          style={{
                            fontSize: 10.5,
                            background: "#fff",
                            border: "1px solid #cbd5e1",
                            padding: "2px 6px",
                            borderRadius: 6,
                          }}
                        >
                          📄 {s}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              {chatLoading && (
                <div style={{ fontSize: 12, color: "#64748b", fontStyle: "italic" }}>
                  {t.assistantAnalyzing}
                </div>
              )}
            </div>
          </div>

          <div style={{ display: "flex", gap: 6, marginTop: 12 }}>
            <input
              type="text"
              placeholder={
                selectedArch
                  ? t.chatPlaceholderSelected(selectedArch.rank, selectedArch.badge)
                  : t.chatPlaceholderDefault
              }
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSendChat()}
              style={{ flex: 1, padding: "8px 10px", borderRadius: 8, border: "1px solid #cbd5e1", fontSize: 12.5 }}
            />
            <button
              type="button"
              onClick={() => handleSendChat()}
              disabled={chatLoading}
              style={{
                background: "#059669",
                color: "#fff",
                border: "none",
                borderRadius: 8,
                padding: "0 12px",
                cursor: "pointer",
                fontWeight: 600,
              }}
            >
              ➤
            </button>
          </div>
        </aside>
      </div>
    </div>
  );
}

export default App;