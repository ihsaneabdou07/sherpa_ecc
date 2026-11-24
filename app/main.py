import unicodedata
from typing import List, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .schemas import ScenarioInput, ScenarioOutput
from .engine.simulator import load_defaults, run_scenario_simulation
from src.ai_assistant import generer_explication
from src.comparaison import comparer_scenarios
from src.engine import optimiser_architecture
from fastapi.responses import StreamingResponse
from .engine.excel_exporter import build_native_excel_report

app = FastAPI(title="H2-Maroc Decision Studio API", version="1.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Profils des 12 régions administratives du Maroc
REGION_PROFILES = {
    "Tanger-Tétouan-Al Hoceïma": {"lcoe": 0.029, "flh_res": 3650, "desal_share": 0.70},
    "Oriental": {"lcoe": 0.030, "flh_res": 3550, "desal_share": 0.65},
    "Fès-Meknès": {"lcoe": 0.033, "flh_res": 3150, "desal_share": 0.25},
    "Rabat-Salé-Kénitra": {"lcoe": 0.034, "flh_res": 3050, "desal_share": 0.55},
    "Béni Mellal-Khénifra": {"lcoe": 0.032, "flh_res": 3250, "desal_share": 0.20},
    "Casablanca-Settat": {"lcoe": 0.035, "flh_res": 2950, "desal_share": 0.60},
    "Marrakech-Safi": {"lcoe": 0.030, "flh_res": 3500, "desal_share": 0.65},
    "Drâa-Tafilalet": {"lcoe": 0.027, "flh_res": 3850, "desal_share": 0.30},
    "Souss-Massa": {"lcoe": 0.031, "flh_res": 3400, "desal_share": 0.75},
    "Guelmim-Oued Noun": {"lcoe": 0.026, "flh_res": 3950, "desal_share": 0.85},
    "Laâyoune-Sakia El Hamra": {"lcoe": 0.025, "flh_res": 4100, "desal_share": 0.88},
    "Dakhla-Oued Eddahab": {"lcoe": 0.024, "flh_res": 4300, "desal_share": 0.90},
}

# 2. Catalogue des villes / pôles industriels et portuaires
CITY_PROFILES = {
    "Dakhla": {"region": "Dakhla-Oued Eddahab", "lcoe": 0.024, "flh_res": 4300, "desal_share": 0.90, "engine_key": "Dakhla"},
    "Laâyoune": {"region": "Laâyoune-Sakia El Hamra", "lcoe": 0.025, "flh_res": 4100, "desal_share": 0.88, "engine_key": "Laayoune"},
    "Boujdour": {"region": "Laâyoune-Sakia El Hamra", "lcoe": 0.0245, "flh_res": 4180, "desal_share": 0.90},
    "Tan-Tan": {"region": "Guelmim-Oued Noun", "lcoe": 0.0255, "flh_res": 4000, "desal_share": 0.88},
    "Guelmim": {"region": "Guelmim-Oued Noun", "lcoe": 0.0265, "flh_res": 3900, "desal_share": 0.80},
    "Agadir": {"region": "Souss-Massa", "lcoe": 0.031, "flh_res": 3400, "desal_share": 0.80},
    "Safi": {"region": "Marrakech-Safi", "lcoe": 0.029, "flh_res": 3620, "desal_share": 0.85},
    "Essaouira": {"region": "Marrakech-Safi", "lcoe": 0.028, "flh_res": 3750, "desal_share": 0.85},
    "Marrakech": {"region": "Marrakech-Safi", "lcoe": 0.031, "flh_res": 3420, "desal_share": 0.35},
    "Ouarzazate": {"region": "Drâa-Tafilalet", "lcoe": 0.026, "flh_res": 3920, "desal_share": 0.25},
    "Jorf Lasfar": {"region": "Casablanca-Settat", "lcoe": 0.033, "flh_res": 3100, "desal_share": 0.85},
    "Casablanca": {"region": "Casablanca-Settat", "lcoe": 0.035, "flh_res": 2950, "desal_share": 0.65},
    "Mohammedia": {"region": "Casablanca-Settat", "lcoe": 0.0345, "flh_res": 2980, "desal_share": 0.75},
    "Kénitra": {"region": "Rabat-Salé-Kénitra", "lcoe": 0.0335, "flh_res": 3080, "desal_share": 0.65},
    "Rabat": {"region": "Rabat-Salé-Kénitra", "lcoe": 0.034, "flh_res": 3050, "desal_share": 0.65},
    "Tanger": {"region": "Tanger-Tétouan-Al Hoceïma", "lcoe": 0.0285, "flh_res": 3720, "desal_share": 0.80},
    "Nador": {"region": "Oriental", "lcoe": 0.0295, "flh_res": 3600, "desal_share": 0.80},
    "Oujda": {"region": "Oriental", "lcoe": 0.0305, "flh_res": 3500, "desal_share": 0.45},
    "Fès": {"region": "Fès-Meknès", "lcoe": 0.033, "flh_res": 3150, "desal_share": 0.25},
    "Béni Mellal": {"region": "Béni Mellal-Khénifra", "lcoe": 0.032, "flh_res": 3250, "desal_share": 0.20},
}

STUDIO_TO_ENGINE_REGION = {
    "Dakhla-Oued Eddahab": "Dakhla",
    "Dakhla": "Dakhla",
    "Laâyoune": "Laayoune",
    "Laayoune": "Laayoune",
    "Laâyoune-Sakia El Hamra": "Laayoune",
}

PRODUCT_FACTORS = {
    "Green hydrogen": {"unit": "€/kg", "cost_mult": 1.0, "co2_mult": 1.0, "water_mult": 15.0, "trl": "TRL 8-9"},
    "e-Methanol": {"unit": "MAD/L", "cost_mult": 0.34, "co2_mult": 0.42, "water_mult": 1.8, "trl": "TRL 6-7"},
    "e-Diesel": {"unit": "MAD/L", "cost_mult": 0.39, "co2_mult": 0.48, "water_mult": 2.1, "trl": "TRL 6-7"},
    "e-Methane": {"unit": "MAD/L", "cost_mult": 0.31, "co2_mult": 0.45, "water_mult": 1.9, "trl": "TRL 7-8"},
}


def _norm(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text.strip().lower())
        if unicodedata.category(c) != "Mn"
    )


