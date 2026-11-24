import numpy as np
import pandas as pd
import lightgbm as lgb
import shap
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error

from src.meteo import telecharger_meteo, profil_solaire, profil_eolien, profil_hybride
from src.engine_horaire import simuler

N = 4000
P_PARC = 50000
rng = np.random.default_rng(1)

df = telecharger_meteo(23.68, -15.96, annee=2022)
profils = {0: profil_eolien(df), 1: profil_solaire(df), 2: profil_hybride(df)}
base = {"Cout_Eau": 0.8, "Taux_Interet": 0.05,
        "Duree_Vie_Electrolyseur": 20, "Annee_Installation": 2026}

lignes = []
for _ in range(N):
    archi = int(rng.integers(0, 3))
    d = dict(base)
    d["Taux_Interet"] = rng.uniform(0.04, 0.09)
    d["Duree_Vie_Electrolyseur"] = int(rng.integers(15, 26))
    d["Cout_Eau"] = rng.uniform(0.3, 2.0)
    lcoe = rng.uniform(0.012, 0.035)
    capex_mult = rng.uniform(1.0, 2.5)
    ratio = rng.uniform(0.1, 1.5)

    r = simuler(profils[archi], P_PARC, ratio, lcoe, d, capex_mult)
    if r:
        lignes.append({
            "architecture": archi, "lcoe": lcoe, "capex_mult": capex_mult,
            "ratio": ratio, "taux_interet": d["Taux_Interet"],
            "duree_vie": d["Duree_Vie_Electrolyseur"], "cout_eau": d["Cout_Eau"],
            "lcoh": r["lcoh"],
        })

data = pd.DataFrame(lignes)
X, y = data.drop(columns="lcoh"), data["lcoh"]
X["architecture"] = X["architecture"].astype("category")
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=0)

modele = lgb.LGBMRegressor(n_estimators=500, learning_rate=0.05, num_leaves=31, verbose=-1)
modele.fit(Xtr, ytr)
pred = modele.predict(Xte)
print("R2  :", round(r2_score(yte, pred), 4))
print("MAE :", round(mean_absolute_error(yte, pred), 4), "€/kg")

explainer = shap.TreeExplainer(modele)
sv = explainer.shap_values(Xte)
shap.summary_plot(sv, Xte, show=False)
plt.tight_layout()
plt.savefig("shap_summary.png", dpi=200)
print("Graphique sauvegardé : shap_summary.png")

importance = pd.Series(np.abs(sv).mean(axis=0), index=X.columns).sort_values(ascending=False)
print("\nImportance SHAP moyenne (€/kg) :")
print(importance.round(3))