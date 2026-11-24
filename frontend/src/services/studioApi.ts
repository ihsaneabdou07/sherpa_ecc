import type { ArchitectureItem, ChatMessage, StudioResponse } from "../types/studio";

const API_BASE_URL = "http://127.0.0.1:8000";

export interface RecommendPayload {
  region: string;
  target_product: string;
  annual_production_tonnes: number;
}

export interface ChatPayload {
  question: string;
  region: string;
  target_product: string;
  architectures: ArchitectureItem[];
}

export interface ChatApiResponse {
  reply: string;
  sources?: string[];
}

async function parseErrorMessage(response: Response, fallbackLabel: string): Promise<string> {
  try {
    const data = await response.json();
    if (typeof data?.detail === "string") {
      return `${fallbackLabel} (${response.status}) : ${data.detail}`;
    }
  } catch {
    // Corps non-JSON : on garde le message par défaut
  }
  return `${fallbackLabel} (${response.status} ${response.statusText})`;
}

export async function fetchRecommendedArchitectures(payload: RecommendPayload): Promise<StudioResponse> {
  const response = await fetch(`${API_BASE_URL}/studio/recommend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response, "Erreur lors du calcul des architectures"));
  }

  return response.json() as Promise<StudioResponse>;
}

export async function sendStudioChatMessage(payload: ChatPayload): Promise<ChatApiResponse> {
  const response = await fetch(`${API_BASE_URL}/studio/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response, "Erreur de l'assistant IA"));
  }

  return response.json() as Promise<ChatApiResponse>;
}

export type { ChatMessage };