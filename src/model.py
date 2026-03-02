"""
==============================================================================
MODULE : model.py
==============================================================================

RÔLE : Entraînement et gestion du modèle prédictif de visibilité.

POURQUOI RANDOM FOREST ?
========================
Pour ce prototype, le RandomForestRegressor est le choix optimal :

1. ROBUSTESSE AUX PETITS DATASETS
   Avec 35-40 observations d'entraînement, un réseau de neurones serait
   largement sur-ajusté. Un RF avec max_depth=6 et min_samples_leaf=2
   reste généralisable.

2. PAS DE NORMALISATION REQUISE
   Les arbres font des splits binaires (feature > seuil). L'échelle des
   variables n'a aucun impact. Pas besoin de StandardScaler.

3. IMPORTANCE DES FEATURES BUILT-IN
   feature_importances_ donne directement la contribution de chaque
   feature à la réduction de variance (impurity). Très utile pour
   une présentation business.

4. ROBUSTESSE AUX OUTLIERS RÉSIDUELS
   Même après cleaning, quelques outliers peuvent subsister. Les arbres
   de décision sont peu sensibles aux valeurs extrêmes car ils font des
   splits, pas des moyennes globales.

5. INTERPRÉTABLE
   On peut visualiser les arbres, expliquer les prédictions avec SHAP.

ALTERNATIVES CONSIDÉRÉES :
- GradientBoosting/XGBoost : meilleure précision mais hyperparamètres plus
  sensibles, risque de surapprentissage avec 40 lignes.
- Ridge Regression : bon baseline, mais suppose une relation linéaire.
  Notre visibilité est clairement non-linéaire.
- KNN : sensible à l'échelle, pas de feature importance.

→ En V2 : tester XGBoost avec cross-validation sur un plus grand dataset.

HYPERPARAMÈTRES RETENUS :
  n_estimators=100  : 100 arbres → variance faible (plus d'arbres = meilleur,
                      mais rendements décroissants)
  max_depth=6       : arbres peu profonds → régularisation (anti-overfitting)
  min_samples_split=4 : un nœud doit avoir ≥4 obs pour être splitté
  min_samples_leaf=2  : chaque feuille doit avoir ≥2 obs (feuilles robustes)

==============================================================================
"""

import numpy as np
import pandas as pd
import json
import yaml
import pickle
from pathlib import Path
from typing import Optional

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score, KFold


# ---------------------------------------------------------------------------
# CLASSE MODÈLE
# ---------------------------------------------------------------------------

