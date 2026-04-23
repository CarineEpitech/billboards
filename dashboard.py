"""
Dashboard Streamlit — Billboard Geolocation Platform, Cotonou
Lancement : streamlit run dashboard.py
"""

import json
import pickle
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import yaml

# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Billboard Geolocation — Cotonou",
    page_icon="🪧",
    layout="wide",
    initial_sidebar_state="expanded",
)

CONFIG_PATH  = Path("config/config.yaml")
REPORT_PATH  = Path("reports/model_results.json")
FIGURES_DIR  = Path("reports/figures")
RAW_PATH     = Path("data/raw/billboards_raw.csv")
CLEAN_PATH   = Path("data/processed/billboards_clean.csv")
MODEL_PATH   = Path("reports/billboard_model.pkl")

FIGURE_INFO = {
    "01_pred_vs_actual.png":    ("Prédit vs Réel",         "Score prédit vs score réel sur le test set. Points sur la diagonale = prédiction parfaite."),
    "02_residuals.png":         ("Analyse des résidus",    "Distribution des erreurs. Idéalement centrée sur 0, gaussienne."),
    "03_feature_importance.png":("Feature Importance",     "Variables les plus déterminantes pour le modèle (MDI)."),
    "04_score_distribution.png":("Distribution des scores","Comparaison des distributions train / test / prédictions."),
    "05_model_comparison.png":  ("RF vs Ridge",            "Comparaison RandomForest vs baseline Ridge sur R², RMSE, MAE."),
    "06_learning_curve.png":    ("Courbe d'apprentissage", "Gap train-CV : mesure de l'overfitting selon la taille du dataset."),
}


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────
@st.cache_data
def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)

@st.cache_data
def load_report():
    if not REPORT_PATH.exists():
        return None
    with open(REPORT_PATH) as f:
        return json.load(f)

@st.cache_data
def load_data(path: Path):
    if not path.exists():
        return None
    return pd.read_csv(path)

def fmt(val, decimals=3):
    if val is None:
        return "—"
    return f"{val:.{decimals}f}"

def delta_color(val, good_direction="up"):
    """Retourne 'normal', 'inverse' pour st.metric."""
    return "normal" if good_direction == "up" else "inverse"


# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🪧 Billboard Cotonou")
    st.caption("Prototype V1 — Pipeline ML complet")
    st.divider()

    page = st.radio(
        "Navigation",
        ["🏠 Accueil & Métriques", "📊 Graphiques", "🗂 Données", "🔮 Prédiction", "⚙️ Pipeline"],
        label_visibility="collapsed",
    )
    st.divider()

    cfg = load_config()
    if cfg:
        st.caption(f"**Projet** : {cfg['project']['name']}")
        st.caption(f"**Panneaux** : {cfg['data_generation']['n_samples']}")
        st.caption(f"**Bruit** : {int(cfg['data_generation']['noise_level']*100)}%")
        st.caption(f"**Modèle** : {cfg['model']['algorithm']}")
        st.caption(f"**CV folds** : {cfg['model']['cv_folds']}")

    st.divider()
    if st.button("🔄 Rafraîchir les données", use_container_width=True):
        st.cache_data.clear()
        st.rerun()


