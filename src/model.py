"""
==============================================================================
MODULE : model.py
==============================================================================

RÔLE : Entraînement, comparaison et gestion des modèles prédictifs.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
POURQUOI RANDOM FOREST ET PAS RÉGRESSION LINÉAIRE ?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  RÉGRESSION LINÉAIRE — Hypothèse forte :
  ----------------------------------------
    score = β0 + β1·trafic + β2·taille + β3·hauteur + ... + ε

    Cette équation suppose que chaque feature a un effet ADDITIF et CONSTANT
    sur le score. Or, dans notre domaine :

    1. L'effet de la taille est diminuant (log, pas linéaire).
       +1m² de la 1ère à la 2ème → +5 pts
       +1m² de la 20ème à la 21ème → +0.5 pts

    2. La hauteur a un optimum (6–8m) — un panneau trop haut est moins visible.
       Relation gaussienne, pas linéaire.

    3. Les interactions comptent : un panneau digital sur un boulevard passe
       de 70 à 90 pts, mais un panneau digital en rue secondaire va de 35 à 40 pts
       seulement. La régression linéaire ne peut pas capturer cet EFFET D'INTERACTION
       sans ingénierie manuelle (feature croisée trafic × panel_type).

    4. La régression linéaire est très sensible aux outliers résiduels du dataset.
       Même après cleaning, quelques valeurs extrêmes faussent les coefficients β.

  RANDOM FOREST — Adapté à notre problème :
  ------------------------------------------
    Le RandomForest est un ensemble de B arbres de décision.
    Chaque arbre apprend des RÈGLES BINAIRES non-linéaires :

      Si trafic > 5000 ET panel_type = digital ALORS score ~ 80
      Si trafic <= 5000 ET distance_route > 50m ALORS score ~ 40

    PROPRIÉTÉS CLÉS :

    1. Non-linéarité native : capture automatiquement les relations en log,
       gaussiennes, par seuils — sans feature engineering supplémentaire.

    2. Interactions implicites : chaque nœud peut splitter sur une feature,
       la suivante dépend du sous-ensemble → interactions capturées naturellement.

    3. Invariance d'échelle : les splits sont binaires (feature > seuil).
       Qu'une feature soit en mètres ou en km ne change rien — pas de StandardScaler.

    4. Robustesse aux outliers : un outlier influence UN arbre sur 100, pas
       l'ensemble. La moyenne des 100 arbres absorbe les valeurs extrêmes.

    5. Pas de multicollinéarité problématique : là où la régression OLS devient
       instable quand deux features sont corrélées (ex: traffic_flow ET log_traffic),
       le RF les traite indépendamment par bootstrap et feature sampling.

  TABLEAU COMPARATIF :
  ─────────────────────────────────────────────────────────────────────────
  Critère                  │ Ridge Regression       │ Random Forest
  ─────────────────────────┼────────────────────────┼──────────────────────
  Relation apprise         │ Linéaire uniquement    │ Non-linéaire native
  Interactions features    │ Manuelle (feature×feat)│ Automatique
  Outliers                 │ Sensible               │ Robuste
  Normalisation            │ Requise (StandardScaler)│ Non requise
  Feature importance       │ |coefficients| normés  │ Réduction d'impureté
  Petit dataset (40 obs)   │ Stable mais biaisé     │ Variance élevée sans régul.
  Interprétabilité globale │ Très lisible (β)        │ Moins direct (ensemble)
  Risque overfitting       │ Faible (régularisation)│ Modéré (contrôlé par depth)
  ─────────────────────────────────────────────────────────────────────────

  CONCLUSION : Pour notre V1 avec un dataset bruité à 45 observations,
  le RandomForest EST meilleur si bien régularisé (max_depth=4, min_leaf=4).
  On l'évalue TOUJOURS contre une baseline Ridge pour valider la valeur ajoutée.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RISQUES D'OVERFITTING AVEC UN PETIT DATASET
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  L'overfitting = le modèle mémorise le bruit du train set au lieu d'apprendre
  le signal. Signes caractéristiques :

    R²_train >> R²_test   → le modèle performe bien en train, mal en test
    CV R² instable        → scores très variables d'un fold à l'autre
    OOB R² faible         → les arbres hors-bootstrap ne prédisent pas bien

  POUR 43 OBSERVATIONS ET 23 FEATURES — RISQUE ÉLEVÉ :
    Le ratio n/p = 43/23 ≈ 1.9. En ML, on veut n/p > 10–20 pour fiabilité.
    Avec n/p faible :
    - Un modèle sans contrainte mémorise chaque point (arbre profond = 1 feuille/obs)
    - La CV 5-fold donne des folds de 8 obs train → variance naturellement élevée

  LEVIERS DE RÉGULARISATION UTILISÉS :
  ┌─────────────────────────────────────────────────────────────────┐
  │ Paramètre          │ Valeur │ Effet                             │
  ├────────────────────┼────────┼───────────────────────────────────┤
  │ max_depth          │ 4      │ Limite la profondeur des arbres   │
  │ min_samples_split  │ 6      │ Nœud doit avoir ≥6 obs pour splitter│
  │ min_samples_leaf   │ 4      │ Feuille doit avoir ≥4 obs         │
  │ n_estimators       │ 100    │ 100 arbres → variance réduite     │
  │ oob_score          │ True   │ Validation gratuite (bootstrap)   │
  └─────────────────────────────────────────────────────────────────┘

  LA LEARNING CURVE comme diagnostic :
    En traçant R²_train et R²_CV vs la taille du dataset, on visualise :
    - Gap (train - CV) important → overfitting
    - Convergence des courbes → le modèle apprend le vrai signal
    - Plateau de CV → plus de données n'aidera pas → feature engineering nécessaire

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VALIDATION CROISÉE — POURQUOI ET COMMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  PROBLÈME DU SIMPLE TRAIN/TEST SPLIT :
    Avec 43 obs, le test set a ~9 observations.
    La variance de R² sur 9 points est ÉNORME — un seul mauvais point
    peut faire chuter R² de 0.6 à 0.2. Ce n'est pas un signal fiable.

  K-FOLD CROSS-VALIDATION (K=5) :
    1. Diviser les données en 5 blocs égaux (~8-9 obs chacun)
    2. Pour chaque fold i : entraîner sur les 4 autres blocs, évaluer sur le fold i
    3. Répéter 5 fois → 5 scores R²
    4. Retourner mean ± std

    Chaque observation est utilisée EXACTEMENT une fois en validation.
    → Estimation non biaisée de la performance en généralisation.

  OOB SCORE — La validation "gratuite" :
    Le bootstrap tire n observations avec remise → ~37% ne sont jamais tirées
    pour un arbre donné. Ces ~37% servent de validation pour cet arbre.
    OOB R² ≈ moyenne des scores out-of-bag sur tous les arbres.
    C'est conceptuellement équivalent à une LOO-CV (Leave-One-Out) mais gratuit.

==============================================================================
"""

