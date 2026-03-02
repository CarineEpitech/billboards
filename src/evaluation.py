"""
==============================================================================
MODULE : evaluation.py
==============================================================================

RÔLE : Évaluation complète — métriques, graphiques de comparaison RF vs Ridge,
       learning curve, analyse des résidus, rapport JSON.

GRAPHIQUES GÉNÉRÉS (6 au total) :
  01_pred_vs_actual.png     — Prédit vs Réel (test set, RandomForest)
  02_residuals.png          — Analyse des résidus (distribution, patterns)
  03_feature_importance.png — Top features par importance MDI + cumul
  04_score_distribution.png — Distribution train/test/prédit
  05_model_comparison.png   — RF vs Ridge sur R², RMSE, MAE (bar chart)
  06_learning_curve.png     — Train vs CV score selon taille dataset

MÉTRIQUES CALCULÉES :
  R²   : Proportion de variance expliquée (1=parfait, 0=prédire la moyenne)
  RMSE : Root Mean Squared Error — pénalise les grosses erreurs (unité : pts)
  MAE  : Mean Absolute Error — erreur médiane (unité : pts)
  MAPE : Mean Absolute Percentage Error — erreur en %
  MedAE: Median Absolute Error — robuste aux outliers de prédiction
  Within10 : % de prédictions dans ±10 pts du score réel

==============================================================================
"""

import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error


# ---------------------------------------------------------------------------
# MÉTRIQUES CORE
# ---------------------------------------------------------------------------

def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, dataset_name: str = "Test") -> Dict[str, float]:
    """
    Calcule l'ensemble des métriques d'évaluation.

    CHOIX DES MÉTRIQUES ET LEUR INTERPRÉTATION :

    R² (coefficient de détermination) :
      R² = 1 - SS_res/SS_tot = 1 - Σ(y - ŷ)² / Σ(y - ȳ)²
      Interprétation : proportion de variance de y expliquée par le modèle.
      R²=0.6 → le modèle explique 60% de la variabilité des scores.
      R²<0   → le modèle fait PIRE que prédire la moyenne constante.
      Limite : sensible au nombre d'observations (instable sur 9 obs test).

    RMSE vs MAE — quand utiliser lequel ?
      RMSE = sqrt(mean((y - ŷ)²)) → pénalise QUADRATIQUEMENT les grosses erreurs.
      MAE  = mean(|y - ŷ|)         → pénalise linéairement, robuste aux outliers.
      Si RMSE >> MAE : quelques très grosses erreurs dominent.
      Si RMSE ≈ MAE : erreurs uniformément distribuées.
      Dans notre contexte métier : MAE est plus interprétable business
      ("en moyenne, on se trompe de X points sur 100").

    Within10 : metric business custom.
      "Quel % de panneaux avons-nous scoré avec moins de 10 pts d'erreur ?"
      Très compréhensible pour un auditoire non-technique.
    """
    r2    = r2_score(y_true, y_pred)
    rmse  = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae   = float(mean_absolute_error(y_true, y_pred))
    mape  = float(np.mean(np.abs((y_true - y_pred) / np.clip(y_true, 1, None))) * 100)
    medae = float(np.median(np.abs(y_true - y_pred)))
    within_10 = float(np.mean(np.abs(y_true - y_pred) <= 10) * 100)

    metrics = {
        f"{dataset_name}_R2":              round(r2,       4),
        f"{dataset_name}_RMSE":            round(rmse,     3),
        f"{dataset_name}_MAE":             round(mae,      3),
        f"{dataset_name}_MAPE_pct":        round(mape,     2),
        f"{dataset_name}_MedAE":           round(medae,    3),
        f"{dataset_name}_Within10pts_pct": round(within_10, 1),
    }

    print(f"\n  --- Métriques {dataset_name} ---")
    print(f"  R²                 = {r2:.4f}")
    print(f"  RMSE               = {rmse:.2f} pts  (erreur quadratique moyenne)")
    print(f"  MAE                = {mae:.2f} pts  (erreur absolue moyenne)")
    print(f"  MAPE               = {mape:.1f}%")
    print(f"  MedAE              = {medae:.2f} pts  (médiane des erreurs absolues)")
    print(f"  Prédictions ±10pts = {within_10:.1f}%")

    if r2 < 0:
        print(f"  [DIAG] R² < 0 → modèle pire que la moyenne. Signe d'overfitting sur petit test set.")
    elif r2 < 0.3:
        print(f"  [DIAG] R² faible — attendu avec ~9 obs en test et données bruitées.")
    elif r2 < 0.5:
        print(f"  [DIAG] R² modéré — acceptable pour prototype V1.")
    else:
        print(f"  [DIAG] R² correct — bon signal appris.")

    return metrics


