# Automatisation du Reporting et des Analyses de Risque

## Présentation

Ce projet implémente un pipeline complet d'automatisation du reporting financier et des analyses de risque, avec des visualisations dynamiques et interactives et des modèles de stress-testing pour évaluer la robustesse des portefeuilles d'investissement.

![Dashboard Preview](https://via.placeholder.com/800x450?text=Risk+Dashboard+Preview)

## Fonctionnalités principales

- **Collecte automatique de données**
  - Extraction de données de marché de diverses sources (Yahoo Finance, FRED, etc.)
  - Support pour différents types d'actifs (actions, obligations, devises, etc.)
  - Mise en cache intelligente pour optimiser les performances

- **Analyse de risque avancée**
  - Calcul de VaR (Value at Risk) par différentes méthodes
  - Analyse des contributions au risque par actif
  - Métriques de performance ajustées au risque
  - Modélisation des corrélations et de la volatilité

- **Modèles de stress-testing**
  - Scénarios prédéfinis (crise financière, choc de taux, etc.)
  - Possibilité de créer des scénarios personnalisés
  - Analyse d'impact sur le portefeuille
  - Évaluation de la robustesse sous différentes conditions de marché

- **Visualisations interactives**
  - Tableaux de bord dynamiques avec Dash et Plotly
  - Rapports HTML détaillés et interactifs
  - Visualisations des allocations, risques et performances
  - Filtres et contrôles pour une analyse personnalisée

- **Automatisation complète**
  - Orchestration du pipeline avec Apache Airflow
  - Exécution planifiée et notifications
  - API pour l'intégration avec d'autres systèmes
  - Scripts utilitaires pour les exécutions manuelles

## Architecture

L'architecture modulaire du système permet une grande flexibilité et évolutivité :

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Collecte des   │    │  Traitement du  │    │   Calcul des    │
│     données     │───>│   portefeuille  │───>│ métriques de    │
│                 │    │                 │    │     risque      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
┌─────────────────┐    ┌─────────────────┐            │
│  Génération de  │<───│  Stress-Testing │<───────────┘
│     rapport     │    │                 │
└─────────────────┘    └─────────────────┘
        │
        │
        ▼
┌─────────────────┐    ┌─────────────────┐
│   Dashboard     │    │  Orchestration  │
│   Interactif    │<───│    (Airflow)    │
└─────────────────┘    └─────────────────┘
```

Pour plus de détails sur l'architecture, consultez [la documentation d'architecture](docs/ARCHITECTURE.md).

## Installation

### Prérequis

- Python 3.8+
- Serveur Apache Airflow (pour l'orchestration)
- Accès aux APIs financières 

### Installation rapide

```bash
# Cloner le dépôt
git clone https://github.com/Kyac99/risk-reporting-automation.git
cd risk-reporting-automation

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
```

Pour des instructions détaillées, consultez le [guide d'installation](docs/INSTALLATION.md).

## Utilisation

### Analyse de risque manuelle

```bash
# Exécuter une analyse de risque sur un portefeuille
python scripts/run_risk_analysis.py --portfolio data/portfolios/example_portfolio.csv

# Lancer le dashboard interactif
python scripts/run_dashboard.py --portfolio data/portfolios/example_portfolio.csv
```

Pour une utilisation plus avancée, consultez le [guide d'utilisation](docs/USAGE.md).

### Automatisation avec Airflow

1. Copiez le fichier `dags/risk_reporting_dag.py` dans votre répertoire de DAGs Airflow
2. Configurez les chemins et paramètres selon votre environnement
3. Activez le DAG dans l'interface web d'Airflow

## Structure du projet

```
risk-reporting-automation/
├── data/                         # Données d'exemple et résultats intermédiaires
│   ├── portfolios/               # Fichiers de portefeuilles
│   ├── market_data/              # Données de marché
│   ├── scenarios/                # Scénarios de stress-testing
│   ├── reports/                  # Rapports générés
│   └── dashboards/               # Configurations des dashboards
├── docs/                         # Documentation
│   ├── INSTALLATION.md           # Guide d'installation
│   ├── USAGE.md                  # Guide d'utilisation
│   └── ARCHITECTURE.md           # Documentation d'architecture
├── notebooks/                    # Notebooks Jupyter pour l'exploration et l'analyse
├── src/                          # Code source
│   ├── data_collection/          # Modules de collecte de données
│   ├── risk_models/              # Modèles d'analyse de risque
│   ├── stress_testing/           # Modèles de stress-testing
│   ├── visualization/            # Outils de visualisation
│   └── utils/                    # Fonctions utilitaires
├── scripts/                      # Scripts utilitaires
│   ├── run_risk_analysis.py      # Script pour lancer l'analyse de risque
│   └── run_dashboard.py          # Script pour lancer le dashboard
├── tests/                        # Tests unitaires et d'intégration
├── dags/                         # DAGs Airflow pour l'orchestration
└── requirements.txt              # Dépendances Python
```

## Exemples

### Calcul de Value at Risk (VaR)

```python
from src.risk_models.var_model import VaRModel, prepare_returns_data
from src.data_collection.market_data import MarketDataCollector
import numpy as np

# Collecter des données de marché
collector = MarketDataCollector()
market_data = collector.get_stock_data(['AAPL', 'MSFT', 'GOOG'], '2024-01-01', '2024-12-31')

# Préparer les données de rendements
returns_data = prepare_returns_data(market_data)

# Définir les poids du portefeuille
weights = np.array([0.4, 0.3, 0.3])

# Calculer la VaR historique
var_model = VaRModel(returns_data)
var, cvar = var_model.calculate_historical_var(weights, confidence_level=0.95, time_horizon=1)

print(f"VaR (95%, 1 jour): {var:.2%}")
print(f"CVaR (95%, 1 jour): {cvar:.2%}")
```

### Stress-testing

```python
from src.stress_testing.scenario_generator import ScenarioGenerator, apply_scenario_to_portfolio
from src.data_collection.portfolio_data import PortfolioLoader

# Charger un portefeuille
loader = PortfolioLoader()
portfolio = loader.load_portfolio_from_csv("data/portfolios/example_portfolio.csv")

# Créer un scénario de stress
scenario_generator = ScenarioGenerator()
scenario = scenario_generator.get_predefined_scenario('financial_crisis_2008')

# Appliquer le scénario au portefeuille
stressed_portfolio = apply_scenario_to_portfolio(portfolio, scenario)

# Calculer l'impact
impact = stressed_portfolio['MarketValue'].sum() - portfolio['MarketValue'].sum()
impact_pct = impact / portfolio['MarketValue'].sum()

print(f"Impact du scénario: {impact_pct:.2%}")
```

## Contribution

Les contributions à ce projet sont les bienvenues. Voici quelques domaines où vous pouvez contribuer :

- Ajout de nouvelles sources de données
- Implémentation de nouveaux modèles de risque
- Amélioration des visualisations
- Optimisation des performances
- Ajout de tests

## Licence

[MIT](LICENSE)

## Contact

Pour toute question ou suggestion, n'hésitez pas à ouvrir une issue dans ce dépôt.