import numpy as np
import pandas as pd
import yaml
import pickle
from pathlib import Path
from typing import Optional

from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, cross_val_score, KFold, learning_curve
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error


# ---------------------------------------------------------------------------
# CLASSE : BASELINE RÉGRESSION RIDGE
# ---------------------------------------------------------------------------

class RidgeBaselineModel:
    """
    Modèle de référence (baseline) basé sur la régression Ridge.

    RÔLE DE LA BASELINE :
      Tout modèle ML doit être comparé à un modèle plus simple.
      Si le RandomForest ne fait pas mieux que la régression Ridge,
      il n'y a PAS de valeur ajoutée à sa complexité.

    POURQUOI RIDGE ET PAS RÉGRESSION ORDINAIRE (OLS) ?
      Ridge = OLS + régularisation L2 : minimise ||y - Xβ||² + α||β||²
      Le terme α||β||² "pénalise" les grands coefficients → anti-overfitting.
      Avec n/p faible (43 obs / 23 features), OLS diverge souvent.
      Ridge reste stable grâce à α (ici alpha=1.0, valeur classique).

    NORMALISATION OBLIGATOIRE :
      La Ridge Regression est sensible aux échelles — une feature en milliers
      (trafic) aurait un coefficient très petit vs une feature en 0–1.
      On intègre StandardScaler dans un Pipeline sklearn pour garantir
      la normalisation automatique, y compris en prédiction.
    """

    def __init__(self, alpha: float = 1.0):
        self.alpha       = alpha
        self.is_trained  = False
        self.feature_names: Optional[list] = None
        # Pipeline : StandardScaler → Ridge
        # Le Pipeline garantit que le scaler est fitté UNIQUEMENT sur le train set
        self.model = Pipeline([
            ("scaler", StandardScaler()),
            ("ridge",  Ridge(alpha=alpha)),
        ])

    def train(self, X_train: pd.DataFrame, y_train: pd.Series) -> None:
        self.feature_names = list(X_train.columns)
        self.model.fit(X_train, y_train)
        self.is_trained = True
        print(f"  [BASELINE] Ridge (α={self.alpha}) entraîné sur {len(X_train)} obs")
        print(f"  [BASELINE] Coefficients Ridge (top 5 en valeur absolue) :")
        coeffs = pd.Series(
            self.model.named_steps["ridge"].coef_,
            index=self.feature_names
        ).abs().sort_values(ascending=False)
        for feat, val in coeffs.head(5).items():
            print(f"             |β_{feat}| = {val:.3f}")

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_trained:
            raise RuntimeError("Baseline non entraîné.")
        return np.clip(self.model.predict(X), 0, 100)

    def cross_validate(self, X: pd.DataFrame, y: pd.Series, cv: int = 5, seed: int = 42) -> dict:
        kf     = KFold(n_splits=cv, shuffle=True, random_state=seed)
        scores = cross_val_score(self.model, X, y, cv=kf, scoring="r2")
        result = {
            "cv_r2_mean": round(float(scores.mean()), 4),
            "cv_r2_std":  round(float(scores.std()),  4),
            "cv_r2_all":  [round(float(s), 4) for s in scores],
        }
        print(f"  [BASELINE CV] Ridge CV R² = {result['cv_r2_mean']:.3f} ± {result['cv_r2_std']:.3f}")
        return result


