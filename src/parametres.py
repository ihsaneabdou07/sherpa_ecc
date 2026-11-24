import json
import os

# Valeurs par défaut (celles utilisées jusqu'ici). Servent de secours si le fichier manque
# ou s'il ne contient pas un paramètre.
DEFAUTS = {
    "capex_facteur": 1.05, "capex_coef": 10719, "capex_exposant": -0.299,
    "capex_baisse_annuelle": 0.98, "capex_annee_ref": 2020, "capex_mult_nominal": 1.75,
    "opex_pct": 0.025, "assurance": 1.01, "eau_m3_par_kg": 0.015, "lhv_kwh_par_kg": 33.33,
    "charge_min": 0.10, "conso_base": 50, "conso_coef": 10, "conso_charge_ref": 0.4,
    "pr_solaire": 0.80, "eolien_hauteur": 100, "eolien_cisaillement": 0.14,
    "eolien_v_in": 3, "eolien_v_nom": 12, "eolien_v_out": 25,
    "part_solaire_hybride": 0.5,
    "courbe_rendement": "hofrichter",
    "co2_stack_kg_par_kw": 137.47,
    "duree_vie_stack_h": 60000,
    "remplacement_stack": 1,
}


def charger_parametres():
    """Lit data/parametres_globaux.json ; chaque entrée est {"valeur": ..., "unite": ..., ...}."""
    params = dict(DEFAUTS)
    chemin = os.path.join(os.path.dirname(__file__), "..", "data", "parametres_globaux.json")
    try:
        with open(chemin, "r", encoding="utf-8") as f:
            brut = json.load(f)
    except FileNotFoundError:
        return params
    for cle, entree in brut.items():
        if cle.startswith("_"):
            continue
        params[cle] = entree["valeur"] if isinstance(entree, dict) else entree
    return params


PARAMS = charger_parametres()