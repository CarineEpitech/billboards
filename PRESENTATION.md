# Discours de Présentation Académique — Modèle ML Billboard Cotonou

> **Format** : Présentation technique (15–20 min) devant jury académique ou comité data.
> **Niveau** : Mid-level data science + stakeholders non-techniques.
> **Structure** : Introduction → Problème → Données → Modèle → Résultats → Critique → Roadmap

---

## SLIDE 1 — Introduction et Problématique (2 min)

### Ce que vous dites :

> "Le marché de l'affichage extérieur à Cotonou représente plusieurs centaines de millions de francs CFA annuellement, mais il n'existe aucune base de données centralisée des panneaux publicitaires. Les acteurs travaillent à l'aveugle : un propriétaire ne sait pas si son panneau est bien positionné, un annonceur ne peut pas comparer les emplacements de façon objective.
>
> Notre objectif est de construire une plateforme géoréférencée qui répond à une question simple mais puissante : **étant donné l'emplacement et les caractéristiques d'un panneau, quel est son score de visibilité estimé ?**
>
> Ce score permettra ensuite de prioriser les investissements, de fixer des tarifs basés sur la valeur réelle, et à terme d'optimiser le placement des futurs panneaux."

### Points clés à afficher :
- Marché non digitalisé → opportunité data
- Question ML : régression (score continu 0–100)
- Valeur business : pricing, placement, arbitrage

---

## SLIDE 2 — Données et Génération (2 min)

### Ce que vous dites :

> "Pour ce prototype, nous n'avons pas de données terrain. Nous avons donc construit un dataset synthétique de 45 panneaux basé sur la connaissance du terrain à Cotonou.
>
> Mais — et c'est essentiel — un dataset synthétique trivial serait inutile. Si chaque feature prédit parfaitement le score, le modèle apprend une règle triviale et sera inutilisable en production.
>
> Nous avons donc appliqué trois mécanismes de réalisme :
>
> **Premièrement**, le score de visibilité n'est pas une somme linéaire. Il intègre des non-linéarités : l'effet de la taille suit un logarithme — un panneau de 4m² vs 8m² est une énorme différence, mais 50m² vs 54m² est négligeable. Le trafic suit une racine carrée pour modéliser la saturation d'attention.
>
> **Deuxièmement**, on injecte un bruit gaussien de 8 points sur 100. Cela représente ce qu'on ne peut pas capturer : l'angle d'exposition au soleil, les obstructions locales par des arbres ou bâtiments, les événements saisonniers.
>
> **Troisièmement**, on injecte intentionnellement des erreurs réalistes : coordonnées GPS imprécises, valeurs manquantes, doublons partiels — pour tester la robustesse du pipeline de nettoyage."

### Points clés à afficher :
- 45 panneaux, 10 quartiers réels de Cotonou
- 8% de valeurs manquantes injectées
- Bruit σ = 8 pts (30% de facteurs non capturés)

---

## SLIDE 3 — Pipeline de Nettoyage (2 min)

### Ce que vous dites :

> "Le cleaning n'est pas cosmétique — c'est la fondation. Garbage in, garbage out.
>
> Notre pipeline de nettoyage s'exécute en 5 étapes dans un ordre précis.
>
> On commence par valider les coordonnées GPS — toute coordonnée hors de la bounding box de Cotonou est supprimée. On ne peut pas imputer une position géographique.
>
> Ensuite on corrige les scores aberrants par écrêtage : un score de -3 ou 999 est une erreur de saisie, on le ramène à [0, 100].
>
> On supprime les doublons en deux passes : d'abord sur le panel_id, ensuite géographiquement — deux panneaux à moins de 100m sont suspects.
>
> Pour les valeurs manquantes numériques, on impute par la **médiane et non la moyenne**. Pourquoi ? Parce que la médiane est robuste aux outliers résiduels. Si un panneau a une hauteur saisie à 50m par erreur, la moyenne serait faussée. La médiane reste réaliste.
>
> Résultat : de 45 panneaux bruts, on passe à 43 panneaux propres, sans aucun NaN."

