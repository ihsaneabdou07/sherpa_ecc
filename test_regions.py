from src.engine import optimiser_architecture

for region in ["Dakhla", "Laayoune"]:
    res = optimiser_architecture(region, n_mc=0)
    if "erreur" in res:
        print(f"{region:10} | ERREUR : {res['erreur']}")
        continue
    b = res["best_overall"]
    print(f"{region:10} | {b['architecture']:8} | LCOH {b['lcoh_eur_kg']:.2f} €/kg "
          f"| ratio {b['ratio_pct']}% | CO2 {b['co2_kg_par_kg']:.2f}")