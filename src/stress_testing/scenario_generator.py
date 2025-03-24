"""
Module pour la génération de scénarios de stress-testing.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Union, Tuple, Any
import logging
from datetime import datetime
import json
import os

logger = logging.getLogger(__name__)


class ScenarioGenerator:
    """
    Classe pour générer des scénarios de stress-testing.
    """
    
    # Dictionnaire des scénarios prédéfinis
    PREDEFINED_SCENARIOS = {
        'financial_crisis_2008': {
            'description': 'Simulation de la crise financière de 2008',
            'shocks': {
                'equity': -0.40,  # Choc des marchés actions de -40%
                'credit_spread': 0.02,  # Augmentation des spreads de crédit de 200 points de base
                'interest_rate': -0.01,  # Baisse des taux d'intérêt de 100 points de base
                'volatility': 0.20,  # Augmentation de la volatilité de 20 points
                'real_estate': -0.30,  # Choc immobilier de -30%
                'fx': {
                    'USD': 0.0,   # Dollar américain comme référence
                    'EUR': -0.15, # Baisse de l'euro de 15%
                    'GBP': -0.20, # Baisse de la livre sterling de 20%
                    'JPY': 0.10,  # Hausse du yen de 10%
                }
            }
        },
        'rate_shock': {
            'description': 'Choc de taux d\'intérêt',
            'shocks': {
                'interest_rate': 0.02,  # Hausse des taux d'intérêt de 200 points de base
                'equity': -0.15,  # Choc des marchés actions de -15%
                'credit_spread': 0.01,  # Augmentation des spreads de crédit de 100 points de base
                'volatility': 0.10,  # Augmentation de la volatilité de 10 points
                'fx': {
                    'USD': 0.0,
                    'EUR': -0.05,
                    'GBP': -0.08,
                    'JPY': 0.03,
                }
            }
        },
        'inflation_shock': {
            'description': 'Choc d\'inflation',
            'shocks': {
                'interest_rate': 0.03,  # Hausse des taux d'intérêt de 300 points de base
                'equity': -0.10,  # Choc des marchés actions de -10%
                'inflation': 0.05,  # Hausse de l'inflation de 5 points
                'credit_spread': 0.005,  # Augmentation des spreads de crédit de 50 points de base
                'commodity': 0.25,  # Hausse des matières premières de 25%
                'fx': {
                    'USD': 0.0,
                    'EUR': -0.07,
                    'GBP': -0.05,
                    'JPY': -0.03,
                }
            }
        },
        'liquidity_crisis': {
            'description': 'Crise de liquidité',
            'shocks': {
                'liquidity_premium': 0.03,  # Augmentation de la prime de liquidité de 300 points de base
                'credit_spread': 0.015,  # Augmentation des spreads de crédit de 150 points de base
                'equity': -0.20,  # Choc des marchés actions de -20%
                'bond_liquidity': -0.30,  # Réduction de la liquidité des obligations de 30%
                'volatility': 0.15,  # Augmentation de la volatilité de 15 points
                'fx': {
                    'USD': 0.0,
                    'EUR': -0.10,
                    'GBP': -0.12,
                    'JPY': 0.05,
                }
            }
        },
        'geopolitical_crisis': {
            'description': 'Crise géopolitique',
            'shocks': {
                'equity': -0.25,  # Choc des marchés actions de -25%
                'energy': 0.40,  # Hausse des prix de l'énergie de 40%
                'volatility': 0.25,  # Augmentation de la volatilité de 25 points
                'credit_spread': 0.01,  # Augmentation des spreads de crédit de 100 points de base
                'interest_rate': 0.005,  # Hausse des taux d'intérêt de 50 points de base
                'fx': {
                    'USD': 0.0,
                    'EUR': -0.08,
                    'GBP': -0.05,
                    'JPY': 0.08,
                }
            }
        }
    }
    
    def __init__(self, scenarios_dir: str = "data/scenarios"):
        """
        Initialiser le générateur de scénarios.
        
        Args:
            scenarios_dir: Répertoire pour stocker les scénarios
        """
        self.scenarios_dir = scenarios_dir
        os.makedirs(scenarios_dir, exist_ok=True)
        
    def create_custom_scenario(
        self, 
        name: str, 
        description: str, 
        shocks: Dict[str, Any],
        save: bool = True
    ) -> Dict[str, Any]:
        """
        Créer un scénario de stress-test personnalisé.
        
        Args:
            name: Nom du scénario
            description: Description du scénario
            shocks: Dictionnaire des chocs à appliquer
            save: Sauvegarder le scénario dans un fichier
            
        Returns:
            Dictionnaire contenant le scénario
        """
        scenario = {
            'name': name,
            'description': description,
            'shocks': shocks,
            'created_at': datetime.now().isoformat()
        }
        
        if save:
            self._save_scenario(scenario)
            
        return scenario
    
    def get_predefined_scenario(
        self, 
        scenario_name: str,
        severity_multiplier: float = 1.0
    ) -> Dict[str, Any]:
        """
        Récupérer un scénario prédéfini avec une sévérité ajustable.
        
        Args:
            scenario_name: Nom du scénario prédéfini
            severity_multiplier: Multiplicateur de sévérité (1.0 = sévérité normale)
            
        Returns:
            Dictionnaire contenant le scénario
        """
        if scenario_name not in self.PREDEFINED_SCENARIOS:
            raise ValueError(f"Unknown predefined scenario: {scenario_name}")
        
        # Récupérer le scénario de base
        base_scenario = self.PREDEFINED_SCENARIOS[scenario_name].copy()
        
        # Ajuster la sévérité des chocs si nécessaire
        if severity_multiplier != 1.0:
            base_shocks = base_scenario['shocks']
            adjusted_shocks = {}
            
            for key, value in base_shocks.items():
                if isinstance(value, dict):  # Pour les dictionnaires imbriqués (ex: FX)
                    adjusted_shocks[key] = {k: v * severity_multiplier for k, v in value.items()}
                else:
                    adjusted_shocks[key] = value * severity_multiplier
            
            base_scenario['shocks'] = adjusted_shocks
            base_scenario['description'] += f" (sévérité: {severity_multiplier:.2f}x)"
        
        # Ajouter les métadonnées
        scenario = {
            'name': scenario_name,
            'description': base_scenario['description'],
            'shocks': base_scenario['shocks'],
            'severity': severity_multiplier,
            'created_at': datetime.now().isoformat(),
            'predefined': True
        }
        
        return scenario
    
    def create_historical_scenario(
        self, 
        name: str, 
        description: str, 
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        market_data: pd.DataFrame,
        save: bool = True
    ) -> Dict[str, Any]:
        """
        Créer un scénario basé sur une période historique.
        
        Args:
            name: Nom du scénario
            description: Description du scénario
            start_date: Date de début de la période historique
            end_date: Date de fin de la période historique
            market_data: DataFrame contenant les données de marché
            save: Sauvegarder le scénario dans un fichier
            
        Returns:
            Dictionnaire contenant le scénario
        """
        # Convertir les dates en chaînes si elles sont des objets datetime
        start_str = start_date.strftime('%Y-%m-%d') if isinstance(start_date, datetime) else start_date
        end_str = end_date.strftime('%Y-%m-%d') if isinstance(end_date, datetime) else end_date
        
        # Filtrer les données pour la période spécifiée
        if 'Date' in market_data.columns:
            market_data = market_data.set_index('Date')
        
        filtered_data = market_data.loc[start_str:end_str]
        
        # Calculer les variations relatives pour chaque série
        start_values = filtered_data.iloc[0]
        end_values = filtered_data.iloc[-1]
        relative_changes = (end_values - start_values) / start_values
        
        # Convertir en dictionnaire
        shocks = relative_changes.to_dict()
        
        # Créer le scénario
        scenario = {
            'name': name,
            'description': description,
            'historical_period': {
                'start_date': start_str,
                'end_date': end_str
            },
            'shocks': shocks,
            'created_at': datetime.now().isoformat()
        }
        
        if save:
            self._save_scenario(scenario)
            
        return scenario
    
    def generate_monte_carlo_scenarios(
        self, 
        base_name: str,
        description: str,
        returns_data: pd.DataFrame,
        num_scenarios: int = 100,
        confidence_level: float = 0.95,
        save: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Générer des scénarios par simulation Monte Carlo.
        
        Args:
            base_name: Nom de base pour les scénarios
            description: Description des scénarios
            returns_data: DataFrame contenant les rendements historiques
            num_scenarios: Nombre de scénarios à générer
            confidence_level: Niveau de confiance pour les scénarios extrêmes
            save: Sauvegarder les scénarios dans des fichiers
            
        Returns:
            Liste de dictionnaires contenant les scénarios
        """
        # Calculer la moyenne et la matrice de covariance des rendements
        mean_returns = returns_data.mean()
        cov_matrix = returns_data.cov()
        
        # Générer des simulations avec distribution normale multivariée
        simulated_returns = np.random.multivariate_normal(
            mean=mean_returns,
            cov=cov_matrix,
            size=num_scenarios
        )
        
        # Convertir en DataFrame
        simulated_returns_df = pd.DataFrame(
            simulated_returns,
            columns=returns_data.columns
        )
        
        # Créer les scénarios
        scenarios = []
        
        for i in range(num_scenarios):
            scenario_name = f"{base_name}_{i+1}"
            shocks = simulated_returns_df.iloc[i].to_dict()
            
            scenario = {
                'name': scenario_name,
                'description': f"{description} (scénario {i+1}/{num_scenarios})",
                'shocks': shocks,
                'created_at': datetime.now().isoformat(),
                'monte_carlo': True,
                'scenario_number': i+1,
                'total_scenarios': num_scenarios
            }
            
            scenarios.append(scenario)
            
            if save:
                self._save_scenario(scenario)
        
        return scenarios
    
    def create_sensitivity_scenario(
        self, 
        name: str, 
        description: str, 
        factor: str, 
        base_value: float,
        shock_values: List[float],
        save: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Créer des scénarios pour l'analyse de sensibilité.
        
        Args:
            name: Nom de base pour les scénarios
            description: Description des scénarios
            factor: Facteur à analyser
            base_value: Valeur de base du facteur
            shock_values: Liste des valeurs de choc à appliquer
            save: Sauvegarder les scénarios dans des fichiers
            
        Returns:
            Liste de dictionnaires contenant les scénarios
        """
        scenarios = []
        
        for i, shock in enumerate(shock_values):
            scenario_name = f"{name}_{factor}_{shock}"
            
            # Calculer le choc relatif
            relative_shock = (shock - base_value) / base_value if base_value != 0 else shock
            
            shocks = {factor: relative_shock}
            
            scenario = {
                'name': scenario_name,
                'description': f"{description} ({factor} = {shock})",
                'sensitivity_analysis': {
                    'factor': factor,
                    'base_value': base_value,
                    'shock_value': shock,
                    'relative_shock': relative_shock
                },
                'shocks': shocks,
                'created_at': datetime.now().isoformat()
            }
            
            scenarios.append(scenario)
            
            if save:
                self._save_scenario(scenario)
        
        return scenarios
    
    def combine_scenarios(
        self, 
        name: str, 
        description: str, 
        scenarios: List[Dict[str, Any]],
        weights: Optional[List[float]] = None,
        save: bool = True
    ) -> Dict[str, Any]:
        """
        Combiner plusieurs scénarios en un seul.
        
        Args:
            name: Nom du scénario combiné
            description: Description du scénario combiné
            scenarios: Liste des scénarios à combiner
            weights: Poids à appliquer à chaque scénario (si None, équipondération)
            save: Sauvegarder le scénario dans un fichier
            
        Returns:
            Dictionnaire contenant le scénario combiné
        """
        if weights is None:
            weights = [1.0 / len(scenarios)] * len(scenarios)
        
        if len(weights) != len(scenarios):
            raise ValueError("The number of weights must match the number of scenarios")
        
        # Normaliser les poids
        weights = np.array(weights) / sum(weights)
        
        # Initialiser les chocs combinés
        combined_shocks = {}
        
        # Pour chaque scénario
        for i, scenario in enumerate(scenarios):
            shocks = scenario['shocks']
            
            for key, value in shocks.items():
                if isinstance(value, dict):  # Pour les dictionnaires imbriqués (ex: FX)
                    if key not in combined_shocks:
                        combined_shocks[key] = {}
                    
                    for sub_key, sub_value in value.items():
                        if sub_key in combined_shocks[key]:
                            combined_shocks[key][sub_key] += sub_value * weights[i]
                        else:
                            combined_shocks[key][sub_key] = sub_value * weights[i]
                else:
                    if key in combined_shocks:
                        combined_shocks[key] += value * weights[i]
                    else:
                        combined_shocks[key] = value * weights[i]
        
        # Créer le scénario combiné
        combined_scenario = {
            'name': name,
            'description': description,
            'shocks': combined_shocks,
            'combined_from': [scenario['name'] for scenario in scenarios],
            'weights': weights.tolist(),
            'created_at': datetime.now().isoformat()
        }
        
        if save:
            self._save_scenario(combined_scenario)
            
        return combined_scenario
    
    def load_scenario(self, scenario_name: str) -> Dict[str, Any]:
        """
        Charger un scénario depuis un fichier.
        
        Args:
            scenario_name: Nom du scénario à charger
            
        Returns:
            Dictionnaire contenant le scénario
        """
        file_path = os.path.join(self.scenarios_dir, f"{scenario_name}.json")
        
        try:
            with open(file_path, 'r') as f:
                scenario = json.load(f)
            
            return scenario
            
        except Exception as e:
            logger.error(f"Error loading scenario {scenario_name}: {e}")
            raise
    
    def list_scenarios(self) -> List[str]:
        """
        Lister tous les scénarios sauvegardés.
        
        Returns:
            Liste des noms de scénarios
        """
        try:
            scenarios = [f.split('.')[0] for f in os.listdir(self.scenarios_dir) 
                         if f.endswith('.json')]
            return scenarios
            
        except Exception as e:
            logger.error(f"Error listing scenarios: {e}")
            return []
    
    def _save_scenario(self, scenario: Dict[str, Any]) -> str:
        """
        Sauvegarder un scénario dans un fichier.
        
        Args:
            scenario: Dictionnaire contenant le scénario
            
        Returns:
            Chemin vers le fichier sauvegardé
        """
        file_path = os.path.join(self.scenarios_dir, f"{scenario['name']}.json")
        
        try:
            with open(file_path, 'w') as f:
                json.dump(scenario, f, indent=4)
            
            logger.info(f"Scenario saved to {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving scenario: {e}")
            return ""


# Fonction utilitaire pour appliquer un scénario à un portefeuille
def apply_scenario_to_portfolio(
    portfolio: pd.DataFrame,
    scenario: Dict[str, Any],
    asset_class_mapping: Optional[Dict[str, List[str]]] = None
) -> pd.DataFrame:
    """
    Appliquer un scénario de stress-test à un portefeuille.
    
    Args:
        portfolio: DataFrame contenant les données du portefeuille
        scenario: Dictionnaire contenant le scénario à appliquer
        asset_class_mapping: Dictionnaire mappant les types d'actifs aux facteurs de risque
        
    Returns:
        DataFrame contenant le portefeuille avec les valeurs stressées
    """
    # Copier le portefeuille pour ne pas modifier l'original
    stressed_portfolio = portfolio.copy()
    
    # Si aucun mapping n'est fourni, utiliser un mapping par défaut
    if asset_class_mapping is None:
        asset_class_mapping = {
            'equity': ['Equity', 'Stock'],
            'bond': ['Bond', 'Fixed Income'],
            'credit': ['Corporate Bond', 'Credit'],
            'sovereign': ['Government Bond', 'Sovereign'],
            'real_estate': ['Real Estate', 'REIT'],
            'commodity': ['Commodity', 'Commodities'],
            'cash': ['Cash', 'Money Market']
        }
    
    # Récupérer les chocs du scénario
    shocks = scenario['shocks']
    
    # Appliquer les chocs en fonction de la classe d'actifs
    for factor, shock in shocks.items():
        if factor == 'fx':  # Traitement spécial pour les chocs de change
            if 'Currency' in stressed_portfolio.columns:
                for currency, fx_shock in shock.items():
                    # Appliquer le choc FX aux lignes avec la devise correspondante
                    mask = stressed_portfolio['Currency'] == currency
                    if 'Price' in stressed_portfolio.columns:
                        stressed_portfolio.loc[mask, 'Price'] *= (1 + fx_shock)
                    if 'MarketValue' in stressed_portfolio.columns:
                        stressed_portfolio.loc[mask, 'MarketValue'] *= (1 + fx_shock)
        else:
            # Pour les autres facteurs, chercher les classes d'actifs correspondantes
            if factor in asset_class_mapping:
                asset_classes = asset_class_mapping[factor]
                if 'AssetClass' in stressed_portfolio.columns:
                    mask = stressed_portfolio['AssetClass'].isin(asset_classes)
                    if 'Price' in stressed_portfolio.columns:
                        stressed_portfolio.loc[mask, 'Price'] *= (1 + shock)
                    if 'MarketValue' in stressed_portfolio.columns:
                        stressed_portfolio.loc[mask, 'MarketValue'] *= (1 + shock)
    
    # Recalculer les poids si nécessaire
    if 'MarketValue' in stressed_portfolio.columns:
        total_value = stressed_portfolio['MarketValue'].sum()
        if 'Weight' in stressed_portfolio.columns:
            stressed_portfolio['Weight'] = stressed_portfolio['MarketValue'] / total_value
    
    # Ajouter des métadonnées sur le scénario
    stressed_portfolio.attrs['scenario_name'] = scenario['name']
    stressed_portfolio.attrs['scenario_description'] = scenario['description']
    stressed_portfolio.attrs['scenario_applied_at'] = datetime.now().isoformat()
    
    return stressed_portfolio


# Exemple d'utilisation
if __name__ == "__main__":
    # Configurer le logging
    logging.basicConfig(level=logging.INFO)
    
    # Créer une instance du générateur de scénarios
    generator = ScenarioGenerator()
    
    # Récupérer un scénario prédéfini
    scenario = generator.get_predefined_scenario('financial_crisis_2008', severity_multiplier=0.8)
    print(f"Scénario: {scenario['name']}")
    print(f"Description: {scenario['description']}")
    print("Chocs:")
    for key, value in scenario['shocks'].items():
        print(f"  {key}: {value}")
    
    # Créer un scénario personnalisé
    custom_scenario = generator.create_custom_scenario(
        name="custom_scenario_1",
        description="Scénario personnalisé pour test",
        shocks={
            'equity': -0.15,
            'interest_rate': 0.01,
            'credit_spread': 0.005,
            'fx': {
                'USD': 0.0,
                'EUR': -0.05
            }
        },
        save=True
    )
    print(f"\nScénario personnalisé créé: {custom_scenario['name']}")
    
    # Exemple de portfolio
    portfolio_data = {
        'Security': ['Apple Inc.', 'US Treasury 10Y', 'EUR Cash', 'Gold ETF'],
        'Ticker': ['AAPL', 'UST10Y', 'EUR', 'GLD'],
        'Quantity': [100, 10, 5000, 20],
        'AssetClass': ['Equity', 'Sovereign', 'Cash', 'Commodity'],
        'Currency': ['USD', 'USD', 'EUR', 'USD'],
        'Price': [150.0, 98.5, 1.0, 180.0],
        'MarketValue': [15000.0, 985.0, 5000.0, 3600.0]
    }
    
    portfolio = pd.DataFrame(portfolio_data)
    
    # Appliquer le scénario au portefeuille
    stressed_portfolio = apply_scenario_to_portfolio(portfolio, scenario)
    
    print("\nPortefeuille original:")
    print(portfolio[['Security', 'AssetClass', 'Currency', 'Price', 'MarketValue']])
    
    print("\nPortefeuille stressé:")
    print(stressed_portfolio[['Security', 'AssetClass', 'Currency', 'Price', 'MarketValue']])
