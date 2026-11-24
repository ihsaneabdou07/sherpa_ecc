export type Lang = "fr" | "en";

export const translations = {
  fr: {
    // En-tête & Projet
    yourProject: "Votre projet",
    targetRegion: "Région cible",
    targetProduct: "Produit cible",
    annualProduction: "Production annuelle",
    tonnesPerYear: "tonnes / an",
    findArchitectures: "Trouver les meilleures architectures",
    calculating: "Calcul en cours...",

    // Produits
    products: {
      "e-Methanol": "e-Méthanol",
      "Green hydrogen": "Hydrogène vert",
      "e-Diesel": "e-Diesel",
      "e-Methane": "e-Méthane",
    } as Record<string, string>,

    // Carte du Maroc
    regionsCount: "12 régions",
    regionsAccessible: "accessibles",
    hideList: "Masquer la liste",
    showList: "Liste des 12 régions",
    mapAriaLabel: "Carte géographique des 12 régions du Maroc",
    listAriaLabel: "Sélectionner une des 12 régions du Maroc",
    poleBadge: "Pôle",
    directProfile: "Profil direct",
    apiPolePrefix: "Pôle API",
    selectRegionPrompt: "Sélectionne une région sur la carte ou dans la liste.",

    // Cartes d'architectures
    recommendedTitle: "Architectures recommandées",
    focusLabel: "Focus",
    activeBadge: "Active",
    loadingArchitectures: "Chargement des architectures... (Vérifie que uvicorn tourne bien sur le port 8000)",
    apiRecommendError: "Connexion impossible à /studio/recommend (vérifie que uvicorn tourne sur http://127.0.0.1:8000).",
    productionCost: "Coût de production",
    co2Emissions: "Émissions CO2",
    waterUse: "Consommation d'eau",
    maturity: "Maturité",
    chainSolarWind: "Solaire + Éolien",
    chainDesalination: "Dessalement",
    chainElectrolyzer: "Électrolyseur + Synthèse",

    // Graphiques
    paretoTitle: "Frontière de Pareto (Coût vs CO2)",
    costAxis: "Coût",
    co2Axis: "CO2 (kg/u)",
    radarTitle: "Profil multicritère",
    axes: {
      cost_score: "Coût",
      co2_score: "CO2",
      water_score: "Eau",
      trl_score: "Maturité",
      efficiency_score: "Efficacité",
    },
    inspectCost: "Coût",
    inspectWater: "Eau",
    inspectScores: "Scores",
    inspectEff: "Eff.",
    inspectAltPoint: "Point alternatif",
    inspectHint: "Survole ou clique sur un point, une courbe radar ou la légende pour inspecter les valeurs exactes.",

    // Assistant IA
    aiAssistant: "Assistant IA",
    you: "Vous",
    assistantName: "Assistant SHERPA",
    assistantAnalyzing: "L'assistant SHERPA analyse les résultats...",
    chatError: "Impossible de contacter l'assistant SHERPA sur le backend (vérifie le serveur FastAPI sur le port 8000).",
    chatPlaceholderSelected: (rank: number, badge: string) => `Poser une question sur #${rank} ${badge}...`,
    chatPlaceholderDefault: "Poser une question sur les résultats...",
    defaultQuestion: (region: string) => `Pourquoi l'architecture 1 est-elle recommandée pour ${region} ?`,
    quickPrompts: [
      "Comparer les architectures #1 et #2 sur le coût et le CO2",
      "Quels sont les principaux compromis sur l'eau et la maturité (TRL) ?",
      "Quelle est la sensibilité de ce classement à la disponibilité renouvelable ?",
    ],

    sensitivityTitle: "Sensibilité du coût à la disponibilité EnR (FLH)",
    flhAxis: "Disponibilité EnR (h/an)",
  },

  en: {
    // Header & Project
    yourProject: "Your project",
    targetRegion: "Target region",
    targetProduct: "Target product",
    annualProduction: "Annual production",
    tonnesPerYear: "tonnes / year",
    findArchitectures: "Find best architectures",
    calculating: "Calculating...",

    // Products
    products: {
      "e-Methanol": "e-Methanol",
      "Green hydrogen": "Green hydrogen",
      "e-Diesel": "e-Diesel",
      "e-Methane": "e-Methane",
    } as Record<string, string>,

    // Morocco Map
    regionsCount: "12 regions",
    regionsAccessible: "available",
    hideList: "Hide list",
    showList: "Show all 12 regions",
    mapAriaLabel: "Geographic map of the 12 regions of Morocco",
    listAriaLabel: "Select one of the 12 regions of Morocco",
    poleBadge: "Hub",
    directProfile: "Direct profile",
    apiPolePrefix: "API Hub",
    selectRegionPrompt: "Select a region on the map or from the list.",

    // Architecture Cards
    recommendedTitle: "Recommended architectures",
    focusLabel: "Focus",
    activeBadge: "Active",
    loadingArchitectures: "Loading architectures... (Make sure uvicorn is running on port 8000)",
    apiRecommendError: "Cannot connect to /studio/recommend (verify uvicorn is running on http://127.0.0.1:8000).",
    productionCost: "Production cost",
    co2Emissions: "CO2 emissions",
    waterUse: "Water use",
    maturity: "Maturity",
    chainSolarWind: "Solar + Wind",
    chainDesalination: "Desalination",
    chainElectrolyzer: "Electrolyzer + Synthesis",

    // Charts
    paretoTitle: "Pareto frontier (Cost vs CO2)",
    costAxis: "Cost",
    co2Axis: "CO2 (kg/u)",
    radarTitle: "Multi-criteria profile",
    axes: {
      cost_score: "Cost",
      co2_score: "CO2",
      water_score: "Water",
      trl_score: "Maturity",
      efficiency_score: "Efficiency",
    },
    inspectCost: "Cost",
    inspectWater: "Water",
    inspectScores: "Scores",
    inspectEff: "Eff.",
    inspectAltPoint: "Alternative point",
    inspectHint: "Hover or click on a point, radar polygon, or legend item to inspect exact values.",

    // AI Assistant
    aiAssistant: "AI assistant",
    you: "You",
    assistantName: "SHERPA Assistant",
    assistantAnalyzing: "SHERPA Assistant is analyzing the results...",
    chatError: "Unable to reach SHERPA assistant on the backend (verify FastAPI server on port 8000).",
    chatPlaceholderSelected: (rank: number, badge: string) => `Ask about #${rank} ${badge}...`,
    chatPlaceholderDefault: "Ask a question about the results...",
    defaultQuestion: (region: string) => `Why is architecture 1 recommended for ${region}?`,
    quickPrompts: [
      "Compare architecture #1 and #2 on cost vs CO2",
      "What are the main trade-offs on water and maturity (TRL)?",
      "How sensitive is this ranking to renewable availability?",
    ],

    sensitivityTitle: "Cost sensitivity to RES availability (FLH)",
    flhAxis: "RES availability (h/yr)",
  },
} as const;