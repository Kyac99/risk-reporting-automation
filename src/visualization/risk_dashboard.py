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
        def update_risk_analysis(n_clicks, confidence_level, time_horizon, var_method, portfolio_json):
            if not n_clicks or not portfolio_json or self.returns_data is None:
                return "", "", "", "", "", "", ""
            
            # Convertir les données JSON en DataFrame
            portfolio = pd.read_json(portfolio_json, orient='split')
            
            # Ici, il faudrait calculer les métriques de risque réelles
            # Pour cet exemple, nous allons simuler des résultats
            
            # Simuler les métriques VaR
            var_metrics = html.Div([
                dbc.Card(
                    dbc.CardBody([
                        html.H5(f"VaR ({confidence_level*100:.0f}%, {time_horizon} jour{'s' if time_horizon > 1 else ''})"),
                        html.H3(f"{np.random.uniform(0.02, 0.05):.2%}"),
                        html.P(f"Méthode: {var_method.capitalize()}")
                    ]),
                    className="mb-2"
                ),
                dbc.Card(
                    dbc.CardBody([
                        html.H5(f"CVaR"),
                        html.H3(f"{np.random.uniform(0.03, 0.07):.2%}")
                    ]),
                    className="mb-2"
                )
            ])
            
            # Simuler les métriques de volatilité
            volatility_metrics = html.Div([
                dbc.Card(
                    dbc.CardBody([
                        html.H5("Volatilité Annualisée"),
                        html.H3(f"{np.random.uniform(0.10, 0.25):.2%}")
                    ]),
                    className="mb-2"
                ),
                dbc.Card(
                    dbc.CardBody([
                        html.H5("Beta vs Marché"),
                        html.H3(f"{np.random.uniform(0.8, 1.2):.2f}")
                    ]),
                    className="mb-2"
                )
            ])
            
            # Simuler la matrice de corrélation
            correlation_fig = px.imshow(
                np.random.uniform(-1, 1, size=(5, 5)),
                labels=dict(x="Asset", y="Asset", color="Correlation"),
                x=['Asset 1', 'Asset 2', 'Asset 3', 'Asset 4', 'Asset 5'],
                y=['Asset 1', 'Asset 2', 'Asset 3', 'Asset 4', 'Asset 5'],
                color_continuous_scale='RdBu_r',
                zmin=-1, zmax=1
            )
            correlation_fig.update_layout(
                title="Matrice de Corrélation",
                margin=dict(l=20, r=20, t=40, b=20)
            )
            
            # Simuler le graphique de contribution à la VaR
            contribution_data = pd.DataFrame({
                'Asset': [f"Asset {i+1}" for i in range(5)],
                'Contribution': np.random.uniform(0.05, 0.4, size=5)
            })
            contribution_data['Contribution'] /= contribution_data['Contribution'].sum()
            
            contribution_fig = px.bar(
                contribution_data,
                x='Asset',
                y='Contribution',
                title="Contribution à la VaR par Actif",
                text_auto='.1%',
                labels={'Contribution': 'Contribution à la VaR'}
            )
            contribution_fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
            
            # Simuler la table de contribution au risque
            risk_contribution_table = dash.dash_table.DataTable(
                id='risk-contribution-datatable',
                columns=[
                    {'name': 'Asset', 'id': 'Asset'},
                    {'name': 'Weight', 'id': 'Weight', 'type': 'numeric', 'format': {'specifier': '.2%'}},
                    {'name': 'VaR Contribution', 'id': 'VaR_Contribution', 'type': 'numeric', 'format': {'specifier': '.2%'}},
                    {'name': '% of Total VaR', 'id': 'Pct_Total_VaR', 'type': 'numeric', 'format': {'specifier': '.1%'}}
                ],
                data=[
                    {
                        'Asset': f"Asset {i+1}",
                        'Weight': np.random.uniform(0.05, 0.3),
                        'VaR_Contribution': np.random.uniform(0.001, 0.02),
                        'Pct_Total_VaR': contribution_data.iloc[i]['Contribution']
                    }
                    for i in range(5)
                ],
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left',
                    'padding': '8px'
                },
                style_header={
                    'backgroundColor': 'rgb(230, 230, 230)',
                    'fontWeight': 'bold'
                }
            )
            
            # Simuler la distribution des rendements
            returns_data = np.random.normal(0.0005, 0.01, size=1000)
            
            # Créer l'histogramme des rendements
            returns_fig = px.histogram(
                returns_data, 
                nbins=50,
                title="Distribution des Rendements",
                labels={'value': 'Rendement', 'count': 'Fréquence'},
                marginal="box"
            )
            
            # Ajouter des lignes pour la VaR et la CVaR
            var_value = np.percentile(returns_data, (1 - confidence_level) * 100)
            cvar_value = returns_data[returns_data <= var_value].mean()
            
            returns_fig.add_vline(
                x=var_value, 
                line_dash="dash", 
                line_color="red",
                annotation_text=f"VaR {confidence_level*100:.0f}%",
                annotation_position="top right"
            )
            
            returns_fig.add_vline(
                x=cvar_value, 
                line_dash="dot", 
                line_color="orange",
                annotation_text=f"CVaR",
                annotation_position="top left"
            )
            
            returns_fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
            
            # Calculer les statistiques des rendements
            returns_stats = html.Div([
                html.H5("Statistiques des Rendements"),
                html.Table([
                    html.Tr([html.Td("Moyenne"), html.Td(f"{np.mean(returns_data):.4f}")]),
                    html.Tr([html.Td("Médiane"), html.Td(f"{np.median(returns_data):.4f}")]),
                    html.Tr([html.Td("Écart-type"), html.Td(f"{np.std(returns_data):.4f}")]),
                    html.Tr([html.Td("Skewness"), html.Td(f"{float(pd.Series(returns_data).skew()):.4f}")]),
                    html.Tr([html.Td("Kurtosis"), html.Td(f"{float(pd.Series(returns_data).kurtosis()):.4f}")]),
                    html.Tr([html.Td("Min"), html.Td(f"{np.min(returns_data):.4f}")]),
                    html.Tr([html.Td("Max"), html.Td(f"{np.max(returns_data):.4f}")]),
                ], className="table table-striped table-sm")
            ])
            
            return (
                var_metrics,
                volatility_metrics,
                dcc.Graph(figure=correlation_fig),
                dcc.Graph(figure=contribution_fig),
                risk_contribution_table,
                dcc.Graph(figure=returns_fig),
                returns_stats
            )
        
        # Callback pour exécuter les stress-tests
        @self.app.callback(
            [Output("store-selected-scenario", "data"),
             Output("stress-test-summary-chart", "children"),
             Output("stress-test-impact-chart", "children"),
             Output("stress-test-details-table", "children")],
            [Input("run-stress-test-button", "n_clicks")],
            [State("scenario-dropdown", "value"),
             State("severity-slider", "value"),
             State("store-portfolio-filtered", "data")]
        )
        def run_stress_test(n_clicks, scenarios, severity, portfolio_json):
            if not n_clicks or not scenarios or not portfolio_json:
                return {}, "", "", ""
            
            # Convertir les données JSON en DataFrame
            portfolio = pd.read_json(portfolio_json, orient='split')
            
            # Créer une liste pour stocker les résultats des scénarios
            scenario_results = []
            
            # Pour chaque scénario sélectionné
            for scenario_name in scenarios:
                # Dans une application réelle, on utiliserait le générateur de scénarios
                # Pour cet exemple, nous allons simuler les résultats
                
                # Simuler l'impact du scénario sur le portefeuille
                impact_percentage = np.random.uniform(-0.25, -0.05) * severity
                scenario_results.append({
                    'name': scenario_name,
                    'description': f"Simulation du scénario {scenario_name}",
                    'impact_percentage': impact_percentage,
                    'impact_value': portfolio['MarketValue'].sum() * impact_percentage
                })
            
            # Stocker les résultats des scénarios pour d'autres callbacks
            scenarios_json = json.dumps(scenario_results)
            
            # Créer le graphique récapitulatif des impacts
            summary_data = pd.DataFrame(scenario_results)
            
            summary_fig = px.bar(
                summary_data,
                x='name',
                y='impact_percentage',
                title="Impact des Scénarios sur le Portefeuille",
                text_auto='.2%',
                labels={
                    'name': 'Scénario',
                    'impact_percentage': 'Impact (%)'
                }
            )
            summary_fig.update_traces(marker_color='red')
            summary_fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
            
            # Simuler l'impact par classe d'actifs
            asset_classes = portfolio['AssetClass'].unique()
            impact_by_asset = pd.DataFrame({
                'AssetClass': asset_classes,
                'BeforeStress': [portfolio[portfolio['AssetClass'] == cls]['MarketValue'].sum() for cls in asset_classes]
            })
            
            # Simuler les valeurs après stress pour chaque scénario
            for i, scenario in enumerate(scenario_results):
                # Simuler des impacts différents selon la classe d'actifs
                impacts = np.random.uniform(-0.3, -0.01, size=len(asset_classes)) * severity
                impact_by_asset[f'AfterStress_{i}'] = impact_by_asset['BeforeStress'] * (1 + impacts)
                impact_by_asset[f'Impact_{i}'] = impact_by_asset[f'AfterStress_{i}'] - impact_by_asset['BeforeStress']
                impact_by_asset[f'Impact_Pct_{i}'] = impact_by_asset[f'Impact_{i}'] / impact_by_asset['BeforeStress']
            
            # Créer le graphique d'impact par classe d'actifs
            impact_fig = go.Figure()
            
            # Ajouter les barres pour les valeurs avant stress
            impact_fig.add_trace(go.Bar(
                x=impact_by_asset['AssetClass'],
                y=impact_by_asset['BeforeStress'],
                name='Avant Stress',
                marker_color='blue'
            ))
            
            # Ajouter les barres pour le premier scénario (pour simplifier)
            if len(scenario_results) > 0:
                impact_fig.add_trace(go.Bar(
                    x=impact_by_asset['AssetClass'],
                    y=impact_by_asset['AfterStress_0'],
                    name=f'Après {scenario_results[0]["name"]}',
                    marker_color='red'
                ))
            
            impact_fig.update_layout(
                barmode='group',
                title="Impact par Classe d'Actifs",
                xaxis_title="Classe d'Actifs",
                yaxis_title="Valeur",
                margin=dict(l=20, r=20, t=40, b=20)
            )
            
            # Créer la table détaillée des résultats de stress-test
            details_table = dash.dash_table.DataTable(
                id='stress-details-datatable',
                columns=[
                    {'name': 'Classe d\'Actifs', 'id': 'AssetClass'},
                    {'name': 'Valeur Initiale', 'id': 'BeforeStress', 'type': 'numeric', 'format': {'specifier': ',.2f'}},
                ] + [
                    {'name': f'Après {scenario["name"]}', 'id': f'AfterStress_{i}', 'type': 'numeric', 'format': {'specifier': ',.2f'}}
                    for i, scenario in enumerate(scenario_results)
                ] + [
                    {'name': f'Impact {scenario["name"]} (%)', 'id': f'Impact_Pct_{i}', 'type': 'numeric', 'format': {'specifier': '.2%'}}
                    for i, scenario in enumerate(scenario_results)
                ],
                data=impact_by_asset.to_dict('records'),
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left',
                    'padding': '8px'
                },
                style_header={
                    'backgroundColor': 'rgb(230, 230, 230)',
                    'fontWeight': 'bold'
                },
                style_data_conditional=[
                    {
                        'if': {
                            'filter_query': '{{{0}}} < 0'.format(col),
                            'column_id': col
                        },
                        'color': 'red'
                    }
                    for col in [f'Impact_Pct_{i}' for i in range(len(scenario_results))]
                ]
            )
            
            return (
                scenarios_json,
                dcc.Graph(figure=summary_fig),
                dcc.Graph(figure=impact_fig),
                details_table
            )
        
        # Callback pour créer et exécuter un scénario personnalisé
        @self.app.callback(
            [Output("store-selected-scenario", "data", allow_duplicate=True),
             Output("stress-test-summary-chart", "children", allow_duplicate=True),
             Output("stress-test-impact-chart", "children", allow_duplicate=True),
             Output("stress-test-details-table", "children", allow_duplicate=True)],
            [Input("create-custom-scenario-button", "n_clicks")],
            [State("custom-scenario-name", "value"),
             State("custom-scenario-description", "value"),
             State("equity-shock", "value"),
             State("interest-rate-shock", "value"),
             State("credit-spread-shock", "value"),
             State("volatility-shock", "value"),
             State("store-portfolio-filtered", "data")],
            prevent_initial_call=True
        )
        def create_custom_scenario(n_clicks, name, description, equity_shock, 
                                   interest_rate_shock, credit_spread_shock, 
                                   volatility_shock, portfolio_json):
            if not n_clicks or not name or not portfolio_json:
                return {}, "", "", ""
            
            # Créer un scénario personnalisé (dans une application réelle, on utiliserait le générateur de scénarios)
            custom_scenario = {
                'name': name,
                'description': description or f"Scénario personnalisé: {name}",
                'shocks': {
                    'equity': float(equity_shock) if equity_shock else -0.15,
                    'interest_rate': float(interest_rate_shock) if interest_rate_shock else 0.01,
                    'credit_spread': float(credit_spread_shock) if credit_spread_shock else 0.005,
                    'volatility': float(volatility_shock) if volatility_shock else 0.10
                }
            }
            
            # Simuler l'impact du scénario sur le portefeuille
            # Pour cet exemple, nous utilisons un impact aléatoire
            impact_percentage = np.random.uniform(-0.2, -0.05)
            
            # Convertir les données JSON en DataFrame
            portfolio = pd.read_json(portfolio_json, orient='split')
            
            # Créer un résultat de scénario
            scenario_result = [{
                'name': custom_scenario['name'],
                'description': custom_scenario['description'],
                'impact_percentage': impact_percentage,
                'impact_value': portfolio['MarketValue'].sum() * impact_percentage
            }]
            
            # Stocker le résultat du scénario
            scenario_json = json.dumps(scenario_result)
            
            # Créer le graphique récapitulatif des impacts
            summary_data = pd.DataFrame(scenario_result)
            
            summary_fig = px.bar(
                summary_data,
                x='name',
                y='impact_percentage',
                title="Impact du Scénario Personnalisé sur le Portefeuille",
                text_auto='.2%',
                labels={
                    'name': 'Scénario',
                    'impact_percentage': 'Impact (%)'
                }
            )
            summary_fig.update_traces(marker_color='red')
            summary_fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
            
            # Simuler l'impact par classe d'actifs (comme dans le callback précédent)
            asset_classes = portfolio['AssetClass'].unique()
            impact_by_asset = pd.DataFrame({
                'AssetClass': asset_classes,
                'BeforeStress': [portfolio[portfolio['AssetClass'] == cls]['MarketValue'].sum() for cls in asset_classes]
            })
            
            # Simuler des impacts différents selon la classe d'actifs
            impacts = np.random.uniform(-0.3, -0.01, size=len(asset_classes))
            impact_by_asset['AfterStress'] = impact_by_asset['BeforeStress'] * (1 + impacts)
            impact_by_asset['Impact'] = impact_by_asset['AfterStress'] - impact_by_asset['BeforeStress']
            impact_by_asset['Impact_Pct'] = impact_by_asset['Impact'] / impact_by_asset['BeforeStress']
            
            # Créer le graphique d'impact par classe d'actifs
            impact_fig = go.Figure()
            
            # Ajouter les barres pour les valeurs avant stress
            impact_fig.add_trace(go.Bar(
                x=impact_by_asset['AssetClass'],
                y=impact_by_asset['BeforeStress'],
                name='Avant Stress',
                marker_color='blue'
            ))
            
            # Ajouter les barres pour le scénario personnalisé
            impact_fig.add_trace(go.Bar(
                x=impact_by_asset['AssetClass'],
                y=impact_by_asset['AfterStress'],
                name=f'Après {custom_scenario["name"]}',
                marker_color='red'
            ))
            
            impact_fig.update_layout(
                barmode='group',
                title="Impact par Classe d'Actifs",
                xaxis_title="Classe d'Actifs",
                yaxis_title="Valeur",
                margin=dict(l=20, r=20, t=40, b=20)
            )
            
            # Créer la table détaillée des résultats de stress-test
            details_table = dash.dash_table.DataTable(
                id='stress-details-datatable-custom',
                columns=[
                    {'name': 'Classe d\'Actifs', 'id': 'AssetClass'},
                    {'name': 'Valeur Initiale', 'id': 'BeforeStress', 'type': 'numeric', 'format': {'specifier': ',.2f'}},
                    {'name': f'Après {custom_scenario["name"]}', 'id': 'AfterStress', 'type': 'numeric', 'format': {'specifier': ',.2f'}},
                    {'name': 'Impact (%)', 'id': 'Impact_Pct', 'type': 'numeric', 'format': {'specifier': '.2%'}}
                ],
                data=impact_by_asset.to_dict('records'),
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left',
                    'padding': '8px'
                },
                style_header={
                    'backgroundColor': 'rgb(230, 230, 230)',
                    'fontWeight': 'bold'
                },
                style_data_conditional=[
                    {
                        'if': {
                            'filter_query': '{Impact_Pct} < 0',
                            'column_id': 'Impact_Pct'
                        },
                        'color': 'red'
                    }
                ]
            )
            
            return (
                scenario_json,
                dcc.Graph(figure=summary_fig),
                dcc.Graph(figure=impact_fig),
                details_table
            )
        
        # Callback pour l'onglet Performance
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
        def update_performance_analysis(n_clicks, timeframe, start_date, end_date, portfolio_json):
            if self.market_data is None:
                return {}, "", "", "", "", ""
            
            # Dans une application réelle, on filtrerait les données selon la période
            # Pour cet exemple, nous allons générer des données simulées
            
            # Définir la période d'analyse
            if timeframe == '1M':
                days = 30
            elif timeframe == '3M':
                days = 90
            elif timeframe == '6M':
                days = 180
            elif timeframe == 'YTD':
                days = (datetime.now() - datetime(datetime.now().year, 1, 1)).days
            elif timeframe == '1Y':
                days = 365
            elif timeframe == '3Y':
                days = 365 * 3
            else:  # 'ALL' ou période personnalisée
                if start_date and end_date:
                    days = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days
                else:
                    days = 365  # Par défaut, 1 an
            
            # Générer des dates
            dates = pd.date_range(end=datetime.now(), periods=days)
            
            # Simuler les rendements cumulés
            np.random.seed(42)  # Pour la reproductibilité
            daily_returns = np.random.normal(0.0005, 0.01, size=days)
            cumulative_returns = (1 + daily_returns).cumprod() - 1
            
            # Calculer le drawdown
            rolling_max = np.maximum.accumulate(np.insert(cumulative_returns, 0, 0))
            drawdown = (cumulative_returns + 1) / rolling_max - 1
            
            # Créer un DataFrame pour les performances
            performance_data = pd.DataFrame({
                'Date': dates,
                'CumulativeReturn': cumulative_returns,
                'Drawdown': drawdown
            })
            
            # Créer le graphique des rendements cumulés
            cumulative_fig = px.line(
                performance_data,
                x='Date',
                y='CumulativeReturn',
                title="Rendements Cumulés",
                labels={
                    'Date': 'Date',
                    'CumulativeReturn': 'Rendement Cumulé'
                }
            )
            cumulative_fig.update_traces(line=dict(color='blue'))
            cumulative_fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
            
            # Créer le graphique de drawdown
            drawdown_fig = px.area(
                performance_data,
                x='Date',
                y='Drawdown',
                title="Drawdown",
                labels={
                    'Date': 'Date',
                    'Drawdown': 'Drawdown'
                }
            )
            drawdown_fig.update_traces(line=dict(color='red'), fillcolor='rgba(255, 0, 0, 0.3)')
            drawdown_fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
            
            # Créer les statistiques de performance
            performance_stats = html.Div([
                html.H5("Statistiques de Performance"),
                html.Table([
                    html.Tr([html.Td("Rendement Cumulé"), html.Td(f"{cumulative_returns[-1]:.2%}")]),
                    html.Tr([html.Td("Rendement Annualisé"), html.Td(f"{((1 + cumulative_returns[-1]) ** (365/days) - 1):.2%}")]),
                    html.Tr([html.Td("Volatilité Annualisée"), html.Td(f"{np.std(daily_returns) * np.sqrt(252):.2%}")]),
                    html.Tr([html.Td("Ratio de Sharpe"), html.Td(f"{((np.mean(daily_returns) * 252) / (np.std(daily_returns) * np.sqrt(252))):.2f}")]),
                    html.Tr([html.Td("Drawdown Maximum"), html.Td(f"{np.min(drawdown):.2%}")]),
                    html.Tr([html.Td("VaR (95%, 1 jour)"), html.Td(f"{np.percentile(daily_returns, 5):.2%}")]),
                ], className="table table-striped table-sm")
            ])
            
            # Simuler la performance par classe d'actifs
            if portfolio_json:
                portfolio = pd.read_json(portfolio_json, orient='split')
                asset_classes = portfolio['AssetClass'].unique()
            else:
                asset_classes = ['Actions', 'Obligations', 'Cash', 'Immobilier']
                
            asset_performance = pd.DataFrame({
                'AssetClass': asset_classes,
                'Return': np.random.uniform(-0.15, 0.25, size=len(asset_classes))
            })
            
            # Créer le graphique de performance par classe d'actifs
            asset_perf_fig = px.bar(
                asset_performance,
                x='AssetClass',
                y='Return',
                title="Performance par Classe d'Actifs",
                text_auto='.2%',
                labels={
                    'AssetClass': 'Classe d\'Actifs',
                    'Return': 'Rendement'
                }
            )
            asset_perf_fig.update_traces(marker_color=['green' if r > 0 else 'red' for r in asset_performance['Return']])
            asset_perf_fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
            
            # Simuler les meilleurs et pires performers
            if portfolio_json:
                portfolio = pd.read_json(portfolio_json, orient='split')
                assets = portfolio['Security'].tolist()
            else:
                assets = [f"Asset {i+1}" for i in range(10)]
                
            performers = pd.DataFrame({
                'Asset': assets,
                'Return': np.random.uniform(-0.3, 0.4, size=len(assets))
            }).sort_values('Return')
            
            # Sélectionner les 3 meilleurs et les 3 pires
            top_performers = performers.tail(3)
            bottom_performers = performers.head(3)
            top_bottom = pd.concat([bottom_performers, top_performers])
            
            # Créer le graphique des meilleurs/pires performers
            performers_fig = px.bar(
                top_bottom,
                x='Asset',
                y='Return',
                title="Meilleurs et Pires Performers",
                text_auto='.2%',
                labels={
                    'Asset': 'Actif',
                    'Return': 'Rendement'
                }
            )
            performers_fig.update_traces(marker_color=['green' if r > 0 else 'red' for r in top_bottom['Return']])
            performers_fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
            
            # Stocker la période sélectionnée
            timeframe_json = json.dumps({
                'timeframe': timeframe,
                'start_date': start_date,
                'end_date': end_date,
                'days': days
            })
            
            return (
                timeframe_json,
                dcc.Graph(figure=cumulative_fig),
                dcc.Graph(figure=drawdown_fig),
                performance_stats,
                dcc.Graph(figure=asset_perf_fig),
                dcc.Graph(figure=performers_fig)
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
    # Configurer le logging
    logging.basicConfig(level=logging.INFO)
    
    # Créer un portefeuille d'exemple
    portfolio_data = {
        'Security': ['Apple Inc.', 'Microsoft Corp.', 'Amazon.com Inc.', 'Alphabet Inc.', 'Meta Platforms Inc.'],
        'Ticker': ['AAPL', 'MSFT', 'AMZN', 'GOOG', 'META'],
        'Quantity': [100, 50, 20, 15, 40],
        'AssetClass': ['Equity', 'Equity', 'Equity', 'Equity', 'Equity'],
        'Sector': ['Technology', 'Technology', 'Consumer Discretionary', 'Communication Services', 'Communication Services'],
        'Currency': ['USD', 'USD', 'USD', 'USD', 'USD'],
        'Price': [150.0, 250.0, 3000.0, 2500.0, 300.0],
        'MarketValue': [15000.0, 12500.0, 60000.0, 37500.0, 12000.0],
        'Weight': [0.11, 0.09, 0.44, 0.27, 0.09]
    }
    
    # Créer un DataFrame
    portfolio = pd.DataFrame(portfolio_data)
    
    # Créer le dashboard
    dashboard = RiskDashboard(
        title="Dashboard de Risque et Performance",
        portfolio_data=portfolio
    )
    
    # Lancer le serveur
    dashboard.run_server(debug=True)
