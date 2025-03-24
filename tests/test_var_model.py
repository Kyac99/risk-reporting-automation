"""
Tests unitaires pour le module de calcul de VaR.
"""

import unittest
import os
import sys
import pandas as pd
import numpy as np

# Ajouter le répertoire parent au chemin de recherche des modules
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)

# Importer les modules à tester
from src.risk_models.var_model import VaRModel, prepare_returns_data


class TestVaRModel(unittest.TestCase):
    """
    Tests pour la classe VaRModel.
    """
    
    def setUp(self):
        """
        Préparer les données pour les tests.
        """
        # Générer des données de rendements simulées
        np.random.seed(42)  # Pour la reproductibilité
        num_assets = 5
        num_periods = 1000
        
        # Simuler des rendements corrélés
        mean_returns = np.random.normal(0.0005, 0.0002, num_assets)
        cov_matrix = np.random.random((num_assets, num_assets))
        # Rendre la matrice de covariance symétrique et semi-définie positive
        cov_matrix = cov_matrix @ cov_matrix.T
        # Réduire l'échelle pour des rendements réalistes
        cov_matrix = cov_matrix * 0.0001
        
        # Générer des rendements
        returns = np.random.multivariate_normal(mean_returns, cov_matrix, num_periods)
        
        # Créer un DataFrame de rendements
        asset_names = ['Asset_' + str(i+1) for i in range(num_assets)]
        self.returns_df = pd.DataFrame(returns, columns=asset_names)
        
        # Créer un portefeuille équipondéré
        self.portfolio_weights = np.ones(num_assets) / num_assets
        
        # Initialiser le modèle VaR
        self.var_model = VaRModel(self.returns_df)
    
    def test_historical_var(self):
        """
        Tester le calcul de la VaR historique.
        """
        # Calculer la VaR historique
        var, cvar = self.var_model.calculate_historical_var(
            self.portfolio_weights, 
            confidence_level=0.95, 
            time_horizon=1
        )
        
        # Vérifier que les valeurs sont positives (car la VaR est négative par convention)
        self.assertGreater(var, 0)
        self.assertGreater(cvar, 0)
        
        # Vérifier que la CVaR est supérieure à la VaR
        self.assertGreater(cvar, var)
    
    def test_parametric_var(self):
        """
        Tester le calcul de la VaR paramétrique.
        """
        # Calculer la VaR paramétrique
        var, cvar = self.var_model.calculate_parametric_var(
            self.portfolio_weights, 
            confidence_level=0.95, 
            time_horizon=1
        )
        
        # Vérifier que les valeurs sont positives
        self.assertGreater(var, 0)
        self.assertGreater(cvar, 0)
        
        # Vérifier que la CVaR est supérieure à la VaR
        self.assertGreater(cvar, var)
    
    def test_monte_carlo_var(self):
        """
        Tester le calcul de la VaR par simulation Monte Carlo.
        """
        # Calculer la VaR par simulation Monte Carlo
        var, cvar = self.var_model.calculate_monte_carlo_var(
            self.portfolio_weights, 
            confidence_level=0.95, 
            time_horizon=1,
            num_simulations=1000
        )
        
        # Vérifier que les valeurs sont positives
        self.assertGreater(var, 0)
        self.assertGreater(cvar, 0)
        
        # Vérifier que la CVaR est supérieure à la VaR
        self.assertGreater(cvar, var)
    
    def test_component_var(self):
        """
        Tester le calcul des contributions à la VaR.
        """
        # Calculer les contributions à la VaR
        component_var = self.var_model.calculate_component_var(
            self.portfolio_weights, 
            confidence_level=0.95, 
            time_horizon=1
        )
        
        # Vérifier que le DataFrame a la bonne forme
        self.assertEqual(len(component_var), len(self.portfolio_weights))
        self.assertIn('ComponentVaR', component_var.columns)
        
        # Vérifier que la somme des contributions est proche de la VaR totale
        var, _ = self.var_model.calculate_parametric_var(
            self.portfolio_weights, 
            confidence_level=0.95, 
            time_horizon=1
        )
        
        total_component_var = component_var['ComponentVaR'].sum()
        self.assertAlmostEqual(total_component_var, var, delta=var*0.01)  # Tolérance de 1%
    
    def test_incremental_var(self):
        """
        Tester le calcul de la VaR incrémentale.
        """
        # Calculer la VaR incrémentale
        incremental_var = self.var_model.calculate_incremental_var(
            self.portfolio_weights, 
            confidence_level=0.95, 
            time_horizon=1
        )
        
        # Vérifier que le DataFrame a la bonne forme
        self.assertEqual(len(incremental_var), len(self.portfolio_weights))
        self.assertIn('IncrementalVaR', incremental_var.columns)
    
    def test_prepare_returns_data(self):
        """
        Tester la fonction de préparation des données de rendements.
        """
        # Créer des données de prix
        dates = pd.date_range(start='2023-01-01', periods=100, freq='B')
        tickers = ['AAPL', 'MSFT', 'GOOG']
        
        # Créer un DataFrame de prix
        data = []
        for ticker in tickers:
            np.random.seed(hash(ticker) % 2**32)  # Différente seed pour chaque ticker
            start_price = 100
            prices = start_price * np.cumprod(1 + np.random.normal(0.0005, 0.01, len(dates)))
            
            for i, date in enumerate(dates):
                data.append({
                    'Date': date,
                    'Ticker': ticker,
                    'Close': prices[i]
                })
        
        prices_df = pd.DataFrame(data)
        
        # Préparer les données de rendements
        returns_df = prepare_returns_data(
            prices_df, 
            date_column='Date', 
            price_column='Close', 
            ticker_column='Ticker', 
            method='log'
        )
        
        # Vérifier que le DataFrame a la bonne forme
        self.assertEqual(len(returns_df), len(dates) - 1)  # Une ligne de moins car on calcule les rendements
        self.assertEqual(len(returns_df.columns), len(tickers))
        
        # Vérifier que les rendements sont dans des plages raisonnables
        for ticker in tickers:
            self.assertTrue((returns_df[ticker].abs() < 0.1).all())


if __name__ == '__main__':
    unittest.main()
