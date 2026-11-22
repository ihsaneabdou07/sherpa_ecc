import numpy as np
import pytest

from src.engine_horaire import rendement_hofrichter


def test_rendement_pleine_charge():
    assert rendement_hofrichter(np.array([1.0]), 2020)[0] == pytest.approx(0.60077, abs=1e-4)


def test_rendement_demi_charge():
    assert rendement_hofrichter(np.array([0.5]), 2020)[0] == pytest.approx(0.67527, abs=1e-4)


def test_rendement_quasi_continu_a_15_pct():
    eta = rendement_hofrichter(np.array([0.1499, 0.1501]), 2020)
    assert abs(eta[0] - eta[1]) < 0.02