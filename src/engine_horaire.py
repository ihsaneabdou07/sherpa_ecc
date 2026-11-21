import numpy as np
from src.engine import (calculer_capex, facteur_annuite, LHV, EAU_M3_PAR_KG,
                        OPEX_PCT, ASSURANCE)

CHARGE_MIN = 0.10   # en dessous de 10 % de charge, l'électrolyseur s'arrête


def conso_specifique(charge):
    """kWh d'électricité par kg d'H2 selon la charge (courbe simplifiée, à remplacer
    par la fiche constructeur)."""
    return 50 + 10 * (charge - 0.4) ** 2


def simuler(cf_horaire, p_parc_kw, ratio, lcoe, donnees, capex_mult=1.0):
    """Simule 8760 h et renvoie le LCOH et les indicateurs."""
    gen = cf_horaire.values * p_parc_kw               # kW produits chaque heure
    p_ely = p_parc_kw * ratio

    charge = np.minimum(gen, p_ely) / p_ely
    marche = charge >= CHARGE_MIN
    charge = np.where(marche, charge, 0.0)

    e_ely = charge * p_ely                             # kWh absorbés
    h2_kg = np.where(marche, e_ely / conso_specifique(np.maximum(charge, 1e-9)), 0).sum()
    if h2_kg <= 0:
        return None

    capex = calculer_capex(p_ely, donnees["Annee_Installation"]) * capex_mult
    af = facteur_annuite(donnees["Taux_Interet"], donnees["Duree_Vie_Electrolyseur"])
    cout_elec = lcoe * gen.sum()                       # le parc dédié est payé en entier
    cout_eau = donnees["Cout_Eau"] * EAU_M3_PAR_KG * h2_kg
    cout_fixe = capex * af + capex * OPEX_PCT

    lcoh = (cout_elec + cout_eau + cout_fixe) / h2_kg * ASSURANCE
    return {
        "lcoh": lcoh,
        "h2_kg": h2_kg,
        "gen_kwh": float(gen.sum()),                   # NOUVEAU : énergie produite par le parc
        "heures_marche": int(marche.sum()),
        "facteur_charge_ely": e_ely.sum() / (p_ely * 8760),
        "energie_perdue_pct": 100 * (1 - e_ely.sum() / gen.sum()),
    }


def optimiser_ratio(cf_horaire, p_parc_kw, lcoe, donnees):
    meilleur = None
    for pct in range(5, 151, 5):                       # jusqu'à 150 % (ely > parc)
        res = simuler(cf_horaire, p_parc_kw, pct / 100, lcoe, donnees)
        if res and (meilleur is None or res["lcoh"] < meilleur["lcoh"]):
            meilleur = {**res, "ratio_pct": pct}
    return meilleur