### Points clés à afficher :
- 1 score aberrant, 2 doublons détectés et supprimés
- 5 colonnes imputées (médiane / mode)
- Pipeline auditée : audit trail complet en JSON

---

## SLIDE 4 — Feature Engineering (2 min)

### Ce que vous dites :

> "Le feature engineering, c'est l'art de traduire la connaissance métier en signal numérique pour le modèle.
>
> Nous partons des features brutes : latitude, longitude, type de panneau, trafic estimé. Puis nous en dérivons de nouvelles.
>
> Par exemple, le **log du trafic** plutôt que le trafic brut, parce que passer de 1 000 à 2 000 véhicules/jour a plus d'impact que passer de 10 000 à 11 000. Le logarithme capture cette non-linéarité.
>
> Le **ratio surface/hauteur** capture l'impact visuel : un grand panneau bas vs un petit panneau haut n'ont pas le même effet.
>
> L'**indice de saturation** combine la concurrence locale et la densité piétonne : une zone très fréquentée avec beaucoup de concurrents dilue l'attention.
>
> Pour l'encodage catégoriel — les 10 quartiers, les 4 types de panneaux — nous utilisons le **Label Encoding** plutôt que le One-Hot Encoding. Pourquoi ? Avec 43 observations, One-Hot sur 10 quartiers génère 10 colonnes pour 43 lignes. Le ratio n/p = 4.3 par colonne est insuffisant. Le RandomForest exploite les codes entiers via des splits binaires implicites."

### Points clés à afficher :
- 23 features au total (brutes + dérivées + géospatiales)
- 7 features dérivées (log_traffic, ratio_surface_hauteur, is_digital, etc.)
- 3 features géospatiales (distance port, plage, centre-ville)

---

## SLIDE 5 — Choix du Modèle (3 min) ← SLIDE CENTRALE

### Ce que vous dites :

> "Pourquoi le **RandomForest** et pas une régression linéaire ? C'est la question centrale.
>
> La **régression Ridge** est notre baseline de référence. C'est une régression linéaire régularisée qui prédit le score comme une combinaison pondérée des features : score = β0 + β1·trafic + β2·taille + ... Elle est stable, interprétable, et rapide.
>
> Mais elle souffre d'une hypothèse forte : **chaque feature a un effet additif et constant**. Or, dans notre domaine, ce n'est pas vrai.
>
> L'effet de la hauteur est **gaussien**, pas linéaire — un panneau de 6–8m est optimal, un panneau de 15m est moins visible. La régression ne peut pas capturer ça sans feature engineering manuel.
>
> L'**interaction** entre le type de panneau et le type de route est capitale : un panneau digital sur boulevard = +30 pts, le même panneau en rue secondaire = +5 pts seulement. Une régression linéaire nécessiterait une feature croisée explicite. Le RandomForest la capture automatiquement.
>
> Le **RandomForest** est un ensemble de 100 arbres de décision. Chaque arbre apprend des règles binaires : 'Si trafic > 5000 ET panneau digital ALORS score ~ 80'. La prédiction finale est la moyenne des 100 arbres. Cela donne :
> - Capture native des non-linéarités et interactions
> - Robustesse aux outliers (un outlier influence 1 arbre sur 100)
> - Invariance d'échelle (pas besoin de StandardScaler)
> - Feature importance built-in (Mean Decrease Impurity)
>
> La limite principale : avec seulement 43 observations, le RandomForest peut sur-apprendre. C'est pourquoi nous le régularisons : max_depth=4 (arbres peu profonds), min_samples_leaf=4 (chaque feuille doit représenter au moins 4 observations)."

### Points clés à afficher :
- Tableau comparatif RF vs Ridge (tableau du module)
- "Baseline d'abord, puis complexité si justifiée"
- Hyperparamètres de régularisation

---

## SLIDE 6 — Validation Croisée et OOB (2 min)

### Ce que vous dites :

