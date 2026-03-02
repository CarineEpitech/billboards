# Pitch 5 minutes — Billboard Geolocation Platform, Cotonou

> **Format** : Pitch investisseur / jury académique / comité technique
> **Durée** : 5 minutes chrono (~700 mots à rythme mesuré)
> **Règle d'or** : une seule idée par section, aucun jargon sans définition immédiate

---

## MINUTAGE GLOBAL

| Section | Durée | Mots ≈ |
|---|---|---|
| 1. Problème business | 0:00 – 0:45 | 100 |
| 2. Solution data | 0:45 – 1:30 | 100 |
| 3. Pipeline technique | 1:30 – 2:30 | 130 |
| 4. Modèle ML | 2:30 – 3:30 | 130 |
| 5. Limites actuelles | 3:30 – 4:00 | 60 |
| 6. Roadmap + Vision | 4:00 – 5:00 | 100 |

---

## SECTION 1 — Le problème (0:00 → 0:45)

> "Imaginez que vous êtes annonceur à Cotonou. Vous devez choisir entre deux emplacements pour votre panneau publicitaire. L'un est sur un boulevard de Dantokpa, l'autre dans une rue secondaire d'Agla. Les deux propriétaires vous donnent le même tarif.
>
> Vous ne savez pas lequel choisir.
>
> Pourquoi ? Parce qu'il n'existe aucune base de données centralisée des panneaux publicitaires à Cotonou. Aucun score objectif. Aucune comparaison possible. Les décisions d'investissement — qui se chiffrent en millions de francs CFA — se font à l'instinct.
>
> C'est le problème que nous résolvons."

**Note speaker** : Ouvrir sur une image mentale concrète, pas sur un chiffre. Marquer une pause après "à l'instinct".

---

## SECTION 2 — La solution (0:45 → 1:30)

> "Notre solution : une plateforme géoréférencée qui attribue à chaque panneau publicitaire un **score de visibilité entre 0 et 100**, calculé par un algorithme entraîné sur les caractéristiques réelles du terrain.
>
> Ce score intègre ce qu'un humain ne peut pas quantifier seul : le volume de trafic estimé, la densité piétonne, le type de panneau, sa hauteur, sa distance à la route principale, la concurrence à 500 mètres, la distance au port et au centre-ville.
>
> Résultat : pour la première fois, un annonceur peut comparer deux emplacements de façon objective. Un propriétaire peut fixer son tarif en fonction de la valeur réelle de son emplacement, pas d'une négociation à l'aveugle."

**Note speaker** : Le mot "objectif" est le pivot de cette section — y revenir si question.

---

## SECTION 3 — Le pipeline technique (1:30 → 2:30)

> "Techniquement, nous avons construit un pipeline en cinq étapes.
>
> **Étape 1 : génération des données.** En l'absence de données terrain, nous avons simulé 45 panneaux réalistes sur 10 quartiers de Cotonou — avec du bruit gaussien intentionnel sur les scores pour éviter un modèle trop parfait et inutilisable en production.
>
> **Étape 2 : nettoyage.** Coordonnées GPS hors zone, valeurs aberrantes, doublons, données manquantes — tout est détecté et corrigé automatiquement. On passe de 45 à 43 panneaux propres, zéro valeur manquante.
>
> **Étape 3 : feature engineering.** On transforme les données brutes en 23 variables exploitables par le modèle : log du trafic, ratio surface/hauteur, indice de saturation concurrentielle, distances géospatiales. Chaque variable traduit une connaissance métier.
>
> **Étapes 4 et 5 : entraînement et évaluation.** Le modèle est entraîné, comparé à une baseline, et évalué sur des données qu'il n'a jamais vues. Quatre graphiques de diagnostic sont générés automatiquement."

**Note speaker** : Aller vite ici — l'objectif est de montrer la rigueur du processus, pas d'expliquer chaque détail.

---

## SECTION 4 — Le modèle ML (2:30 → 3:30)

