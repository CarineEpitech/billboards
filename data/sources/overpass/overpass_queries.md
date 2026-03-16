# Requêtes Overpass Turbo — Cotonou, Bénin

> **Statut :** Validé — Prêtes pour test manuel
> **Date :** 2026-03-16
> **Comment utiliser ce fichier :** Copier-coller chaque requête sur https://overpass-turbo.eu/
> **BBox Cotonou :** sud=6.340, ouest=2.340, nord=6.405, est=2.430

---

## Comment lire une requête Overpass

Le langage Overpass QL (Query Language) ressemble à une liste d'instructions simples.
Voici les éléments de base :

```
[out:json]          → format de sortie : JSON (lisible par Python)
[timeout:60]        → on attend max 60 secondes
{{bbox}}            → la zone géographique visible sur la carte (ou une bbox fixe)

node[...]           → chercher des points
way[...]            → chercher des lignes / polygones
relation[...]       → chercher des groupes d'objets

out geom;           → retourner les résultats avec leurs coordonnées GPS
```

> **Analogie :** C'est comme chercher dans une base de données. `node[amenity=marketplace]`
> signifie : *"Trouve tous les points qui ont l'attribut amenity égal à marketplace"*.

---

## INDEX DES REQUÊTES

| # | Nom | Usage | Priorité |
|---|---|---|---|
| Q1 | Routes principales de Cotonou | Feature `road_type` + `distance_to_main_road_m` | HAUTE |
| Q2 | Tous les carrefours avec feux | Feature `nb_intersections_200m` | HAUTE |
| Q3 | Marchés et zones commerciales | Proxy `pedestrian_density_score` | HAUTE |
| Q4 | Arrêts de bus et transport | Proxy `pedestrian_density_score` | HAUTE |
| Q5 | Limites de quartiers (admin) | Feature `quartier` | HAUTE |
| Q6 | Écoles et universités | Feature `nb_facilities_500m` | MOYENNE |
| Q7 | Hôpitaux et centres de santé | Feature `nb_facilities_500m` | MOYENNE |
| Q8 | Stations-service | Feature `nb_gas_stations_500m` | MOYENNE |
| Q9 | Occupation du sol (land use) | Feature `land_use_type` | MOYENNE |
| Q10 | Panneaux publicitaires OSM (si existants) | Variable cible potentielle | BASSE |

---

## Q1 — Routes principales de Cotonou

### La requête
```overpassql
[out:json][timeout:60];
(
  way["highway"="trunk"](6.340,2.340,6.405,2.430);
  way["highway"="primary"](6.340,2.340,6.405,2.430);
  way["highway"="secondary"](6.340,2.340,6.405,2.430);
  way["highway"="tertiary"](6.340,2.340,6.405,2.430);
);
out geom;
```

### Explication ligne par ligne

| Ligne | Ce qu'elle fait |
|---|---|
| `[out:json]` | Je veux le résultat en format JSON (format lisible par Python) |
| `[timeout:60]` | Si ça prend plus de 60 secondes, on arrête (évite de bloquer le serveur) |
| `way["highway"="trunk"]` | Cherche toutes les voies (`way`) dont l'attribut `highway` vaut `trunk` (route nationale) |
| `(6.340,2.340,6.405,2.430)` | Dans cette zone GPS : c'est notre boîte Cotonou |
| `out geom;` | Retourne les résultats avec les coordonnées GPS de chaque point |

### Ce que ça retourne
Une liste de routes avec pour chaque route :
- Son identifiant OSM unique
- Son type (`trunk`, `primary`, etc.)
- Son nom si disponible (ex: "Boulevard de la Marina")
- La liste de ses points GPS (pour calculer des distances)

### Ce que ça produit dans le dataset
```python
# Dans le script Python, on utilisera ces données pour :
# 1. Identifier le type de la route la plus proche de chaque panneau
# 2. Calculer la distance entre un panneau et la route principale la plus proche
billboard["road_type"] = nearest_road_type(billboard_lat, billboard_lon, roads_gdf)
billboard["distance_to_main_road_m"] = distance_to_nearest(billboard_coords, main_roads)
```

---

## Q2 — Carrefours avec feux tricolores

### La requête
```overpassql
[out:json][timeout:60];
(
  node["highway"="traffic_signals"](6.340,2.340,6.405,2.430);
  node["highway"="crossing"](6.340,2.340,6.405,2.430);
  node["highway"="stop"](6.340,2.340,6.405,2.430);
);
out body;
```

