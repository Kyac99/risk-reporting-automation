# Architecture du Système

Ce document décrit l'architecture du pipeline d'automatisation du reporting et des analyses de risque.

## Vue d'ensemble

Le système est conçu selon une architecture modulaire, où chaque composant peut être utilisé indépendamment ou intégré dans le pipeline complet. Cette approche favorise la maintenabilité, la testabilité et l'extensibilité du système.

## Diagramme de l'architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Collecte des   │    │  Traitement du  │    │   Calcul des    │
│     données     │───>│   portefeuille  │───>│ métriques de    │
│                 │    │                 │    │     risque      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                      │                      │
        │                      │                      │
        ▼                      │                      ▼
┌─────────────────┐            │            ┌─────────────────┐
│   Sources de    │            │            │  Stress-Testing │
│     données     │            │            │                 │
└─────────────────┘            │            └─────────────────┘
                               │                      │
                               ▼                      │
                     ┌─────────────────┐              │
                     │  Génération de  │<─────────────┘
                     │     rapport     │
                     └─────────────────┘
                               │
                               │
                               ▼
                     ┌─────────────────┐
                     │   Dashboard     │
                     │   Interactif    │
                     └─────────────────┘
                               │
                               │
                               ▼
                     ┌─────────────────┐
                     │  Orchestration  │
                     │    (Airflow)    │
                     └─────────────────┘
