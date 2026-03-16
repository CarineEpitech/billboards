"""
Script : 03_fetch_admin_boundaries.py
Phase : 2 — Collecte automatisée
Statut : PROVISOIRE — À valider après Phase 1 d'exploration manuelle
Date   : 2026-03-16

Ce que fait ce script :
    Télécharge les limites administratives (quartiers/arrondissements) de Cotonou depuis OSM.
    L'objectif est de pouvoir assigner automatiquement un nom de quartier à chaque panneau
    en fonction de ses coordonnées GPS.

    POURQUOI C'EST IMPORTANT :
    Dans la V1 du modèle, "quartier_enc" est la 2ème feature la plus importante.
    En V2, on veut que cette feature soit issue de vraies données géographiques
    plutôt que d'une valeur simulée aléatoirement.

Ce qu'il produit :
    - data/sources/overpass/raw/admin_cotonou.geojson        → polygones des quartiers
    - data/sources/overpass/processed/quartiers_cotonou.csv  → tableau simplifié

Colonnes du CSV produit :
    osm_id    → identifiant OSM
    name      → nom du quartier (ex: "Akpakpa", "Cadjehoun")
    level     → niveau administratif OSM (6, 7, ou 8)
    geometry  → polygone GPS du quartier

Comment utiliser ce fichier :
    → 04_build_features_from_osm.py fait un "point-in-polygon" :
       pour chaque panneau (lat, lon), il cherche dans quel polygone il se trouve
       → résultat : billboard["quartier"] = "Akpakpa"

Dépendances :
    pip install requests geopandas pandas pyyaml shapely

Décision liée : DEC-004 (bbox depuis config.yaml)

NOTE IMPORTANTE (hypothèse H-ADM-01) :
    Les niveaux administratifs OSM pour le Bénin ne sont pas standardisés.
    Ce script teste plusieurs niveaux (6, 7, 8) et garde celui qui donne
    les meilleurs résultats (le plus de quartiers avec des noms).
    Si aucun niveau ne fonctionne, on utilise les nodes "place=suburb"
    qui donnent au moins des points nommés (moins précis que des polygones).
    Statut de H-ADM-01 : À vérifier en Phase 1 d'exploration manuelle.
"""

# ============================================================
# IMPORTS
# ============================================================

import requests
import geopandas as gpd
import pandas as pd
import yaml
import time
from pathlib import Path
from shapely.geometry import shape  # pour convertir le JSON en géométrie Shapely

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

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

print("[03_fetch_admin] Démarrage — BBox Cotonou complète")
print(f"[03_fetch_admin] BBox : {BBOX}")

# ============================================================
# STRATÉGIE 1 : Récupérer les relations administratives
# (polygones = niveau préféré car donne des formes géographiques précises)
# ============================================================

def fetch_admin_relations(bbox: tuple, admin_level: int) -> dict:
    """
    Télécharge les limites administratives d'un niveau donné.

    Un "admin_level" dans OSM est un nombre qui indique le niveau
    de granularité administrative :
    - 2 = pays
    - 4 = région
    - 6 = département / ville
    - 7 ou 8 = quartier / arrondissement
    (Les niveaux varient selon les pays, d'où l'incertitude pour le Bénin)

    Retourne le JSON brut de l'API Overpass.
    """
    lat_min, lon_min, lat_max, lon_max = bbox
    bbox_str = f"({lat_min},{lon_min},{lat_max},{lon_max})"

    query = f"""
[out:json][timeout:90];
(
  relation["boundary"="administrative"]["admin_level"="{admin_level}"]{bbox_str};
);
out geom;
"""
    # Explication de "out geom;" pour les relations :
    # Les relations administratives sont des ensembles de ways (lignes) formant un polygone.
    # "out geom;" retourne les coordonnées GPS de chaque way → on peut reconstituer le polygone.

    try:
        response = requests.post(OVERPASS_URL, data={"data": query}, timeout=120)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"    Erreur niveau {admin_level} : {e}")
        return {"elements": []}

# ============================================================
# STRATÉGIE 2 : Récupérer les nodes "place" (fallback)
# Si pas de polygones, on utilise des points nommés (moins précis)
# ============================================================

def fetch_place_nodes(bbox: tuple) -> dict:
    """
    Télécharge les nodes OSM de type "place=suburb" ou "place=neighbourhood".
    Ces nodes sont des points GPS avec un nom de quartier.
    Ils ne donnent pas les limites exactes du quartier mais au moins sa position centrale.
    Utilisé en fallback si les relations administratives sont absentes.
    """
    lat_min, lon_min, lat_max, lon_max = bbox
    bbox_str = f"({lat_min},{lon_min},{lat_max},{lon_max})"

    query = f"""
[out:json][timeout:60];
(
  node["place"~"suburb|neighbourhood|quarter"]{bbox_str};
);
out body;
"""
    try:
        response = requests.post(OVERPASS_URL, data={"data": query}, timeout=90)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"    Erreur nodes place : {e}")
        return {"elements": []}

