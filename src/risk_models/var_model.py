"""
Module pour le calcul de la Value at Risk (VaR) et autres métriques de risque.
"""

import pandas as pd
import numpy as np
import scipy.stats as stats
from typing import List, Dict, Optional, Union, Tuple
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class VaRModel:
    """
    Classe pour calculer la Value at Risk (VaR) et d'autres métriques de risque.
    """
    
    def __init__(self, returns_data: pd.DataFrame = None):
        """
        Initialiser le modèle VaR.
        
        Args:
            returns_data: DataFrame contenant les rendements historiques des actifs
        """
        self.returns_data = returns_data
        
    def set_returns_data(self, returns_data: pd.DataFrame):
        """
        Définir les données de rendements à utiliser pour le calcul de la VaR.
        
        Args:
            returns_data: DataFrame contenant les rendements historiques des actifs
        """
        self.returns_data = returns_data
        
    def calculate_historical_var(
        self, 
        portfolio_weights: np.ndarray, 
        confidence_level: float = 0.95, 
        time_horizon: int = 1
    ) -> Tuple[float, float]:
        """
        Calculer la VaR historique pour un portefeuille donné.
        
        Args:
            portfolio_weights: Poids des actifs dans le portefeuille
            confidence_level: Niveau de confiance (par défaut, 0.95 pour VaR 95%)
            time_horizon: Horizon temporel en jours (par défaut, 1 jour)
            
        Returns:
            Tuple contenant (VaR, CVaR) au niveau de confiance spécifié
        """
        if self.returns_data is None:
            raise ValueError("Returns data not set. Use set_returns_data() first.")
        
        # Calculer les rendements du portefeuille
        portfolio_returns = np.dot(self.returns_data, portfolio_weights)
        
        # Ajuster pour l'horizon temporel (en supposant des rendements i.i.d.)
        # Note: Cela suppose que les rendements sont exprimés dans la même unité que l'horizon temporel
        scaling_factor = np.sqrt(time_horizon)
        
        # Calculer le quantile pour la VaR
        var_percentile = 1 - confidence_level
        var = -np.percentile(portfolio_returns, var_percentile * 100) * scaling_factor
        
        # Calculer la CVaR (Expected Shortfall)
        cvar = -portfolio_returns[portfolio_returns <= -var / scaling_factor].mean() * scaling_factor
        
        return var, cvar
    
    def calculate_parametric_var(
        self, 
        portfolio_weights: np.ndarray, 
        confidence_level: float = 0.95, 
        time_horizon: int = 1
    ) -> Tuple[float, float]:
        """
        Calculer la VaR paramétrique (en supposant une distribution normale) pour un portefeuille donné.
        
        Args:
            portfolio_weights: Poids des actifs dans le portefeuille
            confidence_level: Niveau de confiance (par défaut, 0.95 pour VaR 95%)
            time_horizon: Horizon temporel en jours (par défaut, 1 jour)
            
        Returns:
            Tuple contenant (VaR, CVaR) au niveau de confiance spécifié
        """
        if self.returns_data is None:
            raise ValueError("Returns data not set. Use set_returns_data() first.")
        
        # Calculer les rendements du portefeuille
        portfolio_returns = np.dot(self.returns_data, portfolio_weights)
        
        # Calculer la moyenne et l'écart-type des rendements du portefeuille
        mean_return = portfolio_returns.mean()
        std_return = portfolio_returns.std()
        
        # Calculer le z-score correspondant au niveau de confiance
        z_score = stats.norm.ppf(confidence_level)
        
        # Calculer la VaR paramétrique
        var = -(mean_return + z_score * std_return) * np.sqrt(time_horizon)
        
        # Pour la distribution normale, la CVaR est:
        # E[X | X <= -VaR] = mean_return - std_return * phi(z_score) / (1 - confidence_level)
        # où phi est la fonction de densité de probabilité de la distribution normale
        pdf_z = stats.norm.pdf(z_score)
        cvar = -(mean_return - std_return * pdf_z / (1 - confidence_level)) * np.sqrt(time_horizon)
        
        return var, cvar
    
    def calculate_monte_carlo_var(
        self, 
        portfolio_weights: np.ndarray, 
        confidence_level: float = 0.95, 
        time_horizon: int = 1,
        num_simulations: int = 10000,
        method: str = 'normal'
    ) -> Tuple[float, float]:
        """
        Calculer la VaR par simulation Monte Carlo pour un portefeuille donné.
        
        Args:
            portfolio_weights: Poids des actifs dans le portefeuille
            confidence_level: Niveau de confiance (par défaut, 0.95 pour VaR 95%)
            time_horizon: Horizon temporel en jours (par défaut, 1 jour)
            num_simulations: Nombre de simulations à effectuer
            method: Méthode de simulation ('normal', 't-dist', 'copula')
            
        Returns:
            Tuple contenant (VaR, CVaR) au niveau de confiance spécifié
        """
        if self.returns_data is None:
            raise ValueError("Returns data not set. Use set_returns_data() first.")
        
        # Calculer la matrice de covariance des rendements
        cov_matrix = self.returns_data.cov()
        
        # Calculer la moyenne des rendements
        mean_returns = self.returns_data.mean()
        
        # Générer des simulations en fonction de la méthode spécifiée
        if method == 'normal':
            # Simulation avec distribution normale multivariée
            simulated_returns = np.random.multivariate_normal(
                mean=mean_returns,
                cov=cov_matrix,
                size=num_simulations
            )
        elif method == 't-dist':
            # Simulation avec distribution t multivariée (pour les queues plus épaisses)
            df = 5  # Degrés de liberté pour la distribution t
            simulated_returns = stats.multivariate_t.rvs(
                loc=mean_returns,
                shape=cov_matrix,
                df=df,
                size=num_simulations
            )
        elif method == 'copula':
            # Simulation avec copule (à implémenter selon les besoins)
            # Cela nécessiterait une implémentation plus complexe des copules
            raise NotImplementedError("Copula method not implemented yet")
        else:
            raise ValueError(f"Unknown simulation method: {method}")
        
        # Calculer les rendements simulés du portefeuille
        portfolio_simulated_returns = np.dot(simulated_returns, portfolio_weights)
        
        # Ajuster pour l'horizon temporel
        scaling_factor = np.sqrt(time_horizon)
        portfolio_simulated_returns *= scaling_factor
        
        # Calculer le quantile pour la VaR
        var_percentile = 1 - confidence_level
        var = -np.percentile(portfolio_simulated_returns, var_percentile * 100)
        
        # Calculer la CVaR (Expected Shortfall)
        cvar = -portfolio_simulated_returns[portfolio_simulated_returns <= -var].mean()
        
        return var, cvar
    
    def calculate_component_var(
        self, 
        portfolio_weights: np.ndarray, 
        confidence_level: float = 0.95, 
        time_horizon: int = 1
    ) -> pd.DataFrame:
        """
        Calculer la VaR par composante pour un portefeuille donné (méthode paramétrique).
        
        Args:
            portfolio_weights: Poids des actifs dans le portefeuille
            confidence_level: Niveau de confiance (par défaut, 0.95 pour VaR 95%)
            time_horizon: Horizon temporel en jours (par défaut, 1 jour)
            
        Returns:
            DataFrame contenant la contribution de chaque actif à la VaR totale
        """
        if self.returns_data is None:
            raise ValueError("Returns data not set. Use set_returns_data() first.")
        
        # Calculer la moyenne et la matrice de covariance des rendements
        mean_returns = self.returns_data.mean()
        cov_matrix = self.returns_data.cov()
        
        # Calculer la volatilité du portefeuille
        portfolio_variance = np.dot(portfolio_weights.T, np.dot(cov_matrix, portfolio_weights))
        portfolio_volatility = np.sqrt(portfolio_variance)
        
        # Calculer le z-score correspondant au niveau de confiance
        z_score = stats.norm.ppf(confidence_level)
        
        # Calculer la VaR paramétrique du portefeuille
        portfolio_mean = np.dot(mean_returns, portfolio_weights)
        portfolio_var = -(portfolio_mean + z_score * portfolio_volatility) * np.sqrt(time_horizon)
        
        # Calculer les contributions marginales à la VaR
        marginal_contribution = np.dot(cov_matrix, portfolio_weights) / portfolio_volatility * z_score
        
        # Calculer les contributions à la VaR
        component_var = portfolio_weights * marginal_contribution * np.sqrt(time_horizon)
        
        # Créer un DataFrame pour les résultats
        component_var_df = pd.DataFrame({
            'Weight': portfolio_weights,
            'MarginalContribution': marginal_contribution,
            'ComponentVaR': component_var,
            'PercentContribution': component_var / portfolio_var * 100
        }, index=self.returns_data.columns)
        
        return component_var_df
    
    def calculate_incremental_var(
        self, 
        portfolio_weights: np.ndarray, 
        confidence_level: float = 0.95, 
        time_horizon: int = 1,
        increment: float = 0.01
    ) -> pd.DataFrame:
        """
        Calculer la VaR incrémentale pour chaque actif du portefeuille.
        
        Args:
            portfolio_weights: Poids des actifs dans le portefeuille
            confidence_level: Niveau de confiance (par défaut, 0.95 pour VaR 95%)
            time_horizon: Horizon temporel en jours (par défaut, 1 jour)
            increment: Incrément de poids à utiliser (par défaut, 1%)
            
        Returns:
            DataFrame contenant la VaR incrémentale pour chaque actif
        """
        if self.returns_data is None:
            raise ValueError("Returns data not set. Use set_returns_data() first.")
        
        # Calculer la VaR du portefeuille original
        base_var, _ = self.calculate_parametric_var(
            portfolio_weights, 
            confidence_level, 
            time_horizon
        )
        
        # Initialiser les résultats
        incremental_var = []
        
        # Pour chaque actif, calculer la VaR avec un poids incrémenté
        for i in range(len(portfolio_weights)):
            # Créer un nouveau vecteur de poids avec l'incrément pour l'actif i
            new_weights = portfolio_weights.copy()
            
            # Incrémenter le poids de l'actif i
            new_weights[i] += increment
            
            # Normaliser les poids pour qu'ils somment à 1
            new_weights = new_weights / new_weights.sum()
            
            # Calculer la nouvelle VaR
            new_var, _ = self.calculate_parametric_var(
                new_weights, 
                confidence_level, 
                time_horizon
            )
            
            # Calculer la VaR incrémentale
            inc_var = (new_var - base_var) / increment
            incremental_var.append(inc_var)
        
        # Créer un DataFrame pour les résultats
        incremental_var_df = pd.DataFrame({
            'Weight': portfolio_weights,
            'IncrementalVaR': incremental_var
        }, index=self.returns_data.columns)
        
        return incremental_var_df


