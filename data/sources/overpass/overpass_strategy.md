# Stratégie de collecte — Overpass Turbo / OpenStreetMap

> **Statut :** Validé — Phase documentation initiale
> **Date :** 2026-03-16
> **Périmètre :** Cotonou, Bénin — BBox : lat [6.340–6.405] / lon [2.340–2.430]
> **Source unique traitée ici :** Overpass Turbo / OSM

---

## Table des matières

1. [Vue d'ensemble de la stratégie](#1-vue-densemble-de-la-stratégie)
2. [Types d'objets OSM à extraire](#2-types-dobjets-osm-à-extraire)
3. [Logique par étapes](#3-logique-par-étapes)
4. [Critères de qualité des données](#4-critères-de-qualité-des-données)
5. [Stratégie test avant automatisation](#5-stratégie-test-avant-automatisation)
6. [Plan de fallback si données insuffisantes](#6-plan-de-fallback-si-données-insuffisantes)

---

## 1. Vue d'ensemble de la stratégie

### Principe général

On procède en **4 phases séquentielles** :

```
Phase 1 : Exploration manuelle (Overpass Turbo dans le navigateur)
    ↓
Phase 2 : Validation de la qualité et de la couverture OSM sur Cotonou
    ↓
Phase 3 : Automatisation des requêtes (scripts Python via osmnx ou requests)
    ↓
Phase 4 : Calcul des features géographiques pour chaque panneau
```

### Pourquoi cette séquence ?

> **Règle senior :** On ne code pas avant de comprendre. Tester manuellement d'abord
> permet d'éviter d'écrire un script automatisé sur des données inexistantes ou incomplètes.

Si on automatise directement sans vérifier, on risque :
- D'écrire un script qui renvoie 0 résultats (parce que Cotonou est sous-cartographié)
- De construire des features basées sur des données vides → modèle invalide
- De perdre du temps à déboguer un script plutôt que la vraie donnée

---

## 2. Types d'objets OSM à extraire

OSM organise ses données en **3 types d'objets géométriques** :

| Type OSM | C'est quoi ? | Exemple |
|---|---|---|
| `node` | Un point GPS seul | Un arrêt de bus, une fontaine |
| `way` | Une ligne ou un polygone | Une route, un bâtiment |
| `relation` | Un groupe d'objets liés | Un quartier (ensemble de rues) |

### Objets prioritaires pour ce projet

#### PRIORITÉ 1 — Réseau routier (impact direct sur la visibilité)

| Tag OSM | Description | Importance |
|---|---|---|
| `highway=motorway` | Autoroute (rare à Cotonou) | Très haute |
| `highway=trunk` | Route nationale principale | Très haute |
| `highway=primary` | Route principale inter-quartiers | Haute |
| `highway=secondary` | Route secondaire | Haute |
| `highway=tertiary` | Rue de quartier | Moyenne |
| `highway=residential` | Rue résidentielle | Faible |
| `highway=unclassified` | Route non classifiée | À évaluer |

> **Hypothèse de travail (H2) :** Les panneaux à forte visibilité sont positionnés en priorité le long des
> `trunk`, `primary` et `secondary`. La distance à ces axes est la feature la plus discriminante.
> **Statut :** Confirmé partiellement par V1 (road_type_enc = top feature 26%)

#### PRIORITÉ 2 — Intersections et carrefours

Les intersections sont des points de ralentissement du trafic → plus d'attention disponible pour les panneaux.

On cherchera : les `node` ayant plusieurs `way` qui se croisent, plus les tags :
- `highway=traffic_signals` (feux tricolores)
- `highway=stop` (panneaux stop)

#### PRIORITÉ 3 — Points d'intérêt (POI) — proxy de densité piétonne

| Tag OSM | Type de lieu | Proxy pour |
|---|---|---|
| `amenity=marketplace` | Marché | Forte densité piétonne |
| `amenity=bus_station` / `highway=bus_stop` | Transport en commun | Flux piéton régulier |
| `shop=supermarket` | Supermarchés | Densité commerciale |
| `amenity=school` / `amenity=university` | Écoles | Flux d'entrée/sortie |
| `amenity=hospital` | Hôpital | Flux continu |
| `amenity=fuel` | Station-service | Points d'arrêt véhicules |
| `landuse=commercial` | Zone commerciale | Contexte commercial |
| `landuse=retail` | Zone de commerce de détail | Contexte commercial |

#### PRIORITÉ 4 — Limites administratives (quartiers)

| Tag OSM | Description |
|---|---|
| `admin_level=8` | Arrondissement / quartier |
| `admin_level=6` | Commune (Cotonou) |
| `place=suburb` | Nom de quartier informel |

> **Note importante :** Les limites administratives dans OSM pour Cotonou peuvent
> être incomplètes ou utiliser des niveaux différents des standards internationaux.
> Ce point sera vérifié en Phase 1 (exploration manuelle).

---

## 3. Logique par étapes

### Étape 1 — Exploration manuelle (Overpass Turbo navigateur)
**Durée estimée :** 1 à 2 heures
**Outil :** https://overpass-turbo.eu/

Actions à faire :
1. Visualiser le réseau routier de Cotonou → juger la densité de couverture
2. Vérifier si les quartiers ont des noms dans OSM
3. Chercher quelques marchés et arrêts de transport pour évaluer la complétude
4. Documenter les résultats dans `decisions_log.md`

Critère de validation : Les routes principales sont visibles et nommées.

---

### Étape 2 — Téléchargement des données routes (script Python)
**Fichier :** `scripts/01_fetch_roads.py`
**Librairie recommandée :** `osmnx` (spécialement conçue pour OSM)

Ce script :
- Télécharge le graphe routier complet de Cotonou
- Classe chaque route par type (`highway` tag)
- Sauvegarde en GeoJSON et CSV

**Sortie produite :**
```
data/sources/overpass/raw/roads_cotonou.geojson
data/sources/overpass/processed/roads_cotonou.csv
```

---

### Étape 3 — Téléchargement des POI (script Python)
**Fichier :** `scripts/02_fetch_pois.py`

Ce script :
- Interroge l'API Overpass pour chaque catégorie de POI
- Calcule la position GPS de chaque POI
- Sauvegarde avec les colonnes : id, name, amenity/shop, lat, lon

**Sortie produite :**
```
data/sources/overpass/raw/pois_cotonou.geojson
data/sources/overpass/processed/pois_cotonou.csv
```

---

### Étape 4 — Téléchargement des limites administratives
**Fichier :** `scripts/03_fetch_admin_boundaries.py`

Ce script :
- Télécharge les polygones des quartiers de Cotonou
- Crée une correspondance GPS → nom de quartier
- Permet d'assigner automatiquement un quartier à chaque panneau

**Sortie produite :**
```
data/sources/overpass/raw/admin_boundaries_cotonou.geojson
data/sources/overpass/processed/quartiers_cotonou.csv
```

---

### Étape 5 — Construction des features géographiques
**Fichier :** `scripts/04_build_features_from_osm.py`

Pour chaque panneau publicitaire (identifié par ses coordonnées GPS), ce script calcule :

| Feature calculée | Méthode de calcul |
|---|---|
| `road_type` | Type de la route la plus proche (nearest edge dans graphe OSM) |
| `distance_to_main_road_m` | Distance au trunk/primary le plus proche |
| `nb_intersections_200m` | Compte des nœuds d'intersection dans rayon 200m |
| `nb_pois_500m` | Compte de tous les POI dans rayon 500m |
| `nb_transport_stops_500m` | Compte des arrêts de transport dans rayon 500m |
| `nb_markets_500m` | Compte des marchés dans rayon 500m |
| `commercial_density_500m` | Compte des commerces dans rayon 500m |
| `quartier` | Nom du quartier (point-in-polygon avec les limites OSM) |
| `land_use_type` | Type d'occupation du sol à l'emplacement |

**Sortie produite :**
```
data/sources/overpass/processed/osm_features_per_billboard.csv
```
Ce fichier sera ensuite mergé avec le dataset principal dans `data/processed/`.

---

## 4. Critères de qualité des données

### Critères d'acceptation (une feature OSM est exploitable si...)

| Critère | Seuil minimum | Action si non atteint |
|---|---|---|
| Couverture routes principales | ≥ 80% du réseau visible sur la carte | Signaler comme lacune, ne pas utiliser |
| Nommage des quartiers | ≥ 10 quartiers identifiables | Utiliser une segmentation manuelle via grille GPS |
| POI marchés | ≥ 5 marchés identifiés | Compléter avec données alternatives (hors périmètre) |
| Complétude des attributs | ≤ 30% de valeurs manquantes par feature | Imputation ou abandon de la feature |

### Validation croisée
Quand c'est possible, on comparera les données OSM avec :
- La carte Google Maps (visuellement, pas via API)
- Notre connaissance du terrain (ou celle d'un expert local)

---

## 5. Stratégie de test avant automatisation

> **Règle d'or :** Tester toujours sur un sous-ensemble géographique avant de lancer
> sur toute la ville.

### Zone de test recommandée
**Quartier : Akpakpa / Boulevard du Port (zone connue, bien cartographiée)**

Coordonnées de test :
```
bbox_test = (6.355, 2.375, 6.375, 2.400)
# lat_min, lon_min, lat_max, lon_max
```

### Checklist de validation avant passage en production

- [ ] La requête retourne des résultats non vides
- [ ] Les coordonnées GPS sont cohérentes (restent dans Cotonou)
- [ ] Les types de routes sont correctement classifiés
- [ ] Les noms de rues sont présents pour ≥ 50% des voies principales
- [ ] Le GeoJSON peut être chargé dans Python (geopandas) sans erreur
- [ ] Les POI sont géographiquement cohérents (pas de marchés en mer)

---

## 6. Plan de fallback si données insuffisantes

> **Statut : Provisoire** — À réviser après Phase 1 d'exploration

Si OSM s'avère trop incomplet pour Cotonou :

| Problème | Solution de repli |
|---|---|
| Routes secondaires manquantes | Utiliser uniquement trunk + primary + secondary |
| Quartiers non identifiés dans OSM | Segmenter manuellement via grille GPS 1km² |
| Peu de POI commerciaux | Extraire depuis Google Maps Places (hors périmètre OSM) |
| Absence de limites administratives | Utiliser les données administratives GADM (hors périmètre OSM) |

---

*Stratégie définie le 2026-03-16. À compléter après Phase 1 (exploration manuelle).*