# ---------------------------------------------------------------------------
# CLASSE : MODÈLE PRINCIPAL (RANDOM FOREST)
# ---------------------------------------------------------------------------

class BillboardVisibilityModel:
    """
    Wrapper autour du RandomForestRegressor pour le projet Billboard.

    POURQUOI UNE CLASSE et pas des fonctions ?
      En production, on veut pouvoir :
      1. Sérialiser (pickle) le modèle avec ses métadonnées
      2. Appeler model.predict(new_data) de façon cohérente
      3. Accéder à model.feature_importance_ sans recalculer
      4. Comparer facilement avec la baseline via une interface identique
    """

    def __init__(self, config: dict):
        self.config      = config
        self.ml_cfg      = config["model"]
        self.feature_names: Optional[list] = None
        self.is_trained  = False

        hp = self.ml_cfg["hyperparameters"]
        self.model = RandomForestRegressor(
            n_estimators      = hp["n_estimators"],
            max_depth         = hp["max_depth"],
            min_samples_split = hp["min_samples_split"],
            min_samples_leaf  = hp["min_samples_leaf"],
            random_state      = hp["random_state"],
            n_jobs            = -1,
            oob_score         = True,  # Validation out-of-bag gratuite
        )

    def split_data(self, X: pd.DataFrame, y: pd.Series) -> tuple:
        """
        Sépare train/test (80/20).

        NOTE SUR 9 OBS DE TEST :
          Avec ~43 obs et 20% de test → 9 lignes de test.
          Le R² sur 9 obs a une variance intrinsèque élevée.
          La CV 5-fold sur le train set est plus fiable pour comparer les modèles.
          Le test set sert uniquement à la validation finale (évaluation non biaisée).
        """
        test_size    = self.ml_cfg["test_size"]
        random_state = self.ml_cfg["hyperparameters"]["random_state"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, shuffle=True
        )

        print(f"  [SPLIT] Train: {len(X_train)} obs | Test: {len(X_test)} obs")
        print(f"  [SPLIT] y_train — μ={y_train.mean():.1f}, σ={y_train.std():.1f}")
        print(f"  [SPLIT] y_test  — μ={y_test.mean():.1f},  σ={y_test.std():.1f}")
        return X_train, X_test, y_train, y_test

    def train(self, X_train: pd.DataFrame, y_train: pd.Series) -> None:
        """
        Entraîne le RandomForest.

        MÉCANISME INTERNE :
          Chaque arbre t est entraîné sur B_t = bootstrap(X_train) :
          → tirage de n observations avec remise → ~63% d'obs uniques par arbre
          À chaque nœud, seuls sqrt(n_features) features sont candidats au split
          → les arbres sont décorrélés → la moyenne réduit la variance

        OOB R² :
          Les ~37% d'observations non tirées par arbre t → score OOB de t
          Agrégé sur tous les arbres → OOB R² global (validation sans test set)
          Si OOB R² << Train R² : signal d'overfitting.
        """
        self.feature_names = list(X_train.columns)
        self.model.fit(X_train, y_train)
        self.is_trained = True

        oob = self.model.oob_score_
        print(f"  [TRAIN] RandomForest entraîné sur {len(X_train)} observations")
        print(f"  [TRAIN] OOB R² = {oob:.3f}")
        if oob < 0.2:
            print(f"  [TRAIN] ⚠ OOB faible → fort overfitting probable")
        elif oob < 0.4:
            print(f"  [TRAIN] OOB modéré → acceptable pour petit dataset bruité")
        else:
            print(f"  [TRAIN] OOB correct → bonne généralisation interne")

    def cross_validate(self, X: pd.DataFrame, y: pd.Series) -> dict:
        """
        K-Fold Cross-Validation (K=5).

        INTERPRÉTATION DES SCORES NÉGATIFS :
          Avec K=5 et ~34 obs train → ~27 obs par fold de train, 7 en validation.
          Sur 7 obs, si le modèle se trompe sur 2–3 → R² peut être très négatif.
          R² < 0 signifie : "Le modèle fait PIRE que prédire la moyenne sur ce fold".
          C'est la réalité statistique d'un petit dataset bruité, pas un bug.

          Ce qui importe : la MOYENNE des folds sur 5 évaluations indépendantes.
          Un CV R² de -0.1 ± 0.3 = "le modèle n'a pas appris de signal stable".
          Un CV R² de 0.3 ± 0.2 = "il y a un signal mais il faut plus de données".
        """
        kf = KFold(
            n_splits     = self.ml_cfg["cv_folds"],
            shuffle      = True,
            random_state = self.ml_cfg["hyperparameters"]["random_state"]
        )
        scores = cross_val_score(self.model, X, y, cv=kf, scoring="r2")

        cv_results = {
            "cv_r2_mean": round(float(scores.mean()), 4),
            "cv_r2_std":  round(float(scores.std()),  4),
            "cv_r2_all":  [round(float(s), 4) for s in scores],
            "n_folds":    self.ml_cfg["cv_folds"],
        }

        print(f"  [CV] {self.ml_cfg['cv_folds']}-Fold CV R² = "
              f"{cv_results['cv_r2_mean']:.3f} ± {cv_results['cv_r2_std']:.3f}")
        print(f"  [CV] Scores par fold : {cv_results['cv_r2_all']}")

        if cv_results["cv_r2_std"] > 0.25:
            print(f"  [CV] ⚠ Variance élevée (std={cv_results['cv_r2_std']:.3f}) — "
                  f"normal avec {self.ml_cfg['cv_folds']} folds sur petit dataset")

        return cv_results

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_trained:
            raise RuntimeError("Modèle non entraîné. Appeler train() d'abord.")
        return np.clip(self.model.predict(X), 0, 100)

    def get_feature_importance(self) -> pd.DataFrame:
        """
        Importance des features par réduction d'impureté (MDI).

        MEAN DECREASE IN IMPURITY (MDI) :
          Pour chaque feature, on mesure la réduction moyenne de MSE
          (variance résiduelle) apportée par tous les splits sur cette feature,
          moyennée sur tous les arbres de la forêt.

          importance(f) = Σ_arbres Σ_nœuds_utilisant_f [p(nœud) × ΔImpureté(nœud)]
          normalisé pour sommer à 1.

        LIMITES CONNUES DU MDI :
          - Biais vers les features à haute cardinalité (ex: latitude continue
            peut être splitée en beaucoup plus d'endroits que is_digital ∈ {0,1})
          - Les features corrélées "se partagent" l'importance : si log_traffic
            et traffic_flow_estim sont corrélés, leur importance individuelle
            est sous-estimée par rapport à leur importance conjointe.

        ALTERNATIVE (V2) : Permutation Importance — plus juste mais 10x plus lent.
        ALTERNATIVE (V2) : SHAP values — décomposition par observation, la plus précise.
        """
        if not self.is_trained:
            raise RuntimeError("Modèle non entraîné.")

        importance_df = pd.DataFrame({
            "feature":    self.feature_names,
            "importance": self.model.feature_importances_,
        }).sort_values("importance", ascending=False).reset_index(drop=True)

        importance_df["importance_pct"] = (importance_df["importance"] * 100).round(2)
        importance_df["cumulative_pct"] = importance_df["importance_pct"].cumsum().round(1)
        return importance_df

    def save(self, path: str = "reports/model.pkl") -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(self, f)
        print(f"  [SAVE] Modèle sauvegardé → {path}")

    @classmethod
    def load(cls, path: str) -> "BillboardVisibilityModel":
        with open(path, "rb") as f:
            return pickle.load(f)


