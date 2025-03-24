"""
DAG Airflow pour l'automatisation du reporting de risque.
"""

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from airflow.operators.email_operator import EmailOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta

import sys
import os
import pandas as pd
import numpy as np
import json
import logging
from typing import Dict, List, Any

# Définir le chemin vers le répertoire du projet
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_DIR)

# Importer les modules du projet
from src.data_collection.market_data import MarketDataCollector
from src.data_collection.portfolio_data import PortfolioLoader
from src.risk_models.var_model import VaRModel, prepare_returns_data
from src.stress_testing.scenario_generator import ScenarioGenerator, apply_scenario_to_portfolio
from src.visualization.risk_dashboard import RiskDashboard

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Définir les arguments par défaut pour le DAG
default_args = {
    'owner': 'risk_team',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email': ['risk_team@example.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Créer le DAG
dag = DAG(
    'risk_reporting_pipeline',
    default_args=default_args,
    description='Pipeline d\'automatisation du reporting de risque',
    schedule_interval='0 8 * * 1-5',  # Exécution tous les jours ouvrables à 8h
    catchup=False,
    tags=['risk', 'reporting', 'finance']
)

# Définir les chemins des données
DATA_DIR = os.path.join(PROJECT_DIR, "data")
PORTFOLIO_FILE = os.path.join(DATA_DIR, "portfolios", "current_portfolio.csv")
MARKET_DATA_DIR = os.path.join(DATA_DIR, "market_data")
REPORT_DIR = os.path.join(DATA_DIR, "reports")
DASHBOARD_DIR = os.path.join(DATA_DIR, "dashboards")

# Créer les répertoires nécessaires s'ils n'existent pas
os.makedirs(os.path.join(DATA_DIR, "portfolios"), exist_ok=True)
os.makedirs(MARKET_DATA_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs(DASHBOARD_DIR, exist_ok=True)
os.makedirs(os.path.join(DATA_DIR, "scenarios"), exist_ok=True)


def collect_market_data(**kwargs):
    """
    Collecter les données de marché.
    """
    logger.info("Début de la collecte des données de marché")
    
    # Créer une instance du collecteur de données
    collector = MarketDataCollector(cache_dir=MARKET_DATA_DIR)
    
    # Charger le portefeuille actuel pour extraire les tickers
    loader = PortfolioLoader()
    portfolio = loader.load_portfolio_from_csv(PORTFOLIO_FILE)
    
    # Extraire les tickers du portefeuille
    tickers = portfolio['Ticker'].unique().tolist()
    
    # Définir la période de collecte (1 an en arrière)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    # Collecter les données d'actions
    logger.info(f"Collecte des données pour {len(tickers)} tickers")
    stock_data = collector.get_stock_data(tickers, start_date, end_date)
    
    # Collecter les données économiques
    economic_indicators = ['GDP', 'UNRATE', 'CPIAUCSL', 'FEDFUNDS']
    economic_data = collector.get_economic_data(economic_indicators, start_date, end_date)
    
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
    
    # Sauvegarder les données de marché
    market_data_files = {}
    
    stock_data_file = os.path.join(MARKET_DATA_DIR, f"stock_data_{end_date.strftime('%Y%m%d')}.parquet")
    stock_data.to_parquet(stock_data_file, index=False)
    market_data_files['stock_data'] = stock_data_file
    
    economic_data_file = os.path.join(MARKET_DATA_DIR, f"economic_data_{end_date.strftime('%Y%m%d')}.parquet")
    economic_data.to_parquet(economic_data_file, index=False)
    market_data_files['economic_data'] = economic_data_file
    
    if fx_data is not None:
        fx_data_file = os.path.join(MARKET_DATA_DIR, f"fx_data_{end_date.strftime('%Y%m%d')}.parquet")
        fx_data.to_parquet(fx_data_file, index=False)
        market_data_files['fx_data'] = fx_data_file
    
    # Passer les chemins de fichiers à la tâche suivante
    kwargs['ti'].xcom_push(key='market_data_files', value=market_data_files)
    logger.info("Collecte des données de marché terminée")


def process_portfolio(**kwargs):
    """
    Traiter les données du portefeuille et les enrichir avec les données de marché.
    """
    logger.info("Début du traitement du portefeuille")
    
    # Récupérer les chemins des fichiers de données de marché
    market_data_files = kwargs['ti'].xcom_pull(task_ids='collect_market_data', key='market_data_files')
    
    # Charger les données de marché
    stock_data = pd.read_parquet(market_data_files['stock_data'])
    
    # Charger le portefeuille
    loader = PortfolioLoader()
    portfolio = loader.load_portfolio_from_csv(PORTFOLIO_FILE)
    
    # Enrichir le portefeuille avec les données de marché
    enriched_portfolio = loader.enrich_portfolio_with_market_data(
        portfolio, stock_data, date_column='Date', price_column='Close', ticker_column='Ticker'
    )
    
    # Sauvegarder le portefeuille enrichi
    enriched_file = os.path.join(
        DATA_DIR, "portfolios", 
        f"enriched_portfolio_{datetime.now().strftime('%Y%m%d')}.parquet"
    )
    enriched_portfolio.to_parquet(enriched_file, index=False)
    
    # Préparer les données de rendements pour l'analyse de risque
    returns_data = prepare_returns_data(
        stock_data, date_column='Date', price_column='Close', ticker_column='Ticker', method='log'
    )
    
    returns_file = os.path.join(
        DATA_DIR, "market_data", 
        f"returns_data_{datetime.now().strftime('%Y%m%d')}.parquet"
    )
    returns_data.to_parquet(returns_file)
    
    # Passer les chemins de fichiers à la tâche suivante
    kwargs['ti'].xcom_push(key='enriched_portfolio_file', value=enriched_file)
    kwargs['ti'].xcom_push(key='returns_data_file', value=returns_file)
    logger.info("Traitement du portefeuille terminé")


def calculate_risk_metrics(**kwargs):
    """
    Calculer les métriques de risque pour le portefeuille.
    """
    logger.info("Début du calcul des métriques de risque")
    
    # Récupérer les chemins des fichiers
    enriched_portfolio_file = kwargs['ti'].xcom_pull(task_ids='process_portfolio', key='enriched_portfolio_file')
    returns_data_file = kwargs['ti'].xcom_pull(task_ids='process_portfolio', key='returns_data_file')
    
    # Charger les données
    portfolio = pd.read_parquet(enriched_portfolio_file)
    returns_data = pd.read_parquet(returns_data_file)
    
    # Extraire les poids du portefeuille
    weights = portfolio['Weight'].values
    
    # Initialiser le modèle VaR
    var_model = VaRModel(returns_data)
    
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
                        weights, confidence_level, time_horizon
                    )
                elif method == 'parametric':
                    var, cvar = var_model.calculate_parametric_var(
                        weights, confidence_level, time_horizon
                    )
                else:  # monte_carlo
                    var, cvar = var_model.calculate_monte_carlo_var(
                        weights, confidence_level, time_horizon, num_simulations=10000
                    )
                
                risk_metrics[method][key] = {
                    'var': var,
                    'cvar': cvar
                }
    
    # Calculer les contributions à la VaR
    component_var = var_model.calculate_component_var(weights, 0.95, 1)
    risk_metrics['component_var'] = component_var.to_dict()
    
    # Calculer la VaR incrémentale
    incremental_var = var_model.calculate_incremental_var(weights, 0.95, 1)
    risk_metrics['incremental_var'] = incremental_var.to_dict()
    
    # Enregistrer les métriques de risque
    risk_metrics_file = os.path.join(
        DATA_DIR, "reports", 
        f"risk_metrics_{datetime.now().strftime('%Y%m%d')}.json"
    )
    
    with open(risk_metrics_file, 'w') as f:
        json.dump(risk_metrics, f, indent=4, default=str)
    
    # Passer le chemin du fichier à la tâche suivante
    kwargs['ti'].xcom_push(key='risk_metrics_file', value=risk_metrics_file)
    logger.info("Calcul des métriques de risque terminé")


def run_stress_tests(**kwargs):
    """
    Exécuter les stress-tests sur le portefeuille.
    """
    logger.info("Début des stress-tests")
    
    # Récupérer les chemins des fichiers
    enriched_portfolio_file = kwargs['ti'].xcom_pull(task_ids='process_portfolio', key='enriched_portfolio_file')
    
    # Charger le portefeuille
    portfolio = pd.read_parquet(enriched_portfolio_file)
    
    # Initialiser le générateur de scénarios
    scenario_generator = ScenarioGenerator(scenarios_dir=os.path.join(DATA_DIR, "scenarios"))
    
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
            'original_value': original_value,
            'stressed_value': stressed_value,
            'impact_value': impact_value,
            'impact_percentage': impact_percentage,
            'stressed_portfolio': stressed_portfolio.to_dict()
        }
        
        # Sauvegarder le portefeuille stressé
        stressed_file = os.path.join(
            DATA_DIR, "portfolios", 
            f"stressed_portfolio_{scenario_name}_{datetime.now().strftime('%Y%m%d')}.parquet"
        )
        stressed_portfolio.to_parquet(stressed_file, index=False)
    
    # Créer un scénario combiné (combinaison de choc de taux et de liquidité)
    combined_scenario = scenario_generator.combine_scenarios(
        name="combined_rate_liquidity",
        description="Combinaison d'un choc de taux et d'une crise de liquidité",
        scenarios=[
            scenario_generator.get_predefined_scenario('rate_shock'),
            scenario_generator.get_predefined_scenario('liquidity_crisis')
        ],
        weights=[0.6, 0.4]
    )
    
    # Appliquer le scénario combiné
    stressed_portfolio_combined = apply_scenario_to_portfolio(portfolio, combined_scenario)
    
    # Calculer l'impact du scénario combiné
    original_value = portfolio['MarketValue'].sum()
    stressed_value = stressed_portfolio_combined['MarketValue'].sum()
    impact_value = stressed_value - original_value
    impact_percentage = impact_value / original_value
    
    # Stocker les résultats du scénario combiné
    stress_test_results['combined_rate_liquidity'] = {
        'scenario': combined_scenario,
        'original_value': original_value,
        'stressed_value': stressed_value,
        'impact_value': impact_value,
        'impact_percentage': impact_percentage,
        'stressed_portfolio': stressed_portfolio_combined.to_dict()
    }
    
    # Sauvegarder le portefeuille stressé pour le scénario combiné
    stressed_file_combined = os.path.join(
        DATA_DIR, "portfolios", 
        f"stressed_portfolio_combined_rate_liquidity_{datetime.now().strftime('%Y%m%d')}.parquet"
    )
    stressed_portfolio_combined.to_parquet(stressed_file_combined, index=False)
    
    # Enregistrer les résultats des stress-tests
    stress_test_results_file = os.path.join(
        DATA_DIR, "reports", 
        f"stress_test_results_{datetime.now().strftime('%Y%m%d')}.json"
    )
    
    with open(stress_test_results_file, 'w') as f:
        # Utiliser un convertisseur pour gérer les types non sérialisables
        json.dump(stress_test_results, f, indent=4, default=str)
    
    # Passer le chemin du fichier à la tâche suivante
    kwargs['ti'].xcom_push(key='stress_test_results_file', value=stress_test_results_file)
    logger.info("Stress-tests terminés")


