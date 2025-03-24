#!/usr/bin/env python
"""
Script pour exécuter manuellement le pipeline d'analyse de risque.
"""

import sys
import os
import argparse
import logging
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta

# Ajouter le répertoire parent au chemin d'importation
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Importer les modules du projet
from src.data_collection.market_data import MarketDataCollector
from src.data_collection.portfolio_data import PortfolioLoader
from src.risk_models.var_model import VaRModel, prepare_returns_data
from src.stress_testing.scenario_generator import ScenarioGenerator, apply_scenario_to_portfolio

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Définir les chemins des données
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(PROJECT_DIR, "data")
OUTPUT_DIR = os.path.join(DATA_DIR, "reports")
MARKET_DATA_DIR = os.path.join(DATA_DIR, "market_data")

# Créer les répertoires nécessaires s'ils n'existent pas
os.makedirs(os.path.join(DATA_DIR, "portfolios"), exist_ok=True)
os.makedirs(MARKET_DATA_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.join(DATA_DIR, "scenarios"), exist_ok=True)


def parse_arguments():
    """
    Parser les arguments de ligne de commande.
    """
    parser = argparse.ArgumentParser(description="Analyser le risque d'un portefeuille")
    
    parser.add_argument(
        "--portfolio",
        type=str,
        default=os.path.join(DATA_DIR, "portfolios", "example_portfolio.csv"),
        help="Chemin vers le fichier de portefeuille"
    )
    
    parser.add_argument(
        "--start_date",
        type=str,
        default=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
        help="Date de début pour les données de marché (format: YYYY-MM-DD)"
    )
    
    parser.add_argument(
        "--end_date",
        type=str,
        default=datetime.now().strftime("%Y-%m-%d"),
        help="Date de fin pour les données de marché (format: YYYY-MM-DD)"
    )
    
    parser.add_argument(
        "--confidence_level",
        type=float,
        default=0.95,
        help="Niveau de confiance pour la VaR (entre 0 et 1)"
    )
    
    parser.add_argument(
        "--time_horizon",
        type=int,
        default=1,
        help="Horizon temporel pour la VaR (en jours)"
    )
    
    parser.add_argument(
        "--var_method",
        type=str,
        choices=["historical", "parametric", "monte_carlo"],
        default="historical",
        help="Méthode de calcul de la VaR"
    )
    
    parser.add_argument(
        "--scenarios",
        type=str,
        nargs='+',
        default=["financial_crisis_2008", "rate_shock"],
        help="Liste des scénarios de stress-test à exécuter"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default=os.path.join(OUTPUT_DIR, f"risk_report_{datetime.now().strftime('%Y%m%d')}.json"),
        help="Chemin vers le fichier de sortie"
    )
    
    return parser.parse_args()


def load_portfolio(portfolio_file):
    """
    Charger le portefeuille.
    """
    logger.info(f"Chargement du portefeuille depuis {portfolio_file}")
    
    loader = PortfolioLoader()
    
    if portfolio_file.endswith(".csv"):
        portfolio = loader.load_portfolio_from_csv(portfolio_file)
    elif portfolio_file.endswith(".xlsx") or portfolio_file.endswith(".xls"):
        portfolio = loader.load_portfolio_from_excel(portfolio_file)
    elif portfolio_file.endswith(".json"):
        portfolio = loader.load_portfolio_from_json(portfolio_file)
    else:
        raise ValueError(f"Format de fichier non pris en charge: {portfolio_file}")
    
    return portfolio


def collect_market_data(portfolio, start_date, end_date):
    """
    Collecter les données de marché pour les tickers du portefeuille.
    """
    logger.info("Collecte des données de marché")
    
    # Extraire les tickers du portefeuille
    tickers = portfolio['Ticker'].unique().tolist()
    
    # Créer une instance du collecteur de données
    collector = MarketDataCollector(cache_dir=MARKET_DATA_DIR)
    
    # Collecter les données d'actions
    logger.info(f"Collecte des données pour {len(tickers)} tickers")
    stock_data = collector.get_stock_data(tickers, start_date, end_date)
    
    # Extraire les devises du portefeuille
    currencies = []
    if 'Currency' in portfolio.columns:
        currencies = portfolio['Currency'].unique().tolist()
        # Filtrer la devise de base (USD) si présente
        if 'USD' in currencies:
            currencies.remove('USD')
    
    # Collecter les taux de change si nécessaire
    fx_data = None
    if currencies:
        logger.info(f"Collecte des taux de change pour {len(currencies)} devises")
        fx_data = collector.get_fx_rates(currencies, 'USD', start_date, end_date)
    
    return stock_data, fx_data


def enrich_portfolio(portfolio, market_data):
    """
    Enrichir le portefeuille avec les données de marché.
    """
    logger.info("Enrichissement du portefeuille avec les données de marché")
    
    loader = PortfolioLoader()
    enriched_portfolio = loader.enrich_portfolio_with_market_data(
        portfolio, market_data, date_column='Date', price_column='Close', ticker_column='Ticker'
    )
    
    return enriched_portfolio


