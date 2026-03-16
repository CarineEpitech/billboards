# Historique du projet — Phase Overpass Turbo / OSM

> **Ce fichier est un journal chronologique.** Tout ce qui a été fait dans cette phase y est consigné.
> Les décisions abandonnées et remplacées sont conservées avec leur raison.
> **Aucune entrée ne doit être supprimée.**

---

## 2026-03-16 — Initialisation de la phase OSM

### Contexte
Le projet Billboard Geolocation Cotonou est en **V1 prototype** avec données simulées.
La prochaine étape (V2) nécessite de vraies données géographiques.
Cette session lance la phase de documentation et de stratégie pour la source OSM/Overpass.

### Ce qui existait avant cette session

```
billboards/
├── config/config.yaml        ← BBox Cotonou déjà définie
├── data/raw/                 ← Données synthétiques (45 panneaux)
├── data/processed/           ← Dataset nettoyé
├── src/                      ← Pipeline ML complet (5 modules)
├── main.py                   ← Orchestrateur
├── reports/                  ← Modèle PKL, métriques JSON, 6 figures
├── docs/                     ← Documentation Word (4 fichiers)
└── dashboard.py              ← Dashboard (ajouté session précédente)
```

**Métriques V1 connues :**
- OOB R² ≈ 0.28
- Test RMSE ≈ 18 pts
- Top feature : `panel_type_enc` (26%) — digital > statique

### Ce qui a été produit dans cette session

#### Nouvelle arborescence créée
```
data/sources/overpass/
├── README_overpass.md          ← Rôle de la source, limites, place dans le dataset
├── overpass_strategy.md        ← Stratégie 4 phases, critères de qualité
├── overpass_queries.md         ← 10 requêtes annotées + requête consolidée
├── notes_beginner.md           ← Glossaire et explications pédagogiques
├── decisions_log.md            ← 9 décisions horodatées (ce fichier)
├── project_history.md          ← Ce fichier
└── scripts/                    ← (dossier créé, scripts à développer en Phase 2)
    ├── 01_fetch_roads.py       ← À créer
    ├── 02_fetch_pois.py        ← À créer
    ├── 03_fetch_admin_boundaries.py  ← À créer
    └── 04_build_features_from_osm.py ← À créer
```

### Décisions clés de cette session

| ID | Décision | Statut |
|---|---|---|
| DEC-001 | Dossier séparé par source | VALIDÉE |
| DEC-002 | Documentation avant code | VALIDÉE |
| DEC-003 | osmnx comme librairie principale | VALIDÉE |
| DEC-004 | BBox Cotonou depuis config.yaml | VALIDÉE |
| DEC-005 | Test manuel avant automatisation | VALIDÉE |
| DEC-006 | Zone test = Akpakpa / Bvd Port | VALIDÉE |
| DEC-007 | Rayon 500m pour POI | VALIDÉE |
| DEC-008 | Features V1 conservées en baseline | VALIDÉE |
| DEC-009 | Emplacements panneaux = hors périmètre OSM | VALIDÉE |

### Hypothèses de travail définies

| ID | Hypothèse | Statut |
|---|---|---|
| H1 | Les axes routiers principaux de Cotonou sont suffisamment dans OSM | À vérifier Phase 1 |
| H2 | Les panneaux visibles sont proches des trunk/primary/secondary | Confirmé partiellement V1 |
| H3 | Les panneaux publicitaires ne sont pas taggés dans OSM Cotonou | À vérifier |

### Sources identifiées mais hors périmètre de cette phase

| Source | Ce qu'elle apporte | Traitement futur |
|---|---|---|
| Google Maps / Places API | Trafic temps réel, commerces | `data/sources/google_maps/` |
| WorldPop | Densité de population | `data/sources/worldpop/` |
| GHSL | Hauteur bâtiments, bâti urbain | `data/sources/ghsl/` |
| Mapillary / Street View | Photos terrain | `data/sources/street_view/` |
| Sentinel-2 | Images satellite | `data/sources/sentinel/` |
| Données terrain panneaux | Emplacements réels | Source dédiée à identifier |

---

## Prochaines étapes à planifier

### Phase 2 — Exploration manuelle (à faire après cette session)

1. Aller sur https://overpass-turbo.eu/
2. Tester Q1 (routes) sur la zone Cotonou complète → évaluer la couverture
3. Tester Q5 (quartiers) → vérifier si les noms de quartiers existent dans OSM
4. Tester Q3 (marchés) → compter combien de marchés sont référencés
5. Documenter les résultats dans `decisions_log.md` (nouvelles entrées DEC-010+)

### Phase 3 — Scripts Python (après Phase 2)

1. Écrire `01_fetch_roads.py` en utilisant `osmnx`
2. Écrire `02_fetch_pois.py` pour les POI
3. Écrire `03_fetch_admin_boundaries.py`
4. Tester sur la zone Akpakpa (BBox test)
5. Étendre à Cotonou complet si les tests passent

### Phase 4 — Intégration dans le pipeline ML

1. Écrire `04_build_features_from_osm.py`
2. Merger `osm_features_per_billboard.csv` avec le dataset principal
3. Comparer les métriques V1 (simulé) vs V2 (OSM)
4. Mettre à jour `config/config.yaml` avec les nouvelles features

---

*Historique ouvert le 2026-03-16. Chaque session future ajoutera une nouvelle entrée datée.*
