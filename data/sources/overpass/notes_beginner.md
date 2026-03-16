# Notes pédagogiques — Overpass Turbo et OSM pour débutants

> **Pour qui ?** Pour Carine, qui débute en data géospatiale mais veut comprendre ce qu'elle fait.
> **Niveau :** Débutant motivé. Pas besoin de maths ni de code pour lire ce fichier.
> **Date :** 2026-03-16

---

## Table des matières

1. [C'est quoi une donnée géospatiale ?](#1-cest-quoi-une-donnée-géospatiale)
2. [C'est quoi OSM et pourquoi l'utiliser ?](#2-cest-quoi-osm-et-pourquoi-lutiliser)
3. [C'est quoi un tag OSM ?](#3-cest-quoi-un-tag-osm)
4. [C'est quoi Overpass Turbo ?](#4-cest-quoi-overpass-turbo)
5. [C'est quoi une BBox ?](#5-cest-quoi-une-bbox)
6. [C'est quoi GeoJSON ?](#6-cest-quoi-geojson)
7. [C'est quoi osmnx ?](#7-cest-quoi-osmnx)
8. [Pourquoi calculer des distances depuis des coordonnées GPS ?](#8-pourquoi-calculer-des-distances-depuis-des-coordonnées-gps)
9. [C'est quoi un point-in-polygon ?](#9-cest-quoi-un-point-in-polygon)
10. [Glossaire des termes techniques](#10-glossaire-des-termes-techniques)

---

## 1. C'est quoi une donnée géospatiale ?

Une donnée géospatiale, c'est une donnée qui **a une position sur la Terre**.

**Exemple concret :**
- Un panneau publicitaire a une adresse → on peut la convertir en coordonnées GPS (latitude, longitude)
- Une route a un tracé → c'est une ligne de points GPS
- Un quartier a des limites → c'est un polygone (forme fermée) de points GPS

Dans notre projet, presque toutes les données sont géospatiales :
les panneaux ont des coordonnées, les routes ont des tracés, les marchés ont des positions.

> **Analogie :** Imagine que chaque objet dans le monde réel porte une étiquette avec sa position GPS.
> La donnée géospatiale, c'est cette étiquette.

---

## 2. C'est quoi OSM et pourquoi l'utiliser ?

**OpenStreetMap (OSM)** = la carte du monde en libre accès.

C'est une énorme base de données géographiques créée par des millions de bénévoles à travers le monde.
Tout le monde peut lire les données, les télécharger, et les utiliser gratuitement.

**Pourquoi OSM et pas Google Maps ?**

| Critère | OSM | Google Maps |
|---|---|---|
| **Prix** | Gratuit, toujours | Payant au-delà d'un quota |
| **Accès aux données brutes** | Oui (on peut télécharger tout) | Non (API seulement) |
| **Utilisation dans un projet de recherche** | Autorisé (licence libre) | Restrictions commerciales |
| **Complétude** | Variable (bénévoles) | Meilleure (Google finance) |

**Conclusion :** OSM est le choix naturel pour un projet de recherche open source.
Pour les données de trafic temps réel (ce qu'on ne peut pas faire avec OSM), on envisagera
Google Maps dans une autre phase (hors périmètre ici).

---

## 3. C'est quoi un tag OSM ?

Dans OSM, chaque objet est décrit par des **tags** (étiquettes).
Un tag = une paire `clé=valeur`.

**Exemple :**
```
highway = primary     → c'est une route principale
name = "Boulevard de la Marina"
lanes = 4             → 4 voies de circulation
```

Ces tags permettent de filtrer exactement ce qu'on cherche.
Quand on écrit `way["highway"="primary"]` dans une requête Overpass,
on dit : *"Donne-moi toutes les lignes qui ont l'étiquette highway=primary"*.

**Les tags les plus utiles pour notre projet :**

| Tag | Ce que ça désigne |
|---|---|
| `highway=primary` | Route principale |
| `amenity=marketplace` | Marché |
| `highway=bus_stop` | Arrêt de bus |
| `admin_level=8` | Limite de quartier |
| `landuse=commercial` | Zone commerciale |

---

## 4. C'est quoi Overpass Turbo ?

**Overpass Turbo** est un site web qui permet d'interroger la base de données OSM
avec des questions précises, et de voir les résultats sur une carte.

**Comment l'utiliser :**
1. Aller sur https://overpass-turbo.eu/
2. Écrire une requête dans le panneau de gauche
3. Cliquer sur "Exécuter" (Run)
4. Voir les résultats sur la carte à droite
5. Exporter les données en GeoJSON ou JSON pour les utiliser dans Python

**Exemple visuel :**
```
[panneau gauche]              [carte droite]
way["highway"="primary"]  →  Des lignes bleues apparaissent
(bbox Cotonou)               sur la carte de Cotonou
out geom;                    = les routes principales
```

C'est l'outil qu'on utilise **en Phase 1** pour explorer manuellement avant de coder.

---

## 5. C'est quoi une BBox ?

**BBox** = Bounding Box = Boîte de délimitation.

C'est un rectangle défini par 4 coordonnées GPS qui délimite une zone géographique :

```
BBox Cotonou dans ce projet :
  ┌─────────────────────────────────┐ ← lat_max = 6.405
  │                                 │
  │          C O T O N O U          │
  │                                 │
  └─────────────────────────────────┘ ← lat_min = 6.340
  ↑                                 ↑
lon_min = 2.340              lon_max = 2.430
```

Dans les requêtes Overpass, on écrit toujours la bbox dans cet ordre :
`(lat_min, lon_min, lat_max, lon_max)`

Donc : `(6.340, 2.340, 6.405, 2.430)`

> **Astuce :** lat = latitude = axe nord-sud (comme les lignes horizontales sur un globe)
> lon = longitude = axe est-ouest (comme les lignes verticales)

---

## 6. C'est quoi GeoJSON ?

**GeoJSON** = un format de fichier texte pour stocker des données géographiques.

C'est comme un fichier CSV, mais pour des formes géographiques (points, lignes, polygones).

**Exemple de GeoJSON pour un marché :**
```json
{
  "type": "Feature",
  "geometry": {
    "type": "Point",
    "coordinates": [2.384, 6.362]
  },
  "properties": {
    "name": "Grand Marché de Cotonou",
    "amenity": "marketplace"
  }
}
```

- `coordinates` = [longitude, latitude] (attention, c'est dans cet ordre en GeoJSON !)
- `properties` = les attributs de l'objet (nom, type...)

**Dans Python**, on ouvre un GeoJSON avec la bibliothèque `geopandas` :
```python
import geopandas as gpd
marches = gpd.read_file("pois_cotonou.geojson")
```
C'est comme `pandas.read_csv()` mais pour des données géographiques.

---

## 7. C'est quoi osmnx ?

**osmnx** est une bibliothèque Python qui facilite le travail avec OSM.

Sans osmnx, il faudrait :
1. Écrire une requête Overpass
2. Télécharger le fichier manuellement
3. Analyser le JSON soi-même
4. Calculer les distances à la main

Avec osmnx, c'est beaucoup plus simple :

```python
import osmnx as ox

# Télécharger le réseau routier de Cotonou en 2 lignes
G = ox.graph_from_bbox(6.340, 2.340, 6.405, 2.430, network_type='drive')
edges = ox.graph_to_gdfs(G, nodes=False)  # convertit en tableau
```

osmnx gère automatiquement :
- L'envoi de la requête à Overpass
- La conversion en format utilisable par Python
- Le calcul de distances et de plus courts chemins

> **Analogie :** osmnx est comme un chauffeur de taxi qui connaît toutes les routes.
> Tu lui dis "amène-moi au marché le plus proche" et il calcule le chemin.

---

## 8. Pourquoi calculer des distances depuis des coordonnées GPS ?

Dans notre dataset, on veut savoir : *"Ce panneau est-il loin d'une route principale ?"*

Pour répondre, on calcule la distance entre deux points GPS.

**La formule utilisée :** Haversine (distance sur une sphère)

> **Pas besoin de comprendre la formule !** La bibliothèque Python `geopy` la calcule automatiquement.

```python
from geopy.distance import geodesic

point_panneau = (6.362, 2.384)    # (lat, lon) du panneau
point_route = (6.365, 2.390)      # (lat, lon) du point le plus proche sur la route

distance = geodesic(point_panneau, point_route).meters
# Résultat : distance en mètres
```

**Dans le dataset :**
```
panneau_id | latitude | longitude | distance_to_main_road_m
P001       | 6.362    | 2.384     | 45.7
P002       | 6.370    | 2.395     | 312.4
```

→ P001 est à 45m d'une route principale = bonne visibilité
→ P002 est à 312m = moins visible depuis cette route

---

## 9. C'est quoi un point-in-polygon ?

**Point-in-polygon** = "Ce point GPS est-il à l'intérieur de ce polygone ?"

C'est la question qu'on pose pour savoir dans quel quartier se trouve un panneau.

**Exemple :**
```
Polygone = limites du quartier "Akpakpa" (un grand rectangle approximatif)
Point = coordonnées GPS du panneau P001

Question : est-ce que P001 est dans Akpakpa ?
Réponse : Oui → billboard["quartier"] = "Akpakpa"
```

En Python, `geopandas` fait ça automatiquement avec `sjoin` (spatial join) :

```python
import geopandas as gpd

panneaux = gpd.GeoDataFrame(...)      # nos panneaux
quartiers = gpd.read_file("quartiers_cotonou.geojson")  # les polygones

# Jointure spatiale : assigne un quartier à chaque panneau
result = gpd.sjoin(panneaux, quartiers, how="left", predicate="within")
```

> **Analogie :** Imagine que tu places des punaises (les panneaux) sur une carte découpée
> en régions colorées (les quartiers). Le point-in-polygon, c'est automatiquement demander
> "de quelle couleur est la région où j'ai planté ma punaise ?".

---

## 10. Glossaire des termes techniques

| Terme | Définition simple |
|---|---|
| **API** | Interface pour interroger un service web automatiquement (comme poser une question à un serveur) |
| **BBox** | Rectangle GPS qui délimite une zone de recherche |
| **GeoDataFrame** | Tableau pandas avec une colonne de géométrie (points, lignes, polygones) |
| **GeoJSON** | Format de fichier pour stocker des formes géographiques |
| **Géocodage** | Convertir une adresse texte en coordonnées GPS |
| **Graphe routier** | Représentation d'un réseau de routes comme un ensemble de nœuds (intersections) et d'arêtes (tronçons) |
| **Haversine** | Formule mathématique pour calculer une distance entre deux points GPS sur une sphère |
| **Node (OSM)** | Point GPS simple dans la base OSM |
| **osmnx** | Bibliothèque Python pour travailler avec les données OSM |
| **Overpass API** | Service web d'OSM pour faire des requêtes géographiques |
| **Overpass QL** | Le langage de requête d'Overpass Turbo |
| **Point-in-polygon** | Déterminer si un point est à l'intérieur d'un polygone |
| **Projection** | Façon de "aplatir" la Terre sphérique sur une carte plane |
| **Relation (OSM)** | Groupe d'objets OSM liés (ex : un quartier = plusieurs rues) |
| **Tag** | Étiquette clé=valeur qui décrit un objet dans OSM |
| **Way (OSM)** | Ligne ou polygone dans OSM (route, bâtiment...) |

---

*Ce fichier est un support d'apprentissage permanent. Il sera mis à jour au fur et à mesure que de nouveaux concepts apparaissent dans le projet.*