# ─────────────────────────────────────────────────────────────
# PAGE : ACCUEIL & MÉTRIQUES
# ─────────────────────────────────────────────────────────────
if page == "🏠 Accueil & Métriques":
    st.title("Billboard Geolocation Platform")
    st.markdown("**Cotonou, Bénin** — Prédiction du score de visibilité des panneaux publicitaires")
    st.divider()

    report = load_report()
    if report is None:
        st.warning("Aucun rapport trouvé. Lance le pipeline d'abord (page **⚙️ Pipeline**).")
    else:
        # ── KPIs principaux ────────────────────────────────────
        st.subheader("Métriques du modèle")
        c1, c2, c3, c4 = st.columns(4)

        cv_r2   = report["cross_validation"].get("cv_r2_mean")
        cv_std  = report["cross_validation"].get("cv_r2_std")
        test_r2 = report["test_metrics"].get("Test_R2")
        rmse    = report["test_metrics"].get("Test_RMSE")
        mae     = report["test_metrics"].get("Test_MAE")
        w10     = report["test_metrics"].get("Test_Within10pts_pct")

        c1.metric("CV R² (mean ± std)", f"{fmt(cv_r2)} ± {fmt(cv_std, 2)}")
        c2.metric("Test R²",  fmt(test_r2))
        c3.metric("Test RMSE", f"{fmt(rmse, 1)} pts")
        c4.metric("Test MAE",  f"{fmt(mae, 1)} pts")

        # ── Row 2 ───────────────────────────────────────────────
        c5, c6, c7, c8 = st.columns(4)
        mape  = report["test_metrics"].get("Test_MAPE_pct")
        medae = report["test_metrics"].get("Test_MedAE")
        rf_rmse = report["model_comparison"]["random_forest"]["test"]["rmse"]
        ri_rmse = report["model_comparison"]["ridge_baseline"]["test"]["rmse"]
        rmse_gain = report["model_comparison"]["rf_vs_baseline"]["rmse_gain_pct"]

        c5.metric("Prédictions ±10 pts", f"{fmt(w10, 1)}%")
        c6.metric("MAPE",  f"{fmt(mape, 1)}%")
        c7.metric("MedAE", f"{fmt(medae, 1)} pts")
        c8.metric("RF vs Ridge (RMSE)", f"{rmse_gain:+.1f}%",
                  delta=f"{rmse_gain:+.1f}%",
                  delta_color="inverse")

        st.divider()

        # ── Hyperparamètres ─────────────────────────────────────
        col_hp, col_cv = st.columns(2)
        with col_hp:
            st.subheader("Hyperparamètres RF")
            hp = report.get("hyperparameters", {})
            st.dataframe(
                pd.DataFrame({"Paramètre": list(hp.keys()), "Valeur": list(hp.values())}),
                hide_index=True, use_container_width=True,
            )

        with col_cv:
            st.subheader("Cross-validation (5-fold)")
            cv = report.get("cross_validation", {})
            cv_rows = [
                ("CV R² mean",  fmt(cv.get("cv_r2_mean"))),
                ("CV R² std",   fmt(cv.get("cv_r2_std"))),
                ("CV RMSE mean",f"{fmt(cv.get('cv_rmse_mean'), 2)} pts"),
                ("CV RMSE std", f"{fmt(cv.get('cv_rmse_std'), 2)} pts"),
            ]
            st.dataframe(
                pd.DataFrame(cv_rows, columns=["Métrique", "Valeur"]),
                hide_index=True, use_container_width=True,
            )

        st.divider()

        # ── Diagnostic ──────────────────────────────────────────
        st.subheader("Diagnostic biais-variance")
        diag = report.get("diagnosis", "—")
        if "Overfitting significatif" in diag:
            st.error(f"⚠️ {diag}")
        elif "Overfitting modéré" in diag:
            st.warning(f"⚡ {diag}")
        else:
            st.success(f"✅ {diag}")

        st.divider()

        # ── Top features ─────────────────────────────────────────
        st.subheader("Top 10 Features (MDI importance)")
        top_feats = report.get("top_10_features", [])
        if top_feats:
            df_feats = pd.DataFrame(top_feats)
            df_feats.columns = ["Feature", "Importance (%)", "Cumulatif (%)"]
            st.dataframe(df_feats, hide_index=True, use_container_width=True)


# ─────────────────────────────────────────────────────────────
# PAGE : GRAPHIQUES
# ─────────────────────────────────────────────────────────────
elif page == "📊 Graphiques":
    st.title("Graphiques du modèle")

    if not FIGURES_DIR.exists() or not any(FIGURES_DIR.iterdir()):
        st.warning("Aucun graphique trouvé. Lance le pipeline d'abord (page **⚙️ Pipeline**).")
    else:
        # Affichage 2 colonnes
        figures = list(FIGURE_INFO.items())
        for i in range(0, len(figures), 2):
            cols = st.columns(2)
            for j, col in enumerate(cols):
                if i + j >= len(figures):
                    break
                fname, (title, desc) = figures[i + j]
                fpath = FIGURES_DIR / fname
                if fpath.exists():
                    with col:
                        st.subheader(title)
                        st.caption(desc)
                        st.image(str(fpath), use_container_width=True)
                else:
                    with col:
                        st.info(f"Graphique non trouvé : {fname}")
            st.divider()


# ─────────────────────────────────────────────────────────────
# PAGE : DONNÉES
# ─────────────────────────────────────────────────────────────
elif page == "🗂 Données":
    st.title("Données")

    tab_raw, tab_clean = st.tabs(["📥 Données brutes", "✅ Données nettoyées"])

    with tab_raw:
        df_raw = load_data(RAW_PATH)
        if df_raw is None:
            st.info("Données brutes non trouvées. Lance le pipeline.")
        else:
            st.caption(f"{len(df_raw)} panneaux · {len(df_raw.columns)} colonnes")
            st.dataframe(df_raw, use_container_width=True)
            c1, c2, c3 = st.columns(3)
            c1.metric("Panneaux", len(df_raw))
            c2.metric("Colonnes", len(df_raw.columns))
            c3.metric("Valeurs manquantes", int(df_raw.isnull().sum().sum()))

    with tab_clean:
        df_clean = load_data(CLEAN_PATH)
        if df_clean is None:
            st.info("Données nettoyées non trouvées. Lance le pipeline.")
        else:
            st.caption(f"{len(df_clean)} panneaux · {len(df_clean.columns)} colonnes")
            st.dataframe(df_clean, use_container_width=True)

            st.subheader("Statistiques descriptives")
            st.dataframe(df_clean.describe().round(2), use_container_width=True)


