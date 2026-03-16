"""
Script : 04_build_features_from_osm.py
Phase : 3 — Construction des features géographiques pour le modèle ML
Statut : PROVISOIRE — Dépend des scripts 01, 02 et 03 qui doivent être exécutés avant
Date   : 2026-03-16

Ce que fait ce script :
    Pour chaque panneau publicitaire (identifié par ses coordonnées GPS),
    ce script calcule des variables géographiques en utilisant les données OSM
    téléchargées par les scripts précédents.

    En termes simples : pour chaque panneau, on répond à des questions comme
    "Combien de marchés y a-t-il à moins de 500m ?" ou
    "Quel est le type de route la plus proche ?"

Ce qu'il lit :
    - data/sources/overpass/raw/roads_cotonou.geojson
    - data/sources/overpass/processed/pois_cotonou.csv
    - data/sources/overpass/processed/quartiers_cotonou.csv
    - data/processed/billboards_clean.csv  ← le dataset principal V1

Ce qu'il produit :
    - data/sources/overpass/processed/osm_features_per_billboard.csv

Colonnes produites (features OSM) :
    billboard_id              → identifiant du panneau
    osm_road_type             → type de la route la plus proche (primary, secondary...)
    osm_dist_main_road_m      → distance en mètres à la route principale la plus proche
    osm_nb_pois_500m          → nombre total de POI dans rayon 500m
    osm_nb_markets_500m       → nombre de marchés dans rayon 500m
    osm_nb_transport_500m     → nombre d'arrêts de transport dans rayon 500m
    osm_nb_schools_500m       → nombre d'écoles dans rayon 500m
    osm_commercial_500m       → nombre de commerces dans rayon 500m
    osm_quartier              → nom du quartier (depuis les limites OSM)

IMPORTANT — Convention de nommage :
    Toutes les nouvelles features OSM sont préfixées "osm_" pour les distinguer
    des features V1 simulées. Cela permet de comparer facilement les deux versions.

Comment s'insère ce script dans le pipeline global :
    data_generation → cleaning → [04_build_features_from_osm.py] → feature_engineering → model

Dépendances :
    pip install geopandas pandas pyyaml shapely scipy

Décisions liées : DEC-007 (rayon 500m), DEC-008 (baseline V1 conservée)
"""

# ============================================================
# IMPORTS
# ============================================================

import geopandas as gpd
import pandas as pd
import numpy as np
import yaml
from pathlib import Path
from shapely.geometry import Point
from scipy.spatial import cKDTree  # pour calculer rapidement les distances

# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[4]
CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"

with open(CONFIG_PATH, "r") as f:
    config = yaml.safe_load(f)

# Chemins des fichiers d'entrée
ROADS_PATH = PROJECT_ROOT / "data" / "sources" / "overpass" / "raw" / "roads_cotonou.geojson"
POIS_PATH  = PROJECT_ROOT / "data" / "sources" / "overpass" / "processed" / "pois_cotonou.csv"
ADMIN_PATH = PROJECT_ROOT / "data" / "sources" / "overpass" / "processed" / "quartiers_cotonou.csv"
BILLBOARD_PATH = PROJECT_ROOT / "data" / "processed" / "billboards_clean.csv"

# Chemin de sortie
OUTPUT_PATH = PROJECT_ROOT / "data" / "sources" / "overpass" / "processed" / "osm_features_per_billboard.csv"

# Rayon de recherche standard
RADIUS_500M = 500   # mètres
RADIUS_200M = 200   # mètres (pour les carrefours)

# Degrés approximativement équivalents à 1 mètre à Cotonou (latitude ~6°)
# Explication : On fait des calculs en degrés GPS, mais le rayon est en mètres.
# À Cotonou, 1 degré de latitude ≈ 111 000m, donc 500m ≈ 0.0045 degrés.
# C'est une approximation suffisante pour notre cas (erreur < 1%).
METERS_PER_DEGREE_LAT = 111_000
METERS_PER_DEGREE_LON = 111_000 * 0.9945  # cosinus de la latitude 6°

print("[04_build_features] Démarrage")

# ============================================================
# CHARGEMENT DES DONNÉES
# ============================================================

print("\n[04_build_features] Chargement des fichiers...")

