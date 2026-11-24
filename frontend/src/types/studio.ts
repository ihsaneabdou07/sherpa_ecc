export interface RadarScores {
  cost_score: number;
  co2_score: number;
  water_score: number;
  trl_score: number;
  efficiency_score: number;
}

export interface ArchitectureItem {
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
}

export interface StudioResponse {
  region: string;
  target_product: string;
  annual_production_tonnes: number;
  architectures: ArchitectureItem[];
  pareto_others: { cost: number; co2: number }[];
}

export interface ChatMessage {
  role: "user" | "assistant";
  text: string;
  sources?: string[];
}