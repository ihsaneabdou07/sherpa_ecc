import type { ExplainResponse, ScenarioInput, ScenarioOutput } from "../types/scenario";

const API_BASE_URL = "http://127.0.0.1:8000";

export async function simulateScenario(payload: ScenarioInput): Promise<ScenarioOutput> {
  const response = await fetch(`${API_BASE_URL}/scenarios/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`Erreur simulation (${response.status})`);
  }
  return response.json();
}

export async function explainScenario(output: ScenarioOutput): Promise<ExplainResponse> {
  const response = await fetch(`${API_BASE_URL}/scenarios/explain`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(output),
  });
  if (!response.ok) {
    throw new Error(`Erreur explication (${response.status})`);
  }
  return response.json();
}