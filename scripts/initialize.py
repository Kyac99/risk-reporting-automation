"""
Script d'initialisation pour configurer l'environnement et charger des données d'exemple.
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import argparse

# Ajouter le répertoire parent au chemin de recherche des modules
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)

# Importer les modules du projet
from src.data_collection.market_data import MarketDataCollector
from src.data_collection.portfolio_data import PortfolioLoader
from src.risk_models.var_model import VaRModel, prepare_returns_data
from src.stress_testing.scenario_generator import ScenarioGenerator

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Définir les chemins des répertoires
DATA_DIR = os.path.join(parent_dir, "data")
PORTFOLIO_DIR = os.path.join(DATA_DIR, "portfolios")
MARKET_DATA_DIR = os.path.join(DATA_DIR, "market_data")
REPORT_DIR = os.path.join(DATA_DIR, "reports")
DASHBOARD_DIR = os.path.join(DATA_DIR, "dashboards")
SCENARIOS_DIR = os.path.join(DATA_DIR, "scenarios")


def create_directories():
    """
    Créer les répertoires nécessaires.
    """
    logger.info("Création des répertoires nécessaires")
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(PORTFOLIO_DIR, exist_ok=True)
    os.makedirs(MARKET_DATA_DIR, exist_ok=True)
    os.makedirs(REPORT_DIR, exist_ok=True)
    os.makedirs(DASHBOARD_DIR, exist_ok=True)
    os.makedirs(SCENARIOS_DIR, exist_ok=True)


def create_sample_portfolio():
    """
    Créer un portefeuille d'exemple.
    """
    logger.info("Création d'un portefeuille d'exemple")
    
    # Exemple de portefeuille diversifié
    portfolio_data = {
        'Security': [
            'Apple Inc.', 'Microsoft Corp.', 'Amazon.com Inc.', 'Alphabet Inc.', 'Meta Platforms Inc.',
            'Tesla Inc.', 'NVIDIA Corp.', 'JPMorgan Chase & Co.', 'Bank of America Corp.', 'Goldman Sachs Group Inc.',
            'Johnson & Johnson', 'Pfizer Inc.', 'Merck & Co. Inc.', 'UnitedHealth Group Inc.', 'Abbott Laboratories',
            'Procter & Gamble Co.', 'Coca-Cola Co.', 'PepsiCo Inc.', 'Walmart Inc.', 'Target Corp.',
            'US Treasury 2Y', 'US Treasury 5Y', 'US Treasury 10Y', 'US Treasury 30Y',
            'Vanguard Real Estate ETF', 'iShares Gold Trust', 'Invesco DB Commodity Index'
        ],
        'Ticker': [
            'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META',
            'TSLA', 'NVDA', 'JPM', 'BAC', 'GS',
            'JNJ', 'PFE', 'MRK', 'UNH', 'ABT',
            'PG', 'KO', 'PEP', 'WMT', 'TGT',
            'UST2Y', 'UST5Y', 'UST10Y', 'UST30Y',
            'VNQ', 'IAU', 'DBC'
        ],
        'Quantity': [
            1000, 500, 100, 150, 400,
            200, 300, 300, 500, 100,
            200, 300, 250, 100, 200,
            150, 300, 200, 150, 200,
            1000, 800, 600, 400,
            500, 800, 400
        ],
        'AssetClass': [
            'Equity', 'Equity', 'Equity', 'Equity', 'Equity',
            'Equity', 'Equity', 'Equity', 'Equity', 'Equity',
            'Equity', 'Equity', 'Equity', 'Equity', 'Equity',
            'Equity', 'Equity', 'Equity', 'Equity', 'Equity',
            'Fixed Income', 'Fixed Income', 'Fixed Income', 'Fixed Income',
            'Real Estate', 'Commodity', 'Commodity'
        ],
        'Sector': [
            'Technology', 'Technology', 'Consumer Discretionary', 'Communication Services', 'Communication Services',
            'Consumer Discretionary', 'Technology', 'Financials', 'Financials', 'Financials',
            'Healthcare', 'Healthcare', 'Healthcare', 'Healthcare', 'Healthcare',
            'Consumer Staples', 'Consumer Staples', 'Consumer Staples', 'Consumer Staples', 'Consumer Staples',
            'Government', 'Government', 'Government', 'Government',
            'Real Estate', 'Commodities', 'Commodities'
        ],
        'Currency': [
            'USD', 'USD', 'USD', 'USD', 'USD',
            'USD', 'USD', 'USD', 'USD', 'USD',
            'USD', 'USD', 'USD', 'USD', 'USD',
            'USD', 'USD', 'USD', 'USD', 'USD',
            'USD', 'USD', 'USD', 'USD',
            'USD', 'USD', 'USD'
        ],
        'Price': [
            180.95, 420.20, 178.15, 149.00, 494.82,
            177.0, 925.11, 198.48, 39.23, 471.18,
            152.50, 27.59, 125.46, 490.34, 113.33,
            165.05, 60.71, 173.40, 60.71, 167.48,
            97.50, 95.20, 92.10, 87.50,
            84.51, 43.62, 13.45
        ]
    }
    
    # Calculer la valeur de marché et le poids de chaque position
    portfolio_data['MarketValue'] = [
        portfolio_data['Price'][i] * portfolio_data['Quantity'][i]
        for i in range(len(portfolio_data['Security']))
    ]
    
    total_value = sum(portfolio_data['MarketValue'])
    portfolio_data['Weight'] = [
        value / total_value
        for value in portfolio_data['MarketValue']
    ]
    
    # Créer un DataFrame
    portfolio = pd.DataFrame(portfolio_data)
    
    # Sauvegarder le portefeuille
    portfolio_file = os.path.join(PORTFOLIO_DIR, "example_portfolio.csv")
    portfolio.to_csv(portfolio_file, index=False)
    
    # Sauvegarder également au format parquet
    portfolio_file_parquet = os.path.join(PORTFOLIO_DIR, "example_portfolio.parquet")
    portfolio.to_parquet(portfolio_file_parquet, index=False)
    
    logger.info(f"Portefeuille d'exemple sauvegardé dans {portfolio_file}")
    logger.info(f"Portefeuille d'exemple (parquet) sauvegardé dans {portfolio_file_parquet}")
    
    return portfolio_file


def collect_sample_market_data():
    """
    Collecter des données de marché d'exemple.
    """
    logger.info("Collecte de données de marché d'exemple")
    
    # Créer une instance du collecteur de données
    collector = MarketDataCollector(cache_dir=MARKET_DATA_DIR)
    
    # Définir les tickers pour lesquels collecter des données
    equity_tickers = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'TSLA', 'NVDA', 'JPM', 'BAC', 'GS',
                     'JNJ', 'PFE', 'MRK', 'UNH', 'ABT', 'PG', 'KO', 'PEP', 'WMT', 'TGT']
    
    # Définir la période de collecte (3 ans en arrière)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365*3)
    
    # Collecter les données d'actions
    logger.info(f"Collecte des données pour {len(equity_tickers)} tickers")
    try:
        stock_data = collector.get_stock_data(equity_tickers, start_date, end_date)
        
        # Sauvegarder les données de marché
        stock_data_file = os.path.join(MARKET_DATA_DIR, f"stock_data_sample.parquet")
        stock_data.to_parquet(stock_data_file, index=False)
        logger.info(f"Données d'actions sauvegardées dans {stock_data_file}")
        
        # Collecter les données économiques
        economic_indicators = ['GDP', 'UNRATE', 'CPIAUCSL', 'FEDFUNDS']
        economic_data = collector.get_economic_data(economic_indicators, start_date, end_date)
        
        economic_data_file = os.path.join(MARKET_DATA_DIR, f"economic_data_sample.parquet")
        if not economic_data.empty:
            economic_data.to_parquet(economic_data_file, index=False)
            logger.info(f"Données économiques sauvegardées dans {economic_data_file}")
        
        # Collecter les taux de change
        currencies = ['EUR', 'GBP', 'JPY', 'CAD', 'AUD']
        fx_data = collector.get_fx_rates(currencies, 'USD', start_date, end_date)
        
        fx_data_file = os.path.join(MARKET_DATA_DIR, f"fx_data_sample.parquet")
        if fx_data is not None and not fx_data.empty:
            fx_data.to_parquet(fx_data_file, index=False)
            logger.info(f"Données de taux de change sauvegardées dans {fx_data_file}")
        
        # Préparer les données de rendements
        returns_data = prepare_returns_data(
            stock_data, date_column='Date', price_column='Close', ticker_column='Ticker', method='log'
        )
        
        returns_file = os.path.join(MARKET_DATA_DIR, f"returns_data_sample.parquet")
        returns_data.to_parquet(returns_file)
        logger.info(f"Données de rendements sauvegardées dans {returns_file}")
        
        return stock_data_file, returns_file
    
    except Exception as e:
        logger.error(f"Erreur lors de la collecte des données de marché: {e}")
        # Si la collecte échoue, créer des données simulées
        return generate_simulated_market_data()


def generate_simulated_market_data():
    """
    Générer des données de marché simulées si la collecte échoue.
    """
    logger.info("Génération de données de marché simulées")
    
    # Définir les tickers et les dates
    equity_tickers = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'TSLA', 'NVDA', 'JPM', 'BAC', 'GS',
                     'JNJ', 'PFE', 'MRK', 'UNH', 'ABT', 'PG', 'KO', 'PEP', 'WMT', 'TGT']
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365*3)
    dates = pd.date_range(start=start_date, end=end_date, freq='B')  # Jours ouvrables
    
    # Générer des données pour chaque ticker
    all_data = []
    
    for ticker in equity_tickers:
        # Simuler un prix de départ entre 50 et 500
        start_price = np.random.uniform(50, 500)
        
        # Simuler une volatilité entre 0.1 et 0.5 annualisée
        annual_volatility = np.random.uniform(0.1, 0.5)
        daily_volatility = annual_volatility / np.sqrt(252)
        
        # Simuler un drift entre -0.1 et 0.3 annualisé
        annual_drift = np.random.uniform(-0.1, 0.3)
        daily_drift = annual_drift / 252
        
        # Simuler une marche aléatoire pour les prix
        np.random.seed(hash(ticker) % 2**32)  # Différente seed pour chaque ticker
        returns = np.random.normal(daily_drift, daily_volatility, len(dates))
        log_returns = np.cumsum(returns)
        prices = start_price * np.exp(log_returns)
        
        # Créer un DataFrame pour ce ticker
        ticker_data = pd.DataFrame({
            'Date': dates,
            'Ticker': ticker,
            'Open': prices * np.random.uniform(0.99, 1.0, len(dates)),
            'High': prices * np.random.uniform(1.0, 1.02, len(dates)),
            'Low': prices * np.random.uniform(0.98, 1.0, len(dates)),
            'Close': prices,
            'Volume': np.random.randint(1000000, 10000000, len(dates))
        })
        
        all_data.append(ticker_data)
    
    # Combiner tous les données
    stock_data = pd.concat(all_data, ignore_index=True)
    
    # Sauvegarder les données simulées
    stock_data_file = os.path.join(MARKET_DATA_DIR, f"stock_data_simulated.parquet")
    stock_data.to_parquet(stock_data_file, index=False)
    logger.info(f"Données d'actions simulées sauvegardées dans {stock_data_file}")
    
    # Préparer les données de rendements
    returns_data = prepare_returns_data(
        stock_data, date_column='Date', price_column='Close', ticker_column='Ticker', method='log'
    )
    
    returns_file = os.path.join(MARKET_DATA_DIR, f"returns_data_simulated.parquet")
    returns_data.to_parquet(returns_file)
    logger.info(f"Données de rendements simulées sauvegardées dans {returns_file}")
    
    return stock_data_file, returns_file


def create_sample_risk_metrics(portfolio_file, returns_file):
    """
    Créer des métriques de risque d'exemple.
    """
    logger.info("Création de métriques de risque d'exemple")
    
    try:
        # Charger le portefeuille et les rendements
        if portfolio_file.endswith('.csv'):
            portfolio = pd.read_csv(portfolio_file)
        else:
            portfolio = pd.read_parquet(portfolio_file)
        
        returns_data = pd.read_parquet(returns_file)
        
        # Extraire les poids du portefeuille
        weights = portfolio['Weight'].values
        
        # S'assurer que les rendements correspondent aux actifs du portefeuille
        portfolio_tickers = set(portfolio['Ticker'].unique())
        returns_tickers = set(returns_data.columns)
        common_tickers = portfolio_tickers.intersection(returns_tickers)
        
        if len(common_tickers) < len(portfolio_tickers):
            logger.warning(f"Certains tickers du portefeuille n'ont pas de données de rendements: {portfolio_tickers - common_tickers}")
        
        # Filtrer les rendements et les poids pour ne garder que les actifs communs
        filtered_returns = returns_data[list(common_tickers)]
        
        # Calculer les poids normalisés pour les actifs communs
        filtered_weights = np.zeros(len(common_tickers))
        for i, ticker in enumerate(common_tickers):
            ticker_weight = portfolio.loc[portfolio['Ticker'] == ticker, 'Weight'].sum()
            filtered_weights[i] = ticker_weight
        
        # Normaliser les poids pour qu'ils somment à 1
        filtered_weights = filtered_weights / filtered_weights.sum()
        
        # Initialiser le modèle VaR
        var_model = VaRModel(filtered_returns)
        
        # Calculer les différentes métriques de risque
        risk_metrics = {}
        
        # Calculer la VaR avec différentes méthodes et niveaux de confiance
        for method in ['historical', 'parametric', 'monte_carlo']:
            risk_metrics[method] = {}
            for confidence_level in [0.95, 0.99]:
                for time_horizon in [1, 5, 20]:
                    key = f"var_{confidence_level}_{time_horizon}d"
                    
                    if method == 'historical':
                        var, cvar = var_model.calculate_historical_var(
                            filtered_weights, confidence_level, time_horizon
                        )
                    elif method == 'parametric':
                        var, cvar = var_model.calculate_parametric_var(
                            filtered_weights, confidence_level, time_horizon
                        )
                    else:  # monte_carlo
                        var, cvar = var_model.calculate_monte_carlo_var(
                            filtered_weights, confidence_level, time_horizon, num_simulations=5000
                        )
                    
                    risk_metrics[method][key] = {
                        'var': float(var),
                        'cvar': float(cvar)
                    }
        
        # Calculer les contributions à la VaR
        try:
            component_var = var_model.calculate_component_var(filtered_weights, 0.95, 1)
            risk_metrics['component_var'] = component_var.to_dict()
        except Exception as e:
            logger.warning(f"Erreur lors du calcul des contributions à la VaR: {e}")
        
        # Calculer la VaR incrémentale
        try:
            incremental_var = var_model.calculate_incremental_var(filtered_weights, 0.95, 1)
            risk_metrics['incremental_var'] = incremental_var.to_dict()
        except Exception as e:
            logger.warning(f"Erreur lors du calcul de la VaR incrémentale: {e}")
        
        # Enregistrer les métriques de risque
        risk_metrics_file = os.path.join(REPORT_DIR, f"risk_metrics_sample.json")
        
        with open(risk_metrics_file, 'w') as f:
            json.dump(risk_metrics, f, indent=4, default=str)
        
        logger.info(f"Métriques de risque sauvegardées dans {risk_metrics_file}")
        
        return risk_metrics_file
    
    except Exception as e:
        logger.error(f"Erreur lors de la création des métriques de risque: {e}")
        return None


def create_sample_stress_tests(portfolio_file):
    """
    Créer des stress-tests d'exemple.
    """
    logger.info("Création de stress-tests d'exemple")
    
    try:
        # Charger le portefeuille
        if portfolio_file.endswith('.csv'):
            portfolio = pd.read_csv(portfolio_file)
        else:
            portfolio = pd.read_parquet(portfolio_file)
        
        # Initialiser le générateur de scénarios
        scenario_generator = ScenarioGenerator(scenarios_dir=SCENARIOS_DIR)
        
        # Définir les scénarios à exécuter
        scenarios = ['financial_crisis_2008', 'rate_shock', 'inflation_shock', 'liquidity_crisis', 'geopolitical_crisis']
        
        # Dictionnaire pour stocker les résultats des stress-tests
        stress_test_results = {}
        
        # Exécuter les stress-tests pour chaque scénario
        for scenario_name in scenarios:
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
                'scenario': scenario,
                'original_value': float(original_value),
                'stressed_value': float(stressed_value),
                'impact_value': float(impact_value),
                'impact_percentage': float(impact_percentage),
                'stressed_portfolio': stressed_portfolio.to_dict()
            }
            
            # Sauvegarder le portefeuille stressé
            stressed_file = os.path.join(
                PORTFOLIO_DIR, 
                f"stressed_portfolio_{scenario_name}_sample.parquet"
            )
            stressed_portfolio.to_parquet(stressed_file, index=False)
        
        # Créer un scénario personnalisé
        custom_scenario = scenario_generator.create_custom_scenario(
            name="custom_scenario_sample",
            description="Scénario personnalisé d'exemple",
            shocks={
                'equity': -0.15,
                'interest_rate': 0.01,
                'credit_spread': 0.005,
                'volatility': 0.10,
                'fx': {
                    'EUR': -0.05,
                    'GBP': -0.08,
                    'JPY': 0.03
                }
            },
            save=True
        )
        
        # Appliquer le scénario personnalisé
        stressed_portfolio_custom = apply_scenario_to_portfolio(portfolio, custom_scenario)
        
        # Calculer l'impact du scénario personnalisé
        original_value = portfolio['MarketValue'].sum()
        stressed_value = stressed_portfolio_custom['MarketValue'].sum()
        impact_value = stressed_value - original_value
        impact_percentage = impact_value / original_value
        
        # Stocker les résultats du scénario personnalisé
        stress_test_results['custom_scenario_sample'] = {
            'scenario': custom_scenario,
            'original_value': float(original_value),
            'stressed_value': float(stressed_value),
            'impact_value': float(impact_value),
            'impact_percentage': float(impact_percentage),
            'stressed_portfolio': stressed_portfolio_custom.to_dict()
        }
        
        # Sauvegarder le portefeuille stressé pour le scénario personnalisé
        stressed_file_custom = os.path.join(
            PORTFOLIO_DIR, 
            f"stressed_portfolio_custom_scenario_sample.parquet"
        )
        stressed_portfolio_custom.to_parquet(stressed_file_custom, index=False)
        
        # Enregistrer les résultats des stress-tests
        stress_test_results_file = os.path.join(REPORT_DIR, f"stress_test_results_sample.json")
        
        with open(stress_test_results_file, 'w') as f:
            # Utiliser un convertisseur pour gérer les types non sérialisables
            json.dump(stress_test_results, f, indent=4, default=str)
        
        logger.info(f"Résultats des stress-tests sauvegardés dans {stress_test_results_file}")
        
        return stress_test_results_file
    
    except Exception as e:
        logger.error(f"Erreur lors de la création des stress-tests: {e}")
        return None


def create_sample_report(portfolio_file):
    """
    Créer un rapport d'exemple.
    """
    logger.info("Création d'un rapport d'exemple")
    
    try:
        # Charger le portefeuille
        if portfolio_file.endswith('.csv'):
            portfolio = pd.read_csv(portfolio_file)
        else:
            portfolio = pd.read_parquet(portfolio_file)
        
        # Générer un rapport simple
        report_file = os.path.join(REPORT_DIR, f"risk_report_sample.html")
        
        with open(report_file, 'w') as f:
            f.write("<!DOCTYPE html>\n")
            f.write("<html>\n")
            f.write("<head>\n")
            f.write("    <title>Rapport de Risque - Exemple</title>\n")
            f.write("    <style>\n")
            f.write("        body { font-family: Arial, sans-serif; margin: 20px; }\n")
            f.write("        h1 { color: #2c3e50; }\n")
            f.write("        h2 { color: #3498db; }\n")
            f.write("        table { border-collapse: collapse; width: 100%; }\n")
            f.write("        th, td { text-align: left; padding: 8px; border: 1px solid #ddd; }\n")
            f.write("        th { background-color: #f2f2f2; }\n")
            f.write("        tr:nth-child(even) { background-color: #f9f9f9; }\n")
            f.write("        .negative { color: red; }\n")
            f.write("        .positive { color: green; }\n")
            f.write("    </style>\n")
            f.write("</head>\n")
            f.write("<body>\n")
            
            # En-tête du rapport
            f.write(f"<h1>Rapport de Risque - Exemple</h1>\n")
            f.write(f"<p>Date du rapport: {datetime.now().strftime('%d/%m/%Y')}</p>\n")
            
            # Résumé du portefeuille
            f.write("<h2>Résumé du Portefeuille</h2>\n")
            f.write("<table>\n")
            f.write("    <tr><th>Métrique</th><th>Valeur</th></tr>\n")
            f.write(f"    <tr><td>Valeur Totale</td><td>{portfolio['MarketValue'].sum():,.2f}</td></tr>\n")
            f.write(f"    <tr><td>Nombre d'Actifs</td><td>{len(portfolio)}</td></tr>\n")
            
            asset_classes = portfolio['AssetClass'].unique()
            asset_classes_str = ", ".join(asset_classes)
            f.write(f"    <tr><td>Classes d'Actifs</td><td>{asset_classes_str}</td></tr>\n")
            
            if 'Currency' in portfolio.columns:
                currencies = portfolio['Currency'].unique()
                currencies_str = ", ".join(currencies)
                f.write(f"    <tr><td>Devises</td><td>{currencies_str}</td></tr>\n")
            
            f.write("</table>\n")
            
            # Répartition par classe d'actifs
            f.write("<h2>Répartition par Classe d'Actifs</h2>\n")
            asset_allocation = portfolio.groupby('AssetClass')['MarketValue'].sum().reset_index()
            asset_allocation['Pourcentage'] = asset_allocation['MarketValue'] / portfolio['MarketValue'].sum() * 100
            
            f.write("<table>\n")
            f.write("    <tr><th>Classe d'Actifs</th><th>Valeur</th><th>Pourcentage</th></tr>\n")
            
            for _, row in asset_allocation.iterrows():
                f.write(f"    <tr>\n")
                f.write(f"        <td>{row['AssetClass']}</td>\n")
                f.write(f"        <td>{row['MarketValue']:,.2f}</td>\n")
                f.write(f"        <td>{row['Pourcentage']:.2f}%</td>\n")
                f.write(f"    </tr>\n")
            
            f.write("</table>\n")
            
            # Principales positions
            f.write("<h2>Principales Positions</h2>\n")
            top_positions = portfolio.nlargest(10, 'MarketValue')
            
            f.write("<table>\n")
            f.write("    <tr><th>Security</th><th>Ticker</th><th>Valeur</th><th>Poids</th></tr>\n")
            
            for _, row in top_positions.iterrows():
                f.write(f"    <tr>\n")
                f.write(f"        <td>{row['Security']}</td>\n")
                f.write(f"        <td>{row['Ticker']}</td>\n")
                f.write(f"        <td>{row['MarketValue']:,.2f}</td>\n")
                f.write(f"        <td>{row['Weight']*100:.2f}%</td>\n")
                f.write(f"    </tr>\n")
            
            f.write("</table>\n")
            
            # Pied de page
            f.write("<p><i>Ce rapport a été généré automatiquement.</i></p>\n")
            
            f.write("</body>\n")
            f.write("</html>\n")
        
        logger.info(f"Rapport d'exemple sauvegardé dans {report_file}")
        
        return report_file
    
    except Exception as e:
        logger.error(f"Erreur lors de la création du rapport d'exemple: {e}")
        return None


def create_sample_dashboard_config(portfolio_file, returns_file, risk_metrics_file, stress_test_results_file):
    """
    Créer une configuration de dashboard d'exemple.
    """
    logger.info("Création d'une configuration de dashboard d'exemple")
    
    try:
        # Générer une configuration pour le dashboard
        dashboard_config = {
            "title": "Dashboard de Risque - Exemple",
            "portfolio_file": portfolio_file,
            "returns_file": returns_file,
            "risk_metrics_file": risk_metrics_file,
            "stress_test_results_file": stress_test_results_file,
            "created_at": datetime.now().isoformat()
        }
        
        # Enregistrer la configuration
        dashboard_config_file = os.path.join(DASHBOARD_DIR, "dashboard_config_sample.json")
        
        with open(dashboard_config_file, 'w') as f:
            json.dump(dashboard_config, f, indent=4)
        
        logger.info(f"Configuration de dashboard d'exemple sauvegardée dans {dashboard_config_file}")
        
        return dashboard_config_file
    
    except Exception as e:
        logger.error(f"Erreur lors de la création de la configuration de dashboard: {e}")
        return None


def main():
    """
    Fonction principale.
    """
    parser = argparse.ArgumentParser(description="Initialisation de l'environnement pour l'automatisation du reporting de risque")
    parser.add_argument('--skip-market-data', action='store_true', help="Ignorer la collecte des données de marché")
    args = parser.parse_args()
    
    logger.info("Début de l'initialisation de l'environnement")
    
    # Créer les répertoires nécessaires
    create_directories()
    
    # Créer un portefeuille d'exemple
    portfolio_file = create_sample_portfolio()
    
    # Collecter ou générer des données de marché
    if args.skip_market_data:
        # Générer des données simulées
        stock_data_file, returns_file = generate_simulated_market_data()
    else:
        # Collecter des données réelles (ou simulées si la collecte échoue)
        try:
            stock_data_file, returns_file = collect_sample_market_data()
        except Exception as e:
            logger.error(f"Erreur lors de la collecte des données de marché: {e}")
            logger.info("Génération de données simulées à la place")
            stock_data_file, returns_file = generate_simulated_market_data()
    
    # Créer des métriques de risque d'exemple
    risk_metrics_file = create_sample_risk_metrics(portfolio_file, returns_file)
    
    # Créer des stress-tests d'exemple
    stress_test_results_file = create_sample_stress_tests(portfolio_file)
    
    # Créer un rapport d'exemple
    report_file = create_sample_report(portfolio_file)
    
    # Créer une configuration de dashboard d'exemple
    dashboard_config_file = create_sample_dashboard_config(
        portfolio_file, returns_file, risk_metrics_file, stress_test_results_file
    )
    
    logger.info("Initialisation de l'environnement terminée")
    
    # Afficher un résumé
    print("\n=== Résumé de l'initialisation ===")
    print(f"Portefeuille d'exemple: {portfolio_file}")
    print(f"Données de marché: {stock_data_file}")
    print(f"Données de rendements: {returns_file}")
    print(f"Métriques de risque: {risk_metrics_file}")
    print(f"Résultats des stress-tests: {stress_test_results_file}")
    print(f"Rapport d'exemple: {report_file}")
    print(f"Configuration de dashboard: {dashboard_config_file}")
    print("\nPour lancer l'API REST:")
    print("python -m src.api.app")
    print("\nPour lancer le dashboard:")
    print("python -m src.visualization.risk_dashboard")


if __name__ == "__main__":
    main()
