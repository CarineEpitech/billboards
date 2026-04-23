"""
Génère les trois documents Word de documentation du projet Billboard Cotonou.
"""

from docx import Document
from docx.shared import Pt, RGBColor, Cm, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import json
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────────────
# UTILITAIRES DE STYLE
# ─────────────────────────────────────────────────────────────────────────────

BLEU_TITRE  = RGBColor(0x1A, 0x52, 0x76)   # #1A5276
BLEU_CLAIR  = RGBColor(0x21, 0x8D, 0xBB)   # #218DBB
VERT        = RGBColor(0x1E, 0x8B, 0x4C)   # #1E8B4C
ROUGE       = RGBColor(0xC0, 0x39, 0x2B)   # #C0392B
GRIS_TEXTE  = RGBColor(0x2C, 0x3E, 0x50)   # #2C3E50
GRIS_FOND   = RGBColor(0xF2, 0xF3, 0xF4)   # #F2F3F4
ORANGE      = RGBColor(0xCA, 0x6F, 0x1E)   # #CA6F1E


def set_cell_bg(cell, hex_color: str):
    """Applique une couleur de fond à une cellule de tableau."""
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd  = OxmlElement("w:shd")
    shd.set(qn("w:val"),   "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"),  hex_color)
    tcPr.append(shd)


def heading(doc, text, level=1, color=None):
    h = doc.add_heading(text, level=level)
    if color:
        for run in h.runs:
            run.font.color.rgb = color
    h.paragraph_format.space_before = Pt(14 if level == 1 else 8)
    h.paragraph_format.space_after  = Pt(6)
    return h


def para(doc, text, bold=False, italic=False, color=None, size=10.5, indent=0):
    p = doc.add_paragraph()
    p.paragraph_format.space_after  = Pt(4)
    p.paragraph_format.left_indent  = Cm(indent)
    run = p.add_run(text)
    run.bold   = bold
    run.italic = italic
    run.font.size = Pt(size)
    if color:
        run.font.color.rgb = color
    return p


def bullet(doc, text, level=0, color=None):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.left_indent  = Cm(0.5 + level * 0.5)
    p.paragraph_format.space_after  = Pt(3)
    run = p.add_run(text)
    run.font.size = Pt(10.5)
    if color:
        run.font.color.rgb = color
    return p


def divider(doc):
    p = doc.add_paragraph("─" * 80)
    p.runs[0].font.color.rgb = RGBColor(0xCC, 0xCC, 0xCC)
    p.runs[0].font.size = Pt(7)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after  = Pt(4)


def table_2col(doc, data: list[tuple], header: tuple = None, col_widths=(8, 8)):
    """Crée un tableau à deux colonnes avec header optionnel."""
    rows = (1 if header else 0) + len(data)
    tbl  = doc.add_table(rows=rows, cols=2)
    tbl.style = "Table Grid"
    tbl.alignment = WD_TABLE_ALIGNMENT.LEFT

    row_idx = 0
    if header:
        for j, h in enumerate(header):
            cell = tbl.rows[0].cells[j]
            cell.text = h
            cell.paragraphs[0].runs[0].bold = True
            cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            cell.paragraphs[0].runs[0].font.size = Pt(10)
            set_cell_bg(cell, "1A5276")
        row_idx = 1

    for left, right in data:
        r = tbl.rows[row_idx]
        r.cells[0].text = left
        r.cells[1].text = right
        r.cells[0].paragraphs[0].runs[0].font.size = Pt(10)
        r.cells[1].paragraphs[0].runs[0].font.size = Pt(10)
        if row_idx % 2 == 0:
            set_cell_bg(r.cells[0], "EAF2F8")
            set_cell_bg(r.cells[1], "EAF2F8")
        row_idx += 1

    for i, w in enumerate(col_widths):
        for row in tbl.rows:
            row.cells[i].width = Cm(w)

    doc.add_paragraph()
    return tbl


def page_break(doc):
    doc.add_page_break()


def set_margins(doc):
    for section in doc.sections:
        section.top_margin    = Cm(2.0)
        section.bottom_margin = Cm(2.0)
        section.left_margin   = Cm(2.5)
        section.right_margin  = Cm(2.5)


# ─────────────────────────────────────────────────────────────────────────────
# DOCUMENT 1 — PRÉSENTATION DÉTAILLÉE DU PROJET
# ─────────────────────────────────────────────────────────────────────────────

