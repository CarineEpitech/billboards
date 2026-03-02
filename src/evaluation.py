"""
==============================================================================
MODULE : evaluation.py
==============================================================================

RÔLE : Évaluation complète du modèle — métriques, visualisations, analyse
       des erreurs et rapport final.

PHILOSOPHIE D'ÉVALUATION :
  Une seule métrique ne suffit JAMAIS à évaluer un modèle.
  On combine :
  1. MÉTRIQUES STATISTIQUES : R², RMSE, MAE
  2. ANALYSE DES RÉSIDUS    : distribution des erreurs, biais
  3. IMPORTANCE DES FEATURES : ce que le modèle a réellement appris
  4. ANALYSE DES CAS EXTRÊMES : où le modèle se trompe le plus

MÉTRIQUES UTILISÉES :
---------------------
  R² (coefficient de détermination) :
    - Proportion de variance expliquée par le modèle
    - 1.0 = parfait, 0.0 = aussi bien que prédire la moyenne, < 0 = mauvais
    - Sur données bruitées avec 40 obs : R² ∈ [0.4, 0.7] est raisonnable

  RMSE (Root Mean Squared Error) :
    - Erreur quadratique moyenne → pénalise les grosses erreurs
    - Même unité que la cible (points de visibilité)
    - Exemple : RMSE=8 pts sur 100 → erreur typique de ±8 points

  MAE (Mean Absolute Error) :
    - Erreur absolue moyenne → plus robuste aux outliers que RMSE
    - Interprétation directe : "en moyenne, on se trompe de X points"

  RMSE vs MAE :
    Si RMSE >> MAE → il y a quelques grosses erreurs (outliers de prédiction)
    Si RMSE ≈ MAE → les erreurs sont distribuées uniformément

==============================================================================
"""

import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Backend non-interactif pour serveur sans display
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import yaml
from pathlib import Path
from typing import Dict, Any

from sklearn.metrics import (
    r2_score,
    mean_squared_error,
    mean_absolute_error,
)


# ---------------------------------------------------------------------------
# MÉTRIQUES CORE
# ---------------------------------------------------------------------------

