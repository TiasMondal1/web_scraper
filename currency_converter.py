"""
Currency Conversion Module
Supports currency conversion for prices
"""
import requests
from typing import Optional, Dict
from datetime import datetime

class CurrencyConverter:
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize currency converter
        
        Args:
            api_key: API key for exchange rate service (optional, uses free tier if not provided)
        """
        self.api_key = api_key
        self.base_url = "https://api.exchangerate-api.com/v4/latest"
        self.cache = {}
        self.cache_time = None
        self.cache_duration = 3600  # Cache for 1 hour
    
    def get_exchange_rates(self, base_currency: str = 'INR') -> Dict[str, float]:
        """Get exchange rates for a base currency"""
        # Check cache
        if self.cache_time and (datetime.now() - self.cache_time).seconds < self.cache_duration:
            if base_currency in self.cache:
                return self.cache[base_currency]
        
        try:
            url = f"{self.base_url}/{base_currency}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                rates = data.get('rates', {})
                
                # Cache the rates
                if base_currency not in self.cache:
                    self.cache[base_currency] = {}
                self.cache[base_currency] = rates
                self.cache_time = datetime.now()
                
                return rates
            else:
                # Return default rates if API fails
                return self._get_default_rates(base_currency)
        except Exception as e:
            print(f"Error fetching exchange rates: {e}")
            return self._get_default_rates(base_currency)
    
    def convert(self, amount: float, from_currency: str, to_currency: str) -> float:
        """
        Convert amount from one currency to another
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code (e.g., 'INR', 'USD')
            to_currency: Target currency code (e.g., 'USD', 'EUR')
        
        Returns:
            Converted amount
        """
        if from_currency == to_currency:
            return amount
        
        rates = self.get_exchange_rates(from_currency)
        
        if to_currency in rates:
            return amount * rates[to_currency]
        else:
            # Try reverse conversion
            reverse_rates = self.get_exchange_rates(to_currency)
            if from_currency in reverse_rates:
                return amount / reverse_rates[from_currency]
            else:
                return amount  # Return original if conversion fails
    
    def _get_default_rates(self, base_currency: str) -> Dict[str, float]:
        """Get default/fallback exchange rates (approximate)"""
        # These are approximate rates - for production, use a real API
        default_rates = {
            'INR': {
                'USD': 0.012,
                'EUR': 0.011,
                'GBP': 0.0095,
                'JPY': 1.8,
                'AUD': 0.018,
                'CAD': 0.016
            },
            'USD': {
                'INR': 83.0,
                'EUR': 0.92,
                'GBP': 0.79,
                'JPY': 150.0,
                'AUD': 1.5,
                'CAD': 1.35
            }
        }
        
        return default_rates.get(base_currency, {})
    
    def format_price(self, amount: float, currency: str) -> str:
        """Format price with currency symbol"""
        currency_symbols = {
            'INR': '₹',
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
            'JPY': '¥',
            'AUD': 'A$',
            'CAD': 'C$'
        }
        
        symbol = currency_symbols.get(currency, currency)
        return f"{symbol}{amount:,.2f}"





