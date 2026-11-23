import copy

import numpy as np
from src.engine import charger_donnees, LHV, EAU_M3_PAR_KG
from src.engine_horaire import simuler
from src.meteo import telecharger_meteo, profil_solaire, profil_eolien
from src.parametres import PARAMS as P

# HYPOTHÈSE : multiplicateur CAPEX nominal (centre de la plage 1 à 2,5 du Monte Carlo).
# À valider avec l'équipe Data et l'article de Hofrichter.
CAPEX_MULT_NOMINAL = P["capex_mult_nominal"]
RATIOS = range(10, 151, 5)
PART_SOLAIRE = P["part_solaire_hybride"]

# Paramètres que l'on peut modifier pour une analyse de sensibilité
SURCHARGES_VALIDES = {"lcoe_solaire", "lcoe_eolien", "capex_mult", "taux_interet",
                      "co2_solaire", "co2_eolien"}


def _poids_solaire(cf_sol, cf_vent):
    """Part de l'énergie hybride produite par le solaire."""
    e_sol = PART_SOLAIRE * cf_sol.mean()
    e_vent = (1 - PART_SOLAIRE) * cf_vent.mean()
    return float(e_sol / (e_sol + e_vent))


def _lcoe_hybride(lcoe_sol, lcoe_vent, cf_sol, cf_vent):
    """LCOE de l'hybride pondéré par l'énergie produite par chaque source."""
    w = _poids_solaire(cf_sol, cf_vent)
    return w * lcoe_sol + (1 - w) * lcoe_vent


def _meilleur_ratio(cf, p_parc, lcoe, donnees, capex_mult):
    meilleur = None
    for pct in RATIOS:
        r = simuler(cf, p_parc, pct / 100, lcoe, donnees, capex_mult)
        if r and (meilleur is None or r["lcoh"] < meilleur["lcoh"]):
            meilleur = {**r, "ratio_pct": pct}
    return meilleur


def _monte_carlo(profils, lcoe_sol, lcoe_vent, cf_sol, cf_vent, donnees, p_parc, n, seed=0):
    """Mêmes tirages pour toutes les architectures (un tirage = un 'monde')."""
    rng = np.random.default_rng(seed)
    noms = list(profils)
    res = {k: [] for k in noms}
    for _ in range(n):
        d = dict(donnees)
        d["Taux_Interet"] = rng.uniform(0.04, 0.09)
        capex_mult = rng.uniform(1.0, 2.5)
        ls = lcoe_sol * rng.uniform(0.8, 1.3)
        lv = lcoe_vent * rng.uniform(0.8, 1.3)
        lcoes = {"Eolien": lv, "Solaire": ls,
                 "Hybride": _lcoe_hybride(ls, lv, cf_sol, cf_vent)}
        for nom in noms:
            m = _meilleur_ratio(profils[nom], p_parc, lcoes[nom], d, capex_mult)
            res[nom].append(m["lcoh"] if m else np.nan)

    M = np.array([res[k] for k in noms])
    gagnant = np.nanargmin(np.nan_to_num(M, nan=1e9), axis=0)
    out = {}
    for i, nom in enumerate(noms):
        p10, p50, p90 = np.nanpercentile(M[i], [10, 50, 90])
        out[nom] = {
            "lcoh_p10": round(float(p10), 3),
            "lcoh_p50": round(float(p50), 3),
            "lcoh_p90": round(float(p90), 3),
            "proba_moins_cher_pct": round(100 * float((gagnant == i).mean()), 1),
        }
    return out


