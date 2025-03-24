"""
API FastAPI pour accéder aux rapports et aux dashboards.
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import pandas as pd
import uvicorn

# Ajouter le répertoire parent au chemin de recherche des modules
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(parent_dir)

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

# Définir les chemins des répertoires
DATA_DIR = os.path.join(parent_dir, "data")
PORTFOLIO_DIR = os.path.join(DATA_DIR, "portfolios")
MARKET_DATA_DIR = os.path.join(DATA_DIR, "market_data")
REPORT_DIR = os.path.join(DATA_DIR, "reports")
DASHBOARD_DIR = os.path.join(DATA_DIR, "dashboards")
SCENARIOS_DIR = os.path.join(DATA_DIR, "scenarios")

# S'assurer que les répertoires existent
os.makedirs(PORTFOLIO_DIR, exist_ok=True)
os.makedirs(MARKET_DATA_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs(DASHBOARD_DIR, exist_ok=True)
os.makedirs(SCENARIOS_DIR, exist_ok=True)

# Créer l'application FastAPI
app = FastAPI(
    title="API de Reporting de Risque",
    description="API pour accéder aux rapports de risque et aux dashboards",
    version="1.0.0"
)

# Configurer CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Monter les répertoires de données statiques
app.mount("/reports", StaticFiles(directory=REPORT_DIR), name="reports")
app.mount("/dashboards", StaticFiles(directory=DASHBOARD_DIR), name="dashboards")


@app.get("/")
async def root():
    """
    Endpoint racine de l'API.
    """
    return {
        "message": "API de Reporting de Risque",
        "documentation": "/docs",
        "reports": "/reports",
        "dashboards": "/dashboards",
    }


@app.get("/portfolios", response_model=List[Dict[str, Any]])
async def list_portfolios():
    """
    Lister tous les portefeuilles disponibles.
    """
    portfolios = []
    
    try:
        # Parcourir les fichiers dans le répertoire des portefeuilles
        for filename in os.listdir(PORTFOLIO_DIR):
            if filename.endswith(('.csv', '.parquet')):
                filepath = os.path.join(PORTFOLIO_DIR, filename)
                stats = os.stat(filepath)
                
                # Créer un dictionnaire avec les informations du portefeuille
                portfolio_info = {
                    "name": filename,
                    "path": filepath,
                    "size": stats.st_size,
                    "modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
                    "created": datetime.fromtimestamp(stats.st_ctime).isoformat(),
                }
                
                # Ajouter des informations supplémentaires pour les portefeuilles enrichis
                if filename.startswith('enriched_'):
                    try:
                        if filename.endswith('.csv'):
                            portfolio = pd.read_csv(filepath)
                        else:  # .parquet
                            portfolio = pd.read_parquet(filepath)
                        
                        # Ajouter des informations sur le contenu du portefeuille
                        portfolio_info["total_value"] = float(portfolio['MarketValue'].sum()) if 'MarketValue' in portfolio.columns else None
                        portfolio_info["num_assets"] = len(portfolio)
                        portfolio_info["asset_classes"] = portfolio['AssetClass'].unique().tolist() if 'AssetClass' in portfolio.columns else []
                        portfolio_info["currencies"] = portfolio['Currency'].unique().tolist() if 'Currency' in portfolio.columns else []
                    except Exception as e:
                        logger.error(f"Error reading portfolio {filename}: {e}")
                
                portfolios.append(portfolio_info)
        
        return portfolios
    
    except Exception as e:
        logger.error(f"Error listing portfolios: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/portfolios/{portfolio_name}")
async def get_portfolio(portfolio_name: str):
    """
    Récupérer un portefeuille spécifique.
    """
    filepath = os.path.join(PORTFOLIO_DIR, portfolio_name)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"Portfolio {portfolio_name} not found")
    
    try:
        # Charger le portefeuille
        if portfolio_name.endswith('.csv'):
            portfolio = pd.read_csv(filepath)
        elif portfolio_name.endswith('.parquet'):
            portfolio = pd.read_parquet(filepath)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        # Convertir le DataFrame en dictionnaire
        portfolio_dict = portfolio.to_dict(orient='records')
        
        # Ajouter des métadonnées
        response = {
            "name": portfolio_name,
            "num_assets": len(portfolio),
            "columns": portfolio.columns.tolist(),
            "total_value": float(portfolio['MarketValue'].sum()) if 'MarketValue' in portfolio.columns else None,
            "data": portfolio_dict
        }
        
        return response
    
    except Exception as e:
        logger.error(f"Error getting portfolio {portfolio_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reports", response_model=List[Dict[str, Any]])
async def list_reports():
    """
    Lister tous les rapports disponibles.
    """
    reports = []
    
    try:
        # Parcourir les fichiers dans le répertoire des rapports
        for filename in os.listdir(REPORT_DIR):
            if filename.endswith(('.html', '.pdf', '.xlsx')):
                filepath = os.path.join(REPORT_DIR, filename)
                stats = os.stat(filepath)
                
                # Extraire la date du nom du fichier
                date_str = filename.split('_')[-1].split('.')[0]
                try:
                    report_date = datetime.strptime(date_str, '%Y%m%d').date().isoformat()
                except:
                    report_date = None
                
                # Créer un dictionnaire avec les informations du rapport
                report_info = {
                    "name": filename,
                    "path": filepath,
                    "url": f"/reports/{filename}",
                    "size": stats.st_size,
                    "modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
                    "created": datetime.fromtimestamp(stats.st_ctime).isoformat(),
                    "report_date": report_date
                }
                
                reports.append(report_info)
        
        # Trier les rapports par date (du plus récent au plus ancien)
        reports.sort(key=lambda x: x["created"], reverse=True)
        
        return reports
    
    except Exception as e:
        logger.error(f"Error listing reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reports/{report_name}")
async def get_report(report_name: str):
    """
    Récupérer un rapport spécifique.
    """
    filepath = os.path.join(REPORT_DIR, report_name)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"Report {report_name} not found")
    
    try:
        # Retourner le fichier
        return FileResponse(filepath)
    
    except Exception as e:
        logger.error(f"Error getting report {report_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dashboards", response_model=List[Dict[str, Any]])
async def list_dashboards():
    """
    Lister tous les dashboards disponibles.
    """
    dashboards = []
    
    try:
        # Parcourir les fichiers de configuration des dashboards
        for filename in os.listdir(DASHBOARD_DIR):
            if filename.endswith('.json') and filename.startswith('dashboard_config_'):
                filepath = os.path.join(DASHBOARD_DIR, filename)
                stats = os.stat(filepath)
                
                # Extraire la date du nom du fichier
                date_str = filename.split('_')[-1].split('.')[0]
                try:
                    dashboard_date = datetime.strptime(date_str, '%Y%m%d').date().isoformat()
                except:
                    dashboard_date = None
                
                # Lire la configuration du dashboard
                with open(filepath, 'r') as f:
                    config = json.load(f)
                
                # Créer un dictionnaire avec les informations du dashboard
                dashboard_info = {
                    "name": filename,
                    "path": filepath,
                    "url": f"/dashboards/view/{filename.split('.')[0]}",
                    "size": stats.st_size,
                    "modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
                    "created": datetime.fromtimestamp(stats.st_ctime).isoformat(),
                    "dashboard_date": dashboard_date,
                    "title": config.get("title", "Dashboard"),
                    "config": config
                }
                
                dashboards.append(dashboard_info)
        
        # Trier les dashboards par date (du plus récent au plus ancien)
        dashboards.sort(key=lambda x: x["created"], reverse=True)
        
        return dashboards
    
    except Exception as e:
        logger.error(f"Error listing dashboards: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dashboards/view/{dashboard_id}")
async def view_dashboard(dashboard_id: str):
    """
    Visualiser un dashboard spécifique.
    """
    config_file = f"{dashboard_id}.json"
    config_path = os.path.join(DASHBOARD_DIR, config_file)
    
    if not os.path.exists(config_path):
        raise HTTPException(status_code=404, detail=f"Dashboard {dashboard_id} not found")
    
    try:
        # Lire la configuration du dashboard
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Dans une application réelle, on générerait une page HTML
        # avec l'intégration du dashboard ou on redirigerait vers l'URL du dashboard
        
        # Pour cet exemple, on génère une page HTML simple
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{config.get('title', 'Dashboard')}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #2c3e50; }}
                .info {{ margin-bottom: 20px; }}
                .container {{ width: 100%; height: 800px; border: 1px solid #ddd; }}
                .button {{ padding: 10px; background-color: #3498db; color: white; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <h1>{config.get('title', 'Dashboard')}</h1>
            
            <div class="info">
                <p>Date du dashboard: {config.get('created_at', 'N/A')}</p>
            </div>
            
            <div class="container">
                <iframe src="http://localhost:8050" width="100%" height="100%" frameborder="0"></iframe>
            </div>
            
            <p>Note: Pour exécuter le dashboard, vous devez lancer l'application Dash localement:</p>
            <pre>
            python -m src.visualization.risk_dashboard
            </pre>
            
            <p>Fichiers associés:</p>
            <ul>
                <li>Portfolio: {os.path.basename(config.get('portfolio_file', 'N/A'))}</li>
                <li>Rendements: {os.path.basename(config.get('returns_file', 'N/A'))}</li>
                <li>Métriques de risque: {os.path.basename(config.get('risk_metrics_file', 'N/A'))}</li>
                <li>Résultats des stress-tests: {os.path.basename(config.get('stress_test_results_file', 'N/A'))}</li>
            </ul>
            
            <div>
                <a href="/reports" class="button">Rapports</a>
                <a href="/dashboards" class="button">Dashboards</a>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
    
    except Exception as e:
        logger.error(f"Error viewing dashboard {dashboard_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/scenarios", response_model=List[Dict[str, Any]])
async def list_scenarios():
    """
    Lister tous les scénarios de stress-test disponibles.
    """
    # Initialiser le générateur de scénarios
    scenario_generator = ScenarioGenerator(scenarios_dir=SCENARIOS_DIR)
    
    try:
        # Récupérer la liste des scénarios
        scenario_names = scenario_generator.list_scenarios()
        
        # Récupérer les détails de chaque scénario
        scenarios = []
        for name in scenario_names:
            try:
                scenario = scenario_generator.load_scenario(name)
                scenarios.append(scenario)
            except Exception as e:
                logger.warning(f"Error loading scenario {name}: {e}")
        
        # Ajouter les scénarios prédéfinis
        for name in ScenarioGenerator.PREDEFINED_SCENARIOS:
            scenario = scenario_generator.get_predefined_scenario(name)
            # Marquer comme prédéfini
            scenario['is_predefined'] = True
            scenarios.append(scenario)
        
        return scenarios
    
    except Exception as e:
        logger.error(f"Error listing scenarios: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/scenarios/{scenario_name}")
async def get_scenario(scenario_name: str):
    """
    Récupérer un scénario spécifique.
    """
    # Initialiser le générateur de scénarios
    scenario_generator = ScenarioGenerator(scenarios_dir=SCENARIOS_DIR)
    
    try:
        # Vérifier si le scénario est prédéfini
        if scenario_name in ScenarioGenerator.PREDEFINED_SCENARIOS:
            scenario = scenario_generator.get_predefined_scenario(scenario_name)
            scenario['is_predefined'] = True
        else:
            # Charger le scénario depuis un fichier
            scenario = scenario_generator.load_scenario(scenario_name)
        
        return scenario
    
    except Exception as e:
        logger.error(f"Error getting scenario {scenario_name}: {e}")
        raise HTTPException(status_code=404, detail=f"Scenario {scenario_name} not found")


@app.post("/run-stress-test", response_model=Dict[str, Any])
async def run_stress_test(
    portfolio_name: str,
    scenario_name: str,
    severity: float = 1.0,
    background_tasks: BackgroundTasks = None
):
    """
    Exécuter un stress-test sur un portefeuille.
    """
    # Vérifier si le portefeuille existe
    portfolio_path = os.path.join(PORTFOLIO_DIR, portfolio_name)
    if not os.path.exists(portfolio_path):
        raise HTTPException(status_code=404, detail=f"Portfolio {portfolio_name} not found")
    
    # Initialiser le générateur de scénarios
    scenario_generator = ScenarioGenerator(scenarios_dir=SCENARIOS_DIR)
    
    try:
        # Charger le portefeuille
        if portfolio_name.endswith('.csv'):
            portfolio = pd.read_csv(portfolio_path)
        elif portfolio_name.endswith('.parquet'):
            portfolio = pd.read_parquet(portfolio_path)
        else:
            raise HTTPException(status_code=400, detail="Unsupported portfolio file format")
        
        # Récupérer le scénario
        if scenario_name in ScenarioGenerator.PREDEFINED_SCENARIOS:
            scenario = scenario_generator.get_predefined_scenario(scenario_name, severity_multiplier=severity)
        else:
            scenario = scenario_generator.load_scenario(scenario_name)
        
        # Exécuter le stress-test
        stressed_portfolio = apply_scenario_to_portfolio(portfolio, scenario)
        
        # Calculer l'impact
        original_value = portfolio['MarketValue'].sum() if 'MarketValue' in portfolio.columns else 0
        stressed_value = stressed_portfolio['MarketValue'].sum() if 'MarketValue' in stressed_portfolio.columns else 0
        impact_value = stressed_value - original_value
        impact_percentage = impact_value / original_value if original_value != 0 else 0
        
        # Sauvegarder le portefeuille stressé
        result_name = f"stressed_{scenario_name}_{portfolio_name.split('.')[0]}_{datetime.now().strftime('%Y%m%d')}"
        result_path = os.path.join(PORTFOLIO_DIR, f"{result_name}.parquet")
        stressed_portfolio.to_parquet(result_path, index=False)
        
        # Préparer la réponse
        result = {
            "scenario": scenario,
            "portfolio": portfolio_name,
            "original_value": float(original_value),
            "stressed_value": float(stressed_value),
            "impact_value": float(impact_value),
            "impact_percentage": float(impact_percentage),
            "stressed_portfolio_path": result_path,
            "stressed_portfolio_name": f"{result_name}.parquet",
            "execution_time": datetime.now().isoformat()
        }
        
        # Sauvegarder le résultat
        result_file = os.path.join(REPORT_DIR, f"{result_name}_result.json")
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=4, default=str)
        
        return result
    
    except Exception as e:
        logger.error(f"Error running stress-test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-report", response_model=Dict[str, Any])
async def generate_report(
    portfolio_name: str,
    report_type: str = "risk",
    background_tasks: BackgroundTasks = None
):
    """
    Générer un rapport pour un portefeuille.
    """
    # Vérifier si le portefeuille existe
    portfolio_path = os.path.join(PORTFOLIO_DIR, portfolio_name)
    if not os.path.exists(portfolio_path):
        raise HTTPException(status_code=404, detail=f"Portfolio {portfolio_name} not found")
    
    try:
        # Charger le portefeuille
        if portfolio_name.endswith('.csv'):
            portfolio = pd.read_csv(portfolio_path)
        elif portfolio_name.endswith('.parquet'):
            portfolio = pd.read_parquet(portfolio_path)
        else:
            raise HTTPException(status_code=400, detail="Unsupported portfolio file format")
        
        # Générer un nom pour le rapport
        report_name = f"{report_type}_report_{portfolio_name.split('.')[0]}_{datetime.now().strftime('%Y%m%d')}.html"
        report_path = os.path.join(REPORT_DIR, report_name)
        
        # Préparer le contenu du rapport
        # (Dans une application réelle, on utiliserait des templates plus sophistiqués)
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Rapport de {report_type.capitalize()} - {portfolio_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2, h3 {{ color: #2c3e50; }}
                table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .negative {{ color: red; }}
                .positive {{ color: green; }}
                .summary {{ margin: 20px 0; }}
            </style>
        </head>
        <body>
            <h1>Rapport de {report_type.capitalize()} - {portfolio_name}</h1>
            <p>Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}</p>
            
            <div class="summary">
                <h2>Résumé du Portefeuille</h2>
                <table>
                    <tr><th>Métrique</th><th>Valeur</th></tr>
                    <tr><td>Nombre d'actifs</td><td>{len(portfolio)}</td></tr>
        """
        
        # Ajouter des informations spécifiques au rapport
        if 'MarketValue' in portfolio.columns:
            total_value = portfolio['MarketValue'].sum()
            html_content += f"<tr><td>Valeur totale</td><td>{total_value:,.2f}</td></tr>\n"
        
        if 'AssetClass' in portfolio.columns:
            asset_classes = portfolio['AssetClass'].unique()
            html_content += f"<tr><td>Classes d'actifs</td><td>{', '.join(asset_classes)}</td></tr>\n"
        
        if 'Currency' in portfolio.columns:
            currencies = portfolio['Currency'].unique()
            html_content += f"<tr><td>Devises</td><td>{', '.join(currencies)}</td></tr>\n"
        
        # Fermer la table et ajouter les détails du portefeuille
        html_content += """
                </table>
            </div>
            
            <div>
                <h2>Détails du Portefeuille</h2>
                <table>
                    <tr>
        """
        
        # Ajouter les en-têtes de colonnes
        for col in portfolio.columns:
            html_content += f"<th>{col}</th>\n"
        
        html_content += "</tr>\n"
        
        # Ajouter les lignes de données (limiter à 100 lignes pour les grands portefeuilles)
        for _, row in portfolio.head(100).iterrows():
            html_content += "<tr>\n"
            for col in portfolio.columns:
                value = row[col]
                if isinstance(value, float):
                    html_content += f"<td>{value:,.2f}</td>\n"
                else:
                    html_content += f"<td>{value}</td>\n"
            html_content += "</tr>\n"
        
        # Fermer la table et le document
        html_content += """
                </table>
                <p>Note: Affichage limité aux 100 premiers actifs.</p>
            </div>
            
            <div>
                <h2>Métriques de Risque</h2>
                <p>Pour des métriques de risque détaillées, veuillez consulter le dashboard.</p>
            </div>
            
            <footer>
                <p>Ce rapport a été généré automatiquement.</p>
            </footer>
        </body>
        </html>
        """
        
        # Enregistrer le rapport
        with open(report_path, 'w') as f:
            f.write(html_content)
        
        # Préparer la réponse
        result = {
            "report_name": report_name,
            "report_path": report_path,
            "report_url": f"/reports/{report_name}",
            "portfolio": portfolio_name,
            "report_type": report_type,
            "generation_time": datetime.now().isoformat()
        }
        
        return result
    
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/update-dashboard", response_model=Dict[str, Any])
async def update_dashboard(
    portfolio_name: str,
    background_tasks: BackgroundTasks = None
):
    """
    Mettre à jour le dashboard pour un portefeuille.
    """
    # Vérifier si le portefeuille existe
    portfolio_path = os.path.join(PORTFOLIO_DIR, portfolio_name)
    if not os.path.exists(portfolio_path):
        raise HTTPException(status_code=404, detail=f"Portfolio {portfolio_name} not found")
    
    try:
        # Charger le portefeuille
        if portfolio_name.endswith('.csv'):
            portfolio = pd.read_csv(portfolio_path)
        elif portfolio_name.endswith('.parquet'):
            portfolio = pd.read_parquet(portfolio_path)
        else:
            raise HTTPException(status_code=400, detail="Unsupported portfolio file format")
        
        # Générer une configuration pour le dashboard
        dashboard_config = {
            "title": f"Dashboard de Risque - {portfolio_name}",
            "portfolio_file": portfolio_path,
            "created_at": datetime.now().isoformat()
        }
        
        # Enregistrer la configuration
        dashboard_name = f"dashboard_config_{portfolio_name.split('.')[0]}_{datetime.now().strftime('%Y%m%d')}"
        dashboard_path = os.path.join(DASHBOARD_DIR, f"{dashboard_name}.json")
        
        with open(dashboard_path, 'w') as f:
            json.dump(dashboard_config, f, indent=4)
        
        # Préparer la réponse
        result = {
            "dashboard_name": dashboard_name,
            "dashboard_path": dashboard_path,
            "dashboard_url": f"/dashboards/view/{dashboard_name}",
            "portfolio": portfolio_name,
            "creation_time": datetime.now().isoformat()
        }
        
        return result
    
    except Exception as e:
        logger.error(f"Error updating dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