def build_doc1():
    doc = Document()
    set_margins(doc)

    # ── Titre principal ──────────────────────────────────────────────────────
    title = doc.add_heading("Billboard Geolocation Platform", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in title.runs:
        run.font.color.rgb = BLEU_TITRE
        run.font.size = Pt(22)

    sub = doc.add_paragraph("Cotonou, Bénin — Prototype V1")
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.runs[0].font.size = Pt(13)
    sub.runs[0].font.color.rgb = BLEU_CLAIR
    sub.runs[0].bold = True

    sub2 = doc.add_paragraph("Présentation détaillée du projet — Pipeline ML complet")
    sub2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub2.runs[0].font.size = Pt(11)
    sub2.runs[0].font.color.rgb = GRIS_TEXTE

    doc.add_paragraph()
    divider(doc)

    # ── 1. CONTEXTE ET PROBLÈME ─────────────────────────────────────────────
    heading(doc, "1. Contexte et Problème Business", 1, BLEU_TITRE)

    para(doc,
         "Le marché de l'affichage extérieur (Out-Of-Home) à Cotonou représente "
         "plusieurs centaines de millions de francs CFA annuellement. Pourtant, "
         "aucune base de données centralisée n'existe pour les panneaux publicitaires. "
         "Les acteurs du marché travaillent à l'aveugle.", size=10.5)

    heading(doc, "Conséquences directes :", 3, GRIS_TEXTE)
    bullet(doc, "Les annonceurs ne peuvent pas comparer deux emplacements de façon objective")
    bullet(doc, "Les propriétaires fixent leurs tarifs à l'instinct, pas selon la valeur réelle")
    bullet(doc, "L'optimisation du placement est impossible sans données structurées")
    bullet(doc, "Aucun score de visibilité standardisé n'existe sur le marché béninois")

    heading(doc, "Question ML centrale :", 3, GRIS_TEXTE)
    para(doc,
         "Étant donné l'emplacement et les caractéristiques d'un panneau publicitaire, "
         "quel est son score de visibilité estimé (0–100) ?",
         bold=True, color=BLEU_CLAIR)

    divider(doc)

    # ── 2. OBJECTIF STRATÉGIQUE ──────────────────────────────────────────────
    heading(doc, "2. Objectif Stratégique", 1, BLEU_TITRE)

    para(doc, "Construire une plateforme centralisée permettant :", size=10.5)
    table_2col(doc, [
        ("Géolocalisation",       "Latitude / Longitude GPS de chaque panneau"),
        ("Identification",        "Quartier, type de route, propriétaire"),
        ("Classification",        "Type de panneau : digital / statique / bâche / LED"),
        ("Score de visibilité",   "Indice ML continu entre 0 et 100"),
        ("Feature engineering",  "23 variables ML dérivées de la connaissance terrain"),
        ("Modèle prédictif",      "RandomForest + baseline Ridge — évaluation comparative"),
        ("Roadmap V3",            "Détection satellite, CNN scoring, optimisation multi-variable"),
    ], header=("Fonctionnalité", "Description"), col_widths=(6, 10))

    divider(doc)

    # ── 3. ARCHITECTURE DU PROJET ────────────────────────────────────────────
    heading(doc, "3. Architecture du Projet", 1, BLEU_TITRE)

    table_2col(doc, [
        ("config/config.yaml",           "Configuration centralisée : hyperparamètres, chemins, bbox géo"),
        ("data/raw/billboards_raw.csv",  "45 panneaux bruts avec erreurs intentionnelles injectées"),
        ("data/processed/billboards_clean.csv", "43 panneaux propres après pipeline de nettoyage"),
        ("src/data_generation.py",       "Génération du dataset synthétique réaliste"),
        ("src/cleaning.py",              "Pipeline de nettoyage : validation, imputation, dédoublonnage"),
        ("src/feature_engineering.py",   "Encodage, features dérivées, features géospatiales"),
        ("src/model.py",                 "RandomForestRegressor + Ridge baseline + Learning Curve"),
        ("src/evaluation.py",            "6 graphiques + métriques + rapport JSON"),
        ("main.py",                      "Orchestrateur CLI : pipeline complet en une commande"),
        ("reports/figures/ (6 PNG)",     "Graphiques de diagnostic générés automatiquement"),
        ("reports/model_results.json",   "Rapport complet d'évaluation structuré"),
        ("PRESENTATION.md",              "Discours académique 15–20 min (9 slides)"),
        ("PITCH.md",                     "Pitch 5 minutes investisseur / jury"),
    ], header=("Fichier", "Rôle"), col_widths=(6.5, 9.5))

    divider(doc)
    page_break(doc)

    # ── 4. PIPELINE EN 5 ÉTAPES ──────────────────────────────────────────────
    heading(doc, "4. Pipeline ML — Détail des 5 Étapes", 1, BLEU_TITRE)

    heading(doc, "Étape 1 — Génération des données (data_generation.py)", 2, BLEU_CLAIR)
    para(doc,
         "En l'absence de données terrain, un dataset synthétique réaliste de 45 panneaux "
         "a été généré sur 10 quartiers réels de Cotonou.", size=10.5)
    bullet(doc, "Distribution pondérée des quartiers (Dantokpa et Centre surreprésentés)")
    bullet(doc, "Coordonnées GPS avec dispersion gaussienne σ=0.008° ≈ 900m de rayon")
    bullet(doc, "Score de visibilité non-linéaire : log(taille) + sqrt(trafic) + N(0,8)")
    bullet(doc, "Bruit gaussien intentionnel (σ=8 pts) : simule les facteurs non capturés")
    bullet(doc, "Erreurs injectées : GPS hors zone, scores aberrants, doublons, NaN (8%)")

    heading(doc, "Étape 2 — Nettoyage (cleaning.py)", 2, BLEU_CLAIR)
    para(doc, "Pipeline en 5 sous-étapes dans un ordre précis :", size=10.5)
    table_2col(doc, [
        ("1. Validation GPS",    "Suppression des coordonnées hors bbox Cotonou"),
        ("2. Score clipping",    "Écrêtage des scores hors [0, 100]"),
        ("3. Déduplication",     "2 passes : panel_id exact + géographique à 100m"),
        ("4. Imputation numérique", "Médiane (robuste aux outliers) sur 5 colonnes"),
        ("5. Imputation catégorielle", "Mode ou 'Inconnu' pour le propriétaire"),
    ], header=("Étape", "Action"), col_widths=(5, 11))
    para(doc, "Résultat : 45 → 43 panneaux propres, 0 valeur manquante.", bold=True, color=VERT)

    heading(doc, "Étape 3 — Feature Engineering (feature_engineering.py)", 2, BLEU_CLAIR)
    table_2col(doc, [
        ("Label Encoding",         "panel_type, quartier, road_type → entiers (pas One-Hot : n/p trop faible)"),
        ("log_traffic",            "Log du trafic — capture la saturation non-linéaire"),
        ("ratio_surface_hauteur",  "Rapport taille/hauteur — index d'impact visuel"),
        ("indice_saturation",      "Concurrence × densité piétonne — attention diluée"),
        ("is_digital",             "Flag binaire fort — digital vs statique"),
        ("age_panneau",            "2024 − année d'installation"),
        ("effective_exposure_hours", "24h si digital, sinon heures de lumière du jour"),
        ("score_accessibilite",    "Distance route + distance centre normalisées"),
        ("Features géospatiales",  "Distance plage, port, centre-ville + geo_quadrant"),
    ], header=("Feature", "Justification"), col_widths=(5, 11))
    para(doc, "Total : 23 features ML finales.", bold=True, color=VERT)

    heading(doc, "Étape 4 — Modèle ML (model.py)", 2, BLEU_CLAIR)
    para(doc, "Deux modèles entraînés et comparés :", size=10.5)
    table_2col(doc, [
        ("RandomForestRegressor",  "100 arbres, max_depth=4, min_samples_leaf=4 — modèle principal"),
        ("Ridge Regression",       "α=1.0 + StandardScaler — baseline de comparaison obligatoire"),
        ("OOB Score",              "Validation out-of-bag gratuite intégrée au RF"),
        ("5-Fold Cross-Validation","Estimation non biaisée de la performance de généralisation"),
        ("Learning Curve",         "Train vs CV R² selon taille dataset — diagnostic overfitting"),
        ("compare_with_baseline()", "Tableau comparatif RF vs Ridge sur R², RMSE, MAE"),
    ], header=("Composant", "Description"), col_widths=(5, 11))

    heading(doc, "Étape 5 — Évaluation (evaluation.py)", 2, BLEU_CLAIR)
    table_2col(doc, [
        ("01_pred_vs_actual.png",    "Scatter Prédit vs Réel avec zone ±10 pts"),
        ("02_residuals.png",         "Résidus vs prédictions + distribution (gaussienne ?)"),
        ("03_feature_importance.png","MDI importance + courbe cumulée (règle 80/20)"),
        ("04_score_distribution.png","Distribution train / test réel / test prédit"),
        ("05_model_comparison.png",  "Barres RF vs Ridge sur R², RMSE, MAE"),
        ("06_learning_curve.png",    "Train et CV R² vs taille dataset + bandes ±1σ"),
    ], header=("Graphique", "Contenu"), col_widths=(5.5, 10.5))

    divider(doc)
    page_break(doc)

    # ── 5. RÉSULTATS OBTENUS ────────────────────────────────────────────────
    heading(doc, "5. Résultats Obtenus", 1, BLEU_TITRE)

    table_2col(doc, [
        ("Panneaux générés",          "45 panneaux sur 10 quartiers de Cotonou"),
        ("Panneaux après cleaning",   "43 (2 doublons, 1 score aberrant supprimés)"),
        ("Features ML",               "23 (brutes + dérivées + géospatiales)"),
        ("OOB R²",                    "0.279 — validation interne RF"),
        ("RF CV R² (5-fold)",         "−0.168 ± 0.424 — variance élevée normale sur 34 obs"),
        ("Ridge CV R² (5-fold)",      "0.163 ± 0.142 — plus stable car modèle plus simple"),
        ("Top feature (MDI)",         "panel_type_enc = 26.2% d'importance"),
        ("Top 3 features cumulées",   "panel_type + traffic + longitude = 50.5%"),
        ("Prédiction démo",           "Panneau digital, Dantokpa, boulevard → 72.2 / 100"),
        ("Durée pipeline complet",    "< 10 secondes"),
    ], header=("Indicateur", "Valeur"), col_widths=(6, 10))

    para(doc,
         "Note sur les métriques : avec 43 observations bruitées et 9 en test set, "
         "les métriques présentent une forte variance statistique. "
         "C'est la réalité d'un petit dataset — documentée et assumée.",
         italic=True, color=ORANGE)

    divider(doc)

    # ── 6. ROADMAP ──────────────────────────────────────────────────────────
    heading(doc, "6. Roadmap V1 → V2 → V3", 1, BLEU_TITRE)

    table_2col(doc, [
        ("V1 — Prototype (ACTUEL)",
         "Dataset synthétique 45 panneaux · Pipeline cleaning · 23 features ML · "
         "RandomForest + Ridge baseline · 6 graphiques · Rapport JSON · "
         "Discours académique + Pitch 5 min"),
        ("V2 — Production (3–6 mois)",
         "Collecte terrain 500+ panneaux réels · OpenStreetMap features · "
         "XGBoost + Optuna · SHAP values · API FastAPI · Dashboard Streamlit · "
         "Carte interactive Folium"),
        ("V3 — Intelligence (12–18 mois)",
         "Détection satellite YOLOv8 sur Sentinel-2 · CNN scoring qualité visuelle · "
         "Optimisation multi-variable (algo génétique) · MLOps MLflow · "
         "Extension Lomé, Abidjan, Dakar"),
    ], header=("Version", "Contenu"), col_widths=(4, 12))

    # ── Pied de page ─────────────────────────────────────────────────────────
    doc.add_paragraph()
    divider(doc)
    footer = doc.add_paragraph("Billboard Geolocation Platform — Cotonou, Bénin · Prototype V1 · 2024")
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.runs[0].font.size = Pt(8)
    footer.runs[0].font.color.rgb = RGBColor(0x99, 0x99, 0x99)

    path = Path("docs/01_PRESENTATION_PROJET.docx")
    doc.save(str(path))
    print(f"[OK] {path}")


# ─────────────────────────────────────────────────────────────────────────────
# DOCUMENT 2 — AVANT / APRÈS
# ─────────────────────────────────────────────────────────────────────────────

def build_doc2():
    doc = Document()
    set_margins(doc)

    title = doc.add_heading("Avant / Après", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in title.runs:
        run.font.color.rgb = BLEU_TITRE
        run.font.size = Pt(22)

    sub = doc.add_paragraph("Billboard Geolocation Platform — Impact du Projet")
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.runs[0].font.size = Pt(12)
    sub.runs[0].font.color.rgb = BLEU_CLAIR
    sub.runs[0].bold = True
    doc.add_paragraph()
    divider(doc)

    sections = [
        # (titre_section, avant, après)
        (
            "1. Données",
            [
                "Aucune base de données des panneaux à Cotonou",
                "Informations dispersées : carnet terrain, photos isolées, mémoire des agents",
                "Pas de format standardisé — impossible à croiser",
                "Aucune donnée GPS fiable pour la majorité des panneaux",
            ],
            [
                "Dataset structuré de 45 panneaux avec 18 colonnes standardisées",
                "Coordonnées GPS (lat/lon), quartier, type, taille, hauteur, propriétaire",
                "Pipeline de génération reproductible (seed fixe) → résultats identiques à chaque run",
                "Format CSV propre, exportable dans tout outil (Excel, Power BI, QGIS)",
            ],
        ),
        (
            "2. Qualité des données",
            [
                "Erreurs de saisie non détectées (scores > 100, coordonnées erronées)",
                "Doublons non détectés (même panneau saisi deux fois)",
                "Valeurs manquantes ignorées ou gérées manuellement",
                "Aucun audit de qualité systématique",
            ],
            [
                "Pipeline de cleaning automatisé en 5 étapes ordonnées",
                "Détection GPS hors zone + écrêtage des scores aberrants",
                "Déduplication en 2 passes (panel_id + géographique à 100m)",
                "Imputation médiane / mode avec traçabilité complète",
                "Rapport de qualité JSON généré à chaque exécution",
            ],
        ),
        (
            "3. Variables analytiques",
            [
                "Variables brutes uniquement (hauteur, type) — non transformées",
                "Aucune variable de trafic ni de concurrence locale",
                "Pas de connaissance géospatiale (distance au port, à la plage)",
                "Relation linéaire supposée entre variables et score",
            ],
            [
                "23 features ML : brutes + dérivées + géospatiales",
                "log_traffic (capture la saturation), ratio_surface_hauteur, indice_saturation",
                "Distance plage, port, centre-ville calculées automatiquement",
                "effective_exposure_hours : digital = 24h vs statique = heures de lumière",
                "Interactions non-linéaires capturées par le Random Forest",
            ],
        ),
        (
            "4. Modèle prédictif",
            [
                "Aucun modèle de scoring — décisions 100% subjectives",
                "Pas de comparaison entre emplacements possible",
                "Expertise terrain non formalisée ni transférable",
                "Aucune validation de la pertinence des critères utilisés",
            ],
            [
                "RandomForestRegressor entraîné, validé, sérialisé",
                "Baseline Ridge Regression pour valider la valeur ajoutée du RF",
                "5-Fold Cross-Validation + OOB Score : deux mécanismes de validation",
                "Learning curve : diagnostic overfitting visuel et quantifié",
                "Feature importance : validation que panel_type (26%) et trafic (14%) dominent",
                "Prédiction demo : nouveau panneau scoré en < 1 seconde",
            ],
        ),
        (
            "5. Visualisation et rapports",
            [
                "Aucun graphique de diagnostic",
                "Aucun rapport structuré",
                "Aucune comparaison visuelle possible entre modèles",
            ],
            [
                "6 graphiques PNG générés automatiquement à chaque run",
                "Prédit vs Réel · Résidus · Feature importance (+ cumulé) · Distribution",
                "Comparaison RF vs Ridge (barres) · Learning curve (biais-variance)",
                "Rapport JSON complet : métriques, hyperparamètres, top features, comparaison",
            ],
        ),
        (
            "6. Communication",
            [
                "Aucun support de présentation structuré",
                "Pas de pitch formalisé",
                "Pas de documentation technique",
            ],
            [
                "PRESENTATION.md : discours académique 9 slides, 15–20 min",
                "PITCH.md : pitch 5 minutes investisseur/jury avec minutage",
                "README.md : documentation technique complète avec roadmap",
                "5 réponses préparées aux questions difficiles",
                "3 phrases de secours si perte du fil",
            ],
        ),
        (
            "7. Reproductibilité et déploiement",
            [
                "Aucune reproductibilité : résultats non documentés",
                "Pas de configuration centralisée",
                "Pas de pipeline automatisé",
            ],
            [
                "config.yaml central : modifier un paramètre suffit (seed, n_samples, alpha...)",
                "python main.py : pipeline complet en une commande, < 10 secondes",
                "Modèle sérialisé (pickle) : rechargeable et réutilisable",
                "Git versionné : historique complet, branche dédiée",
            ],
        ),
    ]

    for titre, avant_list, apres_list in sections:
        heading(doc, titre, 1, BLEU_TITRE)

        # Tableau 2 colonnes : Avant | Après
        rows  = max(len(avant_list), len(apres_list))
        tbl   = doc.add_table(rows=rows + 1, cols=2)
        tbl.style = "Table Grid"

        # Header
        h_avant = tbl.rows[0].cells[0]
        h_apres = tbl.rows[0].cells[1]
        h_avant.text = "AVANT"
        h_apres.text = "APRÈS"
        for cell, color in [(h_avant, "C0392B"), (h_apres, "1E8B4C")]:
            set_cell_bg(cell, color)
            cell.paragraphs[0].runs[0].bold = True
            cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            cell.paragraphs[0].runs[0].font.size = Pt(11)
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

        for i in range(rows):
            row = tbl.rows[i + 1]
            # Avant
            a_text = avant_list[i] if i < len(avant_list) else ""
            row.cells[0].text = f"✗  {a_text}" if a_text else ""
            if row.cells[0].paragraphs[0].runs:
                row.cells[0].paragraphs[0].runs[0].font.size = Pt(10)
                row.cells[0].paragraphs[0].runs[0].font.color.rgb = ROUGE
            # Après
            b_text = apres_list[i] if i < len(apres_list) else ""
            row.cells[1].text = f"✓  {b_text}" if b_text else ""
            if row.cells[1].paragraphs[0].runs:
                row.cells[1].paragraphs[0].runs[0].font.size = Pt(10)
                row.cells[1].paragraphs[0].runs[0].font.color.rgb = VERT

            # Fond alternant
            bg = "FDEDEC" if i % 2 == 0 else "FFFFFF"
            set_cell_bg(row.cells[0], bg)
            bg2 = "EAFAF1" if i % 2 == 0 else "FFFFFF"
            set_cell_bg(row.cells[1], bg2)

        for row in tbl.rows:
            row.cells[0].width = Cm(8)
            row.cells[1].width = Cm(8)

        doc.add_paragraph()
        divider(doc)

    # Résumé chiffré
    heading(doc, "Résumé Chiffré de l'Impact", 1, BLEU_TITRE)
    table_2col(doc, [
        ("Données",       "0 base structurée → 45 panneaux, 18 colonnes, 0 NaN"),
        ("Cleaning",      "Manuel / absent → Pipeline 5 étapes automatisé"),
        ("Features",      "Variables brutes → 23 features ML dérivées"),
        ("Modèle",        "Aucun → RF + baseline Ridge + CV + OOB + Learning curve"),
        ("Graphiques",    "0 → 6 graphiques de diagnostic automatiques"),
        ("Rapport",       "Absent → JSON structuré avec toutes les métriques"),
        ("Présentation",  "Aucune → Pitch 5 min + Discours 15 min + README"),
        ("Commande",      "Processus manuel → python main.py (< 10 secondes)"),
    ], header=("Dimension", "Avant → Après"), col_widths=(4, 12))

    doc.add_paragraph()
    divider(doc)
    footer = doc.add_paragraph("Billboard Geolocation Platform — Avant / Après · Prototype V1 · 2024")
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.runs[0].font.size = Pt(8)
    footer.runs[0].font.color.rgb = RGBColor(0x99, 0x99, 0x99)

    path = Path("docs/02_AVANT_APRES.docx")
    doc.save(str(path))
    print(f"[OK] {path}")


# ─────────────────────────────────────────────────────────────────────────────
# DOCUMENT 3 — OUTILS DANS L'ORDRE
# ─────────────────────────────────────────────────────────────────────────────

def build_doc3():
    doc = Document()
    set_margins(doc)

    title = doc.add_heading("Stack Technique & Outils", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in title.runs:
        run.font.color.rgb = BLEU_TITRE
        run.font.size = Pt(22)

    sub = doc.add_paragraph("Billboard Geolocation Platform — Liste récapitulative dans l'ordre d'utilisation")
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.runs[0].font.size = Pt(11)
    sub.runs[0].font.color.rgb = BLEU_CLAIR
    sub.runs[0].bold = True
    doc.add_paragraph()
    divider(doc)

    # ── SECTION A : OUTILS DANS L'ORDRE DU PIPELINE ─────────────────────────
    heading(doc, "A. Outils par Étape de Pipeline", 1, BLEU_TITRE)

    steps = [
        ("ÉTAPE 1 — Génération des données", "data_generation.py", [
            ("numpy",          "1.24+", "Génération des nombres aléatoires (np.random.default_rng, "
                                        "distributions gaussienne, log-normale, Poisson, bootstrap)"),
            ("numpy",          "1.24+", "Calculs vectorisés : clip, sqrt, log1p, exp, radians"),
            ("pandas",         "2.0+",  "Création du DataFrame, gestion des types, export CSV"),
            ("yaml (PyYAML)",  "6.0+",  "Lecture de config.yaml pour n_samples, seed, noise_level"),
            ("pathlib",        "std",   "Gestion des chemins cross-platform (Path.mkdir, .parent)"),
        ]),
        ("ÉTAPE 2 — Nettoyage des données", "cleaning.py", [
            ("pandas",         "2.0+",  "Filtrage (between, isnull, drop_duplicates), fillna, "
                                        "rename, astype, sort_values"),
            ("numpy",          "1.24+",  "clip() pour écrêtage des scores, sum() pour audit NaN"),
            ("yaml (PyYAML)",  "6.0+",  "Lecture des seuils de validation (lat_min, lat_max, score_min...)"),
            ("pathlib",        "std",   "Création du répertoire data/processed/ si absent"),
        ]),
        ("ÉTAPE 3 — Feature Engineering", "feature_engineering.py", [
            ("numpy",          "1.24+", "log1p(), sqrt(), exp(), radians(), where() pour features dérivées"),
            ("pandas",         "2.0+",  "map() pour Label Encoding, DataFrame.copy(), "
                                        "fillna(median) de secours"),
            ("yaml (PyYAML)",  "6.0+",  "Lecture de la liste features.numerical / features.categorical"),
        ]),
        ("ÉTAPE 4 — Entraînement du modèle", "model.py", [
            ("sklearn.ensemble.RandomForestRegressor", "1.3+",
             "Modèle principal : 100 arbres, max_depth=4, min_samples_leaf=4, oob_score=True"),
            ("sklearn.linear_model.Ridge",             "1.3+",
             "Baseline : régression régularisée L2 (α=1.0)"),
            ("sklearn.preprocessing.StandardScaler",   "1.3+",
             "Normalisation obligatoire pour Ridge"),
            ("sklearn.pipeline.Pipeline",              "1.3+",
             "StandardScaler + Ridge encapsulés — garantit cohérence train/test"),
            ("sklearn.model_selection.train_test_split","1.3+",
             "Split 80/20 reproductible (shuffle=True, random_state=42)"),
            ("sklearn.model_selection.KFold",          "1.3+",
             "5-Fold CV avec shuffle — estimation non biaisée"),
            ("sklearn.model_selection.cross_val_score","1.3+",
             "Scoring R² sur chaque fold, retourne array de 5 scores"),
            ("sklearn.model_selection.learning_curve", "1.3+",
             "Train vs val R² pour 6 tailles de dataset — diagnostic biais-variance"),
            ("sklearn.metrics.r2_score",               "1.3+",
             "Coefficient de détermination"),
            ("sklearn.metrics.mean_squared_error",     "1.3+",
             "MSE → RMSE = sqrt(MSE)"),
            ("sklearn.metrics.mean_absolute_error",    "1.3+",
             "MAE — erreur absolue moyenne"),
            ("pickle",                                 "std",
             "Sérialisation du modèle entraîné (dump/load)"),
        ]),
        ("ÉTAPE 5 — Évaluation & Graphiques", "evaluation.py", [
            ("matplotlib",          "3.7+", "Backend Agg (non-interactif), Figure/Axes, savefig(dpi=150)"),
            ("matplotlib.pyplot",   "3.7+", "scatter, plot, hist, barh, fill_between, axhline, axvline"),
            ("matplotlib.patches",  "3.7+", "mpatches.Patch pour légendes personnalisées"),
            ("matplotlib.cm",       "3.7+", "Colormap RdYlGn pour gradient feature importance"),
            ("numpy",               "1.24+","linspace pour bins histogramme et axes learning curve"),
            ("sklearn.metrics",     "1.3+", "r2_score, mean_squared_error, mean_absolute_error"),
            ("json",                "std",  "Sérialisation du rapport d'évaluation complet"),
            ("pathlib",             "std",  "Création répertoire reports/figures/"),
        ]),
        ("ORCHESTRATION", "main.py", [
            ("argparse",  "std",  "CLI : --config, --step (all/generate/clean/train/evaluate/demo)"),
            ("time",      "std",  "time.time() pour mesure durée totale pipeline"),
            ("yaml",      "6.0+", "load_config() : lecture config/config.yaml"),
            ("pathlib",   "std",  "Création des répertoires data/ et reports/ si absents"),
            ("pickle",    "std",  "Rechargement du modèle pour demo_prediction()"),
        ]),
    ]

    for step_title, module, tools in steps:
        heading(doc, step_title, 2, BLEU_CLAIR)
        para(doc, f"Module : {module}", italic=True, color=GRIS_TEXTE)

        tbl = doc.add_table(rows=len(tools) + 1, cols=3)
        tbl.style = "Table Grid"

        for j, h in enumerate(["Outil / Librairie", "Version", "Usage précis dans ce projet"]):
            cell = tbl.rows[0].cells[j]
            cell.text = h
            set_cell_bg(cell, "1A5276")
            cell.paragraphs[0].runs[0].bold = True
            cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            cell.paragraphs[0].runs[0].font.size = Pt(9.5)

        for i, (lib, ver, usage) in enumerate(tools):
            row = tbl.rows[i + 1]
            row.cells[0].text = lib
            row.cells[1].text = ver
            row.cells[2].text = usage
            bg = "EAF2F8" if i % 2 == 0 else "FFFFFF"
            for cell in row.cells:
                set_cell_bg(cell, bg)
                cell.paragraphs[0].runs[0].font.size = Pt(9.5)

        tbl.rows[0].cells[0].width = Cm(4.5)
        tbl.rows[0].cells[1].width = Cm(1.5)
        tbl.rows[0].cells[2].width = Cm(10)
        for row in tbl.rows[1:]:
            row.cells[0].width = Cm(4.5)
            row.cells[1].width = Cm(1.5)
            row.cells[2].width = Cm(10)

        doc.add_paragraph()

    divider(doc)
    page_break(doc)

    # ── SECTION B : VUE CONSOLIDÉE ───────────────────────────────────────────
    heading(doc, "B. Vue Consolidée — Toutes les Librairies", 1, BLEU_TITRE)

    table_2col(doc, [
        ("numpy >= 1.24",          "Calculs numériques, distributions, vectorisation"),
        ("pandas >= 2.0",          "Manipulation de DataFrames, I/O CSV, imputation"),
        ("scikit-learn >= 1.3",    "ML : RandomForest, Ridge, CV, metrics, learning_curve"),
        ("matplotlib >= 3.7",      "Visualisations : scatter, hist, barh, fill_between"),
        ("pyyaml >= 6.0",          "Lecture configuration centralisée (config.yaml)"),
        ("pickle (stdlib)",        "Sérialisation/désérialisation du modèle entraîné"),
        ("json (stdlib)",          "Génération du rapport d'évaluation JSON"),
        ("pathlib (stdlib)",       "Gestion cross-platform des chemins et répertoires"),
        ("argparse (stdlib)",      "Interface CLI (--step, --config, --no-demo)"),
        ("time (stdlib)",          "Mesure de la durée d'exécution du pipeline"),
    ], header=("Librairie", "Rôle"), col_widths=(5, 11))

    divider(doc)

    # ── SECTION C : OUTILS DE DÉVELOPPEMENT ─────────────────────────────────
    heading(doc, "C. Outils de Développement et Documentation", 1, BLEU_TITRE)

    table_2col(doc, [
        ("Git",             "Versioning, branche dédiée claude/billboard-geolocation-db-oRXoT"),
        ("Python 3.11",     "Langage principal — type hints, f-strings, pathlib"),
        ("pip",             "Gestion des dépendances (requirements.txt)"),
        ("YAML",            "Configuration centralisée lisible et modifiable sans code"),
        ("Markdown",        "Documentation : README.md, PRESENTATION.md, PITCH.md"),
        ("python-docx",     "Génération des documents Word (.docx) de ce rapport"),
        ("JSON",            "Format du rapport d'évaluation exportable"),
    ], header=("Outil", "Usage"), col_widths=(4, 12))

    divider(doc)

    # ── SECTION D : ROADMAP OUTILS V2/V3 ─────────────────────────────────────
    heading(doc, "D. Outils Prévus — Roadmap V2 / V3", 1, BLEU_TITRE)

    table_2col(doc, [
        ("xgboost",        "V2 — Gradient Boosting plus précis que RF sur grand dataset"),
        ("optuna",         "V2 — Hyperparameter tuning bayésien automatisé"),
        ("shap",           "V2 — Explicabilité des prédictions individuelles (SHAP values)"),
        ("fastapi",        "V2 — API REST pour exposer le modèle en production"),
        ("streamlit",      "V2 — Dashboard interactif (carte, filtres, score en temps réel)"),
        ("geopandas",      "V2 — Analyse géospatiale avancée (zones, polygones)"),
        ("folium",         "V2 — Carte interactive des panneaux avec scores colorés"),
        ("osmnx",          "V2 — Extraction features réseau routier depuis OpenStreetMap"),
        ("mlflow",         "V2/V3 — Tracking des expériences ML et versioning modèles"),
        ("torch / YOLOv8", "V3 — Détection automatique de panneaux sur images satellite"),
        ("torchvision",    "V3 — CNN scoring qualité visuelle des photos de panneaux"),
        ("Pillow",         "V3 — Traitement des images (resize, format, augmentation)"),
        ("scipy.optimize", "V3 — Optimisation multi-variable pour placement optimal"),
    ], header=("Outil", "Usage prévu"), col_widths=(4, 12))

    doc.add_paragraph()
    divider(doc)
    footer = doc.add_paragraph("Billboard Geolocation Platform — Stack Technique · Prototype V1 · 2024")
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.runs[0].font.size = Pt(8)
    footer.runs[0].font.color.rgb = RGBColor(0x99, 0x99, 0x99)

    path = Path("docs/03_OUTILS_TECHNIQUES.docx")
    doc.save(str(path))
    print(f"[OK] {path}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Génération des documents Word...")
    build_doc1()
    build_doc2()
    build_doc3()
    print("\nDocuments générés dans docs/")
    for f in sorted(Path("docs").glob("*.docx")):
        size_kb = f.stat().st_size // 1024
        print(f"  {f.name:<40} {size_kb} Ko")
