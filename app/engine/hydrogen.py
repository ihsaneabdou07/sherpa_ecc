from typing import Dict, Any

def _crf(wacc: float, years: int) -> float:
    if wacc <= 0:
        return 1.0 / max(years, 1)
    return (wacc * (1 + wacc) ** years) / ((1 + wacc) ** years - 1)

def compute_hydrogen_metrics(params: Dict[str, Any], defaults: Dict[str, Any]) -> Dict[str, float]:
    h2_def = defaults["green_hydrogen"]
    ely_def = h2_def["electrolyzer"]
    water_def = defaults["water_energy_carbon_nexus"]["water_supply"]

    lcoe = params.get("local_lcoe_eur_per_kwh") or h2_def["local_lcoe_eur_per_kwh"]
    flh_res = params.get("flh_res_hours") or h2_def["flh_res_hours"]
    ely_ratio = params["ely_res_ratio"]
    cap_mw = params["electrolyzer_capacity_mw"]

    flh_h2 = min(8200.0, flh_res / max(ely_ratio, 0.25) * 0.92)
    load_factor_pct = (flh_h2 / 8760.0) * 100.0

    if load_factor_pct < ely_def["min_load_threshold_pct"]:
        effective_efficiency = 0.0
    else:
        part_load_bonus = ely_def["part_load_efficiency_gain"] * (1.0 - min(ely_ratio, 1.0))
        effective_efficiency = min(0.80, ely_def["nominal_efficiency_lhv"] + part_load_bonus)

    scale_factor = (cap_mw / ely_def["ref_capacity_mw"]) ** (ely_def["scale_exponent"] - 1.0)
    capex_per_kw = ely_def["capex_eur_per_kw_ref"] * scale_factor

    spec_energy = 33.33 / max(effective_efficiency, 0.01)
    annual_h2_kg_per_kw = flh_h2 / spec_energy if effective_efficiency > 0 else 0.0
    annualized_capex = capex_per_kw * (_crf(ely_def["wacc"], ely_def["lifetime_years"]) + ely_def["opex_pct_capex"])

    lcoh_capex = annualized_capex / max(annual_h2_kg_per_kw, 1e-6)
    lcoh_elec = spec_energy * lcoe
    water_m3_per_kg = (ely_def["water_consumption_l_per_kg_h2"] / 1000.0) / max(params["water_efficiency_factor"], 0.1)
    lcoh_water = water_m3_per_kg * water_def["water_cost_eur_per_m3"]
    lcoh_total = lcoh_capex + lcoh_elec + lcoh_water

    return {
        "flh_h2_hours": round(flh_h2, 1),
        "effective_electrolyzer_efficiency": round(effective_efficiency, 4),
        "capex_eur_per_kw": round(capex_per_kw, 2),
        "lcoh_eur_per_kg": round(lcoh_total, 3),
        "lcoh_fixed_share_pct": round((lcoh_capex / max(lcoh_total, 1e-6)) * 100.0, 1),
        "lcoh_variable_share_pct": round(((lcoh_elec + lcoh_water) / max(lcoh_total, 1e-6)) * 100.0, 1),
        "water_m3_per_kg_h2": round(water_m3_per_kg, 4),
    }