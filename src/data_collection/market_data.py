"""
Module pour la collecte de données de marché à partir de différentes sources.
"""

import pandas as pd
import numpy as np
import yfinance as yf
import pandas_datareader.data as web
from datetime import datetime, timedelta
import logging
import os
import requests
from typing import List, Dict, Optional, Union, Tuple

logger = logging.getLogger(__name__)


class MarketDataCollector:
    """
    Classe pour collecter des données de marché à partir de différentes sources.
    """
    
    def __init__(self, cache_dir: str = "data/market_data"):
        """
        Initialiser le collecteur de données de marché.
        
        Args:
            cache_dir: Répertoire pour stocker les données en cache
        """
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
    def get_stock_data(
        self, 
        tickers: List[str], 
        start_date: Union[str, datetime],
        end_date: Union[str, datetime] = None,
        interval: str = "1d",
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Récupérer les données historiques d'actions à partir de Yahoo Finance.
        
        Args:
            tickers: Liste des symboles d'actions
            start_date: Date de début
            end_date: Date de fin (par défaut, aujourd'hui)
            interval: Intervalle de temps ('1d', '1wk', '1mo')
            use_cache: Utiliser les données en cache si disponibles
            
        Returns:
            DataFrame avec les données des actions
        """
        if end_date is None:
            end_date = datetime.now()
            
        # Convertir les dates en chaînes si elles sont des objets datetime
        start_str = start_date.strftime('%Y-%m-%d') if isinstance(start_date, datetime) else start_date
        end_str = end_date.strftime('%Y-%m-%d') if isinstance(end_date, datetime) else end_date
        
        # Créer une clé de cache unique
        cache_key = f"stock_data_{'-'.join(tickers)}_{start_str}_{end_str}_{interval}.parquet"
        cache_path = os.path.join(self.cache_dir, cache_key)
        
        # Vérifier si les données sont en cache
        if use_cache and os.path.exists(cache_path):
            logger.info(f"Loading cached stock data from {cache_path}")
            return pd.read_parquet(cache_path)
        
        try:
            # Télécharger les données depuis Yahoo Finance
            data = yf.download(
                tickers=tickers,
                start=start_date,
                end=end_date,
                interval=interval,
                group_by='ticker',
                auto_adjust=True,
                threads=True
            )
            
            # Restructurer les données si un seul ticker est fourni
            if len(tickers) == 1:
                data = data.reset_index()
                data['Ticker'] = tickers[0]
            else:
                # Réorganiser les données pour un format plus facile à utiliser
                data = data.stack(level=0).reset_index().rename(
                    columns={'level_1': 'Ticker', 'level_0': 'Date'})
            
            # Sauvegarder les données en cache
            if use_cache:
                logger.info(f"Saving stock data to cache: {cache_path}")
                data.to_parquet(cache_path, index=False)
                
            return data
            
        except Exception as e:
            logger.error(f"Error retrieving stock data: {e}")
            return pd.DataFrame()
    
    def get_economic_data(
        self, 
        indicators: List[str], 
        start_date: Union[str, datetime],
        end_date: Union[str, datetime] = None,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Récupérer des données économiques à partir de FRED (Federal Reserve Economic Data).
        
        Args:
            indicators: Liste des indicateurs économiques (codes FRED)
            start_date: Date de début
            end_date: Date de fin (par défaut, aujourd'hui)
            use_cache: Utiliser les données en cache si disponibles
            
        Returns:
            DataFrame avec les données économiques
        """
        if end_date is None:
            end_date = datetime.now()
            
        # Convertir les dates en chaînes si elles sont des objets datetime
        start_str = start_date.strftime('%Y-%m-%d') if isinstance(start_date, datetime) else start_date
        end_str = end_date.strftime('%Y-%m-%d') if isinstance(end_date, datetime) else end_date
        
        # Créer une clé de cache unique
        cache_key = f"economic_data_{'-'.join(indicators)}_{start_str}_{end_str}.parquet"
        cache_path = os.path.join(self.cache_dir, cache_key)
        
        # Vérifier si les données sont en cache
        if use_cache and os.path.exists(cache_path):
            logger.info(f"Loading cached economic data from {cache_path}")
            return pd.read_parquet(cache_path)
        
        try:
            # Télécharger les données depuis FRED
            data = web.DataReader(
                indicators,
                'fred',
                start=start_date,
                end=end_date
            )
            
            # Restructurer les données pour un format plus facile à utiliser
            data = data.reset_index()
            
            # Sauvegarder les données en cache
            if use_cache:
                logger.info(f"Saving economic data to cache: {cache_path}")
                data.to_parquet(cache_path, index=False)
                
            return data
            
        except Exception as e:
            logger.error(f"Error retrieving economic data: {e}")
            return pd.DataFrame()

    def get_fx_rates(
        self, 
        currencies: List[str], 
        base_currency: str = "USD",
        start_date: Union[str, datetime] = None,
        end_date: Union[str, datetime] = None,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Récupérer les taux de change pour une liste de devises.
        
        Args:
            currencies: Liste des devises (ex: ['EUR', 'GBP', 'JPY'])
            base_currency: Devise de base (par défaut, USD)
            start_date: Date de début (par défaut, 1 an avant aujourd'hui)
            end_date: Date de fin (par défaut, aujourd'hui)
            use_cache: Utiliser les données en cache si disponibles
            
        Returns:
            DataFrame avec les taux de change
        """
        if end_date is None:
            end_date = datetime.now()
        
        if start_date is None:
            start_date = end_date - timedelta(days=365)
            
        # Convertir les dates en chaînes si elles sont des objets datetime
        start_str = start_date.strftime('%Y-%m-%d') if isinstance(start_date, datetime) else start_date
        end_str = end_date.strftime('%Y-%m-%d') if isinstance(end_date, datetime) else end_date
        
        # Créer une clé de cache unique
        currency_str = '-'.join(currencies)
        cache_key = f"fx_data_{currency_str}_{base_currency}_{start_str}_{end_str}.parquet"
        cache_path = os.path.join(self.cache_dir, cache_key)
        
        # Vérifier si les données sont en cache
        if use_cache and os.path.exists(cache_path):
            logger.info(f"Loading cached FX data from {cache_path}")
            return pd.read_parquet(cache_path)
        
        # Créer des paires de devises au format Yahoo Finance
        pairs = [f"{curr}{base_currency}=X" for curr in currencies]
        
        try:
            # Télécharger les données depuis Yahoo Finance
            data = yf.download(
                tickers=pairs,
                start=start_date,
                end=end_date,
                interval='1d',
                group_by='ticker',
                auto_adjust=True,
                threads=True
            )
            
            # Restructurer les données
            if len(pairs) == 1:
                data = data.reset_index()
                data['Currency'] = currencies[0]
            else:
                # Réorganiser les données pour un format plus facile à utiliser
                data = data.stack(level=0).reset_index().rename(
                    columns={'level_1': 'Pair', 'level_0': 'Date'})
                # Extraire la devise de la paire
                data['Currency'] = data['Pair'].str.extract(r'([A-Z]{3})')
            
            # Sauvegarder les données en cache
            if use_cache:
                logger.info(f"Saving FX data to cache: {cache_path}")
                data.to_parquet(cache_path, index=False)
                
            return data
            
        except Exception as e:
            logger.error(f"Error retrieving FX data: {e}")
            return pd.DataFrame()


# Exemple d'utilisation
if __name__ == "__main__":
    # Configurer le logging
    logging.basicConfig(level=logging.INFO)
    
    # Créer une instance du collecteur de données
    collector = MarketDataCollector()
    
    # Récupérer des données d'actions
    stocks = ['AAPL', 'MSFT', 'GOOG', 'AMZN', 'META']
    start_date = '2023-01-01'
    stock_data = collector.get_stock_data(stocks, start_date)
    print(f"Stock data shape: {stock_data.shape}")
    
    # Récupérer des données économiques
    indicators = ['GDP', 'UNRATE', 'CPIAUCSL', 'FEDFUNDS']
    economic_data = collector.get_economic_data(indicators, '2020-01-01')
    print(f"Economic data shape: {economic_data.shape}")
    
    # Récupérer des taux de change
    currencies = ['EUR', 'GBP', 'JPY', 'CAD', 'AUD']
    fx_data = collector.get_fx_rates(currencies)
    print(f"FX data shape: {fx_data.shape}")
