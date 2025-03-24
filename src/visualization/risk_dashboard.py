"""
Module pour la création de dashboards de risque interactifs.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, callback_context
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import logging
from typing import List, Dict, Optional, Union, Tuple, Any
import os
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RiskDashboard:
    """
    Classe pour créer et gérer des dashboards de risque interactifs.
    """
    
    def __init__(
        self,
        title: str = "Dashboard de Risque",
        portfolio_data: Optional[pd.DataFrame] = None,
        market_data: Optional[pd.DataFrame] = None,
        returns_data: Optional[pd.DataFrame] = None,
        scenarios: Optional[List[Dict[str, Any]]] = None,
        risk_metrics: Optional[Dict[str, Any]] = None
    ):
        """
        Initialiser le dashboard de risque.
        
        Args:
            title: Titre du dashboard
            portfolio_data: Données du portefeuille
            market_data: Données de marché
            returns_data: Données de rendements
            scenarios: Liste des scénarios de stress-test
            risk_metrics: Dictionnaire des métriques de risque calculées
        """
        self.title = title
        self.portfolio_data = portfolio_data
        self.market_data = market_data
        self.returns_data = returns_data
        self.scenarios = scenarios or []
        self.risk_metrics = risk_metrics or {}
        
        # Initialiser l'application Dash
        self.app = dash.Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            suppress_callback_exceptions=True
        )
        
        # Configurer le titre de l'application
        self.app.title = title
        
        # Initialiser le layout
        self._setup_layout()
        
        # Configurer les callbacks
        self._setup_callbacks()
    
    def set_portfolio_data(self, portfolio_data: pd.DataFrame):
        """
        Définir les données du portefeuille.
        
        Args:
            portfolio_data: Données du portefeuille
        """
        self.portfolio_data = portfolio_data
        
    def set_market_data(self, market_data: pd.DataFrame):
        """
        Définir les données de marché.
        
        Args:
            market_data: Données de marché
        """
        self.market_data = market_data
        
    def set_returns_data(self, returns_data: pd.DataFrame):
        """
        Définir les données de rendements.
        
        Args:
            returns_data: Données de rendements
        """
        self.returns_data = returns_data
        
    def add_scenario(self, scenario: Dict[str, Any]):
        """
        Ajouter un scénario de stress-test.
        
        Args:
            scenario: Dictionnaire contenant le scénario
        """
        self.scenarios.append(scenario)
        
    def add_scenarios(self, scenarios: List[Dict[str, Any]]):
        """
        Ajouter plusieurs scénarios de stress-test.
        
        Args:
            scenarios: Liste de dictionnaires contenant les scénarios
        """
        self.scenarios.extend(scenarios)
        
    def set_risk_metrics(self, risk_metrics: Dict[str, Any]):
        """
        Définir les métriques de risque.
        
        Args:
            risk_metrics: Dictionnaire des métriques de risque calculées
        """
        self.risk_metrics = risk_metrics
        
    def _setup_layout(self):
        """Configurer le layout du dashboard."""
        self.app.layout = html.Div(
            className="dashboard-container",
            children=[
                # Header
                html.Div(
                    className="header",
                    children=[
                        html.H1(self.title),
                        html.P(f"Mis à jour le {datetime.now().strftime('%Y-%m-%d %H:%M')}")
                    ]
                ),
                
                # Navigation Tabs
                dbc.Tabs(
                    id="tabs",
                    active_tab="tab-portfolio",
                    children=[
                        dbc.Tab(
                            label="Portefeuille",
                            tab_id="tab-portfolio",
                            children=self._create_portfolio_tab()
                        ),
                        dbc.Tab(
                            label="Analyse de Risque",
                            tab_id="tab-risk",
                            children=self._create_risk_tab()
                        ),
                        dbc.Tab(
                            label="Stress-Test",
                            tab_id="tab-stress",
                            children=self._create_stress_tab()
                        ),
                        dbc.Tab(
                            label="Performance",
                            tab_id="tab-performance",
                            children=self._create_performance_tab()
                        ),
                    ]
                ),
                
                # Footer
                html.Div(
                    className="footer",
                    children=[
                        html.P("© 2025 - Automatisation du Reporting et des Analyses de Risque")
                    ]
                ),
                
                # Store for sharing data between callbacks
                dcc.Store(id="store-selected-scenario"),
                dcc.Store(id="store-selected-timeframe"),
                dcc.Store(id="store-portfolio-filtered")
            ]
        )
    
    def _create_portfolio_tab(self):
        """Créer le contenu de l'onglet Portefeuille."""
        return html.Div(
            className="tab-content",
            children=[
                dbc.Row([
                    dbc.Col([
                        html.H3("Répartition du Portefeuille"),
                        html.Div(
                            id="portfolio-allocation-charts",
                            children=[
                                dcc.Loading(
                                    id="loading-allocation-charts",
                                    children=[
                                        html.Div(id="asset-allocation-chart"),
                                        html.Div(id="sector-allocation-chart"),
                                        html.Div(id="currency-allocation-chart")
                                    ]
                                )
                            ]
                        )
                    ], width=8),
                    dbc.Col([
                        html.H3("Filtres"),
                        html.Div(
                            className="filters-container",
                            children=[
                                html.Label("Classe d'actifs:"),
                                dcc.Dropdown(
                                    id="asset-class-filter",
                                    multi=True,
                                    placeholder="Sélectionner..."
                                ),
                                html.Label("Secteur:"),
                                dcc.Dropdown(
                                    id="sector-filter",
                                    multi=True,
                                    placeholder="Sélectionner..."
                                ),
                                html.Label("Devise:"),
                                dcc.Dropdown(
                                    id="currency-filter",
                                    multi=True,
                                    placeholder="Sélectionner..."
                                ),
                                html.Br(),
                                dbc.Button(
                                    "Appliquer les filtres",
                                    id="apply-filters-button",
                                    color="primary"
                                )
                            ]
                        ),
                        html.Hr(),
                        html.H3("Résumé du Portefeuille"),
                        html.Div(id="portfolio-summary")
                    ], width=4)
                ]),
                html.Hr(),
                html.H3("Détails du Portefeuille"),
                html.Div(
                    id="portfolio-details",
                    children=[
                        dcc.Loading(
                            id="loading-portfolio-table",
                            children=[
                                html.Div(id="portfolio-table")
                            ]
                        )
                    ]
                )
            ]
        )
    
    def _create_risk_tab(self):
        """Créer le contenu de l'onglet Analyse de Risque."""
        return html.Div(
            className="tab-content",
            children=[
                dbc.Row([
                    dbc.Col([
                        html.H3("Métriques de Risque"),
                        html.Div(
                            id="risk-metrics-container",
                            children=[
                                dcc.Loading(
                                    id="loading-risk-metrics",
                                    children=[
                                        html.Div(id="var-metrics"),
                                        html.Div(id="volatility-metrics"),
                                        html.Div(id="correlation-metrics")
                                    ]
                                )
                            ]
                        )
                    ], width=8),
                    dbc.Col([
                        html.H3("Paramètres"),
                        html.Div(
                            className="risk-parameters",
                            children=[
                                html.Label("Niveau de confiance:"),
                                dcc.Slider(
                                    id="confidence-level-slider",
                                    min=0.90,
                                    max=0.99,
                                    step=0.01,
                                    value=0.95,
                                    marks={0.90: '90%', 0.95: '95%', 0.99: '99%'},
                                    tooltip={"placement": "bottom", "always_visible": True}
                                ),
                                html.Label("Horizon temporel:"),
                                dcc.RadioItems(
                                    id="time-horizon-radio",
                                    options=[
                                        {'label': '1 jour', 'value': 1},
                                        {'label': '1 semaine', 'value': 5},
                                        {'label': '1 mois', 'value': 20},
                                        {'label': '1 an', 'value': 252}
                                    ],
                                    value=1,
                                    labelStyle={'display': 'inline-block', 'margin-right': '10px'}
                                ),
                                html.Label("Méthode de calcul:"),
                                dcc.Dropdown(
                                    id="var-method-dropdown",
                                    options=[
                                        {'label': 'Historique', 'value': 'historical'},
                                        {'label': 'Paramétrique', 'value': 'parametric'},
                                        {'label': 'Monte Carlo', 'value': 'monte_carlo'}
                                    ],
                                    value='historical',
                                    clearable=False
                                ),
                                html.Br(),
                                dbc.Button(
                                    "Calculer",
                                    id="calculate-risk-button",
                                    color="primary"
                                )
                            ]
                        )
                    ], width=4)
                ]),
                html.Hr(),
                dbc.Row([
                    dbc.Col([
                        html.H3("Contribution au Risque"),
                        dcc.Loading(
                            id="loading-risk-contribution",
                            children=[
                                html.Div(id="var-contribution-chart"),
                                html.Div(id="risk-contribution-table")
                            ]
                        )
                    ], width=6),
                    dbc.Col([
                        html.H3("Distribution des Rendements"),
                        dcc.Loading(
                            id="loading-returns-distribution",
                            children=[
                                html.Div(id="returns-distribution-chart"),
                                html.Div(id="returns-statistics")
                            ]
                        )
                    ], width=6)
                ])
            ]
        )
    
    def _create_stress_tab(self):
        """Créer le contenu de l'onglet Stress-Test."""
        return html.Div(
            className="tab-content",
            children=[
                dbc.Row([
                    dbc.Col([
                        html.H3("Résultats des Stress-Tests"),
                        html.Div(
                            id="stress-test-results-container",
                            children=[
                                dcc.Loading(
                                    id="loading-stress-results",
                                    children=[
                                        html.Div(id="stress-test-summary-chart"),
                                        html.Div(id="stress-test-impact-chart")
                                    ]
                                )
                            ]
                        )
                    ], width=8),
                    dbc.Col([
                        html.H3("Sélection de Scénarios"),
                        html.Div(
                            className="scenario-selection",
                            children=[
                                html.Label("Scénarios prédéfinis:"),
                                dcc.Dropdown(
                                    id="scenario-dropdown",
                                    options=[
                                        {'label': 'Crise financière 2008', 'value': 'financial_crisis_2008'},
                                        {'label': 'Choc de taux', 'value': 'rate_shock'},
                                        {'label': 'Choc d\'inflation', 'value': 'inflation_shock'},
                                        {'label': 'Crise de liquidité', 'value': 'liquidity_crisis'},
                                        {'label': 'Crise géopolitique', 'value': 'geopolitical_crisis'}
                                    ],
                                    multi=True,
                                    placeholder="Sélectionner un ou plusieurs scénarios..."
                                ),
                                html.Label("Sévérité du choc:"),
                                dcc.Slider(
                                    id="severity-slider",
                                    min=0.5,
                                    max=1.5,
                                    step=0.1,
                                    value=1.0,
                                    marks={0.5: '50%', 1.0: '100%', 1.5: '150%'},
                                    tooltip={"placement": "bottom", "always_visible": True}
                                ),
                                html.Br(),
                                dbc.Button(
                                    "Exécuter Stress-Test",
                                    id="run-stress-test-button",
                                    color="primary"
                                ),
                                html.Hr(),
                                html.H4("Scénario personnalisé"),
                                html.Div(
                                    id="custom-scenario-builder",
                                    children=[
                                        # Ajout de contrôles pour la création de scénarios personnalisés
                                        html.Label("Nom du scénario:"),
                                        dcc.Input(
                                            id="custom-scenario-name",
                                            type="text",
                                            placeholder="Ex: Mon Scénario",
                                            style={'width': '100%'}
                                        ),
                                        html.Label("Description:"),
                                        dcc.Textarea(
                                            id="custom-scenario-description",
                                            placeholder="Description du scénario...",
                                            style={'width': '100%', 'height': '60px'}
                                        ),
                                        html.Label("Chocs:"),
                                        dbc.Row([
                                            dbc.Col([
                                                html.Label("Actions:"),
                                                dcc.Input(
                                                    id="equity-shock",
                                                    type="number",
                                                    placeholder="-0.15",
                                                    style={'width': '100%'}
                                                )
                                            ], width=6),
                                            dbc.Col([
                                                html.Label("Taux d'intérêt:"),
                                                dcc.Input(
                                                    id="interest-rate-shock",
                                                    type="number",
                                                    placeholder="0.01",
                                                    style={'width': '100%'}
                                                )
                                            ], width=6)
                                        ]),
                                        dbc.Row([
                                            dbc.Col([
                                                html.Label("Spreads de crédit:"),
                                                dcc.Input(
                                                    id="credit-spread-shock",
                                                    type="number",
                                                    placeholder="0.005",
                                                    style={'width': '100%'}
                                                )
                                            ], width=6),
                                            dbc.Col([
                                                html.Label("Volatilité:"),
                                                dcc.Input(
                                                    id="volatility-shock",
                                                    type="number",
                                                    placeholder="0.10",
                                                    style={'width': '100%'}
                                                )
                                            ], width=6)
                                        ]),
                                        html.Br(),
                                        dbc.Button(
                                            "Créer et exécuter",
                                            id="create-custom-scenario-button",
                                            color="secondary"
                                        )
                                    ]
                                )
                            ]
                        )
                    ], width=4)
                ]),
                html.Hr(),
                html.H3("Détails des Résultats par Scénario"),
                html.Div(
                    id="stress-test-details",
                    children=[
                        dcc.Loading(
                            id="loading-stress-details",
                            children=[
                                html.Div(id="stress-test-details-table")
                            ]
                        )
                    ]
                )
            ]
        )
    
    def _create_performance_tab(self):
        """Créer le contenu de l'onglet Performance."""
        return html.Div(
            className="tab-content",
            children=[
                dbc.Row([
                    dbc.Col([
                        html.H3("Évolution de la Performance"),
                        html.Div(
                            id="performance-charts-container",
                            children=[
                                dcc.Loading(
                                    id="loading-performance-charts",
                                    children=[
                                        html.Div(id="cumulative-returns-chart"),
                                        html.Div(id="drawdown-chart")
                                    ]
                                )
                            ]
                        )
                    ], width=8),
                    dbc.Col([
                        html.H3("Période"),
                        html.Div(
                            className="timeframe-selection",
                            children=[
                                html.Label("Sélectionner la période:"),
                                dcc.RadioItems(
                                    id="timeframe-radio",
                                    options=[
                                        {'label': '1 mois', 'value': '1M'},
                                        {'label': '3 mois', 'value': '3M'},
                                        {'label': '6 mois', 'value': '6M'},
                                        {'label': 'YTD', 'value': 'YTD'},
                                        {'label': '1 an', 'value': '1Y'},
                                        {'label': '3 ans', 'value': '3Y'},
                                        {'label': 'Tout', 'value': 'ALL'}
                                    ],
                                    value='1Y',
                                    labelStyle={'display': 'block', 'margin-bottom': '5px'}
                                ),
                                html.Label("Période personnalisée:"),
                                dcc.DatePickerRange(
                                    id="date-range-picker",
                                    start_date=datetime.now() - timedelta(days=365),
                                    end_date=datetime.now(),
                                    display_format="YYYY-MM-DD"
                                ),
                                html.Br(),
                                dbc.Button(
                                    "Appliquer",
                                    id="apply-timeframe-button",
                                    color="primary"
                                )
                            ]
                        ),
                        html.Hr(),
                        html.H3("Statistiques de Performance"),
                        html.Div(id="performance-statistics")
                    ], width=4)
                ]),
                html.Hr(),
                dbc.Row([
                    dbc.Col([
                        html.H3("Performance par Classe d'Actifs"),
                        dcc.Loading(
                            id="loading-performance-by-asset",
                            children=[
                                html.Div(id="performance-by-asset-chart")
                            ]
                        )
                    ], width=6),
                    dbc.Col([
                        html.H3("Meilleurs/Pires Performers"),
                        dcc.Loading(
                            id="loading-top-bottom-performers",
                            children=[
                                html.Div(id="top-bottom-performers-chart")
                            ]
                        )
                    ], width=6)
                ])
            ]
        )
    
    def _setup_callbacks(self):
        """Configurer les callbacks du dashboard."""
        # Callback pour les filtres du portefeuille
        @self.app.callback(
            [Output("asset-class-filter", "options"),
             Output("sector-filter", "options"),
             Output("currency-filter", "options")],
            [Input("tabs", "active_tab")]
        )
        def update_filters(active_tab):
            if self.portfolio_data is None:
                return [], [], []
            
            # Extraire les valeurs uniques pour chaque filtre
            asset_classes = sorted(self.portfolio_data['AssetClass'].unique())
            asset_class_options = [{'label': cls, 'value': cls} for cls in asset_classes]
            
            sectors = []
            if 'Sector' in self.portfolio_data.columns:
                sectors = sorted(self.portfolio_data['Sector'].unique())
            sector_options = [{'label': sector, 'value': sector} for sector in sectors]
            
            currencies = []
            if 'Currency' in self.portfolio_data.columns:
                currencies = sorted(self.portfolio_data['Currency'].unique())
            currency_options = [{'label': curr, 'value': curr} for curr in currencies]
            
            return asset_class_options, sector_options, currency_options
        
        # Callback pour appliquer les filtres et mettre à jour les graphiques d'allocation
        @self.app.callback(
            [Output("store-portfolio-filtered", "data"),
             Output("asset-allocation-chart", "children"),
             Output("sector-allocation-chart", "children"),
             Output("currency-allocation-chart", "children"),
             Output("portfolio-summary", "children"),
             Output("portfolio-table", "children")],
            [Input("apply-filters-button", "n_clicks")],
            [State("asset-class-filter", "value"),
             State("sector-filter", "value"),
             State("currency-filter", "value")]
        )
        def update_portfolio_view(n_clicks, asset_classes, sectors, currencies):
            if self.portfolio_data is None:
                return {}, "Aucune donnée de portefeuille disponible", "", "", "", ""
            
            # Filtrer le portefeuille
            filtered_portfolio = self.portfolio_data.copy()
            
            if asset_classes:
                filtered_portfolio = filtered_portfolio[filtered_portfolio['AssetClass'].isin(asset_classes)]
            
            if sectors and 'Sector' in filtered_portfolio.columns:
                filtered_portfolio = filtered_portfolio[filtered_portfolio['Sector'].isin(sectors)]
            
            if currencies and 'Currency' in filtered_portfolio.columns:
                filtered_portfolio = filtered_portfolio[filtered_portfolio['Currency'].isin(currencies)]
            
            # Créer les graphiques d'allocation
            asset_allocation_fig = self._create_allocation_chart(
                filtered_portfolio, 'AssetClass', 'Allocation par Classe d\'Actifs')
            
            sector_allocation_fig = None
            if 'Sector' in filtered_portfolio.columns:
                sector_allocation_fig = self._create_allocation_chart(
                    filtered_portfolio, 'Sector', 'Allocation par Secteur')
            
            currency_allocation_fig = None
            if 'Currency' in filtered_portfolio.columns:
                currency_allocation_fig = self._create_allocation_chart(
                    filtered_portfolio, 'Currency', 'Allocation par Devise')
            
            # Créer le résumé du portefeuille
            summary = self._create_portfolio_summary(filtered_portfolio)
            
            # Créer la table détaillée du portefeuille
            table = self._create_portfolio_table(filtered_portfolio)
            
            # Stocker le portefeuille filtré pour d'autres callbacks
            portfolio_json = filtered_portfolio.to_json(orient='split', date_format='iso')
            
            return (
                portfolio_json,
                dcc.Graph(figure=asset_allocation_fig),
                dcc.Graph(figure=sector_allocation_fig) if sector_allocation_fig else "",
                dcc.Graph(figure=currency_allocation_fig) if currency_allocation_fig else "",
                summary,
                table
            )
        
        # Callback pour calculer et afficher les métriques de risque
        @self.app.callback(
            [Output("var-metrics", "children"),
             Output("volatility-metrics", "children"),
             Output("correlation-metrics", "children"),
             Output("var-contribution-chart", "children"),
             Output("risk-contribution-table", "children"),
             Output("returns-distribution-chart", "children"),
             Output("returns-statistics", "children")],
            [Input("calculate-risk-button", "n_clicks")],
            [State("confidence-level-slider", "value"),
             State("time-horizon-radio", "value"),
             State("var-method-dropdown", "value"),
             State("store-portfolio-filtered", "data")]
        )
        def update_risk_metrics(n_clicks, confidence_level, time_horizon, var_method, portfolio_json):
            if n_clicks is None or not portfolio_json or self.returns_data is None:
                return [html.Div("Cliquez sur 'Calculer' pour afficher les métriques de risque")] * 7
            
            # Convertir le portefeuille JSON en DataFrame
            filtered_portfolio = pd.read_json(portfolio_json, orient='split')
            
            # Calculer les métriques de risque
            # Note: Dans une implémentation réelle, ces calculs seraient effectués
            # en utilisant les modules de risque que nous avons développés
            
            # Créer des métriques fictives pour la démonstration
            risk_metrics = {
                'var': {
                    'value': 0.05,  # 5% du portefeuille
                    'method': var_method,
                    'confidence_level': confidence_level,
                    'time_horizon': time_horizon
                },
                'cvar': {
                    'value': 0.07  # 7% du portefeuille
                },
                'volatility': {
                    'daily': 0.01,  # 1% par jour
                    'annualized': 0.15  # 15% par an
                },
                'correlation': {
                    'matrix': np.random.rand(5, 5)  # Matrice de corrélation fictive
                }
            }
            
            # Mise à jour des métriques de risque du dashboard
            self.risk_metrics = risk_metrics
            
            # Créer les affichages des métriques
            var_display = self._create_var_metrics_display(risk_metrics)
            volatility_display = self._create_volatility_metrics_display(risk_metrics)
            correlation_display = self._create_correlation_metrics_display(risk_metrics)
            
            # Créer les graphiques et tableaux
            contribution_chart = self._create_var_contribution_chart(filtered_portfolio, risk_metrics)
            contribution_table = self._create_risk_contribution_table(filtered_portfolio, risk_metrics)
            distribution_chart = self._create_returns_distribution_chart(self.returns_data)
            statistics = self._create_returns_statistics(self.returns_data)
            
            return (
                var_display,
                volatility_display,
                correlation_display,
                dcc.Graph(figure=contribution_chart),
                contribution_table,
                dcc.Graph(figure=distribution_chart),
                statistics
            )
        
        # Callback pour exécuter les stress-tests
        @self.app.callback(
            [Output("store-selected-scenario", "data"),
             Output("stress-test-summary-chart", "children"),
             Output("stress-test-impact-chart", "children"),
             Output("stress-test-details-table", "children")],
            [Input("run-stress-test-button", "n_clicks"),
             Input("create-custom-scenario-button", "n_clicks")],
            [State("scenario-dropdown", "value"),
             State("severity-slider", "value"),
             State("custom-scenario-name", "value"),
             State("custom-scenario-description", "value"),
             State("equity-shock", "value"),
             State("interest-rate-shock", "value"),
             State("credit-spread-shock", "value"),
             State("volatility-shock", "value"),
             State("store-portfolio-filtered", "data")]
        )
        def run_stress_test(
            run_clicks, create_clicks, selected_scenarios, severity,
            custom_name, custom_desc, equity_shock, rate_shock, spread_shock, vol_shock,
            portfolio_json
        ):
            ctx = callback_context
            if not ctx.triggered or not portfolio_json:
                return {}, "Sélectionnez des scénarios et cliquez sur 'Exécuter'", "", ""
            
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
            
            # Convertir le portefeuille JSON en DataFrame
            filtered_portfolio = pd.read_json(portfolio_json, orient='split')
            
            # Liste pour stocker les scénarios à exécuter
            scenarios_to_run = []
            
            if button_id == "run-stress-test-button" and selected_scenarios:
                # Exécuter les scénarios sélectionnés
                for scenario_id in selected_scenarios:
                    # Dans une implémentation réelle, nous utiliserions ScenarioGenerator
                    # pour obtenir les scénarios prédéfinis avec la sévérité ajustée
                    scenario = {
                        'name': scenario_id,
                        'description': f"Scénario: {scenario_id} (sévérité: {severity}x)",
                        'severity': severity,
                        'shocks': {
                            'equity': -0.15 * severity if scenario_id in ['financial_crisis_2008', 'rate_shock'] else -0.05 * severity,
                            'interest_rate': 0.01 * severity if scenario_id in ['rate_shock', 'inflation_shock'] else -0.005 * severity,
                            'credit_spread': 0.005 * severity
                        }
                    }
                    scenarios_to_run.append(scenario)
            
            elif button_id == "create-custom-scenario-button" and custom_name:
                # Créer et exécuter un scénario personnalisé
                custom_scenario = {
                    'name': custom_name,
                    'description': custom_desc or f"Scénario personnalisé: {custom_name}",
                    'shocks': {}
                }
                
                # Ajouter les chocs définis par l'utilisateur
                if equity_shock is not None:
                    custom_scenario['shocks']['equity'] = float(equity_shock)
                if rate_shock is not None:
                    custom_scenario['shocks']['interest_rate'] = float(rate_shock)
                if spread_shock is not None:
                    custom_scenario['shocks']['credit_spread'] = float(spread_shock)
                if vol_shock is not None:
                    custom_scenario['shocks']['volatility'] = float(vol_shock)
                
                scenarios_to_run.append(custom_scenario)
            
            if not scenarios_to_run:
                return {}, "Aucun scénario sélectionné", "", ""
            
            # Stocker les scénarios
            scenarios_json = json.dumps(scenarios_to_run)
            
            # Simuler l'application des scénarios au portefeuille
            # Dans une implémentation réelle, nous utiliserions la fonction apply_scenario_to_portfolio
            
            # Créer les graphiques et tableaux des résultats
            summary_chart = self._create_stress_test_summary_chart(filtered_portfolio, scenarios_to_run)
            impact_chart = self._create_stress_test_impact_chart(filtered_portfolio, scenarios_to_run)
            details_table = self._create_stress_test_details_table(filtered_portfolio, scenarios_to_run)
            
            return (
                scenarios_json,
                dcc.Graph(figure=summary_chart),
                dcc.Graph(figure=impact_chart),
                details_table
            )
        
        # Callback pour afficher les performances
        @self.app.callback(
            [Output("store-selected-timeframe", "data"),
             Output("cumulative-returns-chart", "children"),
             Output("drawdown-chart", "children"),
             Output("performance-statistics", "children"),
             Output("performance-by-asset-chart", "children"),
             Output("top-bottom-performers-chart", "children")],
            [Input("apply-timeframe-button", "n_clicks")],
            [State("timeframe-radio", "value"),
             State("date-range-picker", "start_date"),
             State("date-range-picker", "end_date"),
             State("store-portfolio-filtered", "data")]
        )
        def update_performance_view(n_clicks, timeframe, start_date, end_date, portfolio_json):
            if n_clicks is None or not portfolio_json or self.returns_data is None:
                return {}, "Sélectionnez une période et cliquez sur 'Appliquer'", "", "", "", ""
            
            # Convertir le portefeuille JSON en DataFrame
            filtered_portfolio = pd.read_json(portfolio_json, orient='split')
            
            # Convertir les dates sélectionnées en objets datetime
            start_date = pd.to_datetime(start_date)
            end_date = pd.to_datetime(end_date)
            
            # Stocker les informations de période
            timeframe_info = {
                'timeframe': timeframe,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d')
            }
            timeframe_json = json.dumps(timeframe_info)
            
            # Filtrer les données de rendements pour la période sélectionnée
            # Dans une implémentation réelle, nous utiliserions les données réelles
            
            # Créer les graphiques et statistiques de performance
            cumulative_returns_chart = self._create_cumulative_returns_chart(self.returns_data, timeframe_info)
            drawdown_chart = self._create_drawdown_chart(self.returns_data, timeframe_info)
            performance_stats = self._create_performance_statistics(self.returns_data, timeframe_info)
            asset_performance_chart = self._create_asset_performance_chart(self.returns_data, filtered_portfolio, timeframe_info)
            top_bottom_chart = self._create_top_bottom_performers_chart(self.returns_data, filtered_portfolio, timeframe_info)
            
            return (
                timeframe_json,
                dcc.Graph(figure=cumulative_returns_chart),
                dcc.Graph(figure=drawdown_chart),
                performance_stats,
                dcc.Graph(figure=asset_performance_chart),
                dcc.Graph(figure=top_bottom_chart)
            )
    
    def _create_allocation_chart(self, portfolio_data, category_column, title):
        """
        Créer un graphique d'allocation en camembert.
        
        Args:
            portfolio_data: Données du portefeuille
            category_column: Colonne à utiliser pour la catégorisation
            title: Titre du graphique
            
        Returns:
            Figure Plotly
        """
        if 'MarketValue' not in portfolio_data.columns:
            # Si MarketValue n'est pas disponible, utiliser Quantity comme proxy
            value_column = 'Quantity'
        else:
            value_column = 'MarketValue'
        
        # Agréger par catégorie
        allocation = portfolio_data.groupby(category_column)[value_column].sum().reset_index()
        
        # Calculer les pourcentages
        total = allocation[value_column].sum()
        allocation['Percentage'] = allocation[value_column] / total * 100
        
        # Créer le graphique
        fig = px.pie(
            allocation, 
            values='Percentage', 
            names=category_column, 
            title=title,
            hover_data=[value_column],
            labels={'Percentage': 'Allocation (%)', value_column: 'Valeur'}
        )
        
        # Personnaliser le graphique
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(
            margin=dict(l=20, r=20, t=40, b=20),
            legend=dict(orientation='h', yanchor='bottom', y=-0.2, xanchor='center', x=0.5)
        )
        
        return fig
    
    def _create_portfolio_summary(self, portfolio_data):
        """
        Créer un résumé du portefeuille.
        
        Args:
            portfolio_data: Données du portefeuille
            
        Returns:
            Composant HTML avec le résumé
        """
        if 'MarketValue' not in portfolio_data.columns:
            return html.Div("Données insuffisantes pour le résumé")
        
        total_value = portfolio_data['MarketValue'].sum()
        num_assets = len(portfolio_data)
        num_asset_classes = len(portfolio_data['AssetClass'].unique())
        
        currencies = []
        if 'Currency' in portfolio_data.columns:
            currencies = portfolio_data['Currency'].unique()
        num_currencies = len(currencies)
        
        # Trouver les plus grandes positions
        top_positions = portfolio_data.nlargest(3, 'MarketValue')
        
        summary = html.Div([
            dbc.Card(
                dbc.CardBody([
                    html.H5("Valeur Totale"),
                    html.H3(f"{total_value:,.2f}")
                ]),
                className="mb-2"
            ),
            html.P(f"Nombre d'actifs: {num_assets}"),
            html.P(f"Classes d'actifs: {num_asset_classes}"),
            html.P(f"Devises: {num_currencies}"),
            html.Hr(),
            html.H5("Principales Positions:"),
            html.Ul([
                html.Li(f"{row['Security']} ({row['Ticker']}): "
                        f"{row['MarketValue']:,.2f} ({row['MarketValue']/total_value*100:.1f}%)")
                for _, row in top_positions.iterrows()
            ])
        ])
        
        return summary
    
    def _create_portfolio_table(self, portfolio_data):
        """
        Créer une table détaillée du portefeuille.
        
        Args:
            portfolio_data: Données du portefeuille
            
        Returns:
            Composant HTML avec la table
        """
        if portfolio_data.empty:
            return html.Div("Aucune donnée disponible")
        
        # Sélectionner les colonnes à afficher
        display_columns = ['Security', 'Ticker', 'Quantity', 'Price', 'MarketValue', 'Weight', 'AssetClass']
        if 'Currency' in portfolio_data.columns:
            display_columns.append('Currency')
        if 'Sector' in portfolio_data.columns:
            display_columns.append('Sector')
        
        # Filtrer les colonnes disponibles
        columns = [col for col in display_columns if col in portfolio_data.columns]
        
        # Créer la table
        table = dash.dash_table.DataTable(
            id='portfolio-datatable',
            columns=[{'name': col, 'id': col} for col in columns],
            data=portfolio_data[columns].to_dict('records'),
            sort_action='native',
            filter_action='native',
            page_size=15,
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '8px',
                'minWidth': '100px',
                'width': '150px',
                'maxWidth': '200px',
                'overflow': 'hidden',
                'textOverflow': 'ellipsis'
            },
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'
                }
            ],
            export_format='csv'
        )
        
        return table
    
    def _create_var_metrics_display(self, risk_metrics):
        """
        Créer l'affichage des métriques VaR.
        
        Args:
            risk_metrics: Dictionnaire des métriques de risque
            
        Returns:
            Composant HTML avec les métriques VaR
        """
        if not risk_metrics or 'var' not in risk_metrics:
            return html.Div("Métriques VaR non disponibles")
        
        var_value = risk_metrics['var']['value']
        cvar_value = risk_metrics['cvar']['value'] if 'cvar' in risk_metrics else None
        confidence_level = risk_metrics['var'].get('confidence_level', 0.95)
        time_horizon = risk_metrics['var'].get('time_horizon', 1)
        method = risk_metrics['var'].get('method', 'historical')
        
        # Mapper les noms de méthode
        method_names = {
            'historical': 'Historique',
            'parametric': 'Paramétrique',
            'monte_carlo': 'Monte Carlo'
        }
        method_name = method_names.get(method, method)
        
        # Créer l'affichage
        var_display = html.Div([
            dbc.Card(
                dbc.CardBody([
                    html.H5(f"Value at Risk ({confidence_level*100:.0f}%, {time_horizon} jour{'s' if time_horizon > 1 else ''})"),
                    html.H3(f"{var_value*100:.2f}%"),
                    html.P(f"Méthode: {method_name}")
                ]),
                className="mb-2"
            ),
            dbc.Card(
                dbc.CardBody([
                    html.H5(f"Conditional VaR ({confidence_level*100:.0f}%, {time_horizon} jour{'s' if time_horizon > 1 else ''})"),
                    html.H3(f"{cvar_value*100:.2f}%" if cvar_value is not None else "N/A")
                ]),
                className="mb-2"
            )
        ])
        
        return var_display
    
    def _create_volatility_metrics_display(self, risk_metrics):
        """
        Créer l'affichage des métriques de volatilité.
        
        Args:
            risk_metrics: Dictionnaire des métriques de risque
            
        Returns:
            Composant HTML avec les métriques de volatilité
        """
        if not risk_metrics or 'volatility' not in risk_metrics:
            return html.Div("Métriques de volatilité non disponibles")
        
        daily_vol = risk_metrics['volatility'].get('daily', None)
        annual_vol = risk_metrics['volatility'].get('annualized', None)
        
        vol_display = html.Div([
            dbc.Card(
                dbc.CardBody([
                    html.H5("Volatilité"),
                    html.Div([
                        html.P(f"Journalière: {daily_vol*100:.2f}%" if daily_vol is not None else "Journalière: N/A"),
                        html.P(f"Annualisée: {annual_vol*100:.2f}%" if annual_vol is not None else "Annualisée: N/A")
                    ])
                ]),
                className="mb-2"
            )
        ])
        
        return vol_display
    
    def _create_correlation_metrics_display(self, risk_metrics):
        """
        Créer l'affichage de la matrice de corrélation.
        
        Args:
            risk_metrics: Dictionnaire des métriques de risque
            
        Returns:
            Composant HTML avec la matrice de corrélation
        """
        if not risk_metrics or 'correlation' not in risk_metrics or 'matrix' not in risk_metrics['correlation']:
            return html.Div("Matrice de corrélation non disponible")
        
        corr_matrix = risk_metrics['correlation']['matrix']
        
        # Créer une heatmap pour la matrice de corrélation
        fig = px.imshow(
            corr_matrix,
            labels=dict(x="Actif", y="Actif", color="Corrélation"),
            x=['Actif ' + str(i+1) for i in range(corr_matrix.shape[1])],
            y=['Actif ' + str(i+1) for i in range(corr_matrix.shape[0])],
            title="Matrice de Corrélation"
        )
        
        fig.update_layout(
            margin=dict(l=20, r=20, t=40, b=20),
            height=400
        )
        
        return dcc.Graph(figure=fig)
    
    def _create_var_contribution_chart(self, portfolio_data, risk_metrics):
        """
        Créer un graphique de contribution à la VaR.
        
        Args:
            portfolio_data: Données du portefeuille
            risk_metrics: Dictionnaire des métriques de risque
            
        Returns:
            Figure Plotly
        """
        # Simuler des contributions à la VaR pour la démonstration
        if portfolio_data.empty:
            return go.Figure()
        
        # Utiliser le poids du portefeuille comme proxy pour la contribution à la VaR
        if 'Weight' in portfolio_data.columns:
            contrib_data = portfolio_data[['Security', 'Weight']].copy()
        else:
            # Si les poids ne sont pas disponibles, simuler des contributions
            contrib_data = portfolio_data[['Security']].copy()
            contrib_data['Weight'] = np.random.random(size=len(contrib_data))
            contrib_data['Weight'] = contrib_data['Weight'] / contrib_data['Weight'].sum()
        
        # Renommer la colonne pour plus de clarté
        contrib_data = contrib_data.rename(columns={'Weight': 'Contribution'})
        
        # Trier par contribution
        contrib_data = contrib_data.sort_values('Contribution', ascending=False)
        
        # Créer le graphique
        fig = px.bar(
            contrib_data,
            x='Security',
            y='Contribution',
            title="Contribution à la VaR par Position",
            labels={'Security': 'Position', 'Contribution': 'Contribution à la VaR'}
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            margin=dict(l=20, r=20, t=40, b=80)
        )
        
        return fig
    
    def _create_risk_contribution_table(self, portfolio_data, risk_metrics):
        """
        Créer une table de contribution au risque.
        
        Args:
            portfolio_data: Données du portefeuille
            risk_metrics: Dictionnaire des métriques de risque
            
        Returns:
            Composant HTML avec la table
        """
        if portfolio_data.empty:
            return html.Div("Aucune donnée disponible")
        
        # Simuler des contributions au risque pour la démonstration
        risk_data = portfolio_data[['Security', 'Ticker', 'AssetClass']].copy()
        
        # Ajouter des colonnes de risque simulées
        risk_data['Volatilité'] = np.random.uniform(0.05, 0.30, size=len(risk_data))
        risk_data['ContributionVaR'] = np.random.uniform(0.01, 0.10, size=len(risk_data))
        risk_data['ContributionVaR%'] = risk_data['ContributionVaR'] / risk_data['ContributionVaR'].sum() * 100
        risk_data['Beta'] = np.random.uniform(0.5, 1.5, size=len(risk_data))
        
        # Créer la table
        table = dash.dash_table.DataTable(
            id='risk-contribution-datatable',
            columns=[
                {'name': 'Titre', 'id': 'Security'},
                {'name': 'Ticker', 'id': 'Ticker'},
                {'name': 'Classe d\'actif', 'id': 'AssetClass'},
                {'name': 'Volatilité', 'id': 'Volatilité', 'type': 'numeric', 'format': {'specifier': '.2%'}},
                {'name': 'Contribution VaR', 'id': 'ContributionVaR', 'type': 'numeric', 'format': {'specifier': '.2%'}},
                {'name': 'Contribution VaR %', 'id': 'ContributionVaR%', 'type': 'numeric', 'format': {'specifier': '.2f'}},
                {'name': 'Beta', 'id': 'Beta', 'type': 'numeric', 'format': {'specifier': '.2f'}}
            ],
            data=risk_data.to_dict('records'),
            sort_action='native',
            filter_action='native',
            page_size=10,
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '8px',
                'minWidth': '100px',
                'width': '150px',
                'maxWidth': '200px',
                'overflow': 'hidden',
                'textOverflow': 'ellipsis'
            },
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'
                }
            ]
        )
        
        return table
    
    def _create_returns_distribution_chart(self, returns_data):
        """
        Créer un graphique de distribution des rendements.
        
        Args:
            returns_data: DataFrame des rendements
            
        Returns:
            Figure Plotly
        """
        if returns_data is None or returns_data.empty:
            return go.Figure()
        
        # Simuler des rendements pour la démonstration si nécessaire
        if isinstance(returns_data, pd.DataFrame) and 'portfolio' not in returns_data.columns:
            # Simuler des rendements de portefeuille
            portfolio_returns = np.random.normal(0.0002, 0.01, size=len(returns_data))
        else:
            portfolio_returns = returns_data['portfolio'].values
        
        # Créer l'histogramme
        fig = go.Figure()
        
        fig.add_trace(go.Histogram(
            x=portfolio_returns,
            nbinsx=50,
            name='Rendements',
            marker_color='blue',
            opacity=0.7
        ))
        
        # Ajouter une courbe de distribution normale
        x_vals = np.linspace(min(portfolio_returns), max(portfolio_returns), 100)
        y_vals = stats.norm.pdf(x_vals, np.mean(portfolio_returns), np.std(portfolio_returns))
        
        fig.add_trace(go.Scatter(
            x=x_vals,
            y=y_vals,
            mode='lines',
            name='Distribution normale',
            line=dict(color='red')
        ))
        
        # Personnaliser le graphique
        fig.update_layout(
            title="Distribution des Rendements du Portefeuille",
            xaxis_title="Rendement",
            yaxis_title="Fréquence",
            bargap=0.01,
            bargroupgap=0.05,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        return fig
    
    def _create_returns_statistics(self, returns_data):
        """
        Créer un résumé des statistiques de rendements.
        
        Args:
            returns_data: DataFrame des rendements
            
        Returns:
            Composant HTML avec les statistiques
        """
        if returns_data is None or returns_data.empty:
            return html.Div("Statistiques de rendements non disponibles")
        
        # Simuler des rendements pour la démonstration si nécessaire
        if isinstance(returns_data, pd.DataFrame) and 'portfolio' not in returns_data.columns:
            # Simuler des rendements de portefeuille
            portfolio_returns = np.random.normal(0.0002, 0.01, size=len(returns_data))
        else:
            portfolio_returns = returns_data['portfolio'].values
        
        # Calculer les statistiques
        mean_return = np.mean(portfolio_returns)
        std_return = np.std(portfolio_returns)
        skewness = stats.skew(portfolio_returns)
        kurtosis = stats.kurtosis(portfolio_returns)
        sharpe = mean_return / std_return if std_return > 0 else 0
        
        # Créer l'affichage
        stats_display = html.Div([
            dbc.Card(
                dbc.CardBody([
                    html.H5("Statistiques des Rendements"),
                    html.Table([
                        html.Tr([html.Td("Rendement moyen:"), html.Td(f"{mean_return*100:.4f}%")]),
                        html.Tr([html.Td("Écart-type:"), html.Td(f"{std_return*100:.4f}%")]),
                        html.Tr([html.Td("Asymétrie:"), html.Td(f"{skewness:.4f}")]),
                        html.Tr([html.Td("Kurtosis:"), html.Td(f"{kurtosis:.4f}")]),
                        html.Tr([html.Td("Ratio de Sharpe:"), html.Td(f"{sharpe:.4f}")])
                    ], style={'width': '100%'})
                ]),
                className="mb-2"
            )
        ])
        
        return stats_display
    
    def _create_stress_test_summary_chart(self, portfolio_data, scenarios):
        """
        Créer un graphique de résumé des stress-tests.
        
        Args:
            portfolio_data: Données du portefeuille
            scenarios: Liste des scénarios
            
        Returns:
            Figure Plotly
        """
        if portfolio_data.empty or not scenarios:
            return go.Figure()
        
        # Simuler les impacts des scénarios sur le portefeuille
        scenario_names = [s['name'] for s in scenarios]
        
        # Simuler l'impact en pourcentage
        impacts = []
        for scenario in scenarios:
            # Simuler un impact basé sur les chocs définis dans le scénario
            shocks = scenario['shocks']
            equity_shock = shocks.get('equity', 0)
            rate_shock = shocks.get('interest_rate', 0)
            
            # Simuler un impact plus négatif pour les scénarios avec des chocs d'actions négatifs
            impact = equity_shock * 0.6 + rate_shock * 0.3 + np.random.uniform(-0.02, 0.01)
            impacts.append(impact)
        
        # Créer le graphique
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=scenario_names,
            y=impacts,
            marker_color=['red' if i < 0 else 'green' for i in impacts],
            text=[f"{i*100:.2f}%" for i in impacts],
            textposition='auto'
        ))
        
        fig.update_layout(
            title="Impact des Scénarios sur le Portefeuille",
            xaxis_title="Scénario",
            yaxis_title="Impact (%)",
            yaxis_tickformat='.2%',
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        return fig
    
    def _create_stress_test_impact_chart(self, portfolio_data, scenarios):
        """
        Créer un graphique d'impact des stress-tests par classe d'actifs.
        
        Args:
            portfolio_data: Données du portefeuille
            scenarios: Liste des scénarios
            
        Returns:
            Figure Plotly
        """
        if portfolio_data.empty or not scenarios:
            return go.Figure()
        
        # Obtenir les classes d'actifs uniques
        asset_classes = sorted(portfolio_data['AssetClass'].unique())
        
        # Simuler les impacts par classe d'actifs pour chaque scénario
        scenario_names = [s['name'] for s in scenarios]
        impacts_by_asset = {}
        
        for asset_class in asset_classes:
            impacts = []
            for scenario in scenarios:
                # Simuler un impact basé sur les chocs définis dans le scénario
                shocks = scenario['shocks']
                equity_shock = shocks.get('equity', 0)
                rate_shock = shocks.get('interest_rate', 0)
                
                # Ajuster l'impact en fonction de la classe d'actifs
                if asset_class == 'Equity':
                    impact = equity_shock * 1.2 + np.random.uniform(-0.02, 0.02)
                elif asset_class in ['Bond', 'Fixed Income', 'Sovereign']:
                    impact = rate_shock * 1.5 + np.random.uniform(-0.01, 0.01)
                else:
                    impact = equity_shock * 0.5 + rate_shock * 0.3 + np.random.uniform(-0.015, 0.015)
                
                impacts.append(impact)
            
            impacts_by_asset[asset_class] = impacts
        
        # Créer le graphique
        fig = go.Figure()
        
        for asset_class, impacts in impacts_by_asset.items():
            fig.add_trace(go.Bar(
                name=asset_class,
                x=scenario_names,
                y=impacts,
                text=[f"{i*100:.2f}%" for i in impacts],
                textposition='auto'
            ))
        
        fig.update_layout(
            title="Impact des Scénarios par Classe d'Actifs",
            xaxis_title="Scénario",
            yaxis_title="Impact (%)",
            yaxis_tickformat='.2%',
            barmode='group',
            margin=dict(l=20, r=20, t=40, b=80)
        )
        
        return fig
    
    def _create_stress_test_details_table(self, portfolio_data, scenarios):
        """
        Créer une table détaillée des résultats de stress-test.
        
        Args:
            portfolio_data: Données du portefeuille
            scenarios: Liste des scénarios
            
        Returns:
            Composant HTML avec la table
        """
        if portfolio_data.empty or not scenarios:
            return html.Div("Aucun résultat disponible")
        
        # Créer un DataFrame pour les résultats
        results = []
        
        for scenario in scenarios:
            scenario_name = scenario['name']
            shocks = scenario['shocks']
            
            for _, row in portfolio_data.iterrows():
                security = row['Security']
                ticker = row['Ticker']
                asset_class = row['AssetClass']
                market_value = row['MarketValue'] if 'MarketValue' in row else 0
                
                # Simuler un impact basé sur la classe d'actifs et les chocs
                equity_shock = shocks.get('equity', 0)
                rate_shock = shocks.get('interest_rate', 0)
                
                if asset_class == 'Equity':
                    impact_pct = equity_shock * 1.2 + np.random.uniform(-0.02, 0.02)
                elif asset_class in ['Bond', 'Fixed Income', 'Sovereign']:
                    impact_pct = rate_shock * 1.5 + np.random.uniform(-0.01, 0.01)
                else:
                    impact_pct = equity_shock * 0.5 + rate_shock * 0.3 + np.random.uniform(-0.015, 0.015)
                
                impact_value = market_value * impact_pct
                
                results.append({
                    'Scénario': scenario_name,
                    'Security': security,
                    'Ticker': ticker,
                    'AssetClass': asset_class,
                    'MarketValue': market_value,
                    'ImpactPct': impact_pct,
                    'ImpactValue': impact_value
                })
        
        results_df = pd.DataFrame(results)
        
        # Créer la table
        table = dash.dash_table.DataTable(
            id='stress-test-details-datatable',
            columns=[
                {'name': 'Scénario', 'id': 'Scénario'},
                {'name': 'Titre', 'id': 'Security'},
                {'name': 'Ticker', 'id': 'Ticker'},
                {'name': 'Classe d\'actif', 'id': 'AssetClass'},
                {'name': 'Valeur de marché', 'id': 'MarketValue', 'type': 'numeric', 'format': {'specifier': ',.2f'}},
                {'name': 'Impact %', 'id': 'ImpactPct', 'type': 'numeric', 'format': {'specifier': '.2%'}},
                {'name': 'Impact valeur', 'id': 'ImpactValue', 'type': 'numeric', 'format': {'specifier': ',.2f'}}
            ],
            data=results_df.to_dict('records'),
            sort_action='native',
            filter_action='native',
            page_size=15,
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '8px',
                'minWidth': '100px',
                'width': '150px',
                'maxWidth': '200px',
                'overflow': 'hidden',
                'textOverflow': 'ellipsis'
            },
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'
                },
                {
                    'if': {
                        'filter_query': '{ImpactPct} < 0',
                        'column_id': 'ImpactPct'
                    },
                    'color': 'red'
                },
                {
                    'if': {
                        'filter_query': '{ImpactValue} < 0',
                        'column_id': 'ImpactValue'
                    },
                    'color': 'red'
                }
            ],
            export_format='csv'
        )
        
        return table
    
    def _create_cumulative_returns_chart(self, returns_data, timeframe_info):
        """
        Créer un graphique des rendements cumulatifs.
        
        Args:
            returns_data: DataFrame des rendements
            timeframe_info: Informations sur la période
            
        Returns:
            Figure Plotly
        """
        if returns_data is None or returns_data.empty:
            return go.Figure()
        
        # Simuler des rendements pour la démonstration
        dates = pd.date_range(end=datetime.now(), periods=252, freq='B')
        
        # Simuler des rendements pour quelques indices/benchmarks
        np.random.seed(42)  # Pour la reproductibilité
        returns = pd.DataFrame({
            'Portfolio': np.random.normal(0.0005, 0.010, len(dates)),
            'S&P 500': np.random.normal(0.0004, 0.011, len(dates)),
            'MSCI World': np.random.normal(0.0003, 0.009, len(dates))
        }, index=dates)
        
        # Calculer les rendements cumulatifs
        cumulative_returns = (1 + returns).cumprod() - 1
        
        # Créer le graphique
        fig = go.Figure()
        
        for col in cumulative_returns.columns:
            fig.add_trace(go.Scatter(
                x=cumulative_returns.index,
                y=cumulative_returns[col],
                mode='lines',
                name=col
            ))
        
        fig.update_layout(
            title="Rendements Cumulatifs",
            xaxis_title="Date",
            yaxis_title="Rendement Cumulatif",
            yaxis_tickformat='.2%',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        return fig
    
    def _create_drawdown_chart(self, returns_data, timeframe_info):
        """
        Créer un graphique des drawdowns.
        
        Args:
            returns_data: DataFrame des rendements
            timeframe_info: Informations sur la période
            
        Returns:
            Figure Plotly
        """
        if returns_data is None or returns_data.empty:
            return go.Figure()
        
        # Simuler des rendements pour la démonstration
        dates = pd.date_range(end=datetime.now(), periods=252, freq='B')
        
        # Simuler des rendements pour le portefeuille
        np.random.seed(42)  # Pour la reproductibilité
        returns = pd.Series(np.random.normal(0.0005, 0.010, len(dates)), index=dates)
        
        # Calculer les rendements cumulatifs
        cumulative_returns = (1 + returns).cumprod()
        
        # Calculer les drawdowns
        running_max = cumulative_returns.cummax()
        drawdowns = (cumulative_returns / running_max) - 1
        
        # Créer le graphique
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=drawdowns.index,
            y=drawdowns,
            mode='lines',
            name='Drawdown',
            fill='tozeroy',
            fillcolor='rgba(255, 0, 0, 0.3)',
            line=dict(color='red')
        ))
        
        fig.update_layout(
            title="Drawdowns",
            xaxis_title="Date",
            yaxis_title="Drawdown",
            yaxis_tickformat='.2%',
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        return fig
    
    def _create_performance_statistics(self, returns_data, timeframe_info):
        """
        Créer un résumé des statistiques de performance.
        
        Args:
            returns_data: DataFrame des rendements
            timeframe_info: Informations sur la période
            
        Returns:
            Composant HTML avec les statistiques
        """
        if returns_data is None or returns_data.empty:
            return html.Div("Statistiques de performance non disponibles")
        
        # Simuler des rendements pour la démonstration
        np.random.seed(42)  # Pour la reproductibilité
        returns = np.random.normal(0.0005, 0.010, 252)
        
        # Calculer les statistiques de performance
        total_return = (1 + returns).prod() - 1
        annualized_return = (1 + total_return) ** (252 / len(returns)) - 1
        volatility = np.std(returns) * np.sqrt(252)
        sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
        
        # Calculer le maximum drawdown
        cumulative_returns = (1 + np.array(returns)).cumprod()
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdowns = cumulative_returns / running_max - 1
        max_drawdown = np.min(drawdowns)
        
        # Créer l'affichage
        stats_display = html.Div([
            dbc.Card(
                dbc.CardBody([
                    html.H5("Statistiques de Performance"),
                    html.Table([
                        html.Tr([html.Td("Rendement total:"), html.Td(f"{total_return*100:.2f}%")]),
                        html.Tr([html.Td("Rendement annualisé:"), html.Td(f"{annualized_return*100:.2f}%")]),
                        html.Tr([html.Td("Volatilité annualisée:"), html.Td(f"{volatility*100:.2f}%")]),
                        html.Tr([html.Td("Ratio de Sharpe:"), html.Td(f"{sharpe_ratio:.2f}")]),
                        html.Tr([html.Td("Drawdown maximum:"), html.Td(f"{max_drawdown*100:.2f}%")])
                    ], style={'width': '100%'})
                ]),
                className="mb-2"
            )
        ])
        
        return stats_display
    
    def _create_asset_performance_chart(self, returns_data, portfolio_data, timeframe_info):
        """
        Créer un graphique de performance par classe d'actifs.
        
        Args:
            returns_data: DataFrame des rendements
            portfolio_data: Données du portefeuille
            timeframe_info: Informations sur la période
            
        Returns:
            Figure Plotly
        """
        if portfolio_data.empty:
            return go.Figure()
        
        # Obtenir les classes d'actifs uniques
        asset_classes = sorted(portfolio_data['AssetClass'].unique())
        
        # Simuler les rendements par classe d'actifs
        np.random.seed(42)  # Pour la reproductibilité
        performance = {}
        
        for asset_class in asset_classes:
            # Simuler un rendement pour chaque classe d'actifs
            performance[asset_class] = np.random.uniform(-0.10, 0.25)
        
        # Créer le graphique
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=list(performance.keys()),
            y=list(performance.values()),
            marker_color=['red' if v < 0 else 'green' for v in performance.values()],
            text=[f"{v*100:.2f}%" for v in performance.values()],
            textposition='auto'
        ))
        
        fig.update_layout(
            title="Performance par Classe d'Actifs",
            xaxis_title="Classe d'actif",
            yaxis_title="Performance",
            yaxis_tickformat='.2%',
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        return fig
    
    def _create_top_bottom_performers_chart(self, returns_data, portfolio_data, timeframe_info):
        """
        Créer un graphique des meilleurs et pires performers.
        
        Args:
            returns_data: DataFrame des rendements
            portfolio_data: Données du portefeuille
            timeframe_info: Informations sur la période
            
        Returns:
            Figure Plotly
        """
        if portfolio_data.empty:
            return go.Figure()
        
        # Simuler les performances individuelles pour la démonstration
        performance = {}
        
        for _, row in portfolio_data.iterrows():
            security = row['Security']
            # Simuler une performance
            performance[security] = np.random.uniform(-0.20, 0.40)
        
        # Trier les performances
        sorted_performance = sorted(performance.items(), key=lambda x: x[1])
        
        # Prendre les 5 meilleurs et les 5 pires performers
        bottom_5 = sorted_performance[:5]
        top_5 = sorted_performance[-5:]
        
        # Créer les données pour le graphique
        securities = [item[0] for item in bottom_5] + [item[0] for item in top_5]
        values = [item[1] for item in bottom_5] + [item[1] for item in top_5]
        colors = ['red'] * 5 + ['green'] * 5
        
        # Créer le graphique
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=securities,
            y=values,
            marker_color=colors,
            text=[f"{v*100:.2f}%" for v in values],
            textposition='auto'
        ))
        
        fig.update_layout(
            title="Top 5 / Bottom 5 Performers",
            xaxis_title="Titre",
            yaxis_title="Performance",
            yaxis_tickformat='.2%',
            xaxis_tickangle=-45,
            margin=dict(l=20, r=20, t=40, b=80)
        )
        
        return fig
    
    def run_server(self, debug=False, host='0.0.0.0', port=8050):
        """
        Lancer le serveur Dash.
        
        Args:
            debug: Mode debug
            host: Hôte du serveur
            port: Port du serveur
        """
        self.app.run_server(debug=debug, host=host, port=port)


# Exemple d'utilisation
if __name__ == "__main__":
    # Créer des données de démonstration
    portfolio_data = pd.DataFrame({
        'Security': ['Apple Inc.', 'Microsoft Corp.', 'Amazon.com Inc.', 'Alphabet Inc.', 'Meta Platforms Inc.'],
        'Ticker': ['AAPL', 'MSFT', 'AMZN', 'GOOG', 'META'],
        'Quantity': [100, 50, 20, 15, 40],
        'AssetClass': ['Equity', 'Equity', 'Equity', 'Equity', 'Equity'],
        'Sector': ['Technology', 'Technology', 'Consumer Discretionary', 'Communication Services', 'Communication Services'],
        'Currency': ['USD', 'USD', 'USD', 'USD', 'USD'],
        'Price': [150.0, 300.0, 3000.0, 2500.0, 300.0],
        'MarketValue': [15000.0, 15000.0, 60000.0, 37500.0, 12000.0],
        'Weight': [0.108, 0.108, 0.432, 0.27, 0.082]
    })
    
    # Créer une instance du dashboard
    dashboard = RiskDashboard(
        title="Dashboard de Risque - Démo",
        portfolio_data=portfolio_data
    )
    
    # Lancer le serveur
    dashboard.run_server(debug=True)