def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, dataset_name: str = "Test") -> Dict[str, float]:
    """
    Calcule les métriques d'évaluation principales.

    PARAMÈTRES :
      y_true       : valeurs réelles
      y_pred       : valeurs prédites
      dataset_name : "Train" ou "Test" (pour le logging)

    RETOUR :
      Dictionnaire avec toutes les métriques calculées.
    """
    r2   = r2_score(y_true, y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae  = mean_absolute_error(y_true, y_pred)

    # MAPE (Mean Absolute Percentage Error) — utile si la cible est > 0
    # On évite la division par zéro avec un clip
    mape = float(np.mean(np.abs((y_true - y_pred) / np.clip(y_true, 1, None))) * 100)

    # Médiane des erreurs absolues (robuste aux outliers)
    medae = float(np.median(np.abs(y_true - y_pred)))

    # Pourcentage de prédictions dans ±10 pts de la vraie valeur
    within_10 = float(np.mean(np.abs(y_true - y_pred) <= 10) * 100)

    metrics = {
        f"{dataset_name}_R2":        round(r2,        4),
        f"{dataset_name}_RMSE":      round(rmse,      3),
        f"{dataset_name}_MAE":       round(mae,       3),
        f"{dataset_name}_MAPE_pct":  round(mape,      2),
        f"{dataset_name}_MedAE":     round(medae,     3),
        f"{dataset_name}_Within10pts_pct": round(within_10, 1),
    }

    print(f"\n  --- Métriques {dataset_name} ---")
    print(f"  R²              = {r2:.4f}   (objectif > 0.5 pour prototype)")
    print(f"  RMSE            = {rmse:.2f} pts (erreur typique ±{rmse:.1f} pts sur 100)")
    print(f"  MAE             = {mae:.2f} pts (erreur médiane ±{mae:.1f} pts)")
    print(f"  MAPE            = {mape:.1f}%")
    print(f"  Prédictions ±10 = {within_10:.1f}% des cas")

    # Diagnostic rapide
    if r2 < 0.3:
        print(f"  [DIAG] ⚠ R² faible — le modèle explique peu. Vérifier features et données.")
    elif r2 < 0.5:
        print(f"  [DIAG] R² modéré — acceptable pour un prototype avec données bruitées.")
    else:
        print(f"  [DIAG] R² correct — bon signal appris.")

    return metrics


def detect_train_test_gap(train_metrics: dict, test_metrics: dict) -> str:
    """
    Détecte un éventuel sur-ajustement (overfitting).

    OVERFITTING : Le modèle mémorise le train set mais ne généralise pas.
    Signe : R²_train >> R²_test (écart > 0.15 est préoccupant)

    UNDERFITTING : Le modèle est trop simple pour capturer le signal.
    Signe : R²_train et R²_test tous deux faibles (< 0.3)
    """
    r2_train = train_metrics.get("Train_R2", 0)
    r2_test  = test_metrics.get("Test_R2", 0)
    gap      = r2_train - r2_test

    if gap > 0.20:
        diagnosis = f"Sur-ajustement détecté (gap={gap:.3f}). Augmenter min_samples_leaf ou réduire max_depth."
    elif r2_train < 0.30 and r2_test < 0.30:
        diagnosis = f"Sous-ajustement (R² train={r2_train:.3f}). Ajouter des features ou réduire la régularisation."
    elif gap < 0.10:
        diagnosis = f"Bon équilibre biais-variance (gap={gap:.3f}). Modèle stable."
    else:
        diagnosis = f"Légère variance (gap={gap:.3f}). Acceptable pour ce dataset."

    print(f"\n  [OVERFITTING] {diagnosis}")
    return diagnosis


# ---------------------------------------------------------------------------
# VISUALISATIONS
# ---------------------------------------------------------------------------

def plot_predictions_vs_actual(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    title: str,
    save_path: str
) -> None:
    """
    Graphique Prédit vs Réel — le diagnostic visuel le plus important.

    INTERPRÉTATION :
      - Points proches de la diagonale y=x → bonnes prédictions
      - Points systématiquement au-dessus → biais de sur-estimation
      - Points dispersés uniformément → bruit, pas de biais systématique
      - Pattern non-linéaire → le modèle manque une non-linéarité
    """
    fig, ax = plt.subplots(figsize=(7, 6))

    residuals = y_pred - y_true
    colors = np.where(np.abs(residuals) > 15, "#e74c3c", "#2980b9")

    ax.scatter(y_true, y_pred, c=colors, alpha=0.75, s=60, edgecolors="white", linewidths=0.5)

    # Ligne de parfaite prédiction
    lim_min = max(0,   min(y_true.min(), y_pred.min()) - 5)
    lim_max = min(100, max(y_true.max(), y_pred.max()) + 5)
    ax.plot([lim_min, lim_max], [lim_min, lim_max], "k--", linewidth=1.5,
            label="Prédiction parfaite (y=x)", alpha=0.7)

    # Bandes de confiance ±10 pts
    ax.fill_between([lim_min, lim_max],
                    [lim_min - 10, lim_max - 10],
                    [lim_min + 10, lim_max + 10],
                    alpha=0.08, color="#2ecc71", label="Zone ±10 pts")

    legend_patches = [
        mpatches.Patch(color="#2980b9", label="Erreur ≤ 15 pts"),
        mpatches.Patch(color="#e74c3c", label="Erreur > 15 pts"),
    ]
    ax.legend(handles=legend_patches + ax.get_lines(), fontsize=9, loc="upper left")

    ax.set_xlabel("Score réel (ground truth)", fontsize=11)
    ax.set_ylabel("Score prédit", fontsize=11)
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.set_xlim(lim_min, lim_max)
    ax.set_ylim(lim_min, lim_max)
    ax.grid(alpha=0.3)

    r2   = r2_score(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    ax.text(0.05, 0.92, f"R² = {r2:.3f}  |  RMSE = {rmse:.1f} pts",
            transform=ax.transAxes, fontsize=10,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.8))

    plt.tight_layout()
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [PLOT] Prédit vs Réel → {save_path}")


def plot_residuals(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    save_path: str
) -> None:
    """
    Analyse des résidus — détecte les patterns d'erreur systématiques.

    UN BON MODÈLE a des résidus :
      - Centrés sur 0 (pas de biais)
      - Distribution proche d'une gaussienne
      - Sans pattern en fonction des valeurs prédites (homoscédasticité)

    SI les résidus forment un entonnoir (erreurs plus grandes pour les
    scores élevés) → hétéroscédasticité → considérer log(score) comme cible
    """
    residuals = y_pred - y_true

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Sous-plot 1 : Résidus vs Valeurs Prédites
    ax1 = axes[0]
    ax1.scatter(y_pred, residuals, alpha=0.7, s=55, color="#8e44ad", edgecolors="white", linewidths=0.5)
    ax1.axhline(0, color="black", linewidth=1.5, linestyle="--", alpha=0.7)
    ax1.axhline( 10, color="#e74c3c", linewidth=1, linestyle=":", alpha=0.5, label="±10 pts")
    ax1.axhline(-10, color="#e74c3c", linewidth=1, linestyle=":", alpha=0.5)
    ax1.set_xlabel("Valeurs prédites", fontsize=11)
    ax1.set_ylabel("Résidus (prédit − réel)", fontsize=11)
    ax1.set_title("Résidus vs Prédictions", fontsize=12, fontweight="bold")
    ax1.legend(fontsize=9)
    ax1.grid(alpha=0.3)

    mean_res = residuals.mean()
    std_res  = residuals.std()
    ax1.text(0.05, 0.95, f"μ={mean_res:.2f}  σ={std_res:.2f}",
             transform=ax1.transAxes, fontsize=9,
             bbox=dict(boxstyle="round", facecolor="lightyellow", alpha=0.8),
             verticalalignment="top")

    # Sous-plot 2 : Distribution des résidus
    ax2 = axes[1]
    ax2.hist(residuals, bins=12, color="#3498db", edgecolor="white", alpha=0.8)
    ax2.axvline(0, color="black", linewidth=1.5, linestyle="--", alpha=0.8, label="Erreur=0")
    ax2.axvline(mean_res, color="#e74c3c", linewidth=1.5, linestyle="-",
                alpha=0.8, label=f"Moyenne={mean_res:.1f}")
    ax2.set_xlabel("Résidu (pts)", fontsize=11)
    ax2.set_ylabel("Fréquence", fontsize=11)
    ax2.set_title("Distribution des résidus", fontsize=12, fontweight="bold")
    ax2.legend(fontsize=9)
    ax2.grid(alpha=0.3)

    plt.suptitle("Analyse des résidus du modèle RandomForest", fontsize=13, y=1.01, fontweight="bold")
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [PLOT] Analyse résidus → {save_path}")


def plot_feature_importance(
    feature_importance_df: pd.DataFrame,
    save_path: str,
    top_n: int = 12
) -> None:
    """
    Graphique des features les plus importantes.

    UTILITÉ BUSINESS :
      Ce graphique est souvent la slide la plus importante d'une présentation.
      Il montre QUE le modèle a appris des choses sensées (trafic = important,
      type de panneau = important) et pas des artefacts.

    RED FLAG : Si 'panel_id' ou 'latitude' seuls dominent → problème.
    """
    top = feature_importance_df.head(top_n).copy()
    top = top.sort_values("importance", ascending=True)  # Pour affichage horizontal

    # Palette de couleurs : gradient selon importance
    colors = plt.cm.RdYlGn(np.linspace(0.3, 0.9, len(top)))

    fig, ax = plt.subplots(figsize=(9, max(5, len(top) * 0.45)))

    bars = ax.barh(top["feature"], top["importance_pct"],
                   color=colors, edgecolor="white", linewidth=0.8)

    # Labels à l'intérieur des barres
    for bar, val in zip(bars, top["importance_pct"]):
        ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}%", va="center", ha="left", fontsize=9)

    ax.set_xlabel("Importance relative (%)", fontsize=11)
    ax.set_title(f"Top {top_n} Features — Importance RandomForest\n"
                 f"(Réduction moyenne de variance par feature)",
                 fontsize=12, fontweight="bold")
    ax.grid(axis="x", alpha=0.3)
    ax.set_xlim(0, top["importance_pct"].max() * 1.15)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [PLOT] Feature importance → {save_path}")


