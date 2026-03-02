"""
==============================================================================
MODULE : cleaning.py
==============================================================================

RÔLE : Pipeline de nettoyage des données brutes de panneaux publicitaires.

PHILOSOPHIE DU CLEANING :
  Le cleaning n'est PAS cosmétique — c'est la fondation de toute la chaîne ML.
  Un modèle entraîné sur des données sales produit des prédictions non fiables,
  même s'il a des bonnes métriques sur le train set (garbage in, garbage out).

  On distingue 4 types de problèmes :
  1. VALIDITÉ       : valeurs hors plage physiquement impossible (score > 100)
  2. COHÉRENCE      : latitude hors bbox Cotonou
  3. COMPLÉTUDE     : valeurs manquantes (NaN)
  4. UNICITÉ        : doublons

DÉCISION D'IMPUTATION :
  Pour les valeurs numériques manquantes, on utilise la médiane (et non la moyenne)
  car la médiane est robuste aux outliers. Si on imputait avec la moyenne et qu'un
  outlier traîne, on "polluerait" toutes les lignes imputées.

  Pour les catégoriques, on impute avec le mode (valeur la plus fréquente) ou
  une catégorie "Inconnu" pour ne pas perdre l'information de la missingness.

AUDIT TRAIL :
  Chaque transformation est loggée dans un rapport. En production, ce rapport
  serait stocké en base pour traçabilité réglementaire (RGPD, audit qualité).

==============================================================================
"""

import numpy as np
import pandas as pd
import yaml
from pathlib import Path
from typing import Dict, Any


# ---------------------------------------------------------------------------
# FONCTIONS DE VALIDATION
# ---------------------------------------------------------------------------

def validate_coordinates(df: pd.DataFrame, geo_config: dict) -> pd.DataFrame:
    """
    Filtre les coordonnées GPS hors de la zone géographique de Cotonou.

    POURQUOI : Des erreurs GPS ou de saisie peuvent placer un panneau au Togo
    ou en mer. Ces lignes invalides doivent être supprimées (pas imputées —
    on ne peut pas "deviner" où est un panneau).

    DÉCISION : Suppression plutôt qu'imputation pour les coordonnées invalides.
    Une imputation (ex: mettre la médiane des lat) serait géographiquement
    absurde — on placerait le panneau au centre du dataset, pas à Cotonou.
    """
    lat_min = geo_config["lat_min"]
    lat_max = geo_config["lat_max"]
    lon_min = geo_config["lon_min"]
    lon_max = geo_config["lon_max"]

    # Tolérance de 5km autour de la bbox pour ne pas être trop strict
    tol = 0.05

    mask_valid = (
        df["latitude"].between(lat_min - tol, lat_max + tol) &
        df["longitude"].between(lon_min - tol, lon_max + tol)
    )

    n_removed = (~mask_valid).sum()
    if n_removed > 0:
        print(f"  [COORDS] {n_removed} lignes supprimées (coordonnées hors Cotonou)")

    return df[mask_valid].copy()


