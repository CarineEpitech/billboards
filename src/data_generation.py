"""
==============================================================================
MODULE : data_generation.py
==============================================================================

RÔLE : Générer un dataset synthétique réaliste de panneaux publicitaires
       à Cotonou (Bénin), avec bruit contrôlé et corrélations partielles.

POURQUOI des données simulées ?
  - Aucun dataset open-source n'existe pour Cotonou
  - Permet de contrôler exactement la structure attendue
  - Reproductible via seed fixe
  - Le bruit injecté évite un modèle "trop parfait" (overfitting trivial)

PHILOSOPHIE DU BRUIT :
  Le vrai monde est bruité. Si le score de visibilité est 100% corrélé
  au trafic, le modèle apprendra une règle triviale et sera inutile en
  production. On injecte donc :
  - Du bruit gaussien sur les variables numériques
  - Des outliers réalistes (coordonnées GPS imprécises, données manquantes)
  - Des "surprises" : un panneau en zone rurale avec bon score (carrefour
    stratégique non capturé par le trafic seul)

DÉCISION TECHNIQUE :
  On aurait pu utiliser scikit-learn make_regression(), mais il génère
  des données abstraites. Ici on préfère modéliser la sémantique métier
  (Cotonou, quartiers réels, types de routes) pour un prototype crédible.

==============================================================================
"""

import numpy as np
import pandas as pd
import yaml
from pathlib import Path

# ---------------------------------------------------------------------------
# CONSTANTES MÉTIER — Connaissance du terrain à Cotonou
# ---------------------------------------------------------------------------

# Quartiers réels de Cotonou avec caractéristiques économiques approximatives
# Format : (nom, latitude_centre, longitude_centre, densite_economique [0-1])
QUARTIERS = [
    ("Akpakpa",       6.360, 2.410, 0.85),  # Zone commerciale dense
    ("Cadjehoun",     6.375, 2.378, 0.75),  # Résidentiel + commerces
    ("Gbégamey",      6.367, 2.357, 0.65),  # Mixte
    ("Haie Vive",     6.380, 2.395, 0.80),  # Haut standing, ambassades
    ("Mènontin",      6.373, 2.362, 0.60),  # Résidentiel
    ("Fidjrossè",     6.355, 2.360, 0.55),  # Mixte, bord de mer
    ("Dantokpa",      6.357, 2.420, 0.95),  # Grand marché, très dense
    ("Cotonou Centre",6.370, 2.390, 0.90),  # Centre-ville
    ("Agla",          6.382, 2.370, 0.50),  # Résidentiel calme
    ("Zongo",         6.362, 2.400, 0.70),  # Quartier populaire actif
]

# Types de panneaux avec caractéristiques de base
PANEL_TYPES = {
    "digital":   {"base_score": 70, "cost_factor": 2.5, "maintenance_freq": 0.8},
    "statique":  {"base_score": 45, "cost_factor": 1.0, "maintenance_freq": 0.3},
    "bache":     {"base_score": 30, "cost_factor": 0.6, "maintenance_freq": 0.1},
    "led_small": {"base_score": 55, "cost_factor": 1.5, "maintenance_freq": 0.6},
}

# Types de routes avec facteur de trafic
ROAD_TYPES = {
    "boulevard":    {"traffic_base": 8000, "visibility_bonus": 15},
    "avenue":       {"traffic_base": 5000, "visibility_bonus": 8},
    "rue_principale": {"traffic_base": 3000, "visibility_bonus": 3},
    "rue_secondaire": {"traffic_base": 1200, "visibility_bonus": -5},
}

# Propriétaires actifs sur le marché béninois (fictifs mais crédibles)
PROPRIETAIRES = [
    "Affichage Pro Bénin", "MediaOut SARL", "Côte d'Ivoire Affichage",
    "BéninMedia", "Atlantic Billboard", "WAfrica Displays",
    "Propriétaire Privé Inconnu", "Mairie de Cotonou"
]


