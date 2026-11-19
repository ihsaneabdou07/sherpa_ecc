from pprint import pprint
from src.engine import optimiser_architecture
from src.ai_assistant import generer_explication

resultats = optimiser_architecture("Dakhla")

print("=== RÉSULTATS ===")
pprint(resultats)

print("\n=== EXPLICATION IA ===")
print(generer_explication("Dakhla", resultats))