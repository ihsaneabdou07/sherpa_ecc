from src.sensibilite import analyser_region, exporter_csv, resume_textuel

for region in ["Dakhla", "Laayoune"]:
    analyse = analyser_region(region)
    print(f"\n=== {region} (profil {analyse['profil']}) ===")
    for ligne in resume_textuel(analyse):
        print("-", ligne)
    print("CSV :", exporter_csv(analyse))