```

## Composants principaux

### 1. Collecte des données

**Module principal :** `src/data_collection/`

Ce composant est responsable de la collecte des données financières à partir de diverses sources (APIs, bases de données, fichiers, etc.). Il comprend :

- `market_data.py` : Collecte des données de marché (prix, rendements, etc.)
- `portfolio_data.py` : Chargement et enrichissement des données de portefeuille

**Fonctionnalités clés :**
- Extraction des données via des APIs financières (Yahoo Finance, FRED, etc.)
- Mise en cache des données pour optimiser les performances
- Gestion des erreurs et des données manquantes
- Conversion des formats de données

### 2. Traitement du portefeuille

**Module principal :** `src/data_collection/portfolio_data.py`

Ce composant assure le chargement, la validation et l'enrichissement des données de portefeuille.

**Fonctionnalités clés :**
- Chargement de portefeuilles à partir de différents formats (CSV, Excel, JSON, etc.)
- Validation des données et gestion des erreurs
- Enrichissement avec des données de marché actuelles
- Calcul des métriques de base (valeur de marché, poids, etc.)

### 3. Calcul des métriques de risque

**Module principal :** `src/risk_models/`

Ce composant implémente les algorithmes de calcul des métriques de risque.

- `var_model.py` : Calcul de la Value at Risk (VaR) et d'autres métriques de risque

**Fonctionnalités clés :**
- Calcul de la VaR par différentes méthodes (historique, paramétrique, Monte Carlo)
- Calcul de la CVaR (Conditional Value at Risk)
- Analyse des contributions au risque par actif
- Calcul de métriques de risque incrémentales

### 4. Stress-Testing

**Module principal :** `src/stress_testing/`

Ce composant permet d'appliquer des scénarios de stress sur les portefeuilles pour évaluer leur robustesse.

- `scenario_generator.py` : Génération et application de scénarios de stress-test

**Fonctionnalités clés :**
- Définition de scénarios prédéfinis (crise financière, choc de taux, etc.)
- Création de scénarios personnalisés
- Application des scénarios aux portefeuilles
- Analyse des résultats des stress-tests

### 5. Visualisation

**Module principal :** `src/visualization/`

Ce composant gère la création de visualisations et de tableaux de bord interactifs.

- `risk_dashboard.py` : Dashboard interactif pour l'analyse de risque

**Fonctionnalités clés :**
- Dashboard interactif avec Dash et Plotly
- Visualisations de l'allocation du portefeuille
- Affichage des métriques de risque
- Visualisation des résultats des stress-tests
- Analyse de performance

### 6. Orchestration

**Module principal :** `dags/`

Ce composant assure l'orchestration et l'automatisation du pipeline complet.

- `risk_reporting_dag.py` : DAG Airflow pour l'automatisation du reporting

**Fonctionnalités clés :**
- Définition du workflow d'exécution
- Planification des tâches
- Gestion des dépendances entre les tâches
- Gestion des erreurs et notifications

## Flux de données

1. Les données de marché sont collectées à partir de sources externes
2. Les données de portefeuille sont chargées et enrichies avec les données de marché
3. Les métriques de risque sont calculées sur le portefeuille enrichi
4. Les scénarios de stress-test sont appliqués au portefeuille
5. Les rapports sont générés à partir des résultats d'analyse
6. Le dashboard interactif est mis à jour avec les dernières données
7. Le processus complet est orchestré par Airflow selon une planification définie

## Stockage des données

Le système utilise une approche basée sur des fichiers pour le stockage des données :

- `data/portfolios/` : Données de portefeuille (CSV, Excel, etc.)
- `data/market_data/` : Données de marché (parquet)
- `data/scenarios/` : Définitions des scénarios de stress-test (JSON)
- `data/reports/` : Rapports générés (HTML, JSON)
- `data/dashboards/` : Configurations des dashboards (JSON)

Cette approche permet une grande flexibilité et facilite l'intégration avec d'autres systèmes.

## Extensibilité

L'architecture modulaire du système permet d'étendre facilement ses fonctionnalités :

1. **Ajout de nouvelles sources de données :**
   - Implémentez une nouvelle classe dans le module `data_collection`
   - Respectez l'interface commune pour l'intégration avec le reste du système

2. **Ajout de nouveaux modèles de risque :**
   - Créez une nouvelle classe dans le module `risk_models`
   - Intégrez-la dans le pipeline principal ou utilisez-la indépendamment

3. **Ajout de nouveaux scénarios de stress-test :**
   - Définissez de nouveaux scénarios dans la classe `ScenarioGenerator`
   - Ou implémentez une nouvelle méthode de génération de scénarios

4. **Personnalisation des visualisations :**
   - Modifiez ou étendez la classe `RiskDashboard` dans le module `visualization`
   - Ajoutez de nouveaux éléments visuels selon vos besoins

## Considérations de performance

1. **Mise en cache des données :**
   - Les données de marché sont mises en cache pour éviter des requêtes répétées
   - Les formats de fichiers efficaces (parquet) sont utilisés pour les données volumineuses

2. **Traitement parallèle :**
   - Les opérations indépendantes peuvent être exécutées en parallèle via Airflow
   - Les calculs intensifs (Monte Carlo) sont optimisés pour les performances

3. **Requêtes API optimisées :**
   - Les requêtes API sont regroupées lorsque possible
   - La gestion des limites de taux (rate limiting) est implémentée

## Sécurité

1. **Gestion des informations sensibles :**
   - Les informations d'identification sont gérées via les variables d'environnement ou les secrets Airflow
   - Les données sensibles ne sont pas versionnées dans le code source

2. **Validation des entrées :**
   - Les données d'entrée sont validées avant traitement
   - Des mécanismes de gestion des erreurs sont en place pour éviter les comportements inattendus

## Évolutions futures

L'architecture du système permet d'envisager plusieurs évolutions :

1. **Base de données :**
   - Migration vers une base de données pour le stockage des données au lieu de fichiers
   - Implémentation d'un système de versionnement des données

2. **API REST :**
   - Exposition des fonctionnalités via une API REST
   - Intégration avec d'autres systèmes via cette API

3. **Analyses avancées :**
   - Intégration de modèles d'apprentissage automatique pour la prévision des risques
   - Analyse de scénarios plus complexes
   
4. **Interface utilisateur plus riche :**
   - Développement d'une interface utilisateur plus complète
   - Ajout de fonctionnalités de personnalisation avancées
