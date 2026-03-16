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
6. [Place dans la future base de données](#place-dans-la-future-base-de-données)
7. [Sources futures — hors périmètre](#sources-futures--hors-périmètre)

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
