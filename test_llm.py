from src.engine import optimiser_architecture
from src.ai_assistant import generer_explication

res = optimiser_architecture("Dakhla", n_mc=0)

print("--- Explication par défaut ---")
print(generer_explication("Dakhla", res))

print("\n--- Question libre ---")
print(generer_explication("Dakhla", res,
      question="Pourquoi pas l'éolien seul, alors qu'il émet moins de CO2 ?"))

print("\n--- Question hors données ---")
print(generer_explication("Dakhla", res,
      question="Quel est le prix du terrain à Dakhla ?"))