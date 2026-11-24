import json

import pytest

from src.ai_assistant import (_resume_comparaison, construire_prompt,
                              generer_explication)
from src.ai_assistant import _ecarts_entre_regions, _ecarts_relatifs
from src.comparaison import comparer_scenarios
from src.engine import optimiser_architecture
from src.comparaison import CRITERES


@pytest.fixture(scope="module")
def donnees():
    res = optimiser_architecture("Dakhla", n_mc=0)
    comps = [comparer_scenarios("Dakhla"), comparer_scenarios("Laayoune")]
    return res, comps


@pytest.fixture(autouse=True)
def sans_api(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    
def test_ecarts_relatifs_zero_pour_le_meilleur(donnees):
    _, comps = donnees
    ecarts = _ecarts_relatifs(comps[0]["scenarios"])
    # le scénario le moins cher a un écart de 0 % sur le LCOH
    moins_cher = comps[0]["scenarios"]
    nom = min(moins_cher, key=lambda n: moins_cher[n]["valeurs"]["lcoh_eur_kg"])
    assert ecarts[nom]["lcoh_eur_kg"] == 0
    
def test_pas_d_ecart_pour_les_interruptions(donnees):
    _, comps = donnees
    ecarts = _ecarts_relatifs(comps[0]["scenarios"])
    assert all("interruption_max_h" not in e for e in ecarts.values())


def test_resume_contient_les_criteres_actifs(donnees):
    from src.ai_assistant import _resume_comparaison
    _, comps = donnees
    resume = _resume_comparaison(comps[0])
    assert any(c["famille"] == "technique" for c in resume[0]["criteres_actifs"])


def test_ecarts_entre_regions_calcules(donnees):
    _, comps = donnees
    e = _ecarts_entre_regions(comps)
    cle = "Laayoune_par_rapport_a_Dakhla"
    assert cle in e
    lcoh = e[cle]["Eolien"]["lcoh_eur_kg"]
    assert lcoh["ecart_pct"] > 5   # Laayoune est nettement plus cher que Dakhla


def test_ecarts_entre_regions_une_seule_region(donnees):
    _, comps = donnees
    assert _ecarts_entre_regions([comps[0]]) is None


def test_resume_serialisable_et_compact(donnees):
    _, comps = donnees
    resume = _resume_comparaison(comps)
    assert len(resume) == 2
    assert len(json.dumps(resume, allow_nan=False)) < 12000


def test_prompt_contient_les_deux_regions(donnees):
    res, comps = donnees
    prompt = construire_prompt("Dakhla", res, "Quelle différence ?", comps)
    assert "Dakhla" in prompt and "Laayoune" in prompt
    assert "Quelle différence ?" in prompt


def test_prompt_sans_comparaison_reste_valide(donnees):
    res, _ = donnees
    prompt = construire_prompt("Dakhla", res)
    assert "comparaison_multicritere" not in prompt


def test_texte_simule_avec_comparaison(donnees):
    res, comps = donnees
    texte = generer_explication("Dakhla", res, comparaison=comps)
    assert "Comparaison multicritère à Dakhla" in texte
    assert "Comparaison multicritère à Laayoune" in texte
    assert comps[0]["recommandation"] in texte


def test_compatibilite_ancien_appel(donnees):
    res, _ = donnees
    texte = generer_explication("Dakhla", res)
    assert isinstance(texte, str) and "Comparaison multicritère" not in texte


def test_comparaison_en_erreur_ne_plante_pas(donnees):
    res, _ = donnees
    texte = generer_explication("Dakhla", res, comparaison=[{"erreur": "Région absente"}])
    assert isinstance(texte, str) and len(texte) > 50
    

def test_prompt_contient_continuite_et_co2_decompose(donnees):
    res, comps = donnees
    prompt = construire_prompt("Dakhla", res, comparaison=comps)
    for cle in ("interruption_max_h", "mois_creux_pct", "disponibilite_pct",
                "co2_electricite_kg_par_kg", "co2_fabrication_kg_par_kg",
                "part_fabrication_dans_le_co2_pct"):
        assert cle in prompt    
        
def test_quasi_equivalent_seulement_sous_2_pct(donnees):
    _, comps = donnees
    for region in _resume_comparaison(comps):
        for s in region["scenarios"].values():
            for lib in s["criteres_quasi_equivalents_au_meilleur"]:
                cle = next(c[0] for c in CRITERES if c[1] == lib)
                assert 0 < s["ecart_relatif_au_meilleur_scenario_pct"][cle] < 2