class BillboardVisibilityModel:
    """
    Wrapper autour du RandomForestRegressor pour le projet Billboard.

    POURQUOI UNE CLASSE et pas des fonctions ?
      En production, on veut pouvoir :
      1. Sérialiser le modèle (pickle/joblib) avec ses métadonnées
      2. Appeler model.predict(new_data) facilement
      3. Accéder à model.feature_importance_ sans recalculer
      4. Tracer l'historique d'entraînement (date, métriques, version)

    Cette classe encapsule tout cela proprement.
    """

    def __init__(self, config: dict):
        """
        Initialise le modèle avec la configuration YAML.

        PARAMÈTRES :
          config : dictionnaire chargé depuis config/config.yaml
        """
        self.config     = config
        self.ml_cfg     = config["model"]
        self.feature_names: Optional[list] = None
        self.model: Optional[RandomForestRegressor] = None
        self.is_trained = False

        # Initialiser le RandomForest avec les hyperparamètres du config
        hp = self.ml_cfg["hyperparameters"]
        self.model = RandomForestRegressor(
            n_estimators      = hp["n_estimators"],
            max_depth         = hp["max_depth"],
            min_samples_split = hp["min_samples_split"],
            min_samples_leaf  = hp["min_samples_leaf"],
            random_state      = hp["random_state"],
            n_jobs            = -1,    # Utiliser tous les CPU disponibles
            oob_score         = True,  # Out-of-bag score (validation gratuite)
        )

    def split_data(self, X: pd.DataFrame, y: pd.Series) -> tuple:
        """
        Sépare les données en train/test.

        STRATÉGIE : split simple (pas de stratification car régression, pas classification)
        PROPORTION : 80% train / 20% test (règle classique)

        POURQUOI PAS UNIQUEMENT LA CROSS-VALIDATION ?
          Pour un prototype, train/test split est suffisant et plus lisible.
          La CV est utilisée EN PLUS pour estimer la variance des métriques.

        NOTE SUR LES PETITS DATASETS :
          Avec ~40 observations, 20% = 8 lignes de test. C'est peu, donc
          les métriques seront variables d'une run à l'autre. La CV sur 5 folds
          donne une estimation plus stable.
        """
        test_size   = self.ml_cfg["test_size"]
        random_state = self.ml_cfg["hyperparameters"]["random_state"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size    = test_size,
            random_state = random_state,
            shuffle      = True    # Mélanger avant split (au cas où données triées)
        )

        print(f"  [SPLIT] Train: {len(X_train)} obs | Test: {len(X_test)} obs")
        print(f"  [SPLIT] Target train — mean: {y_train.mean():.1f}, std: {y_train.std():.1f}")
        print(f"  [SPLIT] Target test  — mean: {y_test.mean():.1f},  std: {y_test.std():.1f}")

        return X_train, X_test, y_train, y_test

    def train(self, X_train: pd.DataFrame, y_train: pd.Series) -> None:
        """
        Entraîne le RandomForest.

        COMMENT ÇA MARCHE ?
          1. Le RF construit n_estimators=100 arbres de décision
          2. Chaque arbre est entraîné sur un bootstrap du dataset
             (tirage avec remise de n_train observations)
          3. À chaque split, seules sqrt(n_features) features sont candidates
             (randomisation → arbres décorrélés)
          4. La prédiction finale = moyenne des 100 arbres

        OOB SCORE (Out-Of-Bag) :
          Pour chaque observation, ~37% des arbres ne l'ont pas vue
          (non tirées lors du bootstrap). On peut prédire avec ces arbres
          → score de validation "gratuit" sans toucher au test set.
          OOB R² proche de 0.5–0.7 est attendu avec nos données bruitées.
        """
        self.feature_names = list(X_train.columns)
        self.model.fit(X_train, y_train)
        self.is_trained = True

        oob = self.model.oob_score_
        print(f"  [TRAIN] Modèle entraîné sur {len(X_train)} observations")
        print(f"  [TRAIN] OOB R² = {oob:.3f}  (validation interne sans test set)")

    def cross_validate(self, X: pd.DataFrame, y: pd.Series) -> dict:
        """
        Cross-validation K-Fold sur les données d'entraînement complètes.

        POURQUOI LA CV ?
          Avec 40 obs, un seul train/test split peut être chanceux ou malchanceux.
          La CV sur 5 folds donne 5 évaluations différentes → on obtient :
          - CV mean R² : estimation non biaisée de la performance
          - CV std R²  : variance de la performance (stabilité)

        INTERPRÉTATION :
          CV R² = 0.55 ± 0.12 → "Le modèle explique ~55% de la variance,
          avec une incertitude de ±12 points selon le split"

          Si std > 0.15 sur un petit dataset, c'est normal et attendu.
        """
        kf = KFold(
            n_splits  = self.ml_cfg["cv_folds"],
            shuffle   = True,
            random_state = self.ml_cfg["hyperparameters"]["random_state"]
        )

        # Utiliser le même modèle (clone implicite par sklearn)
        scores = cross_val_score(self.model, X, y, cv=kf, scoring="r2")

        cv_results = {
            "cv_r2_mean": round(float(scores.mean()), 4),
            "cv_r2_std":  round(float(scores.std()), 4),
            "cv_r2_all":  [round(float(s), 4) for s in scores],
            "n_folds":    self.ml_cfg["cv_folds"],
        }

        print(f"  [CV] {self.ml_cfg['cv_folds']}-Fold CV R² = "
              f"{cv_results['cv_r2_mean']:.3f} ± {cv_results['cv_r2_std']:.3f}")
        print(f"  [CV] Scores par fold : {cv_results['cv_r2_all']}")

        return cv_results

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Prédit le score de visibilité pour de nouveaux panneaux.

        NOTE : En production, cette méthode recevrait un DataFrame avec les
        mêmes colonnes que X_train. Un pipeline sklearn garantirait la cohérence
        des transformations (encodage, features dérivées, etc.).
        """
        if not self.is_trained:
            raise RuntimeError("Le modèle n'est pas encore entraîné. Appeler train() d'abord.")

        predictions = self.model.predict(X)
        # Clip pour garantir que les prédictions restent dans [0, 100]
        return np.clip(predictions, 0, 100)

    def get_feature_importance(self) -> pd.DataFrame:
        """
        Retourne un DataFrame trié des importances de features.

        FEATURE IMPORTANCE du RandomForest :
          Mesure la réduction moyenne de variance (MSE) apportée par chaque
          feature sur tous les splits de tous les arbres.

          Une importance de 0.15 signifie que cette feature contribue à 15%
          de la réduction de variance totale.

        LIMITES :
          - Biais vers les features continues vs catégoriques
          - Les features corrélées se partagent l'importance
          → En V2 : utiliser SHAP values (plus précis et décomposable)
        """
        if not self.is_trained:
            raise RuntimeError("Modèle non entraîné.")

        importance_df = pd.DataFrame({
            "feature":    self.feature_names,
            "importance": self.model.feature_importances_,
        }).sort_values("importance", ascending=False).reset_index(drop=True)

        importance_df["importance_pct"] = (importance_df["importance"] * 100).round(2)

        return importance_df

    def save(self, path: str = "reports/model.pkl") -> None:
        """Sérialise le modèle entraîné."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(self, f)
        print(f"  [SAVE] Modèle sauvegardé → {path}")

    @classmethod
    def load(cls, path: str) -> "BillboardVisibilityModel":
        """Charge un modèle depuis le disque."""
        with open(path, "rb") as f:
            return pickle.load(f)


