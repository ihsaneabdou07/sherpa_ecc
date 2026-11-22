import json
import os
from src.parametres import PARAMS as P

# ---------- Constantes ----------
LHV = P["lhv_kwh_par_kg"]       # kWh/kg : pouvoir calorifique inférieur de l'H2
EFFICACITE = 0.62               # utilisé seulement par l'ancienne version v1
EAU_M3_PAR_KG = P["eau_m3_par_kg"]
OPEX_PCT = P["opex_pct"]
ASSURANCE = P["assurance"]
HEURES_AN = 8760

def charger_donnees(region):
    """Lit le fichier JSON (sera remplacé par l'Excel de l'équipe Data)."""
    chemin = os.path.join(os.path.dirname(__file__), "..", "data", "mock_data.json")
    with open(chemin, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get(region)


def calculer_capex(puissance_kw, annee):
    """Eq. 3 : CAPEX total de l'électrolyseur en euros (paramètres dans parametres_globaux.json)."""
    cout_par_kw = (P["capex_facteur"] * (P["capex_coef"] * puissance_kw ** P["capex_exposant"])
                   * (P["capex_baisse_annuelle"] ** (annee - P["capex_annee_ref"])))
    return cout_par_kw * puissance_kw


def facteur_annuite(taux, n):
    """Facteur d'annuité pour étaler le CAPEX sur la durée de vie."""
    return (taux * (1 + taux) ** n) / ((1 + taux) ** n - 1)


def fraction_energie_captee(ratio):
    """
    Part de l'énergie du parc ENR absorbée par l'électrolyseur.
    Modèle SIMPLIFIÉ (placeholder) : plus l'électrolyseur est gros, plus il capte
    d'énergie, avec des rendements décroissants.
    À remplacer plus tard par un vrai calcul horaire.
    """
    return 1 - (1 - ratio) ** 2


def calculer_lcoh(ratio, donnees, archi):
    """LCOH (€/kg) pour un ratio électrolyseur/parc donné, avec les Eq. 3 à 6."""
    p_parc = donnees["Puissance_Parc_ENR_kW"]
    p_ely = p_parc * ratio

    # Eq. 3 : CAPEX et OPEX
    capex = calculer_capex(p_ely, donnees["Annee_Installation"])
    opex = capex * OPEX_PCT

    # H2 produit par an
    energie_dispo = p_parc * HEURES_AN * archi["Facteur_Charge"]   # kWh/an
    energie_ely = energie_dispo * fraction_energie_captee(ratio)   # kWh/an
    h2_kg = energie_ely * EFFICACITE / LHV

    # Eq. 4 : LCOH variable (électricité + eau)
    lcoh_var = (archi["LCOE"] * LHV / EFFICACITE) + (donnees["Cout_Eau"] * EAU_M3_PAR_KG)

    # Eq. 5 : LCOH fixe (OPEX + CAPEX annualisé) / H2 produit
    af = facteur_annuite(donnees["Taux_Interet"], donnees["Duree_Vie_Electrolyseur"])
    lcoh_fix = (opex + capex * af) / h2_kg

    # Eq. 6 : total avec assurance
    lcoh = (lcoh_var + lcoh_fix) * ASSURANCE
    return lcoh, h2_kg, p_ely


def optimiser_architecture_v1(region):
    """
    Pour chaque architecture (Eolien, Solaire, Hybride), teste les ratios 5 % à 100 %
    et garde le meilleur. Puis désigne les 3 scénarios.
    """
    donnees = charger_donnees(region)
    if not donnees:
        return {"erreur": f"Région '{region}' non trouvée"}

    candidats = []
    for nom, archi in donnees["Architectures"].items():
        meilleur = None
        for ratio_pct in range(5, 101, 5):
            lcoh, h2_kg, p_ely = calculer_lcoh(ratio_pct / 100, donnees, archi)
            if meilleur is None or lcoh < meilleur["lcoh_eur_kg"]:
                meilleur = {
                    "architecture": nom,
                    "lcoh_eur_kg": round(lcoh, 3),
                    "co2_kg_par_kg": round(archi["CO2_kg_par_kWh"] * LHV / EFFICACITE, 3),
                    "eau_L_par_kg": round(EAU_M3_PAR_KG * 1000, 1),
                    "trl": archi["TRL"],
                    "ratio_pct": ratio_pct,
                    "puissance_kw": round(p_ely),
                    "h2_tonnes_an": round(h2_kg / 1000, 1),
                }
        candidats.append(meilleur)

    # Normalisation min-max pour trouver le meilleur compromis
    def norm(valeur, vmin, vmax):
        return 0 if vmax == vmin else (valeur - vmin) / (vmax - vmin)

    couts = [c["lcoh_eur_kg"] for c in candidats]
    co2s = [c["co2_kg_par_kg"] for c in candidats]
    for c in candidats:
        c["score"] = round(
            0.5 * norm(c["lcoh_eur_kg"], min(couts), max(couts))
            + 0.5 * norm(c["co2_kg_par_kg"], min(co2s), max(co2s)), 3)

    return {
        "best_overall": min(candidats, key=lambda c: c["score"]),
        "lowest_cost": min(candidats, key=lambda c: c["lcoh_eur_kg"]),
        "lowest_co2": min(candidats, key=lambda c: c["co2_kg_par_kg"]),
        "toutes_architectures": candidats,   # pour le Pareto et le radar
    }
    
def optimiser_architecture(region, n_mc=0, surcharges=None):
    """Point d'entrée utilisé par le frontend : moteur horaire."""
    from src.optimiseur import optimiser_architecture_horaire
    return optimiser_architecture_horaire(region, n_mc=n_mc, surcharges=surcharges)