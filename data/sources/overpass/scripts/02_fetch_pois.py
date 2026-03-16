"""
Script : 02_fetch_pois.py
Phase : 2 — Collecte automatisée (APRÈS validation manuelle via Overpass Turbo navigateur)
Statut : PROVISOIRE — À valider après Phase 1 d'exploration manuelle
Date   : 2026-03-16

Ce que fait ce script :
    Télécharge les Points d'Intérêt (POI) de Cotonou depuis OSM via l'API Overpass.
    Les POI sont les marchés, arrêts de transport, commerces, écoles, hôpitaux, etc.

    IMPORTANT : Ce script utilise des requêtes HTTP directes à l'API Overpass
    (et non osmnx) car osmnx est optimisé pour les routes, pas pour les POI variés.
    L'API Overpass est interrogée catégorie par catégorie pour éviter les timeouts.

Ce qu'il produit dans le dataset :
    - data/sources/overpass/raw/pois_cotonou.geojson     → tous les POI avec géométrie
    - data/sources/overpass/processed/pois_cotonou.csv   → tableau simplifié

Colonnes du CSV produit :
    osm_id       → identifiant unique dans OSM
    name         → nom du lieu (si disponible)
    category     → catégorie (marketplace, bus_stop, school, etc.)
    lat          → latitude GPS
    lon          → longitude GPS

Comment utiliser ce fichier dans le pipeline :
    → Ce CSV sera lu par 04_build_features_from_osm.py pour calculer :
       - nb_markets_500m        (marchés dans rayon 500m)
       - nb_transport_stops_500m (arrêts de transport dans rayon 500m)
       - nb_schools_500m
       - commercial_density_500m
       → Ces variables alimentent le proxy de "pedestrian_density_score"

Dépendances (à installer) :
    pip install requests geopandas pandas pyyaml shapely

Décisions liées : DEC-007 (rayon 500m), DEC-004 (bbox)
"""

# ============================================================
# IMPORTS
# ============================================================

import requests            # pour faire des requêtes HTTP à l'API Overpass
import geopandas as gpd    # tableaux géographiques
import pandas as pd        # tableaux classiques
import yaml                # lecture de config.yaml
import time                # pour les pauses entre requêtes (politesse envers le serveur)
from pathlib import Path
from shapely.geometry import Point  # pour créer des points géographiques

# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[4]
CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"

with open(CONFIG_PATH, "r") as f:
    config = yaml.safe_load(f)

GEO = config["geography"]
BBOX = (GEO["lat_min"], GEO["lon_min"], GEO["lat_max"], GEO["lon_max"])

RAW_DIR = PROJECT_ROOT / "data" / "sources" / "overpass" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "sources" / "overpass" / "processed"
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Zone de test (désactiver USE_TEST_ZONE pour lancer sur Cotonou entier)
BBOX_TEST = (6.355, 2.375, 6.375, 2.400)
USE_TEST_ZONE = True
bbox_to_use = BBOX_TEST if USE_TEST_ZONE else BBOX
zone_label = "test" if USE_TEST_ZONE else "cotonou"

# URL de l'API Overpass (serveur public gratuit)
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Pause entre les requêtes (en secondes)
# Explication : L'API Overpass est gratuite. Par politesse, on attend 2 secondes
# entre chaque requête pour ne pas surcharger le serveur.
PAUSE_BETWEEN_REQUESTS = 2

# ============================================================
# DÉFINITION DES CATÉGORIES DE POI À COLLECTER
# Format : { "nom_categorie": "requête_overpass_QL" }
# La variable {{bbox}} sera remplacée par la bbox réelle
# ============================================================

# Explication du format {{bbox}} dans la requête :
# Dans Overpass QL, {{bbox}} est un raccourci pour (sud, ouest, nord, est)
# On le remplacera dans le code par nos vraies coordonnées

def build_query(overpass_filter: str, bbox: tuple) -> str:
    """
    Construit une requête Overpass QL complète.

    Arguments :
        overpass_filter : le filtre OSM (ex: '["amenity"="marketplace"]')
        bbox : tuple (lat_min, lon_min, lat_max, lon_max)

    Retourne :
        str : la requête complète prête à être envoyée à l'API
    """
    lat_min, lon_min, lat_max, lon_max = bbox
    bbox_str = f"({lat_min},{lon_min},{lat_max},{lon_max})"
    return f"""
[out:json][timeout:60];
(
  node{overpass_filter}{bbox_str};
  way{overpass_filter}{bbox_str};
);
out center;
"""
# Explication de "out center;" :
# Pour les ways (polygones = bâtiments, marchés), on retourne le centre du polygone
# plutôt que la liste de tous les points GPS de la forme.
# Résultat : un seul point GPS par objet, plus facile à travailler.

# Dictionnaire des requêtes par catégorie
POI_QUERIES = {
    "marketplace":    '["amenity"="marketplace"]',
    "commercial":     '["landuse"~"commercial|retail"]',
    "supermarket":    '["shop"~"supermarket|mall|convenience"]',
    "bus_stop":       '["highway"="bus_stop"]',
    "bus_station":    '["amenity"="bus_station"]',
    "school":         '["amenity"~"school|college"]',
    "university":     '["amenity"="university"]',
    "hospital":       '["amenity"~"hospital|clinic|health_post"]',
    "fuel":           '["amenity"="fuel"]',
    "bank":           '["amenity"="bank"]',
    "hotel":          '["tourism"~"hotel|hostel"]',
}