def _resolve_location(location: str) -> dict:
    """Résout une région ou une ville vers son profil énergétique complet."""
    target = _norm(location)
    for city_name, cfg in CITY_PROFILES.items():
        if _norm(city_name) == target:
            return {
                "display_name": city_name,
                "region": cfg["region"],
                "city": city_name,
                "lcoe": cfg["lcoe"],
                "flh_res": cfg["flh_res"],
                "desal_share": cfg["desal_share"],
                "engine_key": cfg.get("engine_key"),
            }
    for reg_name, cfg in REGION_PROFILES.items():
        if _norm(reg_name) == target:
            return {
                "display_name": reg_name,
                "region": reg_name,
                "city": None,
                "lcoe": cfg["lcoe"],
                "flh_res": cfg["flh_res"],
                "desal_share": cfg["desal_share"],
                "engine_key": STUDIO_TO_ENGINE_REGION.get(reg_name),
            }
    default_cfg = REGION_PROFILES["Dakhla-Oued Eddahab"]
    return {
        "display_name": location,
        "region": "Dakhla-Oued Eddahab",
        "city": None,
        "lcoe": default_cfg["lcoe"],
        "flh_res": default_cfg["flh_res"],
        "desal_share": default_cfg["desal_share"],
        "engine_key": "Dakhla",
    }


class StudioRequest(BaseModel):
    region: str = "Dakhla-Oued Eddahab"
    city: Optional[str] = None
    target_product: str = "e-Methanol"
    annual_production_tonnes: float = 100000


