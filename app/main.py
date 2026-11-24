from typing import List, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .schemas import ScenarioInput, ScenarioOutput
from .engine.simulator import load_defaults, run_scenario_simulation

app = FastAPI(title="H2-Maroc Decision Studio API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REGION_PROFILES = {
    "Dakhla-Oued Eddahab": {"lcoe": 0.024, "flh_res": 4300, "desal_share": 0.90},
    "Laâyoune": {"lcoe": 0.026, "flh_res": 4050, "desal_share": 0.85},
    "Laâyoune-Sakia El Hamra": {"lcoe": 0.026, "flh_res": 4050, "desal_share": 0.85},
    "Souss-Massa": {"lcoe": 0.031, "flh_res": 3400, "desal_share": 0.75},
    "Casablanca-Settat": {"lcoe": 0.035, "flh_res": 2950, "desal_share": 0.60},
    "Oriental": {"lcoe": 0.030, "flh_res": 3550, "desal_share": 0.65},
}

PRODUCT_FACTORS = {
    "Green hydrogen": {"unit": "€/kg", "cost_mult": 1.0, "co2_mult": 1.0, "water_mult": 15.0, "trl": "TRL 8-9"},
    "e-Methanol": {"unit": "MAD/L", "cost_mult": 0.34, "co2_mult": 0.42, "water_mult": 1.8, "trl": "TRL 6-7"},
    "e-Diesel": {"unit": "MAD/L", "cost_mult": 0.39, "co2_mult": 0.48, "water_mult": 2.1, "trl": "TRL 6-7"},
    "e-Methane": {"unit": "MAD/L", "cost_mult": 0.31, "co2_mult": 0.45, "water_mult": 1.9, "trl": "TRL 7-8"},
}

class StudioRequest(BaseModel):
    region: str = "Dakhla-Oued Eddahab"
    target_product: str = "e-Methanol"
    annual_production_tonnes: float = 100000

class ChatRequest(BaseModel):
    question: str
    region: str
    target_product: str
    architectures: List[dict]
    annual_production_tonnes: Optional[float] = None
    lang: str = "fr"

