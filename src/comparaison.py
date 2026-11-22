import csv
import os

import numpy as np

from src.engine import optimiser_architecture

CATEGORIES = ["economique", "environnemental", "technique"]

# (clé, libellé, catégorie, sens) ; sens "min" = plus petit est meilleur
CRITERES = [
    ("lcoh_eur_kg", "LCOH (€/kg)", "economique", "min"),
    ("capex_par_kg_h2_an", "CAPEX par kg d'H2 annuel (€)", "economique", "min"),
    ("proba_moins_cher_pct", "Probabilité d'être le moins cher (%)", "economique", "max"),
    ("co2_kg_par_kg", "CO2 (kg/kg H2)", "environnemental", "min"),
    ("eau_L_par_kg", "Eau (L/kg H2)", "environnemental", "min"),
    ("trl", "TRL (maturité 1-9)", "technique", "max"),
    ("facteur_charge_electrolyseur", "Utilisation de l'électrolyseur", "technique", "max"),
    ("energie_perdue_pct", "Énergie perdue (%)", "technique", "min"),
    ("h2_tonnes_an", "Production H2 (t/an)", "technique", "max"),
]

# Poids par famille de critères (somme = 1). HYPOTHÈSE : à valider avec les parties prenantes.
PROFILS = {
    "equilibre": {"economique": 0.4, "environnemental": 0.3, "technique": 0.3},
    "economique": {"economique": 0.6, "environnemental": 0.2, "technique": 0.2},
    "environnemental": {"economique": 0.2, "environnemental": 0.6, "technique": 0.2},
    "technique": {"economique": 0.2, "environnemental": 0.2, "technique": 0.6},
}


def _criteres_actifs(archis):
    """Un critère est ignoré s'il est absent ou identique pour tous les scénarios."""
    actifs = []
    for cle, libelle, cat, sens in CRITERES:
        valeurs = [a.get(cle) for a in archis]
        if any(v is None for v in valeurs):
            continue
        if max(valeurs) - min(valeurs) < 1e-9:
            continue
        actifs.append((cle, libelle, cat, sens))
    return actifs


def _normaliser(archis, actifs):
    """Score de 0 à 1 par critère et par scénario (1 = meilleur des scénarios comparés)."""
    norm = {}
    for cle, _, _, sens in actifs:
        v = np.array([a[cle] for a in archis], dtype=float)
        vmin, vmax = v.min(), v.max()
        norm[cle] = (vmax - v) / (vmax - vmin) if sens == "min" else (v - vmin) / (vmax - vmin)
    return norm


def _matrice_categories(norm, actifs, n):
    """Score moyen par famille (NaN si la famille n'a aucun critère actif)."""
    M = np.full((n, len(CATEGORIES)), np.nan)
    for j, cat in enumerate(CATEGORIES):
        cles = [c for c, _, k, _ in actifs if k == cat]
        if cles:
            M[:, j] = np.mean([norm[c] for c in cles], axis=0)
    return M


def _totaux(M, W):
    """
    Score total pour chaque jeu de poids. M : (scénarios, 3) ; W : (jeux de poids, 3).
    Les familles sans critère actif sont ignorées et les poids restants renormalisés.
    Renvoie un tableau (jeux de poids, scénarios).
    """
    masque = ~np.isnan(M[0])
    M0 = np.nan_to_num(M, nan=0.0)
    return (W @ M0.T) / (W * masque).sum(axis=1)[:, None]


def _verifier_poids(poids):
    if set(poids) != set(CATEGORIES) or any(p < 0 for p in poids.values()) or sum(poids.values()) <= 0:
        raise ValueError(f"Poids invalides : fournissez {CATEGORIES}, valeurs positives.")


