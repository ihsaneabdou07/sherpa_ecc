import json

import pytest

from src.engine import optimiser_architecture
from src.ai_assistant import generer_explication

REGIONS = ["Dakhla", "Laayoune"]
SCENARIOS = ["best_overall", "lowest_cost", "lowest_co2"]
CHAMPS_OBLIGATOIRES = {
    "architecture", "lcoh_eur_kg", "co2_kg_par_kg", "eau_L_par_kg", "trl",
    "ratio_pct", "puissance_kw", "h2_tonnes_an", "facteur_charge_parc",
    "energie_perdue_pct", "score",
}
CHAMPS_MONTE_CARLO = {"lcoh_p10", "lcoh_p50", "lcoh_p90", "proba_moins_cher_pct"}


@pytest.fixture(scope="module", params=REGIONS)
def resultat(request):
    """Calcule une fois par région (rapide : n_mc=0, météo en cache)."""
    return optimiser_architecture(request.param, n_mc=0)


# ---------- Structure du dictionnaire (contrat frontend) ----------

def test_cles_principales(resultat):
    for cle in SCENARIOS + ["toutes_architectures"]:
        assert cle in resultat


def test_trois_architectures(resultat):
    noms = {a["architecture"] for a in resultat["toutes_architectures"]}
    assert noms == {"Eolien", "Solaire", "Hybride"}


def test_champs_obligatoires(resultat):
    for archi in resultat["toutes_architectures"]:
        manquants = CHAMPS_OBLIGATOIRES - set(archi)
        assert not manquants, f"{archi['architecture']} : champs manquants {manquants}"
    for scenario in SCENARIOS:
        assert CHAMPS_OBLIGATOIRES <= set(resultat[scenario])


def test_serialisable_en_json(resultat):
    """Échoue si un np.float64 ou un NaN se glisse dans le résultat."""
    json.dumps(resultat, allow_nan=False)


# ---------- Cohérence des valeurs ----------

def test_valeurs_positives_et_plausibles(resultat):
    for a in resultat["toutes_architectures"]:
        assert 0.5 < a["lcoh_eur_kg"] < 15, "LCOH hors plage (€/kg)"
        assert a["co2_kg_par_kg"] > 0
        assert a["h2_tonnes_an"] > 0
        assert 0 < a["ratio_pct"] <= 150
        assert a["puissance_kw"] > 0
        assert 0 <= a["energie_perdue_pct"] <= 100
        assert 0 < a["facteur_charge_parc"] < 1


def test_scenarios_coherents_avec_la_liste(resultat):
    archis = resultat["toutes_architectures"]
    moins_cher = min(a["lcoh_eur_kg"] for a in archis)
    moins_co2 = min(a["co2_kg_par_kg"] for a in archis)
    assert resultat["lowest_cost"]["lcoh_eur_kg"] == moins_cher
    assert resultat["lowest_co2"]["co2_kg_par_kg"] == moins_co2
    assert resultat["best_overall"]["architecture"] in {a["architecture"] for a in archis}


def test_scores_entre_0_et_1(resultat):
    for a in resultat["toutes_architectures"]:
        assert 0 <= a["score"] <= 1


# ---------- Comportement entre régions ----------

def test_les_regions_donnent_des_resultats_differents():
    d = optimiser_architecture("Dakhla", n_mc=0)["best_overall"]
    l = optimiser_architecture("Laayoune", n_mc=0)["best_overall"]
    assert d["lcoh_eur_kg"] != l["lcoh_eur_kg"]
    assert d["co2_kg_par_kg"] != l["co2_kg_par_kg"]


def test_region_inconnue():
    res = optimiser_architecture("Atlantide", n_mc=0)
    assert "erreur" in res
    assert "best_overall" not in res


# ---------- Monte Carlo ----------

@pytest.fixture(scope="module")
def resultat_mc():
    return optimiser_architecture("Dakhla", n_mc=10)


def test_champs_monte_carlo(resultat_mc):
    for archi in resultat_mc["toutes_architectures"]:
        assert CHAMPS_MONTE_CARLO <= set(archi)
        assert archi["lcoh_p10"] <= archi["lcoh_p50"] <= archi["lcoh_p90"]
        assert 0 <= archi["proba_moins_cher_pct"] <= 100


def test_probabilites_somment_a_100(resultat_mc):
    total = sum(a["proba_moins_cher_pct"] for a in resultat_mc["toutes_architectures"])
    assert total == pytest.approx(100, abs=0.5)


def test_monte_carlo_serialisable(resultat_mc):
    json.dumps(resultat_mc, allow_nan=False)


# ---------- Assistant IA (sans appel réseau) ----------

def test_assistant_mode_simule(monkeypatch, resultat):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    texte = generer_explication("Dakhla", resultat)
    assert isinstance(texte, str) and len(texte) > 50
    assert resultat["best_overall"]["architecture"] in texte


def test_assistant_propage_une_erreur(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert "non trouvée" in generer_explication("X", {"erreur": "Région 'X' non trouvée"})