# ============================================================
# TENTATIVE AVEC LES NIVEAUX ADMINISTRATIFS
# On teste du plus fin (8) au moins fin (6)
# ============================================================

admin_levels_to_try = [8, 7, 6]
best_result = []
best_level = None

for level in admin_levels_to_try:
    print(f"\n[03_fetch_admin] Tentative admin_level={level}...")
    data = fetch_admin_relations(BBOX, level)
    elements = [e for e in data.get("elements", []) if e.get("tags", {}).get("name")]

    print(f"  → {len(elements)} relation(s) avec un nom trouvée(s)")

    if len(elements) > len(best_result):
        best_result = elements
        best_level = level

    time.sleep(2)

# ============================================================
# TRAITEMENT DES RÉSULTATS
# ============================================================

quartiers = []

if len(best_result) >= 3:
    # On a des polygones utilisables
    print(f"\n[03_fetch_admin] ✓ Utilisation du niveau {best_level} "
          f"({len(best_result)} quartiers)")

    for element in best_result:
        tags = element.get("tags", {})
        name = tags.get("name", tags.get("name:fr", tags.get("loc_name", "Inconnu")))

        # Reconstituer le polygone depuis les membres de la relation
        # Note : c'est simplifié. Pour une reconstruction exacte, utiliser osmnx
        #        ou la bibliothèque overpy. Ici on garde le centroïde de la bbox
        #        des membres comme approximation.
        geometry = None
        if "bounds" in element:
            bounds = element["bounds"]
            # Créer un rectangle approximatif depuis les bounds
            from shapely.geometry import box
            geometry = box(
                bounds["minlon"], bounds["minlat"],
                bounds["maxlon"], bounds["maxlat"]
            )

        quartiers.append({
            "osm_id":   element.get("id"),
            "name":     name,
            "level":    best_level,
            "geometry": geometry,
            "source":   "relation"
        })

else:
    # Fallback : on utilise les nodes place=suburb
    print(f"\n[03_fetch_admin] ⚠ Peu de polygones trouvés (niveau {best_level})")
    print("[03_fetch_admin] Basculement sur les nodes 'place=suburb' (fallback)...")

    data = fetch_place_nodes(BBOX)
    elements = data.get("elements", [])
    print(f"  → {len(elements)} nodes de place trouvés")

    from shapely.geometry import Point
    for element in elements:
        tags = element.get("tags", {})
        name = tags.get("name", tags.get("name:fr", None))
        if not name:
            continue

        quartiers.append({
            "osm_id":   element.get("id"),
            "name":     name,
            "level":    tags.get("admin_level", "N/A"),
            "geometry": Point(element.get("lon"), element.get("lat")),
            "source":   "place_node"  # ← indique qu'on a utilisé le fallback
        })

# ============================================================
# SAUVEGARDE
# ============================================================

if not quartiers:
    print("\n[03_fetch_admin] ⚠ ATTENTION : aucun quartier trouvé !")
    print("  → Hypothèse H-ADM-01 infirmée : OSM Cotonou n'a pas de limites administratives")
    print("  → Plan de fallback à activer : segmentation GPS manuelle par grille")
    print("  → Documenter dans decisions_log.md")
    raise ValueError("Aucun quartier trouvé — voir plan de fallback dans overpass_strategy.md")

df = pd.DataFrame(quartiers)
gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")

geojson_path = RAW_DIR / "admin_cotonou.geojson"
gdf.to_file(geojson_path, driver="GeoJSON")
print(f"\n[03_fetch_admin] ✓ GeoJSON sauvegardé : {geojson_path}")

csv_path = PROCESSED_DIR / "quartiers_cotonou.csv"
df.drop(columns=["geometry"]).to_csv(csv_path, index=False)
print(f"[03_fetch_admin] ✓ CSV sauvegardé : {csv_path}")

# ============================================================
# RÉSUMÉ
# ============================================================

print(f"\n[03_fetch_admin] === RÉSUMÉ ===")
print(f"  Quartiers trouvés : {len(df)}")
print(f"  Source utilisée   : {df['source'].unique().tolist()}")
print(f"  Noms des quartiers :")
for name in sorted(df['name'].tolist()):
    print(f"    - {name}")

print(f"\n[03_fetch_admin] ✓ Script terminé avec succès")
print("[03_fetch_admin] → Prochaine étape : 04_build_features_from_osm.py")