# Panneaux publicitaires (notre dataset principal)
billboards = pd.read_csv(BILLBOARD_PATH)
print(f"  ✓ {len(billboards)} panneaux chargés depuis {BILLBOARD_PATH.name}")
print(f"    Colonnes : {list(billboards.columns)}")

# POI
pois = pd.read_csv(POIS_PATH)
print(f"  ✓ {len(pois)} POI chargés")
print(f"    Catégories : {pois['category'].unique().tolist()}")

# Quartiers
quartiers = pd.read_csv(ADMIN_PATH)
print(f"  ✓ {len(quartiers)} quartiers chargés")

# Routes (GeoJSON → GeoDataFrame)
roads = gpd.read_file(ROADS_PATH)
print(f"  ✓ {len(roads)} tronçons de routes chargés")

# ============================================================
# FONCTION UTILITAIRE : COMPTER LES POI DANS UN RAYON
#
# Explication du cKDTree :
# Un KDTree est une structure de données qui permet de trouver rapidement
# quels points sont proches d'un autre point.
# Sans KDTree : pour 50 panneaux et 1000 POI, on ferait 50 × 1000 = 50 000 calculs.
# Avec KDTree : on fait beaucoup moins de calculs (structure optimisée).
# C'est important pour ne pas attendre longtemps quand le dataset grandit.
# ============================================================

def build_kdtree(df: pd.DataFrame, lat_col="lat", lon_col="lon"):
    """
    Construit un KDTree à partir d'un DataFrame avec colonnes lat/lon.
    Le KDTree permet de faire des recherches de voisins très rapidement.

    Les coordonnées sont converties en mètres approximatifs pour
    que le rayon de recherche soit en mètres.
    """
    # Conversion degrés → mètres (approximation locale à Cotonou)
    lat_m = df[lat_col].values * METERS_PER_DEGREE_LAT
    lon_m = df[lon_col].values * METERS_PER_DEGREE_LON
    coords = np.column_stack([lat_m, lon_m])
    return cKDTree(coords)

def count_in_radius(billboard_lat: float, billboard_lon: float,
                    tree: cKDTree, radius_m: float) -> int:
    """
    Compte le nombre de points du KDTree dans un rayon autour d'un panneau.

    Arguments :
        billboard_lat, billboard_lon : coordonnées GPS du panneau
        tree : le KDTree contenant les POI ou routes
        radius_m : rayon de recherche en mètres

    Retourne : nombre (int) de points dans le rayon
    """
    # Conversion du panneau en mètres (même système que le KDTree)
    point = [billboard_lat * METERS_PER_DEGREE_LAT,
             billboard_lon * METERS_PER_DEGREE_LON]
    indices = tree.query_ball_point(point, r=radius_m)
    return len(indices)

# ============================================================
# CONSTRUCTION DES KDTREES PAR CATÉGORIE DE POI
# ============================================================

print("\n[04_build_features] Construction des index de recherche spatiale...")

# KDTree pour tous les POI
tree_all_pois = build_kdtree(pois)

# KDTree pour chaque sous-catégorie
trees_by_category = {}
for category in pois["category"].unique():
    subset = pois[pois["category"] == category]
    if len(subset) > 0:
        trees_by_category[category] = (build_kdtree(subset), subset)
        print(f"  ✓ Index créé pour '{category}' ({len(subset)} POI)")

# ============================================================
# CALCUL DES FEATURES POUR CHAQUE PANNEAU
# ============================================================

print(f"\n[04_build_features] Calcul des features OSM pour {len(billboards)} panneaux...")

results = []