class ChatHistoryItem(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    question: str
    region: str
    city: Optional[str] = None
    target_product: str
    architectures: List[dict]
    annual_production_tonnes: Optional[float] = None
    lang: str = "fr"
    history: Optional[List[ChatHistoryItem]] = None
    
    
class ExportExcelRequest(BaseModel):
    region: str = "Dakhla-Oued Eddahab"
    city: Optional[str] = None
    target_product: str = "e-Methanol"
    annual_production_tonnes: float = 100000
    lang: str = "fr"


@app.post("/studio/export-excel")
def studio_export_excel(req: ExportExcelRequest):
    sim_data = recommend_architectures(
        StudioRequest(
            region=req.region,
            city=req.city,
            target_product=req.target_product,
            annual_production_tonnes=req.annual_production_tonnes,
        )
    )
    excel_stream = build_native_excel_report(
        region=sim_data["region"],
        city=sim_data["city"],
        target_product=req.target_product,
        annual_production_tonnes=req.annual_production_tonnes,
        architectures=sim_data["architectures"],
        sensitivity_curve=sim_data["sensitivity_curve"],
        pareto_others=sim_data["pareto_others"],
        lang=req.lang,
    )
    loc_slug = _norm(req.city or req.region).replace(" ", "_")
    prod_slug = _norm(req.target_product).replace(" ", "_")
    filename = f"sherpa_h2_{loc_slug}_{prod_slug}.xlsx"
    return StreamingResponse(
        excel_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _build_fallback_resultats(architectures: List[dict], annual_tonnes: float) -> dict:
    cap_kw = round(max(20000.0, min(1500000.0, annual_tonnes)), 1)
    ratios = [75, 90, 65]
    entries = []
    for idx, arch in enumerate(architectures[:3]):
        entries.append({
            "architecture": arch.get("badge", f"Architecture {idx + 1}"),
            "lcoh_eur_kg": float(arch.get("cost", 0.0)),
            "co2_kg_par_kg": float(arch.get("co2", 0.0)),
            "ratio_pct": ratios[idx] if idx < len(ratios) else 75,
            "puissance_kw": cap_kw,
        })
    while len(entries) < 3:
        entries.append(entries[-1] if entries else {
            "architecture": "Best overall",
            "lcoh_eur_kg": 0.0,
            "co2_kg_par_kg": 0.0,
            "ratio_pct": 75,
            "puissance_kw": cap_kw,
        })
    return {
        "best_overall": entries[0],
        "lowest_cost": entries[1],
        "lowest_co2": entries[2],
        "toutes_architectures": entries,
    }


@app.get("/")
def root():
    return {"message": "H2-Maroc Decision Studio API is running", "docs": "/docs"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/defaults")
def get_defaults():
    return load_defaults()


@app.get("/locations")
def get_locations():
    """Retourne les 12 régions et les villes rattachées."""
    cities_by_region = {r: [] for r in REGION_PROFILES}
    for city, cfg in CITY_PROFILES.items():
        cities_by_region[cfg["region"]].append(city)
    return {"regions": list(REGION_PROFILES.keys()), "cities_by_region": cities_by_region}


@app.post("/scenarios/simulate", response_model=ScenarioOutput)
def simulate_scenario(payload: ScenarioInput):
    return run_scenario_simulation(payload.model_dump())


@app.post("/studio/recommend")
def recommend_architectures(req: StudioRequest):
    loc = _resolve_location(req.city if req.city else req.region)
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
            "local_lcoe_eur_per_kwh": loc["lcoe"],
            "flh_res_hours": loc["flh_res"],
            "storage_duration_hours": storage_h,
            "ev_smart_charging_share": ev_share,
            "water_efficiency_factor": water_eff,
            "desalination_share": loc["desal_share"],
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

    flh_multipliers = [0.80, 0.90, 1.00, 1.10, 1.20]
    sensitivity_curve = []
    for mult in flh_multipliers:
        flh_test = round(loc["flh_res"] * mult)
        point = {"flh": flh_test, "label": f"{int((mult - 1) * 100):+d}%"}
        for arch_id, rank, label, color, ratio, storage_h, ev_share, water_eff, cost_factor, water_factor in configs:
            sim_s = run_scenario_simulation({
                "scenario_name": label,
                "ely_res_ratio": ratio,
                "electrolyzer_capacity_mw": cap_mw,
                "local_lcoe_eur_per_kwh": loc["lcoe"],
                "flh_res_hours": flh_test,
                "storage_duration_hours": storage_h,
                "ev_smart_charging_share": ev_share,
                "water_efficiency_factor": water_eff,
                "desalination_share": loc["desal_share"],
                "season": "annual",
            })
            point[arch_id] = round(sim_s["metrics"]["lcoh_eur_per_kg"] * prod["cost_mult"] * cost_factor, 2)
        sensitivity_curve.append(point)

    return {
        "region": loc["region"],
        "city": loc["city"],
        "display_location": loc["display_name"],
        "target_product": req.target_product,
        "annual_production_tonnes": req.annual_production_tonnes,
        "architectures": architectures,
        "pareto_others": pareto_others,
        "sensitivity_curve": sensitivity_curve,
    }


@app.post("/studio/chat")
def studio_chat(req: ChatRequest):
    loc = _resolve_location(req.city if req.city else req.region)
    engine_region = loc["engine_key"]
    comparaison = None
    sources = ["src/engine.py (Optimisation EnR-H2)", "src/ai_assistant.py (SHERPA LLM)"]

    if engine_region:
        resultats = optimiser_architecture(engine_region, n_mc=0)
        try:
            comp = comparer_scenarios(engine_region)
            if comp and "erreur" not in comp:
                comparaison = comp
                sources.append("src/comparaison.py (Analyse multicritère)")
        except Exception:
            comparaison = None
    else:
        resultats = _build_fallback_resultats(
            req.architectures,
            req.annual_production_tonnes or 100000.0,
        )
        sources = [f"app/engine/simulator.py ({loc['display_name']})", "src/ai_assistant.py (SHERPA LLM)"]

    # Détecte si l'utilisateur demande dans le chat une autre ville/région que celle sélectionnée
    q_norm = _norm(req.question)
    mentioned_city = next(
        (c for c in CITY_PROFILES if _norm(c) in q_norm and _norm(c) != _norm(loc["display_name"])),
        None,
    )

    lang_directive = (
        "Answer in English (max 200 words), keeping decimal dots."
        if req.lang == "en"
        else "Réponds en français (max 200 mots)."
    )
    prod_info = f"Localisation active : {loc['display_name']} (Région {loc['region']}). Produit cible : {req.target_product}"
    if req.annual_production_tonnes:
        prod_info += f" ({int(req.annual_production_tonnes):,} t/an)"

    extra_note = ""
    if mentioned_city:
        target_reg = CITY_PROFILES[mentioned_city]["region"]
        extra_note = (
            f" Note : l'utilisateur demande un scénario à {mentioned_city} (région {target_reg}), "
            f"alors que la simulation affichée concerne {loc['display_name']}. "
            f"Indique-lui qu'il peut sélectionner directement la ville « {mentioned_city} » "
            f"(ou la région « {target_reg} ») dans le panneau Projet à gauche pour lancer le calcul."
        )

    enriched_question = f"{req.question}\n[{prod_info}.{extra_note} {lang_directive}]"
    historique = [m.model_dump() for m in req.history] if req.history else None

    reply = generer_explication(
        region=engine_region or loc["display_name"],
        resultats=resultats,
        question=enriched_question,
        historique=historique,
        comparaison=comparaison,
    )

    return {"reply": reply, "sources": sources}