# ---------------------------------------------------------------------------
# COMPARAISON MODÈLES
# ---------------------------------------------------------------------------

def compare_with_baseline(
    rf_model: BillboardVisibilityModel,
    baseline: RidgeBaselineModel,
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
) -> dict:
    """
    Compare le RandomForest à la baseline Ridge sur les métriques clés.

    POURQUOI CETTE COMPARAISON EST INDISPENSABLE :
      Sans baseline, on ne sait pas si le RandomForest "apprend vraiment".
      Si Ridge R²=0.30 et RF R²=0.32, la complexité du RF ne se justifie pas.
      Si Ridge R²=0.25 et RF R²=0.50, le RF apporte 2× plus de signal.

    RETOUR :
      Dictionnaire avec métriques des deux modèles + différences relatives.
    """
    def _metrics(y_t, y_p):
        return {
            "r2":   round(r2_score(y_t, y_p), 4),
            "rmse": round(float(np.sqrt(mean_squared_error(y_t, y_p))), 3),
            "mae":  round(float(mean_absolute_error(y_t, y_p)), 3),
        }

    # Prédictions RF
    rf_train_pred = rf_model.predict(X_train)
    rf_test_pred  = rf_model.predict(X_test)

    # Prédictions baseline
    b_train_pred  = baseline.predict(X_train)
    b_test_pred   = baseline.predict(X_test)

    rf_train_m  = _metrics(y_train.values, rf_train_pred)
    rf_test_m   = _metrics(y_test.values,  rf_test_pred)
    b_train_m   = _metrics(y_train.values, b_train_pred)
    b_test_m    = _metrics(y_test.values,  b_test_pred)

    # Gain du RF sur la baseline (test set)
    rmse_gain_pct = (b_test_m["rmse"] - rf_test_m["rmse"]) / b_test_m["rmse"] * 100
    r2_gain_abs   = rf_test_m["r2"] - b_test_m["r2"]

    comparison = {
        "random_forest": {"train": rf_train_m, "test": rf_test_m},
        "ridge_baseline": {"train": b_train_m, "test": b_test_m},
        "rf_vs_baseline": {
            "rmse_gain_pct":    round(rmse_gain_pct, 1),
            "r2_gain_absolute": round(r2_gain_abs,   4),
            "rf_wins_on_test":  rf_test_m["rmse"] < b_test_m["rmse"],
        },
    }

    print(f"\n  --- Comparaison RF vs Baseline (Test Set) ---")
    print(f"  {'Métrique':<12} {'RandomForest':>15} {'Ridge Baseline':>16} {'Gain RF':>10}")
    print(f"  {'-'*55}")
    print(f"  {'R²':<12} {rf_test_m['r2']:>15.4f} {b_test_m['r2']:>16.4f} "
          f"{r2_gain_abs:>+10.4f}")
    print(f"  {'RMSE (pts)':<12} {rf_test_m['rmse']:>15.3f} {b_test_m['rmse']:>16.3f} "
          f"{rmse_gain_pct:>+9.1f}%")
    print(f"  {'MAE (pts)':<12} {rf_test_m['mae']:>15.3f} {b_test_m['mae']:>16.3f}")

    if comparison["rf_vs_baseline"]["rf_wins_on_test"]:
        print(f"\n  → RandomForest GAGNE sur la baseline (RMSE {rmse_gain_pct:+.1f}%)")
    else:
        print(f"\n  → Baseline GAGNE sur ce test set (bruit élevé, 9 obs test)")
        print(f"    Interpréter avec la CV pour décision finale.")

    return comparison


