from src.engine import charger_donnees
from src.meteo import telecharger_meteo, profil_eolien
from src.optimiseur import _meilleur_ratio, CAPEX_MULT_NOMINAL
from src.parametres import PARAMS

PARAMS["courbe_rendement"] = "hofrichter"
region = "Dakhla"

d = charger_donnees(region)
df = telecharger_meteo(d["Latitude"], d["Longitude"], annee=2022, nom=region.lower())
p_parc = d["Puissance_Parc_ENR_kW"]
lcoe = d["Architectures"]["Eolien"]["LCOE"]

print("=== 1. Hauteur de mât ===")
for h in (100, 150, 200):
    PARAMS["eolien_hauteur"] = h
    print(f"mât {h} m -> facteur de charge {profil_eolien(df).mean():.3f}")
PARAMS["eolien_hauteur"] = 100   # retour à la valeur d'origine

print("\n=== 2. Facteur de charge imposé (éolien, Dakhla) ===")
cf = profil_eolien(df)
for cible in (None, 0.50, 0.60, 0.74):
    cf_t = cf if cible is None else (cf * cible / cf.mean()).clip(upper=1.0)
    for mult in (CAPEX_MULT_NOMINAL, 1.0):
        m = _meilleur_ratio(cf_t, p_parc, lcoe, d, mult)
        print(f"FC {cf_t.mean():.3f} | CAPEX x{mult} -> ratio {m['ratio_pct']}% | LCOH {m['lcoh']:.2f} €/kg")