# ---------------------------------------------------------------------------
# PIPELINE PRINCIPAL
# ---------------------------------------------------------------------------

def training_pipeline(
    X: pd.DataFrame,
    y: pd.Series,
    config: dict
) -> tuple[BillboardVisibilityModel, dict, dict]:
    """
    Pipeline complet d'entraînement.

    RETOUR :
      trained_model : Modèle entraîné prêt à prédire
      split_data    : dict avec X_train, X_test, y_train, y_test
      cv_results    : Résultats de la cross-validation
    """
    print("\n[MODEL TRAINING] Démarrage...")

    bill_model = BillboardVisibilityModel(config)

    # Split train/test
    X_train, X_test, y_train, y_test = bill_model.split_data(X, y)

    # Cross-validation sur toutes les données (avant fit final)
    # IMPORTANT : On fait la CV AVANT le fit final pour que la CV soit honnête
    # (le modèle ne voit pas le test set lors de la CV)
    print("\n  --- Cross-Validation ---")
    cv_results = bill_model.cross_validate(X_train, y_train)

    # Entraînement final sur tout le train set
    print("\n  --- Entraînement final ---")
    bill_model.train(X_train, y_train)

    # Afficher les top features
    feat_imp = bill_model.get_feature_importance()
    print(f"\n  --- Top 10 Features Importantes ---")
    print(feat_imp.head(10).to_string(index=False))

    split_data = {
        "X_train": X_train,
        "X_test":  X_test,
        "y_train": y_train,
        "y_test":  y_test,
    }

    print("\n[MODEL TRAINING] Terminé.\n")
    return bill_model, split_data, cv_results


def run(config_path: str = "config/config.yaml"):
    """Point d'entrée du module (pour test standalone)."""
    from src.data_generation import run as gen_run
    from src.cleaning import run as clean_run
    from src.feature_engineering import run as fe_run

    with open(config_path) as f:
        config = yaml.safe_load(f)

    gen_run(config_path)
    clean_run(config_path)
    X, y, feat_cols, mappings = fe_run(config_path)
    model, split_data, cv_results = training_pipeline(X, y, config)
    return model, split_data, cv_results, feat_cols


if __name__ == "__main__":
    run()
