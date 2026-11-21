import json
import os

from dotenv import load_dotenv

load_dotenv(override=True)  # override pour forcer la lecture du .env même si la variable d'environnement existe

MODELES = [m.strip() for m in os.getenv("GEMINI_MODELS","gemini-3.5-flash-lite,gemini-3.5-flash,gemini-3.7-flash,gemini-3.8-flash").split(",") if m.strip()]

SYSTEM_PROMPT = """Tu es un ingénieur conseil spécialisé en hydrogène vert, intégré à la plateforme SHERPA.
Règles strictes :
- Utilise UNIQUEMENT les chiffres fournis dans les résultats. N'invente aucune valeur.
- Si une information n'est pas dans les résultats, dis-le clairement.
- Les résultats viennent d'un modèle simplifié avec des hypothèses (LCOE, CAPEX, intensité carbone,
  une seule année météo). Rappelle-le brièvement quand tu donnes une recommandation.
- Unités : LCOH en €/kg, CO2 en kg CO2/kg H2, puissance en kW.
- Si le champ proba_moins_cher_pct existe, utilise-le pour parler de robustesse.
- Ne cite jamais les noms de champs techniques (best_overall, proba_moins_cher_pct, lowest_cost...) :
  parle de « meilleur compromis », « option la moins chère », « option la moins émettrice ».
- Ne mentionne pas les informations absentes sauf si l'utilisateur les demande.
- Ne commence pas par te présenter. Va directement à la réponse.
- puissance_kw est la puissance de l'électrolyseur (pas du parc renouvelable) : écris « électrolyseur de X kW ».
- Ne cite pas la valeur du champ score : dis simplement que c'est le meilleur compromis coût/CO2.
- Ne compare pas les puissances entre architectures, sauf si l'utilisateur le demande. Ne confonds jamais la puissance de l'électrolyseur avec celle du parc renouvelable.
- Ne compare pas les puissances entre architectures, sauf si l'utilisateur le demande. Ne confonds jamais la puissance de l'électrolyseur avec celle du parc renouvelable.
- N'explique pas les causes physiques ou techniques qui ne figurent pas dans les résultats fournis.
- Réponds en français, de façon claire et concise (maximum 150 mots), sans jargon inutile."""


def _resume_resultats(resultats):
    """Garde l'essentiel pour limiter la taille du prompt."""
    return {
        "best_overall": resultats["best_overall"]["architecture"],
        "lowest_cost": resultats["lowest_cost"]["architecture"],
        "lowest_co2": resultats["lowest_co2"]["architecture"],
        "architectures": resultats["toutes_architectures"],
    }


def construire_prompt(region, resultats, question=None):
    donnees = json.dumps(_resume_resultats(resultats), ensure_ascii=False,
                         indent=1, default=float)
    q = question or ("Explique pourquoi l'architecture 'best_overall' est recommandée, "
                     "en citant les chiffres.")
    return f"Région : {region}\nRésultats du calcul :\n{donnees}\n\nQuestion : {q}"


def generer_explication_simulee(region, resultats):
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
    return txt


def generer_explication(region, resultats, question=None, historique=None):
    """
    Point d'entrée pour le frontend.
    Essaie chaque modèle de MODELES dans l'ordre ; si tous échouent,
    retombe sur la version simulée.
    """
    if "erreur" in resultats:
        return resultats["erreur"]

    cle = os.getenv("GEMINI_API_KEY")
    if not cle:
        return generer_explication_simulee(region, resultats)

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return generer_explication_simulee(region, resultats)

    contenu = []
    for m in (historique or []):
        role = "model" if m["role"] == "assistant" else "user"
        contenu.append(types.Content(role=role, parts=[types.Part(text=m["content"])]))
    contenu.append(types.Content(
        role="user",
        parts=[types.Part(text=construire_prompt(region, resultats, question))]))

    client = genai.Client(api_key=cle,
                          http_options=types.HttpOptions(timeout=25000))

    for modele in MODELES:
        try:
            reponse = client.models.generate_content(
                model=modele,
                contents=contenu,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    max_output_tokens=2000,
                ),
            )
            if reponse.text:
                return reponse.text
        except Exception as err:
            print(f"[assistant] {modele} indisponible ({type(err).__name__}), essai suivant.")

    print("[assistant] Aucun modèle disponible, mode simulé.")
    return generer_explication_simulee(region, resultats)