# ============================================================
# FONCTION : APPEL À L'API OVERPASS
# ============================================================

def fetch_overpass(query: str) -> dict:
    """
    Envoie une requête à l'API Overpass et retourne le résultat JSON.

    Arguments :
        query : la requête Overpass QL en texte

    Retourne :
        dict : les données OSM au format JSON
              Contient une clé "elements" avec la liste des objets trouvés

    En cas d'erreur (timeout, serveur indisponible), retourne un dict vide.
    """
    try:
        response = requests.post(
            OVERPASS_URL,
            data={"data": query},
            timeout=90  # on attend max 90 secondes
        )
        response.raise_for_status()  # lève une exception si le code HTTP n'est pas 200
        return response.json()
    except requests.exceptions.Timeout:
        print("    ✗ Timeout — le serveur Overpass n'a pas répondu à temps")
        return {"elements": []}
    except requests.exceptions.RequestException as e:
        print(f"    ✗ Erreur réseau : {e}")
        return {"elements": []}

# ============================================================
# FONCTION : EXTRACTION DES COORDONNÉES GPS
# ============================================================

def extract_coords(element: dict) -> tuple:
    """
    Extrait les coordonnées GPS d'un élément OSM.

    Pour les nodes (points) : les coordonnées sont directement dans l'élément
    Pour les ways (polygones) : on utilise le centre calculé par "out center;"

    Retourne : (lat, lon) ou (None, None) si non disponible
    """
    if element["type"] == "node":
        return element.get("lat"), element.get("lon")
    elif element["type"] == "way" and "center" in element:
        return element["center"].get("lat"), element["center"].get("lon")
    return None, None

# ============================================================
# COLLECTE PRINCIPALE
# ============================================================

print(f"[02_fetch_pois] Démarrage — zone : {zone_label}")
print(f"[02_fetch_pois] BBox utilisée : {bbox_to_use}")
print(f"[02_fetch_pois] {len(POI_QUERIES)} catégories de POI à collecter\n")

all_pois = []  # liste qui va accumuler tous les POI

for category, osm_filter in POI_QUERIES.items():
    print(f"  Collecte : {category}...", end=" ", flush=True)

    query = build_query(osm_filter, bbox_to_use)
    data = fetch_overpass(query)

    elements = data.get("elements", [])

    if not elements:
        print(f"0 résultats")
    else:
        count = 0
        for element in elements:
            lat, lon = extract_coords(element)
            if lat is None or lon is None:
                continue  # on ignore les éléments sans coordonnées

            tags = element.get("tags", {})
            poi = {
                "osm_id":   element.get("id"),
                "osm_type": element.get("type"),
                "name":     tags.get("name", None),  # None si pas de nom dans OSM
                "category": category,
                "lat":      lat,
                "lon":      lon,
            }
            all_pois.append(poi)
            count += 1

        print(f"{count} POI trouvés ✓")

    # Pause de politesse entre les requêtes
    time.sleep(PAUSE_BETWEEN_REQUESTS)

print(f"\n[02_fetch_pois] Total : {len(all_pois)} POI collectés")

# ============================================================
# CRÉATION DU GEODATAFRAME
# ============================================================

if not all_pois:
    print("[02_fetch_pois] ⚠ ATTENTION : aucun POI collecté !")
    print("[02_fetch_pois] Vérifier :")
    print("  1. La connexion internet")
    print("  2. Que la zone de test est bien dans Cotonou")
    print("  3. Que l'API Overpass est accessible")
    raise ValueError("Aucun POI collecté — arrêt du script")

df = pd.DataFrame(all_pois)

# Créer la colonne géométrique (Point = un point GPS)
# Note : dans geopandas, on passe (lon, lat) et non (lat, lon) — c'est l'inverse !
df["geometry"] = df.apply(lambda row: Point(row["lon"], row["lat"]), axis=1)

# Convertir en GeoDataFrame avec le système de coordonnées standard
gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")
# EPSG:4326 = système de coordonnées GPS standard (WGS 84) — le même que Google Maps

# ============================================================
# SAUVEGARDE
# ============================================================

geojson_path = RAW_DIR / f"pois_{zone_label}.geojson"
gdf.to_file(geojson_path, driver="GeoJSON")
print(f"[02_fetch_pois] ✓ GeoJSON sauvegardé : {geojson_path}")

csv_path = PROCESSED_DIR / f"pois_{zone_label}.csv"
df.drop(columns=["geometry"]).to_csv(csv_path, index=False)
print(f"[02_fetch_pois] ✓ CSV sauvegardé : {csv_path}")

# ============================================================
# VALIDATION ET RÉSUMÉ
# ============================================================

print("\n[02_fetch_pois] === RÉSUMÉ PAR CATÉGORIE ===")
print(df.groupby("category").size().sort_values(ascending=False).to_string())

print(f"\n[02_fetch_pois] === QUALITÉ DES DONNÉES ===")
print(f"  POI avec nom : {df['name'].notna().sum()} "
      f"({df['name'].notna().mean()*100:.0f}%)")
print(f"  POI sans nom : {df['name'].isna().sum()} "
      f"(sera ignoré dans les features de densité)")

print(f"\n[02_fetch_pois] ✓ Script terminé avec succès")
print("[02_fetch_pois] → Prochaine étape : 03_fetch_admin_boundaries.py")
