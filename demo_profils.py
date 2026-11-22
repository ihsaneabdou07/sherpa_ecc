from src.sensibilite import analyser_region, resume_textuel

PROFILS = ["equilibre", "economique", "environnemental", "technique"]

for region in ["Dakhla", "Laayoune"]:
    for profil in PROFILS:
        analyse = analyser_region(region, profil=profil)
        print(f"\n=== {region} | profil {profil} ===")
        for ligne in resume_textuel(analyse):
            if "recommandé" in ligne:   # le scénario le moins cher ne dépend pas du profil
                print("-", ligne)