def validate_visibility_score(df: pd.DataFrame, clean_config: dict) -> pd.DataFrame:
    """
    Corrige les scores de visibilité hors plage [0, 100].

    POURQUOI : Un score de -3 ou 999 est une erreur de saisie.
    DÉCISION : Clipping (écrêtage) plutôt que suppression.
    On perd de l'info mais on garde la ligne — préférable si les autres
    features sont valides.

    NOTE : On clip AVANT de calculer les stats pour que la médiane utilisée
    ensuite soit basée sur des valeurs propres.
    """
    score_min = clean_config["visibility_score_min"]
    score_max = clean_config["visibility_score_max"]

    n_out = ((df["visibility_score"] < score_min) | (df["visibility_score"] > score_max)).sum()

    if n_out > 0:
        print(f"  [SCORE] {n_out} scores aberrants écrêtés vers [{score_min}, {score_max}]")

    df["visibility_score"] = df["visibility_score"].clip(score_min, score_max)
    return df


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Supprime les doublons basés sur panel_id et la position géographique.

    STRATÉGIE en deux passes :
      1. Doublon exact sur panel_id → on garde la première occurrence
      2. Doublon géographique approximatif (même lat/lon à 100m près) →
         on garde celui avec le plus d'informations (moins de NaN)

    POURQUOI deux passes ? Un panneau peut avoir deux IDs différents mais
    être physiquement le même (re-saisie après mise à jour). La passe
    géographique capture ce cas.
    """
    n_before = len(df)

    # Passe 1 : doublons exacts sur panel_id
    df = df.drop_duplicates(subset=["panel_id"], keep="first")
    n_after_pass1 = len(df)

    if n_before - n_after_pass1 > 0:
        print(f"  [DEDUP] {n_before - n_after_pass1} doublons panel_id supprimés")

    # Passe 2 : doublons géographiques (arrondi à ~100m = 3 décimales)
    df["_lat_round"] = df["latitude"].round(3)
    df["_lon_round"] = df["longitude"].round(3)

    # Parmi les géo-doublons, garder la ligne avec le moins de NaN
    df["_n_missing"] = df.isnull().sum(axis=1)
    df = df.sort_values("_n_missing")
    df = df.drop_duplicates(subset=["_lat_round", "_lon_round"], keep="first")

    n_geo_removed = n_after_pass1 - len(df)
    if n_geo_removed > 0:
        print(f"  [DEDUP] {n_geo_removed} doublons géographiques supprimés")

    df = df.drop(columns=["_lat_round", "_lon_round", "_n_missing"])
    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# FONCTIONS D'IMPUTATION
# ---------------------------------------------------------------------------

def impute_numerical(df: pd.DataFrame) -> pd.DataFrame:
    """
    Impute les valeurs numériques manquantes par la médiane.

    POURQUOI LA MÉDIANE et pas la MOYENNE ?
      La médiane est le quantile 50% — elle n'est pas affectée par les
      outliers. Exemple : si 44 panneaux ont une hauteur entre 3 et 10m
      et un a 50m (erreur de saisie non détectée), la moyenne serait faussée
      mais la médiane resterait réaliste.

    POURQUOI PAS kNN Imputer ou MICE ?
      Ces méthodes sont plus précises mais plus complexes. Pour un prototype
      à 45 lignes, la médiane est suffisante et compréhensible.
      → À ajouter en V2 quand le dataset sera plus grand.

    TRAÇABILITÉ : On enregistre la valeur utilisée pour chaque colonne.
    """
    num_cols = [
        "height_m", "size_m2", "traffic_flow_estim",
        "distance_to_main_road_m", "hours_of_daylight_exposure",
        "pedestrian_density_score"
    ]

    imputation_values = {}
    for col in num_cols:
        if col in df.columns and df[col].isnull().any():
            median_val = df[col].median()
            n_imputed  = df[col].isnull().sum()
            df[col]    = df[col].fillna(median_val)
            imputation_values[col] = round(median_val, 2)
            print(f"  [IMPUTE] '{col}' : {n_imputed} NaN → médiane={median_val:.2f}")

    return df


def impute_categorical(df: pd.DataFrame) -> pd.DataFrame:
    """
    Impute les catégoriques manquantes.

    STRATÉGIE :
      - 'proprietaire' → "Inconnu" (on ne peut pas deviner le propriétaire)
      - 'quartier', 'panel_type', 'road_type' → mode (rarement manquants)

    NOTE : On aurait pu utiliser 'Inconnu' pour tout, mais pour panel_type
    et road_type, le mode est plus informatif et n'introduit pas une nouvelle
    catégorie qui créerait des problèmes d'encodage en production.
    """
    cat_imputation = {
        "proprietaire": "Inconnu",
        "quartier":     df["quartier"].mode()[0] if df["quartier"].isnull().any() else None,
        "panel_type":   df["panel_type"].mode()[0] if df["panel_type"].isnull().any() else None,
        "road_type":    df["road_type"].mode()[0] if df["road_type"].isnull().any() else None,
    }

    for col, val in cat_imputation.items():
        if col in df.columns and val is not None and df[col].isnull().any():
            n_imputed = df[col].isnull().sum()
            df[col]   = df[col].fillna(val)
            print(f"  [IMPUTE] '{col}' : {n_imputed} NaN → '{val}'")

    return df


# ---------------------------------------------------------------------------
# AUDIT & RAPPORT
# ---------------------------------------------------------------------------

def generate_quality_report(df_raw: pd.DataFrame, df_clean: pd.DataFrame) -> Dict[str, Any]:
    """
    Génère un rapport de qualité des données avant/après cleaning.

    UTILITÉ : En production, ce rapport est présenté au comité de données
    pour valider la qualité avant tout entraînement de modèle.
    """
    report = {
        "rows_before":    len(df_raw),
        "rows_after":     len(df_clean),
        "rows_removed":   len(df_raw) - len(df_clean),
        "columns":        list(df_clean.columns),
        "missing_before": df_raw.isnull().sum().to_dict(),
        "missing_after":  df_clean.isnull().sum().to_dict(),
        "dtypes":         df_clean.dtypes.astype(str).to_dict(),
        "stats_target":   df_clean["visibility_score_clean"].describe().round(2).to_dict(),
    }
    return report


# ---------------------------------------------------------------------------
# PIPELINE PRINCIPAL
# ---------------------------------------------------------------------------

def clean_pipeline(df: pd.DataFrame, config: dict) -> tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Pipeline de nettoyage complet, exécuté dans un ordre précis.

    ORDRE DES ÉTAPES — Pourquoi cet ordre ?
      1. Validation coordonnées → supprimer les lignes invalides EN PREMIER
         pour que les stats calculées ensuite (médiane, mode) soient propres
      2. Validation scores → clipping avant imputation
      3. Suppression doublons → réduire le biais d'imputation
      4. Imputation numériques → toujours avant l'encodage
      5. Imputation catégoriques → en dernier pour éviter d'imputer une
         catégorie sur une ligne qui aurait dû être supprimée

    DÉCISION : Pipeline linéaire (pas de sklearn Pipeline) pour ce prototype —
    plus lisible et débogable. En production, utiliser sklearn.pipeline.Pipeline
    pour garantir que les mêmes transformations s'appliquent au test set.
    """
    df_raw  = df.copy()
    geo_cfg = config["geography"]
    cln_cfg = config["cleaning"]

    print("\n[CLEANING] Début du pipeline de nettoyage...")
    print(f"  Lignes initiales : {len(df)}")

    # Étape 1 : Coordonnées GPS invalides
    df = validate_coordinates(df, geo_cfg)

    # Étape 2 : Scores hors plage
    df = validate_visibility_score(df, cln_cfg)

    # Étape 3 : Doublons
    df = remove_duplicates(df)

    # Étape 4 : Imputation numériques
    df = impute_numerical(df)

    # Étape 5 : Imputation catégoriques
    df = impute_categorical(df)

    # Étape 6 : Cast des types (sécurité)
    df["traffic_flow_estim"]      = df["traffic_flow_estim"].astype(int)
    df["competition_radius_500m"] = df["competition_radius_500m"].astype(int)
    df["year_installed"]          = df["year_installed"].astype(int)
    df["has_photo"]               = df["has_photo"].astype(bool)

    # Renommer la cible nettoyée pour distinguer du score brut
    df = df.rename(columns={"visibility_score": "visibility_score_clean"})

    print(f"  Lignes finales   : {len(df)}")
    print(f"  NaN restants     : {df.isnull().sum().sum()}")
    print("[CLEANING] Pipeline terminé.\n")

    report = generate_quality_report(df_raw, df)
    return df, report


def run(config_path: str = "config/config.yaml") -> pd.DataFrame:
    """Point d'entrée du module."""
    with open(config_path) as f:
        config = yaml.safe_load(f)

    raw_path = config["paths"]["raw_data"]
    df_raw   = pd.read_csv(raw_path)
    print(f"[CLEANING] Dataset brut chargé : {len(df_raw)} lignes, {df_raw.shape[1]} colonnes")

    df_clean, report = clean_pipeline(df_raw, config)

    out_path = Path(config["paths"]["processed_data"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(out_path, index=False)
    print(f"[CLEANING] Dataset propre sauvegardé → {out_path}")

    return df_clean, report


if __name__ == "__main__":
    run()
