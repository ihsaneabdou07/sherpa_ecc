import pytest

from src.engine import optimiser_architecture
from src.sensibilite import analyser_parametre, analyser_region, resume_textuel


def lcoh(res, nom):
    return next(a["lcoh_eur_kg"] for a in res["toutes_architectures"] if a["architecture"] == nom)


def test_surcharge_lcoe_solaire_agit_sur_le_solaire_seulement():
    bas = optimiser_architecture("Dakhla", surcharges={"lcoe_solaire": 0.020})
    haut = optimiser_architecture("Dakhla", surcharges={"lcoe_solaire": 0.050})
    assert lcoh(haut, "Solaire") > lcoh(bas, "Solaire")
    assert lcoh(haut, "Eolien") == pytest.approx(lcoh(bas, "Eolien"))


def test_surcharge_capex_augmente_le_lcoh():
    bas = optimiser_architecture("Dakhla", surcharges={"capex_mult": 1.0})
    haut = optimiser_architecture("Dakhla", surcharges={"capex_mult": 3.0})
    assert lcoh(haut, "Eolien") > lcoh(bas, "Eolien")


def test_surcharge_inconnue_renvoie_une_erreur():
    assert "erreur" in optimiser_architecture("Dakhla", surcharges={"fantaisie": 1})


def test_surcharge_ne_modifie_pas_les_donnees():
    avant = optimiser_architecture("Dakhla")
    optimiser_architecture("Dakhla", surcharges={"lcoe_solaire": 0.001})
    apres = optimiser_architecture("Dakhla")
    assert avant["best_overall"] == apres["best_overall"]


def test_analyse_parametre_structure():
    a = analyser_parametre("Dakhla", "lcoe_solaire", n_points=5)
    assert len(a["points"]) == 5
    assert a["gagnant_base"]["gagnant_compromis"] in {"Eolien", "Solaire", "Hybride"}


def test_parametre_inconnu():
    with pytest.raises(ValueError):
        analyser_parametre("Dakhla", "fantaisie")


def test_resume_textuel_non_vide():
    analyse = analyser_region("Dakhla", parametres=["lcoe_solaire"], n_points=3)
    lignes = resume_textuel(analyse)
    assert lignes and all(isinstance(l, str) for l in lignes)
    
def test_co2_eolien_est_un_parametre_analysable():
    a = analyser_parametre("Dakhla", "co2_eolien", n_points=3)
    assert len(a["points"]) == 3
    assert a["valeur_base"] > 0


def test_analyse_avec_un_autre_profil():
    a = analyser_parametre("Dakhla", "lcoe_solaire", n_points=3, profil="economique")
    assert a["gagnant_base"]["gagnant_compromis"] in {"Eolien", "Solaire", "Hybride"}    