# ---------------------------------------------------------------------------
# FONCTIONS DE GÉNÉRATION
# ---------------------------------------------------------------------------

def _compute_base_visibility(
    panel_type: str,
    road_type: str,
    height_m: float,
    size_m2: float,
    traffic_flow: float,
    quartier_density: float,
    distance_road: float,
    competition: int,
    rng: np.random.Generator
) -> float:
    """
    Calcule un score de visibilité "semi-déterministe".

    LOGIQUE MÉTIER :
      Le score n'est PAS une simple somme linéaire — en réalité la visibilité
      dépend d'interactions non-linéaires (ex: un panneau digital a plus
      d'impact la nuit, un grand panneau est moins efficace si trop près
      d'un concurrent, etc.).

    On modélise donc :
      score = base_type
            + bonus_route
            + effet_taille (log pour limiter les gains marginaux)
            + effet_hauteur (optimal vers 5-8m, au-delà moins visible)
            + effet_trafic (sqrt pour saturation)
            + effet_densité
            - malus_distance
            - malus_concurrence
            + bruit gaussien

    BRUIT CONTRÔLÉ :
      noise_level ~ N(0, 8) simule les facteurs non capturés :
      angle d'exposition au soleil, obstructions locales, événements
      saisonniers, visibilité depuis feux rouges, etc.
    """
    panel_base   = PANEL_TYPES[panel_type]["base_score"]
    road_bonus   = ROAD_TYPES[road_type]["visibility_bonus"]

    # Effet taille : log pour éviter qu'un immense panneau score 200
    # Un panneau de 4m² = log(4)=1.4, de 25m² = log(25)=3.2
    size_effect  = np.log1p(size_m2) * 4.5

    # Hauteur optimale entre 4m et 8m (gaussienne centrée sur 6m)
    height_effect = 10 * np.exp(-0.5 * ((height_m - 6) / 3) ** 2)

    # Trafic : sqrt pour effet de saturation (doublement du trafic ≠ doublement du score)
    traffic_effect = np.sqrt(traffic_flow / 500)

    # Densité économique du quartier
    density_effect = quartier_density * 12

    # Distance à la route principale : pénalité exponentielle
    # À 0m → 0 pénalité, à 50m → -8 pts, à 200m → -15 pts
    distance_penalty = 15 * (1 - np.exp(-distance_road / 80))

    # Concurrence : chaque panneau concurrent dans 500m fait perdre ~2 pts
    competition_penalty = competition * 2.5

    raw_score = (
        panel_base
        + road_bonus
        + size_effect
        + height_effect
        + traffic_effect
        + density_effect
        - distance_penalty
        - competition_penalty
    )

    # Bruit gaussien : sigma=8 pts sur 100 → variabilité réaliste
    # Représente tout ce qu'on ne capture pas avec nos features
    noise = rng.normal(0, 8)

    score = raw_score + noise

    # Clipping réaliste : un panneau réel a toujours une visibilité > 5
    return float(np.clip(score, 5, 98))