# ─────────────────────────────────────────────────────────────
# PAGE : PRÉDICTION
# ─────────────────────────────────────────────────────────────
elif page == "🔮 Prédiction":
    st.title("Prédiction — Nouveau panneau")
    st.markdown("Saisisse les caractéristiques d'un emplacement pour obtenir un score de visibilité estimé.")

    if not MODEL_PATH.exists():
        st.warning("Modèle non trouvé. Lance le pipeline d'abord (page **⚙️ Pipeline**).")
    else:
        with st.form("prediction_form"):
            st.subheader("Caractéristiques de l'emplacement")

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("**Localisation**")
                latitude   = st.number_input("Latitude",  value=6.357, format="%.4f", min_value=6.340, max_value=6.405)
                longitude  = st.number_input("Longitude", value=2.420, format="%.4f", min_value=2.340, max_value=2.430)
                quartier   = st.selectbox("Quartier", options=[
                    (0, "Akpakpa"), (1, "Cadjehoun"), (2, "Fidjrossè"), (3, "Gbèdjromèdji"),
                    (4, "Haie Vive"), (5, "Jéricho"), (6, "Dantokpa"), (7, "Agla"),
                ], format_func=lambda x: x[1])

            with c2:
                st.markdown("**Panneau**")
                height_m    = st.slider("Hauteur (m)",  min_value=2, max_value=15, value=7)
                size_m2     = st.slider("Surface (m²)", min_value=4, max_value=50, value=18)
                is_digital  = st.checkbox("Digital (LED)", value=True)
                panel_type  = st.selectbox("Type de panneau", [(0, "Billboard"), (1, "Mupi"), (2, "Totem")], format_func=lambda x: x[1])
                age_panneau = st.slider("Âge (années)", min_value=0, max_value=20, value=1)

            with c3:
                st.markdown("**Contexte**")
                traffic         = st.number_input("Trafic (veh/jour)", min_value=0, max_value=50000, value=7500, step=500)
                road_type       = st.selectbox("Type de route", [(0, "Boulevard"), (1, "Avenue"), (2, "Rue")], format_func=lambda x: x[1])
                pedestrian_dens = st.slider("Densité piétonne (0-100)", 0, 100, 88)
                competition     = st.slider("Panneaux concurrents (500m)", 0, 10, 2)
                dist_main_road  = st.number_input("Distance route principale (m)", 0, 500, 5)
                daylight        = st.slider("Heures d'exposition lumière/jour", 4, 16, 10)

            submitted = st.form_submit_button("Calculer le score", use_container_width=True, type="primary")

        if submitted:
            try:
                sys.path.insert(0, ".")
                from src.model import BillboardVisibilityModel

                loaded_model = BillboardVisibilityModel.load(str(MODEL_PATH))

                dist_center  = ((latitude - 6.366)**2 + (longitude - 2.419)**2)**0.5 * 111
                dist_beach   = ((latitude - 6.350)**2 + (longitude - 2.385)**2)**0.5 * 111
                dist_port    = ((latitude - 6.355)**2 + (longitude - 2.425)**2)**0.5 * 111
                geo_quadrant = int(latitude > 6.372) * 2 + int(longitude > 2.385)

                new_billboard = pd.DataFrame([{
                    "latitude":                   latitude,
                    "longitude":                  longitude,
                    "traffic_flow_estim":         traffic,
                    "height_m":                   float(height_m),
                    "size_m2":                    float(size_m2),
                    "distance_to_center_km":      dist_center,
                    "distance_to_main_road_m":    float(dist_main_road),
                    "hours_of_daylight_exposure": float(daylight),
                    "pedestrian_density_score":   float(pedestrian_dens),
                    "competition_radius_500m":    competition,
                    "panel_type_enc":             panel_type[0],
                    "quartier_enc":               quartier[0],
                    "road_type_enc":              road_type[0],
                    "ratio_surface_hauteur":      size_m2 / height_m,
                    "log_traffic":                np.log1p(traffic),
                    "score_accessibilite":        dist_main_road / 200 + dist_center / 5,
                    "indice_saturation":          competition * (pedestrian_dens / 100),
                    "is_digital":                 int(is_digital),
                    "age_panneau":                age_panneau,
                    "effective_exposure_hours":   daylight if not is_digital else 24,
                    "distance_to_beach_km":       dist_beach,
                    "distance_to_port_km":        dist_port,
                    "geo_quadrant":               geo_quadrant,
                }])

                feat_cols = loaded_model.feature_names
                new_billboard = new_billboard[feat_cols]
                score = loaded_model.predict(new_billboard)[0]

                st.divider()
                col_score, col_interp = st.columns([1, 2])

                with col_score:
                    color = "#2ecc71" if score >= 70 else "#f39c12" if score >= 50 else "#e74c3c"
                    st.markdown(f"""
                    <div style='background:{color}22; border-left:4px solid {color};
                                padding:1.5rem; border-radius:8px; text-align:center;'>
                        <p style='font-size:0.9rem; color:#666; margin:0'>Score de visibilité estimé</p>
                        <p style='font-size:3rem; font-weight:bold; color:{color}; margin:0.2rem 0'>{score:.1f}</p>
                        <p style='font-size:0.85rem; color:#666; margin:0'>/ 100</p>
                    </div>
                    """, unsafe_allow_html=True)

                with col_interp:
                    if score >= 70:
                        st.success("**Excellent emplacement** — Fort potentiel publicitaire")
                        st.markdown("Ce site présente d'excellentes caractéristiques : trafic élevé, bonne visibilité, faible concurrence.")
                    elif score >= 50:
                        st.warning("**Bon emplacement** — Potentiel modéré")
                        st.markdown("Site correct avec quelques points d'amélioration possibles.")
                    elif score >= 30:
                        st.warning("**Emplacement moyen** — À développer")
                        st.markdown("Des contraintes limitent la visibilité. Considérer l'amélioration du trafic ou de la taille.")
                    else:
                        st.error("**Emplacement faible** — Peu attractif")
                        st.markdown("Ce site présente des caractéristiques défavorables pour la publicité.")

            except Exception as e:
                st.error(f"Erreur lors de la prédiction : {e}")