def prepare_returns_data(
    prices: pd.DataFrame, 
    date_column: str = 'Date',
    price_column: str = 'Close',
    ticker_column: str = 'Ticker',
    method: str = 'log',
    frequency: str = 'D'
) -> pd.DataFrame:
    """
    Préparer les données de rendements à partir des prix.
    
    Args:
        prices: DataFrame contenant les prix historiques
        date_column: Nom de la colonne de date
        price_column: Nom de la colonne de prix
        ticker_column: Nom de la colonne de ticker
        method: Méthode de calcul des rendements ('simple' ou 'log')
        frequency: Fréquence des rendements ('D' pour quotidien, 'W' pour hebdomadaire, 'M' pour mensuel)
        
    Returns:
        DataFrame contenant les rendements par actif en colonnes et dates en index
    """
    try:
        # Pivoter les données pour avoir un DataFrame avec les dates en index et les tickers en colonnes
        pivot_prices = prices.pivot(index=date_column, columns=ticker_column, values=price_column)
        
        # Réindexer le DataFrame pour assurer une fréquence régulière
        pivot_prices = pivot_prices.sort_index()
        
        # Calculer les rendements selon la méthode spécifiée
        if method == 'simple':
            returns = pivot_prices.pct_change().dropna()
        elif method == 'log':
            returns = np.log(pivot_prices / pivot_prices.shift(1)).dropna()
        else:
            raise ValueError(f"Unknown return calculation method: {method}")
        
        # Rééchantillonner à la fréquence demandée si nécessaire
        if frequency != 'D':
            if frequency == 'W':
                returns = returns.resample('W').apply(lambda x: (1 + x).prod() - 1)
            elif frequency == 'M':
                returns = returns.resample('M').apply(lambda x: (1 + x).prod() - 1)
            else:
                raise ValueError(f"Unknown frequency: {frequency}")
        
        return returns
        
    except Exception as e:
        logger.error(f"Error preparing returns data: {e}")
        return pd.DataFrame()