def detect_train_test_gap(train_metrics: dict, test_metrics: dict) -> str:
    """
    Détecte et caractérise l'overfitting.

    BIAIS-VARIANCE TRADEOFF :
      Tout modèle fait face à deux types d'erreurs :
      - BIAIS    : erreur systématique (modèle trop simple)
      - VARIANCE : sensibilité au dataset d'entraînement (modèle trop complexe)

      Gap R²_train - R²_test mesure la VARIANCE.
      Un modèle idéal a biais faible ET variance faible.
      Sur petit dataset, il faut accepter un compromis.
    """
    r2_train = train_metrics.get("Train_R2", 0)
    r2_test  = test_metrics.get("Test_R2", 0)
    gap      = r2_train - r2_test

    if gap > 0.30:
        d = f"Overfitting significatif (gap={gap:.3f}). Augmenter min_samples_leaf, réduire max_depth."
    elif gap > 0.15:
        d = f"Overfitting modéré (gap={gap:.3f}). Normal avec {9} obs test — évaluer sur CV."
    elif r2_train < 0.25 and r2_test < 0.25:
        d = f"Sous-ajustement (R²_train={r2_train:.3f}). Ajouter des features ou données."
    else:
        d = f"Équilibre biais-variance acceptable (gap={gap:.3f})."

    print(f"\n  [BIAIS-VARIANCE] {d}")
    return d


# ---------------------------------------------------------------------------
# VISUALISATIONS — MODÈLE UNIQUE
# ---------------------------------------------------------------------------

def plot_predictions_vs_actual(
    y_true: np.ndarray, y_pred: np.ndarray,
    title: str, save_path: str
) -> None:
    """
    Graphique Prédit vs Réel (scatter plot).

    LECTURE :
      Points sur la diagonale → prédictions parfaites.
      Points en rouge → erreur > 15 pts (cas difficiles).
      Zone verte → ±10 pts (critère business acceptable).
    """
    residuals = y_pred - y_true
    colors    = np.where(np.abs(residuals) > 15, "#e74c3c", "#2980b9")

    fig, ax = plt.subplots(figsize=(7, 6))
    ax.scatter(y_true, y_pred, c=colors, alpha=0.8, s=70,
               edgecolors="white", linewidths=0.5)

    lim = [max(0, min(y_true.min(), y_pred.min()) - 5),
           min(100, max(y_true.max(), y_pred.max()) + 5)]
    ax.plot(lim, lim, "k--", lw=1.5, alpha=0.7, label="Parfait (y=x)")
    ax.fill_between(lim, [lim[0]-10, lim[1]-10], [lim[0]+10, lim[1]+10],
                    alpha=0.07, color="#2ecc71", label="Zone ±10 pts")

    patches = [mpatches.Patch(color="#2980b9", label="Erreur ≤ 15 pts"),
               mpatches.Patch(color="#e74c3c", label="Erreur > 15 pts")]
    ax.legend(handles=patches + [ax.get_lines()[0]], fontsize=9, loc="upper left")

    r2   = r2_score(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    ax.text(0.05, 0.91, f"R² = {r2:.3f}  |  RMSE = {rmse:.1f} pts",
            transform=ax.transAxes, fontsize=10,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.8))

    ax.set_xlabel("Score réel (ground truth)", fontsize=11)
    ax.set_ylabel("Score prédit", fontsize=11)
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.set_xlim(lim); ax.set_ylim(lim); ax.grid(alpha=0.3)
    plt.tight_layout()
    _save(fig, save_path, "Prédit vs Réel")