def generate_report(**kwargs):
    """
    Générer le rapport de risque.
    """
    logger.info("Début de la génération du rapport")
    
    # Récupérer les chemins des fichiers
    enriched_portfolio_file = kwargs['ti'].xcom_pull(task_ids='process_portfolio', key='enriched_portfolio_file')
    risk_metrics_file = kwargs['ti'].xcom_pull(task_ids='calculate_risk_metrics', key='risk_metrics_file')
    stress_test_results_file = kwargs['ti'].xcom_pull(task_ids='run_stress_tests', key='stress_test_results_file')
    
    # Charger les données
    portfolio = pd.read_parquet(enriched_portfolio_file)
    
    with open(risk_metrics_file, 'r') as f:
        risk_metrics = json.load(f)
    
    with open(stress_test_results_file, 'r') as f:
        stress_test_results = json.load(f)
    
    # Générer le rapport (ici on génère un simple fichier HTML, mais dans une application réelle
    # on pourrait utiliser une bibliothèque de reporting plus sophistiquée)
    report_file = os.path.join(
        REPORT_DIR, 
        f"risk_report_{datetime.now().strftime('%Y%m%d')}.html"
    )
    
    with open(report_file, 'w') as f:
        f.write("<!DOCTYPE html>\n")
        f.write("<html>\n")
        f.write("<head>\n")
        f.write("    <title>Rapport de Risque</title>\n")
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
        f.write(f"<h1>Rapport de Risque - {datetime.now().strftime('%d/%m/%Y')}</h1>\n")
        
        # Résumé du portefeuille
        f.write("<h2>Résumé du Portefeuille</h2>\n")
        f.write("<table>\n")
        f.write("    <tr><th>Métrique</th><th>Valeur</th></tr>\n")
        f.write(f"    <tr><td>Valeur Totale</td><td>{portfolio['MarketValue'].sum():,.2f}</td></tr>\n")
        f.write(f"    <tr><td>Nombre d'Actifs</td><td>{len(portfolio)}</td></tr>\n")
        f.write(f"    <tr><td>Classes d'Actifs</td><td>{len(portfolio['AssetClass'].unique())}</td></tr>\n")
        if 'Currency' in portfolio.columns:
            f.write(f"    <tr><td>Devises</td><td>{len(portfolio['Currency'].unique())}</td></tr>\n")
        f.write("</table>\n")
        
        # Métriques de risque
        f.write("<h2>Métriques de Risque</h2>\n")
        
        # VaR
        f.write("<h3>Value at Risk (VaR)</h3>\n")
        f.write("<table>\n")
        f.write("    <tr><th>Méthode</th><th>Niveau de Confiance</th><th>Horizon Temporel</th><th>VaR</th><th>CVaR</th></tr>\n")
        
        for method in ['historical', 'parametric', 'monte_carlo']:
            for confidence_level in [0.95, 0.99]:
                for time_horizon in [1, 5, 20]:
                    key = f"var_{confidence_level}_{time_horizon}d"
                    if key in risk_metrics[method]:
                        var = risk_metrics[method][key]['var']
                        cvar = risk_metrics[method][key]['cvar']
                        
                        f.write(f"    <tr>\n")
                        f.write(f"        <td>{method.capitalize()}</td>\n")
                        f.write(f"        <td>{confidence_level*100:.0f}%</td>\n")
                        f.write(f"        <td>{time_horizon} jour{'s' if time_horizon > 1 else ''}</td>\n")
                        f.write(f"        <td class='negative'>{float(var)*100:.2f}%</td>\n")
                        f.write(f"        <td class='negative'>{float(cvar)*100:.2f}%</td>\n")
                        f.write(f"    </tr>\n")
        
        f.write("</table>\n")
        
        # Résultats des stress-tests
        f.write("<h2>Résultats des Stress-Tests</h2>\n")
        f.write("<table>\n")
        f.write("    <tr><th>Scénario</th><th>Valeur Initiale</th><th>Valeur Après Stress</th><th>Impact</th><th>Impact (%)</th></tr>\n")
        
        for scenario_name, results in stress_test_results.items():
            f.write(f"    <tr>\n")
            f.write(f"        <td>{results['scenario']['name']}</td>\n")
            f.write(f"        <td>{float(results['original_value']):,.2f}</td>\n")
            f.write(f"        <td>{float(results['stressed_value']):,.2f}</td>\n")
            f.write(f"        <td class=\"{'positive' if float(results['impact_value']) > 0 else 'negative'}\">{float(results['impact_value']):,.2f}</td>\n")
            f.write(f"        <td class=\"{'positive' if float(results['impact_percentage']) > 0 else 'negative'}\">{float(results['impact_percentage'])*100:.2f}%</td>\n")
            f.write(f"    </tr>\n")
        
        f.write("</table>\n")
        
        # Pied de page
        f.write("<p><i>Ce rapport a été généré automatiquement.</i></p>\n")
        
        f.write("</body>\n")
        f.write("</html>\n")
    
    # Passer le chemin du rapport à la tâche suivante
    kwargs['ti'].xcom_push(key='report_file', value=report_file)
    logger.info(f"Rapport généré et sauvegardé dans {report_file}")