def plot_score_distribution(
    y_train: np.ndarray,
    y_test: np.ndarray,
    y_pred: np.ndarray,
    save_path: str
) -> None:
    """
    Distribution des scores réels vs prédits — vue globale de la qualité.

    INTERPRÉTATION :
      Si la distribution prédite est proche de la distribution réelle,
      le modèle a bien appris la structure globale des scores,
      même s'il se trompe individuellement.
    """
    fig, ax = plt.subplots(figsize=(9, 5))

    bins = np.linspace(0, 100, 20)
    ax.hist(y_train, bins=bins, alpha=0.5, color="#3498db", label=f"Train réel (n={len(y_train)})")
    ax.hist(y_test,  bins=bins, alpha=0.6, color="#e74c3c", label=f"Test réel (n={len(y_test)})")
    ax.hist(y_pred,  bins=bins, alpha=0.5, color="#2ecc71", label=f"Test prédit (n={len(y_pred)})",
            linestyle="--", histtype="step", linewidth=2.5)

    ax.set_xlabel("Score de visibilité (0-100)", fontsize=11)
    ax.set_ylabel("Nombre de panneaux", fontsize=11)
    ax.set_title("Distribution des scores — Réel vs Prédit", fontsize=12, fontweight="bold")
    ax.legend(fontsize=10)
    ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [PLOT] Distribution scores → {save_path}")