def plot_residuals(y_true: np.ndarray, y_pred: np.ndarray, save_path: str) -> None:
    """
    Analyse des résidus en deux panneaux.

    PANNEAU 1 — Résidus vs Prédictions :
      Homoscédasticité : les résidus ne doivent PAS avoir de pattern.
      Si l'amplitude des résidus augmente avec les prédictions → hétéroscédasticité
      → considérer log(score) comme cible en V2.

    PANNEAU 2 — Distribution des résidus :
      Distribution gaussienne centrée sur 0 → bon modèle, bruit aléatoire.
      Distribution asymétrique → biais systématique (sur- ou sous-estimation).
    """
    residuals = y_pred - y_true
    mean_res  = residuals.mean()
    std_res   = residuals.std()

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    ax1 = axes[0]
    ax1.scatter(y_pred, residuals, alpha=0.75, s=60,
                color="#8e44ad", edgecolors="white", linewidths=0.5)
    ax1.axhline(0,   color="black",   lw=1.5, ls="--", alpha=0.7)
    ax1.axhline( 10, color="#e74c3c", lw=1.0, ls=":", alpha=0.6, label="±10 pts")
    ax1.axhline(-10, color="#e74c3c", lw=1.0, ls=":", alpha=0.6)
    ax1.text(0.05, 0.95, f"μ = {mean_res:.2f}\nσ = {std_res:.2f}",
             transform=ax1.transAxes, fontsize=9, va="top",
             bbox=dict(boxstyle="round", facecolor="lightyellow", alpha=0.8))
    ax1.set_xlabel("Valeurs prédites", fontsize=11)
    ax1.set_ylabel("Résidu (prédit − réel)", fontsize=11)
    ax1.set_title("Résidus vs Prédictions\n(homoscédasticité ?)", fontsize=11, fontweight="bold")
    ax1.legend(fontsize=9); ax1.grid(alpha=0.3)

    ax2 = axes[1]
    ax2.hist(residuals, bins=10, color="#3498db", edgecolor="white", alpha=0.8)
    ax2.axvline(0,        color="black",   lw=1.5, ls="--", alpha=0.8, label="Erreur=0")
    ax2.axvline(mean_res, color="#e74c3c", lw=1.5, ls="-",  alpha=0.8,
                label=f"μ = {mean_res:.1f}")
    ax2.set_xlabel("Résidu (pts)", fontsize=11)
    ax2.set_ylabel("Fréquence", fontsize=11)
    ax2.set_title("Distribution des résidus\n(gaussienne centrée = idéal)", fontsize=11, fontweight="bold")
    ax2.legend(fontsize=9); ax2.grid(alpha=0.3)

    plt.suptitle("Analyse des Résidus — RandomForest (Test Set)",
                 fontsize=13, fontweight="bold", y=1.01)
    plt.tight_layout()
    _save(fig, save_path, "Analyse résidus")


def plot_feature_importance(
    feature_importance_df: pd.DataFrame, save_path: str, top_n: int = 12
) -> None:
    """
    Graphique des importances MDI avec courbe cumulée.

    DEUX DIMENSIONS D'INFORMATION :
      1. Barres horizontales → importance individuelle de chaque feature
      2. Ligne cumulée (axe droit) → combien de features capturent 80% du signal

    RÈGLE DU 80/20 EN FEATURE IMPORTANCE :
      Souvent, les 3–5 premières features capturent 70–80% de l'importance.
      Les suivantes marginalement. Utile pour savoir quelles features
      conserver en cas de besoin de simplification du modèle.

    VALIDATION MÉTIER :
      Si panel_type_enc et traffic_flow_estim dominent → cohérent avec
      l'expertise terrain (type de panneau et trafic = facteurs principaux).
      Si une feature inattendue domine (ex: panel_id) → bug dans le pipeline.
    """
    top  = feature_importance_df.head(top_n).copy()
    top  = top.sort_values("importance", ascending=True)
    colors = plt.cm.RdYlGn(np.linspace(0.25, 0.9, len(top)))

    fig, ax1 = plt.subplots(figsize=(10, max(5, len(top) * 0.48)))

    bars = ax1.barh(top["feature"], top["importance_pct"],
                    color=colors, edgecolor="white", linewidth=0.8)
    for bar, val in zip(bars, top["importance_pct"]):
        ax1.text(bar.get_width() + 0.15, bar.get_y() + bar.get_height() / 2,
                 f"{val:.1f}%", va="center", ha="left", fontsize=9)

    # Courbe cumulée (ordre croissant → on revert)
    ax2 = ax1.twiny()
    cumul = top["cumulative_pct"].values[::-1]   # on retrace du bas au haut
    # Recalculer le cumul dans l'ordre décroissant pour le graphique
    all_cumul = feature_importance_df["cumulative_pct"].values
    top_names = top["feature"].values
    cumul_mapped = [
        feature_importance_df.loc[feature_importance_df["feature"] == n, "cumulative_pct"].values[0]
        for n in top_names
    ]
    ax2.plot(cumul_mapped, range(len(top)), "o--", color="#2c3e50",
             linewidth=1.5, markersize=5, alpha=0.7, label="Cumulatif")
    ax2.axvline(80, color="#e74c3c", lw=1, ls=":", alpha=0.6, label="Seuil 80%")
    ax2.set_xlabel("Importance cumulée (%)", fontsize=10, color="#2c3e50")
    ax2.legend(fontsize=8, loc="lower right")

    ax1.set_xlabel("Importance individuelle (%)", fontsize=11)
    ax1.set_title(
        f"Top {top_n} Features — MDI (Mean Decrease Impurity)\n"
        f"Réduction de variance MSE moyennée sur 100 arbres",
        fontsize=12, fontweight="bold"
    )
    ax1.grid(axis="x", alpha=0.3)
    ax1.set_xlim(0, top["importance_pct"].max() * 1.20)

    plt.tight_layout()
    _save(fig, save_path, "Feature importance")


