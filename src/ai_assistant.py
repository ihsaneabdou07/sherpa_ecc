import json
import os

from dotenv import load_dotenv

load_dotenv(override=True)  # le .env du projet prime sur une éventuelle variable système

MODELES = [m.strip() for m in os.getenv(
    "GEMINI_MODELS",
    "gemini-3.5-flash-lite,gemini-3.5-flash,gemini-3.7-flash,gemini-3.8-flash"
).split(",") if m.strip()]

SYSTEM_PROMPT = """Tu es un ingénieur conseil spécialisé en hydrogène vert, intégré à la plateforme SHERPA.
Règles strictes :
- Utilise UNIQUEMENT les chiffres fournis. N'invente aucune valeur.
- Si une information n'est pas dans les données, dis-le clairement.
- Les résultats viennent d'un modèle simplifié avec des hypothèses (LCOE, CAPEX, intensité carbone,
  une seule année météo). Rappelle-le brièvement quand tu donnes une recommandation.
- Unités : LCOH en €/kg, CO2 en kg CO2/kg H2, puissance en kW.
- Ne cite jamais les noms de champs techniques : parle de « meilleur compromis »,
  « option la moins chère », « option la moins émettrice », « CAPEX par kg d'hydrogène produit ».
- Ne mentionne pas les informations absentes sauf si l'utilisateur les demande.
- Ne commence pas par te présenter. Va directement à la réponse.
- puissance_kw est la puissance de l'électrolyseur (pas du parc renouvelable).
- Ne cite pas les scores bruts comme des valeurs absolues.
Quand une comparaison multicritère est fournie :
- Indique le scénario recommandé et la part des pondérations testées pour lesquelles il l'emporte.
- Précise si le gagnant change selon le profil de priorités (économique, environnemental, technique).
- Explique les points forts et faibles des scénarios avec leurs valeurs chiffrées.
- Rappelle que les poids des profils sont des hypothèses et que les scores sont relatifs
  aux trois scénarios comparés, pas des notes absolues.
- Pour comparer deux régions, utilise les données de chaque région fournie.
- Le pourcentage de tirages aléatoires de poids gagnés ne dépend d'aucun profil : ne l'associe jamais
  à un profil précis. Pour un profil donné, utilise uniquement le gagnant de ce profil.
- Pour tout pourcentage d'écart, utilise uniquement les champs ecart_relatif_au_meilleur_scenario_pct
  et ecarts_entre_regions. Ne calcule jamais un écart toi-même.
- N'emploie « quasi équivalent » que pour les critères listés dans criteres_quasi_equivalents_au_meilleur.
  Pour tout autre écart, donne le pourcentage fourni sans parler d'équivalence.
- Ne répète le rappel des hypothèses qu'une seule fois, en une phrase courte.
- Respecte strictement la limite de 200 mots.
- Le CO2 total est la somme du CO2 de l'électricité et de la fabrication du stack de l'électrolyseur.
  Il exclut les équipements annexes, le parc renouvelable, l'eau et le transport : précise-le en une
  phrase quand tu donnes un chiffre de CO2. Pour la part de fabrication, utilise
  part_fabrication_dans_le_co2_pct sans la recalculer.
- La continuité de production se lit avec la plus longue interruption (en heures), le mois le plus faible
  (en % de la moyenne mensuelle, un « mois » étant un bloc de 730 h) et la disponibilité (% d'heures de marche).
  Ce sont des indicateurs de continuité de production, pas de fiabilité des équipements : n'emploie jamais
  le mot « fiabilité » pour eux. Le solaire s'arrête chaque nuit : ne présente pas sa faible disponibilité
  comme un défaut.
  - Pour la plus longue interruption et le mois le plus faible, cite les valeurs absolues
  (heures, % de la moyenne), jamais un pourcentage d'écart.
- Les critères d'une même famille pèsent autant les uns que les autres. Pour expliquer le poids
  d'un critère dans le classement, utilise criteres_actifs et poids_des_profils.
- Écris les nombres à la française, avec une virgule décimale.
- Réponds en français, de façon claire et concise (maximum 200 mots), sans jargon inutile."""