def comparer_scenarios(region, n_mc=0, profils=None, poids_perso=None, n_poids=2000, seed=0):
    """
    Compare les scénarios d'une région sur plusieurs critères.
    n_mc > 0 ajoute le critère de robustesse économique (Monte Carlo, ~20 s pour 200).
    poids_perso : ex. {"economique": 0.5, "environnemental": 0.3, "technique": 0.2}
    """
    res = optimiser_architecture(region, n_mc=n_mc)
    if "erreur" in res:
        return res

    archis = res["toutes_architectures"]
    noms = [a["architecture"] for a in archis]
    n = len(archis)

    profils = dict(profils or PROFILS)
    if poids_perso:
        profils["personnalise"] = poids_perso
    for p in profils.values():
        _verifier_poids(p)

    actifs = _criteres_actifs(archis)
    norm = _normaliser(archis, actifs)
    M = _matrice_categories(norm, actifs, n)

    # Classement pour chaque profil
    classement, gagnant_par_profil = {}, {}
    for nom_p, poids in profils.items():
        W = np.array([[poids[c] for c in CATEGORIES]], dtype=float)
        tot = _totaux(M, W)[0]
        ordre = np.argsort(-tot)
        classement[nom_p] = [
            {"rang": r + 1, "architecture": noms[i], "score": round(float(tot[i]), 3)}
            for r, i in enumerate(ordre)
        ]
        gagnant_par_profil[nom_p] = noms[ordre[0]]

    # Robustesse du classement face aux poids : combien de jeux de poids aléatoires chaque scénario gagne
    rng = np.random.default_rng(seed)
    Wr = rng.dirichlet([1, 1, 1], size=n_poids)
    gagnants = np.argmax(_totaux(M, Wr), axis=1)
    robustesse = {noms[i]: round(100 * float((gagnants == i).mean()), 1) for i in range(n)}

    # Détail par scénario
    scenarios = {}
    for i, a in enumerate(archis):
        scenarios[a["architecture"]] = {
            "valeurs": {cle: a[cle] for cle, *_ in CRITERES if cle in a},
            "scores_categories": {
                cat: (None if np.isnan(M[i, j]) else round(float(M[i, j]), 3))
                for j, cat in enumerate(CATEGORIES)
            },
            "forces": [lib for cle, lib, _, _ in actifs if norm[cle][i] >= 0.999],
            "faiblesses": [lib for cle, lib, _, _ in actifs if norm[cle][i] <= 0.001],
            "ratio_pct": a["ratio_pct"],
            "puissance_kw": a["puissance_kw"],
        }

    actifs_cles = {c[0] for c in actifs}
    return {
        "region": region,
        "criteres": [
            {"cle": cle, "libelle": lib, "categorie": cat, "sens": sens,
             "actif": cle in actifs_cles}
            for cle, lib, cat, sens in CRITERES
        ],
        "profils": profils,
        "scenarios": scenarios,
        "classement": classement,
        "gagnant_par_profil": gagnant_par_profil,
        "robustesse_poids_pct": robustesse,
        "recommandation": gagnant_par_profil.get("equilibre"),
    }


def comparer_regions(regions, n_mc=0, **kwargs):
    """Compare les scénarios dans chaque région et résume le scénario recommandé par profil."""
    detail = {r: comparer_scenarios(r, n_mc=n_mc, **kwargs) for r in regions}
    synthese = []
    for r, d in detail.items():
        if "erreur" in d:
            continue
        for profil, nom in d["gagnant_par_profil"].items():
            v = d["scenarios"][nom]["valeurs"]
            synthese.append({
                "region": r, "profil": profil, "scenario_recommande": nom,
                "lcoh_eur_kg": v["lcoh_eur_kg"], "co2_kg_par_kg": v["co2_kg_par_kg"],
                "h2_tonnes_an": v["h2_tonnes_an"],
            })
    return {"regions": detail, "synthese": synthese}


def exporter_csv(comparaison, dossier="exports"):
    """Écrit un CSV (séparateur ';', lisible dans Excel) pour le rapport."""
    os.makedirs(dossier, exist_ok=True)
    chemin = os.path.join(dossier, f"comparaison_{comparaison['region']}.csv")
    noms = list(comparaison["scenarios"])
    cles = list(comparaison["scenarios"][noms[0]]["valeurs"])
    profils = list(comparaison["classement"])
    scores = {p: {l["architecture"]: l["score"] for l in comparaison["classement"][p]} for p in profils}

    with open(chemin, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["architecture"] + cles + [f"score_{p}" for p in profils]
                   + ["gagne_pct_des_poids_aleatoires"])
        for nom in noms:
            w.writerow([nom] + [comparaison["scenarios"][nom]["valeurs"][c] for c in cles]
                       + [scores[p][nom] for p in profils]
                       + [comparaison["robustesse_poids_pct"][nom]])
    return chemin