def generate_billboard_dataset(config: dict) -> pd.DataFrame:
    """
    Génère le dataset complet des panneaux publicitaires.

    PARAMÈTRES (depuis config.yaml) :
      - n_samples : nombre de panneaux à générer (45 par défaut)
      - random_seed : reproductibilité
      - noise_level : pourcentage de bruit additionnel sur features
      - missing_rate : taux de valeurs manquantes injectées

    RETOUR :
      DataFrame avec toutes les colonnes brutes (incluant erreurs intentionnelles
      pour tester le pipeline de cleaning).
    """
    cfg      = config["data_generation"]
    geo      = config["geography"]
    n        = cfg["n_samples"]
    seed     = cfg["random_seed"]
    noise    = cfg["noise_level"]
    miss_r   = cfg["missing_rate"]

    rng = np.random.default_rng(seed)

    records = []

    for i in range(n):
        # --- 1. Choix du quartier (distribution non-uniforme : Dantokpa et
        #        Centre sont surreprésentés car zones d'affichage privilégiées)
        quartier_weights = [0.08, 0.10, 0.08, 0.10, 0.07, 0.07, 0.15, 0.15, 0.08, 0.12]
        q_idx = rng.choice(len(QUARTIERS), p=quartier_weights)
        q_name, q_lat, q_lon, q_density = QUARTIERS[q_idx]

        # --- 2. Coordonnées GPS avec dispersion réaliste autour du centre quartier
        #    sigma=0.008° ≈ ~900m de rayon → cohérent avec taille des quartiers
        lat = float(np.clip(
            rng.normal(q_lat, 0.008),
            geo["lat_min"], geo["lat_max"]
        ))
        lon = float(np.clip(
            rng.normal(q_lon, 0.008),
            geo["lon_min"], geo["lon_max"]
        ))

        # --- 3. Type de panneau et route
        panel_type = rng.choice(list(PANEL_TYPES.keys()), p=[0.25, 0.45, 0.20, 0.10])
        road_type  = rng.choice(list(ROAD_TYPES.keys()),  p=[0.20, 0.30, 0.30, 0.20])

        # --- 4. Caractéristiques physiques du panneau
        # Hauteur : distribution bimodale (petits panneaux ~3m, grands ~7m)
        height_mode = rng.choice([3.0, 7.0], p=[0.4, 0.6])
        height_m = float(np.clip(rng.normal(height_mode, 1.5), 1.5, 15.0))

        # Taille en m² : log-normale pour éviter des valeurs négatives
        size_m2 = float(np.clip(rng.lognormal(mean=2.0, sigma=0.6), 1.5, 50.0))

        # --- 5. Variables de trafic et contexte
        road_base    = ROAD_TYPES[road_type]["traffic_base"]
        # Trafic avec bruit multiplicatif ±30%
        traffic_mult = rng.uniform(0.7, 1.3)
        traffic_flow = float(road_base * traffic_mult)

        distance_road = float(np.clip(rng.exponential(scale=25), 0, 200))
        competition   = int(rng.poisson(lam=1.5))  # Poisson car comptage discret

        # Exposition lumière du jour (heures/jour) : varie selon orientation
        daylight_hours = float(np.clip(rng.normal(9, 2.5), 4, 14))

        # Score piétons : corrélé à la densité quartier mais avec bruit
        ped_score = float(np.clip(
            q_density * 80 + rng.normal(0, 15),
            0, 100
        ))

        # Distance au centre-ville (Cotonou Centre : 6.370, 2.390)
        dist_center = float(np.sqrt(
            ((lat - 6.370) * 111) ** 2 +
            ((lon - 2.390) * 111 * np.cos(np.radians(lat))) ** 2
        ))

        # --- 6. Calcul du score de visibilité (variable cible)
        vis_score = _compute_base_visibility(
            panel_type, road_type, height_m, size_m2,
            traffic_flow, q_density, distance_road, competition, rng
        )

        # --- 7. Informations administratives
        proprietaire = rng.choice(PROPRIETAIRES)
        panel_id     = f"COT-{2024 + rng.integers(0, 2)}-{i+1:03d}"
        year_install = int(rng.integers(2015, 2025))

        # --- 8. Injection de bruit ADDITIONNEL sur les features numériques
        #    POURQUOI ? Simule les erreurs de mesure terrain (GPS imprécis,
        #    comptage trafic approximatif, etc.)
        if noise > 0:
            traffic_flow  *= rng.uniform(1 - noise, 1 + noise)
            ped_score      = float(np.clip(ped_score + rng.normal(0, noise * 20), 0, 100))

        record = {
            "panel_id":                   panel_id,
            "latitude":                   round(lat, 6),
            "longitude":                  round(lon, 6),
            "quartier":                   q_name,
            "panel_type":                 panel_type,
            "road_type":                  road_type,
            "height_m":                   round(height_m, 1),
            "size_m2":                    round(size_m2, 1),
            "traffic_flow_estim":         int(traffic_flow),
            "distance_to_main_road_m":    round(distance_road, 1),
            "distance_to_center_km":      round(dist_center, 3),
            "hours_of_daylight_exposure": round(daylight_hours, 1),
            "pedestrian_density_score":   round(ped_score, 1),
            "competition_radius_500m":    competition,
            "visibility_score":           round(vis_score, 1),
            "proprietaire":               proprietaire,
            "year_installed":             year_install,
            "has_photo":                  bool(rng.choice([True, False], p=[0.65, 0.35])),
        }
        records.append(record)

    df = pd.DataFrame(records)

    # --- 9. Injection de valeurs manquantes et anomalies intentionnelles
    #    POURQUOI ? Tester la robustesse du pipeline de cleaning.
    #    Dans un vrai projet, ces erreurs viennent de saisies manuelles
    #    et de capteurs GPS défectueux.
    _inject_realistic_errors(df, rng, miss_r)

    return df


