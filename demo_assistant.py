from src.ai_assistant import generer_explication
from src.comparaison import comparer_scenarios
from src.engine import optimiser_architecture

res = optimiser_architecture("Dakhla", n_mc=0)
comps = [comparer_scenarios("Dakhla"), comparer_scenarios("Laayoune")]

questions = [
    None,
    "Pourquoi l'éolien alors que l'hybride a le CAPEX par kg le plus bas ?",
    "Que change-t-il si je privilégie le coût plutôt que l'environnement ?",
    "Quelle différence entre Dakhla et Laayoune ?",
    "Quel est le prix du terrain à Dakhla ?",
]

for q in questions:
    print("\n--- Question :", q or "(explication par défaut)")
    print(generer_explication("Dakhla", res, question=q, comparaison=comps))