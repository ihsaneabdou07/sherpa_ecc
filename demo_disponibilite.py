from src.engine import optimiser_architecture

for region in ("Dakhla", "Laayoune"):
    res = optimiser_architecture(region)
    print(f"\n=== {region} ===")
    for a in res["toutes_architectures"]:
        print(f"{a['architecture']:8} marche {a['disponibilite_pct']:5.1f} % | "
              f"plus longue interruption {a['interruption_max_h']:4d} h | "
              f"mois le plus faible {a['mois_creux_pct']:5.1f} % de la moyenne")