# Guide d'installation

Ce document détaille les étapes d'installation et de configuration du pipeline d'automatisation du reporting et des analyses de risque.

## Prérequis

- Python 3.8+ 
- Serveur Apache Airflow (pour l'orchestration des tâches automatisées)
- Accès aux APIs financières (Yahoo Finance, FRED, etc.)
- Permissions d'accès aux répertoires de données

## Installation des dépendances

1. Cloner le dépôt :
```bash
git clone https://github.com/Kyac99/risk-reporting-automation.git
cd risk-reporting-automation
```

2. Créer un environnement virtuel Python :
```bash
python -m venv venv
source venv/bin/activate  # Sur Windows : venv\Scripts\activate
```

3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

## Configuration de l'environnement

### Configuration des chemins de données

Les chemins par défaut pour les données sont définis dans les différents scripts, mais vous pouvez les personnaliser en fonction de votre environnement.

Structure des données :
```
risk-reporting-automation/
├── data/
│   ├── portfolios/     # Fichiers de portefeuilles
│   ├── market_data/    # Données de marché
│   ├── scenarios/      # Scénarios de stress-testing
│   ├── reports/        # Rapports générés
│   └── dashboards/     # Configurations des dashboards
├── ...
```

### Configuration d'Airflow

1. Assurez-vous qu'Airflow est installé et configuré (voir la [documentation officielle d'Airflow](https://airflow.apache.org/docs/apache-airflow/stable/start.html))

2. Configurer le DAG Airflow :
   - Copier le fichier `dags/risk_reporting_dag.py` vers le répertoire des DAGs d'Airflow
   - Modifier les chemins et paramètres selon votre environnement

3. Initialiser la base de données Airflow (si ce n'est pas déjà fait) :
```bash
airflow db init
```

4. Démarrer les composants d'Airflow :
```bash
# Démarrer le webserveur
airflow webserver --port 8080

# Dans un autre terminal, démarrer le scheduler
airflow scheduler
```

5. Accéder à l'interface web d'Airflow (http://localhost:8080) et activer le DAG "risk_reporting_pipeline"

## Configuration des accès aux données

### Données de portefeuille

Placez votre fichier de portefeuille dans le répertoire `data/portfolios/`. Le format attendu est un fichier CSV contenant au minimum les colonnes suivantes :
- Security (nom du titre)
- Ticker (symbole du titre)
- Quantity (quantité détenue)
- AssetClass (classe d'actifs)

D'autres colonnes optionnelles mais utiles :
- Sector (secteur)
- Currency (devise)
- Price (prix)
- MarketValue (valeur de marché)
- Weight (poids dans le portefeuille)

Exemple de fichier disponible : `data/portfolios/example_portfolio.csv`

### Configuration des APIs financières

Le système utilise plusieurs APIs pour récupérer les données de marché. La plupart des appels sont gérés via les bibliothèques Python comme `yfinance` et `pandas-datareader`, qui ne nécessitent pas de clés d'API.

Si vous souhaitez connecter des sources de données supplémentaires, modifiez le module `src/data_collection/market_data.py` en conséquence.

## Vérification de l'installation

Pour vérifier que l'installation est correcte, vous pouvez exécuter le script d'analyse de risque sur le portefeuille d'exemple :

```bash
python scripts/run_risk_analysis.py --portfolio data/portfolios/example_portfolio.csv
```

Si tout est correctement configuré, le script devrait s'exécuter sans erreurs et générer un rapport dans le répertoire `data/reports/`.

De même, vous pouvez lancer le dashboard interactif :

```bash
python scripts/run_dashboard.py --portfolio data/portfolios/example_portfolio.csv
```

Le dashboard devrait être accessible à l'adresse http://localhost:8050.