# ---------------------------------------------------------------------------
# LEARNING CURVE
# ---------------------------------------------------------------------------

def compute_learning_curve(
    model: BillboardVisibilityModel,
    X: pd.DataFrame,
    y: pd.Series,
    config: dict,
) -> dict:
    """
    Calcule la courbe d'apprentissage du RandomForest.

    QU'EST-CE QU'UNE LEARNING CURVE ?
      On entraîne le modèle sur des sous-ensembles de taille croissante du
      dataset (10%, 30%, 50%, 70%, 100% des données de train) et on mesure
      à chaque fois le score train et le score en CV.

    COMMENT LIRE LA COURBE :
      ┌──────────────────────────────────────────────────────┐
      │ R²                                                   │
      │ 1.0 ┤ ──── Train                                    │
      │     │      ╲                                        │
      │ 0.7 ┤       ╲──────────────  Train converge         │
      │     │                ╱                              │
      │ 0.4 ┤    ────────────  CV converge                  │
      │     │   ╱                                           │
      │ 0.1 ┤  ╱  gap = OVERFITTING                        │
      │     └──────────────────────────────── n_train       │
      │          10%  30%  50%  70%  100%                   │
      └──────────────────────────────────────────────────────┘

      Si les deux courbes convergent → le modèle generalise bien
      Si le gap reste constant → plus de données aidera (non saturé)
      Si le gap diminue → la régularisation est efficace
      Si les deux plafonnent bas → plus de features nécessaires

    DÉCISION TECHNIQUE :
      train_sizes = [0.2, 0.4, 0.6, 0.8, 1.0] de X_train (pas tout X)
      Pour chaque taille : 3-fold CV (et non 5, car très peu d'obs par fold sinon)
    """
    seed = config["model"]["hyperparameters"]["random_state"]

    # On utilise sklearn.model_selection.learning_curve
    # cv=3 car avec n_train_min ~= 0.2 * 34 ≈ 7 obs, 5-fold serait trop petit
    train_sizes_abs, train_scores, val_scores = learning_curve(
        estimator    = model.model,
        X            = X,
        y            = y,
        train_sizes  = np.linspace(0.3, 1.0, 6),
        cv           = 3,
        scoring      = "r2",
        random_state = seed,
        n_jobs       = -1,
        shuffle      = True,
    )

    lc_data = {
        "train_sizes":        train_sizes_abs.tolist(),
        "train_scores_mean":  np.mean(train_scores, axis=1).round(4).tolist(),
        "train_scores_std":   np.std(train_scores,  axis=1).round(4).tolist(),
        "val_scores_mean":    np.mean(val_scores,   axis=1).round(4).tolist(),
        "val_scores_std":     np.std(val_scores,    axis=1).round(4).tolist(),
    }

    print(f"\n  --- Learning Curve (3-fold CV) ---")
    print(f"  {'N_train':<10} {'Train R²':>10} {'Val R²':>10} {'Gap':>8}")
    for n, tr, vl in zip(
        lc_data["train_sizes"],
        lc_data["train_scores_mean"],
        lc_data["val_scores_mean"]
    ):
        print(f"  {n:<10} {tr:>10.3f} {vl:>10.3f} {tr - vl:>+8.3f}")

    return lc_data