def _inject_realistic_errors(df: pd.DataFrame, rng: np.random.Generator, miss_rate: float):
    """
    Injecte des erreurs réalistes dans le dataset brut.

    TYPES D'ERREURS :
      1. Valeurs manquantes (NaN) sur colonnes souvent incomplètes en terrain
      2. Outliers GPS : coordonnées légèrement hors bbox (erreur GPS)
      3. Valeurs aberrantes : trafic négatif, score > 100 (erreur de saisie)
      4. Doublons partiels : même emplacement, données légèrement différentes
    """
    n = len(df)

    # Colonnes souvent incomplètes sur le terrain
    cols_with_missing = [
        "height_m", "size_m2", "proprietaire",
        "hours_of_daylight_exposure", "pedestrian_density_score"
    ]

    # Injecter des NaN
    for col in cols_with_missing:
        n_missing = max(1, int(n * miss_rate))
        idx_missing = rng.choice(n, size=n_missing, replace=False)
        df.loc[idx_missing, col] = np.nan

    # Quelques outliers GPS (coordonnées légèrement erronées)
    n_gps_errors = max(1, int(n * 0.04))
    idx_gps = rng.choice(n, size=n_gps_errors, replace=False)
    df.loc[idx_gps, "latitude"]  += rng.uniform(-0.05, 0.05, size=n_gps_errors)
    df.loc[idx_gps, "longitude"] += rng.uniform(-0.05, 0.05, size=n_gps_errors)

    # Une valeur de score aberrante (erreur de saisie)
    idx_outlier = rng.integers(0, n)
    df.loc[idx_outlier, "visibility_score"] = rng.choice([105.0, -3.0, 999.0])

    # Un doublon partiel (même panneau saisi deux fois)
    if n > 10:
        idx_dup = rng.integers(0, n - 1)
        df.loc[n - 1, ["latitude", "longitude", "quartier", "panel_type"]] = \
            df.loc[idx_dup, ["latitude", "longitude", "quartier", "panel_type"]].values
        df.loc[n - 1, "panel_id"] = df.loc[idx_dup, "panel_id"]  # Même ID → doublon détectable


def run(config_path: str = "config/config.yaml") -> pd.DataFrame:
    """Point d'entrée du module. Génère et sauvegarde le dataset brut."""
    with open(config_path) as f:
        config = yaml.safe_load(f)

    print("[DATA GENERATION] Démarrage de la génération...")
    df = generate_billboard_dataset(config)

    output_path = Path(config["paths"]["raw_data"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    print(f"[DATA GENERATION] {len(df)} panneaux générés → {output_path}")
    print(f"[DATA GENERATION] Colonnes : {list(df.columns)}")
    print(f"[DATA GENERATION] Valeurs manquantes :\n{df.isnull().sum()[df.isnull().sum() > 0]}")
    return df


if __name__ == "__main__":
    run()
