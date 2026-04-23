"""
Génère le document Word : 04_OUTILS_EXPLORATION_DATASET.docx
"""

from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────────────
# PALETTE
# ─────────────────────────────────────────────────────────────────────────────
BLEU_TITRE  = RGBColor(0x1A, 0x52, 0x76)
BLEU_CLAIR  = RGBColor(0x21, 0x8D, 0xBB)
VERT        = RGBColor(0x1E, 0x8B, 0x4C)
ROUGE       = RGBColor(0xC0, 0x39, 0x2B)
ORANGE      = RGBColor(0xCA, 0x6F, 0x1E)
GRIS_TEXTE  = RGBColor(0x2C, 0x3E, 0x50)
VIOLET      = RGBColor(0x6C, 0x3F, 0x83)
BLANC       = RGBColor(0xFF, 0xFF, 0xFF)

# Hex strings pour shading XML
HEX = {
    "bleu_titre":   "1A5276",
    "bleu_header":  "2980B9",
    "bleu_pale":    "D6EAF8",
    "vert_header":  "1E8B4C",
    "vert_pale":    "D5F5E3",
    "orange_header":"CA6F1E",
    "orange_pale":  "FDEBD0",
    "violet_header":"6C3F83",
    "violet_pale":  "E8DAEF",
    "gris_header":  "566573",
    "gris_pale":    "F2F3F4",
    "jaune_pale":   "FEF9E7",
    "blanc":        "FFFFFF",
    "rouge_header": "C0392B",
    "rouge_pale":   "FADBD8",
}

PRIO_COLORS = {
    "Très haute": ("1E8B4C", BLANC),
    "Haute":      ("2980B9", BLANC),
    "Moyenne":    ("CA6F1E", BLANC),
}


# ─────────────────────────────────────────────────────────────────────────────
# UTILITAIRES
# ─────────────────────────────────────────────────────────────────────────────

def set_cell_bg(cell, hex_color: str):
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd  = OxmlElement("w:shd")
    shd.set(qn("w:val"),   "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"),  hex_color)
    tcPr.append(shd)


def cell_text(cell, text, bold=False, italic=False,
              color=None, size=9.5, align=None):
    p = cell.paragraphs[0]
    p.clear()
    if align:
        p.alignment = align
    run = p.add_run(text)
    run.bold   = bold
    run.italic = italic
    run.font.size = Pt(size)
    if color:
        run.font.color.rgb = color


def header_row(tbl, headers, bg_hex, text_color=None, sizes=None):
    row = tbl.rows[0]
    for j, h in enumerate(headers):
        c = row.cells[j]
        set_cell_bg(c, bg_hex)
        sz = sizes[j] if sizes else 9.5
        cell_text(c, h, bold=True, size=sz,
                  color=text_color or BLANC,
                  align=WD_ALIGN_PARAGRAPH.CENTER)


def set_col_widths(tbl, widths_cm):
    for row in tbl.rows:
        for j, w in enumerate(widths_cm):
            if j < len(row.cells):
                row.cells[j].width = Cm(w)


def add_heading(doc, text, level=1, color=None, space_before=12):
    h = doc.add_heading(text, level=level)
    h.paragraph_format.space_before = Pt(space_before)
    h.paragraph_format.space_after  = Pt(5)
    if color:
        for run in h.runs:
            run.font.color.rgb = color
    return h


def add_para(doc, text, bold=False, italic=False, color=None,
             size=10.5, indent=0, align=None, space_after=4):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    if indent:
        p.paragraph_format.left_indent = Cm(indent)
    if align:
        p.alignment = align
    r = p.add_run(text)
    r.bold = bold; r.italic = italic; r.font.size = Pt(size)
    if color:
        r.font.color.rgb = color
    return p


def add_bullet(doc, text, color=None, size=10, indent=0.5):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.left_indent = Cm(indent)
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run(text)
    r.font.size = Pt(size)
    if color:
        r.font.color.rgb = color


