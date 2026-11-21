import numpy as np
from src.meteo import telecharger_meteo, profil_solaire, profil_eolien, profil_hybride
from src.engine_horaire import simuler

N = 500
P_PARC = 50000
RATIOS = range(10, 151, 10)
rng = np.random.default_rng(0)

df = telecharger_meteo(23.68, -15.96, annee=2022)
cfs = {"Eolien": profil_eolien(df), "Solaire": profil_solaire(df), "Hybride": profil_hybride(df)}
base = {"Cout_Eau": 0.8, "Taux_Interet": 0.05,
        "Duree_Vie_Electrolyseur": 20, "Annee_Installation": 2026}

# Part de l'énergie hybride venant du solaire (pour calculer son LCOE)
e_sol = 0.5 * cfs["Solaire"].mean()
e_vent = 0.5 * cfs["Eolien"].mean()
w_sol = e_sol / (e_sol + e_vent)

res = {k: [] for k in cfs}
ratios_opt = {k: [] for k in cfs}

for _ in range(N):
    # Un "monde" : mêmes incertitudes pour toutes les architectures
    d = dict(base)
    d["Taux_Interet"] = rng.uniform(0.04, 0.09)
    capex_mult = rng.uniform(1.0, 2.5)
    lcoe_sol = 0.016 * rng.uniform(0.8, 1.3)
    lcoe_vent = 0.028 * rng.uniform(0.8, 1.3)
    lcoes = {"Eolien": lcoe_vent, "Solaire": lcoe_sol,
             "Hybride": w_sol * lcoe_sol + (1 - w_sol) * lcoe_vent}

    for nom, cf in cfs.items():
        meilleur = None
        for pct in RATIOS:
            r = simuler(cf, P_PARC, pct / 100, lcoes[nom], d, capex_mult)
            if r and (meilleur is None or r["lcoh"] < meilleur[0]):
                meilleur = (r["lcoh"], pct)
        res[nom].append(meilleur[0])
        ratios_opt[nom].append(meilleur[1])

noms = list(cfs)
M = np.array([res[n] for n in noms])          # (3, N)
gagnant = M.argmin(axis=0)

print(f"{'Archi':8} | {'P10':>5} | {'P50':>5} | {'P90':>5} | ratio med. | % de mondes où c'est le moins cher")
for i, n in enumerate(noms):
    p10, p50, p90 = np.percentile(M[i], [10, 50, 90])
    print(f"{n:8} | {p10:5.2f} | {p50:5.2f} | {p90:5.2f} | {np.median(ratios_opt[n]):7.0f}%   | {100*(gagnant==i).mean():5.1f}%")