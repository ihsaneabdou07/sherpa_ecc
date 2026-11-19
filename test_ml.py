import time
import joblib
import pandas as pd
from src.engine import calculer_lcoh

modele = joblib.load("data/modele_lcoh.joblib")

donnees = {"Puissance_Parc_ENR_kW": 50000, "Cout_Eau": 0.8, "Taux_Interet": 0.05,
           "Duree_Vie_Electrolyseur": 20, "Annee_Installation": 2026}
archi = {"LCOE": 0.026, "Facteur_Charge": 0.62}

exact, _, _ = calculer_lcoh(0.45, donnees, archi)

X = pd.DataFrame([{**donnees, **archi, "ratio": 0.45}])
pred = modele.predict(X)[0]

print(f"Moteur : {exact:.3f} €/kg | ML : {pred:.3f} €/kg | écart : {abs(exact - pred):.3f}")