def divider(doc):
    p = doc.add_paragraph("─" * 90)
    p.runs[0].font.size = Pt(6)
    p.runs[0].font.color.rgb = RGBColor(0xCC, 0xCC, 0xCC)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after  = Pt(4)


def set_margins(doc):
    for s in doc.sections:
        s.top_margin    = Cm(1.8)
        s.bottom_margin = Cm(1.8)
        s.left_margin   = Cm(2.0)
        s.right_margin  = Cm(2.0)


# ─────────────────────────────────────────────────────────────────────────────
# DOCUMENT
# ─────────────────────────────────────────────────────────────────────────────

def build():
    doc = Document()
    set_margins(doc)

    # ── PAGE DE TITRE ────────────────────────────────────────────────────────
    t = doc.add_heading("Outils d'Exploration du Dataset", 0)
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for r in t.runs:
        r.font.color.rgb = BLEU_TITRE
        r.font.size = Pt(20)

    s1 = doc.add_paragraph("Billboard Geolocation Platform — Cotonou, Bénin")
    s1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    s1.runs[0].bold = True
    s1.runs[0].font.size = Pt(12)
    s1.runs[0].font.color.rgb = BLEU_CLAIR

    s2 = doc.add_paragraph(
        "Tableau récapitulatif · Familles de variables · Roadmap d'utilisation"
    )
    s2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    s2.runs[0].font.size = Pt(10)
    s2.runs[0].font.color.rgb = GRIS_TEXTE

    doc.add_paragraph()
    divider(doc)

    # ═════════════════════════════════════════════════════════════════════════
    # SECTION 1 — TABLEAU RÉCAPITULATIF PRINCIPAL
    # ═════════════════════════════════════════════════════════════════════════
    add_heading(doc, "1. Tableau Récapitulatif — Outils d'Exploration", 1, BLEU_TITRE)
    add_para(doc,
             "Pour chaque outil : rôle principal, type de données récupérées, "
             "variables utilisables dans le modèle ML, utilité concrète et priorité d'intégration.",
             italic=True, color=GRIS_TEXTE)
    doc.add_paragraph()

    # Colonnes : Outil | Rôle | Type de données | Variables produites | Utilité concrète | Priorité
    cols = [
        "Outil",
        "Rôle principal",
        "Type de données récupérées / manipulées",
        "Variables ou familles de variables",
        "Utilité concrète pour le projet",
        "Priorité",
    ]
    widths = [3.0, 3.2, 3.8, 3.8, 3.8, 1.6]

    rows_data = [
        (
            "OpenStreetMap\n(OSM)",
            "Source de données urbaines ouverte de base",
            "Réseau routier, bâtiments, points d'intérêt, lieux urbains, équipements",
            "Hiérarchie routière, proximité routes majeures, marchés / commerces / écoles / hôpitaux, densité fonctionnelle, accessibilité locale",
            "Sert de fondation au dataset spatial",
            "Très haute",
        ),
        (
            "Overpass Turbo",
            "Exploration et extraction rapide de données OSM",
            "Objets OSM filtrés par catégorie ou zone",
            "Routes principales, intersections, marchés, arrêts, commerces, zones d'activité, équipements urbains",
            "Tester rapidement ce qui existe réellement à Cotonou avant automatisation",
            "Très haute",
        ),
        (
            "QGIS",
            "Visualisation, nettoyage et contrôle spatial",
            "Couches vectorielles et raster",
            "Variables indirectes après vérification spatiale, nettoyage couches, découpage zone d'étude, harmonisation géographique",
            "Préparer des couches fiables avant modélisation",
            "Très haute",
        ),
        (
            "GeoPandas",
            "Construction de la table analytique spatiale",
            "Tables géographiques, points, lignes, polygones",
            "Distances, densités locales, jointures spatiales, voisinages, agrégations par zone, exposition contextuelle",
            "Outil central pour transformer les couches en dataset ML exploitable",
            "Très haute",
        ),
        (
            "OSMnx",
            "Analyse réseau à partir d'OSM",
            "Graphe routier, nœuds, segments, structure du réseau",
            "Centralité, connectivité, importance des axes, proximité nœuds stratégiques, structure trafic potentiel",
            "Modéliser la visibilité liée au réseau routier",
            "Très haute",
        ),
        (
            "NetworkX",
            "Calcul d'indicateurs de graphe",
            "Graphes issus du réseau routier",
            "Centralité, degré, accessibilité structurelle, importance relative des nœuds / segments",
            "Complète OSMnx pour produire les variables réseau",
            "Haute",
        ),
        (
            "WorldPop",
            "Ajouter la dimension démographique",
            "Raster de population",
            "Densité de population, exposition humaine potentielle, pression démographique autour d'un site",
            "Proxy de fréquentation / audience potentielle",
            "Très haute",
        ),
        (
            "GHSL",
            "Ajouter la dimension urbaine et bâtie",
            "Raster de densité bâtie / urbanisation",
            "Densité bâtie, intensité urbaine, structure du tissu urbain, niveau d'urbanisation, compacité spatiale",
            "Qualifier l'environnement physique d'un emplacement",
            "Très haute",
        ),
        (
            "Sentinel-2 /\nCopernicus",
            "Enrichissement satellitaire",
            "Images satellites",
            "Occupation du sol, zones ouvertes ou denses, texture urbaine, contexte visuel large",
            "Enrichissement V2 — pas obligatoire pour démarrer",
            "Moyenne",
        ),
        (
            "Google Earth\nEngine",
            "Traitement géospatial / raster avancé",
            "Imagerie et rasters à grande échelle",
            "Indices spatiaux, enrichissements raster, variables environnementales, occupation du sol dérivée",
            "Utile si raster poussé — pas indispensable au début",
            "Moyenne",
        ),
        (
            "Rasterio",
            "Lecture et traitement de rasters dans Python",
            "Population, bâti, imagerie, couches continues",
            "Extraction de valeurs raster autour des sites, statistiques locales, agrégats spatiaux",
            "Complète GeoPandas pour intégrer les données raster au dataset final",
            "Haute",
        ),
        (
            "Folium",
            "Contrôle visuel interactif",
            "Cartes interactives web",
            "Pas de variables nouvelles — validation spatiale des résultats, inspection des scores",
            "Vérifier si les emplacements et scores font sens visuellement",
            "Moyenne",
        ),
    ]

    tbl = doc.add_table(rows=len(rows_data) + 1, cols=len(cols))
    tbl.style = "Table Grid"
    tbl.alignment = WD_TABLE_ALIGNMENT.LEFT

    # Header
    header_row(tbl, cols, HEX["bleu_titre"], sizes=[9, 9, 9, 9, 9, 9])

    # Data rows
    for i, row_vals in enumerate(rows_data):
        row = tbl.rows[i + 1]
        prio = row_vals[-1]
        bg_main = HEX["bleu_pale"] if i % 2 == 0 else HEX["blanc"]

        for j, val in enumerate(row_vals):
            c = row.cells[j]
            if j == len(cols) - 1:  # colonne Priorité
                prio_bg, prio_fg = PRIO_COLORS.get(prio, ("566573", BLANC))
                set_cell_bg(c, prio_bg)
                cell_text(c, val, bold=True, color=prio_fg, size=8.5,
                          align=WD_ALIGN_PARAGRAPH.CENTER)
            else:
                set_cell_bg(c, bg_main)
                # Outil en gras
                cell_text(c, val, bold=(j == 0), size=9 if j == 0 else 9)

    set_col_widths(tbl, widths)
    doc.add_paragraph()
    divider(doc)

    # ═════════════════════════════════════════════════════════════════════════
    # SECTION 2 — CE QUE CHAQUE FAMILLE APPORTE
    # ═════════════════════════════════════════════════════════════════════════
    add_heading(doc, "2. Ce que chaque Famille d'Outils vous Apporte", 1, BLEU_TITRE)

    familles = [
        (
            "Réseau routier et structure de circulation",
            "OSM, Overpass Turbo, OSMnx, NetworkX",
            "Variables de connectivité, centralité, importance des axes, "
            "proximité des carrefours, accessibilité",
            "bleu_header", "bleu_pale",
        ),
        (
            "Contexte urbain et points d'intérêt",
            "OSM, Overpass Turbo, QGIS, GeoPandas",
            "Densité de commerces, proximité de marchés, concentration d'équipements, "
            "attractivité fonctionnelle",
            "vert_header", "vert_pale",
        ),
        (
            "Exposition humaine",
            "WorldPop, GeoPandas, Rasterio",
            "Densité de population, présence humaine potentielle, "
            "intensité de fréquentation indirecte",
            "orange_header", "orange_pale",
        ),
        (
            "Morphologie et densité urbaine",
            "GHSL, Sentinel-2, Rasterio, QGIS",
            "Densité bâtie, urbanisation, compacité, ouverture relative de l'espace",
            "violet_header", "violet_pale",
        ),
        (
            "Assemblage du dataset final",
            "GeoPandas, QGIS, Rasterio",
            "Jointures spatiales, calcul de distances, agrégations, "
            "enrichissement des emplacements candidats",
            "gris_header", "gris_pale",
        ),
        (
            "Contrôle qualité et lecture cartographique",
            "QGIS, Folium",
            "Vérification visuelle, validation géographique, repérage des anomalies",
            "rouge_header", "rouge_pale",
        ),
    ]

    tbl2 = doc.add_table(rows=len(familles) + 1, cols=3)
    tbl2.style = "Table Grid"

    header_row(tbl2,
               ["Famille d'outils", "Outils principaux", "Ce qu'elle vous apporte"],
               HEX["bleu_titre"])

    for i, (famille, outils, apport, bg_h, bg_l) in enumerate(familles):
        row = tbl2.rows[i + 1]
        set_cell_bg(row.cells[0], bg_h)
        cell_text(row.cells[0], famille, bold=True, color=BLANC, size=9.5)

        set_cell_bg(row.cells[1], bg_l)
        cell_text(row.cells[1], outils, size=9.5)

        set_cell_bg(row.cells[2], bg_l)
        cell_text(row.cells[2], apport, size=9.5)

    set_col_widths(tbl2, [4.5, 4.0, 10.5])
    doc.add_paragraph()
    divider(doc)

    # ═════════════════════════════════════════════════════════════════════════
    # SECTION 3 — FAMILLES DE VARIABLES PRODUITES
    # ═════════════════════════════════════════════════════════════════════════
    add_heading(doc, "3. Familles de Variables Construites pour le Modèle ML", 1, BLEU_TITRE)
    add_para(doc,
             "Variables raisonnablement constructibles à partir des outils ci-dessus.",
             italic=True, color=GRIS_TEXTE)
    doc.add_paragraph()

    variables = [
        (
            "Accessibilité routière",
            "Importance des routes, proximité des axes majeurs, carrefours, connectivité",
            "OSM, OSMnx, NetworkX, GeoPandas",
            "bleu_pale", "bleu_header",
        ),
        (
            "Exposition potentielle",
            "Présence humaine et intensité d'occupation des environs",
            "WorldPop, GHSL, Rasterio",
            "vert_pale", "vert_header",
        ),
        (
            "Attractivité urbaine",
            "Proximité zones commerciales, marchés, services, équipements",
            "OSM, Overpass Turbo, GeoPandas",
            "orange_pale", "orange_header",
        ),
        (
            "Centralité spatiale",
            "Position stratégique dans la ville, rôle dans le réseau",
            "OSMnx, NetworkX",
            "violet_pale", "violet_header",
        ),
        (
            "Contexte morphologique",
            "Densité du bâti, structure du tissu urbain, zones ouvertes ou compactes",
            "GHSL, Sentinel-2, QGIS",
            "gris_pale", "gris_header",
        ),
        (
            "Densité fonctionnelle",
            "Concentration d'activités et de points d'intérêt autour des sites",
            "OSM, Overpass Turbo, GeoPandas",
            "bleu_pale", "bleu_header",
        ),
        (
            "Variables de voisinage",
            "Ce qu'il y a dans un rayon donné autour d'un site",
            "GeoPandas, Rasterio, QGIS",
            "vert_pale", "vert_header",
        ),
        (
            "Variables de contrôle spatial",
            "Appartenance à une zone, distance à un pôle majeur, structure du quartier",
            "QGIS, GeoPandas, OSM",
            "orange_pale", "orange_header",
        ),
    ]

    tbl3 = doc.add_table(rows=len(variables) + 1, cols=3)
    tbl3.style = "Table Grid"
    header_row(tbl3,
               ["Grande famille de variables", "Exemples de ce qu'elles représentent",
                "Outils les plus utiles"],
               HEX["bleu_titre"])

    for i, (famille, exemples, outils, bg_l, bg_h) in enumerate(variables):
        row = tbl3.rows[i + 1]
        set_cell_bg(row.cells[0], bg_h)
        cell_text(row.cells[0], famille, bold=True, color=BLANC, size=9.5)

        set_cell_bg(row.cells[1], bg_l)
        cell_text(row.cells[1], exemples, size=9.5)

        set_cell_bg(row.cells[2], bg_l)
        cell_text(row.cells[2], outils, italic=True, size=9.5)

    set_col_widths(tbl3, [4.2, 8.3, 6.5])
    doc.add_paragraph()
    divider(doc)

    # ═════════════════════════════════════════════════════════════════════════
    # SECTION 4 — LECTURE PRATIQUE / NIVEAUX DE PRIORITÉ
    # ═════════════════════════════════════════════════════════════════════════
    add_heading(doc, "4. Lecture Pratique — Quels Outils Utiliser en Premier ?", 1, BLEU_TITRE)

    niveaux = [
        (
            "Noyau immédiat",
            "OSM + Overpass Turbo + QGIS + GeoPandas + OSMnx + WorldPop + GHSL",
            "Suffisant pour construire une vraie base de données de recherche",
            "1E8B4C",  # vert
        ),
        (
            "Très utile ensuite",
            "NetworkX + Rasterio + Folium",
            "Enrichit l'analyse, améliore le contrôle et la qualité du dataset",
            "2980B9",  # bleu
        ),
        (
            "Optionnel au démarrage",
            "Sentinel-2 + Google Earth Engine",
            "Utile pour aller plus loin sur le raster et l'imagerie (V2/V3)",
            "CA6F1E",  # orange
        ),
    ]

    tbl4 = doc.add_table(rows=len(niveaux) + 1, cols=3)
    tbl4.style = "Table Grid"
    header_row(tbl4, ["Niveau", "Outils", "Pourquoi"], HEX["bleu_titre"])

    for i, (niveau, outils, pourquoi, bg) in enumerate(niveaux):
        row = tbl4.rows[i + 1]
        set_cell_bg(row.cells[0], bg)
        cell_text(row.cells[0], niveau, bold=True, color=BLANC, size=10,
                  align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell_bg(row.cells[1], HEX["gris_pale"])
        cell_text(row.cells[1], outils, bold=True, size=9.5)
        set_cell_bg(row.cells[2], HEX["blanc"])
        cell_text(row.cells[2], pourquoi, size=9.5)

    set_col_widths(tbl4, [3.2, 8.3, 7.5])
    doc.add_paragraph()
    divider(doc)

    # ═════════════════════════════════════════════════════════════════════════
    # SECTION 5 — RÉSUMÉ + VARIABLES PRODUITES
    # ═════════════════════════════════════════════════════════════════════════
    add_heading(doc, "5. Résumé — Ce que le Noyau Immédiat Permet de Produire", 1, BLEU_TITRE)

    add_para(doc,
             "En démarrant uniquement avec le noyau immédiat (OSM, Overpass Turbo, "
             "QGIS, GeoPandas, OSMnx, WorldPop, GHSL), vous pouvez construire :",
             size=10.5)

    livrables = [
        ("Une base d'emplacements candidats",
         "Liste géoréférencée de sites avec coordonnées GPS précises"),
        ("Variables de réseau routier",
         "Hiérarchie, centralité, connectivité, distance aux axes majeurs"),
        ("Variables de densité humaine",
         "Population dans un rayon de 200m, 500m, 1km autour du panneau"),
        ("Variables de contexte urbain",
         "Densité bâtie, niveau d'urbanisation, compacité du tissu"),
        ("Variables de proximité et densité de POI",
         "Nombre de commerces, marchés, arrêts dans un rayon donné"),
        ("Table analytique finale",
         "Dataset complet utilisable directement dans le pipeline ML V2"),
    ]

    tbl5 = doc.add_table(rows=len(livrables) + 1, cols=2)
    tbl5.style = "Table Grid"
    header_row(tbl5, ["Livrable produit", "Contenu"], HEX["vert_header"])

    for i, (livrable, contenu) in enumerate(livrables):
        row = tbl5.rows[i + 1]
        bg = HEX["vert_pale"] if i % 2 == 0 else HEX["blanc"]
        set_cell_bg(row.cells[0], bg)
        set_cell_bg(row.cells[1], bg)
        cell_text(row.cells[0], f"✓  {livrable}", bold=True,
                  color=VERT, size=10)
        cell_text(row.cells[1], contenu, size=10)

    set_col_widths(tbl5, [6.5, 12.5])

    # ─── NOTE FINALE ─────────────────────────────────────────────────────────
    doc.add_paragraph()
    divider(doc)
    add_heading(doc, "Note sur l'intégration avec le Pipeline Actuel (V1)", 2, BLEU_CLAIR)
    add_para(doc,
             "Le pipeline V1 utilise des données synthétiques générées dans data_generation.py. "
             "En V2, les features issues des outils ci-dessus remplaceront ou enrichiront "
             "directement les colonnes de billboards_raw.csv. "
             "GeoPandas produira la table, feature_engineering.py l'intégrera sans modification "
             "structurelle du pipeline.",
             size=10.5, italic=True, color=GRIS_TEXTE)

    add_bullet(doc, "OSM / Overpass Turbo → traffic_flow_estim, road_type, distance_to_main_road_m",
               color=BLEU_CLAIR)
    add_bullet(doc, "OSMnx / NetworkX → quartier_enc, geo_quadrant, score_accessibilite",
               color=BLEU_CLAIR)
    add_bullet(doc, "WorldPop → pedestrian_density_score (proxy population réel)",
               color=BLEU_CLAIR)
    add_bullet(doc, "GHSL → is_urban_core (nouvelle feature V2), compacite_tissu",
               color=BLEU_CLAIR)
    add_bullet(doc, "GeoPandas → distance_to_beach_km, distance_to_port_km, distance_to_center_km",
               color=BLEU_CLAIR)

    doc.add_paragraph()
    divider(doc)
    foot = doc.add_paragraph(
        "Billboard Geolocation Platform — Outils d'Exploration · V2 Data Roadmap · 2024"
    )
    foot.alignment = WD_ALIGN_PARAGRAPH.CENTER
    foot.runs[0].font.size = Pt(8)
    foot.runs[0].font.color.rgb = RGBColor(0x99, 0x99, 0x99)

    out = Path("docs/04_OUTILS_EXPLORATION_DATASET.docx")
    doc.save(str(out))
    size_kb = out.stat().st_size // 1024
    print(f"[OK] {out}  ({size_kb} Ko)")


if __name__ == "__main__":
    build()
