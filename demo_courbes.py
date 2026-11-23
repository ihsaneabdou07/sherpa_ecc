from src.parametres import PARAMS
from src.optimiseur import optimiser_architecture_horaire

for courbe in ("quadratique", "hofrichter"):
    PARAMS["courbe_rendement"] = courbe
    for region in ("Dakhla", "Laayoune"):
        res = optimiser_architecture_horaire(region)
        print(f"\n{courbe} | {region} | recommandé : {res['best_overall']['architecture']}")
        for a in res["toutes_architectures"]:
            print(f"  {a['architecture']:8} LCOH {a['lcoh_eur_kg']:.2f} | ratio {a['ratio_pct']}% "
                  f"| CO2 {a['co2_kg_par_kg']:.2f} | H2 {a['h2_tonnes_an']} t")