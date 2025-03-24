# Guide d'utilisation

Ce document explique comment utiliser le pipeline d'automatisation du reporting et des analyses de risque.

## Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Préparation des données de portefeuille](#préparation-des-données-de-portefeuille)
3. [Exécution du pipeline](#exécution-du-pipeline)
4. [Utilisation du dashboard interactif](#utilisation-du-dashboard-interactif)
5. [Personnalisation des scénarios de stress-testing](#personnalisation-des-scénarios-de-stress-testing)
6. [Automatisation avec Airflow](#automatisation-avec-airflow)
7. [Dépannage](#dépannage)

## Vue d'ensemble

Le système d'automatisation du reporting et des analyses de risque se compose de plusieurs modules :

- **Collecte de données** : Extraction des données de marché à partir de sources diverses (Yahoo Finance, FRED, etc.)
- **Traitement des portefeuilles** : Chargement et enrichissement des données de portefeuille
- **Modèles de risque** : Calcul de métriques de risque (VaR, CVaR, etc.)
- **Stress-testing** : Application de scénarios de stress sur les portefeuilles
- **Visualisation** : Création de tableaux de bord interactifs et de rapports

Ces modules peuvent être utilisés indépendamment ou ensemble via le pipeline d'automatisation.

## Préparation des données de portefeuille

### Format du fichier de portefeuille

Le système accepte plusieurs formats de fichiers :
- CSV (recommandé)
- Excel (XLSX, XLS)
- JSON
- Parquet

Le fichier doit contenir au minimum les colonnes suivantes :
- `Security` : Nom du titre
- `Ticker` : Symbole du titre (compatible avec Yahoo Finance)
- `Quantity` : Quantité détenue
- `AssetClass` : Classe d'actifs

Colonnes recommandées pour des fonctionnalités avancées :
- `Sector` : Secteur économique
- `Currency` : Devise de cotation
- `Price` : Prix unitaire (si absent, sera récupéré automatiquement)
- `MarketValue` : Valeur de marché (si absent, sera calculée)
- `Weight` : Poids dans le portefeuille (si absent, sera calculé)

### Exemple de préparation d'un portefeuille

Vous pouvez utiliser la classe `PortfolioLoader` pour charger et enrichir un portefeuille :

```python
from src.data_collection.portfolio_data import PortfolioLoader
from src.data_collection.market_data import MarketDataCollector
from datetime import datetime, timedelta

# Charger le portefeuille
loader = PortfolioLoader()
portfolio = loader.load_portfolio_from_csv("data/portfolios/my_portfolio.csv")

# Collecter les données de marché pour les tickers du portefeuille
collector = MarketDataCollector()
tickers = portfolio['Ticker'].unique().tolist()
end_date = datetime.now()
start_date = end_date - timedelta(days=30)
market_data = collector.get_stock_data(tickers, start_date, end_date)

# Enrichir le portefeuille avec les données de marché
enriched_portfolio = loader.enrich_portfolio_with_market_data(portfolio, market_data)

# Sauvegarder le portefeuille enrichi
loader.save_portfolio(enriched_portfolio, "my_enriched_portfolio", format="csv")
```

## Exécution du pipeline

### Exécution manuelle

Le script `scripts/run_risk_analysis.py` permet d'exécuter manuellement le pipeline d'analyse de risque :

```bash
python scripts/run_risk_analysis.py --portfolio data/portfolios/example_portfolio.csv
```

Options disponibles :
- `--portfolio` : Chemin vers le fichier de portefeuille
- `--start_date` : Date de début pour les données de marché (format: YYYY-MM-DD)
- `--end_date` : Date de fin pour les données de marché (format: YYYY-MM-DD)
- `--confidence_level` : Niveau de confiance pour la VaR (entre 0 et 1)
- `--time_horizon` : Horizon temporel pour la VaR (en jours)
- `--var_method` : Méthode de calcul de la VaR (historical, parametric, monte_carlo)
- `--scenarios` : Liste des scénarios de stress-test à exécuter
- `--output` : Chemin vers le fichier de sortie

Exemple avec des options personnalisées :
```bash
python scripts/run_risk_analysis.py \
    --portfolio data/portfolios/my_portfolio.csv \
    --start_date 2024-01-01 \
    --end_date 2024-12-31 \
    --confidence_level 0.99 \
    --time_horizon 10 \
    --var_method monte_carlo \
    --scenarios financial_crisis_2008 rate_shock inflation_shock \
    --output data/reports/my_risk_report.json
```

### Interprétation des résultats

Le rapport généré contient :
- Un résumé du portefeuille
- Les métriques de risque calculées (VaR, CVaR, etc.)
- Les résultats des stress-tests appliqués

Ces informations sont enregistrées au format JSON et peuvent être visualisées via le dashboard interactif.

## Utilisation du dashboard interactif

### Lancement du dashboard

Le script `scripts/run_dashboard.py` permet de lancer le dashboard interactif :

```bash
python scripts/run_dashboard.py --portfolio data/portfolios/example_portfolio.csv
```

Options disponibles :
- `--portfolio` : Chemin vers le fichier de portefeuille
- `--market_data` : Chemin vers le fichier de données de marché (optionnel)
- `--returns_data` : Chemin vers le fichier de données de rendements (optionnel)
- `--risk_metrics` : Chemin vers le fichier de métriques de risque (optionnel)
- `--stress_test_results` : Chemin vers le fichier de résultats de stress-test (optionnel)
- `--title` : Titre du dashboard
- `--host` : Hôte sur lequel exécuter le serveur Dash
- `--port` : Port sur lequel exécuter le serveur Dash
- `--debug` : Lancer en mode debug

### Navigation dans le dashboard

Le dashboard est organisé en quatre onglets :

1. **Portefeuille** : Vue d'ensemble du portefeuille, avec des graphiques de répartition par classe d'actifs, secteur, devise, etc.
2. **Analyse de Risque** : Métriques de risque (VaR, CVaR, volatilité), contributions au risque, distribution des rendements
3. **Stress-Test** : Résultats des scénarios de stress-test, impact sur le portefeuille
4. **Performance** : Suivi de la performance du portefeuille dans le temps, analyse des rendements

Chaque onglet offre des filtres et des contrôles interactifs pour personnaliser l'analyse.

## Personnalisation des scénarios de stress-testing

### Scénarios prédéfinis

Le système inclut plusieurs scénarios de stress-testing prédéfinis :
- `financial_crisis_2008` : Simulation de la crise financière de 2008
- `rate_shock` : Choc de taux d'intérêt
- `inflation_shock` : Choc d'inflation
- `liquidity_crisis` : Crise de liquidité
- `geopolitical_crisis` : Crise géopolitique

### Création de scénarios personnalisés

Vous pouvez créer vos propres scénarios de stress-testing en utilisant la classe `ScenarioGenerator` :

```python
from src.stress_testing.scenario_generator import ScenarioGenerator

# Initialiser le générateur de scénarios
generator = ScenarioGenerator()

# Créer un scénario personnalisé
custom_scenario = generator.create_custom_scenario(
    name="my_custom_scenario",
    description="Mon scénario personnalisé",
    shocks={
        'equity': -0.20,  # Choc de -20% sur les actions
        'interest_rate': 0.01,  # Hausse des taux d'intérêt de 100 points de base
        'credit_spread': 0.005,  # Augmentation des spreads de crédit de 50 points de base
        'volatility': 0.15,  # Augmentation de la volatilité de 15 points
        'fx': {
            'USD': 0.0,
            'EUR': -0.05,  # Baisse de l'euro de 5% par rapport au dollar
            'GBP': -0.08,  # Baisse de la livre sterling de 8% par rapport au dollar
        }
    },
    save=True  # Sauvegarder le scénario pour une utilisation ultérieure
)
```

## Automatisation avec Airflow

### Configuration du DAG

Le DAG Airflow `risk_reporting_pipeline` est configuré pour s'exécuter quotidiennement (jours ouvrables) et effectuer les étapes suivantes :
1. Collecte des données de marché
2. Traitement du portefeuille
3. Calcul des métriques de risque
4. Exécution des stress-tests
5. Génération du rapport
6. Mise à jour du dashboard
7. Envoi de notifications

Vous pouvez personnaliser la planification et les paramètres du DAG en modifiant le fichier `dags/risk_reporting_dag.py`.

### Surveillance des exécutions

Accédez à l'interface web d'Airflow (http://localhost:8080 par défaut) pour surveiller les exécutions du DAG et consulter les logs en cas d'erreur.

## Dépannage

### Problèmes courants

#### Erreurs de collecte de données
- Vérifiez que les tickers sont valides pour Yahoo Finance
- Assurez-vous d'avoir une connexion Internet active
- Vérifiez les limites de rate des APIs utilisées

#### Erreurs de calcul de risque
- Assurez-vous que les données de rendements sont suffisantes
- Vérifiez que les poids du portefeuille somment à 1

#### Problèmes d'affichage du dashboard
- Vérifiez que les dépendances Dash sont correctement installées
- Assurez-vous que le port n'est pas déjà utilisé par une autre application

### Logs

Les logs du système sont écrits dans la console et peuvent être redirigés vers un fichier si nécessaire. Activez le mode debug pour obtenir plus d'informations en cas de problème :

```bash
python scripts/run_risk_analysis.py --portfolio data/portfolios/example_portfolio.csv --debug
```

Pour les logs Airflow, consultez le répertoire des logs d'Airflow configuré dans votre installation.