def _resume_resultats(resultats):
    """Garde l'essentiel pour limiter la taille du prompt."""
    return {
        "best_overall": resultats["best_overall"]["architecture"],
        "lowest_cost": resultats["lowest_cost"]["architecture"],
        "lowest_co2": resultats["lowest_co2"]["architecture"],
        "architectures": resultats["toutes_architectures"],
    }


def _ecarts_relatifs(scenarios):
    """Pour chaque critère, écart relatif (%) de chaque scénario au meilleur scénario."""
    from src.comparaison import CRITERES
    sortie = {nom: {} for nom in scenarios}
    for cle, _, _, sens in CRITERES:
        if cle in ("interruption_max_h", "mois_creux_pct"):
            continue
        vals = {n: s["valeurs"].get(cle) for n, s in scenarios.items()}
        if any(v is None for v in vals.values()):
            continue
        ref = min(vals.values()) if sens == "min" else max(vals.values())
        if ref == 0:
            continue
        for n, v in vals.items():
            sortie[n][cle] = round(100 * abs(v - ref) / abs(ref), 1)
    return sortie


def _ecarts_entre_regions(comparaison):
    """Écart relatif (%) de chaque scénario entre régions, par rapport à la première région."""
    comps = comparaison if isinstance(comparaison, list) else [comparaison]
    comps = [c for c in comps if c and "erreur" not in c]
    if len(comps) < 2:
        return None
    ref = comps[0]
    sortie = {}
    for c in comps[1:]:
        par_scenario = {}
        for nom, s in c["scenarios"].items():
            par_scenario[nom] = {}
            for cle in ("lcoh_eur_kg", "co2_kg_par_kg", "capex_par_kg_h2_an", "h2_tonnes_an"):
                a = ref["scenarios"][nom]["valeurs"].get(cle)
                b = s["valeurs"].get(cle)
                if a and b is not None:
                    par_scenario[nom][cle] = {
                        ref["region"]: a, c["region"]: b,
                        "ecart_pct": round(100 * (b - a) / a, 1),
                    }
        sortie[f"{c['region']}_par_rapport_a_{ref['region']}"] = par_scenario
    return sortie

def _part_fabrication(valeurs):
    """Part (%) de la fabrication du stack dans le CO2 total, précalculée pour le modèle."""
    total, fab = valeurs.get("co2_kg_par_kg"), valeurs.get("co2_fabrication_kg_par_kg")
    if not total or fab is None:
        return None
    return round(100 * fab / total, 1)


def _resume_comparaison(comparaison):
    """Accepte la comparaison d'une région (dict) ou de plusieurs (liste)."""
    from src.comparaison import CRITERES
    libelles = {c[0]: c[1] for c in CRITERES}
    comps = comparaison if isinstance(comparaison, list) else [comparaison]
    sortie = []
    for c in comps:
        if not c or "erreur" in c:
            continue
        ecarts = _ecarts_relatifs(c["scenarios"])
        sortie.append({
            "region": c["region"],
            "scenario_recommande_profil_equilibre": c["recommandation"],
            "gagnant_par_profil": c["gagnant_par_profil"],
            "part_des_tirages_aleatoires_de_poids_gagnes_pct": c["robustesse_poids_pct"],
            "poids_des_profils": c["profils"],
            "criteres_actifs": [{"critere": k["libelle"], "famille": k["categorie"]}
                                for k in c["criteres"] if k["actif"]],
            "classement": {
                p: [{"scenario": l["architecture"], "score": l["score"]} for l in lignes]
                for p, lignes in c["classement"].items()
            },
            "scenarios": {
                nom: {"valeurs": s["valeurs"],
                      "part_fabrication_dans_le_co2_pct": _part_fabrication(s["valeurs"]),
                        "criteres_quasi_equivalents_au_meilleur": [
                          libelles[k] for k, e in ecarts[nom].items()
                          if k in libelles and 0 < e < 2],
                      "ecart_relatif_au_meilleur_scenario_pct": ecarts[nom],
                      "points_forts": s["forces"],
                      "points_faibles": s["faiblesses"]}
                for nom, s in c["scenarios"].items()
            },
        })
    return sortie


