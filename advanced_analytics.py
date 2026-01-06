"""
Advanced Analytics Module
ML price prediction, volatility analysis, seasonal trends
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from database import PriceDatabase
from typing import Dict, Optional, List
import warnings
warnings.filterwarnings('ignore')

# Try to import ML libraries (optional)
try:
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

class AdvancedAnalytics:
    def __init__(self, db_file='price_history.db'):
        self.db = PriceDatabase(db_file)
    
    def calculate_volatility(self, product_name: str, days_back: int = 30) -> Dict:
        """Calculate price volatility metrics"""
        df = self.db.get_price_history(product_name)
        
        if df.empty:
            return {'error': 'No data available'}
        
        # Filter to last N days
        cutoff_date = datetime.now() - timedelta(days=days_back)
        if 'Date' in df.columns:
            df_filtered = df[df['Date'] >= cutoff_date].copy()
        else:
            df_filtered = df.copy()
        
        if df_filtered.empty or len(df_filtered) < 2:
            return {'error': 'Insufficient data for volatility calculation'}
        
        prices = df_filtered['Price'].values
        
        # Calculate returns (percentage change)
        returns = np.diff(prices) / prices[:-1] * 100
        
        # Volatility metrics
        volatility = np.std(returns)  # Standard deviation of returns
        variance = np.var(returns)
        max_drawdown = self._calculate_max_drawdown(prices)
        
        # Price range metrics
        price_range = np.max(prices) - np.min(prices)
        price_range_percent = (price_range / np.min(prices)) * 100
        
        # Volatility classification
        if volatility < 2:
            volatility_level = "Low"
        elif volatility < 5:
            volatility_level = "Medium"
        else:
            volatility_level = "High"
        
        return {
            'product_name': product_name,
            'period_days': days_back,
            'volatility': float(volatility),
            'variance': float(variance),
            'max_drawdown': float(max_drawdown),
            'price_range': float(price_range),
            'price_range_percent': float(price_range_percent),
            'volatility_level': volatility_level,
            'data_points': len(df_filtered)
        }
    
    def detect_seasonal_trends(self, product_name: str) -> Dict:
        """Detect seasonal patterns in price data"""
        df = self.db.get_price_history(product_name)
        
        if df.empty or 'Date' not in df.columns:
            return {'error': 'Date data required for seasonal analysis'}
        
        df['Date'] = pd.to_datetime(df['Date'])
        df['Month'] = df['Date'].dt.month
        df['DayOfWeek'] = df['Date'].dt.dayofweek
        df['Quarter'] = df['Date'].dt.quarter
        
        # Monthly patterns
        monthly_stats = df.groupby('Month')['Price'].agg(['mean', 'min', 'max', 'std']).to_dict('index')
        
        # Day of week patterns
        daily_stats = df.groupby('DayOfWeek')['Price'].agg(['mean', 'min', 'max']).to_dict('index')
        
        # Quarterly patterns
        quarterly_stats = df.groupby('Quarter')['Price'].agg(['mean', 'min', 'max']).to_dict('index')
        
        # Find best and worst months
        monthly_avg = df.groupby('Month')['Price'].mean()
        best_month = monthly_avg.idxmin()
        worst_month = monthly_avg.idxmax()
        
        return {
            'product_name': product_name,
            'monthly_patterns': {str(k): v for k, v in monthly_stats.items()},
            'daily_patterns': {str(k): v for k, v in daily_stats.items()},
            'quarterly_patterns': {str(k): v for k, v in quarterly_stats.items()},
            'best_month': int(best_month),
            'worst_month': int(worst_month),
            'monthly_average_prices': {str(k): float(v) for k, v in monthly_avg.to_dict().items()}
        }
    
    def predict_price(self, product_name: str, days_ahead: int = 7, method: str = 'linear') -> Dict:
        """Predict future price using ML or statistical methods"""
        if not SKLEARN_AVAILABLE and method == 'ml':
            method = 'linear'  # Fallback to linear regression
        
        df = self.db.get_price_history(product_name)
        
        if df.empty:
            return {'error': 'No data available'}
        
        if len(df) < 10:
            return {'error': 'Insufficient data for prediction (need at least 10 data points)'}
        
        # Prepare data
        df_sorted = df.sort_values('Date' if 'Date' in df.columns else df.index[0])
        prices = df_sorted['Price'].values
        
        if method == 'linear' or not SKLEARN_AVAILABLE:
            # Simple linear regression using numpy
            X = np.arange(len(prices)).reshape(-1, 1)
            y = prices
            
            # Fit linear model
            coeffs = np.polyfit(X.flatten(), y, 1)
            
            # Predict future prices
            future_X = np.arange(len(prices), len(prices) + days_ahead).reshape(-1, 1)
            predictions = np.polyval(coeffs, future_X.flatten())
            
            slope = coeffs[0]
            intercept = coeffs[1]
            
        elif method == 'ml' and SKLEARN_AVAILABLE:
            # Use scikit-learn for more sophisticated prediction
            X = np.arange(len(prices)).reshape(-1, 1)
            y = prices
            
            # Create features (could be enhanced with lag features, etc.)
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
            
            model = LinearRegression()
            model.fit(X_train, y_train)
            
            # Predict
            future_X = np.arange(len(prices), len(prices) + days_ahead).reshape(-1, 1)
            predictions = model.predict(future_X)
            
            slope = model.coef_[0]
            intercept = model.intercept_
        
        else:
            return {'error': f'Unknown prediction method: {method}'}
        
        # Calculate confidence (based on recent volatility)
        recent_prices = prices[-min(30, len(prices)):]
        volatility = np.std(recent_prices)
        
        current_price = prices[-1]
        predicted_price = predictions[-1]
        price_change = predicted_price - current_price
        price_change_percent = (price_change / current_price) * 100
        
        # Generate prediction dates
        if 'Date' in df_sorted.columns:
            last_date = pd.to_datetime(df_sorted['Date'].iloc[-1])
            prediction_dates = [(last_date + timedelta(days=i+1)).isoformat() for i in range(days_ahead)]
        else:
            prediction_dates = [f"Day {i+1}" for i in range(days_ahead)]
        
        return {
            'product_name': product_name,
            'method': method,
            'days_ahead': days_ahead,
            'current_price': float(current_price),
            'predicted_price': float(predicted_price),
            'predicted_change': float(price_change),
            'predicted_change_percent': float(price_change_percent),
            'predictions': [
                {'date': date, 'predicted_price': float(pred)}
                for date, pred in zip(prediction_dates, predictions)
            ],
            'trend': 'increasing' if slope > 0 else 'decreasing',
            'slope': float(slope),
            'confidence': 'low' if volatility > current_price * 0.1 else 'medium' if volatility > current_price * 0.05 else 'high',
            'volatility': float(volatility)
        }
    
    def moving_averages(self, product_name: str, windows: List[int] = [7, 14, 30]) -> Dict:
        """Calculate moving averages for trend analysis"""
        df = self.db.get_price_history(product_name)
        
        if df.empty:
            return {'error': 'No data available'}
        
        # Ensure data is sorted by date
        if 'Date' in df.columns:
            df = df.sort_values('Date')
            df['Date'] = pd.to_datetime(df['Date'])
        
        prices = df['Price'].values
        
        moving_avgs = {}
        for window in windows:
            if len(prices) >= window:
                ma = pd.Series(prices).rolling(window=window).mean()
                moving_avgs[f'MA_{window}'] = {
                    'values': [float(x) if pd.notna(x) else None for x in ma],
                    'latest': float(ma.iloc[-1]) if pd.notna(ma.iloc[-1]) else None
                }
        
        # Golden/Death cross detection (if we have multiple MAs)
        if len(windows) >= 2 and len(moving_avgs) >= 2:
            short_ma_key = f'MA_{min(windows)}'
            long_ma_key = f'MA_{max(windows)}'
            
            if moving_avgs[short_ma_key]['latest'] and moving_avgs[long_ma_key]['latest']:
                if moving_avgs[short_ma_key]['latest'] > moving_avgs[long_ma_key]['latest']:
                    crossover = "Golden Cross (Bullish)"
                else:
                    crossover = "Death Cross (Bearish)"
            else:
                crossover = None
        else:
            crossover = None
        
        return {
            'product_name': product_name,
            'moving_averages': moving_avgs,
            'current_price': float(prices[-1]),
            'crossover_signal': crossover
        }
    
    def _calculate_max_drawdown(self, prices: np.ndarray) -> float:
        """Calculate maximum drawdown (peak to trough decline)"""
        cumulative = np.cumsum(prices)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = cumulative - running_max
        max_drawdown = np.min(drawdown)
        return abs(max_drawdown) if max_drawdown < 0 else 0
    
    def support_resistance_levels(self, product_name: str, window: int = 30) -> Dict:
        """Identify support and resistance price levels"""
        df = self.db.get_price_history(product_name)
        
        if df.empty:
            return {'error': 'No data available'}
        
        # Filter to recent data
        cutoff_date = datetime.now() - timedelta(days=window)
        if 'Date' in df.columns:
            df_filtered = df[df['Date'] >= cutoff_date].copy()
        else:
            df_filtered = df.tail(window).copy()
        
        if df_filtered.empty:
            df_filtered = df.copy()
        
        prices = df_filtered['Price'].values
        
        # Simple support/resistance: price levels that prices frequently touch
        # This is a simplified approach - real support/resistance analysis is more complex
        
        # Find local minima (potential support) and maxima (potential resistance)
        from scipy.signal import argrelextrema
        
        try:
            # Find local minima and maxima
            minima_indices = argrelextrema(prices, np.less, order=3)[0]
            maxima_indices = argrelextrema(prices, np.greater, order=3)[0]
            
            support_levels = sorted(set(prices[minima_indices]))[:5]  # Top 5 support levels
            resistance_levels = sorted(set(prices[maxima_indices]), reverse=True)[:5]  # Top 5 resistance levels
            
            current_price = prices[-1]
            
            # Find nearest support and resistance
            nearest_support = max([s for s in support_levels if s <= current_price], default=min(support_levels) if support_levels else None)
            nearest_resistance = min([r for r in resistance_levels if r >= current_price], default=max(resistance_levels) if resistance_levels else None)
            
            return {
                'product_name': product_name,
                'current_price': float(current_price),
                'support_levels': [float(s) for s in support_levels],
                'resistance_levels': [float(r) for r in resistance_levels],
                'nearest_support': float(nearest_support) if nearest_support else None,
                'nearest_resistance': float(nearest_resistance) if nearest_resistance else None
            }
        except ImportError:
            # Fallback if scipy is not available
            return {
                'product_name': product_name,
                'current_price': float(prices[-1]),
                'error': 'scipy required for support/resistance analysis',
                'min_price': float(np.min(prices)),
                'max_price': float(np.max(prices)),
                'avg_price': float(np.mean(prices))
            }




