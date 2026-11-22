import csv
import os

import numpy as np

from src.comparaison import comparer_scenarios
from src.engine import charger_donnees
from src.optimiseur import CAPEX_MULT_NOMINAL

# Plages balayées. HYPOTHÈSE : plages larges choisies par le Backend, à ajuster.
PARAMETRES = {
    "lcoe_solaire": {"libelle": "LCOE solaire (€/kWh)", "plage": (0.010, 0.060)},
    "lcoe_eolien": {"libelle": "LCOE éolien (€/kWh)", "plage": (0.015, 0.060)},
    "capex_mult": {"libelle": "Multiplicateur CAPEX", "plage": (0.8, 3.0)},
    "taux_interet": {"libelle": "Taux d'intérêt", "plage": (0.03, 0.12)},
    "co2_solaire": {"libelle": "Intensité carbone du solaire (kg CO2/kWh)", "plage": (0.020, 0.180)},
    "co2_eolien": {"libelle": "Intensité carbone de l'éolien (kg CO2/kWh)", "plage": (0.005, 0.120)},
}

CRITERES_GAGNANT = {
    "gagnant_compromis": "scénario recommandé",
    "gagnant_cout": "scénario le moins cher",
}


def _valeur_base(region, parametre):
    d = charger_donnees(region)
    if parametre == "lcoe_solaire":
        return d["Architectures"]["Solaire"]["LCOE"]
    if parametre == "lcoe_eolien":
        return d["Architectures"]["Eolien"]["LCOE"]
    if parametre == "taux_interet":
        return d["Taux_Interet"]
    if parametre == "co2_solaire":
        return d["Architectures"]["Solaire"]["CO2_kg_par_kWh"]
    if parametre == "co2_eolien":
        return d["Architectures"]["Eolien"]["CO2_kg_par_kWh"]
    if parametre == "capex_mult":
        return CAPEX_MULT_NOMINAL
    raise ValueError(f"Paramètre inconnu : {parametre}")


def _evaluer(region, parametre, valeur, profil):
    """Calcule les scénarios avec un paramètre modifié et renvoie les gagnants."""
    c = comparer_scenarios(region, surcharges={parametre: float(valeur)})
    if "erreur" in c:
        raise ValueError(c["erreur"])
    lcoh = {n: s["valeurs"]["lcoh_eur_kg"] for n, s in c["scenarios"].items()}
    return {
        "gagnant_compromis": c["classement"][profil][0]["architecture"],
        "gagnant_cout": min(lcoh, key=lcoh.get),
        "lcoh": lcoh,
    }


def _seuil(region, parametre, p_avant, p_apres, critere, profil):
    """Affine par dichotomie la valeur où le gagnant change entre deux points voisins."""
    bas, haut = p_avant["valeur"], p_apres["valeur"]
    gagnant_bas = p_avant[critere]
    for _ in range(10):
        milieu = (bas + haut) / 2
        if _evaluer(region, parametre, milieu, profil)[critere] == gagnant_bas:
            bas = milieu
        else:
            haut = milieu
    return (bas + haut) / 2


def analyser_parametre(region, parametre, n_points=13, profil="equilibre"):
    if parametre not in PARAMETRES:
        raise ValueError(f"Paramètre inconnu : {parametre}. Choix : {list(PARAMETRES)}")
    lo, hi = PARAMETRES[parametre]["plage"]

    points = []
    for v in np.linspace(lo, hi, n_points):
        points.append({"valeur": float(v), **_evaluer(region, parametre, v, profil)})

    base = _valeur_base(region, parametre)
    ref = _evaluer(region, parametre, base, profil)

    changements = []
    for critere in CRITERES_GAGNANT:
        for p, q in zip(points, points[1:]):
            if p[critere] != q[critere]:
                seuil = _seuil(region, parametre, p, q, critere, profil)
                changements.append({
                    "critere": critere,
                    "de": p[critere],
                    "vers": q[critere],
                    "seuil": float(seuil),
                    "ecart_a_la_base_pct": round(100 * (seuil - base) / base, 1),
                })

    return {
        "parametre": parametre,
        "libelle": PARAMETRES[parametre]["libelle"],
        "plage": (lo, hi),
        "valeur_base": base,
        "gagnant_base": {c: ref[c] for c in CRITERES_GAGNANT},
        "points": points,
        "changements": changements,
    }


def analyser_region(region, parametres=None, n_points=13, profil="equilibre"):
    parametres = parametres or list(PARAMETRES)
    return {
        "region": region,
        "profil": profil,
        "analyses": {p: analyser_parametre(region, p, n_points, profil) for p in parametres},
    }


def resume_textuel(analyse_region):
    """Une phrase par paramètre et par critère, prête à relire pour le rapport."""
    lignes = []
    for a in analyse_region["analyses"].values():
        lo, hi = a["plage"]
        for critere, etiquette in CRITERES_GAGNANT.items():
            gagnant = a["gagnant_base"][critere]
            changements = [c for c in a["changements"] if c["critere"] == critere]
            if not changements:
                lignes.append(
                    f"{a['libelle']} : {gagnant} reste le {etiquette} sur toute la plage "
                    f"testée ({lo:.4g} à {hi:.4g}) ; valeur de base {a['valeur_base']:.4g}.")
            for c in changements:
                lignes.append(
                    f"{a['libelle']} : le {etiquette} passe de {c['de']} à {c['vers']} autour de "
                    f"{c['seuil']:.4g} (valeur de base {a['valeur_base']:.4g}, "
                    f"soit {c['ecart_a_la_base_pct']:+.0f} %).")
    return lignes


def exporter_csv(analyse_region, dossier="exports"):
    """CSV (séparateur ';', lisible dans Excel) de tous les points balayés."""
    os.makedirs(dossier, exist_ok=True)
    chemin = os.path.join(dossier, f"sensibilite_{analyse_region['region']}.csv")
    with open(chemin, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["parametre", "valeur", "gagnant_recommande", "gagnant_moins_cher",
                    "lcoh_Eolien", "lcoh_Solaire", "lcoh_Hybride"])
        for a in analyse_region["analyses"].values():
            for p in a["points"]:
                w.writerow([a["parametre"], round(p["valeur"], 5), p["gagnant_compromis"],
                            p["gagnant_cout"], p["lcoh"].get("Eolien"),
                            p["lcoh"].get("Solaire"), p["lcoh"].get("Hybride")])
    return chemin