# ─────────────────────────────────────────────────────────────
# PAGE : PIPELINE
# ─────────────────────────────────────────────────────────────
elif page == "⚙️ Pipeline":
    st.title("Exécution du pipeline")
    st.markdown("""
    Lance le pipeline complet ou une étape spécifique directement depuis le dashboard.

    ```
    data_generation → cleaning → feature_engineering → model → evaluation
    ```
    """)

    col_btn, col_info = st.columns([1, 2])

    with col_btn:
        st.subheader("Actions")
        run_full = st.button("▶ Pipeline complet", use_container_width=True, type="primary")
        run_gen  = st.button("1. Générer les données", use_container_width=True)

    with col_info:
        st.subheader("Étapes du pipeline")
        steps = [
            ("1. data_generation", "Génère 45 panneaux synthétiques avec bruit réaliste"),
            ("2. cleaning",        "Valide, dédoublonne, impute les valeurs manquantes"),
            ("3. feature_engineering", "Encode les catégories, crée 20 features ML"),
            ("4. model",           "RandomForest 100 arbres + cross-validation 5-fold"),
            ("5. evaluation",      "6 graphiques + rapport JSON + modèle .pkl"),
        ]
        for name, desc in steps:
            st.markdown(f"**{name}** — {desc}")

    if run_full or run_gen:
        args = [sys.executable, "main.py"]
        if run_gen:
            args += ["--step", "generate"]

        st.divider()
        with st.spinner("Exécution en cours..."):
            output_placeholder = st.empty()
            try:
                result = subprocess.run(
                    args,
                    capture_output=True,
                    text=True,
                    cwd=str(Path(__file__).parent),
                    timeout=120,
                )
                if result.returncode == 0:
                    st.success("Pipeline terminé avec succès !")
                    st.cache_data.clear()
                else:
                    st.error("Le pipeline a rencontré une erreur.")

                with st.expander("Logs du pipeline", expanded=True):
                    st.code(result.stdout or "(aucun output)")
                    if result.stderr:
                        st.code(result.stderr, language="text")

            except subprocess.TimeoutExpired:
                st.error("Timeout — le pipeline a pris trop de temps.")
            except Exception as e:
                st.error(f"Erreur : {e}")

    st.divider()
    st.subheader("Fichiers générés")

    files = {
        "Données brutes":       RAW_PATH,
        "Données nettoyées":    CLEAN_PATH,
        "Rapport JSON":         REPORT_PATH,
        "Modèle (.pkl)":        MODEL_PATH,
    }

    for label, path in files.items():
        if path.exists():
            size_kb = path.stat().st_size / 1024
            st.success(f"✅ **{label}** — `{path}` ({size_kb:.1f} Ko)")
        else:
            st.error(f"❌ **{label}** — non trouvé")

    figs_found = list(FIGURES_DIR.glob("*.png")) if FIGURES_DIR.exists() else []
    if figs_found:
        st.success(f"✅ **Graphiques** — {len(figs_found)}/6 générés dans `reports/figures/`")
    else:
        st.error("❌ **Graphiques** — non trouvés")
