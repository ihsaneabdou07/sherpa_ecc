import pytest

from src.engine import optimiser_architecture
from src.parametres import PARAMS


def test_co2_total_egale_somme_des_composantes():
    for a in optimiser_architecture("Dakhla")["toutes_architectures"]:
        total = a["co2_electricite_kg_par_kg"] + a["co2_fabrication_kg_par_kg"]
        assert a["co2_kg_par_kg"] == pytest.approx(total, abs=0.002)
        assert a["co2_fabrication_kg_par_kg"] > 0


def test_le_remplacement_du_stack_augmente_la_fabrication(monkeypatch):
    avec = optimiser_architecture("Dakhla")["best_overall"]["co2_fabrication_kg_par_kg"]
    monkeypatch.setitem(PARAMS, "remplacement_stack", 0)
    sans = optimiser_architecture("Dakhla")["best_overall"]["co2_fabrication_kg_par_kg"]
    assert avec >= sans