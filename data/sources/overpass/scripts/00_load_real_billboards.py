"""
Script : 00_load_real_billboards.py
Phase  : 2 — Premier chargement de données réelles
Statut : VALIDÉ — Premier fichier OSM réel intégré au projet
Date   : 2026-03-16

Contexte :
    Ce script traite le premier fichier GeoJSON réel du projet :
    "billboards_osm_raw.geojson" — exporté depuis Overpass Turbo le 2026-03-16
    avec la requête : node["advertising"="billboard"](bbox Cotonou élargie)

    C'est le point de départ du dataset V2 (données réelles).
    En V1, les panneaux étaient simulés (45 lignes inventées par data_generation.py).
    Ici, on a 11 vrais panneaux géolocalisés dans OSM.

Ce que fait ce script :
    1. Charge le GeoJSON brut
    2. Extrait les coordonnées GPS et les attributs de chaque panneau
    3. Ajoute des colonnes dérivées (is_lit, in_cotonou_core, etc.)
    4. Filtre les panneaux géographiquement suspects (hors zone Cotonou)
    5. Sauvegarde un CSV propre prêt pour le pipeline

Ce qu'il produit :
    - data/sources/overpass/processed/billboards_osm_v1.csv

Colonnes produites :
    osm_id          → identifiant unique dans OSM (ex: "node/3539813703")
    longitude       → coordonnée GPS est-ouest
    latitude        → coordonnée GPS nord-sud
    is_lit          → 1 si éclairé la nuit (lit=yes), 0 sinon
    has_name        → 1 si un nom est renseigné dans OSM, 0 sinon
    name            → nom du panneau (ex: "Pharmacie Camp Guezo"), None sinon
    source_survey   → 1 si ajouté par une enquête terrain (source=survey)
    zone            → "cotonou_core", "cotonou_extended" ou "hors_zone"
    advertising     → toujours "billboard" dans ce fichier

Décisions liées :
    DEC-010 (H3 infirmée), DEC-011 (bbox élargie), DEC-012 (filtre géographique)

Comment ce script s'insère dans le pipeline V2 :
    00_load_real_billboards.py   → billboards_osm_v1.csv (positions réelles)
           ↓
    04_build_features_from_osm.py → osm_features_per_billboard.csv (features contextuelles)
           ↓
    feature_engineering.py       → dataset final pour le modèle ML

Dépendances :
    pip install geopandas pandas pyyaml
"""

# ============================================================
# IMPORTS
# ============================================================

import json
import geopandas as gpd
import pandas as pd
import yaml
from pathlib import Path

# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[4]
CONFIG_PATH  = PROJECT_ROOT / "config" / "config.yaml"

with open(CONFIG_PATH, "r") as f:
    config = yaml.safe_load(f)

GEO = config["geography"]

# BBox principale (config.yaml — élargie en DEC-011)
LAT_MIN = GEO["lat_min"]   # 6.330
LAT_MAX = GEO["lat_max"]   # 6.430
LON_MIN = GEO["lon_min"]   # 2.330
LON_MAX = GEO["lon_max"]   # 2.450

# BBox "cœur de Cotonou" (ancienne bbox stricte, conservée pour information)
LAT_CORE_MIN, LAT_CORE_MAX = 6.340, 6.405
LON_CORE_MIN, LON_CORE_MAX = 2.340, 2.430

# Chemins
RAW_PATH       = PROJECT_ROOT / "data" / "sources" / "overpass" / "raw" / "billboards_osm_raw.geojson"
PROCESSED_DIR  = PROJECT_ROOT / "data" / "sources" / "overpass" / "processed"
OUTPUT_PATH    = PROCESSED_DIR / "billboards_osm_v1.csv"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

print("[00_load_billboards] Chargement du fichier OSM réel...")
print(f"  Fichier : {RAW_PATH.name}")

# ============================================================
# ÉTAPE 1 : LECTURE DU GEOJSON
#
# Explication :
# Un fichier GeoJSON est structuré ainsi :
# {
#   "type": "FeatureCollection",
#   "features": [
#     { "type": "Feature",
#       "properties": { "advertising": "billboard", "lit": "yes" },
#       "geometry": { "type": "Point", "coordinates": [lon, lat] }
#     }, ...
#   ]
# }
# On lit "features" pour accéder à chaque panneau.
# ============================================================