> "Comment valider un modèle sur seulement 43 observations ? C'est le défi principal.
>
> Un simple train/test split (80/20) donne 9 observations de test. Le R² sur 9 points a une variance statistique immense — un seul mauvais point peut faire chuter R² de 0.5 à 0.2. Ce n'est pas un signal fiable.
>
> Nous utilisons donc **deux mécanismes complémentaires**.
>
> La **validation croisée K-fold (K=5)** divise le dataset en 5 blocs. À chaque itération, on entraîne sur 4 blocs et on évalue sur le 5ème. On répète 5 fois. Chaque observation est utilisée exactement une fois en validation. On obtient 5 scores R² — la moyenne donne une estimation non biaisée, l'écart-type mesure la stabilité.
>
> Le **score OOB (Out-Of-Bag)** exploite le mécanisme bootstrap du RandomForest. Chaque arbre n'est entraîné que sur ~63% des observations (tirage avec remise). Les ~37% restantes servent de validation 'gratuite' pour cet arbre. Agrégé sur 100 arbres, l'OOB R² est conceptuellement équivalent à une Leave-One-Out CV, sans coût supplémentaire.
>
> Sur notre dataset bruité à 43 observations, les CV R² peuvent être négatifs — cela signifie 'sur ce fold de 7 observations, le modèle fait moins bien que prédire la moyenne'. C'est normal et attendu. L'important est la tendance : est-ce que le RF fait mieux que la Ridge baseline en CV ?"

### Points clés à afficher :
- K-fold : estimation non biaisée de la généralisation
- OOB : validation gratuite intégrée au RandomForest
- Variance élevée = réalité statistique du petit dataset

---

## SLIDE 7 — Résultats et Comparaison (3 min)

### Ce que vous dites :

> "Regardons les résultats. Je vais vous montrer trois niveaux d'analyse.
>
> **Premier niveau : le test set (9 observations).**
> Notre RandomForest obtient un R² d'environ 0.23 à 0.35 selon le split. La Ridge baseline obtient un R² similaire. Avec 9 observations, ces deux valeurs sont statistiquement peu distinguables — l'intervalle de confiance se chevauche.
>
> **Deuxième niveau : la cross-validation sur X_train.**
> En CV 5-fold, le RandomForest obtient un R² moyen avec une forte variance — ce qui révèle que sur ce petit dataset bruité, les deux modèles capturent peu de signal stable. C'est une conclusion honnête, pas un échec.
>
> **Troisième niveau : les features importantes.**
> Et c'est ici que le modèle devient intéressant. Le type de panneau — digital ou statique — représente 26% de l'importance totale. C'est cohérent avec l'expertise terrain. Le trafic estimé pèse 14%. La longitude, qui différencie les zones est/ouest de Cotonou, pèse 10%. Ces résultats font sens métier — c'est la validation qualitative du modèle.
>
> **La learning curve** montre l'évolution du R² train vs CV selon la taille du dataset. On voit clairement le gap overfitting — mais on voit aussi que ce gap diminue légèrement quand n augmente. La conclusion : avec 200 panneaux réels, ce gap se réduira significativement."

### Points clés à afficher :
- Graphique 05 : RF vs Ridge (barres)
- Graphique 06 : Learning curve (gap overfitting)
- Graphique 03 : Feature importance (validation métier)

---

## SLIDE 8 — Critique Honnête et Limites (1 min)

### Ce que vous dites :

> "Un modèle ML honnête doit admettre ses limites.
>
> La limite principale de ce prototype est la **taille du dataset**. Avec 43 observations pour 23 features, le ratio n/p = 1.9. En ML, on veut n/p > 10 pour de bonnes garanties statistiques. Toutes nos métriques sont instables sur ce dataset.
>
> Le **bruit intentionnel** de 8 points sur 100 représente ~30% de la variance de la cible. Même un modèle parfait ne pourrait pas dépasser R² ≈ 0.7 sur ces données.
>
> La **feature importance MDI** présente un biais connu vers les features continues à haute cardinalité. En V2, nous utiliserons les SHAP values, plus précises.
>
> Ces limites sont connues, quantifiées, et documentées. Elles guident directement la roadmap."

---

## SLIDE 9 — Roadmap V1 → V2 → V3 (2 min)

### Ce que vous dites :