def plot_score_distribution(
    y_train: np.ndarray, y_test: np.ndarray,
    y_pred: np.ndarray, save_path: str
) -> None:
    """Distribution des scores réels vs prédits."""
    fig, ax = plt.subplots(figsize=(9, 5))
    bins = np.linspace(0, 100, 20)
    ax.hist(y_train, bins=bins, alpha=0.5, color="#3498db",
            label=f"Train réel (n={len(y_train)})")
    ax.hist(y_test,  bins=bins, alpha=0.6, color="#e74c3c",
            label=f"Test réel (n={len(y_test)})")
    ax.hist(y_pred,  bins=bins, alpha=0.5, color="#2ecc71",
            histtype="step", linewidth=2.5,
            label=f"Test prédit (n={len(y_pred)})")
    ax.set_xlabel("Score de visibilité (0-100)", fontsize=11)
    ax.set_ylabel("Nombre de panneaux", fontsize=11)
    ax.set_title("Distribution des scores — Réel vs Prédit\n"
                 "(Distribution proche = bon modèle global)", fontsize=12, fontweight="bold")
    ax.legend(fontsize=10); ax.grid(alpha=0.3)
    plt.tight_layout()
    _save(fig, save_path, "Distribution scores")


# ---------------------------------------------------------------------------
# VISUALISATIONS — COMPARAISON ET DIAGNOSTIC
# ---------------------------------------------------------------------------

