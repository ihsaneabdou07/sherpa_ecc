import { useEffect, useState } from "react";
import { MoroccoMap } from "./components/MoroccoMap";
import { ChartsPanel } from "./components/ChartsPanel";

const API_BASE = "http://127.0.0.1:8000";

interface ChatMessage {
  role: "user" | "assistant";
  text: string;
  sources?: string[];
}

export function App() {
  const [region, setRegion] = useState("Dakhla-Oued Eddahab");
  const [targetProduct, setTargetProduct] = useState("e-Methanol");
  const [production, setProduction] = useState(100000);
  const [studioData, setStudioData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState("");

  async function fetchRecommendations(reg = region, prod = targetProduct, qty = production) {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/studio/recommend`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          region: reg,
          target_product: prod,
          annual_production_tonnes: qty,
        }),
      });
      const data = await res.json();
      setStudioData(data);

      const defaultQ = `Why is architecture 1 recommended for ${reg}?`;
      const chatRes = await fetch(`${API_BASE}/studio/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: defaultQ,
          region: reg,
          target_product: prod,
          architectures: data.architectures,
        }),
      });
      const chatJson = await chatRes.json();
      setMessages([
        { role: "user", text: defaultQ },
        { role: "assistant", text: chatJson.reply, sources: chatJson.sources },
      ]);
    } catch (err) {
      console.error("Erreur API:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchRecommendations();
  }, []);

  async function handleSendChat() {
    if (!chatInput.trim() || !studioData) return;
    const q = chatInput.trim();
    setChatInput("");
    setMessages((prev) => [...prev, { role: "user", text: q }]);

    try {
      const res = await fetch(`${API_BASE}/studio/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: q,
          region,
          target_product: targetProduct,
          architectures: studioData.architectures,
        }),
      });
      const data = await res.json();
      setMessages((prev) => [...prev, { role: "assistant", text: data.reply, sources: data.sources }]);
    } catch (err) {
      console.error("Erreur Chat:", err);
    }
  }

  return (
    <div style={{ minHeight: "100vh", background: "#f1f5f9", fontFamily: "Inter, system-ui, sans-serif", color: "#0f172a" }}>
      {/* Barre supérieure */}
      <header
        style={{
          background: "#fff",
          borderBottom: "1px solid #e2e8f0",
          padding: "10px 24px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
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
        <div style={{ display: "flex", alignItems: "center", gap: 12, fontSize: 12 }}>
          <span style={{ background: "#f1f5f9", padding: "4px 10px", borderRadius: 999 }}>FR | EN</span>
          <span style={{ background: "#0f172a", color: "#fff", padding: "5px 10px", borderRadius: 999 }}>SHERPA ECC</span>
        </div>
      </header>

      {/* Grille 3 colonnes */}
      <div style={{ display: "grid", gridTemplateColumns: "290px 1fr 340px", gap: 16, padding: 16 }}>
        {/* Colonne 1 : Your project */}
        <aside style={{ background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", padding: 16 }}>
          <h3 style={{ margin: "0 0 14px", fontSize: 15 }}>🎯 Your project</h3>

          <div style={{ fontSize: 12, fontWeight: 600, color: "#475569", marginBottom: 8 }}>🗺️ Target region</div>
          <MoroccoMap selectedRegion={region} onSelectRegion={setRegion} />

          <div style={{ fontSize: 12, fontWeight: 600, color: "#475569", margin: "16px 0 6px" }}>🧪 Target product</div>
          <select
            value={targetProduct}
            onChange={(e) => setTargetProduct(e.target.value)}
            style={{ width: "100%", padding: "8px 10px", borderRadius: 8, border: "1px solid #cbd5e1", fontSize: 13 }}
          >
            <option value="e-Methanol">e-Methanol</option>
            <option value="Green hydrogen">Green hydrogen</option>
            <option value="e-Diesel">e-Diesel</option>
            <option value="e-Methane">e-Methane</option>
          </select>

          <div style={{ fontSize: 12, fontWeight: 600, color: "#475569", margin: "16px 0 6px" }}>📊 Annual production</div>
          <div style={{ display: "flex", border: "1px solid #cbd5e1", borderRadius: 8, overflow: "hidden" }}>
            <input
              type="number"
              value={production}
              onChange={(e) => setProduction(Number(e.target.value))}
              style={{ width: "100%", border: "none", padding: "8px 10px", fontSize: 13 }}
            />
            <span style={{ background: "#f8fafc", padding: "8px 10px", fontSize: 11, color: "#64748b", whiteSpace: "nowrap" }}>
              tonnes / year
            </span>
          </div>

          <button
            type="button"
            onClick={() => fetchRecommendations()}
            disabled={loading}
            style={{
              marginTop: 18,
              width: "100%",
              background: "#059669",
              color: "#fff",
              border: "none",
              borderRadius: 10,
              padding: "10px 14px",
              fontWeight: 600,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 8,
            }}
          >
            <span>🔍</span>
            {loading ? "Calcul..." : "Find best architectures"}
          </button>
        </aside>

        {/* Colonne 2 : Recommended architectures + Graphiques */}
        <main>
          <div style={{ background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", padding: 16 }}>
            <h3 style={{ margin: "0 0 12px", fontSize: 15 }}>⚡ Recommended architectures</h3>

            {!studioData && (
              <p style={{ fontSize: 13, color: "#64748b" }}>
                Chargement des architectures... (Vérifie que uvicorn tourne bien sur le port 8000)
              </p>
            )}

            {studioData && (
              <>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
                  {studioData.architectures.map((arch: any) => (
                    <div
                      key={arch.id}
                      style={{
                        border: `2px solid ${arch.color}`,
                        borderRadius: 12,
                        padding: 12,
                        background: "#ffffff",
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
                        <span
                          style={{
                            background: arch.color,
                            color: "#fff",
                            width: 22,
                            height: 22,
                            borderRadius: "50%",
                            display: "inline-flex",
                            alignItems: "center",
                            justifyContent: "center",
                            fontSize: 12,
                            fontWeight: 700,
                          }}
                        >
                          {arch.rank}
                        </span>
                        <span style={{ fontWeight: 600, fontSize: 13, color: arch.color }}>{arch.badge}</span>
                      </div>

                      {/* Schéma chaîne technologique */}
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          background: "#f8fafc",
                          padding: "8px 6px",
                          borderRadius: 8,
                          marginBottom: 12,
                          fontSize: 12,
                          color: "#475569",
                        }}
                      >
                        <span title="Solar + Wind">☀️🌬️</span>
                        <span>→</span>
                        <span title="Desalination">💧</span>
                        <span>→</span>
                        <span title="Electrolyzer + Synthesis">🏭</span>
                      </div>

                      <div style={{ display: "flex", flexDirection: "column", gap: 8, fontSize: 13 }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                          <span>💰</span>
                          <div>
                            <strong>
                              {arch.cost} {arch.unit}
                            </strong>
                            <div style={{ fontSize: 11, color: "#64748b" }}>Production cost</div>
                          </div>
                        </div>

                        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                          <span>🌱</span>
                          <div>
                            <strong>{arch.co2} kg CO2/unit</strong>
                            <div style={{ fontSize: 11, color: "#64748b" }}>CO2 emissions</div>
                          </div>
                        </div>

                        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                          <span>💧</span>
                          <div>
                            <strong>{arch.water} L/unit</strong>
                            <div style={{ fontSize: 11, color: "#64748b" }}>Water use</div>
                          </div>
                        </div>

                        <div style={{ fontSize: 12, color: "#334155", marginTop: 2 }}>
                          ⚙️ <strong>{arch.trl}</strong> — <span style={{ color: "#64748b" }}>Maturity</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                <ChartsPanel architectures={studioData.architectures} paretoOthers={studioData.pareto_others} />
              </>
            )}
          </div>
        </main>

        {/* Colonne 3 : AI assistant */}
        <aside
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
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
              <span>✨</span>
              <h3 style={{ margin: 0, fontSize: 15 }}>AI assistant</h3>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 10, maxHeight: 460, overflowY: "auto" }}>
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
                    <span>{m.role === "user" ? "Vous" : "Assistant SHERPA"}</span>
                  </div>
                  {m.text}
                  {m.sources && (
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
            </div>
          </div>

          <div style={{ display: "flex", gap: 6, marginTop: 12 }}>
            <input
              type="text"
              placeholder="Ask a question about the results..."
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSendChat()}
              style={{ flex: 1, padding: "8px 10px", borderRadius: 8, border: "1px solid #cbd5e1", fontSize: 12.5 }}
            />
            <button
              type="button"
              onClick={handleSendChat}
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