#!/usr/bin/env python
"""
Script pour lancer le dashboard de risque interactif.
"""

import sys
import os
import argparse
import logging
import pandas as pd
import json
from datetime import datetime

# Ajouter le répertoire parent au chemin d'importation
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Importer le module de dashboard
from src.visualization.risk_dashboard import RiskDashboard

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Définir les chemins des données
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(PROJECT_DIR, "data")


def parse_arguments():
    """
    Parser les arguments de ligne de commande.
    """
    parser = argparse.ArgumentParser(description="Lancer le dashboard de risque interactif")
    
    parser.add_argument(
        "--portfolio",
        type=str,
        default=os.path.join(DATA_DIR, "portfolios", "example_portfolio.csv"),
        help="Chemin vers le fichier de portefeuille"
    )
    
    parser.add_argument(
        "--market_data",
        type=str,
        default=None,
        help="Chemin vers le fichier de données de marché (optionnel)"
    )
    
    parser.add_argument(
        "--returns_data",
        type=str,
        default=None,
        help="Chemin vers le fichier de données de rendements (optionnel)"
    )
    
    parser.add_argument(
        "--risk_metrics",
        type=str,
        default=None,
        help="Chemin vers le fichier de métriques de risque (optionnel)"
    )
    
    parser.add_argument(
        "--stress_test_results",
        type=str,
        default=None,
        help="Chemin vers le fichier de résultats de stress-test (optionnel)"
    )
    
    parser.add_argument(
        "--title",
        type=str,
        default="Dashboard de Risque et Performance",
        help="Titre du dashboard"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Hôte sur lequel exécuter le serveur Dash"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8050,
        help="Port sur lequel exécuter le serveur Dash"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Lancer en mode debug"
    )
    
    return parser.parse_args()


def load_portfolio(portfolio_file):
    """
    Charger le portefeuille.
    """
    logger.info(f"Chargement du portefeuille depuis {portfolio_file}")
    
    if portfolio_file.endswith(".csv"):
        return pd.read_csv(portfolio_file)
    elif portfolio_file.endswith(".parquet"):
        return pd.read_parquet(portfolio_file)
    elif portfolio_file.endswith(".xlsx") or portfolio_file.endswith(".xls"):
        return pd.read_excel(portfolio_file)
    elif portfolio_file.endswith(".json"):
        return pd.read_json(portfolio_file)
    else:
        raise ValueError(f"Format de fichier non pris en charge: {portfolio_file}")


def load_market_data(market_data_file):
    """
    Charger les données de marché.
    """
    if market_data_file is None:
        return None
    
    logger.info(f"Chargement des données de marché depuis {market_data_file}")
    
    if market_data_file.endswith(".csv"):
        return pd.read_csv(market_data_file)
    elif market_data_file.endswith(".parquet"):
        return pd.read_parquet(market_data_file)
    else:
        raise ValueError(f"Format de fichier non pris en charge: {market_data_file}")


def load_returns_data(returns_data_file):
    """
    Charger les données de rendements.
    """
    if returns_data_file is None:
        return None
    
    logger.info(f"Chargement des données de rendements depuis {returns_data_file}")
    
    if returns_data_file.endswith(".csv"):
        return pd.read_csv(returns_data_file, index_col=0)
    elif returns_data_file.endswith(".parquet"):
        return pd.read_parquet(returns_data_file)
    else:
        raise ValueError(f"Format de fichier non pris en charge: {returns_data_file}")


def load_risk_metrics(risk_metrics_file):
    """
    Charger les métriques de risque.
    """
    if risk_metrics_file is None:
        return None
    
    logger.info(f"Chargement des métriques de risque depuis {risk_metrics_file}")
    
    with open(risk_metrics_file, 'r') as f:
        return json.load(f)


def load_stress_test_results(stress_test_results_file):
    """
    Charger les résultats des stress-tests.
    """
    if stress_test_results_file is None:
        return None
    
    logger.info(f"Chargement des résultats de stress-test depuis {stress_test_results_file}")
    
    with open(stress_test_results_file, 'r') as f:
        return json.load(f)


def setup_dashboard_from_config(config_file):
    """
    Configurer le dashboard à partir d'un fichier de configuration.
    """
    logger.info(f"Configuration du dashboard à partir de {config_file}")
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    # Charger les données
    portfolio = load_portfolio(config['portfolio_file'])
    returns_data = load_returns_data(config['returns_file']) if 'returns_file' in config else None
    
    # Charger les métriques de risque
    risk_metrics = None
    if 'risk_metrics_file' in config:
        with open(config['risk_metrics_file'], 'r') as f:
            risk_metrics = json.load(f)
    
    # Charger les résultats des stress-tests
    stress_test_results = None
    if 'stress_test_results_file' in config:
        with open(config['stress_test_results_file'], 'r') as f:
            stress_test_results = json.load(f)
    
    # Créer le dashboard
    dashboard = RiskDashboard(
        title=config.get('title', "Dashboard de Risque et Performance"),
        portfolio_data=portfolio,
        returns_data=returns_data,
        risk_metrics=risk_metrics,
        scenarios=[result['scenario'] for result in stress_test_results.values()] if stress_test_results else None
    )
    
    return dashboard


def main():
    """
    Fonction principale.
    """
    # Parser les arguments
    args = parse_arguments()
    
    # Vérifier si un fichier de configuration est fourni
    if args.portfolio.endswith(".json") and os.path.basename(args.portfolio).startswith("dashboard_config"):
        dashboard = setup_dashboard_from_config(args.portfolio)
    else:
        # Charger les données
        portfolio = load_portfolio(args.portfolio)
        market_data = load_market_data(args.market_data)
        returns_data = load_returns_data(args.returns_data)
        risk_metrics = load_risk_metrics(args.risk_metrics)
        stress_test_results = load_stress_test_results(args.stress_test_results)
        
        # Créer le dashboard
        dashboard = RiskDashboard(
            title=args.title,
            portfolio_data=portfolio,
            market_data=market_data,
            returns_data=returns_data,
            risk_metrics=risk_metrics,
            scenarios=[result['scenario'] for result in stress_test_results.values()] if stress_test_results else None
        )
    
    # Lancer le serveur Dash
    logger.info(f"Lancement du dashboard sur http://{args.host}:{args.port}")
    dashboard.run_server(debug=args.debug, host=args.host, port=args.port)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution: {e}", exc_info=True)
        sys.exit(1)
