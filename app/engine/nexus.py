from typing import Dict, Any

def compute_water_carbon_metrics(
    params: Dict[str, Any], h2_metrics: Dict[str, float], defaults: Dict[str, Any]
) -> Dict[str, float]:
    nexus_def = defaults["water_energy_carbon_nexus"]
    water_def = nexus_def["water_supply"]

    season = params.get("season", "annual")
    seasonal_mult = nexus_def["seasonal_grid_variation_factor"].get(season, 1.0)

    grid_ef = nexus_def["grid_emission_factor_kg_co2e_per_kwh"] * seasonal_mult
    res_ef = nexus_def["renewable_emission_factor_kg_co2e_per_kwh"]

    desal_share = params["desalination_share"]
    water_eff = params["water_efficiency_factor"]

    base_water_energy = (
        desal_share * water_def["desalination_energy_kwh_per_m3"]
        + (1.0 - desal_share) * water_def["wastewater_treatment_energy_kwh_per_m3"]
        + water_def["pumping_energy_kwh_per_m3"]
    )
    specific_water_energy_kwh_m3 = base_water_energy / max(water_eff, 0.1)

    water_carbon_grid_kg_m3 = specific_water_energy_kwh_m3 * grid_ef
    water_carbon_res_kg_m3 = specific_water_energy_kwh_m3 * res_ef

    h2_water_m3 = h2_metrics["water_m3_per_kg_h2"]
    h2_carbon_intensity = (h2_water_m3 * water_carbon_res_kg_m3) + (
        (33.33 / max(h2_metrics["effective_electrolyzer_efficiency"], 0.01)) * res_ef
    )

    return {
        "water_energy_intensity_kwh_per_m3": round(specific_water_energy_kwh_m3, 3),
        "water_carbon_footprint_grid_kg_co2e_per_m3": round(water_carbon_grid_kg_m3, 3),
        "water_carbon_footprint_res_kg_co2e_per_m3": round(water_carbon_res_kg_m3, 3),
        "h2_carbon_intensity_kg_co2e_per_kg": round(h2_carbon_intensity, 3),
    }