# Exemple d'utilisation
if __name__ == "__main__":
    # Configurer le logging
    logging.basicConfig(level=logging.INFO)
    
    # Exemple de données de rendements (normalement calculées à partir des prix)
    np.random.seed(42)
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
    returns_df = pd.DataFrame(returns, columns=asset_names)
    
    # Créer un portefeuille équipondéré
    portfolio_weights = np.ones(num_assets) / num_assets
    
    # Initialiser le modèle VaR
    var_model = VaRModel(returns_df)
    
    # Calculer les différentes VaR
    hist_var, hist_cvar = var_model.calculate_historical_var(portfolio_weights)
    print(f"Historical VaR (95%, 1-day): {hist_var:.6f}")
    print(f"Historical CVaR (95%, 1-day): {hist_cvar:.6f}")
    
    param_var, param_cvar = var_model.calculate_parametric_var(portfolio_weights)
    print(f"Parametric VaR (95%, 1-day): {param_var:.6f}")
    print(f"Parametric CVaR (95%, 1-day): {param_cvar:.6f}")
    
    mc_var, mc_cvar = var_model.calculate_monte_carlo_var(portfolio_weights, num_simulations=5000)
    print(f"Monte Carlo VaR (95%, 1-day): {mc_var:.6f}")
    print(f"Monte Carlo CVaR (95%, 1-day): {mc_cvar:.6f}")
    
    # Calculer les contributions à la VaR
    component_var = var_model.calculate_component_var(portfolio_weights)
    print("\nComponent VaR:")
    print(component_var)
