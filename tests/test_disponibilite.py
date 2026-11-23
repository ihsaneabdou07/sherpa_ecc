import numpy as np

from src.engine import optimiser_architecture
from src.engine_horaire import _plus_longue_serie


def test_plus_longue_serie():
    assert _plus_longue_serie(np.array([0, 1, 1, 0, 1, 1, 1, 0], dtype=bool)) == 3
    assert _plus_longue_serie(np.zeros(5, dtype=bool)) == 0
    assert _plus_longue_serie(np.ones(4, dtype=bool)) == 4


def test_indicateurs_de_disponibilite_coherents():
    res = optimiser_architecture("Dakhla")
    for a in res["toutes_architectures"]:
        assert 0 < a["disponibilite_pct"] <= 100
        assert 0 <= a["interruption_max_h"] <= 8760
        assert 0 <= a["mois_creux_pct"] <= 100