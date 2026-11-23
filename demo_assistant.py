from src.ai_assistant import generer_explication
from src.comparaison import comparer_scenarios
from src.engine import optimiser_architecture

res = optimiser_architecture("Dakhla", n_mc=0)
comps = [comparer_scenarios("Dakhla"), comparer_scenarios("Laayoune")]

questions = [
    None,
    "Quelle part du CO2 vient de la fabrication de l'électrolyseur ?",
    "Pourquoi l'éolien alors qu'il a la plus longue interruption de production ?",
    "À Laayoune, l'éolien est-il vraiment meilleur que l'hybride ?",
    "Quel est le prix du terrain à Dakhla ?",
]

for q in questions:
    print("\n--- Question :", q or "(explication par défaut)")
    print(generer_explication("Dakhla", res, question=q, comparaison=comps))