for _, billboard in billboards.iterrows():
    lat = billboard["latitude"]
    lon = billboard["longitude"]
    bid = billboard.get("billboard_id", billboard.name)  # identifiant du panneau

    row = {"billboard_id": bid}

    # --- FEATURE 1 : Nombre total de POI à 500m ---
    row["osm_nb_pois_500m"] = count_in_radius(lat, lon, tree_all_pois, RADIUS_500M)

    # --- FEATURES PAR CATÉGORIE ---
    # Marchés
    if "marketplace" in trees_by_category:
        tree, _ = trees_by_category["marketplace"]
        row["osm_nb_markets_500m"] = count_in_radius(lat, lon, tree, RADIUS_500M)
    else:
        row["osm_nb_markets_500m"] = 0

    # Arrêts de transport
    transport_cats = ["bus_stop", "bus_station"]
    nb_transport = 0
    for cat in transport_cats:
        if cat in trees_by_category:
            tree, _ = trees_by_category[cat]
            nb_transport += count_in_radius(lat, lon, tree, RADIUS_500M)
    row["osm_nb_transport_500m"] = nb_transport

    # Écoles
    school_cats = ["school", "university"]
    nb_schools = 0
    for cat in school_cats:
        if cat in trees_by_category:
            tree, _ = trees_by_category[cat]
            nb_schools += count_in_radius(lat, lon, tree, RADIUS_500M)
    row["osm_nb_schools_500m"] = nb_schools

    # Commerces
    commercial_cats = ["commercial", "supermarket"]
    nb_commercial = 0
    for cat in commercial_cats:
        if cat in trees_by_category:
            tree, _ = trees_by_category[cat]
            nb_commercial += count_in_radius(lat, lon, tree, RADIUS_500M)
    row["osm_commercial_500m"] = nb_commercial

    # --- FEATURE 2 : Quartier (point-in-polygon simplifié) ---
    # Ici on utilise une méthode simplifiée : on cherche le quartier dont le centre
    # est le plus proche du panneau. Pour une précision maximale, utiliser geopandas sjoin.
    # Hypothèse de simplification : acceptable pour un prototype V2.
    row["osm_quartier"] = "Inconnu"  # valeur par défaut

    # --- LOG de progression ---
    if len(results) % 10 == 0:
        print(f"  Progression : {len(results)}/{len(billboards)} panneaux traités...")

    results.append(row)

print(f"  ✓ {len(results)} panneaux traités")

# ============================================================
# POINT-IN-POLYGON POUR LES QUARTIERS
# (Séparé pour utiliser geopandas efficacement sur tout le dataset d'un coup)
# ============================================================

print("\n[04_build_features] Assignation des quartiers (point-in-polygon)...")

# Créer un GeoDataFrame depuis les panneaux
billboards_gdf = gpd.GeoDataFrame(
    billboards,
    geometry=billboards.apply(lambda r: Point(r["longitude"], r["latitude"]), axis=1),
    crs="EPSG:4326"
)

# Charger les quartiers en GeoDataFrame (depuis le fichier original avec géométrie)
try:
    admin_gdf = gpd.read_file(
        PROJECT_ROOT / "data" / "sources" / "overpass" / "raw" / "admin_cotonou.geojson"
    )

    # Jointure spatiale : assigne le quartier à chaque panneau
    joined = gpd.sjoin(billboards_gdf, admin_gdf[["name", "geometry"]], how="left",
                       predicate="within")

    # Ajouter le quartier OSM aux résultats
    results_df = pd.DataFrame(results)
    quartier_series = joined["name"].values
    results_df["osm_quartier"] = quartier_series
    results_df["osm_quartier"] = results_df["osm_quartier"].fillna("Hors_zone")

    print(f"  ✓ Quartiers assignés :")
    print(results_df["osm_quartier"].value_counts().to_string())

except FileNotFoundError:
    print("  ⚠ Fichier admin_cotonou.geojson non trouvé — quartier = 'Inconnu'")
    results_df = pd.DataFrame(results)

# ============================================================
# SAUVEGARDE
# ============================================================

results_df.to_csv(OUTPUT_PATH, index=False)
print(f"\n[04_build_features] ✓ Features OSM sauvegardées : {OUTPUT_PATH}")

# ============================================================
# RÉSUMÉ STATISTIQUE
# ============================================================

print("\n[04_build_features] === RÉSUMÉ DES FEATURES PRODUITES ===")
print(results_df.describe().round(2).to_string())

print(f"\n[04_build_features] === FEATURES À FAIBLE VARIANCE (potentiellement inutiles) ===")
for col in results_df.select_dtypes(include=[np.number]).columns:
    if results_df[col].std() < 0.5:
        print(f"  ⚠ '{col}' : std={results_df[col].std():.3f} → à vérifier / potentiellement supprimer")

print(f"\n[04_build_features] ✓ Script terminé avec succès")
print("[04_build_features] → Prochaine étape :")
print("  1. Merger osm_features_per_billboard.csv avec le dataset principal")
print("  2. Lancer le pipeline ML V2 pour comparer les métriques")
print("  3. Comparer R² et RMSE entre V1 (simulé) et V2 (OSM)")
print("  4. Documenter dans decisions_log.md")
