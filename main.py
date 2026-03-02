"""
==============================================================================
MAIN.PY — Orchestrateur du Pipeline Billboard Geolocation
==============================================================================

RÔLE : Point d'entrée unique du projet. Exécute l'ensemble du pipeline
       dans l'ordre correct, avec logging et gestion d'erreurs.

ARCHITECTURE DU PIPELINE :
  [data_generation] → [cleaning] → [feature_engineering] → [model] → [evaluation]

      Données brutes      Données      Features ML           Modèle       Métriques
      (45 panneaux)       propres      (X, y)                entraîné     & graphiques
                          (sans NaN)

UTILISATION :
  python main.py                     # Pipeline complet
  python main.py --step generate     # Uniquement la génération
  python main.py --step clean        # Uniquement le cleaning
  python main.py --step train        # Génération + clean + train

DESIGN PATTERN : Pipeline linéaire (pas de parallélisation pour ce prototype)
  Chaque étape prend en entrée l'output de l'étape précédente.
  Avantage : simple à déboguer, chaque étape est isolée et testable.

==============================================================================
"""

import sys
import time
import yaml
import argparse
from pathlib import Path

# Import des modules du projet
from src import data_generation, cleaning, feature_engineering, model, evaluation


def load_config(config_path: str = "config/config.yaml") -> dict:
    """Charge la configuration globale."""
    with open(config_path) as f:
        config = yaml.safe_load(f)
    return config


