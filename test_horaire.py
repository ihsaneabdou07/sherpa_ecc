from src.meteo import telecharger_meteo, profil_solaire, profil_eolien, profil_hybride
from src.engine_horaire import optimiser_ratio

# Dakhla : lat 23.68, lon -15.96
df = telecharger_meteo(23.68, -15.96, annee=2022)
print("Heures chargées :", len(df))

donnees = {"Cout_Eau": 0.8, "Taux_Interet": 0.05,
           "Duree_Vie_Electrolyseur": 20, "Annee_Installation": 2026}
P_PARC = 50000

archis = {
    "Eolien":  (profil_eolien(df),  0.028),
    "Solaire": (profil_solaire(df), 0.016),
    "Hybride": (profil_hybride(df), 0.026),
}

for nom, (cf, lcoe) in archis.items():
    r = optimiser_ratio(cf, P_PARC, lcoe, donnees)
    print(f"{nom:8} | facteur de charge parc {cf.mean():.2f} | ratio opt. {r['ratio_pct']}% "
          f"| LCOH {r['lcoh']:.2f} €/kg | énergie perdue {r['energie_perdue_pct']:.1f}%")