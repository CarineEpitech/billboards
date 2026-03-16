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

*Ce journal sera enrichi à chaque nouvelle décision. Aucune entrée ne sera supprimée.*