# ---------------------------------------------------------------------------
# PIPELINE PRINCIPAL
# ---------------------------------------------------------------------------

def training_pipeline(
    X: pd.DataFrame,
    y: pd.Series,
    config: dict
) -> tuple:
    """
    Pipeline complet d'entraînement.

    ORDRE :
      1. Split train/test (figé pour toute la session)
      2. Entraînement baseline Ridge (pour comparaison)
      3. CV du RandomForest sur X_train
      4. Entraînement final RandomForest sur X_train
      5. Comparaison RF vs Baseline sur test set
      6. Learning curve pour diagnostic overfitting

    RETOUR :
      rf_model      : Modèle RF entraîné
      baseline      : Modèle Ridge entraîné
      split_data    : dict X_train/X_test/y_train/y_test
      cv_results    : dict métriques CV du RF
      comparison    : dict comparaison RF vs Ridge
      lc_data       : dict données de la learning curve
    """
    print("\n[MODEL TRAINING] Démarrage...")

    rf_model = BillboardVisibilityModel(config)
    X_train, X_test, y_train, y_test = rf_model.split_data(X, y)

    # --- Baseline Ridge ---
    print("\n  === Baseline : Ridge Regression ===")
    baseline = RidgeBaselineModel(alpha=1.0)
    baseline.train(X_train, y_train)
    baseline_cv = baseline.cross_validate(X_train, y_train,
                                          cv=config["model"]["cv_folds"],
                                          seed=config["model"]["hyperparameters"]["random_state"])

    # --- RandomForest : Cross-Validation ---
    print("\n  === RandomForest : Cross-Validation ===")
    cv_results = rf_model.cross_validate(X_train, y_train)

    # --- RandomForest : Entraînement final ---
    print("\n  === RandomForest : Entraînement final ===")
    rf_model.train(X_train, y_train)

    # --- Top features ---
    feat_imp = rf_model.get_feature_importance()
    print(f"\n  --- Top 10 Features (MDI Importance) ---")
    print(f"  {'Feature':<35} {'Importance':>11} {'Cumulatif':>10}")
    print(f"  {'-'*58}")
    for _, row in feat_imp.head(10).iterrows():
        print(f"  {row['feature']:<35} {row['importance_pct']:>10.2f}% {row['cumulative_pct']:>9.1f}%")

    # --- Comparaison RF vs Baseline ---
    print("\n  === Comparaison RF vs Baseline ===")
    comparison = compare_with_baseline(
        rf_model, baseline, X_train, X_test, y_train, y_test
    )
    comparison["baseline_cv"] = baseline_cv

    # --- Learning Curve ---
    print("\n  === Learning Curve (diagnostic overfitting) ===")
    lc_data = compute_learning_curve(rf_model, X_train, y_train, config)

    split_data = {
        "X_train": X_train, "X_test": X_test,
        "y_train": y_train, "y_test": y_test,
    }

    print("\n[MODEL TRAINING] Terminé.\n")
    return rf_model, baseline, split_data, cv_results, comparison, lc_data


def run(config_path: str = "config/config.yaml"):
    """Point d'entrée standalone."""
    from src.data_generation import generate_billboard_dataset
    from src.cleaning import clean_pipeline
    from src.feature_engineering import engineering_pipeline

    with open(config_path) as f:
        config = yaml.safe_load(f)

    df_raw              = generate_billboard_dataset(config)
    df_clean, _         = clean_pipeline(df_raw, config)
    X, y, feat_cols, _  = engineering_pipeline(df_clean, config)
    return training_pipeline(X, y, config)


if __name__ == "__main__":
    run()