### Explication
- `node` = un point GPS simple (ici un carrefour, c'est juste un point sur la carte)
- `highway=traffic_signals` = feu de signalisation (les véhicules s'arrêtent = plus d'attention)
- `highway=crossing` = passage piéton (flux de piétons = plus de regards)
- `out body;` = retourne les données sans les géométries détaillées (économise de la bande passante)

### Ce que ça produit dans le dataset
```python
# Compte le nombre de feux/croisements dans un rayon autour de chaque panneau
billboard["nb_intersections_200m"] = count_pois_in_radius(
    billboard_coords, traffic_nodes, radius_m=200
)
```

> **Pourquoi 200m ?** Un automobiliste à 50km/h parcourt 200m en ~15 secondes.
> C'est le temps d'attention disponible avant et après un feu.

---

## Q3 — Marchés et zones commerciales

### La requête
```overpassql
[out:json][timeout:60];
(
  node["amenity"="marketplace"](6.340,2.340,6.405,2.430);
  way["amenity"="marketplace"](6.340,2.340,6.405,2.430);
  node["landuse"="retail"](6.340,2.340,6.405,2.430);
  way["landuse"="commercial"](6.340,2.340,6.405,2.430);
  node["shop"="supermarket"](6.340,2.340,6.405,2.430);
  node["shop"="mall"](6.340,2.340,6.405,2.430);
);
out geom;
```

### Explication
- `amenity=marketplace` = marché (Grand Marché, marché Ganhi, etc.)
- `landuse=retail` = zone de commerce de détail
- `landuse=commercial` = zone commerciale générale
- `shop=supermarket` = supermarchés comme Erevan, Score

> **Analogie :** On cherche tous les endroits où les gens font leurs courses.
> Ces lieux génèrent un fort passage piéton et vehiculaire = meilleure visibilité.

### Ce que ça produit dans le dataset
```python
billboard["nb_markets_500m"] = count_pois_in_radius(billboard_coords, markets, 500)
billboard["commercial_density_500m"] = count_pois_in_radius(billboard_coords, shops, 500)
```

---

## Q4 — Arrêts de bus et de transport

### La requête
```overpassql
[out:json][timeout:60];
(
  node["highway"="bus_stop"](6.340,2.340,6.405,2.430);
  node["amenity"="bus_station"](6.340,2.340,6.405,2.430);
  node["public_transport"="stop_position"](6.340,2.340,6.405,2.430);
  node["public_transport"="platform"](6.340,2.340,6.405,2.430);
);
out body;
```

### Explication
Les arrêts de transport en commun sont des points où les gens **attendent** :
ils ont donc les yeux disponibles pour regarder les panneaux.

- `highway=bus_stop` = arrêt de bus classique
- `amenity=bus_station` = gare routière (fort trafic)
- `public_transport=platform` = quai de transport (zémidjan, bus SOTRA...)

### Ce que ça produit dans le dataset
```python
billboard["nb_transport_stops_500m"] = count_pois_in_radius(
    billboard_coords, transport_stops, 500
)
# Cette variable sera intégrée dans pedestrian_density_score (V2)
```

---

## Q5 — Limites de quartiers (administrative)

### La requête
```overpassql
[out:json][timeout:60];
(
  relation["boundary"="administrative"]["admin_level"="8"](6.340,2.340,6.405,2.430);
  relation["boundary"="administrative"]["admin_level"="7"](6.340,2.340,6.405,2.430);
  relation["place"="suburb"](6.340,2.340,6.405,2.430);
  node["place"="suburb"](6.340,2.340,6.405,2.430);
  node["place"="neighbourhood"](6.340,2.340,6.405,2.430);
);
out geom;
```

### Explication
- `relation["boundary"="administrative"]` = un quartier/arrondissement dessiné dans OSM
- `admin_level=8` = niveau communal dans la hiérarchie OSM (varie selon les pays)
- `place=suburb` = nom de lieu résidentiel informel (très utilisé en Afrique)
- `place=neighbourhood` = quartier au sens informel

> **Note :** Au Bénin, les niveaux administratifs OSM peuvent ne pas être standardisés.
> On teste admin_level=7 et admin_level=8 pour voir lequel correspond aux arrondissements.

### Ce que ça produit dans le dataset
```python
# Point-in-polygon : pour chaque panneau, on trouve dans quel quartier il se trouve
billboard["quartier"] = spatial_join(billboard_coords, quartiers_polygons)
# Résultat : "Akpakpa", "Cadjehoun", "Fidjrossè", "Haie Vive", etc.
```

---

## Q6 — Écoles et universités

### La requête
```overpassql
[out:json][timeout:60];
(
  node["amenity"="school"](6.340,2.340,6.405,2.430);
  way["amenity"="school"](6.340,2.340,6.405,2.430);
  node["amenity"="university"](6.340,2.340,6.405,2.430);
  node["amenity"="college"](6.340,2.340,6.405,2.430);
);
out geom;
```

### Ce que ça produit dans le dataset
```python
billboard["nb_schools_500m"] = count_pois_in_radius(billboard_coords, schools, 500)
# Matin et soir : fort flux de parents et d'élèves
```

---

## Q7 — Hôpitaux et centres de santé

### La requête
```overpassql
[out:json][timeout:60];
(
  node["amenity"="hospital"](6.340,2.340,6.405,2.430);
  way["amenity"="hospital"](6.340,2.340,6.405,2.430);
  node["amenity"="clinic"](6.340,2.340,6.405,2.430);
  node["amenity"="health_post"](6.340,2.340,6.405,2.430);
);
out geom;
```

### Ce que ça produit dans le dataset
```python
billboard["nb_health_facilities_500m"] = count_pois_in_radius(billboard_coords, health, 500)
```

---

## Q8 — Stations-service

### La requête
```overpassql
[out:json][timeout:60];
(
  node["amenity"="fuel"](6.340,2.340,6.405,2.430);
  way["amenity"="fuel"](6.340,2.340,6.405,2.430);
);
out geom;
```

### Ce que ça produit dans le dataset
```python
billboard["nb_fuel_stations_500m"] = count_pois_in_radius(billboard_coords, fuel, 500)
# Les stations-service = arrêt de véhicules + attention disponible
```

---

## Q9 — Occupation du sol (Land Use)

### La requête
```overpassql
[out:json][timeout:60];
(
  way["landuse"](6.340,2.340,6.405,2.430);
  relation["landuse"](6.340,2.340,6.405,2.430);
);
out geom;
```

### Valeurs importantes du tag `landuse`

| Valeur | Signification | Impact visibilité |
|---|---|---|
| `commercial` | Zone commerciale | Fort (beaucoup de passages) |
| `retail` | Commerce de détail | Fort |
| `residential` | Zone résidentielle | Modéré |
| `industrial` | Zone industrielle | Faible (peu de piétons) |
| `cemetery` | Cimetière | Très faible |

### Ce que ça produit dans le dataset
```python
billboard["land_use_type"] = point_in_polygon(billboard_coords, landuse_polygons)
# Variable catégorielle → sera encodée comme quartier_enc
```

---

## Q10 — Panneaux publicitaires dans OSM (si existants)

> **Statut : BASSE PRIORITÉ** — Données très probablement absentes à Cotonou

### La requête
```overpassql
[out:json][timeout:60];
(
  node["advertising"](6.340,2.340,6.405,2.430);
  way["advertising"](6.340,2.340,6.405,2.430);
  node["tourism"="artwork"]["artwork_type"="sculpture"](6.340,2.340,6.405,2.430);
);
out geom;
```

### Pourquoi basse priorité ?

> **Hypothèse de travail (H3) :** Les panneaux publicitaires ne sont pas taggés dans OSM Cotonou.
> OSM au Bénin est principalement cartographié pour les routes et les bâtiments majeurs.
> Les panneaux publicitaires sont rarement renseignés même dans les pays bien couverts.

Cette requête sera quand même testée — si elle retourne des résultats, c'est un bonus.

---

## Requête complète consolidée (pour téléchargement unique)

Pour collecter tout en une seule requête (utile pour éviter de surcharger le serveur) :

```overpassql
[out:json][timeout:120];
(
  // Routes
  way["highway"~"trunk|primary|secondary|tertiary"](6.340,2.340,6.405,2.430);

  // Carrefours
  node["highway"~"traffic_signals|crossing|stop"](6.340,2.340,6.405,2.430);

  // Marchés et commercial
  node["amenity"="marketplace"](6.340,2.340,6.405,2.430);
  way["amenity"="marketplace"](6.340,2.340,6.405,2.430);
  way["landuse"~"commercial|retail"](6.340,2.340,6.405,2.430);
  node["shop"~"supermarket|mall"](6.340,2.340,6.405,2.430);

  // Transport
  node["highway"="bus_stop"](6.340,2.340,6.405,2.430);
  node["amenity"="bus_station"](6.340,2.340,6.405,2.430);

  // Équipements publics
  way["amenity"~"school|university|hospital"](6.340,2.340,6.405,2.430);
  node["amenity"~"school|university|hospital|fuel"](6.340,2.340,6.405,2.430);

  // Administratif
  relation["boundary"="administrative"]["admin_level"~"7|8"](6.340,2.340,6.405,2.430);
  node["place"~"suburb|neighbourhood"](6.340,2.340,6.405,2.430);

  // Land use
  way["landuse"](6.340,2.340,6.405,2.430);
);
out geom;
```

> **Avertissement :** Cette requête consolidée peut être lente (>60s). Utiliser `[timeout:120]`.
> Si elle expire, la découper en requêtes séparées (Q1 à Q9 individuellement).

---

---

## MISE À JOUR — 2026-03-16 (Option B : élargissement des requêtes advertising)

> **Contexte :** Le premier export OSM (`advertising=billboard`) a retourné 11 panneaux.
> C'est insuffisant pour un modèle ML. On élargit à tous les sous-types de tags `advertising`.
> Décision liée : DEC-013.

---

## Q11 — Panneaux de type `board` (panneaux fixes classiques)

### La requête
```overpassql
[out:json][timeout:60];
(
  node["advertising"="board"](6.330,2.330,6.430,2.450);
  way["advertising"="board"](6.330,2.330,6.430,2.450);
);
out geom;
```

### Explication
`advertising=board` désigne les panneaux fixes de taille moyenne, souvent muraux
ou sur poteaux, différents des grands `billboard`. En Afrique de l'Ouest,
beaucoup de supports publicitaires correspondent à ce tag plutôt qu'à `billboard`.

### Ce que ça produit
Des panneaux supplémentaires à ajouter à `billboards_osm_raw.geojson`.

---

## Q12 — Écrans digitaux (`screen`)

### La requête
```overpassql
[out:json][timeout:60];
(
  node["advertising"="screen"](6.330,2.330,6.430,2.450);
  way["advertising"="screen"](6.330,2.330,6.430,2.450);
);
out geom;
```

### Explication
`advertising=screen` = écrans LED/LCD publicitaires numériques.
Correspond à `panel_type=digital` dans notre modèle V1. Feature `is_lit=1` implicite.

---

## Q13 — Colonnes publicitaires (`column`)

### La requête
```overpassql
[out:json][timeout:60];
(
  node["advertising"="column"](6.330,2.330,6.430,2.450);
  node["advertising"="poster"](6.330,2.330,6.430,2.450);
  node["advertising"="totem"](6.330,2.330,6.430,2.450);
);
out body;
```

### Explication
- `column` = colonne Morris ou similaire (cylindrique, plusieurs affiches)
- `poster` = panneau d'affichage de petite taille (4m² typiquement)
- `totem` = structure verticale en façade (fréquent devant les commerces)

---

## Q14 — Recherche large : tous les objets `advertising` (requête filet)

> **Usage :** Pour ne rien manquer. À utiliser après les requêtes ciblées pour vérifier
> s'il n'existe pas d'autres sous-types présents à Cotonou.

### La requête
```overpassql
[out:json][timeout:60];
(
  node["advertising"](6.330,2.330,6.430,2.450);
  way["advertising"](6.330,2.330,6.430,2.450);
);
out geom;
```

### Explication
`["advertising"]` sans valeur = *"tout objet qui a un tag advertising, quelle que soit sa valeur"*.
Permet de découvrir des sous-types inattendus (ex: `advertising=banner`, `advertising=sign`...).

### Ce que ça produit
Une liste exhaustive de tous les supports publicitaires dans OSM autour de Cotonou.
On pourra ensuite grouper par type et décider lesquels inclure dans le dataset.

---

## Q15 — Requête consolidée advertising (tous types, nouvelle bbox)

> Remplace la requête consolidée précédente pour utiliser la **nouvelle bbox élargie**.

```overpassql
[out:json][timeout:90];
(
  // Tous les types de supports publicitaires
  node["advertising"](6.330,2.330,6.430,2.450);
  way["advertising"](6.330,2.330,6.430,2.450);

  // Routes principales (nouvelle bbox)
  way["highway"~"trunk|primary|secondary|tertiary"](6.330,2.330,6.430,2.450);

  // Marchés et commercial
  node["amenity"="marketplace"](6.330,2.330,6.430,2.450);
  way["amenity"="marketplace"](6.330,2.330,6.430,2.450);
  way["landuse"~"commercial|retail"](6.330,2.330,6.430,2.450);

  // Transport
  node["highway"="bus_stop"](6.330,2.330,6.430,2.450);
  node["amenity"="bus_station"](6.330,2.330,6.430,2.450);

  // Administratif
  relation["boundary"="administrative"]["admin_level"~"7|8"](6.330,2.330,6.430,2.450);
  node["place"~"suburb|neighbourhood"](6.330,2.330,6.430,2.450);
);
out geom;
```

> **Note :** BBox mise à jour de `(6.340,2.340,6.405,2.430)` à `(6.330,2.330,6.430,2.450)`
> suite à DEC-011. L'ancienne requête consolidée reste dans l'historique ci-dessus pour traçabilité.

---

*Dernière mise à jour : 2026-03-16. Requêtes Q11–Q15 ajoutées suite à l'analyse du premier export OSM.*
