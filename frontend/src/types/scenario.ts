export type SeasonType = "annual" | "winter" | "summer";

export interface ScenarioInput {
  scenario_name: string;
  ely_res_ratio: number;
  electrolyzer_capacity_mw: number;
  local_lcoe_eur_per_kwh?: number | null;
  flh_res_hours?: number | null;
  storage_duration_hours: number;
  ev_smart_charging_share: number;
  water_efficiency_factor: number;
  desalination_share: number;
  season: SeasonType;
}

export interface TradeoffItem {
  axis: string;
  status: string;
  summary: string;
}

export interface ScenarioOutput {
  scenario_name: string;
  metrics: Record<string, number>;
  decision_axes: Record<string, number>;
  tradeoffs: TradeoffItem[];
  assumptions_used: Record<string, unknown>;
}

export interface ExplainResponse {
  executive_summary: string;
  decision_axes: Record<string, number>;
  grounded_assumptions: Record<string, unknown>;
}