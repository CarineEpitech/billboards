# Billboard Geolocation Platform — Cotonou, Bénin

> **Prototype V1** — Plateforme centralisée de panneaux publicitaires géoréférencés

---

## Vue d'ensemble

Ce projet construit un pipeline ML complet pour **analyser et prédire le potentiel de visibilité** des panneaux publicitaires à Cotonou. Il constitue la fondation technique d'une plateforme évolutive vers la détection satellite et l'optimisation multi-variable.

---

## Architecture du projet

```
billboards/
├── config/
│   └── config.yaml              # Configuration centralisée
├── data/
│   ├── raw/billboards_raw.csv   # Données brutes (avec erreurs intentionnelles)
│   └── processed/billboards_clean.csv
├── src/
│   ├── data_generation.py       # Génération dataset synthétique (45 panneaux)
│   ├── cleaning.py              # Validation, imputation, dédoublonnage
│   ├── feature_engineering.py  # Encodage, features dérivées, géospatiales
│   ├── model.py                 # RandomForestRegressor + CV
│   └── evaluation.py           # Métriques + 4 graphiques + rapport JSON
├── reports/
│   ├── figures/                 # 4 graphiques générés automatiquement
│   ├── model_results.json
│   └── billboard_model.pkl
├── main.py                      # Orchestrateur — point d'entrée unique
└── requirements.txt
```

---

## Installation et exécution

```bash
pip install -r requirements.txt
python main.py
```

---

## Pipeline ML

```
data_generation → cleaning → feature_engineering → model → evaluation
    45 panneaux    Validation   20 features ML       RF      R², RMSE,
    Cotonou        GPS, NaN,    (physiques, geo,     100T    Graphiques,
    Bruit injecté  doublons     trafic, context)     CV=5    JSON report
```

---

## Features du modèle (20 features)

| Catégorie | Features |
|---|---|
| **Physiques** | height_m, size_m2, ratio_surface_hauteur, is_digital |
| **Trafic** | traffic_flow_estim, log_traffic, road_type_enc |
| **Localisation** | latitude, longitude, quartier_enc, geo_quadrant |
| **Géospatiales** | distance_to_center_km, distance_to_beach_km, distance_to_port_km |
| **Contexte** | pedestrian_density_score, competition_radius_500m, indice_saturation |
| **Temporelles** | age_panneau, hours_of_daylight_exposure, effective_exposure_hours |
| **Accessibilité** | distance_to_main_road_m, score_accessibilite |

---

## Métriques attendues (45 obs bruitées)

| Métrique | Valeur typique | Interprétation |
|---|---|---|
| **CV R²** | 0.45 – 0.65 | Variance expliquée en cross-validation |
| **Test RMSE** | 8 – 14 pts | Erreur typique sur 100 pts |
| **Test MAE** | 6 – 11 pts | Erreur absolue moyenne |

> Avec 45 observations bruitées, ces métriques sont normales et attendues.

---

## Pourquoi RandomForest ?

| Critère | RandomForest | Alternative |
|---|---|---|
| **Petit dataset** | Excellent (régularisé) | XGBoost : risque overfitting |
| **Pas de normalisation** | Invariant aux échelles | Ridge : requiert StandardScaler |
| **Interprétabilité** | feature_importances_ built-in | Réseau de neurones : boîte noire |
| **Non-linéarités** | Capture automatiquement | Régression linéaire : assume linéarité |

---

## Roadmap

### V1 — Prototype (ACTUEL)
- Dataset synthétique réaliste, Pipeline complet, RandomForest, Métriques

### V2 — Production Ready (3–6 mois)
- Dataset réel (collecte terrain + OpenStreetMap)
- XGBoost + Optuna hyperparameter tuning
- SHAP values pour l'explicabilité
- API REST (FastAPI) + Dashboard Streamlit

### V3 — Intelligence Avancée (12–18 mois)
- Détection satellite : YOLOv8 sur images Sentinel-2
- CNN scoring : qualité visuelle des photos
- Optimisation multi-variable (algo génétique)
- MLOps : MLflow, CI/CD du modèle

---

## Phrases clés pour la présentation

- *"Le bruit gaussien simule les facteurs non capturés — angle du soleil, obstructions locales, saisonnalité."*
- *"Médiane et non moyenne pour l'imputation : robustesse aux outliers résiduels."*
- *"RandomForest avec max_depth=6 : régularisation intentionnelle pour 40 observations."*
- *"Le gap R²_train − R²_test mesure l'overfitting. Un gap faible montre que le modèle généralise."*
