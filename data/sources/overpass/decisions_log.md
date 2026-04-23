# Journal de décisions — Phase Overpass Turbo / OSM

> **Ce fichier ne doit jamais être nettoyé.** Toutes les décisions, même abandonnées, sont conservées.
> Les décisions remplacées sont marquées `[REMPLACÉE]` avec horodatage et raison.
> **Date de création :** 2026-03-16

---

## Format d'une entrée

```
### [DEC-XXX] Titre de la décision
- **Date :** YYYY-MM-DD HH:MM
- **Décision :** Ce qui a été décidé
- **Contexte :** Pourquoi on a dû prendre cette décision
- **Justification :** Argument principal qui a guidé le choix
- **Impact :** Ce que ça change dans le projet
- **Statut :** PROVISOIRE / VALIDÉE / REMPLACÉE / ABANDONNÉE
```

---

## Décisions — 2026-03-16

---

### [DEC-001] Créer un dossier séparé par source de données

- **Date :** 2026-03-16 00:00
- **Décision :** Chaque source de données (Overpass, WorldPop, GHSL, etc.) aura son propre dossier sous `data/sources/`.
- **Contexte :** Le projet utilise plusieurs sources hétérogènes. Sans séparation, les fichiers se mélangeraient rapidement.
- **Justification :** Principe de séparation des responsabilités (SoC). Facilite la maintenance, la révision, et l'onboarding d'un nouveau collaborateur. Si une source change ou disparaît, son impact est isolé.
- **Impact :** Structure du dépôt plus longue mais beaucoup plus claire. Chaque source documente sa propre logique.
- **Statut :** VALIDÉE

---

### [DEC-002] Commencer par la documentation avant le code

- **Date :** 2026-03-16 00:00
- **Décision :** Pour chaque source, produire d'abord la documentation complète (README, stratégie, requêtes, décisions) avant d'écrire les scripts Python.
- **Contexte :** Carine est débutante. Coder directement sans comprendre la logique crée de la confusion et des erreurs difficiles à corriger.
- **Justification :** En ingénierie data senior, on conçoit avant de coder. La documentation force à clarifier les objectifs, les limites, et les risques. Elle évite aussi de coder une feature basée sur des données qui n'existent pas.
- **Impact :** La Phase 1 est entièrement documentaire. Le code sera produit en Phase 2 après validation manuelle via Overpass Turbo navigateur.
- **Statut :** VALIDÉE

---

### [DEC-003] Utiliser osmnx comme bibliothèque principale pour l'accès OSM

- **Date :** 2026-03-16 00:00
- **Décision :** Utiliser la bibliothèque Python `osmnx` pour télécharger les données OSM dans les scripts automatisés.
- **Contexte :** Deux options principales existent : `osmnx` (bibliothèque haut niveau) vs requêtes HTTP directes à l'API Overpass.
- **Justification :**
  - `osmnx` gère automatiquement la pagination, le rate limiting, et la conversion en GeoDataFrame
  - Code plus court = plus lisible pour une débutante
  - Communauté active, bien documentée
  - S'intègre directement avec `geopandas` et `networkx`
  - Alternative HTTP directe : plus flexible mais complexe, réservée aux cas avancés
- **Impact :** `osmnx` sera ajouté à `requirements.txt`. Les scripts seront plus courts et lisibles.
- **Statut :** VALIDÉE

---

### [DEC-004] BBox de Cotonou fixée à (6.340, 2.340, 6.405, 2.430)

- **Date :** 2026-03-16 00:00
- **Décision :** Utiliser la BBox déjà définie dans `config/config.yaml` comme zone de référence pour toutes les requêtes OSM.
- **Contexte :** Le projet a déjà défini une bounding box dans le fichier de configuration. Il faut être cohérent.
- **Justification :** Centraliser les paramètres géographiques évite les incohérences. Si la zone change un jour, un seul fichier est à modifier.
- **Impact :** Toutes les requêtes OSM utilisent cette bbox. Les scripts Python liront ce paramètre depuis `config/config.yaml`.
- **Statut :** VALIDÉE

---

### [DEC-005] Tester manuellement sur Overpass Turbo avant d'automatiser

