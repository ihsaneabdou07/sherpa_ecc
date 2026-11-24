import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error

from src.engine import calculer_lcoh


def generer_dataset(n=5000, seed=42):
    """Fait varier les paramètres au hasard et calcule le LCOH avec votre moteur."""
    rng = np.random.default_rng(seed)
    lignes = []
    for _ in range(n):
        donnees = {
            "Puissance_Parc_ENR_kW": rng.uniform(10_000, 100_000),
            "Cout_Eau": rng.uniform(0.3, 2.0),
            "Taux_Interet": rng.uniform(0.03, 0.10),
            "Duree_Vie_Electrolyseur": int(rng.integers(10, 31)),
            "Annee_Installation": int(rng.integers(2026, 2036)),
        }
        archi = {
            "LCOE": rng.uniform(0.01, 0.05),
            "Facteur_Charge": rng.uniform(0.2, 0.7),
        }
        ratio = rng.uniform(0.05, 1.0)

        lcoh, _, _ = calculer_lcoh(ratio, donnees, archi)

        lignes.append({
            **donnees,
            **archi,
            "ratio": ratio,
            "lcoh": lcoh,
        })
    return pd.DataFrame(lignes)


if __name__ == "__main__":
    df = generer_dataset()
    print(df.describe().round(3))

    X = df.drop(columns="lcoh")
    y = df["lcoh"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=0
    )

    modele = GradientBoostingRegressor(n_estimators=300, max_depth=4, random_state=0)
    modele.fit(X_train, y_train)

    pred = modele.predict(X_test)
    print("\n=== PERFORMANCE ===")
    print("R2  :", round(r2_score(y_test, pred), 4))
    print("MAE :", round(mean_absolute_error(y_test, pred), 4), "€/kg")

    print("\n=== PARAMÈTRES LES PLUS INFLUENTS ===")
    importances = pd.Series(modele.feature_importances_, index=X.columns)
    print(importances.sort_values(ascending=False).round(3))

    joblib.dump(modele, "data/modele_lcoh.joblib")
    print("\nModèle sauvegardé dans data/modele_lcoh.joblib")