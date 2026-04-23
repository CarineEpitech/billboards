"""
==============================================================================
MODULE : feature_engineering.py
==============================================================================

RÔLE : Transformer les données propres en features exploitables par le modèle.

QU'EST-CE QUE LE FEATURE ENGINEERING ?
  C'est l'art de créer des variables pertinentes à partir des données brutes.
  Un RandomForest peut théoriquement apprendre des non-linéarités, mais lui
  donner directement les bonnes features :
  - Accélère la convergence
  - Améliore la généralisation
  - Rend le modèle plus interprétable

CATÉGORIES DE FEATURES CRÉÉES :
  1. ENCODAGE CATÉGORIEL  → transformer texte en nombres
  2. FEATURES DÉRIVÉES    → calculer des interactions physiquement pertinentes
  3. FEATURES GÉOSPATIALES → extraire du signal des coordonnées GPS
  4. NORMALISATION        → mise à l'échelle pour les algorithmes sensibles

DÉCISIONS CLÉS :
  - On utilise Label Encoding (pas One-Hot) pour le RandomForest
    → RF gère les ordinaux implicites, et One-Hot sur 10 quartiers = 10 colonnes
    inutiles pour un dataset de 40 lignes (risque de sur-ajustement)
  - On ne normalise PAS pour le RandomForest (il est invariant aux échelles)
    mais on crée une version normalisée pour la roadmap V2 (réseaux de neurones)

==============================================================================
"""

import numpy as np
import pandas as pd
import yaml
from pathlib import Path


# ---------------------------------------------------------------------------
# 1. ENCODAGE DES VARIABLES CATÉGORIELLES
# ---------------------------------------------------------------------------

def encode_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Encode les variables catégorielles en entiers.

    POURQUOI LABEL ENCODING et pas ONE-HOT ENCODING ici ?
    -------------------------------------------------------
    One-Hot Encoding crée une colonne binaire par modalité.
    Pour 10 quartiers → 10 colonnes. Avec 40 lignes d'entraînement,
    on a trop peu d'exemples par combinaison → sur-ajustement garanti.

    Label Encoding assigne un entier à chaque catégorie (Akpakpa=0, Cadjehoun=1...).
    Le RandomForest peut exploiter ces codes car il fait des splits binaires
    (quartier <= 3 vs quartier > 3) ce qui regroupe implicitement des quartiers.

    LIMITES : Label Encoding introduit un ordre arbitraire. Un modèle linéaire
    interpréterait Zongo=9 > Akpakpa=0 comme "Zongo est plus grand", ce qui est
    faux. Pour les modèles linéaires, utiliser One-Hot.
    → En V2 avec des features géospatiales, ce problème disparaît.

    TRAÇABILITÉ : On sauvegarde le mapping pour pouvoir décoder les prédictions.
    """
    mappings = {}

    for col in ["panel_type", "quartier", "road_type"]:
        if col in df.columns:
            categories   = sorted(df[col].dropna().unique())
            cat_to_int   = {cat: idx for idx, cat in enumerate(categories)}
            enc_col_name = f"{col}_enc"
            df[enc_col_name] = df[col].map(cat_to_int)
            mappings[col] = cat_to_int
            print(f"  [ENCODE] '{col}' → '{enc_col_name}' | {len(categories)} modalités")

    return df, mappings


# ---------------------------------------------------------------------------
# 2. FEATURES DÉRIVÉES (Feature Engineering Métier)
# ---------------------------------------------------------------------------

def create_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Crée des features calculées à partir des features existantes.

    PHILOSOPHIE :
      On intègre ici la connaissance métier. Le modèle pourrait théoriquement
      apprendre ces relations, mais les lui donner explicitement :
      1. Réduit le nombre d'exemples nécessaires à l'apprentissage
      2. Améliore l'interprétabilité des features importantes
      3. Capture des interactions que les arbres de décision simples manquent

    FEATURES CRÉÉES :
    -----------------
    a) score_surface_hauteur : rapport taille/hauteur
       → Un grand panneau bas vs un petit panneau haut n'ont pas le même impact
       → Ratio capturé mieux par le produit que par les features indépendantes

    b) log_traffic : trafic en échelle logarithmique
       → Le gain de visibilité de 1000→2000 véhicules est plus fort que
         de 10000→11000. Le log capture cette non-linéarité.

    c) score_accessibilite : distance route + distance centre combinées
       → Un panneau loin de la route ET du centre est doublement pénalisé

    d) indice_saturation : compétition * densité piétonne
       → Zone très fréquentée avec beaucoup de concurrents : impact ambigu
         (plus de visibilité MAIS attention diluée)

    e) is_digital_flag : binaire pour type digital
       → Feature high-impact méritant un signal fort séparé de l'encodage

    f) age_panneau : ancienneté depuis l'installation
       → Les vieux panneaux sont souvent dégradés ou moins bien positionnés
    """
    current_year = 2024  # Année de référence du dataset

    # a) Ratio surface/hauteur — index d'impact visuel
    # Éviter division par zéro avec clip
    df["ratio_surface_hauteur"] = df["size_m2"] / df["height_m"].clip(lower=0.5)

    # b) Trafic en log — capture la non-linéarité de la saturation visuelle
    # log1p = log(1 + x) pour gérer les cas x=0
    df["log_traffic"] = np.log1p(df["traffic_flow_estim"])

    # c) Score d'accessibilité composite (distance route + distance centre)
    # On normalise chaque composante pour qu'elles aient le même ordre de grandeur
    # distance_road en mètres, distance_center en km → convertir en mètres
    df["score_accessibilite"] = (
        (df["distance_to_main_road_m"] / 200)      # normalisé sur 200m max
        + (df["distance_to_center_km"] / 5)         # normalisé sur 5km max
    )
    # Un score proche de 0 = très accessible, proche de 2 = très éloigné

    # d) Indice de saturation publicitaire
    # competition * (pedestrian_score / 100) → entre 0 et ~5
    df["indice_saturation"] = (
        df["competition_radius_500m"] * (df["pedestrian_density_score"] / 100)
    )

    # e) Flag numérique pour panneau digital (forte importance métier)
    df["is_digital"] = (df["panel_type"] == "digital").astype(int)

    # f) Âge du panneau
    df["age_panneau"] = current_year - df["year_installed"]

    # g) Exposition solaire pondérée par type de panneau
    # Un panneau digital est visible 24h, un statique dépend de la lumière
    df["effective_exposure_hours"] = np.where(
        df["panel_type"] == "digital",
        24,                                          # Digital = visible la nuit aussi
        df["hours_of_daylight_exposure"]
    )

    print(f"  [FEATURES] 7 features dérivées créées")
    return df