@app.get("/")
def root():
    return {"message": "H2-Maroc Decision Studio API is running", "docs": "/docs"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/defaults")
def get_defaults():
    return load_defaults()

@app.post("/scenarios/simulate", response_model=ScenarioOutput)
def simulate_scenario(payload: ScenarioInput):
    return run_scenario_simulation(payload.model_dump())

@app.post("/studio/recommend")
def recommend_architectures(req: StudioRequest):
    reg = REGION_PROFILES.get(req.region, REGION_PROFILES["Dakhla-Oued Eddahab"])
    prod = PRODUCT_FACTORS.get(req.target_product, PRODUCT_FACTORS["e-Methanol"])
    cap_mw = max(20.0, min(1500.0, req.annual_production_tonnes / 1000.0))

    configs = [
        ("arch-1", 1, "Best overall", "#10b981", 0.75, 4.0, 0.45, 1.15, 1.00, 1.00),
        ("arch-2", 2, "Lowest cost", "#2563eb", 0.90, 2.0, 0.30, 0.90, 0.86, 1.25),
        ("arch-3", 3, "Lowest CO2", "#7c3aed", 0.65, 6.0, 0.70, 1.25, 1.16, 1.45),
    ]

    architectures = []
    for arch_id, rank, label, color, ratio, storage_h, ev_share, water_eff, cost_factor, water_factor in configs:
        sim = run_scenario_simulation({
            "scenario_name": label,
            "ely_res_ratio": ratio,
            "electrolyzer_capacity_mw": cap_mw,
            "local_lcoe_eur_per_kwh": reg["lcoe"],
            "flh_res_hours": reg["flh_res"],
            "storage_duration_hours": storage_h,
            "ev_smart_charging_share": ev_share,
            "water_efficiency_factor": water_eff,
            "desalination_share": reg["desal_share"],
            "season": "annual",
        })
        m = sim["metrics"]
        cost_val = round(m["lcoh_eur_per_kg"] * prod["cost_mult"] * cost_factor, 2)
        co2_mult_arch = 1.12 if rank == 2 else (0.78 if rank == 3 else 1.0)
        co2_val = round(m["h2_carbon_intensity_kg_co2e_per_kg"] * prod["co2_mult"] * co2_mult_arch, 2)
        water_val = round(prod["water_mult"] * water_factor, 1)
        architectures.append({
            "id": arch_id,
            "rank": rank,
            "badge": label,
            "color": color,
            "cost": cost_val,
            "unit": prod["unit"],
            "co2": co2_val,
            "water": water_val,
            "trl": prod["trl"],
            "radar": {
                "cost_score": sim["decision_axes"]["economique"],
                "co2_score": sim["decision_axes"]["environnemental"],
                "water_score": round(min(100.0, water_eff * 72), 1),
                "trl_score": 82 if rank == 1 else (86 if rank == 2 else 74),
                "efficiency_score": round(m["effective_electrolyzer_efficiency"] * 115, 1),
            },
            "assumptions": sim["assumptions_used"],
        })

    pareto_others = [
        {"cost": round(architectures[1]["cost"] * (0.98 + i * 0.045), 2), "co2": round(max(0.12, 0.92 - i * 0.052), 2)}
        for i in range(16)
    ]

    return {
        "region": req.region,
        "target_product": req.target_product,
        "annual_production_tonnes": req.annual_production_tonnes,
        "architectures": architectures,
        "pareto_others": pareto_others,
    }

@app.post("/studio/chat")
def studio_chat(req: ChatRequest):
    archs = req.architectures
    a1 = archs[0] if len(archs) > 0 else {}
    a2 = archs[1] if len(archs) > 1 else a1
    a3 = archs[2] if len(archs) > 2 else a1

    q = req.question.lower()
    is_en = req.lang == "en"

    water_stressed_regions = {"Dakhla-Oued Eddahab", "Laâyoune", "Laâyoune-Sakia El Hamra", "Souss-Massa"}
    is_water_stressed = req.region in water_stressed_regions

    if any(k in q for k in ["eau", "water", "dessal", "hydrique", "litre", "l/"]):
        if is_en:
            region_note = (
                f"{req.region} faces high water stress: desalination and water efficiency are critical."
                if is_water_stressed
                else f"For {req.region}, managing water demand remains a key lever for local integration."
            )
            reply = (
                f"Water & Desalination Analysis — {req.region} ({req.target_product}):\n"
                f"• {region_note}\n"
                f"• Architecture 1 ({a1.get('badge', 'Best overall')}): {a1.get('water')} L/unit, vs. {a2.get('water')} L/unit for {a2.get('badge')} and {a3.get('water')} L/unit for {a3.get('badge')}.\n"
                f"• Keeping the water-to-hydrogen ratio low reduces desalination power demand and secures operations."
            )
        else:
            region_note = (
                f"{req.region} présente une forte sensibilité hydrique : le dessalement et l'efficacité eau sont déterminants."
                if is_water_stressed
                else f"Pour {req.region}, la maîtrise de la demande en eau reste un levier clé d'intégration locale."
            )
            reply = (
                f"Analyse eau & dessalement — {req.region} ({req.target_product}) :\n"
                f"• {region_note}\n"
                f"• Architecture 1 ({a1.get('badge', 'Best overall')}) : {a1.get('water')} L/unité, contre {a2.get('water')} L/unité pour {a2.get('badge')} et {a3.get('water')} L/unité pour {a3.get('badge')}.\n"
                f"• Un ratio eau/hydrogène maîtrisé réduit la charge électrique du dessalement et sécurise l'exploitation."
            )
        sources = ["Carbonfootprint.pdf (Nexus Eau-Énergie)", "1-mainext.pdf (Couplage EnR-H2)"]

    elif any(k in q for k in ["cout", "coût", "cost", "prix", "mad", "moins cher", "econom", "écono"]):
        if is_en:
            reply = (
                f"Economic Analysis — {req.region} ({req.target_product}):\n"
                f"• {a2.get('badge', 'Lowest cost')} achieves the lowest cost at {a2.get('cost')} {a2.get('unit')}, driven by a higher electrolyzer-to-RES ratio and lighter storage.\n"
                f"• {a1.get('badge', 'Best overall')} sits at {a1.get('cost')} {a1.get('unit')}, keeping the premium modest while improving environmental balance and resilience.\n"
                f"• {a3.get('badge', 'Lowest CO2')} reaches {a3.get('cost')} {a3.get('unit')}, reflecting the added storage needed for maximum decarbonization."
            )
        else:
            reply = (
                f"Analyse économique — {req.region} ({req.target_product}) :\n"
                f"• {a2.get('badge', 'Lowest cost')} affiche le coût le plus bas à {a2.get('cost')} {a2.get('unit')}, grâce à un ratio électrolyseur/EnR plus élevé et un stockage plus léger.\n"
                f"• {a1.get('badge', 'Best overall')} se situe à {a1.get('cost')} {a1.get('unit')}, soit un écart contenu tout en améliorant l'équilibre environnemental et la résilience.\n"
                f"• {a3.get('badge', 'Lowest CO2')} atteint {a3.get('cost')} {a3.get('unit')}, reflétant le surcoût lié à la réduction maximale des émissions."
            )
        sources = ["1-mainext.pdf (Couplage EnR-H2)", "morocco_defaults.json (Profils régionaux)"]

    elif any(k in q for k in ["co2", "carbone", "emission", "émission", "climat", "enviro"]):
        if is_en:
            reply = (
                f"Carbon & Emissions Analysis — {req.region} ({req.target_product}):\n"
                f"• {a3.get('badge', 'Lowest CO2')} delivers the lowest carbon intensity ({a3.get('co2')} kg CO2/unit) through flexible coupling and larger storage.\n"
                f"• {a1.get('badge', 'Best overall')} achieves {a1.get('co2')} kg CO2/unit, compared to {a2.get('co2')} kg CO2/unit for {a2.get('badge')}.\n"
                f"• The final selection depends on the trade-off between carbon intensity, unit cost, and technological maturity ({a1.get('trl')})."
            )
        else:
            reply = (
                f"Analyse carbone & émissions — {req.region} ({req.target_product}) :\n"
                f"• {a3.get('badge', 'Lowest CO2')} vise l'intensité carbone la plus faible ({a3.get('co2')} kg CO2/unité) via un couplage plus souple et un stockage accru.\n"
                f"• {a1.get('badge', 'Best overall')} atteint {a1.get('co2')} kg CO2/unité, face à {a2.get('co2')} kg CO2/unité pour {a2.get('badge')}.\n"
                f"• Le choix final dépend du compromis accepté entre intensité carbone, coût de production et maturité technologique ({a1.get('trl')})."
            )
        sources = ["Carbonfootprint.pdf (Nexus Eau-Énergie)", "1-mainext.pdf (Couplage EnR-H2)"]

    else:
        prod_label = (
            f" ({int(req.annual_production_tonnes):,} t/yr)" if is_en else f" ({int(req.annual_production_tonnes):,} t/an)"
        ) if req.annual_production_tonnes is not None else ""

        if is_en:
            reply = (
                f"Summary for {req.region} — {req.target_product}{prod_label}:\n"
                f"• Architecture 1 ({a1.get('badge', 'Best overall')}): {a1.get('cost')} {a1.get('unit')}, {a1.get('co2')} kg CO2/unit, {a1.get('water')} L/unit ({a1.get('trl')}).\n"
                f"• Architecture 2 ({a2.get('badge', 'Lowest cost')}): {a2.get('cost')} {a2.get('unit')} — prioritizes minimum unit production cost.\n"
                f"• Architecture 3 ({a3.get('badge', 'Lowest CO2')}): {a3.get('co2')} kg CO2/unit — prioritizes minimum carbon emissions."
            )
        else:
            reply = (
                f"Synthèse pour {req.region} — {req.target_product}{prod_label} :\n"
                f"• Architecture 1 ({a1.get('badge', 'Best overall')}) : {a1.get('cost')} {a1.get('unit')}, {a1.get('co2')} kg CO2/unité, {a1.get('water')} L/unité ({a1.get('trl')}).\n"
                f"• Architecture 2 ({a2.get('badge', 'Lowest cost')}) : {a2.get('cost')} {a2.get('unit')} — priorité à la minimisation du coût unitaire.\n"
                f"• Architecture 3 ({a3.get('badge', 'Lowest CO2')}) : {a3.get('co2')} kg CO2/unité — priorité à la réduction des émissions."
            )
        sources = ["1-mainext.pdf (Couplage EnR-H2)", "Carbonfootprint.pdf (Nexus Eau-Énergie)"]
        
        
    # Courbe de sensibilité à la disponibilité renouvelable (-20% à +20% FLH)
    flh_multipliers = [0.80, 0.90, 1.00, 1.10, 1.20]
    sensitivity_curve = []
    for mult in flh_multipliers:
        flh_test = round(reg["flh_res"] * mult)
        point = {"flh": flh_test, "label": f"{int((mult - 1) * 100):+d}%"}
        for arch_id, rank, label, color, ratio, storage_h, ev_share, water_eff, cost_factor, water_factor in configs:
            sim_s = run_scenario_simulation({
                "scenario_name": label,
                "ely_res_ratio": ratio,
                "electrolyzer_capacity_mw": cap_mw,
                "local_lcoe_eur_per_kwh": reg["lcoe"],
                "flh_res_hours": flh_test,
                "storage_duration_hours": storage_h,
                "ev_smart_charging_share": ev_share,
                "water_efficiency_factor": water_eff,
                "desalination_share": reg["desal_share"],
                "season": "annual",
            })
            point[arch_id] = round(sim_s["metrics"]["lcoh_eur_per_kg"] * prod["cost_mult"] * cost_factor, 2)
        sensitivity_curve.append(point)

    return {
        "region": req.region,
        "target_product": req.target_product,
        "annual_production_tonnes": req.annual_production_tonnes,
        "architectures": architectures,
        "pareto_others": pareto_others,
        "sensitivity_curve": sensitivity_curve,
    }    

    return {"reply": reply, "sources": sources}