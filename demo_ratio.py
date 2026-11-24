from src.parametres import PARAMS
from src.optimiseur import optimiser_architecture_horaire

PARAMS["courbe_rendement"] = "hofrichter"

print("Éolien, Dakhla, courbe Hofrichter")
for capex_mult in (1.75, 1.0):
    for lcoe in (0.030, 0.040):
        res = optimiser_architecture_horaire(
            "Dakhla", surcharges={"capex_mult": capex_mult, "lcoe_eolien": lcoe})
        e = next(a for a in res["toutes_architectures"] if a["architecture"] == "Eolien")
        print(f"CAPEX x{capex_mult} | LCOE {lcoe:.3f} -> ratio {e['ratio_pct']}% | LCOH {e['lcoh_eur_kg']:.2f} €/kg")