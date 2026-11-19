def construire_prompt(region, resultats):
    """Prompt qui sera envoyé à l'API (OpenAI, etc.) plus tard."""
    return f"""Tu es un ingénieur spécialisé en hydrogène vert.
Région : {region}
Résultats du calcul : {resultats}
Explique à l'utilisateur pourquoi l'architecture 'best_overall' est recommandée,
en citant les chiffres (LCOH en €/kg, CO2 en kg/kg H2)."""


def generer_explication(region, resultats):
    """Version simulée : génère un texte à partir des chiffres."""
    if "erreur" in resultats:
        return resultats["erreur"]

    b = resultats["best_overall"]
    c = resultats["lowest_cost"]
    e = resultats["lowest_co2"]

    return (
        f"Pour {region}, l'architecture recommandée est {b['architecture']} : "
        f"LCOH de {b['lcoh_eur_kg']} €/kg, {b['co2_kg_par_kg']} kg CO2/kg H2, "
        f"avec un électrolyseur à {b['ratio_pct']} % de la puissance du parc "
        f"({b['puissance_kw']} kW). C'est le meilleur compromis coût/CO2. "
        f"L'option la moins chère est {c['architecture']} ({c['lcoh_eur_kg']} €/kg), "
        f"et la moins émettrice est {e['architecture']} ({e['co2_kg_par_kg']} kg CO2/kg H2)."
    )