def update_dashboard(**kwargs):
    """
    Mettre à jour le dashboard de risque.
    """
    logger.info("Début de la mise à jour du dashboard")
    
    # Récupérer les chemins des fichiers
    enriched_portfolio_file = kwargs['ti'].xcom_pull(task_ids='process_portfolio', key='enriched_portfolio_file')
    returns_data_file = kwargs['ti'].xcom_pull(task_ids='process_portfolio', key='returns_data_file')
    risk_metrics_file = kwargs['ti'].xcom_pull(task_ids='calculate_risk_metrics', key='risk_metrics_file')
    stress_test_results_file = kwargs['ti'].xcom_pull(task_ids='run_stress_tests', key='stress_test_results_file')
    
    # Charger les données
    portfolio = pd.read_parquet(enriched_portfolio_file)
    returns_data = pd.read_parquet(returns_data_file)
    
    with open(risk_metrics_file, 'r') as f:
        risk_metrics = json.load(f)
    
    with open(stress_test_results_file, 'r') as f:
        stress_test_results = json.load(f)
    
    # Créer le dashboard
    dashboard = RiskDashboard(
        title="Dashboard de Risque et Performance",
        portfolio_data=portfolio,
        returns_data=returns_data
    )
    
    # Configurer les métriques de risque
    dashboard.set_risk_metrics(risk_metrics)
    
    # Ajouter les scénarios de stress-test
    for scenario_name, results in stress_test_results.items():
        dashboard.add_scenario(results['scenario'])
    
    # Sauvegarder la configuration du dashboard
    dashboard_config_file = os.path.join(
        DASHBOARD_DIR, 
        f"dashboard_config_{datetime.now().strftime('%Y%m%d')}.json"
    )
    
    # Créer un dictionnaire de configuration simplifié
    dashboard_config = {
        'title': dashboard.title,
        'portfolio_file': enriched_portfolio_file,
        'returns_file': returns_data_file,
        'risk_metrics_file': risk_metrics_file,
        'stress_test_results_file': stress_test_results_file,
        'created_at': datetime.now().isoformat()
    }
    
    with open(dashboard_config_file, 'w') as f:
        json.dump(dashboard_config, f, indent=4)
    
    logger.info(f"Configuration du dashboard sauvegardée dans {dashboard_config_file}")
    
    # Remarque : Dans une application réelle, on pourrait déployer le dashboard sur un serveur web
    # ou générer une version statique du dashboard