def print_banner():
    banner = """
╔══════════════════════════════════════════════════════════════════╗
║    BILLBOARD GEOLOCATION — Cotonou, Bénin                        ║
║    Pipeline ML : Génération → Cleaning → FE → Modèle → Éval.    ║
║    Version 1.0.0  |  Prototype Technique                         ║
╚══════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def run_full_pipeline(config: dict) -> None:
    """
    Exécute le pipeline complet de bout en bout.

    ÉTAPE 1 : DATA GENERATION
      Génère un dataset de 45 panneaux avec bruit réaliste.
      Output : data/raw/billboards_raw.csv

    ÉTAPE 2 : CLEANING
      Valide, dédoublonne, impute les données brutes.
      Output : data/processed/billboards_clean.csv

    ÉTAPE 3 : FEATURE ENGINEERING
      Encode, dérive, sélectionne les features ML.
      Output : X (DataFrame features), y (Série cible)

    ÉTAPE 4 : MODEL TRAINING
      Entraîne un RandomForestRegressor avec cross-validation.
      Output : Modèle entraîné + métriques CV

    ÉTAPE 5 : EVALUATION
      Calcule métriques, génère graphiques, sauvegarde rapport JSON.
      Output : reports/figures/*.png, reports/model_results.json
    """
    t0 = time.time()

    # ─────────────────────────────────────────────────────────────
    # ÉTAPE 1 : GÉNÉRATION DES DONNÉES
    # ─────────────────────────────────────────────────────────────
    print("\n" + "═" * 60)
    print("  ÉTAPE 1/5 : GÉNÉRATION DES DONNÉES")
    print("═" * 60)
    df_raw = data_generation.generate_billboard_dataset(config)

    raw_path = Path(config["paths"]["raw_data"])
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    df_raw.to_csv(raw_path, index=False)
    print(f"  → {len(df_raw)} panneaux générés → {raw_path}")

    # ─────────────────────────────────────────────────────────────
    # ÉTAPE 2 : CLEANING
    # ─────────────────────────────────────────────────────────────
    print("\n" + "═" * 60)
    print("  ÉTAPE 2/5 : NETTOYAGE DES DONNÉES")
    print("═" * 60)
    df_clean, quality_report = cleaning.clean_pipeline(df_raw, config)

    proc_path = Path(config["paths"]["processed_data"])
    proc_path.parent.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(proc_path, index=False)
    print(f"  → {len(df_clean)} panneaux propres → {proc_path}")

    # ─────────────────────────────────────────────────────────────
    # ÉTAPE 3 : FEATURE ENGINEERING
    # ─────────────────────────────────────────────────────────────
    print("\n" + "═" * 60)
    print("  ÉTAPE 3/5 : FEATURE ENGINEERING")
    print("═" * 60)
    X, y, feat_cols, encodings = feature_engineering.engineering_pipeline(df_clean, config)
    print(f"  → {len(feat_cols)} features | {len(X)} observations")
    print(f"  → Features : {feat_cols}")

    # ─────────────────────────────────────────────────────────────
    # ÉTAPE 4 : ENTRAÎNEMENT DU MODÈLE
    # ─────────────────────────────────────────────────────────────
    print("\n" + "═" * 60)
    print("  ÉTAPE 4/5 : ENTRAÎNEMENT DU MODÈLE")
    print("═" * 60)
    trained_model, baseline, split_data, cv_results, comparison, lc_data = \
        model.training_pipeline(X, y, config)

    # Sauvegarder le modèle
    model_pkl_path = "reports/billboard_model.pkl"
    trained_model.save(model_pkl_path)

    # ─────────────────────────────────────────────────────────────
    # ÉTAPE 5 : ÉVALUATION
    # ─────────────────────────────────────────────────────────────
    print("\n" + "═" * 60)
    print("  ÉTAPE 5/5 : ÉVALUATION DU MODÈLE")
    print("═" * 60)
    eval_report = evaluation.evaluation_pipeline(
        trained_model, baseline, split_data,
        cv_results, comparison, lc_data, config
    )

    # ─────────────────────────────────────────────────────────────
    # RÉSUMÉ FINAL
    # ─────────────────────────────────────────────────────────────
    elapsed = time.time() - t0
    print("\n" + "═" * 60)
    print("  RÉSUMÉ DU PIPELINE")
    print("═" * 60)
    print(f"  Temps total          : {elapsed:.1f}s")
    print(f"  Panneaux générés     : {len(df_raw)}")
    print(f"  Panneaux après clean : {len(df_clean)}")
    print(f"  Features ML          : {len(feat_cols)}")
    print(f"  RF CV R²             : {cv_results['cv_r2_mean']:.3f} ± {cv_results['cv_r2_std']:.3f}")
    print(f"  RF Test R²           : {eval_report['test_metrics']['Test_R2']:.3f}")
    print(f"  RF Test RMSE         : {eval_report['test_metrics']['Test_RMSE']:.2f} pts")
    print(f"  RF Test MAE          : {eval_report['test_metrics']['Test_MAE']:.2f} pts")
    b_test = comparison["ridge_baseline"]["test"]
    print(f"  Ridge Test R²        : {b_test['r2']:.3f}  (baseline)")
    print(f"  Ridge Test RMSE      : {b_test['rmse']:.2f} pts (baseline)")
    print(f"  RF vs Ridge (RMSE)   : {comparison['rf_vs_baseline']['rmse_gain_pct']:+.1f}%")
    print(f"\n  Graphiques (6)       : reports/figures/")
    print(f"  Rapport JSON         : {config['paths']['model_output']}")
    print(f"  Modèle sauvegardé    : {model_pkl_path}")
    print("\n  Pipeline terminé avec succès.")
    print("═" * 60)

    return eval_report


def demo_prediction(config: dict, model_path: str = "reports/billboard_model.pkl") -> None:
    """
    Démonstration : prédire le score d'un nouveau panneau hypothétique.

    UTILITÉ BUSINESS :
      Cette fonction montre comment utiliser le modèle en production.
      Un opérateur terrain saisit les caractéristiques d'un emplacement
      potentiel et obtient un score de visibilité estimé.
    """
    print("\n" + "═" * 60)
    print("  DÉMONSTRATION : Prédiction sur un nouveau panneau")
    print("═" * 60)

    # Charger le modèle entraîné
    loaded_model = model.BillboardVisibilityModel.load(model_path)

    # Nouveau panneau hypothétique : digital, boulevard à Dantokpa
    import pandas as pd
    import numpy as np

    new_billboard = pd.DataFrame([{
        # Features originales
        "latitude":                   6.357,
        "longitude":                  2.420,
        "traffic_flow_estim":         7500,
        "height_m":                   7.0,
        "size_m2":                    18.0,
        "distance_to_center_km":      1.8,
        "distance_to_main_road_m":    5.0,
        "hours_of_daylight_exposure": 10.0,
        "pedestrian_density_score":   88.0,
        "competition_radius_500m":    2,
        # Features encodées (Dantokpa=6, digital=0, boulevard=0 — voir mappings)
        "panel_type_enc":             0,
        "quartier_enc":               6,
        "road_type_enc":              0,
        # Features dérivées
        "ratio_surface_hauteur":      18.0 / 7.0,
        "log_traffic":                np.log1p(7500),
        "score_accessibilite":        5.0/200 + 1.8/5,
        "indice_saturation":          2 * (88.0 / 100),
        "is_digital":                 1,
        "age_panneau":                1,
        "effective_exposure_hours":   24,
        # Features géospatiales
        "distance_to_beach_km":       1.9,
        "distance_to_port_km":        0.4,
        "geo_quadrant":               0,
    }])

    # Sélectionner uniquement les colonnes que le modèle connaît
    feat_cols = loaded_model.feature_names
    new_billboard = new_billboard[feat_cols]

    predicted_score = loaded_model.predict(new_billboard)[0]

    print(f"\n  Caractéristiques du panneau hypothétique :")
    print(f"    Emplacement   : Dantokpa, boulevard principal")
    print(f"    Type          : Digital")
    print(f"    Taille        : 18 m²  |  Hauteur : 7m")
    print(f"    Trafic estimé : 7 500 véhicules/jour")
    print(f"    Concurrents   : 2 panneaux dans 500m")
    print(f"\n  Score de visibilité prédit : {predicted_score:.1f} / 100")

    if predicted_score >= 70:
        interpretation = "Excellent emplacement — fort potentiel publicitaire"
    elif predicted_score >= 50:
        interpretation = "Bon emplacement — potentiel modéré"
    elif predicted_score >= 30:
        interpretation = "Emplacement moyen — à développer"
    else:
        interpretation = "Emplacement faible — peu attractif"

    print(f"  Interprétation : {interpretation}")


def main():
    print_banner()

    parser = argparse.ArgumentParser(description="Billboard Geolocation Pipeline")
    parser.add_argument("--config", default="config/config.yaml", help="Chemin vers le fichier de configuration")
    parser.add_argument("--step", choices=["all", "generate", "clean", "train", "evaluate", "demo"],
                        default="all", help="Étape à exécuter")
    parser.add_argument("--no-demo", action="store_true", help="Désactiver la démonstration finale")
    args = parser.parse_args()

    config = load_config(args.config)

    if args.step == "all":
        eval_report = run_full_pipeline(config)
        if not args.no_demo:
            try:
                demo_prediction(config)
            except Exception as e:
                print(f"\n  [INFO] Démonstration ignorée : {e}")
    elif args.step == "generate":
        df = data_generation.generate_billboard_dataset(config)
        df.to_csv(config["paths"]["raw_data"], index=False)
        print(f"Données générées : {len(df)} lignes → {config['paths']['raw_data']}")
    elif args.step == "demo":
        demo_prediction(config)
    else:
        print(f"Étape '{args.step}' : exécutez le pipeline complet d'abord (--step all)")


if __name__ == "__main__":
    main()