- **Date :** 2026-03-16 00:00
- **Décision :** La Phase 1 de collecte est une exploration manuelle via le site overpass-turbo.eu. L'automatisation Python n'est déclenchée qu'après validation de la couverture OSM.
- **Contexte :** La qualité OSM à Cotonou est incertaine. Automatiser sans vérifier risque de produire un pipeline sur des données vides ou très partielles.
- **Justification :** Coût faible (1-2h d'exploration manuelle) pour un gain de sécurité élevé. Principe "fail fast" : mieux vaut découvrir les problèmes tôt.
- **Impact :** Ralentit légèrement le démarrage du code mais prévient des bugs silencieux (dataset incomplet non détecté).
- **Statut :** VALIDÉE

---

### [DEC-006] Zone de test = Akpakpa / Boulevard du Port

- **Date :** 2026-03-16 00:00
- **Décision :** La zone de test initiale pour les requêtes OSM sera centrée sur le quartier Akpakpa et le boulevard du Port.
- **Contexte :** Il faut choisir une zone test représentative et probablement bien cartographiée dans OSM.
- **Justification :** Le boulevard du Port et la zone de l'échangeur sont des axes majeurs de Cotonou, visibles sur toutes les cartes. Ils sont très probablement bien renseignés dans OSM. C'est la zone idéale pour valider que les requêtes fonctionnent avant de les étendre à toute la ville.
- **Impact :** BBox de test : `(6.355, 2.375, 6.375, 2.400)`. Réduction de la zone = requêtes plus rapides pour les tests.
- **Statut :** VALIDÉE

---

### [DEC-007] Rayon de 500m pour le comptage des POI

- **Date :** 2026-03-16 00:00
- **Décision :** Utiliser un rayon de 500 mètres pour compter les POI autour de chaque panneau (marchés, transports, commerces...).
- **Contexte :** Il faut choisir un rayon standard pour les features de densité environnementale. Plusieurs options existent : 200m, 500m, 1km.
- **Justification :**
  - 200m = trop restrictif (peu de POI pour une ville dense)
  - 1km = trop large (capture des zones non pertinentes pour la visibilité)
  - 500m ≈ 6-7 minutes à pied = zone d'influence raisonnable pour un panneau
  - C'est le rayon déjà utilisé dans `competition_radius_500m` en V1 (cohérence)
- **Impact :** Feature `nb_pois_500m`, `nb_markets_500m`, etc. toutes calculées sur 500m. Le rayon de 200m est utilisé uniquement pour les carrefours (zone d'attention immédiate d'un conducteur).
- **Statut :** VALIDÉE

---

### [DEC-008] Conserver les features V1 simulées comme baseline de comparaison

- **Date :** 2026-03-16 00:00
- **Décision :** Les nouvelles features OSM (V2) ne remplaceront pas immédiatement les features simulées V1. Les deux coexisteront le temps de valider l'amélioration du modèle.
- **Contexte :** Remplacer directement les features simulées par les features OSM sans valider d'abord pourrait dégrader le modèle si les données OSM sont incomplètes.
- **Justification :** Principe scientifique : on compare le modèle V1 (simulé) vs V2 (OSM) sur les mêmes métriques (RMSE, R²). L'amélioration doit être prouvée, pas supposée.
- **Impact :** Le dataset V2 aura potentiellement deux versions des mêmes features (simulée + OSM). On sélectionnera la meilleure via feature importance.
- **Statut :** VALIDÉE

---

### [DEC-009] Ne pas collecter les données réelles des panneaux dans cette phase

- **Date :** 2026-03-16 00:00
- **Décision :** La collecte des emplacements réels des panneaux publicitaires (coordonnées GPS terrain) est **hors périmètre** de cette phase OSM.
- **Contexte :** La variable cible (emplacement des panneaux) nécessite soit une collecte terrain, soit une source dédiée (base de données Ramses Media, Affimad, etc.). Ce n'est pas ce que fait OSM.
- **Justification :** Mélanger la collecte des features contextuelles (OSM) avec la collecte de la variable cible créerait de la confusion. Ces deux collectes ont des logiques différentes.
- **Impact :** En V2, les emplacements de panneaux seront soit simulés (amélioration de la simulation), soit collectés via une autre source à identifier. Cette source sera documentée dans un dossier séparé.
- **Statut :** VALIDÉE

---

---

## Décisions — 2026-03-16 (mise à jour après analyse du premier export OSM)

---

### [DEC-010] Hypothèse H3 partiellement infirmée — OSM contient des panneaux à Cotonou

- **Date :** 2026-03-16 (après analyse de export.geojson)
- **Décision :** L'hypothèse H3 (*"les panneaux publicitaires ne sont pas taggés dans OSM Cotonou"*) est **partiellement infirmée**. On a trouvé 11 panneaux avec `advertising=billboard` dans une zone élargie autour de Cotonou.
- **Contexte :** Premier export Overpass Turbo réel chargé et analysé. Fichier : `billboards_osm_raw.geojson`, exporté le 2026-03-16.
- **Justification :** Les données existent mais sont très partielles (11 panneaux au total, dont 7 dans/près de Cotonou et 4 probablement à Porto-Novo). C'est un point de départ réel, pas un dataset complet.
- **Impact :**
  - Le dataset V2 commence avec 7 panneaux réels (zone Cotonou élargie)
  - H3 est reformulée : *"OSM contient quelques panneaux à Cotonou mais la couverture est très partielle"*
  - On doit chercher d'autres tags OSM pour compléter (voir DEC-013)
- **Statut :** VALIDÉE

---

### [DEC-011] Élargissement de la BBox Cotonou suite aux données réelles

- **Date :** 2026-03-16
- **Décision :** La BBox du projet est élargie de `(6.340–6.405, 2.340–2.430)` à `(6.330–6.430, 2.330–2.450)`.
- **Contexte :** 5 des 11 panneaux OSM trouvés sont à `lat ~6.41–6.42`, juste au nord de l'ancienne limite `lat_max=6.405`. 1 panneau est à `lon ~2.447`, juste à l'est de `lon_max=2.430`.
- **Justification :** Les données réelles prouvent que la bbox V1 était trop conservative. Rogner des données réelles pour respecter une limite arbitraire serait une erreur méthodologique.
- **Impact :**
  - `config/config.yaml` mis à jour (bbox principale élargie, bbox V1 conservée sous `lat_core_*`)
  - L'ancienne bbox est conservée dans la config comme `lat_core_min/max` et `lon_core_min/max`
  - Tous les scripts OSM utiliseront la nouvelle bbox
- **Décision V1 originale conservée :** bbox `(6.340–6.405, 2.340–2.430)` dans `lat_core_*`
- **Statut :** VALIDÉE

---

### [DEC-012] Exclusion des panneaux hors zone (Porto-Novo cluster)

- **Date :** 2026-03-16
- **Décision :** Les 4 panneaux OSM à `lon ~2.676, lat ~6.516` sont classés `hors_zone` et exclus du dataset Cotonou.
- **Contexte :** Ces 4 panneaux (`node/5174487056`, `5174487057`, `5588568313`, `5588595893`) sont à ~25km à l'est de Cotonou, probablement dans la zone Porto-Novo / Sèmè-Kpodji.
- **Justification :** Ce projet est centré sur Cotonou. Mélanger des données de Porto-Novo biaiserait le modèle (le contexte urbain est différent). Ces données seront conservées dans le fichier brut mais filtrées dans le pipeline.
- **Impact :** Script `00_load_real_billboards.py` applique le filtre `zone != "hors_zone"`. Les données sont conservées dans `billboards_osm_raw.geojson` (jamais supprimées).
- **Statut :** VALIDÉE

---

### [DEC-013] Recherche étendue aux autres tags advertising OSM

- **Date :** 2026-03-16
- **Décision :** Élargir les requêtes Overpass à tous les types de tags `advertising` (pas seulement `billboard`) pour maximiser la collecte de panneaux réels.
- **Contexte :** Le premier export utilisait uniquement `advertising=billboard`. D'autres types existent : `board`, `column`, `screen`, `poster`, `totem`.
- **Justification :** Un dataset de 7 panneaux est insuffisant pour entraîner un modèle ML fiable. On doit maximiser la collecte avant de conclure sur le volume disponible.
- **Impact :** Nouvelles requêtes Q11–Q15 ajoutées dans `overpass_queries.md`. Un deuxième export OSM sera effectué et intégré.
- **Statut :** VALIDÉE

---

### [DEC-014] Ajout de la feature `is_lit` au modèle

- **Date :** 2026-03-16
- **Décision :** La feature `is_lit` (panneau éclairé la nuit, issu du tag OSM `lit=yes`) est ajoutée au modèle V2.
- **Contexte :** 7 des 11 panneaux OSM ont `lit=yes`. Cette donnée n'existait pas en V1 (simulée indirectement via `panel_type_enc`).
- **Justification :** Un panneau éclairé est visible 24h/24 → impact direct sur la visibilité. C'est une feature réelle, gratuite, et disponible dans OSM pour les panneaux taggés.
- **Impact :** `is_lit` sera ajoutée dans la liste `features.numerical` de `config.yaml` lors de la construction du dataset V2.
- **Statut :** VALIDÉE

---

*Ce journal sera enrichi à chaque nouvelle décision. Aucune entrée ne sera supprimée.*