def send_notification(**kwargs):
    """
    Envoyer une notification que le rapport est prêt.
    """
    logger.info("Envoi de la notification")
    
    # Récupérer le chemin du rapport
    report_file = kwargs['ti'].xcom_pull(task_ids='generate_report', key='report_file')
    
    # Construire le message de notification
    message = f"""
    Le rapport de risque du {datetime.now().strftime('%d/%m/%Y')} est prêt.
    
    Vous pouvez le consulter à l'adresse suivante:
    {report_file}
    
    Ce message a été envoyé automatiquement par le pipeline d'automatisation du reporting de risque.
    """
    
    # Dans une application réelle, on enverrait un email ou une notification via un service de messagerie
    # Pour cet exemple, on se contente de logger le message
    logger.info(f"Notification: {message}")


# Définir les tâches
task_collect_market_data = PythonOperator(
    task_id='collect_market_data',
    python_callable=collect_market_data,
    provide_context=True,
    dag=dag,
)

task_process_portfolio = PythonOperator(
    task_id='process_portfolio',
    python_callable=process_portfolio,
    provide_context=True,
    dag=dag,
)

task_calculate_risk_metrics = PythonOperator(
    task_id='calculate_risk_metrics',
    python_callable=calculate_risk_metrics,
    provide_context=True,
    dag=dag,
)

task_run_stress_tests = PythonOperator(
    task_id='run_stress_tests',
    python_callable=run_stress_tests,
    provide_context=True,
    dag=dag,
)

task_generate_report = PythonOperator(
    task_id='generate_report',
    python_callable=generate_report,
    provide_context=True,
    dag=dag,
)

task_update_dashboard = PythonOperator(
    task_id='update_dashboard',
    python_callable=update_dashboard,
    provide_context=True,
    dag=dag,
)

task_send_notification = PythonOperator(
    task_id='send_notification',
    python_callable=send_notification,
    provide_context=True,
    dag=dag,
)

# Définir les dépendances entre les tâches
task_collect_market_data >> task_process_portfolio
task_process_portfolio >> [task_calculate_risk_metrics, task_run_stress_tests]
[task_calculate_risk_metrics, task_run_stress_tests] >> task_generate_report
task_generate_report >> task_update_dashboard >> task_send_notification
