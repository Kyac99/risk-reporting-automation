"""
Module pour la collecte et le chargement des données de portefeuille.
"""

import pandas as pd
import numpy as np
import os
import logging
from typing import List, Dict, Optional, Union, Tuple
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class PortfolioLoader:
    """
    Classe pour charger et préparer les données de portefeuille.
    """
    
    def __init__(self, data_dir: str = "data/portfolios"):
        """
        Initialiser le chargeur de portefeuille.
        
        Args:
            data_dir: Répertoire contenant les données de portefeuille
        """
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
    def load_portfolio_from_excel(
        self, 
        file_path: str, 
        sheet_name: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Charger un portefeuille à partir d'un fichier Excel.
        
        Args:
            file_path: Chemin vers le fichier Excel
            sheet_name: Nom de la feuille à charger (si None, la première feuille est utilisée)
            
        Returns:
            DataFrame contenant les données du portefeuille
        """
        try:
            portfolio = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # Vérifier les colonnes minimales nécessaires
            required_cols = ['Security', 'Ticker', 'Quantity', 'AssetClass']
            missing_cols = [col for col in required_cols if col not in portfolio.columns]
            
            if missing_cols:
                logger.warning(f"Missing required columns in portfolio data: {missing_cols}")
            
            # Normaliser les noms de colonnes
            portfolio.columns = portfolio.columns.str.strip()
            
            return portfolio
            
        except Exception as e:
            logger.error(f"Error loading portfolio from Excel: {e}")
            return pd.DataFrame()
    
    def load_portfolio_from_csv(
        self, 
        file_path: str, 
        delimiter: str = ','
    ) -> pd.DataFrame:
        """
        Charger un portefeuille à partir d'un fichier CSV.
        
        Args:
            file_path: Chemin vers le fichier CSV
            delimiter: Délimiteur utilisé dans le fichier CSV
            
        Returns:
            DataFrame contenant les données du portefeuille
        """
        try:
            portfolio = pd.read_csv(file_path, delimiter=delimiter)
            
            # Vérifier les colonnes minimales nécessaires
            required_cols = ['Security', 'Ticker', 'Quantity', 'AssetClass']
            missing_cols = [col for col in required_cols if col not in portfolio.columns]
            
            if missing_cols:
                logger.warning(f"Missing required columns in portfolio data: {missing_cols}")
            
            # Normaliser les noms de colonnes
            portfolio.columns = portfolio.columns.str.strip()
            
            return portfolio
            
        except Exception as e:
            logger.error(f"Error loading portfolio from CSV: {e}")
            return pd.DataFrame()
    
    def load_portfolio_from_json(
        self, 
        file_path: str
    ) -> pd.DataFrame:
        """
        Charger un portefeuille à partir d'un fichier JSON.
        
        Args:
            file_path: Chemin vers le fichier JSON
            
        Returns:
            DataFrame contenant les données du portefeuille
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Convertir en DataFrame
            portfolio = pd.DataFrame(data)
            
            # Vérifier les colonnes minimales nécessaires
            required_cols = ['Security', 'Ticker', 'Quantity', 'AssetClass']
            missing_cols = [col for col in required_cols if col not in portfolio.columns]
            
            if missing_cols:
                logger.warning(f"Missing required columns in portfolio data: {missing_cols}")
            
            return portfolio
            
        except Exception as e:
            logger.error(f"Error loading portfolio from JSON: {e}")
            return pd.DataFrame()
    
    def enrich_portfolio_with_market_data(
        self, 
        portfolio: pd.DataFrame, 
        market_data: pd.DataFrame,
        date_column: str = 'Date',
        price_column: str = 'Close',
        ticker_column: str = 'Ticker',
        as_of_date: Optional[Union[str, datetime]] = None
    ) -> pd.DataFrame:
        """
        Enrichir le portefeuille avec des données de marché (prix, etc.).
        
        Args:
            portfolio: DataFrame du portefeuille
            market_data: DataFrame des données de marché
            date_column: Nom de la colonne de date dans les données de marché
            price_column: Nom de la colonne de prix dans les données de marché
            ticker_column: Nom de la colonne de ticker dans les données de marché
            as_of_date: Date à utiliser pour les prix (si None, utilise la dernière date disponible)
            
        Returns:
            DataFrame du portefeuille enrichi avec les données de marché
        """
        try:
            # Copier le portefeuille pour ne pas modifier l'original
            enriched_portfolio = portfolio.copy()
            
            # Si as_of_date est fourni, le convertir en datetime si c'est une chaîne
            if as_of_date is not None and isinstance(as_of_date, str):
                as_of_date = pd.to_datetime(as_of_date)
            
            # Filtrer les données de marché pour la date spécifiée ou la dernière date
            if as_of_date is not None:
                market_data_filtered = market_data[market_data[date_column] == as_of_date]
            else:
                # Trouver la dernière date disponible
                last_date = market_data[date_column].max()
                market_data_filtered = market_data[market_data[date_column] == last_date]
            
            # Créer un dictionnaire de prix indexé par ticker
            price_dict = dict(zip(
                market_data_filtered[ticker_column],
                market_data_filtered[price_column]
            ))
            
            # Ajouter les prix au portefeuille
            enriched_portfolio['Price'] = enriched_portfolio['Ticker'].map(price_dict)
            
            # Calculer la valeur de marché
            enriched_portfolio['MarketValue'] = enriched_portfolio['Quantity'] * enriched_portfolio['Price']
            
            # Calculer le poids dans le portefeuille
            total_value = enriched_portfolio['MarketValue'].sum()
            enriched_portfolio['Weight'] = enriched_portfolio['MarketValue'] / total_value
            
            return enriched_portfolio
            
        except Exception as e:
            logger.error(f"Error enriching portfolio with market data: {e}")
            return portfolio  # Retourner le portefeuille original en cas d'erreur
    
    def save_portfolio(
        self, 
        portfolio: pd.DataFrame, 
        file_name: str, 
        format: str = 'csv'
    ) -> str:
        """
        Sauvegarder le portefeuille dans un fichier.
        
        Args:
            portfolio: DataFrame du portefeuille
            file_name: Nom du fichier (sans extension)
            format: Format du fichier ('csv', 'excel', 'json', 'parquet')
            
        Returns:
            Chemin vers le fichier sauvegardé
        """
        file_path = os.path.join(self.data_dir, f"{file_name}")
        
        try:
            if format.lower() == 'csv':
                file_path += '.csv'
                portfolio.to_csv(file_path, index=False)
            elif format.lower() == 'excel':
                file_path += '.xlsx'
                portfolio.to_excel(file_path, index=False)
            elif format.lower() == 'json':
                file_path += '.json'
                portfolio.to_json(file_path, orient='records', indent=4)
            elif format.lower() == 'parquet':
                file_path += '.parquet'
                portfolio.to_parquet(file_path, index=False)
            else:
                logger.error(f"Unsupported format: {format}")
                return ""
            
            logger.info(f"Portfolio saved to {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving portfolio: {e}")
            return ""


# Exemple d'utilisation
if __name__ == "__main__":
    # Configurer le logging
    logging.basicConfig(level=logging.INFO)
    
    # Créer une instance du chargeur de portefeuille
    loader = PortfolioLoader()
    
    # Exemple de création d'un portefeuille
    portfolio_data = {
        'Security': ['Apple Inc.', 'Microsoft Corp.', 'Amazon.com Inc.', 'Alphabet Inc.', 'Meta Platforms Inc.'],
        'Ticker': ['AAPL', 'MSFT', 'AMZN', 'GOOG', 'META'],
        'Quantity': [100, 50, 20, 15, 40],
        'AssetClass': ['Equity', 'Equity', 'Equity', 'Equity', 'Equity'],
        'Sector': ['Technology', 'Technology', 'Consumer Discretionary', 'Communication Services', 'Communication Services'],
        'Currency': ['USD', 'USD', 'USD', 'USD', 'USD']
    }
    
    # Créer un DataFrame
    portfolio = pd.DataFrame(portfolio_data)
    
    # Sauvegarder le portefeuille
    file_path = loader.save_portfolio(portfolio, 'example_portfolio', format='csv')
    print(f"Portfolio saved to: {file_path}")
    
    # Charger le portefeuille sauvegardé
    loaded_portfolio = loader.load_portfolio_from_csv(file_path)
    print("Loaded portfolio:")
    print(loaded_portfolio.head())
