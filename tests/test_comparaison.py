import json

import pytest

from src.comparaison import PROFILS, comparer_regions, comparer_scenarios


@pytest.fixture(scope="module", params=["Dakhla", "Laayoune"])
def comp(request):
    return comparer_scenarios(request.param, n_mc=0)


def test_structure(comp):
    for cle in ["region", "criteres", "scenarios", "classement",
                "gagnant_par_profil", "robustesse_poids_pct", "recommandation"]:
        assert cle in comp
    assert set(comp["scenarios"]) == {"Eolien", "Solaire", "Hybride"}


def test_scores_entre_0_et_1(comp):
    for s in comp["scenarios"].values():
        for v in s["scores_categories"].values():
            assert v is None or 0 <= v <= 1


def test_classements_complets_et_tries(comp):
    assert set(comp["classement"]) >= set(PROFILS)
    for lignes in comp["classement"].values():
        assert [l["rang"] for l in lignes] == [1, 2, 3]
        scores = [l["score"] for l in lignes]
        assert scores == sorted(scores, reverse=True)


def test_robustesse_somme_100(comp):
    assert sum(comp["robustesse_poids_pct"].values()) == pytest.approx(100, abs=0.5)


def test_serialisable_en_json(comp):
    json.dumps(comp, allow_nan=False)


def test_poids_personnalises():
    c = comparer_scenarios("Dakhla", poids_perso={"economique": 0.5,
                                                   "environnemental": 0.3,
                                                   "technique": 0.2})
    assert "personnalise" in c["classement"]


def test_poids_invalides():
    with pytest.raises(ValueError):
        comparer_scenarios("Dakhla", poids_perso={"economique": 1.0})


def test_region_inconnue():
    assert "erreur" in comparer_scenarios("Atlantide")


def test_synthese_inter_regions():
    res = comparer_regions(["Dakhla", "Laayoune"])
    assert len(res["synthese"]) == 2 * len(PROFILS)