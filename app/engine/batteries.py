from typing import Dict, Any

def _crf(wacc: float, years: int) -> float:
    if wacc <= 0:
        return 1.0 / max(years, 1)
    return (wacc * (1 + wacc) ** years) / ((1 + wacc) ** years - 1)

def compute_storage_and_ev_metrics(params: Dict[str, Any], defaults: Dict[str, Any]) -> Dict[str, float]:
    bat_def = defaults["batteries_and_ev"]
    h2_def = defaults["green_hydrogen"]

    lcoe = params.get("local_lcoe_eur_per_kwh") or h2_def["local_lcoe_eur_per_kwh"]
    duration_h = params["storage_duration_hours"]
    ev_smart = params["ev_smart_charging_share"]

    annualized_capex_per_kwh = bat_def["capex_eur_per_kwh"] * _crf(bat_def["wacc"], bat_def["lifetime_years"])
    annual_throughput_kwh = bat_def["cycles_per_year"] * bat_def["round_trip_efficiency"]
    lcos_eur_per_kwh = annualized_capex_per_kwh / max(annual_throughput_kwh, 1.0)

    pv_plus_storage_lcoe = lcoe + (lcos_eur_per_kwh * (duration_h / 8.0) * 0.45)
    valcoe_eur_per_mwh = (pv_plus_storage_lcoe * 1000.0) - (
        bat_def["pv_storage_valcoe_bonus_eur_per_mwh"] * (duration_h / 4.0)
    )

    battery_flex_score = min(100.0, (duration_h / 8.0) * 65.0)
    ev_flex_score = ev_smart * 35.0
    total_flexibility_index = round(min(100.0, battery_flex_score + ev_flex_score), 1)

    return {
        "lcos_eur_per_kwh": round(lcos_eur_per_kwh, 4),
        "pv_storage_lcoe_eur_per_kwh": round(pv_plus_storage_lcoe, 4),
        "valcoe_eur_per_mwh": round(max(0.0, valcoe_eur_per_mwh), 2),
        "system_flexibility_index": total_flexibility_index,
    }