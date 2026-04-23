"""
Script : 01_fetch_roads.py
Phase : 2 — Collecte automatisée (APRÈS validation manuelle via Overpass Turbo navigateur)
Statut : PROVISOIRE — À valider après Phase 1 d'exploration manuelle
Date   : 2026-03-16

Ce que fait ce script :
    1. Télécharge le réseau routier complet de Cotonou depuis OSM (via osmnx)
    2. Filtre les routes par type (trunk, primary, secondary, tertiary)
    3. Sauvegarde le résultat en GeoJSON (format géographique) et CSV (format tableau)

Ce qu'il produit dans le dataset :
    - data/sources/overpass/raw/roads_cotonou.geojson  → toutes les routes avec géométrie
    - data/sources/overpass/processed/roads_cotonou.csv → tableau simplifié pour le ML

Colonnes du CSV produit :
    osmid       → identifiant unique de la route dans OSM
    name        → nom de la route (ex: "Boulevard de la Marina")
    highway     → type de route (trunk, primary, secondary, tertiary)
    lanes       → nombre de voies (si disponible, sinon NaN)
    geometry    → tracé GPS de la route (type LineString)

Comment utiliser ce fichier dans le pipeline :
    → Ce CSV sera lu par 04_build_features_from_osm.py pour calculer :
       - road_type (type de la route la plus proche d'un panneau)
       - distance_to_main_road_m (distance en mètres à la route principale la plus proche)

Dépendances (à installer) :
    pip install osmnx geopandas pandas pyyaml

Décisions liées : DEC-003 (osmnx), DEC-004 (bbox depuis config.yaml)
"""

# ============================================================
# IMPORTS
# ============================================================

import osmnx as ox          # bibliothèque OSM pour Python
import geopandas as gpd     # tableaux avec colonnes géographiques (comme pandas mais géo)
import pandas as pd         # tableaux de données classiques
import yaml                 # pour lire le fichier config.yaml
import os                   # pour gérer les chemins de fichiers
from pathlib import Path    # gestion des chemins (plus propre que os.path)

# ============================================================
# CONFIGURATION
# Explication : on lit les paramètres depuis config.yaml au lieu de les coder
# en dur ici. Ainsi, si la bbox change, on modifie un seul fichier.
# ============================================================

# Chemin vers la racine du projet (remonte depuis scripts/ → overpass/ → sources/ → data/ → project)
PROJECT_ROOT = Path(__file__).resolve().parents[4]
CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"

with open(CONFIG_PATH, "r") as f:
    config = yaml.safe_load(f)

# Récupérer la bbox depuis config.yaml
GEO = config["geography"]
BBOX = (GEO["lat_min"], GEO["lon_min"], GEO["lat_max"], GEO["lon_max"])
# BBOX = (6.340, 2.340, 6.405, 2.430) pour Cotonou

# Dossiers de sortie
RAW_DIR = PROJECT_ROOT / "data" / "sources" / "overpass" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "sources" / "overpass" / "processed"
RAW_DIR.mkdir(parents=True, exist_ok=True)        # crée le dossier si nécessaire
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# ÉTAPE 1 : ZONE DE TEST
# Explication : On commence TOUJOURS par tester sur une petite zone.
# Si ça marche ici, on lance sur toute la ville.
# ============================================================

BBOX_TEST = (6.355, 2.375, 6.375, 2.400)  # Akpakpa / Boulevard du Port
USE_TEST_ZONE = True  # ← CHANGER EN False POUR LANCER SUR TOUTE LA VILLE

bbox_to_use = BBOX_TEST if USE_TEST_ZONE else BBOX
zone_label = "test" if USE_TEST_ZONE else "cotonou"

print(f"[01_fetch_roads] Démarrage — zone : {zone_label}")
print(f"[01_fetch_roads] BBox utilisée : {bbox_to_use}")

# ============================================================
# ÉTAPE 2 : TÉLÉCHARGEMENT DU RÉSEAU ROUTIER
# Explication : osmnx.graph_from_bbox() envoie une requête à l'API Overpass
# et télécharge toutes les routes dans la zone spécifiée.
# network_type='drive' = routes pour voitures (exclut les chemins piétons)
# ============================================================

print("[01_fetch_roads] Téléchargement du graphe routier depuis OSM...")

try:
    G = ox.graph_from_bbox(
        north=bbox_to_use[2],  # lat_max
        south=bbox_to_use[0],  # lat_min
        east=bbox_to_use[3],   # lon_max
        west=bbox_to_use[1],   # lon_min
        network_type='drive',  # routes pour voitures
        simplify=True          # simplifie le graphe (moins de nœuds, plus propre)
    )
    print(f"[01_fetch_roads] ✓ Graphe téléchargé — {len(G.edges())} tronçons de routes")
