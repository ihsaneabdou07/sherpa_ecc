def generer_explication(region, resultats):
    if "erreur" in resultats:
        return resultats["erreur"]

    b = resultats["best_overall"]
    c = resultats["lowest_cost"]
    e = resultats["lowest_co2"]

    txt = (
        f"Pour {region}, l'architecture recommandée est {b['architecture']} : "
        f"LCOH de {b['lcoh_eur_kg']:.2f} €/kg, {b['co2_kg_par_kg']:.2f} kg CO2/kg H2, "
        f"avec un électrolyseur à {b['ratio_pct']} % de la puissance du parc "
        f"({b['puissance_kw']} kW). "
    )
    if "lcoh_p50" in b:
        txt += (
            f"Sur les simulations d'incertitude, son LCOH se situe entre "
            f"{b['lcoh_p10']:.2f} et {b['lcoh_p90']:.2f} €/kg (médiane {b['lcoh_p50']:.2f}), "
            f"et elle est la moins chère dans {b['proba_moins_cher_pct']:.0f} % des scénarios. "
        )
    if c["architecture"] == b["architecture"]:
        txt += "C'est aussi l'option la moins chère. "
    else:
        txt += f"L'option la moins chère est {c['architecture']} ({c['lcoh_eur_kg']:.2f} €/kg). "
    if e["architecture"] == b["architecture"]:
        txt += "C'est aussi la moins émettrice."
    else:
        txt += (f"La moins émettrice est {e['architecture']} "
                f"({e['co2_kg_par_kg']:.2f} kg CO2/kg H2, LCOH {e['lcoh_eur_kg']:.2f} €/kg).")
    return txt