# Catalogue des features — Projet Billboard Cotonou

> **Statut :** Validé — Version 1.0
> **Date de création :** 2026-03-18
> **Périmètre :** Toutes les features du projet, toutes sources confondues
> **Cohérence :** Ce document couvre les features V1 (simulées), les features OSM
> (en cours de collecte), et les features futures identifiées (autres sources).
> **Public visé :** Carine — débutante motivée, cherche à comprendre l'origine
> et l'utilité réelle de chaque variable.

---

## Table des matières

1. [Introduction](#1-introduction)
2. [Principes généraux — comment lire ce document](#2-principes-généraux)
3. [Tableau synthétique global](#3-tableau-synthétique-global)
4. [Détail par famille de variables](#4-détail-par-famille-de-variables)
   - [F1 — Accessibilité routière](#f1--accessibilité-routière)
   - [F2 — Structure du réseau / Topologie](#f2--structure-du-réseau--topologie)
   - [F3 — Attractivité urbaine (POI)](#f3--attractivité-urbaine-poi)
   - [F4 — Densité humaine](#f4--densité-humaine)
   - [F5 — Densité bâtie / Morphologie urbaine](#f5--densité-bâtie--morphologie-urbaine)
   - [F6 — Caractéristiques du panneau / Exposition](#f6--caractéristiques-du-panneau--exposition)
   - [F7 — Saturation / Concurrence](#f7--saturation--concurrence)
   - [F8 — Contexte spatial général](#f8--contexte-spatial-général)
   - [F9 — Variables dérivées / Composites](#f9--variables-dérivées--composites)
5. [Features exploitables à court terme pour Cotonou/Littoral](#5-features-exploitables-à-court-terme-pour-cotonouttoral)
6. [Features théoriquement intéressantes mais difficiles sans terrain](#6-features-théoriquement-intéressantes-mais-difficiles-sans-terrain)
7. [Recommandations pour Cotonou / Littoral](#7-recommandations-pour-cotonou--littoral)
8. [Variables à prioriser immédiatement](#8-variables-à-prioriser-immédiatement)
9. [Variables à garder pour plus tard](#9-variables-à-garder-pour-plus-tard)
10. [Conclusion pratique](#10-conclusion-pratique)

---

## 1. Introduction

Ce document répond à une question fondamentale du projet :

> *"Quelles variables utiliser pour estimer la visibilité d'un panneau publicitaire à Cotonou, et comment les obtenir sans aller sur le terrain ?"*

### Pourquoi ce catalogue est important

En machine learning, la qualité des **features** (variables d'entrée du modèle) détermine
la qualité des prédictions. Un mauvais modèle avec de bonnes features surpasse souvent
un modèle sophistiqué avec de mauvaises features.

Ce catalogue sert à :
1. **Comprendre** ce qu'on mesure et pourquoi
2. **Décider** quelles variables construire en priorité
3. **Tracer** l'origine de chaque variable (importante pour la reproductibilité)
4. **Éviter** de perdre du temps sur des variables inaccessibles ou peu utiles

### État actuel du projet (au 2026-03-18)

| Phase | Description | État |
|---|---|---|
| V1 | 23 features simulées, modèle RF entraîné | ✅ Terminé |
| V2 (en cours) | Remplacement progressif par données OSM réelles | 🔄 En cours |
| V3 | Features avancées (satellite, trafic temps réel) | 📋 Planifié |

---

## 2. Principes généraux

### Types de variables

Ce document distingue 4 types de variables :

| Type | Définition | Exemple |
|---|---|---|
| **Brute** | Donnée directement observable ou téléchargeable | Coordonnées GPS, type de route |
| **Proxy** | Variable qu'on ne peut pas mesurer directement → on l'approxime par autre chose | Nombre de marchés dans 500m ≈ proxy de densité piétonne |
| **Dérivée** | Calculée à partir d'autres variables | ratio_surface_hauteur = size_m2 / height_m |
| **Composite** | Combinaison de plusieurs variables avec une formule | score_accessibilite = dist_route + dist_centre |

> **Règle clé :** Un proxy n'est pas une mauvaise variable — c'est une approximation
> honnête. L'important est de documenter qu'il s'agit d'un proxy et de connaître ses limites.

### Niveaux spatiaux

| Niveau | C'est quoi | Exemple |
|---|---|---|
| **Point** | Un seul endroit précis (coordonnées GPS) | La position d'un panneau |
| **Buffer** | Cercle autour d'un point | Les POI à 500m d'un panneau |
| **Segment** | Un tronçon de route | La route la plus proche |
| **Intersection** | Le nœud où plusieurs routes se croisent | Un carrefour |
| **Zone** | Un polygone géographique | Un quartier, une zone commerciale |

### Échelle de difficulté de collecte

| Symbole | Niveau | Signification |
|---|---|---|
| ★☆☆ | Facile | Téléchargeable immédiatement, outil simple |
| ★★☆ | Moyen | Nécessite du code Python ou une étape de calcul |
| ★★★ | Difficile | Dépend d'une source payante, d'un accès terrain, ou d'un traitement complexe |

---

## 3. Tableau synthétique global

> Vue d'ensemble de **toutes les features** du projet, classées par famille.
> Les features V1 (simulées) sont marquées `[V1]`. Les features OSM sont `[OSM]`. Les features futures sont `[V3]`.

| # | Famille | Nom de la variable | Description courte | Statut var. | Source | Difficulté | Priorité |
|---|---|---|---|---|---|---|---|
| 1 | Accessibilité routière | `road_type` | Type de la route la plus proche | Brute | OSM | ★☆☆ | Immédiat |
| 2 | Accessibilité routière | `distance_to_main_road_m` | Distance en m à la route principale | Brute | OSM (calcul) | ★★☆ | Immédiat |
| 3 | Accessibilité routière | `road_lanes` | Nombre de voies de la route | Brute | OSM (partiel) | ★★☆ | V2 |
| 4 | Topologie réseau | `nb_intersections_200m` | Nb de carrefours dans rayon 200m | Dérivée | OSM | ★★☆ | Immédiat |
| 5 | Topologie réseau | `has_traffic_signals_200m` | Présence de feux tricolores | Brute | OSM | ★☆☆ | V2 |
| 6 | Topologie réseau | `degree_nearest_intersection` | Nb de branches au carrefour le plus proche | Dérivée | OSM (calcul réseau) | ★★★ | V3 |
| 7 | Attractivité urbaine | `nb_markets_500m` | Nb de marchés dans rayon 500m | Proxy | OSM | ★☆☆ | Immédiat |
| 8 | Attractivité urbaine | `nb_transport_stops_500m` | Nb d'arrêts de transport dans 500m | Proxy | OSM | ★☆☆ | Immédiat |
| 9 | Attractivité urbaine | `nb_schools_500m` | Nb d'écoles et universités dans 500m | Proxy | OSM | ★☆☆ | Immédiat |
| 10 | Attractivité urbaine | `nb_health_facilities_500m` | Nb de structures de santé dans 500m | Proxy | OSM | ★☆☆ | V2 |
| 11 | Attractivité urbaine | `commercial_density_500m` | Nb de commerces dans 500m | Proxy | OSM | ★☆☆ | Immédiat |
| 12 | Attractivité urbaine | `nb_fuel_stations_500m` | Nb de stations-service dans 500m | Proxy | OSM | ★☆☆ | V2 |
| 13 | Densité humaine | `pedestrian_density_score` | Score 0-100 de fréquentation piétonne | Proxy composite | OSM (calculé) | ★★☆ | Immédiat |
| 14 | Densité humaine | `population_density_500m` | Nb d'habitants estimés dans 500m | Brute | WorldPop | ★★☆ | V2 |
| 15 | Densité humaine | `traffic_flow_estim` | Flux estimé de véhicules/jour | Proxy | Simulation / API | ★★★ | V2 |
| 16 | Morphologie urbaine | `land_use_type` | Type d'occupation du sol | Brute | OSM | ★★☆ | V2 |
| 17 | Morphologie urbaine | `building_density_500m` | Densité de bâtiments dans 500m | Proxy | OSM / GHSL | ★★★ | V3 |
| 18 | Morphologie urbaine | `is_coastal` | À moins de 1km de la mer/lagune | Dérivée | Calcul GPS | ★☆☆ | V2 |
| 19 | Panneau / Exposition | `panel_type` → `panel_type_enc` | Type de support (digital, statique…) | Brute | Terrain / OSM | ★☆☆ | Immédiat |
| 20 | Panneau / Exposition | `is_lit` | Panneau éclairé la nuit (lit=yes) | Brute | OSM | ★☆☆ | Immédiat |
| 21 | Panneau / Exposition | `height_m` | Hauteur du panneau en mètres | Brute | Terrain | ★★★ | V2 |
| 22 | Panneau / Exposition | `size_m2` | Surface du panneau en m² | Brute | Terrain | ★★★ | V2 |
| 23 | Panneau / Exposition | `hours_of_daylight_exposure` | Heures d'exposition solaire estimées | Proxy | Simulation | ★★☆ | V2 |
| 24 | Saturation | `competition_radius_500m` | Nb de panneaux concurrents dans 500m | Brute (partiel) | OSM (partiel) | ★★☆ | V2 |
| 25 | Saturation | `indice_saturation` | Competition × densité piétonne | Composite | Calculé | ★☆☆ | V2 |
| 26 | Contexte spatial | `quartier` → `quartier_enc` | Nom du quartier | Brute | OSM / Admin | ★☆☆ | Immédiat |
| 27 | Contexte spatial | `latitude` | Coordonnée GPS nord-sud | Brute | GPS / OSM | ★☆☆ | Immédiat |
| 28 | Contexte spatial | `longitude` | Coordonnée GPS est-ouest | Brute | GPS / OSM | ★☆☆ | Immédiat |
| 29 | Contexte spatial | `distance_to_center_km` | Distance au centre-ville en km | Dérivée | Calcul GPS | ★☆☆ | Immédiat |
| 30 | Contexte spatial | `distance_to_beach_km` | Distance à la mer en km | Dérivée | Calcul GPS | ★☆☆ | V2 |
| 31 | Contexte spatial | `distance_to_port_km` | Distance au port en km | Dérivée | Calcul GPS | ★☆☆ | V2 |
| 32 | Contexte spatial | `geo_quadrant` | Quadrant géographique (NE/NW/SE/SW) | Dérivée | Calcul GPS | ★☆☆ | V2 |
| 33 | Dérivées | `ratio_surface_hauteur` | size_m2 / height_m | Dérivée | Calculé | ★☆☆ | V2 |
| 34 | Dérivées | `log_traffic` | log(1 + traffic_flow) | Dérivée | Calculé | ★☆☆ | V2 |
| 35 | Dérivées | `score_accessibilite` | Composite : route + centre | Composite | Calculé | ★☆☆ | V2 |
| 36 | Dérivées | `is_digital` | Flag binaire : panneau numérique | Dérivée | Calculé | ★☆☆ | Immédiat |
| 37 | Dérivées | `age_panneau` | Années depuis l'installation | Dérivée | Calculé | ★★★ | V3 |
| 38 | Dérivées | `effective_exposure_hours` | Heures d'exposition effectives | Dérivée | Calculé | ★★☆ | V2 |

---

## 4. Détail par famille de variables

---

### F1 — Accessibilité routière

> **Principe :** La visibilité d'un panneau dépend directement du flux de véhicules devant lui.
> Un panneau sur un boulevard de 8 voies est vu par 10× plus de personnes qu'un panneau
> dans une ruelle. L'accessibilité routière capture cette logique.

---

#### `road_type` → `road_type_enc`

| Attribut | Valeur |
|---|---|
| **Définition** | Type hiérarchique de la route la plus proche du panneau |
| **Pourquoi utile** | Variable la plus discriminante en V1 (26% d'importance). Une route trunk ou primary garantit un trafic intense. |
| **Type** | Brute → encodée (Label Encoding) |
| **Niveau spatial** | Segment |
| **Valeurs possibles** | boulevard, avenue, rue_principale, rue_secondaire (V1) / trunk, primary, secondary, tertiary (OSM V2) |
| **Source réelle** | OpenStreetMap — tag `highway=*` |
| **Outil** | osmnx : `G = ox.graph_from_bbox(...)` puis `edges["highway"]` |
| **Format** | Ligne (way OSM) → valeur catégorielle |
| **Mode de calcul** | Jointure spatiale : on cherche l'arête OSM la plus proche du panneau |
| **Limites** | OSM peut classer différemment les routes béninoises vs standards internationaux |
| **Exemple Cotonou** | Boulevard de la Marina = `trunk`, Avenue Steinmetz = `primary`, Rue de Missèbo = `tertiary` |
| **Priorité** | **IMMÉDIAT** |

---

#### `distance_to_main_road_m`

| Attribut | Valeur |
|---|---|
| **Définition** | Distance en mètres entre le panneau et le tronçon trunk/primary le plus proche |
| **Pourquoi utile** | Un panneau loin de la route principale est mal vu. Pénalité exponentielle : chaque mètre supplémentaire coûte plus cher en visibilité. |
| **Type** | Dérivée (calculée depuis le réseau OSM) |
| **Niveau spatial** | Buffer (calcul de distance) |
| **Source réelle** | OSM — réseau routier |
| **Outil** | osmnx + geopandas : `gdf.distance(nearest_road_point)` |
| **Format** | Numérique (float, mètres) |
| **Mode de calcul** | Distance euclidienne approximative ou géodésique vers la route la plus proche |
| **Limites** | Si la route n'est pas dans OSM, la distance sera erronée. Fallback : utiliser Google Maps visuellement pour valider. |
| **Exemple Cotonou** | Panneau à Dantokpa à 15m du boulevard = forte visibilité. Panneau à Agla à 300m = faible. |
| **Priorité** | **IMMÉDIAT** |

---

#### `road_lanes` *(futur — V2)*

| Attribut | Valeur |
|---|---|
| **Définition** | Nombre de voies de la route principale la plus proche |
| **Pourquoi utile** | Un boulevard à 4 voies génère 2× plus de trafic qu'une route à 2 voies. `road_type` seul ne capture pas cette nuance. |
| **Type** | Brute |
| **Source** | OSM — tag `lanes=*` |
| **Limites** | **Très souvent absent dans OSM Bénin.** Estimé à < 30% de complétude. Hypothèse de travail : utiliser `road_type` comme proxy si `lanes` manque. |
| **Priorité** | V2 — seulement si taux de complétude > 40% |

---

### F2 — Structure du réseau / Topologie

> **Principe :** Ce n'est pas juste le type de route qui compte, c'est aussi la
> *structure* du réseau autour du panneau. Les carrefours sont des points où
> les véhicules ralentissent et ont plus de temps pour regarder les panneaux.
>
> **Analogie :** À un feu rouge, tu as 30-60 secondes d'attention captive. Sur une
> autoroute, 2-3 secondes. La topologie du réseau modélise ce temps d'attention.

---

#### `nb_intersections_200m`

| Attribut | Valeur |
|---|---|
| **Définition** | Nombre d'intersections (croisements de routes) dans un rayon de 200m autour du panneau |
| **Pourquoi utile** | Plus il y a de carrefours proches, plus les véhicules ralentissent fréquemment = plus de regard disponible pour le panneau. |
| **Type** | Proxy (approximation du trafic ralenti) |
| **Niveau spatial** | Buffer 200m |
| **Source** | OSM — nœuds avec `highway=traffic_signals` ou intersection de ways |
| **Outil** | osmnx : `ox.graph_from_bbox(...)` puis compter les nœuds ayant degré ≥ 3 |
| **Format** | Numérique entier (count) |
| **Mode de calcul** | Compter les nœuds OSM dans le rayon de 200m avec `scipy.spatial.cKDTree` |
| **Limites** | Les petits carrefours non taggés dans OSM ne sont pas comptés. Sous-estimation probable. |
| **Exemple Cotonou** | Zone Échangeur de Cadjehoun : 5-8 intersections dans 200m. Zone Fidjrossè résidentielle : 1-2. |
| **Priorité** | **IMMÉDIAT** |

> **Pourquoi 200m et pas 500m ?**
> À 50 km/h, 200m = ~15 secondes. C'est la zone d'influence directe d'un carrefour sur l'attention d'un conducteur.

---

#### `has_traffic_signals_200m`

| Attribut | Valeur |
|---|---|
| **Définition** | 1 si un feu tricolore existe dans rayon 200m, 0 sinon |
| **Pourquoi utile** | Un feu rouge = arrêt complet = maximale durée d'exposition au panneau |
| **Type** | Proxy (binaire) |
| **Source** | OSM : `highway=traffic_signals` |
| **Limites** | Les feux de Cotonou sont souvent non taggés dans OSM |
| **Priorité** | V2 |

---

#### `degree_nearest_intersection` *(avancé — V3)*

| Attribut | Valeur |
|---|---|
| **Définition** | Nombre de branches du carrefour le plus proche (degré du nœud dans le graphe routier) |
| **Pourquoi utile** | Un carrefour à 5 branches (échangeur) génère plus de trafic qu'un carrefour à 3 branches. |
| **Type** | Dérivée (analyse de graphe) |
| **Source** | osmnx — networkx `G.degree(node_id)` |
| **Outil** | osmnx + networkx |
| **Limites** | Nécessite une bonne connaissance de l'analyse de graphe. Plus complexe à implémenter. |
| **Priorité** | V3 |

---

### F3 — Attractivité urbaine (POI)

> **Principe :** Les Points d'Intérêt (marchés, écoles, arrêts de bus) attirent
> des flux humains réguliers. Un panneau près d'un grand marché est vu par
> beaucoup plus de personnes qu'un panneau en zone résidentielle isolée.
>
> **Ce sont tous des proxys :** on ne mesure pas directement le flux humain,
> on l'approxime par la densité d'attracteurs connus.

---

#### `nb_markets_500m`

| Attribut | Valeur |
|---|---|
| **Définition** | Nombre de marchés (marchés traditionnels + supermarchés) dans rayon 500m |
| **Pourquoi utile** | Les marchés génèrent le flux piéton le plus intense et le plus régulier à Cotonou. Le Grand Marché Dantokpa attire des centaines de milliers de personnes par jour. |
| **Type** | Proxy de densité piétonne |
| **Niveau spatial** | Buffer 500m |
| **Source** | OSM : `amenity=marketplace`, `shop=supermarket`, `shop=mall` |
| **Outil** | `02_fetch_pois.py` + cKDTree pour comptage dans rayon |
| **Format** | Entier (count) |
| **Limites** | Les petits marchés informels (appakos) ne sont souvent pas taggés dans OSM. Sous-estimation importante à Cotonou. |
| **Exemple Cotonou** | Panneau à 200m de Dantokpa : `nb_markets_500m=3`. Panneau à Agla résidentiel : `nb_markets_500m=0`. |
| **Priorité** | **IMMÉDIAT** |

---

#### `nb_transport_stops_500m`

| Attribut | Valeur |
|---|---|
| **Définition** | Nombre d'arrêts de bus, taxis et zémidjans dans rayon 500m |
| **Pourquoi utile** | Les personnes qui attendent un transport ont les yeux libres → attention maximale pour les panneaux. |
| **Type** | Proxy de densité piétonne |
| **Source** | OSM : `highway=bus_stop`, `amenity=bus_station`, `public_transport=platform` |
| **Limites** | Les arrêts de zémidjan (motos-taxis) ne sont généralement pas dans OSM |
| **Priorité** | **IMMÉDIAT** |

---

#### `nb_schools_500m`

| Attribut | Valeur |
|---|---|
| **Définition** | Nombre d'écoles et universités dans rayon 500m |
| **Pourquoi utile** | Entrées/sorties d'école = flux dense 2× par jour. Zone captive (parents, élèves). |
| **Type** | Proxy de flux piéton temporel |
| **Source** | OSM : `amenity=school`, `amenity=university`, `amenity=college` |
| **Limites** | Les petites écoles privées sont rarement dans OSM |
| **Priorité** | **IMMÉDIAT** |

---

#### `nb_health_facilities_500m`

| Attribut | Valeur |
|---|---|
| **Définition** | Nombre de structures de santé (hôpitaux, cliniques, dispensaires) dans rayon 500m |
| **Pourquoi utile** | Flux continu de patients et visiteurs, souvent anxieux → attention disponible pendant l'attente |
| **Type** | Proxy |
| **Source** | OSM : `amenity=hospital`, `amenity=clinic`, `amenity=health_post` |
| **Priorité** | V2 |

---

#### `commercial_density_500m`

| Attribut | Valeur |
|---|---|
| **Définition** | Nombre total de commerces (shops, services, banques, hôtels) dans rayon 500m |
| **Pourquoi utile** | Une zone commerciale dense = beaucoup de passages. Corrélé avec le type de zone urbaine. |
| **Type** | Proxy de densité économique |
| **Source** | OSM : `shop=*`, `amenity=bank`, `tourism=hotel`, `landuse=retail` |
| **Priorité** | **IMMÉDIAT** |

---

#### `nb_fuel_stations_500m`

| Attribut | Valeur |
|---|---|
| **Définition** | Nombre de stations-service dans rayon 500m |
| **Pourquoi utile** | Points d'arrêt obligatoires pour les véhicules. Temps d'attention disponible pendant le plein. |
| **Type** | Proxy de trafic arrêté |
| **Source** | OSM : `amenity=fuel` |
| **Priorité** | V2 |

---

### F4 — Densité humaine

> **Principe :** La visibilité dépend du nombre de personnes qui passent devant
> le panneau. La densité humaine est la variable la plus importante théoriquement,
> mais aussi la plus difficile à mesurer sans terrain.
>
> **Stratégie :** En l'absence de données directes, on l'approche par trois méthodes
> complémentaires : les POI (famille F3), WorldPop (grille de population), et l'estimation simulée.

---

#### `pedestrian_density_score`

| Attribut | Valeur |
|---|---|
| **Définition** | Score 0–100 estimant l'intensité du flux piéton à l'emplacement du panneau |
| **Pourquoi utile** | Variable synthétique proxy de la fréquentation réelle. En V1, calculée depuis la densité économique du quartier. En V2, calculée depuis les POI OSM. |
| **Type** | Proxy composite |
| **Source V1** | Simulée : corrélée à `quartier_density` + bruit gaussien |
| **Source V2** | Calculée : combinaison normalisée de `nb_markets_500m`, `nb_transport_stops_500m`, `commercial_density_500m` |
| **Mode de calcul V2** | `ped_score = 20 × ln(1 + nb_markets) + 15 × nb_stops + 10 × nb_commerces` (proposition) |
| **Limites** | C'est une approximation. Le flux réel varie selon l'heure, la saison, les jours de marché. |
| **Exemple** | Dantokpa = 90/100. Zone résidentielle Agla = 20/100. |
| **Priorité** | **IMMÉDIAT** |

---

#### `population_density_500m` *(V2 — WorldPop)*

| Attribut | Valeur |
|---|---|
| **Définition** | Nombre estimé d'habitants dans un rayon de 500m autour du panneau, selon le modèle WorldPop |
| **Pourquoi utile** | La densité résidentielle est un proxy de fréquentation de longue durée (habitants habituels ≠ flux de passage) |
| **Type** | Brute (données raster) |
| **Source** | WorldPop — https://www.worldpop.org/ — grille de population à 100m de résolution pour le Bénin |
| **Outil** | Python : `rasterio` pour lire le raster + extraction d'une valeur en un point GPS |
| **Format** | Raster (grille GPS avec valeur par cellule) → extraction d'une valeur numérique |
| **Mode de calcul** | Extraction des cellules dans le rayon 500m, somme des habitants estimés |
| **Limites** | WorldPop est un modèle statistique, pas une mesure directe. Résolution 100m peut masquer des hétérogénéités intra-quartier. |
| **Dossier futur** | `data/sources/worldpop/` |
| **Priorité** | V2 |

---

#### `traffic_flow_estim`

| Attribut | Valeur |
|---|---|
| **Définition** | Estimation du nombre de véhicules par jour devant le panneau |
| **Pourquoi utile** | Variable fondamentale pour la visibilité publicitaire. Plus il y a de véhicules, plus le panneau est vu. |
| **Type** | Proxy (en V1 : simulé depuis le type de route + bruit) |
| **Source V1** | Simulation : base selon `road_type` ± 30% de bruit |
| **Source V2 possible** | Google Maps API (payant) / TomTom API (payant) / OpenStreetMap `maxspeed` + `lanes` comme proxy |
| **Limites** | **Aucune source gratuite et fiable de trafic réel ne couvre Cotonou.** C'est le principal gap de ce projet. |
| **Hors périmètre OSM** | OUI — à traiter dans `data/sources/google_maps/` si budget disponible |
| **Priorité** | V2 (si accès API trafic) / V3 (si pas de budget) |

---

### F5 — Densité bâtie / Morphologie urbaine

> **Principe :** Le tissu urbain (zone commerciale vs résidentielle vs industrielle)
> donne une information sur le type d'audience et l'intensité du flux.
> Un panneau en zone industrielle n'a pas la même audience qu'un panneau en centre commercial.

---

#### `land_use_type`

| Attribut | Valeur |
|---|---|
| **Définition** | Type d'occupation du sol à l'emplacement du panneau (commercial, résidentiel, industriel...) |
| **Pourquoi utile** | Variable contextuelle qui encode le "type de quartier" plus précisément que le nom du quartier seul. |
| **Type** | Brute → encodée (catégorielle) |
| **Niveau spatial** | Zone (polygone) |
| **Source** | OSM : tag `landuse=*` (commercial, residential, industrial, retail, cemetery...) |
| **Outil** | geopandas `sjoin` : point-in-polygon entre le panneau et les polygones `landuse` |
| **Limites** | `landuse` est incomplet dans OSM Cotonou. Beaucoup de zones sans tag. |
| **Exemple Cotonou** | Zone de Dantokpa = `commercial`. Haie Vive = `residential`. Port = `industrial`. |
| **Priorité** | V2 |

---

#### `building_density_500m` *(V3 — GHSL)*

| Attribut | Valeur |
|---|---|
| **Définition** | Estimation de la densité du bâti dans rayon 500m (% de surface construite) |
| **Pourquoi utile** | Zones très construites = moins de visibilité au loin, mais plus d'habitants proches. |
| **Type** | Brute (données raster) |
| **Source** | GHSL (Global Human Settlement Layer) — données satellite Copernicus / European Commission |
| **Outil** | `rasterio` pour extraction de valeurs raster |
| **Limites** | Résolution parfois insuffisante pour Cotonou. Traitement raster nécessite des bases SIG. |
| **Dossier futur** | `data/sources/ghsl/` |
| **Priorité** | V3 |

---

#### `is_coastal`

| Attribut | Valeur |
|---|---|
| **Définition** | 1 si le panneau est à moins de 1km de la mer ou de la lagune de Cotonou, 0 sinon |
| **Pourquoi utile** | La zone côtière est un axe touristique et économique distinct. Audience différente (touristes, expatriés, entreprises haut de gamme). |
| **Type** | Dérivée (calculée depuis un point de référence côtier) |
| **Mode de calcul** | `is_coastal = 1 if distance_to_beach_km < 1.0 else 0` |
| **Source** | Coordonnées GPS du bord de mer (point fixe) + calcul haversine |
| **Priorité** | V2 |

---

### F6 — Caractéristiques du panneau / Exposition

> **Principe :** Indépendamment de l'environnement, le panneau lui-même a des
> caractéristiques qui influencent sa visibilité : est-il grand ? haut ? éclairé ?
> Ces données viennent idéalement du terrain ou de la base de données du régisseur.

---

#### `panel_type` → `panel_type_enc`

| Attribut | Valeur |
|---|---|
| **Définition** | Type physique du support : digital, statique, bâche, led_small |
| **Pourquoi utile** | **Top feature V1 (26% d'importance).** Un panneau digital est visible de nuit, plus attractif, plus coûteux → segment de marché différent. |
| **Type** | Brute → encodée |
| **Source V1** | Simulée |
| **Source réelle** | Collecte terrain ou base de données régisseur (Affichage Pro, MediaOut...) |
| **Source OSM partielle** | Tag `advertising=screen` (digital) ou `advertising=billboard` (statique) |
| **Limites** | Très peu taggé dans OSM Cotonou. En V2, cette information viendra principalement du terrain ou d'un partenaire. |
| **Priorité** | **IMMÉDIAT** (déjà en V1, à compléter avec données réelles) |

---

#### `is_lit`

| Attribut | Valeur |
|---|---|
| **Définition** | 1 si le panneau est éclairé la nuit (tag OSM `lit=yes`), 0 sinon |
| **Pourquoi utile** | Un panneau éclairé est visible 24h/24 → doublement de la fenêtre d'exposition. **Nouvelle feature V2** non présente en V1. |
| **Type** | Brute |
| **Source** | OSM : tag `lit=yes` sur les nœuds `advertising=billboard` |
| **Disponibilité Cotonou** | **Disponible dès maintenant** : 7/11 panneaux OSM ont `lit=yes` dans notre premier export |
| **Exemple** | Panneau "Pharmacie Camp Guezo" = `lit=yes` → visible la nuit |
| **Priorité** | **IMMÉDIAT** |

---

#### `height_m`

| Attribut | Valeur |
|---|---|
| **Définition** | Hauteur du panneau en mètres (depuis le sol) |
| **Pourquoi utile** | Hauteur optimale ≈ 5-8m pour la visibilité automobile. Trop bas = caché par végétation/véhicules. Trop haut = difficile à lire. |
| **Type** | Brute |
| **Source réelle** | Mesure terrain ou base de données du régisseur |
| **Source OSM** | Tag `height=*` — **rarement renseigné** |
| **Limites** | **Nécessite terrain ou partenaire.** Pas disponible dans OSM. |
| **Priorité** | V2 (nécessite collecte partenaire) |

---

#### `size_m2`

| Attribut | Valeur |
|---|---|
| **Définition** | Surface totale du panneau en mètres carrés |
| **Pourquoi utile** | Plus grand = plus visible à distance. Relation log (diminishing returns). |
| **Type** | Brute |
| **Source réelle** | Mesure terrain ou base de données régisseur |
| **Limites** | **Nécessite terrain ou partenaire.** Non disponible dans OSM. |
| **Priorité** | V2 (nécessite collecte partenaire) |

---

#### `hours_of_daylight_exposure`

| Attribut | Valeur |
|---|---|
| **Définition** | Nombre d'heures par jour où le panneau reçoit de la lumière naturelle |
| **Pourquoi utile** | Un panneau orienté à l'ouest capte le soleil de l'après-midi (heure de pointe). Un panneau orienté nord peut être dans l'ombre. |
| **Type** | Proxy (difficile à mesurer sans terrain) |
| **Source V1** | Simulée : distribution normale centrée sur 9h |
| **Source réelle** | Calcul depuis l'orientation du panneau (azimut) + données solaires Cotonou. Azimut = terrain obligatoire. |
| **Limites** | L'orientation du panneau n'est jamais dans OSM. Ce calcul nécessite une enquête terrain ou photos Street View. |
| **Priorité** | V2 → dérivée simplifiée via `is_lit` + `panel_type` |

---

### F7 — Saturation / Concurrence

> **Principe :** Même un emplacement excellent peut être dévalorisé si
> trop de panneaux concurrents se disputent l'attention dans la même zone.
> C'est le principe de saturation publicitaire.

---

#### `competition_radius_500m`

| Attribut | Valeur |
|---|---|
| **Définition** | Nombre de panneaux publicitaires concurrents dans rayon 500m |
| **Pourquoi utile** | Effet de dilution de l'attention. Zone saturée = attention divisée entre plusieurs supports. |
| **Type** | Brute (mais très partielle via OSM) |
| **Source** | OSM : `advertising=*` dans rayon 500m (très incomplet à Cotonou) |
| **Source idéale** | Base de données du régisseur ou relevé terrain exhaustif |
| **Limites** | **Donnée OSM très partielle.** Sur les 11 panneaux trouvés, 5 sont dans une zone concentrée (cluster nord). La concurrence réelle est beaucoup plus élevée. |
| **Priorité** | V2 (avec les données disponibles) — à réviser avec données terrain |

---

#### `indice_saturation`

| Attribut | Valeur |
|---|---|
| **Définition** | Score composite : `competition_radius_500m × (pedestrian_density_score / 100)` |
| **Pourquoi utile** | Un panneau en zone très fréquentée avec beaucoup de concurrents subit une double contrainte. Ce score l'encode. |
| **Type** | Composite |
| **Mode de calcul** | Déjà implémenté dans `feature_engineering.py` |
| **Exemple** | Zone Dantokpa : ped_density=90, competition=5 → indice=4.5. Zone Agla : ped_density=20, competition=1 → indice=0.2. |
| **Priorité** | V2 |

---

### F8 — Contexte spatial général

> **Principe :** La position GPS brute d'un panneau contient de l'information
> implicite (quartier, proximité du centre, de la mer, du port...).
> On la rend explicite via des variables dérivées de géographie.

---

#### `quartier` → `quartier_enc`

| Attribut | Valeur |
|---|---|
| **Définition** | Nom du quartier où se situe le panneau |
| **Pourquoi utile** | Chaque quartier a un profil économique différent. En V1, variable très discriminante. |
| **Type** | Brute → encodée (Label Encoding) |
| **Source V1** | Simulée depuis une liste de 10 quartiers réels de Cotonou |
| **Source V2** | OSM : limites administratives (`admin_level=7/8`) ou `place=suburb` + geopandas `sjoin` |
| **Valeurs connues** | Akpakpa, Cadjehoun, Gbégamey, Haie Vive, Mènontin, Fidjrossè, Dantokpa, Cotonou Centre, Agla, Zongo |
| **Priorité** | **IMMÉDIAT** |

---

#### `latitude` et `longitude`

| Attribut | Valeur |
|---|---|
| **Définition** | Coordonnées GPS du panneau (WGS84, EPSG:4326) |
| **Pourquoi utile** | Le modèle RF peut apprendre des splits géographiques implicites. Complémentaire des features dérivées. |
| **Type** | Brute |
| **Source** | OSM (panneaux taggés) ou GPS terrain |
| **Priorité** | **IMMÉDIAT** |

---

#### `distance_to_center_km`

| Attribut | Valeur |
|---|---|
| **Définition** | Distance en km au centre-ville de Cotonou (ref: 6.370, 2.390) |
| **Pourquoi utile** | Gradient centre-périphérie : le centre commercial de Cotonou attire plus de trafic. |
| **Type** | Dérivée (haversine depuis le point de référence) |
| **Mode de calcul** | Déjà implémenté dans `data_generation.py` et `feature_engineering.py` |
| **Priorité** | **IMMÉDIAT** |

---

#### `distance_to_beach_km` et `distance_to_port_km`

| Attribut | Valeur |
|---|---|
| **Définition** | Distance en km à la plage (6.340, 2.383) et au port (6.350, 2.422) |
| **Pourquoi utile** | Deux pôles d'attraction économique distincts à Cotonou. Le port génère du trafic lourd. La plage génère du tourisme. |
| **Type** | Dérivée |
| **Priorité** | V2 |

---

#### `geo_quadrant`

| Attribut | Valeur |
|---|---|
| **Définition** | Quadrant géographique : 0=SW, 1=SE, 2=NW, 3=NE (par rapport au centre 6.370, 2.390) |
| **Pourquoi utile** | Division simple de la ville en 4 zones sans avoir besoin des noms de quartiers |
| **Type** | Dérivée |
| **Mode de calcul** | Déjà implémenté dans `feature_engineering.py` |
| **Priorité** | V2 |

---

### F9 — Variables dérivées / Composites

> **Principe :** Ces variables sont **calculées** à partir des variables brutes.
> Elles encodent de la connaissance métier : une relation non-linéaire ou
> une interaction entre deux variables que le modèle aurait du mal à apprendre seul.

---

#### `ratio_surface_hauteur`

| Attribut | Valeur |
|---|---|
| **Définition** | `size_m2 / height_m` — rapport entre la surface et la hauteur du panneau |
| **Pourquoi utile** | Un grand panneau bas (4m² à 2m de hauteur) n'a pas le même impact qu'un petit panneau haut (4m² à 8m). Le ratio capture l'impact visuel relatif. |
| **Type** | Dérivée |
| **Mode de calcul** | `df["ratio_surface_hauteur"] = df["size_m2"] / df["height_m"].clip(lower=0.5)` |
| **Priorité** | V2 (dépend de height_m et size_m2 réels) |

---

#### `log_traffic`

| Attribut | Valeur |
|---|---|
| **Définition** | `log(1 + traffic_flow_estim)` — trafic en échelle logarithmique |
| **Pourquoi utile** | Passer de 1000 à 2000 véhicules/jour améliore beaucoup la visibilité. Passer de 10 000 à 11 000 beaucoup moins. Le log capture cette saturation. |
| **Type** | Dérivée |
| **Mode de calcul** | `df["log_traffic"] = np.log1p(df["traffic_flow_estim"])` |
| **Priorité** | V2 (dépend de traffic_flow_estim réel) |

---

#### `score_accessibilite`

| Attribut | Valeur |
|---|---|
| **Définition** | Score composite : `(dist_route_m / 200) + (dist_centre_km / 5)` — proche de 0 = très accessible, proche de 2 = très éloigné |
| **Pourquoi utile** | Résume en un seul chiffre l'accessibilité globale. Un panneau loin de la route ET du centre est doublement pénalisé. |
| **Type** | Composite |
| **Mode de calcul** | Déjà dans `feature_engineering.py`. Les normalisations (200m, 5km) sont des hypothèses ajustables. |
| **Priorité** | V2 |

---

#### `is_digital`

| Attribut | Valeur |
|---|---|
| **Définition** | 1 si `panel_type == "digital"`, 0 sinon |
| **Pourquoi utile** | Signal binaire fort pour le modèle : les panneaux digitaux ont un comportement très différent (score plus élevé, prix plus élevé, nuit incluse). Complémentaire de `panel_type_enc`. |
| **Type** | Dérivée (binaire) |
| **Mode de calcul** | `df["is_digital"] = (df["panel_type"] == "digital").astype(int)` |
| **Priorité** | **IMMÉDIAT** |

---

#### `age_panneau`

| Attribut | Valeur |
|---|---|
| **Définition** | `année_courante - year_installed` — ancienneté du panneau en années |
| **Pourquoi utile** | Les vieux panneaux sont souvent moins bien entretenus, moins attractifs pour les annonceurs. L'emplacement peut aussi avoir perdu de la valeur. |
| **Type** | Dérivée |
| **Source** | `year_installed` — doit être fournie par le régisseur ou déduite d'une photo |
| **Limites** | **Impossible à obtenir sans terrain ou partenaire.** |
| **Priorité** | V3 |

---

#### `effective_exposure_hours`

| Attribut | Valeur |
|---|---|
| **Définition** | Heures d'exposition effectives par jour : 24h si digital, sinon `hours_of_daylight_exposure` |
| **Pourquoi utile** | Capture l'avantage nocturne des panneaux éclairés/digitaux de façon explicite |
| **Type** | Dérivée |
| **Mode de calcul** | `np.where(panel_type == "digital", 24, hours_of_daylight_exposure)` |
| **Simplification V2** | Peut être calculée depuis `is_lit` et `is_digital` : `24 if is_lit or is_digital else 10` |
| **Priorité** | V2 |

---

## 5. Features exploitables à court terme pour Cotonou / Littoral

> Cette section liste uniquement ce qu'on peut **construire dès maintenant**,
> avec les outils disponibles et sans collecte terrain.

### Ce qu'on peut faire tout de suite

| Feature | Source | Outil exact | Limite connue |
|---|---|---|---|
| `road_type` (OSM réel) | OSM via osmnx | `01_fetch_roads.py` | Peut manquer les routes non taggées |
| `distance_to_main_road_m` | OSM + geopandas | `04_build_features_from_osm.py` | Dépend de la couverture OSM |
| `nb_intersections_200m` | OSM via osmnx | Analyse nœuds dans `04_build_features.py` | Feux non taggés = sous-estimation |
| `nb_markets_500m` | OSM via Overpass | `02_fetch_pois.py` | Marchés informels absents OSM |
| `nb_transport_stops_500m` | OSM via Overpass | `02_fetch_pois.py` | Zémidjans absents OSM |
| `nb_schools_500m` | OSM via Overpass | `02_fetch_pois.py` | Petites écoles privées absentes |
| `commercial_density_500m` | OSM via Overpass | `02_fetch_pois.py` | Commerces informels absents |
| `quartier` (OSM réel) | OSM limites admin | `03_fetch_admin_boundaries.py` | Niveau admin incertain au Bénin |
| `is_lit` | OSM (déjà disponible) | `00_load_real_billboards.py` | Seulement 7 panneaux pour l'instant |
| `is_digital` | OSM + `panel_type` | Calculé en Python | Partiel : dépend du tag `advertising=screen` |
| `latitude`, `longitude` | OSM (7 panneaux réels) | Déjà dans `billboards_osm_v1.csv` | Dataset très petit (7 obs) |
| `distance_to_center_km` | Calcul haversine | `feature_engineering.py` (déjà codé) | Dépend de la qualité des coordonnées |
| `pedestrian_density_score` | Calculé depuis POI OSM | `04_build_features_from_osm.py` | Proxy, pas mesure directe |

### Outils minimaux nécessaires

```
pip install osmnx geopandas pandas scipy shapely pyyaml requests
```

| Outil | Rôle |
|---|---|
| `osmnx` | Télécharger le réseau routier OSM et les graphes |
| `geopandas` | Manipuler les données géographiques (points, lignes, polygones) |
| `scipy.spatial.cKDTree` | Calculer rapidement les distances et comptages dans un rayon |
| `requests` | Appeler l'API Overpass directement pour les POI |
| `shapely` | Géométrie : créer des points, tester si un point est dans un polygone |

---

## 6. Features théoriquement intéressantes mais difficiles sans terrain

> Ces variables seraient très utiles pour le modèle, mais elles nécessitent
> des ressources que ce projet n'a pas encore.

| Feature | Pourquoi utile | Pourquoi difficile | Alternative possible |
|---|---|---|---|
| `traffic_flow_estim` (réel) | Variable fondamentale : nb de véhicules | Aucune source gratuite et fiable pour Cotonou | Proxy OSM : type de route + nb de voies |
| `height_m` (réel) | Impact visuel direct | Mesure physique impossible sans terrain | Estimation depuis photos Street View / Mapillary |
| `size_m2` (réel) | Impact visuel direct | Mesure physique impossible sans terrain | Estimation depuis photos |
| `orientation` | Visibilité selon sens de circulation | Azimut = collecte terrain ou déduction depuis la géométrie de la route | Simplifier : perpendiculaire à la route = bonne orientation |
| `hours_of_daylight_exposure` (réel) | Exposition solaire réelle | Dépend de l'orientation + obstructions locales | Proxy simple : is_lit + panel_type |
| `age_panneau` (réel) | Qualité estimée du panneau | Year_installed connu que du régisseur | Proxy : tags OSM (timestamp de création) |
| `competition_radius_500m` (réel) | Saturation locale | Peu de panneaux dans OSM → dataset incomplet | Partiel avec les 11 panneaux OSM |
| `building_density_500m` | Morphologie urbaine fine | Données GHSL nécessitent traitement raster | Proxy : land_use_type (OSM) |
| `ndvi_value` | Présence de végétation (obstruction potentielle) | Données Sentinel-2, traitement satellite | Non prioritaire en V2 |
| `nighttime_light` | Intensité lumineuse nocturne de la zone | Données VIIRS/GHSL, traitement raster | `is_lit` du panneau comme proxy partiel |
| `street_view_quality_score` | Qualité visuelle réelle | Nécessite photos + modèle CNN | V3 uniquement |

---

## 7. Recommandations pour Cotonou / Littoral

### Ce qu'on sait sur le contexte local

1. **OSM est partiellement couvert à Cotonou.** Les axes principaux (Boulevard de la Marina, Avenue Jean-Paul II, Route de l'Aéroport) sont bien renseignés. Les rues secondaires sont incomplètes.

2. **Les marchés informels sont sous-représentés.** Le Grand Marché Dantokpa est probablement taggé, mais les centaines de marchés de quartier (appakos) ne le sont pas.

3. **Le département du Littoral = Cotonou.** Pour une extension au Littoral, la même BBox suffit. Le Littoral est entièrement couvert par la BBox élargie `(6.330–6.430, 2.330–2.450)`.

4. **Les quartiers administratifs du Bénin** sont organisés en arrondissements (13 pour Cotonou). OSM utilise `admin_level=8` pour ce niveau, mais c'est à vérifier.

5. **La lagune de Cotonou** divise la ville en partie nord et sud. C'est une contrainte géographique importante : un panneau au nord de la lagune n'est pas vu depuis le sud. À modéliser via `is_coastal` ou une variable `north_of_lagoon`.

### Proposition : variable `north_of_lagoon`

```python
# La lagune de Cotonou est approximativement à lat ~6.365
billboard["north_of_lagoon"] = (billboard["latitude"] > 6.365).astype(int)
# 1 = nord de la lagune (zone résidentielle + universitaire)
# 0 = sud de la lagune (zone portuaire + commerciale)
```

Cette variable simple capture une contrainte géographique majeure de Cotonou sans nécessiter de données supplémentaires.

---

## 8. Variables à prioriser immédiatement

> **Ce sont les features à construire en priorité pour passer de V1 (simulé) à V2 (réel).**

### Liste des 10 features prioritaires

| # | Feature | Source | Effort estimé |
|---|---|---|---|
| 1 | `road_type` (OSM réel) | osmnx | 1h |
| 2 | `distance_to_main_road_m` (OSM réel) | osmnx + geopandas | 1h |
| 3 | `quartier` (OSM réel) | Overpass admin_level | 1h |
| 4 | `nb_markets_500m` | Overpass + KDTree | 2h |
| 5 | `nb_transport_stops_500m` | Overpass + KDTree | 1h |
| 6 | `commercial_density_500m` | Overpass + KDTree | 1h |
| 7 | `nb_intersections_200m` | osmnx graphe | 2h |
| 8 | `is_lit` | Déjà disponible (billboards_osm_v1.csv) | 0h |
| 9 | `is_digital` | Déjà calculé dans feature_engineering.py | 0h |
| 10 | `pedestrian_density_score` (OSM) | Composite des features 4-6 | 1h |

---

## 9. Variables à garder pour plus tard

| Feature | Raison de l'attente | Quand la débloquer |
|---|---|---|
| `height_m` (réel) | Nécessite terrain ou partenaire | Dès qu'un partenaire régisseur accepte de partager sa base |
| `size_m2` (réel) | Idem | Idem |
| `traffic_flow_estim` (réel) | Pas de source gratuite | Si budget API trafic disponible |
| `population_density_500m` | Simple à implémenter avec WorldPop | V2 — dès qu'on maîtrise le raster |
| `land_use_type` (OSM) | OSM potentiellement incomplet | Tester la couverture OSM d'abord |
| `building_density_500m` | Nécessite rasterio + GHSL | V3 |
| `age_panneau` | Dépend du régisseur | V3 |
| `street_view_quality_score` | Nécessite CNN + photos | V3 |

---

## 10. Conclusion pratique

### Liste des 10 features prioritaires à construire

1. `road_type` → OSM, osmnx
2. `distance_to_main_road_m` → OSM, geopandas
3. `quartier` → OSM, admin boundaries
4. `nb_markets_500m` → OSM Overpass
5. `nb_transport_stops_500m` → OSM Overpass
6. `commercial_density_500m` → OSM Overpass
7. `nb_intersections_200m` → OSM, osmnx graphe
8. `is_lit` → Déjà disponible
9. `pedestrian_density_score` (V2) → Composite OSM
10. `north_of_lagoon` → Calcul simple (lat > 6.365)

### Outils minimaux (liste d'installation)

```bash
pip install osmnx geopandas pandas scipy shapely pyyaml requests numpy
```

### Ordre de construction recommandé pour un débutant

```
Étape 1 — Vérifier la couverture OSM manuellement (1-2h)
  → Overpass Turbo navigateur (Q1, Q3, Q5 de overpass_queries.md)
  → Documenter les lacunes dans decisions_log.md

Étape 2 — Lancer les scripts de collecte (dans l'ordre)
  → 01_fetch_roads.py     (routes + types)
  → 02_fetch_pois.py      (marchés, transport, écoles)
  → 03_fetch_admin_boundaries.py  (quartiers)

Étape 3 — Calculer les features pour chaque panneau
  → 04_build_features_from_osm.py

Étape 4 — Ajouter north_of_lagoon et is_coastal
  → Calcul Python simple (2 lignes par feature)

Étape 5 — Merger avec le dataset principal et comparer
  → V1 (simulé) vs V2 (OSM) : R² et RMSE
  → Si V2 meilleure → on valide la démarche

Étape 6 — WorldPop (population_density_500m)
  → Télécharger le raster Bénin depuis worldpop.org
  → Extraire les valeurs pour chaque panneau avec rasterio

Étape 7 — Partenaire régisseur (height_m, size_m2, year_installed)
  → Ce sont les features terrain incontournables pour la V3
```

---

> **Rappel :** Ce catalogue est un document vivant. À chaque nouvelle session,
> les statuts des features doivent être mis à jour pour refléter ce qui a été
> construit, validé ou abandonné.

*Créé le 2026-03-18. Cohérent avec les décisions DEC-001 à DEC-014.*