> "Pour le modèle, nous avons choisi un **Random Forest Regressor**. Pourquoi pas une régression linéaire ? Parce que la visibilité d'un panneau ne se calcule pas avec une somme. Un panneau de 6 mètres de haut est optimal — plus haut ne signifie pas plus visible. Un panneau digital sur boulevard vaut beaucoup plus qu'en rue secondaire. Ces interactions non-linéaires, le Random Forest les capture naturellement, sans que nous ayons à les programmer explicitement.
>
> Nous avons comparé ce modèle à une **baseline Ridge Regression**. C'est une règle méthodologique : tout modèle complexe doit prouver sa valeur face à un modèle simple. La comparaison est documentée, graphique à l'appui.
>
> La feature la plus importante identifiée par le modèle ? Le **type de panneau** — digital ou statique — avec 26% de l'importance totale. C'est cohérent avec le terrain. Ça valide que le modèle a appris quelque chose de sensé, pas du bruit."

**Note speaker** : L'exemple du panneau de 6m et la feature importance sont vos deux phrases d'ancrage — si vous oubliez quelque chose, ces deux phrases suffisent.

---

## SECTION 5 — Les limites actuelles (3:30 → 4:00)

> "Soyons honnêtes. Ce prototype a trois limites que nous assumons pleinement.
>
> Premièrement, 43 observations, c'est peu. Nos métriques de validation sont instables — c'est la réalité statistique d'un petit dataset bruité, et nous la documentons explicitement.
>
> Deuxièmement, les données sont simulées. Le modèle n'a pas encore été confronté au terrain réel.
>
> Troisièmement, le Random Forest sur données bruitées à 45 obs ne battra pas systématiquement la régression simple. Ce prototype est une preuve de concept, pas un produit fini.
>
> Ces limites ne sont pas des défauts de conception — elles définissent exactement ce que la V2 doit résoudre."

**Note speaker** : La franchise sur les limites augmente la crédibilité. Ne pas minimiser, ne pas s'excuser non plus. Ton neutre, factuel.

---

## SECTION 6 — Roadmap et vision (4:00 → 5:00)

> "La roadmap est en trois versions.
>
> **V2, dans 3 à 6 mois** : collecte terrain de 500 panneaux réels à Cotonou, intégration OpenStreetMap, modèle XGBoost optimisé, et une API REST que n'importe quel annonceur peut interroger. C'est le produit minimum viable.
>
> **V3, dans 12 à 18 mois** : détection automatique des panneaux par images satellite via YOLOv8, scoring visuel des photos par réseau de neurones, et optimisation multi-variable du placement — budget, visibilité, concurrence — simultanément.
>
> La vision à long terme est simple : devenir **la référence de l'affichage outdoor en Afrique de l'Ouest**. Le même rôle que Nielsen pour la télévision, mais pour les panneaux à Cotonou, Lomé, Abidjan, Dakar.
>
> Ce prototype est la première brique. Merci."

**Note speaker** : Terminer sur "Merci" après une pause d'une seconde sur "Dakar". Ne pas ajouter de phrase après le remerciement.

---

## Les 5 chiffres à retenir par cœur

| Chiffre | Contexte |
|---|---|
| **45** panneaux générés, 10 quartiers | Taille du dataset prototype |
| **23** features ML | Variables utilisées par le modèle |
| **26%** | Importance de la feature `panel_type` (top feature) |
| **3–6 mois** | Timeline V2 (données réelles + API) |
| **0 à 100** | Plage du score de visibilité |

---

## Les 3 phrases de secours (si vous perdez le fil)

> *"Notre modèle attribue un score de visibilité objectif à chaque panneau — c'est ça l'essentiel."*

> *"On compare toujours le RandomForest à une baseline Ridge. Un modèle complexe doit prouver sa valeur face à un modèle simple."*

> *"Ce prototype prouve que le pipeline fonctionne. La V2 y ajoute les données réelles."*

---

## Questions prévisibles et réponses en 20 secondes

**"Pourquoi pas des données réelles ?"**
> "Aucune base n'existe à Cotonou — c'est précisément le problème qu'on résout. Les données simulées valident le pipeline. La V2 intègre la collecte terrain."

**"Le modèle est fiable ?"**
> "Il est honnête : on documente ses limites, on le compare à une baseline, on génère des graphiques de diagnostic. Un modèle qui admet ses limites est plus fiable qu'un modèle qui les cache."

**"Quel est le business model ?"**
> "Abonnement SaaS pour les régies publicitaires et annonceurs. Score gratuit pour les propriétaires, accès API et dashboard payants pour les professionnels."

**"Pourquoi Cotonou d'abord ?"**
> "Marché sous-digitalisé, potentiel élevé, connaissance terrain. C'est le bon endroit pour valider le modèle avant d'étendre à Lagos, Abidjan, Dakar."
