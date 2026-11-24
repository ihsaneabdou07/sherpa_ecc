import json
from pathlib import Path
from typing import Dict, Any, List
from .hydrogen import compute_hydrogen_metrics
from .batteries import compute_storage_and_ev_metrics
from .nexus import compute_water_carbon_metrics

DEFAULTS_PATH = Path(__file__).resolve().parent.parent / "data" / "morocco_defaults.json"

def load_defaults() -> Dict[str, Any]:
    with open(DEFAULTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def run_scenario_simulation(input_data: Dict[str, Any]) -> Dict[str, Any]:
    defaults = load_defaults()

    h2_metrics = compute_hydrogen_metrics(input_data, defaults)
    bat_metrics = compute_storage_and_ev_metrics(input_data, defaults)
    nexus_metrics = compute_water_carbon_metrics(input_data, h2_metrics, defaults)

    metrics = {**h2_metrics, **bat_metrics, **nexus_metrics}

    tech_score = round(min(100.0, (h2_metrics["flh_h2_hours"] / 6500.0) * 50.0 + bat_metrics["system_flexibility_index"] * 0.5), 1)
    econ_score = round(max(0.0, min(100.0, 100.0 - (h2_metrics["lcoh_eur_per_kg"] - 1.5) * 18.0)), 1)
    env_score = round(max(0.0, min(100.0, 100.0 - nexus_metrics["h2_carbon_intensity_kg_co2e_per_kg"] * 22.0)), 1)
    sovereignty_score = round(
        min(100.0, 40.0 + (1.0 - input_data["desalination_share"]) * 25.0 + input_data["ev_smart_charging_share"] * 35.0), 1
    )

    tradeoffs: List[Dict[str, str]] = [
        {
            "axis": "Économique vs Utilisation Électrolyseur",
            "status": "favorable" if h2_metrics["lcoh_eur_per_kg"] < 3.2 else "attention",
            "summary": (
                f"Avec un Ely-RES-Ratio de {input_data['ely_res_ratio']}, le LCOH atteint "
                f"{h2_metrics['lcoh_eur_per_kg']} €/kg pour {h2_metrics['flh_h2_hours']} h de fonctionnement."
            ),
        },
        {
            "axis": "Nexus Eau–Carbone",
            "status": "favorable" if nexus_metrics["water_carbon_footprint_res_kg_co2e_per_m3"] < 0.15 else "attention",
            "summary": (
                f"La part de dessalement ({int(input_data['desalination_share']*100)} %) conduit à une intensité "
                f"hydrique de {nexus_metrics['water_energy_intensity_kwh_per_m3']} kWh/m³."
            ),
        },
    ]

    assumptions_used = {
        "local_lcoe_eur_per_kwh": input_data.get("local_lcoe_eur_per_kwh") or defaults["green_hydrogen"]["local_lcoe_eur_per_kwh"],
        "flh_res_hours": input_data.get("flh_res_hours") or defaults["green_hydrogen"]["flh_res_hours"],
        "ely_res_ratio": input_data["ely_res_ratio"],
        "storage_duration_hours": input_data["storage_duration_hours"],
        "ev_smart_charging_share": input_data["ev_smart_charging_share"],
        "water_efficiency_factor": input_data["water_efficiency_factor"],
        "desalination_share": input_data["desalination_share"],
        "season": input_data["season"],
    }

    return {
        "scenario_name": input_data["scenario_name"],
        "metrics": metrics,
        "decision_axes": {
            "technique": tech_score,
            "economique": econ_score,
            "environnemental": env_score,
            "souverainete_resilience": sovereignty_score,
        },
        "tradeoffs": tradeoffs,
        "assumptions_used": assumptions_used,
    }