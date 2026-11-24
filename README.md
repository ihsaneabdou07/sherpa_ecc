# sherpa_ecc
Plateforme d'aide à la décision (Streamlit) pour la modélisation systémique de l'écosystème énergétique marocain.


lien de google drive :https://drive.google.com/drive/folders/1FgSpWPrO_3rSd5RCCPQ0J-WjCtKqzFwK?usp=drive_link


# H2-Maroc Decision Studio — Plateforme SHERPA ECC

Plateforme d'aide à la décision pour la modélisation techno-économique et environnementale de filières **hydrogène vert et dérivés Power-to-X** (*e-Methanol*, *Green hydrogen*, *e-Diesel*, *e-Methane*) à l'échelle des **12 régions administratives** et des **20 pôles industriels/villes** du Maroc.

---

## Architecture du projet

```text
sherpa_ecc/
├── app/                        # API Backend FastAPI
│   ├── main.py                 # Endpoints REST (/studio/recommend, /studio/chat, /locations...)
│   ├── schemas.py              # Modèles de validation Pydantic
│   └── engine/
│       └── simulator.py        # Simulateur paramétrique régional & calcul des axes décisionnels
├── src/                        # Moteur scientifique & optimisation
│   ├── engine.py               # Optimisation des architectures EnR-H2 et simulations Monte Carlo
│   ├── engine_horaire.py       # Simulation horaire & courbe de rendement Hofrichter
│   ├── comparaison.py          # Analyse multicritère et robustesse aux pondérations
│   └── ai_assistant.py         # Assistant ingénieur conseil (Gemini + mode secours déterministe)
├── frontend/                   # Interface web interactive (React + TypeScript + Vite)
│   └── src/
│       ├── App.tsx             # Studio principal responsive (Projet, Recommandations, Assistant)
│       ├── components/
│       │   ├── MoroccoMap.tsx  # Carte interactive GeoJSON des 12 régions du Maroc
│       │   └── ChartsPanel.tsx # Frontière de Pareto, Radar multicritère & Sensibilité FLH
│       ├── data/               # Données géographiques (morocco-12-regions.geo.json)
│       └── i18n/               # Traductions dynamiques Français / Anglais (FR | EN)
├── tests/                      # Suite de 65 tests unitaires et d'intégration (pytest)
├── pytest.ini                  # Configuration pytest (pythonpath = .)
└── requirements.txt            # Dépendances Python