from src.comparaison import comparer_regions, exporter_csv


def afficher(d):
    noms = list(d["scenarios"])
    print(f"\n=== {d['region']} ===")
    print(f"{'Critère':42}" + "".join(f"{n:>10}" for n in noms))
    for c in d["criteres"]:
        if c["cle"] not in d["scenarios"][noms[0]]["valeurs"]:
            continue
        ligne = f"{c['libelle']:42}" + "".join(
            f"{d['scenarios'][n]['valeurs'][c['cle']]:>10}" for n in noms)
        if not c["actif"]:
            ligne += "   (ignoré : identique pour tous)"
        print(ligne)

    print("\nClassement par profil :")
    for profil, lignes in d["classement"].items():
        print(f"  {profil:16}: " + "  >  ".join(f"{l['architecture']} ({l['score']})" for l in lignes))

    print("\nRobustesse face aux poids (% de jeux de poids gagnés) :", d["robustesse_poids_pct"])
    print("\nForces et faiblesses :")
    for nom, s in d["scenarios"].items():
        print(f"  {nom}")
        print(f"    meilleur sur : {', '.join(s['forces']) or '-'}")
        print(f"    moins bon sur : {', '.join(s['faiblesses']) or '-'}")
    print("\nRecommandation (profil équilibré) :", d["recommandation"])


res = comparer_regions(["Dakhla", "Laayoune"], n_mc=0)
for d in res["regions"].values():
    afficher(d)
    print("CSV :", exporter_csv(d))

print("\n=== SYNTHÈSE ===")
for l in res["synthese"]:
    print(f"{l['region']:9} | {l['profil']:16} | {l['scenario_recommande']:8} | "
          f"LCOH {l['lcoh_eur_kg']} | CO2 {l['co2_kg_par_kg']} | H2 {l['h2_tonnes_an']} t/an")