# ---------------------------------------------------------------------------
# RAPPORT FINAL
# ---------------------------------------------------------------------------

def generate_report(
    train_metrics: dict,
    test_metrics: dict,
    cv_results: dict,
    diagnosis: str,
    feature_importance_df: pd.DataFrame,
    config: dict,
    save_path: str
) -> Dict[str, Any]:
    """
    Génère et sauvegarde le rapport complet d'évaluation en JSON.

    CE RAPPORT EST LA LIVRABLE TECHNIQUE pour le comité.
    En production, il serait enrichi avec :
    - Timestamp d'entraînement
    - Version du dataset
    - Hash du modèle (reproductibilité)
    - Comparaison avec la version précédente
    """
    report = {
        "model_name":        config["model"]["algorithm"],
        "hyperparameters":   config["model"]["hyperparameters"],
        "train_metrics":     train_metrics,
        "test_metrics":      test_metrics,
        "cross_validation":  cv_results,
        "diagnosis":         diagnosis,
        "top_10_features":   feature_importance_df.head(10)[["feature", "importance_pct"]].to_dict("records"),
        "dataset_config": {
            "n_samples":    config["data_generation"]["n_samples"],
            "noise_level":  config["data_generation"]["noise_level"],
            "test_size":    config["model"]["test_size"],
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
    split_data: dict,
    cv_results: dict,
    config: dict
) -> Dict[str, Any]:
    """
    Pipeline d'évaluation complet.
    """
    print("\n[EVALUATION] Démarrage de l'évaluation complète...")
    fig_dir = Path(config["paths"]["figures_dir"])
    fig_dir.mkdir(parents=True, exist_ok=True)

    X_train = split_data["X_train"]
    X_test  = split_data["X_test"]
    y_train = split_data["y_train"].values
    y_test  = split_data["y_test"].values

    # Prédictions
    y_pred_train = trained_model.predict(X_train)
    y_pred_test  = trained_model.predict(X_test)

    # Métriques
    train_metrics = compute_metrics(y_train, y_pred_train, "Train")
    test_metrics  = compute_metrics(y_test,  y_pred_test,  "Test")

    # Diagnostic overfitting
    diagnosis = detect_train_test_gap(train_metrics, test_metrics)

    # Importance des features
    feat_imp = trained_model.get_feature_importance()

    # Visualisations
    plot_predictions_vs_actual(
        y_test, y_pred_test,
        "Score Prédit vs Réel — RandomForest (Test Set)",
        str(fig_dir / "01_pred_vs_actual.png")
    )
    plot_residuals(
        y_test, y_pred_test,
        str(fig_dir / "02_residuals.png")
    )
    plot_feature_importance(
        feat_imp,
        str(fig_dir / "03_feature_importance.png")
    )
    plot_score_distribution(
        y_train, y_test, y_pred_test,
        str(fig_dir / "04_score_distribution.png")
    )

    # Rapport JSON
    report = generate_report(
        train_metrics, test_metrics, cv_results, diagnosis,
        feat_imp, config,
        config["paths"]["model_output"]
    )

    print(f"\n[EVALUATION] Terminé. Graphiques sauvegardés dans '{fig_dir}/'")
    return report


def run(config_path: str = "config/config.yaml"):
    """Point d'entrée standalone pour test."""
    pass


if __name__ == "__main__":
    run()