> "Ce prototype n'est pas une fin en soi — c'est le point zéro d'une trajectoire.
>
> En **V2** (3–6 mois), on passe à la production : collecte terrain de 500+ panneaux à Cotonou, intégration OpenStreetMap pour les features routières, XGBoost avec Optuna pour l'optimisation des hyperparamètres. On ajoute les SHAP values pour l'explicabilité individuelle — un propriétaire peut voir pourquoi son panneau a un score de 65 et pas 80. On expose le modèle via une API FastAPI et un dashboard Streamlit.
>
> En **V3** (12–18 mois), on monte en intelligence : détection automatique des panneaux par satellite via YOLOv8 sur images Sentinel-2 — cela permet de détecter les panneaux non déclarés. Un CNN évalue la qualité visuelle des photos. Un algorithme génétique optimise le placement multi-variable en intégrant budget, visibilité et concurrence simultanément.
>
> À chaque version, la valeur business augmente : V1 = catalogue, V2 = scoring outil de vente, V3 = optimisation stratégique."

### Points clés à afficher :
```
V1 (actuel)   → Dataset simulé, pipeline ML, prototype
V2 (3-6 mois) → Dataset réel, XGBoost, SHAP, API, Dashboard
V3 (12-18 m)  → YOLOv8, CNN, optimisation multi-variable, MLOps
```

---

## Réponses aux questions difficiles

### "Pourquoi pas XGBoost directement ?"
> "XGBoost est meilleur en performance absolue, mais avec 43 observations, ses hyperparamètres (learning_rate, n_estimators, subsample, colsample_bytree...) sont très sensibles. Sans validation croisée robuste — ce qui est difficile avec si peu de données — on risque de l'optimiser pour le train set. Le RandomForest avec des contraintes simples est plus sûr pour ce prototype. XGBoost sera notre premier candidat en V2 avec 500+ observations."

### "Le R² est faible, le modèle est inutile ?"
> "Non — et c'est une interprétation courante mais incorrecte. Premièrement, le R² sur 9 observations est statistiquement peu fiable : l'intervalle de confiance est large. Deuxièmement, même un modèle avec R²=0.3 sur données bruitées peut être business-useful : il rank correctement les panneaux dans 70% des cas, ce qui suffit pour prioriser les investissements. Troisièmement, notre target contient 30% de variance irréductible — le R² max théorique sur ce dataset est ~0.7."

### "Comment choisir alpha pour Ridge ?"
> "alpha=1.0 est la valeur par défaut recommandée comme point de départ. Pour optimiser, on utiliserait RidgeCV avec cross_validation intégrée qui teste automatiquement plusieurs alphas. Sur un petit dataset, la différence entre alpha=0.1 et alpha=10 est souvent faible en termes de RMSE test."

### "Pourquoi Label Encoding et pas Target Encoding ?"
> "Le Target Encoding remplacerait chaque quartier par la moyenne de la target dans ce quartier. C'est très efficace sur grands datasets, mais sur 43 observations, certains quartiers ont 3–4 panneaux — la moyenne serait bruitée et introduirait un fort data leakage. Label Encoding est plus conservateur et sûr pour ce prototype."

### "Est-ce que le modèle pourrait être discriminatoire ?"
> "Question importante. Le modèle ne contient aucune variable démographique — pas de revenu, ethnie ou statut social. Il utilise uniquement des caractéristiques physiques (type, taille, hauteur) et géographiques (trafic, quartier, distance routes). Le quartier pourrait capturer indirectement des inégalités économiques, mais c'est un proxy de trafic et densité commerciale, pas de population."

---

## Checklist de présentation

- [ ] Avoir le pipeline tourné récemment (`python main.py`) avec les 6 graphiques à jour
- [ ] Ouvrir `reports/figures/` : préparer `05_model_comparison.png` et `06_learning_curve.png` en plein écran
- [ ] Avoir `reports/model_results.json` ouvert pour montrer la structure du rapport
- [ ] Préparer la démo live : `python main.py --step demo` pour la prédiction sur nouveau panneau
- [ ] Connaître les valeurs exactes : CV R², OOB R², top feature, RMSE RF vs Ridge