# ---------------------------------------------------------------------------
# 3. FEATURES GÉOSPATIALES
# ---------------------------------------------------------------------------

def create_geo_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extrait du signal géospatial des coordonnées GPS.

    POURQUOI ?
      Les modèles ML ne comprennent pas les coordonnées GPS brutes comme
      "quartier nord-est". Il faut leur donner des features qui capturent
      la sémantique géographique.

    FEATURES CRÉÉES :
    -----------------
    a) distance_to_beach : distance à la plage (axe de tourisme Cotonou)
       → Les panneaux près de la côte ciblent une clientèle différente

    b) distance_to_port : distance au Port Autonome de Cotonou
       → Zone de fort trafic commercial (camions → public captif)

    c) quadrant : division de Cotonou en 4 zones (NE, NW, SE, SW)
       → Feature catégorielle simple capturant la géographie sans coordonnées

    SIMPLIFICATION : On utilise des distances euclidiennes approximatives
    (valables pour de courtes distances en degrés). En V2, on utilisera
    des distances géodésiques avec geopy ou shapely.
    """
    # Points de référence géographiques de Cotonou
    BEACH_LAT,  BEACH_LON  = 6.340, 2.383  # Bord de mer (Fidjrossè/Cadjehoun)
    PORT_LAT,   PORT_LON   = 6.350, 2.422  # Port Autonome de Cotonou
    CENTER_LAT, CENTER_LON = 6.370, 2.390  # Centre-ville (référence)

    def haversine_simple(lat, lon, ref_lat, ref_lon):
        """Distance approximative en km (valide pour < 50km)."""
        dlat = (lat - ref_lat) * 111.0
        dlon = (lon - ref_lon) * 111.0 * np.cos(np.radians(lat))
        return np.sqrt(dlat**2 + dlon**2)

    df["distance_to_beach_km"] = haversine_simple(
        df["latitude"], df["longitude"], BEACH_LAT, BEACH_LON
    ).round(3)

    df["distance_to_port_km"] = haversine_simple(
        df["latitude"], df["longitude"], PORT_LAT, PORT_LON
    ).round(3)

    # Quadrant géographique (0=SW, 1=SE, 2=NW, 3=NE)
    df["geo_quadrant"] = (
        (df["latitude"]  >= CENTER_LAT).astype(int) * 2 +
        (df["longitude"] >= CENTER_LON).astype(int)
    )

    print(f"  [GEO] 3 features géospatiales créées")
    return df


# ---------------------------------------------------------------------------
# 4. SÉLECTION ET PRÉPARATION DES FEATURES FINALES
# ---------------------------------------------------------------------------

def select_features(df: pd.DataFrame, config: dict) -> tuple[pd.DataFrame, pd.Series, list]:
    """
    Sélectionne les features finales pour l'entraînement.

    FEATURES RETENUES :
      On combine les features originales + dérivées + géospatiales.
      On EXCLUT :
      - panel_id (identifiant non-prédictif)
      - quartier, panel_type, road_type (remplacés par leur encodage numérique)
      - proprietaire (trop de modalités, peu prédictif pour la visibilité)
      - has_photo (meta-donnée sur la qualité de la saisie, non métier)
      - year_installed (remplacé par age_panneau)
      - latitude/longitude brutes (remplacées par features dérivées géo)

    POURQUOI GARDER latitude/longitude quand même ?
      Le RandomForest peut trouver des splits géographiques utiles
      (lon > 2.40 = zone est de Cotonou). On les garde en supplément
      des features dérivées.

    CIBLE : visibility_score_clean (score 0–100 continu → régression)
    """
    feature_cols = config["features"]["numerical"] + config["features"]["categorical"]

    # Ajouter les features dérivées créées dans ce module
    extra_features = [
        "ratio_surface_hauteur",
        "log_traffic",
        "score_accessibilite",
        "indice_saturation",
        "is_digital",
        "age_panneau",
        "effective_exposure_hours",
        "distance_to_beach_km",
        "distance_to_port_km",
        "geo_quadrant",
    ]

    all_features = feature_cols + extra_features

    # Filtrer les colonnes qui existent réellement dans le DataFrame
    available = [c for c in all_features if c in df.columns]
    missing   = [c for c in all_features if c not in df.columns]

    if missing:
        print(f"  [SELECT] Colonnes absentes ignorées : {missing}")

    target = config["features"]["target"]

    X = df[available].copy()
    y = df[target].copy()

    print(f"  [SELECT] {len(available)} features sélectionnées pour {len(X)} observations")
    print(f"  [SELECT] Cible '{target}' : min={y.min():.1f}, max={y.max():.1f}, "
          f"mean={y.mean():.1f}, std={y.std():.1f}")

    return X, y, available


# ---------------------------------------------------------------------------
# PIPELINE PRINCIPAL
# ---------------------------------------------------------------------------

def engineering_pipeline(df: pd.DataFrame, config: dict) -> tuple[pd.DataFrame, pd.Series, list, dict]:
    """
    Pipeline complet de feature engineering.

    ORDRE D'EXÉCUTION :
      1. Encodage catégoriel (les features dérivées peuvent utiliser panel_type en texte)
      2. Features dérivées (utilise height_m, size_m2 qui sont propres après cleaning)
      3. Features géospatiales (utilise lat/lon propres)
      4. Sélection finale

    RETOUR :
      X         : DataFrame des features
      y         : Série de la variable cible
      feat_cols : Liste des noms de features
      mappings  : Dictionnaire des encodages catégoriels (pour décodage futur)
    """
    print("\n[FEATURE ENGINEERING] Démarrage...")

    df, mappings = encode_categoricals(df)
    df           = create_derived_features(df)
    df           = create_geo_features(df)
    X, y, feat_cols = select_features(df, config)

    # Vérification finale : aucun NaN dans X
    n_nan = X.isnull().sum().sum()
    if n_nan > 0:
        print(f"  [WARNING] {n_nan} NaN détectés dans les features → imputation de secours par médiane")
        X = X.fillna(X.median(numeric_only=True))

    print(f"[FEATURE ENGINEERING] Terminé. Shape final : X={X.shape}, y={y.shape}\n")
    return X, y, feat_cols, mappings


def run(config_path: str = "config/config.yaml") -> tuple:
    """Point d'entrée du module."""
    with open(config_path) as f:
        config = yaml.safe_load(f)

    clean_path = config["paths"]["processed_data"]
    df = pd.read_csv(clean_path)
    print(f"[FE] Dataset propre chargé : {df.shape}")

    return engineering_pipeline(df, config)


if __name__ == "__main__":
    run()
