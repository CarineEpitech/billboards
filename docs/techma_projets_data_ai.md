# Exploration des projets Data & IA — TECHMA Bénin
## Dossier de certification — Coding Academy by Epitech

> **Auteur :** Carine
> **Contexte :** TECHMA Bénin — transformation digitale, CRM, automatisation, API, SaaS PME
> **Date :** 2026-03-18
> **Version :** 1.0 — Document de référence pour choix de projet de certification

---

## Table des matières

- [Introduction](#introduction)
- [Projet 1 — Lead Scoring CRM avec Machine Learning](#projet-1--lead-scoring-crm-avec-machine-learning)
- [Projet 2 — Prédiction du Churn Client (Customer Attrition)](#projet-2--prédiction-du-churn-client)
- [Projet 3 — Chatbot NLP intelligent avec RAG](#projet-3--chatbot-nlp-intelligent-avec-rag)
- [Projet 4 — Pipeline de données unifié multi-sources](#projet-4--pipeline-de-données-unifié-multi-sources)
- [Projet 5 — Analyse NLP des tickets et communications clients](#projet-5--analyse-nlp-des-tickets-et-communications-clients)
- [Projet 6 — Système de recommandation de solutions digitales](#projet-6--système-de-recommandation-de-solutions-digitales)
- [Projet 7 — Prédiction de performance et ROI des projets](#projet-7--prédiction-de-performance-et-roi-des-projets)
- [Projet 8 — Dashboard BI intelligent avec détection d'anomalies](#projet-8--dashboard-bi-intelligent-avec-détection-danomalies)
- [Tableau comparatif final](#tableau-comparatif-final)
- [TOP 2 recommandés](#top-2-recommandés)
- [Combinaisons possibles](#combinaisons-possibles)

---

## Introduction

### Pourquoi TECHMA Bénin est un terrain idéal pour un projet Data & IA

TECHMA opère à l'intersection de plusieurs systèmes riches en données :

```
Zoho CRM / HubSpot     →  données clients, leads, deals, historiques
Make / Zapier          →  logs d'automatisation, workflows, événements
APIs tierces           →  données partenaires, intégrations SaaS
Interactions clients   →  emails, chats, tickets support
Projets digitaux PME   →  livrables, délais, budgets, satisfaction
```

Chaque couche produit des données structurées et non-structurées exploitables
pour des projets Data & IA de niveaux variés. Le contexte africain (marché béninois,
PME locales, adoption digitale en croissance) ajoute une dimension de **recherche
appliquée** particulièrement valorisée dans un jury de certification.

---

## Projet 1 — Lead Scoring CRM avec Machine Learning

### 1. Description du projet

#### Problème métier
TECHMA génère des leads via son site web, des événements, des référencements, et
des campagnes. Tous les leads ne se valent pas : certains vont acheter rapidement,
d'autres jamais. L'équipe commerciale perd du temps sur des leads froids.

**Question clé :** *Quelle est la probabilité qu'un lead donné se convertisse
en client dans les 30/60/90 prochains jours ?*

#### Objectif Data & AI
Construire un **modèle de scoring** qui attribue à chaque lead un score entre
0 et 100 représentant sa probabilité de conversion. Ce score guide les priorités
de l'équipe commerciale.

#### Pourquoi pertinent pour TECHMA
- Directement actionnable : le score peut être injecté dans Zoho CRM via API
- Réduit le temps de prospection à froid
- Améliore le taux de conversion sans augmenter les effectifs
- ROI mesurable et démontrable à un jury

---

### 2. Potentiel Data & IA

#### Types de modèles possibles

| Approche | Modèle | Complexité |
|---|---|---|
| Baseline | Régression logistique | Débutant |
| Intermédiaire | Random Forest, XGBoost | Intermédiaire |
| Avancé | LightGBM + SHAP + calibration | Avancé |
| Séquentiel | RNN/LSTM sur séquences d'interactions | Expert |

#### Complexité globale : **Avancé**

L'aspect le plus complexe n'est pas le modèle mais le **feature engineering temporel** :
calculer des features sur des fenêtres glissantes (7j, 30j, 90j) d'interactions.

#### Extensions possibles
- Score en temps réel via une API REST (FastAPI)
- A/B testing : commerciaux guidés vs non guidés par le score
- Modèle multi-horizon : score à 30j, 60j, 90j séparément
- Intégration automatique dans Zoho via Make/Zapier

---

### 3. Données nécessaires

#### Types de données
```
Leads CRM :
  - lead_id, date_creation, source (web, événement, référence...)
  - secteur d'activité, taille de l'entreprise
  - localisation géographique

Interactions :
  - nombre d'emails échangés
  - délai de réponse moyen (heures)
  - nombre d'appels
  - nombre de rendez-vous
  - pièces jointes envoyées (devis, contrats)

Historique des deals :
  - étape actuelle (qualification, proposition, négociation, clôture)
  - durée dans chaque étape
  - montant estimé du deal
  - won/lost (variable cible)

Données contextuelles :
  - saison (mois, trimestre)
  - nombre de jours depuis le dernier contact
```

#### Données réelles vs simulées
- **Idéal :** données Zoho CRM de TECHMA (avec anonymisation)
- **Alternative :** simuler 500–2000 leads réalistes depuis les patterns connus
- **Dataset public de référence :** Salesforce Lead Scoring Dataset (Kaggle)

#### Difficulté d'accès
- Données TECHMA : moyen (besoin d'export Zoho + RGPD/anonymisation)
- Données simulées : facile (2–4h de génération Python)

---

### 4. Feature Engineering

#### Variables brutes → features ML

| Variable brute | Feature engineered | Transformation |
|---|---|---|
| `date_creation` | `age_lead_jours` | Aujourd'hui - date_creation |
| `date_dernier_contact` | `jours_sans_contact` | Aujourd'hui - date_dernier_contact |
| Séquence d'emails | `email_response_rate` | Emails répondus / emails envoyés |
| Historique étapes | `velocity_score` | Vitesse de progression dans le funnel |
| Montant estimé | `deal_size_log` | log(1 + montant) |
| Source du lead | `source_enc` | Label encoding |
| Interactions 7j | `nb_interactions_7d` | Count sur fenêtre glissante |
| Interactions 30j | `nb_interactions_30d` | Count sur fenêtre glissante |
| Ratio 7j/30j | `recency_ratio` | interactions_7d / interactions_30d |

#### Features avancées
```python
# Vitesse de progression dans le funnel (feature clé)
df["velocity"] = df["etapes_franchies"] / df["age_lead_jours"].clip(lower=1)

# Engagement decay : l'interaction récente compte plus que l'ancienne
df["weighted_engagement"] = (
    df["nb_interactions_7d"] * 3
    + df["nb_interactions_30d"] * 1
    + df["nb_interactions_90d"] * 0.3
)

# Score de profil (features entreprise)
df["profile_score"] = (
    (df["taille_entreprise"] / 10) * 0.4
    + (df["secteur_prioritaire"] == True).astype(int) * 0.6
)
```

---

### 5. Modèles & Méthodes

#### Pipeline complet

```
1. EDA
   → Distribution des taux de conversion par source, secteur, taille
   → Analyse temporelle : quand les leads convertissent-ils ?
   → Corrélations entre features et conversion

2. Preprocessing
   → Imputation (médiane pour numériques, "Inconnu" pour catégoriels)
   → Encodage (OneHot pour source, Label pour secteur)
   → Gestion du déséquilibre : SMOTE ou class_weight

3. Modèles à tester
   → Baseline : régression logistique (interprétable)
   → Intermédiaire : Random Forest (feature_importances_)
   → Avancé : XGBoost/LightGBM + Optuna (hyperparameter tuning)
   → Calibration : CalibratedClassifierCV (pour que le score = vraie proba)

4. Évaluation
   → ROC-AUC (capacité de discrimination)
   → Precision-Recall Curve (si déséquilibre classes)
   → Brier Score (qualité de la calibration)
   → Lift Chart (valeur business du scoring)

5. Interprétabilité
   → SHAP values : pourquoi CE lead a un score de 87/100 ?
   → Feature importance globale
```

#### Métriques d'évaluation

| Métrique | Valeur cible | Pourquoi |
|---|---|---|
| ROC-AUC | ≥ 0.75 | Capacité à classer leads chauds vs froids |
| Precision @top20% | ≥ 60% | 60% des leads à haut score doivent convertir |
| Brier Score | < 0.15 | Qualité de la probabilité calibrée |
| Lift @décile 1 | ≥ 2.5 | Top 10% de leads = 2.5× plus de conversions que random |

---

### 6. Statistiques à utiliser

#### Statistiques descriptives
- Taux de conversion global et par segment (source, secteur, taille)
- Distribution du temps de conversion (médiane, percentiles 25/75)
- Distribution des montants de deals

#### Tests statistiques
- **Chi-² :** la source du lead influence-t-elle significativement la conversion ?
- **Test de Mann-Whitney :** les leads référencés convertissent-ils plus vite que les leads web ?
- **Courbes de survie (Kaplan-Meier) :** quelle est la probabilité qu'un lead convertisse après X jours ?

#### Analyse avancée
- **Modèle de Cox (hazard proportionnel) :** identifier les features qui accélèrent la conversion dans le temps
- **Corrélations de Spearman** entre features continues et taux de conversion
- **Analyse de variance (ANOVA)** : différences de score entre quartiers/secteurs

---

### 7. Stack technique

| Couche | Outil | Usage |
|---|---|---|
| Données | Zoho CRM export (CSV) / Python simulation | Source |
| Traitement | pandas, numpy | Manipulation |
| Feature Eng. | pandas, scipy | Fenêtres glissantes, transformations |
| ML | scikit-learn, XGBoost, LightGBM | Modèles |
| Tuning | Optuna | Hyperparamètres automatiques |
| Interprétabilité | SHAP | Explication des prédictions |
| Déséquilibre | imbalanced-learn (SMOTE) | Resampling |
| API de scoring | FastAPI | Endpoint de prédiction en temps réel |
| Intégration CRM | Zoho API / Make | Injection du score dans CRM |
| Visualisation | matplotlib, seaborn, Plotly | Graphiques |
| Dashboard | Streamlit ou Zoho Analytics | Interface utilisateur |

---

### 8. Deliverables attendus

1. **Modèle entraîné** : `lead_scoring_model.pkl` (XGBoost calibré)
2. **API FastAPI** : endpoint `POST /score` → retourne `{"lead_id": X, "score": 0.87, "top_reasons": [...]}`
3. **Dashboard Streamlit** : vue globale du pipeline de leads avec scores
4. **Rapport SHAP** : quelles features expliquent le score de chaque lead
5. **Notebook Jupyter** : EDA → Feature Eng → Modèles → Évaluation → Déploiement
6. **Documentation technique** : architecture, décisions, métriques

---

### 9. Avantages & Limites

#### Points forts
- ROI immédiat et mesurable pour TECHMA
- Pipeline ML complet = très valorisé en certification
- Interprétabilité SHAP = point de différenciation fort
- Déploiement API = preuve de compétence système

#### Difficultés techniques
- Déséquilibre des classes (typiquement 5–20% de conversion)
- Fenêtres temporelles complexes à calculer correctement
- Calibration du modèle (score ≠ probabilité si non calibré)

#### Risques
- Données TECHMA potentiellement insuffisantes → simulation nécessaire
- Sur-ajustement sur un petit dataset → régularisation et CV obligatoires

---

### 10. Pertinence pour certification

**Score : 9/10**

> Projet complet avec pipeline end-to-end (EDA → ML → API → CRM), valeur métier
> directement démontrable, SHAP pour l'interprétabilité, déploiement FastAPI.
> Couvre : Feature Engineering, ML supervisé, évaluation, déploiement.
> Parfait pour un jury Epitech Data & AI.

---
---

## Projet 2 — Prédiction du Churn Client

### 1. Description du projet

#### Problème métier
TECHMA a des clients en contrat de maintenance/support (CRM managé, automatisation,
intégrations). Certains ne renouvellent pas leur contrat. Les identifier à l'avance
permet d'agir avant qu'il ne soit trop tard.

**Question clé :** *Quels clients risquent de ne pas renouveler leur contrat
dans les 3 prochains mois, et pourquoi ?*

#### Objectif Data & AI
Modèle de classification binaire (churn = oui/non) avec probabilité et explication
des facteurs de risque. Système d'alerte automatique quand le risque dépasse un seuil.

#### Pourquoi pertinent pour TECHMA
- Coût d'acquisition client >> coût de rétention
- Chaque client perdu = perte de revenus récurrents
- Les signaux de désengagement sont détectables dans les données CRM

---

### 2. Potentiel Data & IA

#### Types de modèles

| Approche | Méthode | Complexité |
|---|---|---|
| Classification simple | Logistic Regression, Random Forest | Intermédiaire |
| Analyse de survie | Cox Proportional Hazards, Kaplan-Meier | Avancé |
| Séquentiel | LSTM sur séquences de tickets/interactions | Expert |
| Ensemble | Gradient Boosting + SHAP | Avancé |

#### Complexité globale : **Avancé**

L'analyse de survie est la méthode académiquement la plus solide pour le churn :
elle modélise le **temps jusqu'au churn**, pas juste la probabilité binaire.

#### Extensions
- Segmentation des churners (clustering K-Means) : qui part et pourquoi
- Modèle de valeur client résiduelle (CLV)
- Système d'alerte automatique via Zoho + Make webhook

---

### 3. Données nécessaires

```
Clients actifs/inactifs :
  - client_id, date_début_contrat, date_fin (ou date_churn)
  - type de contrat (CRM, automatisation, intégration...)
  - valeur annuelle du contrat

Engagement :
  - fréquence de connexion au service
  - nombre de tickets support ouverts / résolus
  - délai moyen de résolution des tickets
  - NPS ou satisfaction déclarée

Historique financier :
  - retards de paiement
  - évolutions tarifaires acceptées/refusées
  - upsells acceptés/refusés

Interactions commerciales :
  - fréquence des réunions de suivi
  - dernier contact (jours)
  - réponses aux campagnes de rétention
```

---

### 4. Feature Engineering

#### Features critiques pour le churn

```python
# Tendance d'engagement : le client se désengage-t-il ?
df["engagement_trend"] = df["nb_interactions_last_30d"] - df["nb_interactions_prev_30d"]
# Négatif = signal d'alarme

# Ratio tickets non résolus
df["ticket_unresolved_rate"] = df["nb_tickets_open"] / df["nb_tickets_total"].clip(1)

# Temps depuis dernier contact significatif
df["days_since_meaningful_contact"] = (today - df["last_meeting_date"]).dt.days

# Feature RFM adaptée au churn
df["recency_score"] = 1 / (1 + df["days_since_last_login"])
df["frequency_score"] = np.log1p(df["avg_monthly_logins"])
df["monetary_score"] = df["contrat_value_annuel"] / df["contrat_value_annuel"].max()

# Indicateur de frustration
df["frustration_index"] = (
    df["avg_ticket_resolution_days"] * df["nb_tickets_last_90d"]
)
```

#### Variables cible
- `churn_binary` : 0 = renouvellement, 1 = churn (classification)
- `time_to_churn_days` : jours avant le churn (survie)

---

### 5. Modèles & Méthodes

#### Approche recommandée : double modèle

**Modèle A — Classification :** *"Ce client va-t-il churner ?"*
```
XGBoost / LightGBM
→ Seuil optimal : maximiser F1-score (si déséquilibre)
→ SHAP pour les top 3 facteurs de risque par client
```

**Modèle B — Survie :** *"Dans combien de jours va-t-il churner ?"*
```
lifelines.CoxPHFitter
→ hazard ratios par feature
→ Courbe de survie personnalisée par client
→ Médiane de survie prévisionnelle
```

#### Pipeline d'évaluation
```
Données → Train/Test split temporel (pas aléatoire !)
→ Validation : ROC-AUC, F1, Recall @top20% clients à risque
→ Courbes Kaplan-Meier par segment (type contrat, taille client)
→ SHAP global + SHAP local (waterfall plot par client)
```

> **Important :** Le split doit être **temporel** (entraîner sur les clients
> d'avant une date X, tester sur les clients après X). Un split aléatoire
> introduirait du data leakage.

---

### 6. Statistiques

- **Kaplan-Meier :** courbes de survie par segment de client → quel type de contrat churne le plus vite ?
- **Test log-rank :** les clients CRM churnet-ils significativement différemment des clients automatisation ?
- **Coefficient de corrélation de Spearman :** entre satisfaction (NPS) et probabilité de churn
- **Test exact de Fisher :** les clients avec retard de paiement churnet-ils plus ?
- **Bootstrap :** intervalles de confiance sur les taux de churn par segment

---

### 7. Stack technique

```
pandas, numpy          → manipulation des données
scikit-learn           → preprocessing, classification
XGBoost / LightGBM    → modèle de churn
lifelines              → analyse de survie (CoxPH, Kaplan-Meier)
SHAP                   → interprétabilité
imbalanced-learn       → SMOTE si déséquilibre fort
Plotly / Streamlit     → dashboard de monitoring churn
FastAPI                → API de scoring temps réel
Zoho CRM API           → récupération et mise à jour des données
Make / Webhook         → alerte automatique si score > seuil
```

---

### 8. Deliverables

1. **Rapport d'analyse de survie** : courbes Kaplan-Meier par segment + hazard ratios
2. **Modèle XGBoost exporté** : `churn_model.pkl`
3. **Dashboard Streamlit** : liste des clients à risque avec score + top raisons SHAP
4. **Alerte automatique** : webhook Zoho/Make quand un client dépasse le seuil de risque
5. **Notebook complet** : EDA → survie → classification → SHAP → alerte

---

### 9. Avantages & Limites

#### Points forts
- Analyse de survie = méthode rare et valorisée en certification
- Application directe : chaque client dans le dashboard est un cas concret
- Double approche (quand + si churn) = projet ambitieux

#### Difficultés
- Besoin de données longitudinales (minimum 12–18 mois d'historique)
- Si TECHMA est jeune, peu d'exemples de churn → simulation nécessaire
- Interprétation des hazard ratios nécessite des bases en statistiques

#### Risques
- Classe très déséquilibrée si peu de churns historiques
- Confusion entre censure (fin d'observation) et churn réel → erreur classique en survie

---

### 10. Pertinence certification

**Score : 8.5/10**

> Analyse de survie + ML supervisé + SHAP + intégration CRM. Démontre une
> maîtrise des statistiques avancées rarement vues en certification junior.
> Légèrement moins fort que le lead scoring sur le volet "déploiement".

---
---

## Projet 3 — Chatbot NLP intelligent avec RAG

### 1. Description du projet

#### Problème métier
TECHMA reçoit des questions répétitives de ses clients PME : "Comment configurer
tel workflow ?", "Quelle est la différence entre Zoho et HubSpot ?", "Comment
intégrer Make avec notre système ?". Répondre manuellement est chronophage.

**Question clé :** *Comment automatiser intelligemment le support client
tout en maintenant la qualité des réponses ?*

#### Objectif Data & AI
Construire un **chatbot RAG** (Retrieval-Augmented Generation) capable de :
1. Comprendre les questions en langage naturel (français/anglais)
2. Retrouver les informations pertinentes dans la documentation TECHMA
3. Générer des réponses précises et contextuelles
4. Escalader les cas complexes vers un humain

#### Pourquoi pertinent pour TECHMA
- Support 24/7 sans coût additionnel
- Cohérence des réponses
- Scalable avec la croissance client
- Intégrable dans Zoho Desk ou WhatsApp Business

---

### 2. Potentiel Data & IA

#### Architecture RAG

```
Question utilisateur
      ↓
Embedding (sentence-transformers)
      ↓
Recherche vectorielle (FAISS / ChromaDB)
      ↓
Top-K documents pertinents récupérés
      ↓
Prompt enrichi → LLM (Claude API / Mistral / Llama3)
      ↓
Réponse générée + sources citées
```

#### Modèles possibles

| Composant | Option simple | Option avancée |
|---|---|---|
| Embedding | `all-MiniLM-L6-v2` | `text-embedding-3-small` (OpenAI) |
| Vector DB | FAISS (local) | ChromaDB, Pinecone |
| LLM | Mistral 7B local | Claude API, GPT-4 |
| Reranking | BM25 | Cohere Rerank |
| Interface | Streamlit | WhatsApp API + FastAPI |

#### Complexité : **Avancé** (architecture système complète)

#### Extensions
- Intégration Zoho Desk (tickets auto-résolus)
- Mémoire conversationnelle (LangChain Memory)
- Évaluation automatique des réponses (RAGAs framework)
- Fine-tuning sur les FAQ TECHMA (si données suffisantes)

---

### 3. Données nécessaires

```
Documentation TECHMA :
  - FAQs existantes (Word, PDF, Notion...)
  - Guides utilisateurs Zoho/HubSpot/Make
  - Documentation des intégrations API
  - Historique des tickets résolus (questions + réponses)

Données externes libres :
  - Documentation officielle Zoho (public)
  - Documentation Make/Zapier (public)
  - Articles de blog TECHMA

Données de test :
  - 50–100 questions-réponses de référence pour l'évaluation
```

#### Difficulté d'accès : **Faible à Moyen**
La documentation est disponible. Le vrai travail est le **preprocessing** :
chunking intelligent des documents, nettoyage, structuration.

---

### 4. Feature Engineering (pour un RAG, c'est le preprocessing)

#### Stratégie de chunking

```python
# Chunking sémantique (pas juste par taille)
# Un chunk = une idée complète, pas une coupure arbitraire

CHUNK_SIZE = 512        # tokens
CHUNK_OVERLAP = 50      # chevauchement pour ne pas perdre le contexte aux jonctions

# Méta-données par chunk (cruciales pour la recherche)
chunk_metadata = {
    "source": "FAQ_Zoho_CRM.pdf",
    "section": "Configuration des pipelines",
    "page": 12,
    "date_maj": "2026-01-15",
    "langue": "fr",
    "type": "procedure"  # vs "concept" vs "troubleshooting"
}
```

#### Features de qualité du retrieval

```python
# Score de pertinence cosinus entre question et chunk
cosine_similarity(query_embedding, chunk_embedding)

# BM25 score (terme fréquence inverse)
bm25_score(query_tokens, chunk_tokens)

# Score hybride
final_score = 0.7 * cosine_score + 0.3 * bm25_score
```

---

### 5. Modèles & Méthodes

#### Pipeline RAG complet

```python
# 1. Indexation (une seule fois)
documents = load_and_split_documents("docs/")
embeddings = embed_documents(documents)  # sentence-transformers
vector_db = FAISS.from_documents(documents, embeddings)

# 2. Retrieval (à chaque question)
def retrieve(question: str, k: int = 5):
    query_embedding = embed_query(question)
    return vector_db.similarity_search(query_embedding, k=k)

# 3. Génération
def generate_answer(question: str, context_chunks: list) -> str:
    prompt = f"""
    Contexte :
    {chr(10).join([c.page_content for c in context_chunks])}

    Question : {question}

    Réponds en français de façon précise et concise. Si tu ne sais pas, dis-le.
    """
    return llm.invoke(prompt)
```

#### Évaluation avec RAGAs

```python
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision

# Mesure si la réponse est fidèle aux sources
scores = evaluate(
    dataset=test_qa_pairs,
    metrics=[faithfulness, answer_relevancy, context_precision]
)
```

| Métrique RAGAs | Valeur cible | Signification |
|---|---|---|
| Faithfulness | ≥ 0.85 | La réponse est fidèle aux sources |
| Answer Relevancy | ≥ 0.80 | La réponse répond à la question |
| Context Precision | ≥ 0.75 | Les bons chunks sont retrouvés |

---

### 6. Statistiques

- **Distribution des scores de similarité cosinus** → identifier les questions sans bonne réponse
- **Analyse des échecs** : quelles catégories de questions ont des scores < 0.5 ?
- **Courbe précision-rappel du retrieval** → optimiser le k
- **Kappa de Cohen** : accord inter-annotateurs sur la qualité des réponses (évaluation humaine)
- **Test t de Student** : RAG vs réponse directe LLM → lequel est plus précis ?

---

### 7. Stack technique

```
LangChain                → orchestration RAG
sentence-transformers    → embeddings locaux gratuits
FAISS                    → base vectorielle locale
Mistral 7B (via Ollama)  → LLM gratuit en local
  OU
Claude API / GPT-4       → LLM cloud (plus performant)
RAGAs                    → évaluation automatique
FastAPI                  → API backend du chatbot
Streamlit                → interface de démonstration
python-docx, pypdf       → parsing des documents
tiktoken                 → comptage de tokens
```

---

### 8. Deliverables

1. **Base vectorielle indexée** : `techma_knowledge_base/` (FAISS index)
2. **API FastAPI** : `POST /chat` → retourne réponse + sources
3. **Interface Streamlit** : chatbot démonstrable en live
4. **Rapport d'évaluation RAGAs** : scores sur 50 questions de test
5. **Notebook** : indexation → RAG → évaluation → exemples
6. **Guide d'extension** : comment ajouter des nouveaux documents

---

### 9. Avantages & Limites

#### Points forts
- Architecture RAG = tech 2024–2025 très valorisée
- Démo très impressionnante lors d'une soutenance (chatbot en live)
- Extensible : WhatsApp, Zoho Desk, Slack...
- Pas besoin de beaucoup de données labellisées

#### Difficultés
- Chunking de qualité = 50% du travail
- Hallucinations du LLM : le modèle peut inventer des réponses
- Évaluation objective difficile (RAGAs nécessite des données de référence)

#### Risques
- LLM cloud coûteux à grande échelle → Mistral local comme solution
- Latence si LLM local sur machine peu puissante

---

### 10. Pertinence certification

**Score : 9.5/10**

> Architecture la plus moderne et la plus impressionnante. RAG + LLM + évaluation
> automatique + déploiement API. Démontre une maîtrise du NLP avancé et de l'IA
> générative. Effet "wow" garanti en soutenance. **Projet le plus fort sur le plan
> de l'impact visuel.**

---
---

## Projet 4 — Pipeline de données unifié multi-sources

### 1. Description du projet

#### Problème métier
TECHMA travaille avec des dizaines de clients, chacun ayant ses propres outils
(Zoho, HubSpot, Make, APIs custom, Google Sheets, etc.). Les données sont **silotées** :
impossible d'avoir une vue unifiée sans assembler manuellement des exports.

**Question clé :** *Comment centraliser automatiquement toutes les données
de TECHMA dans un entrepôt cohérent, prêt pour l'analyse ?*

#### Objectif Data & AI
Concevoir et implémenter un **pipeline ELT/ETL automatisé** :
- Extract : collecter depuis Zoho API, HubSpot API, Make webhooks, Google Sheets
- Load : stocker dans une base unifiée (PostgreSQL ou DuckDB)
- Transform : nettoyer, dédoublonner, calculer des KPIs
- Orchestration : automatiser via Airflow ou Prefect

#### Pourquoi pertinent pour TECHMA
- Fondation technique pour TOUS les autres projets Data
- Démontre la maîtrise des architectures data modernes
- Valeur opérationnelle immédiate : un seul endroit pour voir toutes les données

---

### 2. Potentiel Data & IA

#### Types d'IA dans ce projet

| Couche | Technique | Usage |
|---|---|---|
| Qualité données | Isolation Forest | Détecter les anomalies dans le pipeline |
| Déduplication | Record Linkage / fuzzy matching | Fusionner les doublons cross-sources |
| Classification auto | NLP zero-shot | Classer les tickets sans labels |
| Monitoring | ADWIN (drift detection) | Détecter si les données changent |

#### Complexité : **Avancé** (ingénierie data + ML léger)

Ce projet est moins centré sur le ML et plus sur **l'architecture data**,
ce qui le rend complémentaire des projets 1, 2, 3.

---

### 3. Données nécessaires

```
Sources à connecter :
  - Zoho CRM API (OAuth 2.0) → leads, contacts, deals, activités
  - HubSpot API → contacts, pipelines, emails marketing
  - Make/Zapier logs → exécutions de workflows, erreurs
  - Google Sheets API → rapports manuels, imports clients
  - Fichiers plats (CSV/Excel) → données historiques offline

Données de monitoring :
  - Logs d'exécution du pipeline
  - Métriques de qualité par source (% nulls, % doublons)
  - Temps d'exécution par étape
```

---

### 4. Feature Engineering (pour les KPIs unifiés)

```python
# KPIs calculés dans la couche Transform

# 1. Taux de conversion unifié (toutes sources leads)
kpi["global_conversion_rate"] = won_deals / total_leads

# 2. Temps moyen du cycle de vente
kpi["avg_sales_cycle_days"] = mean(deal_close_date - deal_create_date)

# 3. Score de santé du pipeline de données
kpi["data_quality_score"] = (
    (1 - null_rate) * 0.4
    + (1 - duplicate_rate) * 0.3
    + freshness_score * 0.3
)

# 4. Revenu récurrent mensuel (MRR)
kpi["mrr"] = sum(contrats_actifs_valeur_annuelle) / 12
```

---

### 5. Modèles & Méthodes

#### Architecture du pipeline

```
[Zoho API]  [HubSpot API]  [Make webhooks]  [Google Sheets]
     ↓            ↓               ↓                ↓
  [Extractors Python — requests, gspread, hubspot-api-client]
                         ↓
               [Raw Layer — DuckDB / PostgreSQL]
               (données brutes, sans transformation)
                         ↓
               [Staging Layer — dbt ou pandas]
               (nettoyage, typage, dédoublonnage)
                         ↓
               [Mart Layer — vues agrégées]
               (KPIs, métriques, features ML-ready)
                         ↓
            [Orchestration — Airflow ou Prefect]
            (planification, retry, alertes d'échec)
                         ↓
            [Dashboard — Metabase / Streamlit]
```

#### Détection d'anomalies dans le pipeline

```python
from sklearn.ensemble import IsolationForest

# Détecter les jours où le volume de données est anormal
model = IsolationForest(contamination=0.05)
anomalies = model.fit_predict(daily_record_counts.reshape(-1, 1))
# -1 = anomalie (jour avec trop peu ou trop de données → problème pipeline)
```

---

### 6. Statistiques

- **Métriques de qualité des données :** % nulls, % doublons, fraîcheur (lag)
- **Contrôle statistique de processus (SPC)** : alerter si volume de données sort de ±2σ
- **Test de Kolmogorov-Smirnov** : les distributions changent-elles entre semaines ?
- **Analyse de latence** : distribution des temps de réponse des APIs
- **Corrélation temporelle** : auto-corrélation des KPIs pour détecter les patterns

---

### 7. Stack technique

```
Python                       → orchestration générale
requests / httpx             → appels API REST
gspread                      → Google Sheets API
hubspot-api-client           → HubSpot API
DuckDB                       → entrepôt local léger et puissant
  OU
PostgreSQL                   → entrepôt production
dbt (data build tool)        → transformations SQL versionnées
Apache Airflow               → orchestration et planification
  OU
Prefect                      → orchestration Python-native (plus simple)
Great Expectations           → tests de qualité des données
Metabase / Superset          → BI open source
Docker                       → conteneurisation du pipeline
```

---

### 8. Deliverables

1. **Code source du pipeline** : extractors, transformers, loaders
2. **DAG Airflow** : pipeline orchestré et planifié
3. **Schéma de base de données** : documentation du modèle de données unifié
4. **Tests de qualité** : Great Expectations suite sur chaque source
5. **Dashboard Metabase** : KPIs unifiés en temps réel
6. **Documentation d'architecture** : diagramme, décisions techniques, runbook

---

### 9. Avantages & Limites

#### Points forts
- Fondation réutilisable pour tous les autres projets
- Montre une maîtrise de l'ingénierie data (data engineering)
- Très concret : le pipeline tourne en production

#### Difficultés
- Gestion des erreurs API (rate limiting, tokens expirés)
- Idempotence : relancer le pipeline sans dupliquer les données
- dbt nécessite une courbe d'apprentissage

#### Risques
- Accès API TECHMA nécessaire → dépend des autorisations
- Maintenir le pipeline à jour si les APIs changent

---

### 10. Pertinence certification

**Score : 7.5/10**

> Moins "IA" que les autres mais démontre une vraie maîtrise de l'ingénierie
> data. Idéal en complément d'un projet ML. Seul, peut paraître moins ambitieux
> sur l'aspect "Intelligence Artificielle" pour un jury Epitech.

---
---

## Projet 5 — Analyse NLP des tickets et communications clients

### 1. Description du projet

#### Problème métier
TECHMA gère des tickets support, des emails clients, et des comptes-rendus de
réunions. Ces textes contiennent une information précieuse non exploitée :
quels sont les vrais problèmes des clients ? Quels sujets reviennent le plus ?
Quel est le niveau de satisfaction réel ?

**Question clé :** *Que disent réellement les clients dans leurs communications,
et comment cette information peut-elle améliorer les services de TECHMA ?*

#### Objectif Data & AI
- **Classification automatique** des tickets par catégorie
- **Analyse de sentiment** des communications
- **Topic modeling** : découvrir les thèmes récurrents
- **Résumé automatique** des tickets complexes

---

### 2. Potentiel Data & IA

#### Techniques NLP applicables

| Tâche | Méthode simple | Méthode avancée |
|---|---|---|
| Classification tickets | TF-IDF + SVM | BERT fine-tuné |
| Analyse de sentiment | VADER / TextBlob | CamemBERT (français) |
| Topic modeling | LDA | BERTopic |
| Résumé automatique | Extractif (TextRank) | Génératif (Mistral) |
| Détection d'urgence | Règles + ML | Transformers |
| NER (entités nommées) | spaCy | CamemBERT NER |

#### Complexité : **Avancé**

#### Extensions
- Dashboard "voix du client" en temps réel
- Alerte si sentiment très négatif → escalade automatique
- Suivi temporel des sujets : les problèmes évoluent-ils ?

---

### 3. Données nécessaires

```
Tickets support :
  - texte de la demande
  - catégorie manuelle (si disponible → supervisé)
  - priorité, statut, délai de résolution
  - satisfaction après résolution (NPS, étoiles)

Emails clients :
  - objet + corps de l'email (anonymisés)
  - direction (entrant/sortant)

Comptes-rendus réunions :
  - notes prises lors des réunions de suivi
  - décisions, points bloquants mentionnés

Données de test :
  - 100–200 tickets labelisés manuellement pour l'évaluation
```

---

### 4. Feature Engineering NLP

```python
# Preprocessing standard
import re
from nltk.corpus import stopwords

def preprocess_french(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-zàâçéèêëîïôûùüÿñæœ\s]', '', text)
    tokens = text.split()
    tokens = [t for t in tokens if t not in stopwords.words('french')]
    return ' '.join(tokens)

# Features statistiques du texte
df["text_length"]      = df["text"].str.len()
df["word_count"]       = df["text"].str.split().str.len()
df["exclamation_count"]= df["text"].str.count('!')
df["question_count"]   = df["text"].str.count('\?')
df["caps_ratio"]       = df["text"].apply(lambda x: sum(1 for c in x if c.isupper()) / len(x))
# caps_ratio élevé = client qui "crie" = fort sentiment négatif

# TF-IDF pour la classification
from sklearn.feature_extraction.text import TfidfVectorizer
tfidf = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
X_tfidf = tfidf.fit_transform(df["text_clean"])

# Embeddings sémantiques pour BERTopic
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("camembert-base")
embeddings = model.encode(df["text_clean"].tolist())
```

---

### 5. Modèles & Méthodes

#### A. Classification automatique des tickets

```
Pipeline supervisé (si labels disponibles) :
  TF-IDF → SVM (baseline) → BERT fine-tuné (avancé)

Pipeline non-supervisé (si pas de labels) :
  BERTopic → clusters de tickets → nommage manuel des clusters
```

#### B. Analyse de sentiment

```python
# Option 1 : CamemBERT (meilleur pour le français)
from transformers import pipeline
sentiment_analyzer = pipeline(
    "sentiment-analysis",
    model="tblard/tf-allocine"  # modèle français pré-entraîné
)
results = sentiment_analyzer(df["text"].tolist())

# Option 2 : VADER adapté au français (plus rapide, moins précis)
```

#### C. Topic Modeling avec BERTopic

```python
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer

embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
topic_model = BERTopic(
    embedding_model=embedding_model,
    language="french",
    min_topic_size=5,
    nr_topics="auto"
)
topics, probs = topic_model.fit_transform(df["text_clean"])
```

---

### 6. Statistiques

- **Fréquence des termes** : TF-IDF scores, nuages de mots pondérés
- **Distribution des sentiments** par période (amélioration ou dégradation ?)
- **Chi-² :** certains mots sont-ils significativement associés à un sentiment négatif ?
- **Analyse temporelle :** série temporelle du sentiment moyen par mois
- **Corrélation** : sentiment négatif vs délai de résolution des tickets
- **Cohérence des topics (Cv)** : mesure de qualité du topic modeling

---

### 7. Stack technique

```
spaCy + fr_core_news_sm    → NLP français, NER, tokenization
transformers (Hugging Face) → BERT, CamemBERT, sentiment
sentence-transformers       → embeddings sémantiques
BERTopic                    → topic modeling moderne
scikit-learn                → TF-IDF, SVM, évaluation
nltk                        → preprocessing, stopwords
Plotly / WordCloud          → visualisations NLP
pandas                      → manipulation
Streamlit                   → dashboard "voix du client"
```

---

### 8. Deliverables

1. **Modèle de classification** : `ticket_classifier.pkl` (catégories auto)
2. **Analyse de sentiment** : rapport avec évolution temporelle
3. **Rapport BERTopic** : les 10 thèmes principaux dans les tickets
4. **Dashboard Streamlit** : "Voix du client" — sentiment + topics + alertes
5. **Notebook complet** : preprocessing → classification → sentiment → topics
6. **API** : `POST /analyze_ticket` → retourne {catégorie, sentiment, topic, urgence}

---

### 9. Avantages & Limites

#### Points forts
- NLP = très valorisé en 2025 dans les jurys de certification
- Applicable immédiatement sans changer les processus TECHMA
- Multiples techniques démontrables dans un seul projet

#### Difficultés
- Données en français → certains modèles anglais moins performants
- Anonymisation des données clients avant utilisation
- Topic modeling non-supervisé : les clusters ne sont pas toujours évidents

---

### 10. Pertinence certification

**Score : 8/10**

> Multiple techniques NLP (sentiment + classification + topic modeling). Bien
> adapté à un jury technique. Légèrement moins impactant qu'un RAG mais
> démontrable sur des données réelles dès les premiers jours.

---
---

## Projet 6 — Système de recommandation de solutions digitales

### 1. Description du projet

#### Problème métier
TECHMA accompagne des PME béninoises dans leur transformation digitale. Le commercial
doit recommander les bons outils (Zoho vs HubSpot, Make vs Zapier, etc.) selon le profil
de chaque client. Ce choix est souvent intuitif et subjectif.

**Question clé :** *Quels outils digitaux recommander à une PME selon son profil,
son secteur, sa taille et ses besoins déclarés ?*

#### Objectif Data & AI
Moteur de recommandation hybride :
- **Content-based** : recommander des outils similaires à ceux déjà adoptés
- **Collaborative filtering** : "les PME comme vous utilisent aussi..."
- **Modèle de scoring** : probabilité d'adoption de chaque solution

---

### 2. Potentiel Data & IA

#### Approches possibles

| Approche | Méthode | Complexité |
|---|---|---|
| Filtrage collaboratif | SVD (Matrix Factorization) | Avancé |
| Contenu | TF-IDF + cosine similarity | Intermédiaire |
| Hybride | Weighted combination | Avancé |
| Séquentiel | RNN / Transformer sur séquence d'adoption | Expert |
| Explicatif | SHAP sur un modèle de prédiction d'adoption | Avancé |

#### Complexité : **Avancé**

Le cold start (nouvelle PME sans historique) est le principal défi technique.

#### Extensions
- Quiz interactif → recommandation en temps réel
- Suivi de l'adoption → amélioration continue du modèle
- Module de comparaison : "Zoho vs HubSpot pour votre profil"

---

### 3. Données nécessaires

```
Profils clients PME :
  - secteur d'activité (commerce, services, industrie...)
  - taille (nb employés, CA approximatif)
  - niveau de maturité digitale (score 0-5)
  - besoins déclarés (CRM, automatisation, facturation...)
  - outils actuellement utilisés
  - budget annuel IT

Historique d'adoption :
  - PME X → a adopté Zoho CRM → succès/abandon après 6 mois
  - PME Y → a adopté Make → succès
  → Matrice PME × Outils avec score de satisfaction

Catalogue de solutions :
  - liste des outils disponibles
  - catégorie, prix, complexité d'implémentation
  - intégrations disponibles
  - cas d'usage recommandés
```

---

### 4. Feature Engineering

```python
# Profil client encodé
df["maturite_digitale_score"] = df["nb_outils_actuels"] * df["usage_actif_rate"]

# Distance entre profil client et profil cible d'un outil
def tool_client_match_score(client_features, tool_target_profile):
    return cosine_similarity(
        client_features.reshape(1, -1),
        tool_target_profile.reshape(1, -1)
    )[0][0]

# Embedding sémantique des besoins déclarés
needs_text = "nous avons besoin de gérer nos contacts et automatiser les relances"
needs_embedding = sentence_transformer.encode(needs_text)

# Matching sémantique besoins ↔ description de l'outil
for tool in tools_catalog:
    tool["match_score"] = cosine_similarity(
        needs_embedding,
        tool["description_embedding"]
    )
```

---

### 5. Modèles & Méthodes

#### Filtrage collaboratif (SVD)

```python
from surprise import SVD, Dataset, Reader

# Matrice PME × Outils avec ratings (1-5)
reader = Reader(rating_scale=(1, 5))
data = Dataset.load_from_df(df[["pme_id", "outil_id", "satisfaction"]], reader)

model = SVD(n_factors=50, n_epochs=20)
model.fit(data.build_full_trainset())

# Recommander les 5 meilleurs outils pour une PME
top5 = get_top_n_recommendations(model, pme_id=42, n=5)
```

#### Gestion du cold start

```python
# Pour une nouvelle PME sans historique :
# 1. Calculer la similarité avec d'autres PME connues (profil-based)
similar_pmes = find_similar_pmes(new_pme_profile, known_pmes_profiles)
# 2. Recommander ce que ces PME similaires utilisent avec succès
recommendations = aggregate_tools(similar_pmes, weights=similarity_scores)
```

---

### 6. Statistiques

- **Précision@K** : parmi les K outils recommandés, combien sont réellement adoptés ?
- **NDCG (Normalized Discounted Cumulative Gain)** : qualité du classement
- **Coverage** : % d'outils du catalogue recommandés au moins une fois
- **Diversité** : les recommandations varient-elles selon les profils ?
- **A/B test** : recommandations algorithmiques vs recommandations commerciales

---

### 7. Stack technique

```
scikit-surprise          → filtrage collaboratif (SVD, KNN)
sentence-transformers    → embeddings des besoins textuels
numpy, pandas            → manipulation matricielle
FastAPI                  → API de recommandation
Streamlit                → quiz interactif + résultats
Plotly                   → visualisation des recommandations
MLflow                   → tracking des expériences
```

---

### 8. Deliverables

1. **Moteur de recommandation** : `recommender_model.pkl`
2. **Application quiz** : Streamlit — "Trouvez les outils faits pour vous"
3. **API** : `POST /recommend` avec profil PME → retourne top 5 outils
4. **Rapport d'évaluation** : précision@5, NDCG, coverage
5. **Matrice de similarité inter-outils** : visualisation des proximités

---

### 9. Avantages & Limites

#### Points forts
- Système de recommandation = compétence très recherchée
- Applicable immédiatement dans le processus commercial de TECHMA
- Quiz interactif = démo très engageante

#### Difficultés
- Cold start problème difficile avec peu de données
- Collecte de données historiques d'adoption nécessite du temps
- Validation difficile sans retours terrain

---

### 10. Pertinence certification

**Score : 7/10**

> Intéressant techniquement (filtrage collaboratif, NLP). Moins fort que les
> projets 1 et 3 sur le plan de la complexité ML. Fort sur le plan métier.

---
---

## Projet 7 — Prédiction de performance et ROI des projets

### 1. Description du projet

#### Problème métier
TECHMA livre des projets de transformation digitale. Certains dépassent le budget,
d'autres les délais. Identifier dès le début quels projets sont à risque permettrait
d'ajuster les ressources et les promesses clients.

**Question clé :** *Quels projets risquent de dépasser le budget ou les délais,
et quels facteurs l'expliquent ?*

---

### 2. Potentiel Data & IA

| Tâche prédictive | Modèle | Variable cible |
|---|---|---|
| Prédiction délai | Régression (RF, XGBoost) | `nb_jours_réels / nb_jours_estimés` |
| Prédiction dépassement budget | Classification binaire | `over_budget (oui/non)` |
| Estimation ROI client | Régression | `roi_6_mois` |
| Clustering projets | K-Means | Types de projets par profil de risque |

#### Complexité : **Intermédiaire à Avancé**

---

### 3. Données nécessaires

```
Par projet :
  - type de projet (CRM, automatisation, intégration, formation...)
  - taille client (PME petite/moyenne/grande)
  - stack technique (Zoho, HubSpot, Make, custom...)
  - nb de consultants assignés
  - durée estimée vs durée réelle
  - budget estimé vs budget réel
  - nb de révisions demandées par le client
  - nb de changements de périmètre (scope changes)
  - satisfaction client à 3 mois et 6 mois
```

---

### 4. Feature Engineering

```python
# Ratio dépassement
df["budget_ratio"] = df["budget_reel"] / df["budget_estime"]
df["delay_ratio"]  = df["duree_reelle"] / df["duree_estimee"]

# Complexité technique estimée
df["tech_complexity"] = (
    (df["nb_integrations"] * 2)
    + (df["is_custom_dev"] * 3)
    + df["nb_modules_configures"]
)

# Expérience de l'équipe sur ce type de projet
df["team_experience_score"] = (
    df["consultant_nb_projets_similaires"] / df["consultant_nb_projets_similaires"].max()
)

# Engagement client (proxy de qualité de la collaboration)
df["client_engagement"] = (
    (1 / (1 + df["avg_response_delay_days"])) * 0.5
    + (1 - df["nb_scope_changes"] / 5).clip(0) * 0.5
)
```

---

### 5. Modèles & Méthodes

```
Régression : prédire le ratio délai/budget
  → Random Forest Regressor
  → Gradient Boosting
  → Evaluation : MAE, RMSE, R²

Classification : dépassement budget (oui/non)
  → XGBoost + SHAP
  → Evaluation : F1, ROC-AUC, Recall (minimiser les faux négatifs)

Clustering : profils de projets
  → K-Means sur features standardisées
  → Silhouette score pour choisir K
  → Nommage des clusters : "projets risqués complexes", "projets standards", etc.
```

---

### 6. Statistiques

- **Corrélation de Pearson** : nb de scope changes vs dépassement budget
- **Test ANOVA** : différences de délai selon le type de projet
- **Analyse de sensibilité** : quelle feature fait le plus varier la prédiction ?
- **Intervalles de confiance** : fourchette de délai prévisionnelle par type

---

### 7. Stack

```
scikit-learn, XGBoost, SHAP → ML principal
K-Means, silhouette_score  → clustering
matplotlib, seaborn, Plotly → visualisations
Streamlit                  → outil d'estimation de risque projet
MLflow                     → suivi des expériences
```

---

### 8. Deliverables

1. **Outil d'estimation de risque** : interface Streamlit pour estimer le risque avant de signer
2. **Modèle exporté** : `project_risk_model.pkl`
3. **Dashboard projet** : visualisation des projets passés + prédictions
4. **Rapport SHAP** : quelles caractéristiques causent les dépassements ?

---

### 9. Avantages & Limites

#### Points forts
- Directement utile pour la gestion interne de TECHMA
- Combine régression + classification + clustering

#### Difficultés
- Petit dataset probable (dizaines de projets seulement)
- Simulation nécessaire pour enrichir

---

### 10. Pertinence certification

**Score : 7/10**

> Solide sur le plan ML (multi-tâche) mais moins innovant que les projets 1/3.
> Fort si combiné avec le projet 4 (pipeline unifié).

---
---

## Projet 8 — Dashboard BI intelligent avec détection d'anomalies

### 1. Description du projet

#### Problème métier
TECHMA produit des rapports de performance pour ses clients PME. Actuellement
manuels, ces rapports sont chronophages et réactifs (on découvre les problèmes
après coup). Il faut passer à un **monitoring proactif et intelligent**.

**Question clé :** *Comment détecter automatiquement les anomalies dans les KPIs
des clients et alerter avant que les problèmes s'aggravent ?*

---

### 2. Potentiel Data & IA

| Technique | Usage | Complexité |
|---|---|---|
| Isolation Forest | Détection d'anomalies ponctuelles | Intermédiaire |
| Prophet (Facebook) | Prévision de séries temporelles | Avancé |
| ARIMA / SARIMA | Prévision + intervalles de confiance | Avancé |
| ADWIN | Détection de drift dans les données | Expert |
| Autoencoder (LSTM) | Anomalies dans les séquences temporelles | Expert |

#### Complexité : **Avancé**

---

### 3. Données nécessaires

```
KPIs clients (séries temporelles) :
  - Nb de leads par semaine
  - Taux de conversion mensuel
  - Chiffre d'affaires mensuel
  - Nb de tickets support par semaine
  - Temps de réponse moyen

Données de référence :
  - Saisonnalité connue (fin d'année = pics, Ramadan = creux...)
  - Objectifs fixés par le client en début de contrat
```

---

### 4. Feature Engineering

```python
# Features temporelles pour anomaly detection
df["rolling_mean_4w"] = df["kpi"].rolling(4).mean()
df["rolling_std_4w"]  = df["kpi"].rolling(4).std()
df["zscore"]          = (df["kpi"] - df["rolling_mean_4w"]) / df["rolling_std_4w"]
df["is_anomaly"]      = df["zscore"].abs() > 2.5

# Features de tendance
df["trend_slope"] = # régression linéaire sur les 8 dernières semaines → positif/négatif
df["seasonality_index"] = df["kpi"] / df["rolling_mean_52w"]  # vs moyenne annuelle
```

---

### 5. Modèles & Méthodes

#### Prévision avec Prophet

```python
from prophet import Prophet

model = Prophet(
    seasonality_mode='multiplicative',
    yearly_seasonality=True,
    weekly_seasonality=True,
    changepoint_prior_scale=0.05
)
model.fit(df[["ds", "y"]])  # ds = date, y = valeur KPI

future = model.make_future_dataframe(periods=12, freq='W')
forecast = model.predict(future)
# forecast contient : valeur prévue + intervalles de confiance (yhat_lower, yhat_upper)
# Anomalie = valeur réelle hors des intervalles
```

#### Détection d'anomalies avec Isolation Forest

```python
from sklearn.ensemble import IsolationForest

iso = IsolationForest(contamination=0.05, random_state=42)
# contamination = proportion attendue d'anomalies (5%)
anomalies = iso.fit_predict(X_multivariate)
# -1 = anomalie, 1 = normal
```

---

### 6. Statistiques

- **Intervalles de confiance Prophet** : 80%, 95%
- **Z-score** : déviation à la moyenne glissante
- **Test ADF (Augmented Dickey-Fuller)** : la série est-elle stationnaire ?
- **Corrélation croisée (CCF)** : un KPI en retard prédit-il un autre ?
- **MAPE, RMSE** : évaluation des prévisions

---

### 7. Stack

```
Prophet                 → prévision séries temporelles
scikit-learn            → Isolation Forest
statsmodels             → ARIMA, tests statistiques
pandas                  → manipulation des séries
Plotly                  → graphiques interactifs de monitoring
Streamlit               → dashboard temps réel
APScheduler             → tâches planifiées (refresh automatique)
Make/Zapier webhook     → alerte si anomalie détectée
```

---

### 8. Deliverables

1. **Dashboard Streamlit** : monitoring temps réel de 5 KPIs par client
2. **Modèle Prophet** : prévisions 3 mois avec intervalles de confiance
3. **Système d'alertes** : webhook → email/SMS si anomalie
4. **Rapport hebdomadaire auto-généré** : PDF via ReportLab
5. **Notebook** : détection d'anomalies + évaluation

---

### 9. Avantages & Limites

#### Points forts
- Très visuel et démontrable (graphiques animés en live)
- Prophet = bibliothèque robuste avec excellent résultat sur des données saisonnières
- Alertes automatiques = valeur business immédiate

#### Difficultés
- Au moins 1–2 ans de données historiques pour Prophet
- Faux positifs d'anomalies si le contexte change (COVID, nouvelle stratégie...)

---

### 10. Pertinence certification

**Score : 8/10**

> Séries temporelles + anomaly detection + dashboard + alertes. Très fort
> visuellement. Complémentaire du projet 1 ou 4.

---
---

## Tableau comparatif final

| Projet | Complexité ML | Valeur métier | Niveau IA | Faisabilité solo | Données simulables | Pertinence certification |
|---|---|---|---|---|---|---|
| **1 — Lead Scoring** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ Oui | **9/10** |
| **2 — Churn** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ✅ Oui | **8.5/10** |
| **3 — Chatbot RAG** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ✅ Oui (docs) | **9.5/10** |
| **4 — Pipeline unifié** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⚠️ Partiel | **7.5/10** |
| **5 — NLP tickets** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ Oui | **8/10** |
| **6 — Recommandation** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ✅ Oui | **7/10** |
| **7 — Performance projets** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ Oui | **7/10** |
| **8 — BI + anomalies** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ Oui | **8/10** |

---

## TOP 2 recommandés

### 🥇 Projet 3 — Chatbot RAG **(Score : 9.5/10)**

**Pourquoi c'est le meilleur choix pour la certification :**
- Architecture 2025 : RAG + LLM = technologie de pointe, très demandée
- Démo live en soutenance = impact maximal sur le jury
- Compétences démontrées : NLP, embeddings, bases vectorielles, déploiement API
- Données disponibles dès maintenant (docs publiques Zoho/Make)
- Extensible : WhatsApp, Zoho Desk, multilingue

**Effort estimé :** 3–4 semaines pour un prototype complet

---

### 🥈 Projet 1 — Lead Scoring CRM **(Score : 9/10)**

**Pourquoi c'est le deuxième meilleur choix :**
- Pipeline ML complet et classique = couvre 80% des attentes d'une certification
- SHAP = interprétabilité démontrable et pédagogique
- Valeur métier directe et mesurable → "avec notre modèle, le taux de conversion a augmenté de X%"
- FastAPI → injection dans Zoho CRM = déploiement réel
- Bien documenté, reproductible, testable

**Effort estimé :** 2–3 semaines pour un prototype complet

---

## Combinaisons possibles

### Combinaison A — "Full Stack Data & AI" (ambition maximale)

```
Projet 4 (Pipeline unifié)
    +
Projet 1 (Lead Scoring)
    +
Projet 8 (BI + anomalies)

→ Fondation data → prédiction → monitoring
→ Démontre : ingénierie data + ML supervisé + séries temporelles
→ Un seul système cohérent de bout en bout
→ Score certification estimé : 9/10
```

### Combinaison B — "NLP & IA Générative" (impact jury maximum)

```
Projet 3 (Chatbot RAG)
    +
Projet 5 (NLP tickets)

→ Le chatbot répond aux nouvelles questions
→ Le NLP tickets analyse les conversations passées
→ Complémentaires sur la même base de données textuelle
→ Score certification estimé : 9.5/10
```

### Combinaison C — "Valeur Métier Directe" (faisabilité optimale)

```
Projet 1 (Lead Scoring)
    +
Projet 2 (Churn)

→ Les deux côtés du cycle client : attirer + retenir
→ Même stack technique (XGBoost, SHAP, FastAPI)
→ Réutilisation maximale du code
→ Effort = 1 projet complet avec deux modèles
→ Score certification estimé : 8.5/10
```

---

## Recommandation finale

> **Si tu dois choisir UN seul projet :** Projet 3 (Chatbot RAG)
> **Si tu veux deux projets cohérents :** Combinaison B (RAG + NLP)
> **Si tu veux maximiser la valeur métier démontrée :** Combinaison A

Le Chatbot RAG est le projet qui combine le mieux :
- Technologie récente et valorisée (IA générative)
- Démonstrabilité en soutenance
- Faisabilité sans accès aux données privées de TECHMA
- Extension naturelle vers tous les autres projets

---

*Document créé le 2026-03-18. À réviser après choix du projet de certification.*