def construire_prompt(region, resultats, question=None, comparaison=None):
    contenu = {"resultats_optimisation": _resume_resultats(resultats)}
    comp = _resume_comparaison(comparaison) if comparaison else []
    if comp:
        contenu["comparaison_multicritere"] = comp
        ecarts_regions = _ecarts_entre_regions(comparaison)
        if ecarts_regions:
            contenu["ecarts_entre_regions"] = ecarts_regions
    donnees = json.dumps(contenu, ensure_ascii=False, indent=1, default=float)

    if question:
        q = question
    elif comp:
        q = ("Explique le scénario recommandé et dis si la recommandation change "
             "selon les priorités, en citant les chiffres.")
    else:
        q = "Explique pourquoi l'architecture 'best_overall' est recommandée, en citant les chiffres."
    return f"Région : {region}\nDonnées calculées :\n{donnees}\n\nQuestion : {q}"


def _texte_comparaison_simule(comparaison):
    morceaux = []
    comps = comparaison if isinstance(comparaison, list) else [comparaison]
    for c in comps:
        if not c or "erreur" in c:
            continue
        rec = c["recommandation"]
        part = c["robustesse_poids_pct"].get(rec, 0)
        t = (f"Comparaison multicritère à {c['region']} : le scénario recommandé (priorités "
             f"équilibrées) est {rec}, premier dans {part:.0f} % des pondérations testées. ")
        autres = [f"{p} : {n}" for p, n in c["gagnant_par_profil"].items() if n != rec]
        if autres:
            t += "Le gagnant change selon le profil (" + ", ".join(autres) + ")."
        else:
            t += "Il reste premier quel que soit le profil de priorités."
        morceaux.append(t)
    return " ".join(morceaux)


def generer_explication_simulee(region, resultats, comparaison=None):
    """Texte sans API (secours)."""
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
    if comparaison:
        suite = _texte_comparaison_simule(comparaison)
        if suite:
            txt += " " + suite
    return txt


def generer_explication(region, resultats, question=None, historique=None, comparaison=None):
    """
    Point d'entrée pour le frontend.
    - question     : texte libre de l'utilisateur (sinon explication par défaut)
    - historique   : liste [{"role": "user"/"assistant", "content": "..."}]
    - comparaison  : résultat de comparer_scenarios(region), ou liste de résultats pour
                     plusieurs régions (optionnel)
    Essaie chaque modèle de MODELES ; si tous échouent, retombe sur la version simulée.
    """
    if "erreur" in resultats:
        return resultats["erreur"]

    cle = os.getenv("GEMINI_API_KEY")
    if not cle:
        return generer_explication_simulee(region, resultats, comparaison)

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return generer_explication_simulee(region, resultats, comparaison)

    contenu = []
    for m in (historique or []):
        role = "model" if m["role"] == "assistant" else "user"
        contenu.append(types.Content(role=role, parts=[types.Part(text=m["content"])]))
    contenu.append(types.Content(
        role="user",
        parts=[types.Part(text=construire_prompt(region, resultats, question, comparaison))]))

    client = genai.Client(api_key=cle, http_options=types.HttpOptions(timeout=40000))

    for modele in MODELES:
        try:
            reponse = client.models.generate_content(
                model=modele,
                contents=contenu,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    max_output_tokens=6000,
                ),
            )
            if reponse.text:
                return reponse.text
        except Exception as err:
            print(f"[assistant] {modele} indisponible ({type(err).__name__}: {str(err)[:150]}), essai suivant.")

    print("[assistant] Aucun modèle disponible, mode simulé.")
    return generer_explication_simulee(region, resultats, comparaison)