except Exception as e:
    print(f"[01_fetch_roads] ✗ ERREUR lors du téléchargement : {e}")
    print("[01_fetch_roads] Vérifier la connexion internet ou réessayer dans quelques minutes")
    raise

# ============================================================
# ÉTAPE 3 : CONVERSION EN GEODATAFRAME
# Explication : Le graphe OSM est un objet complexe (réseau de nœuds et arêtes).
# On le convertit en tableau (GeoDataFrame) pour pouvoir le manipuler facilement.
# nodes=False → on ne veut que les arêtes (les routes), pas les intersections
# ============================================================

print("[01_fetch_roads] Conversion du graphe en tableau (GeoDataFrame)...")

nodes, edges = ox.graph_to_gdfs(G)  # nodes = intersections, edges = tronçons de routes

print(f"[01_fetch_roads] ✓ {len(edges)} tronçons de routes convertis")
print(f"[01_fetch_roads]   Colonnes disponibles : {list(edges.columns)}")

# ============================================================
# ÉTAPE 4 : FILTRAGE ET NETTOYAGE
# Explication : On garde uniquement les colonnes utiles pour notre modèle.
# On filtre aussi par type de route (on ne garde que les routes "importantes").
# ============================================================

# Types de routes à conserver (du plus important au moins important)
ROAD_TYPES_TO_KEEP = ["motorway", "trunk", "primary", "secondary", "tertiary", "unclassified"]

# Certaines routes ont plusieurs types dans une liste (ex: ["primary", "primary_link"])
# On extrait le premier type dans ces cas
def extract_first_highway_type(highway_value):
    """
    Extrait le premier type de route si c'est une liste.
    Ex: ["primary", "primary_link"] → "primary"
    Ex: "secondary" → "secondary"
    """
    if isinstance(highway_value, list):
        return highway_value[0]
    return highway_value

edges["highway_clean"] = edges["highway"].apply(extract_first_highway_type)

# Filtrer uniquement les types qui nous intéressent
roads_filtered = edges[edges["highway_clean"].isin(ROAD_TYPES_TO_KEEP)].copy()

print(f"[01_fetch_roads] Après filtrage : {len(roads_filtered)} tronçons retenus")
print(f"[01_fetch_roads] Répartition par type :")
print(roads_filtered["highway_clean"].value_counts().to_string())

# ============================================================
# ÉTAPE 5 : SÉLECTION DES COLONNES UTILES
# ============================================================

# Colonnes à conserver pour le dataset final
cols_to_keep = ["osmid", "name", "highway_clean", "geometry"]

# Certaines colonnes peuvent ne pas exister dans toutes les versions d'osmnx
optional_cols = ["lanes", "maxspeed", "oneway"]
for col in optional_cols:
    if col in roads_filtered.columns:
        cols_to_keep.append(col)

roads_clean = roads_filtered[cols_to_keep].rename(columns={"highway_clean": "highway"})

# ============================================================
# ÉTAPE 6 : SAUVEGARDE
# ============================================================

# Sauvegarde en GeoJSON (conserve la géométrie complète = tracé GPS de chaque route)
geojson_path = RAW_DIR / f"roads_{zone_label}.geojson"
roads_clean.to_file(geojson_path, driver="GeoJSON")
print(f"[01_fetch_roads] ✓ GeoJSON sauvegardé : {geojson_path}")

# Sauvegarde en CSV (sans géométrie pour la lisibilité, utile pour vérification rapide)
csv_path = PROCESSED_DIR / f"roads_{zone_label}.csv"
roads_clean.drop(columns=["geometry"]).to_csv(csv_path, index=False)
print(f"[01_fetch_roads] ✓ CSV sauvegardé : {csv_path}")

# ============================================================
# ÉTAPE 7 : VALIDATION MINIMALE
# Explication : On vérifie que les données ont du sens avant de les utiliser.
# ============================================================

print("\n[01_fetch_roads] === VALIDATION ===")
print(f"  Nombre total de tronçons : {len(roads_clean)}")
print(f"  Tronçons avec nom : {roads_clean['name'].notna().sum()} "
      f"({roads_clean['name'].notna().mean()*100:.0f}%)")
print(f"  Types de routes : {roads_clean['highway'].unique().tolist()}")

# Vérification que les coordonnées sont bien dans la zone Cotonou
bounds = roads_clean.total_bounds  # [minx, miny, maxx, maxy]
print(f"  Étendue GPS : lat [{bounds[1]:.3f}, {bounds[3]:.3f}], "
      f"lon [{bounds[0]:.3f}, {bounds[2]:.3f}]")

print("\n[01_fetch_roads] ✓ Script terminé avec succès")
print("[01_fetch_roads] → Prochaine étape : vérifier les fichiers produits, "
      "puis lancer 02_fetch_pois.py")