def plot_model_comparison(comparison: dict, save_path: str) -> None:
    """
    Compare RandomForest vs Ridge Baseline sur 3 métriques (test set).

    POURQUOI CE GRAPHIQUE EST ESSENTIEL EN PRÉSENTATION :
      Il répond à la question : "Vaut-il la peine d'utiliser un modèle complexe ?"
      Si RF et Ridge ont des métriques proches → la complexité ne se justifie pas.
      Si RF gagne clairement → le RF capture des non-linéarités que Ridge manque.

    LECTURE :
      Barres bleues = RandomForest, barres oranges = Ridge Baseline.
      Pour R²  : plus haut = mieux.
      Pour RMSE et MAE : plus bas = mieux → les barres sont inversées (affichage négatif).

    NOTE SUR L'INSTABILITÉ DES MÉTRIQUES AVEC 9 OBS TEST :
      Il est normal que Ridge batte RF sur ce test set spécifique.
      La conclusion doit s'appuyer sur la CV, pas uniquement sur 9 obs.
    """
    rf_test = comparison["random_forest"]["test"]
    b_test  = comparison["ridge_baseline"]["test"]

    # R² : plus haut = mieux
    # RMSE et MAE : plus bas = mieux (on les affiche en négatif pour avoir "plus haut = mieux")
    metrics_labels = ["R² (↑)", "RMSE négatif (↑)", "MAE négatif (↑)"]
    rf_vals = [rf_test["r2"], -rf_test["rmse"], -rf_test["mae"]]
    b_vals  = [b_test["r2"],  -b_test["rmse"],  -b_test["mae"]]

    x     = np.arange(len(metrics_labels))
    width = 0.32

    fig, ax = plt.subplots(figsize=(9, 5))
    bars_rf = ax.bar(x - width/2, rf_vals, width,
                     label="Random Forest", color="#2980b9", edgecolor="white")
    bars_b  = ax.bar(x + width/2, b_vals,  width,
                     label="Ridge Baseline", color="#e67e22", edgecolor="white")

    for bar in bars_rf:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + (0.01 if h >= 0 else -0.5),
                f"{h:.3f}", ha="center", va="bottom", fontsize=9, fontweight="bold")
    for bar in bars_b:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + (0.01 if h >= 0 else -0.5),
                f"{h:.3f}", ha="center", va="bottom", fontsize=9)

    ax.axhline(0, color="black", lw=0.8, alpha=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(metrics_labels, fontsize=11)
    ax.set_ylabel("Score (plus haut = mieux)", fontsize=11)
    ax.set_title(
        "RandomForest vs Ridge Baseline — Test Set\n"
        "RMSE/MAE en négatif : une barre plus haute = erreur plus faible",
        fontsize=12, fontweight="bold"
    )
    ax.legend(fontsize=10)
    ax.grid(axis="y", alpha=0.3)

    # Annotation du gagnant
    winner_text = (
        "RF gagne sur RMSE" if comparison["rf_vs_baseline"]["rf_wins_on_test"]
        else "Ridge gagne (variance test set — voir CV pour décision finale)"
    )
    ax.text(0.5, 0.02, winner_text, transform=ax.transAxes,
            ha="center", fontsize=9, color="#555",
            bbox=dict(facecolor="lightyellow", alpha=0.7, boxstyle="round"))

    plt.tight_layout()
    _save(fig, save_path, "Comparaison modèles")


def plot_learning_curve(lc_data: dict, save_path: str) -> None:
    """
    Courbe d'apprentissage — diagnostic visuel du biais-variance.

    COMMENT LIRE CETTE COURBE :

    CAS 1 — Overfitting classique (notre cas probable) :
      Train R² élevé et stable, CV R² faible.
      → Le gap diminue légèrement quand n augmente.
      Remède : plus de données, ou régularisation plus forte.

    CAS 2 — Underfitting (sous-ajustement) :
      Train R² ET CV R² faibles, les deux convergent bas.
      → Le modèle est trop simple, ou les features sont insuffisantes.
      Remède : ajouter des features, réduire la régularisation.

    CAS 3 — Bonne généralisation :
      Train R² et CV R² proches et élevés.
      Les deux convergent quand n augmente.

    BANDES D'INCERTITUDE :
      Les zones colorées autour de chaque courbe = ±1 std des 3-fold CV scores.
      Une bande large = forte variance, instabilité des résultats.
    """
    sizes      = np.array(lc_data["train_sizes"])
    tr_mean    = np.array(lc_data["train_scores_mean"])
    tr_std     = np.array(lc_data["train_scores_std"])
    val_mean   = np.array(lc_data["val_scores_mean"])
    val_std    = np.array(lc_data["val_scores_std"])

    fig, ax = plt.subplots(figsize=(9, 5))

    # Courbe train
    ax.plot(sizes, tr_mean, "o-", color="#2980b9", lw=2, ms=7, label="Score Train (R²)")
    ax.fill_between(sizes, tr_mean - tr_std, tr_mean + tr_std,
                    color="#2980b9", alpha=0.15)

    # Courbe validation CV
    ax.plot(sizes, val_mean, "s--", color="#e74c3c", lw=2, ms=7, label="Score CV (R²) — 3-fold")
    ax.fill_between(sizes, val_mean - val_std, val_mean + val_std,
                    color="#e74c3c", alpha=0.15)

    ax.axhline(0, color="gray", lw=1, ls=":", alpha=0.6, label="R²=0 (baseline naive)")

    # Annotation du gap max
    gap_max = (tr_mean - val_mean).max()
    ax.annotate(
        f"Gap max = {gap_max:.2f}\n(mesure de l'overfitting)",
        xy=(sizes[-1], (tr_mean[-1] + val_mean[-1]) / 2),
        xytext=(sizes[0] + 2, (tr_mean[-1] + val_mean[-1]) / 2 + 0.15),
        fontsize=9, color="#555",
        arrowprops=dict(arrowstyle="->", color="#555", lw=1),
    )

    ax.set_xlabel("Taille du dataset d'entraînement (observations)", fontsize=11)
    ax.set_ylabel("R²", fontsize=11)
    ax.set_title(
        "Courbe d'Apprentissage — RandomForest\n"
        "Diagnostic Biais-Variance : gap (bleu−rouge) = overfitting",
        fontsize=12, fontweight="bold"
    )
    ax.legend(fontsize=10)
    ax.grid(alpha=0.3)
    ax.set_ylim(min(-0.5, val_mean.min() - val_std.max() - 0.1), 1.05)

    plt.tight_layout()
    _save(fig, save_path, "Learning curve")


# ---------------------------------------------------------------------------
# UTILITAIRE
# ---------------------------------------------------------------------------

def _save(fig, path: str, label: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  [PLOT] {label} → {path}")


# ---------------------------------------------------------------------------
# RAPPORT JSON
# ---------------------------------------------------------------------------

def generate_report(
    train_metrics: dict,
    test_metrics: dict,
    cv_results: dict,
    diagnosis: str,
    feature_importance_df: pd.DataFrame,
    comparison: dict,
    config: dict,
    save_path: str,
) -> Dict[str, Any]:
    """
    Rapport JSON complet d'évaluation.

    En production ce rapport serait versionné (git tag) et stocké en base
    pour traçabilité : date, dataset hash, model hash, métriques, comparaison.
    """
    report = {
        "model_name":        config["model"]["algorithm"],
        "hyperparameters":   config["model"]["hyperparameters"],
        "train_metrics":     train_metrics,
        "test_metrics":      test_metrics,
        "cross_validation":  cv_results,
        "diagnosis":         diagnosis,
        "model_comparison":  {
            k: v for k, v in comparison.items()
            if k in ("random_forest", "ridge_baseline", "rf_vs_baseline")
        },
        "top_10_features": feature_importance_df.head(10)[
            ["feature", "importance_pct", "cumulative_pct"]
        ].to_dict("records"),
        "dataset_config": {
            "n_samples":   config["data_generation"]["n_samples"],
            "noise_level": config["data_generation"]["noise_level"],
            "test_size":   config["model"]["test_size"],
        },
    }

    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    with open(save_path, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"  [REPORT] Rapport sauvegardé → {save_path}")
    return report


# ---------------------------------------------------------------------------
# PIPELINE PRINCIPAL
# ---------------------------------------------------------------------------

def evaluation_pipeline(
    trained_model,
    baseline,
    split_data: dict,
    cv_results: dict,
    comparison: dict,
    lc_data: dict,
    config: dict,
) -> Dict[str, Any]:
    """
    Pipeline d'évaluation complet — 6 graphiques + rapport JSON.
    """
    print("\n[EVALUATION] Démarrage de l'évaluation complète...")
    fig_dir = Path(config["paths"]["figures_dir"])
    fig_dir.mkdir(parents=True, exist_ok=True)

    X_train = split_data["X_train"]
    X_test  = split_data["X_test"]
    y_train = split_data["y_train"].values
    y_test  = split_data["y_test"].values

    y_pred_train = trained_model.predict(X_train)
    y_pred_test  = trained_model.predict(X_test)

    # Métriques
    train_metrics = compute_metrics(y_train, y_pred_train, "Train")
    test_metrics  = compute_metrics(y_test,  y_pred_test,  "Test")

    # Diagnostic
    diagnosis = detect_train_test_gap(train_metrics, test_metrics)

    # Feature importance
    feat_imp = trained_model.get_feature_importance()

    # Graphiques
    plot_predictions_vs_actual(
        y_test, y_pred_test,
        "Score Prédit vs Réel — RandomForest (Test Set)",
        str(fig_dir / "01_pred_vs_actual.png")
    )
    plot_residuals(y_test, y_pred_test, str(fig_dir / "02_residuals.png"))
    plot_feature_importance(feat_imp, str(fig_dir / "03_feature_importance.png"))
    plot_score_distribution(y_train, y_test, y_pred_test,
                            str(fig_dir / "04_score_distribution.png"))
    plot_model_comparison(comparison, str(fig_dir / "05_model_comparison.png"))
    plot_learning_curve(lc_data, str(fig_dir / "06_learning_curve.png"))

    # Rapport
    report = generate_report(
        train_metrics, test_metrics, cv_results, diagnosis,
        feat_imp, comparison, config,
        config["paths"]["model_output"]
    )

    print(f"\n[EVALUATION] Terminé — 6 graphiques dans '{fig_dir}/'")
    return report


def run(config_path: str = "config/config.yaml"):
    pass


if __name__ == "__main__":
    run()
