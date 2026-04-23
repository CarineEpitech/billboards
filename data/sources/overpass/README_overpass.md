# README — Source de données : Overpass Turbo / OpenStreetMap

> **Statut du fichier :** Validé — Phase documentation initiale
> **Date de création :** 2026-03-16
> **Auteur :** Carine (assisté par Claude Code, ingénieur data senior)
> **Version :** 1.0
> **Périmètre :** UNIQUEMENT Overpass Turbo / OpenStreetMap — aucune autre source traitée ici

---

## Table des matières

1. [C'est quoi Overpass Turbo ?](#cest-quoi-overpass-turbo)
2. [Rôle dans ce projet](#rôle-dans-ce-projet)
3. [Ce qu'on peut extraire](#ce-quon-peut-extraire)
4. [Ce qu'on NE PEUT PAS extraire](#ce-quon-ne-peut-pas-extraire)
5. [Limites importantes](#limites-importantes)
6. [Tableau synthétique des features du projet](#tableau-synthétique-des-features-du-projet)
7. [Place dans la future base de données](#place-dans-la-future-base-de-données)
8. [Sources futures — hors périmètre](#sources-futures--hors-périmètre)

---

## C'est quoi Overpass Turbo ?

**OpenStreetMap (OSM)** est une carte du monde entier, créée collaborativement par des bénévoles.
C'est un peu comme Wikipedia, mais pour les cartes : tout le monde peut contribuer.

**Overpass Turbo** est l'outil qui permet d'interroger cette carte avec des questions précises.
Par exemple : *"Donne-moi toutes les routes principales de Cotonou"* ou *"Donne-moi tous les marchés dans un rayon de 500 mètres autour de ce point GPS"*.

> **Analogie simple :** OSM est une bibliothèque de cartes. Overpass Turbo est le bibliothécaire à qui on peut poser des questions très précises pour trouver exactement ce qu'on cherche.

**Accès gratuit :** https://overpass-turbo.eu/
Pas besoin de créer un compte. Les données sont libres et téléchargeables.

---

## Rôle dans ce projet

Dans la V1 du projet, toutes les données sont **simulées** (générées par ordinateur).
Dans la V2 (prochaine étape), on veut utiliser de **vraies données géographiques** pour que le modèle soit plus précis et crédible.

OpenStreetMap nous fournit la **géographie réelle de Cotonou** : les vraies routes, les vrais marchés, les vraies limites de quartiers. Ces informations vont directement améliorer les features (variables) que le modèle utilise pour prédire la visibilité d'un panneau publicitaire.

**Position dans le pipeline :**
```
OSM (Overpass) → features géographiques réelles → pipeline ML → meilleure prédiction
```

---

## Ce qu'on peut extraire

### Réseau routier
| Donnée OSM | Variable produite dans le dataset | Utilité pour la visibilité |
|---|---|---|
| Type de route (primary, secondary, trunk...) | `road_type` | Plus la route est grande, plus le trafic est fort |
| Nom de la rue | `street_name` | Identification, croisement avec d'autres sources |
| Voie principale proche | `distance_to_main_road_m` | Déjà dans V1 (simulé) — sera réel en V2 |
| Carrefours (intersections) | `nb_intersections_500m` | Les carrefours = points de fort passage |

### Points d'intérêt (POI)
| Donnée OSM | Variable produite | Utilité |
|---|---|---|
| Marchés, supermarchés | `nb_markets_500m` | Proxy de densité piétonne |
| Arrêts de bus, taxi | `nb_transport_stops_500m` | Trafic piéton intense |
| Écoles, hôpitaux | `nb_facilities_500m` | Attractions de flux humains |
| Commerces (shops) | `commercial_density_500m` | Zone commerciale = forte visibilité |
| Stations-service | `nb_gas_stations_500m` | Points d'arrêt = attention |

### Limites administratives
| Donnée OSM | Variable produite | Utilité |
|---|---|---|
| Nom du quartier | `quartier` | Variable catégorielle importante (top feature V1) |
| Limites de Cotonou | — | Délimite la zone d'étude |

### Occupation du sol (Land Use)
| Donnée OSM | Variable produite | Utilité |
|---|---|---|
| Zone commerciale | `land_use_type` | Contexte de l'emplacement |
| Zone résidentielle | `land_use_type` | Proximité habitants |
| Zone industrielle | `land_use_type` | Moins de passages piétons |

---

## Ce qu'on NE PEUT PAS extraire

> **Important :** ces limites définissent ce qu'il faudra chercher dans d'autres sources.

| Ce qu'on ne peut pas avoir | Raison | Source alternative à envisager |
|---|---|---|
| Trafic routier en temps réel | OSM ne collecte pas le flux de véhicules | Google Maps API, Tomtom (hors périmètre) |
| Densité de population par quartier | Ce n'est pas une donnée cartographique | WorldPop (hors périmètre) |
| Hauteur des bâtiments | Rarement renseigné en Afrique de l'Ouest | GHSL, images satellites (hors périmètre) |
| Photos des lieux | OSM ne stocke pas de photos | Google Street View, Mapillary (hors périmètre) |
| Trafic piéton mesuré | Pas de capteurs dans OSM | Enquêtes terrain (hors périmètre) |
| Emplacement réel des panneaux | Très peu taggés dans OSM Cotonou | Collecte terrain manuelle (hors périmètre) |
| Données satellite (nuit, NDVI...) | OSM = vecteurs, pas rasters | Sentinel-2, GHSL (hors périmètre) |

---

## Limites importantes

### 1. Complétude de la donnée OSM à Cotonou
OSM est plus complet dans les pays à forte communauté de contributeurs (Europe, USA).
**À Cotonou, la couverture est partielle.** Certains quartiers sont bien cartographiés,
d'autres beaucoup moins. C'est un risque à documenter.

> **Hypothèse de travail (H1) :** Les axes routiers principaux de Cotonou (boulevard du Port, avenue Jean-Paul II, route de l'Aéroport, etc.) sont suffisamment renseignés dans OSM pour être exploitables. Les rues secondaires peuvent être incomplètes.

> **Statut de H1 :** À vérifier lors de la phase d'exploration (voir overpass_strategy.md)

### 2. Qualité des attributs
Même quand un objet existe dans OSM, ses attributs (nom, type) peuvent être manquants
ou incohérents selon le contributeur.

### 3. Données statiques
OSM ne se met pas à jour automatiquement. Un nouveau marché ouvert en 2025 peut
ne pas encore être dans OSM.

### 4. Aucune donnée propriétaire
OSM est libre mais ne contient aucune donnée commerciale privée
(ex : comptage de véhicules des sociétés de trafic).

---

## Tableau synthétique des features du projet

> **Ajouté le 2026-03-18** — Vue d'ensemble de toutes les variables, toutes sources.
> Pour le détail complet de chaque variable, voir `features_catalog_cotonou.md`.
>
> **Légende difficulté :** ★☆☆ = facile · ★★☆ = moyen · ★★★ = difficile
> **Statut var. :** B = Brute · P = Proxy · D = Dérivée · C = Composite

| Famille | Variable(s) | Description | Statut var. | Source principale | Difficulté | Priorité |
|---|---|---|---|---|---|---|
| **Accessibilité routière** | `road_type` | Type de la route la plus proche | B | OSM `highway=*` | ★☆☆ | Immédiat |
| | `distance_to_main_road_m` | Distance en m à la route principale | D | OSM + calcul | ★★☆ | Immédiat |
| | `road_lanes` | Nombre de voies | B | OSM (partiel) | ★★☆ | V2 |
| **Topologie réseau** | `nb_intersections_200m` | Carrefours dans rayon 200m | D | OSM nœuds | ★★☆ | Immédiat |
| | `has_traffic_signals_200m` | Présence de feux | B | OSM | ★☆☆ | V2 |
| | `degree_nearest_intersection` | Branches du carrefour le plus proche | D | osmnx graphe | ★★★ | V3 |
| **Attractivité urbaine** | `nb_markets_500m` | Marchés dans rayon 500m | P | OSM amenity | ★☆☆ | Immédiat |
| | `nb_transport_stops_500m` | Arrêts transport dans 500m | P | OSM highway | ★☆☆ | Immédiat |
| | `nb_schools_500m` | Écoles dans 500m | P | OSM amenity | ★☆☆ | Immédiat |
| | `commercial_density_500m` | Commerces dans 500m | P | OSM shop | ★☆☆ | Immédiat |
| | `nb_health_facilities_500m` | Structures de santé dans 500m | P | OSM amenity | ★☆☆ | V2 |
| | `nb_fuel_stations_500m` | Stations-service dans 500m | P | OSM amenity | ★☆☆ | V2 |
| **Densité humaine** | `pedestrian_density_score` | Score 0–100 fréquentation piétonne | C | POI OSM calculé | ★★☆ | Immédiat |
| | `population_density_500m` | Habitants estimés dans 500m | B | WorldPop raster | ★★☆ | V2 |
| | `traffic_flow_estim` | Flux véhiculaire/jour | P | Simulation / API | ★★★ | V2–V3 |
| **Morphologie urbaine** | `land_use_type` | Type d'occupation du sol | B | OSM landuse | ★★☆ | V2 |
| | `building_density_500m` | Densité du bâti dans 500m | P | GHSL raster | ★★★ | V3 |
| | `is_coastal` | À moins de 1km de la mer | D | Calcul GPS | ★☆☆ | V2 |
| | `north_of_lagoon` | Au nord de la lagune de Cotonou | D | Calcul GPS | ★☆☆ | V2 |
| **Panneau / Exposition** | `panel_type` → `panel_type_enc` | Type de support (digital, statique…) | B | Terrain / OSM | ★☆☆ | Immédiat |
| | `is_lit` | Éclairé la nuit (`lit=yes`) | B | OSM (disponible) | ★☆☆ | **Disponible** |
| | `height_m` | Hauteur en mètres | B | Terrain | ★★★ | V2 |
| | `size_m2` | Surface en m² | B | Terrain | ★★★ | V2 |
| | `hours_of_daylight_exposure` | Heures d'exposition solaire | P | Simulation | ★★☆ | V2 |
| **Saturation** | `competition_radius_500m` | Panneaux concurrents dans 500m | B | OSM (partiel) | ★★☆ | V2 |
| | `indice_saturation` | Competition × densité piétonne | C | Calculé | ★☆☆ | V2 |
| **Contexte spatial** | `quartier` → `quartier_enc` | Nom du quartier | B | OSM admin | ★☆☆ | Immédiat |
| | `latitude`, `longitude` | Coordonnées GPS | B | GPS / OSM | ★☆☆ | Immédiat |
| | `distance_to_center_km` | Distance au centre-ville | D | Calcul GPS | ★☆☆ | Immédiat |
| | `distance_to_beach_km` | Distance à la mer | D | Calcul GPS | ★☆☆ | V2 |
| | `distance_to_port_km` | Distance au port | D | Calcul GPS | ★☆☆ | V2 |
| | `geo_quadrant` | Quadrant NE/NW/SE/SW | D | Calcul GPS | ★☆☆ | V2 |
| **Dérivées / Composites** | `ratio_surface_hauteur` | size_m2 / height_m | D | Calculé | ★☆☆ | V2 |
| | `log_traffic` | log(1 + traffic_flow) | D | Calculé | ★☆☆ | V2 |
| | `score_accessibilite` | Route + centre (normalisé) | C | Calculé | ★☆☆ | V2 |
| | `is_digital` | Panneau numérique ? (binaire) | D | Calculé | ★☆☆ | Immédiat |
| | `effective_exposure_hours` | Heures effectives (nuit incluse si lit) | D | Calculé | ★☆☆ | V2 |
| | `age_panneau` | Ancienneté depuis installation | D | Terrain | ★★★ | V3 |

> **Pour le détail complet (définition, exemple, limites, mode de calcul)** →
> consulter `features_catalog_cotonou.md`

---

## Place dans la future base de données

Le dataset final (V2) aura cette structure cible :

```
billboard_id | latitude | longitude | ... features V1 simulées ... | ... features OSM réelles ...
```

Les colonnes issues d'OSM alimenteront directement plusieurs features existantes du modèle V1 :

| Feature V1 (simulée) | Remplacement OSM (V2) | Impact attendu |
|---|---|---|
| `road_type_enc` | Extrait directement de OSM highway=* | Meilleure précision |
| `quartier_enc` | Extrait des limites administratives OSM | Plus fiable que simulation |
| `distance_to_main_road_m` | Calculé depuis le réseau OSM | Donnée réelle vs simulée |
| `pedestrian_density_score` | Proxy : nb POI + stops dans rayon 500m | Approximation réelle |
| `competition_radius_500m` | Panneaux OSM dans rayon 500m | Très partiel (données manquantes) |

---

## Sources futures — hors périmètre

> Ces sources ont été **identifiées** pendant cette phase mais seront traitées **dans des fichiers séparés**.

| Source | Ce qu'elle apporte | Dossier futur |
|---|---|---|
| Google Maps / Places API | Trafic temps réel, commerces vérifiés | `data/sources/google_maps/` |
| WorldPop | Densité de population par cellule GPS | `data/sources/worldpop/` |
| GHSL (Global Human Settlement Layer) | Hauteur bâtiments, bâti urbain | `data/sources/ghsl/` |
| Mapillary / Street View | Photos terrain, visibilité réelle | `data/sources/street_view/` |
| Sentinel-2 | Images satellite, NDVI, lumière nocturne | `data/sources/sentinel/` |

---

*Fichier créé le 2026-03-16. Prochaine révision prévue après validation de la phase exploration.*
