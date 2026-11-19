from pprint import pprint
from src.engine import optimiser_architecture
from src.ai_assistant import generer_explication

res = optimiser_architecture("Dakhla", n_mc=200)
pprint(res["best_overall"])
print()
print(generer_explication("Dakhla", res))