with open(RAW_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

features = data.get("features", [])
print(f"  ✓ {len(features)} panneaux trouvés dans le fichier brut")
print(f"  Exporté le : {data.get('timestamp', 'date inconnue')}")

# ============================================================
# ÉTAPE 2 : EXTRACTION DES DONNÉES
#
# Pour chaque panneau (= feature), on extrait :
# - ses coordonnées GPS (dans geometry.coordinates)
# - ses attributs (dans properties)
# ============================================================

rows = []

for feature in features:
    props = feature.get("properties", {})
    geom  = feature.get("geometry", {})

    # Coordonnées GPS
    # ATTENTION : dans GeoJSON, l'ordre est [longitude, latitude] (pas lat, lon !)
    coords = geom.get("coordinates", [None, None])
    lon = coords[0]
    lat = coords[1]

    if lon is None or lat is None:
        print(f"  ⚠ Panneau sans coordonnées ignoré : {feature.get('id')}")
        continue

    # Attributs du panneau
    osm_id       = props.get("@id", feature.get("id"))
    lit_raw      = props.get("lit", "no")
    is_lit       = 1 if str(lit_raw).lower() == "yes" else 0
    name         = props.get("name", None)
    has_name     = 1 if name else 0
    source_raw   = props.get("source", "")
    source_survey = 1 if "survey" in str(source_raw).lower() else 0
    advertising  = props.get("advertising", "billboard")

    # Classification géographique
    # On classe chaque panneau selon sa position par rapport aux zones connues
    in_core     = (LAT_CORE_MIN <= lat <= LAT_CORE_MAX and
                   LON_CORE_MIN <= lon <= LON_CORE_MAX)
    in_extended = (LAT_MIN <= lat <= LAT_MAX and
                   LON_MIN <= lon <= LON_MAX)

    if in_core:
        zone = "cotonou_core"       # dans la bbox V1 stricte
    elif in_extended:
        zone = "cotonou_extended"   # dans la bbox élargie (DEC-011)
    else:
        zone = "hors_zone"          # probablement Porto-Novo ou autre ville

    rows.append({
        "osm_id":        osm_id,
        "longitude":     lon,
        "latitude":      lat,
        "is_lit":        is_lit,
        "has_name":      has_name,
        "name":          name,
        "source_survey": source_survey,
        "zone":          zone,
        "advertising":   advertising,
    })

df = pd.DataFrame(rows)
print(f"\n[00_load_billboards] === RÉPARTITION GÉOGRAPHIQUE ===")
print(df["zone"].value_counts().to_string())

# ============================================================
# ÉTAPE 3 : FILTRE — ON GARDE UNIQUEMENT LES PANNEAUX COTONOU
#
# Décision DEC-012 : on exclut les panneaux "hors_zone"
# (probablement Porto-Novo, ~lon 2.67).
# Ils pourront être traités dans un projet séparé "Porto-Novo".
# ============================================================

df_filtered = df[df["zone"] != "hors_zone"].copy()

n_excluded = len(df) - len(df_filtered)
print(f"\n[00_load_billboards] Filtre géographique :")
print(f"  Panneaux retenus : {len(df_filtered)}")
print(f"  Panneaux exclus (hors zone) : {n_excluded}")

# ============================================================
# ÉTAPE 4 : AJOUT D'UN IDENTIFIANT INTERNE
#
# On crée un identifiant simple "B001", "B002"... pour notre usage interne.
# L'identifiant OSM (osm_id) est conservé pour traçabilité.
# ============================================================

df_filtered = df_filtered.reset_index(drop=True)
df_filtered.insert(0, "billboard_id", [f"B{i+1:03d}" for i in df_filtered.index])

# ============================================================
# ÉTAPE 5 : SAUVEGARDE
# ============================================================

df_filtered.to_csv(OUTPUT_PATH, index=False)
print(f"\n[00_load_billboards] ✓ CSV sauvegardé : {OUTPUT_PATH}")

# ============================================================
# RÉSUMÉ FINAL
# ============================================================

print("\n[00_load_billboards] === RÉSUMÉ DU DATASET RÉEL V1 ===")
print(df_filtered.to_string(index=False))

print(f"\n  Panneaux éclairés (is_lit=1)  : {df_filtered['is_lit'].sum()}")
print(f"  Panneaux nommés   (has_name=1) : {df_filtered['has_name'].sum()}")
print(f"  Issus d'enquête terrain        : {df_filtered['source_survey'].sum()}")
print(f"  Dans cœur Cotonou              : {(df_filtered['zone']=='cotonou_core').sum()}")
print(f"  Dans zone élargie uniquement   : {(df_filtered['zone']=='cotonou_extended').sum()}")

print(f"\n[00_load_billboards] ✓ Script terminé")
print("[00_load_billboards] → Prochaine étape : lancer 01_fetch_roads.py pour enrichir")
print("                        ces panneaux avec les features contextuelles OSM")