def optimiser_architecture_horaire(region, n_mc=0, annee_meteo=2022, surcharges=None):
    """
    Même format de sortie que l'ancienne version.
    n_mc = 0   : rapide (déterministe), pour l'interface.
    n_mc = 200 : ajoute P10/P50/P90 et la probabilité d'être le moins cher (~20 s).
    surcharges : dict optionnel pour l'analyse de sensibilité, par exemple
                 {"lcoe_solaire": 0.025, "capex_mult": 2.0}. Clés valides :
                 lcoe_solaire, lcoe_eolien, capex_mult, taux_interet, co2_solaire, co2_eolien.
    """
    surcharges = surcharges or {}
    inconnues = set(surcharges) - SURCHARGES_VALIDES
    if inconnues:
        return {"erreur": f"Surcharges inconnues : {sorted(inconnues)}"}

    donnees = charger_donnees(region)
    if not donnees:
        return {"erreur": f"Région '{region}' non trouvée"}
    if "Latitude" not in donnees or "Longitude" not in donnees:
        return {"erreur": f"Coordonnées manquantes pour '{region}' dans le JSON"}

    # Copie : les surcharges ne modifient jamais le fichier de données
    donnees = copy.deepcopy(donnees)
    archis = donnees["Architectures"]
    if "taux_interet" in surcharges:
        donnees["Taux_Interet"] = float(surcharges["taux_interet"])
    if "lcoe_solaire" in surcharges:
        archis["Solaire"]["LCOE"] = float(surcharges["lcoe_solaire"])
    if "lcoe_eolien" in surcharges:
        archis["Eolien"]["LCOE"] = float(surcharges["lcoe_eolien"])
    if "co2_solaire" in surcharges:
        archis["Solaire"]["CO2_kg_par_kWh"] = float(surcharges["co2_solaire"])
    if "co2_eolien" in surcharges:
        archis["Eolien"]["CO2_kg_par_kWh"] = float(surcharges["co2_eolien"])
    capex_mult = float(surcharges.get("capex_mult", CAPEX_MULT_NOMINAL))

    df = telecharger_meteo(donnees["Latitude"], donnees["Longitude"],
                           annee=annee_meteo, nom=region.lower())
    cf_sol, cf_vent = profil_solaire(df), profil_eolien(df)
    profils = {
        "Eolien": cf_vent,
        "Solaire": cf_sol,
        "Hybride": PART_SOLAIRE * cf_sol + (1 - PART_SOLAIRE) * cf_vent,
    }

    p_parc = donnees["Puissance_Parc_ENR_kW"]
    lcoe_sol, lcoe_vent = archis["Solaire"]["LCOE"], archis["Eolien"]["LCOE"]
    lcoes = {"Eolien": lcoe_vent, "Solaire": lcoe_sol,
             "Hybride": _lcoe_hybride(lcoe_sol, lcoe_vent, cf_sol, cf_vent)}

    # Intensité carbone (kg CO2/kWh) ; l'hybride est pondéré par l'énergie de chaque source
    w_sol = _poids_solaire(cf_sol, cf_vent)
    co2_kwh = {
        "Eolien": archis["Eolien"]["CO2_kg_par_kWh"],
        "Solaire": archis["Solaire"]["CO2_kg_par_kWh"],
        "Hybride": w_sol * archis["Solaire"]["CO2_kg_par_kWh"]
                   + (1 - w_sol) * archis["Eolien"]["CO2_kg_par_kWh"],
    }

    candidats = []
    for nom, cf in profils.items():
        m = _meilleur_ratio(cf, p_parc, lcoes[nom], donnees, capex_mult)
        if m is None:
            continue   # architecture sans production exploitable
        candidats.append({
            "architecture": nom,
            "lcoh_eur_kg": round(float(m["lcoh"]), 3),
            # Émissions du parc entier rapportées au H2 produit (l'énergie perdue compte)
            "co2_kg_par_kg": round(float(co2_kwh[nom] * m["gen_kwh"] / m["h2_kg"]), 3),
            "eau_L_par_kg": round(EAU_M3_PAR_KG * 1000, 1),
            "trl": archis[nom]["TRL"],
            "ratio_pct": m["ratio_pct"],
            "puissance_kw": round(p_parc * m["ratio_pct"] / 100),
            "h2_tonnes_an": round(float(m["h2_kg"]) / 1000, 1),
            "facteur_charge_parc": round(float(cf.mean()), 3),
            "disponibilite_pct": round(float(m["disponibilite_pct"]), 1),
            "interruption_max_h": int(m["interruption_max_h"]),
            "mois_creux_pct": round(float(m["mois_creux_pct"]), 1),
            "energie_perdue_pct": round(float(m["energie_perdue_pct"]), 1),
            "capex_meur": round(float(m["capex_eur"]) / 1e6, 2),
            "capex_par_kg_h2_an": round(float(m["capex_eur"]) / float(m["h2_kg"]), 2),
            "cout_annuel_meur": round(float(m["cout_annuel_eur"]) / 1e6, 2),
            "heures_marche": int(m["heures_marche"]),
            "facteur_charge_electrolyseur": round(float(m["facteur_charge_ely"]), 3),
        })

    if not candidats:
        return {"erreur": f"Aucune architecture exploitable pour '{region}'"}

    if n_mc > 0:
        mc = _monte_carlo(profils, lcoe_sol, lcoe_vent, cf_sol, cf_vent,
                          donnees, p_parc, n_mc)
        for c in candidats:
            c.update(mc[c["architecture"]])

    def norm(v, vmin, vmax):
        return 0 if vmax == vmin else (v - vmin) / (vmax - vmin)

    couts = [c["lcoh_eur_kg"] for c in candidats]
    co2s = [c["co2_kg_par_kg"] for c in candidats]
    for c in candidats:
        c["score"] = round(float(0.5 * norm(c["lcoh_eur_kg"], min(couts), max(couts))
                           + 0.5 * norm(c["co2_kg_par_kg"], min(co2s), max(co2s))), 3)

    return {
        "best_overall": min(candidats, key=lambda c: c["score"]),
        "lowest_cost": min(candidats, key=lambda c: c["lcoh_eur_kg"]),
        "lowest_co2": min(candidats, key=lambda c: c["co2_kg_par_kg"]),
        "toutes_architectures": candidats,
    }