def calculate_risk_metrics(portfolio, market_data, confidence_level, time_horizon, var_method):
    """
    Calculer les métriques de risque pour le portefeuille.
    """
    logger.info("Calcul des métriques de risque")
    
    # Préparer les données de rendements
    returns_data = prepare_returns_data(
        market_data, date_column='Date', price_column='Close', ticker_column='Ticker', method='log'
    )
    
    # Extraire les poids du portefeuille
    if 'Weight' in portfolio.columns:
        weights = portfolio['Weight'].values
    else:
        # Calculer les poids à partir des valeurs de marché
        if 'MarketValue' in portfolio.columns:
            total_value = portfolio['MarketValue'].sum()
            weights = portfolio['MarketValue'] / total_value
        else:
            raise ValueError("Le portefeuille ne contient pas les poids ni les valeurs de marché")
    
    # Initialiser le modèle VaR
    var_model = VaRModel(returns_data)
    
    # Calculer la VaR
    if var_method == 'historical':
        var, cvar = var_model.calculate_historical_var(weights, confidence_level, time_horizon)
    elif var_method == 'parametric':
        var, cvar = var_model.calculate_parametric_var(weights, confidence_level, time_horizon)
    else:  # monte_carlo
        var, cvar = var_model.calculate_monte_carlo_var(
            weights, confidence_level, time_horizon, num_simulations=10000
        )
    
    # Calculer les contributions à la VaR
    component_var = var_model.calculate_component_var(weights, confidence_level, time_horizon)
    
    # Calculer la VaR incrémentale
    incremental_var = var_model.calculate_incremental_var(weights, confidence_level, time_horizon)
    
    risk_metrics = {
        'var': float(var),
        'cvar': float(cvar),
        'method': var_method,
        'confidence_level': confidence_level,
        'time_horizon': time_horizon,
        'component_var': component_var.to_dict(),
        'incremental_var': incremental_var.to_dict()
    }
    
    return risk_metrics, returns_data


def run_stress_tests(portfolio, scenarios):
    """
    Exécuter des stress-tests sur le portefeuille.
    """
    logger.info("Exécution des stress-tests")
    
    # Initialiser le générateur de scénarios
    scenario_generator = ScenarioGenerator(scenarios_dir=os.path.join(DATA_DIR, "scenarios"))
    
    # Dictionnaire pour stocker les résultats des stress-tests
    stress_test_results = {}
    
    # Exécuter les stress-tests pour chaque scénario
    for scenario_name in scenarios:
        logger.info(f"Exécution du scénario: {scenario_name}")
        
        # Récupérer le scénario
        scenario = scenario_generator.get_predefined_scenario(scenario_name)
        
        # Appliquer le scénario au portefeuille
        stressed_portfolio = apply_scenario_to_portfolio(portfolio, scenario)
        
        # Calculer l'impact du scénario
        original_value = portfolio['MarketValue'].sum()
        stressed_value = stressed_portfolio['MarketValue'].sum()
        impact_value = stressed_value - original_value
        impact_percentage = impact_value / original_value
        
        # Stocker les résultats
        stress_test_results[scenario_name] = {
            'name': scenario_name,
            'description': scenario['description'],
            'original_value': float(original_value),
            'stressed_value': float(stressed_value),
            'impact_value': float(impact_value),
            'impact_percentage': float(impact_percentage)
        }
    
    return stress_test_results


def generate_report(portfolio, risk_metrics, stress_test_results, output_file):
    """
    Générer un rapport d'analyse de risque.
    """
    logger.info("Génération du rapport d'analyse de risque")
    
    # Créer le rapport
    report = {
        'timestamp': datetime.now().isoformat(),
        'portfolio_summary': {
            'total_value': float(portfolio['MarketValue'].sum()),
            'num_assets': len(portfolio),
            'asset_classes': portfolio['AssetClass'].unique().tolist(),
            'currencies': portfolio['Currency'].unique().tolist() if 'Currency' in portfolio.columns else []
        },
        'risk_metrics': risk_metrics,
        'stress_test_results': stress_test_results
    }
    
    # Créer le répertoire de sortie s'il n'existe pas
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Enregistrer le rapport
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=4)
    
    logger.info(f"Rapport sauvegardé dans {output_file}")
    
    return report


def main():
    """
    Fonction principale.
    """
    # Parser les arguments
    args = parse_arguments()
    
    # Charger le portefeuille
    portfolio = load_portfolio(args.portfolio)
    
    # Collecter les données de marché
    market_data, fx_data = collect_market_data(portfolio, args.start_date, args.end_date)
    
    # Enrichir le portefeuille avec les données de marché
    enriched_portfolio = enrich_portfolio(portfolio, market_data)
    
    # Calculer les métriques de risque
    risk_metrics, returns_data = calculate_risk_metrics(
        enriched_portfolio, market_data, args.confidence_level, args.time_horizon, args.var_method
    )
    
    # Exécuter les stress-tests
    stress_test_results = run_stress_tests(enriched_portfolio, args.scenarios)
    
    # Générer le rapport
    report = generate_report(enriched_portfolio, risk_metrics, stress_test_results, args.output)
    
    return report


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution: {e}", exc_info=True)
        sys.exit(1)
