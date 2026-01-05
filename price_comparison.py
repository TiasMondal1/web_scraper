"""
Price Comparison Module
Compare prices across sellers, trend comparison, best time analysis
"""
import pandas as pd
from datetime import datetime, timedelta
from database import PriceDatabase
from typing import List, Dict, Optional
import statistics

class PriceComparer:
    def __init__(self, db_file='price_history.db'):
        self.db = PriceDatabase(db_file)
    
    def compare_products(self, product_names: List[str]) -> Dict:
        """Compare prices and trends across multiple products"""
        comparison = {
            'products': [],
            'summary': {}
        }
        
        all_prices = []
        all_stats = []
        
        for product_name in product_names:
            df = self.db.get_price_history(product_name)
            stats = self.db.get_statistics(product_name)
            
            if df.empty:
                continue
            
            latest_price = df['Price'].iloc[-1]
            product_data = {
                'name': product_name,
                'latest_price': float(latest_price),
                'average_price': float(stats.get('avg_price', 0)),
                'min_price': float(stats.get('min_price', 0)),
                'max_price': float(stats.get('max_price', 0)),
                'price_change_percent': self._calculate_price_change(df),
                'record_count': stats.get('count', 0)
            }
            
            comparison['products'].append(product_data)
            all_prices.append(latest_price)
            all_stats.append(product_data)
        
        if comparison['products']:
            # Find cheapest and most expensive
            cheapest = min(all_stats, key=lambda x: x['latest_price'])
            most_expensive = max(all_stats, key=lambda x: x['latest_price'])
            
            comparison['summary'] = {
                'cheapest_product': cheapest['name'],
                'cheapest_price': cheapest['latest_price'],
                'most_expensive_product': most_expensive['name'],
                'most_expensive_price': most_expensive['latest_price'],
                'price_difference': most_expensive['latest_price'] - cheapest['latest_price'],
                'price_difference_percent': ((most_expensive['latest_price'] - cheapest['latest_price']) / cheapest['latest_price']) * 100,
                'average_price': statistics.mean(all_prices),
                'median_price': statistics.median(all_prices)
            }
        
        return comparison
    
    def compare_sellers(self, product_name: str, seller_urls: List[str]) -> Dict:
        """Compare prices for the same product across different sellers"""
        # This would require tracking multiple URLs for the same product
        # For now, we'll compare based on product names that might represent different sellers
        comparison = {
            'product_name': product_name,
            'sellers': []
        }
        
        # In a real implementation, you'd have seller information in the database
        # For now, this is a placeholder structure
        return comparison
    
    def analyze_best_buy_time(self, product_name: str, days_back: int = 30) -> Dict:
        """Analyze historical data to determine best time to buy"""
        df = self.db.get_price_history(product_name)
        
        if df.empty:
            return {'error': 'No data available'}
        
        # Filter to last N days
        cutoff_date = datetime.now() - timedelta(days=days_back)
        df_filtered = df[df['Date'] >= cutoff_date].copy() if 'Date' in df.columns else df.copy()
        
        if df_filtered.empty:
            df_filtered = df.copy()
        
        # Calculate statistics
        min_price = df_filtered['Price'].min()
        max_price = df_filtered['Price'].max()
        avg_price = df_filtered['Price'].mean()
        median_price = df_filtered['Price'].median()
        
        # Find when minimum price occurred
        min_price_row = df_filtered[df_filtered['Price'] == min_price].iloc[0]
        min_price_date = min_price_row['Date'] if 'Date' in min_price_row else None
        
        # Analyze day of week patterns
        if 'Date' in df_filtered.columns:
            df_filtered['DayOfWeek'] = pd.to_datetime(df_filtered['Date']).dt.day_name()
            day_stats = df_filtered.groupby('DayOfWeek')['Price'].agg(['mean', 'min', 'count']).to_dict('index')
        else:
            day_stats = {}
        
        # Analyze price trends
        current_price = df_filtered['Price'].iloc[-1]
        price_vs_min = ((current_price - min_price) / min_price) * 100
        price_vs_avg = ((current_price - avg_price) / avg_price) * 100
        
        # Recommendation
        if current_price <= min_price * 1.05:  # Within 5% of minimum
            recommendation = "Excellent time to buy - price is near historical low"
        elif current_price <= avg_price:
            recommendation = "Good time to buy - price is below average"
        elif current_price <= avg_price * 1.1:
            recommendation = "Fair time to buy - price is slightly above average"
        else:
            recommendation = "Wait for better price - current price is significantly above average"
        
        return {
            'product_name': product_name,
            'analysis_period_days': days_back,
            'current_price': float(current_price),
            'statistics': {
                'minimum_price': float(min_price),
                'maximum_price': float(max_price),
                'average_price': float(avg_price),
                'median_price': float(median_price),
                'minimum_price_date': min_price_date.isoformat() if min_price_date and hasattr(min_price_date, 'isoformat') else str(min_price_date)
            },
            'price_comparison': {
                'vs_minimum': float(price_vs_min),
                'vs_average': float(price_vs_avg),
                'is_near_minimum': current_price <= min_price * 1.05
            },
            'day_of_week_patterns': day_stats,
            'recommendation': recommendation
        }
    
    def compare_trends(self, product_names: List[str], days_back: int = 30) -> Dict:
        """Compare price trends across multiple products"""
        trends = {
            'products': [],
            'period_days': days_back
        }
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        for product_name in product_names:
            df = self.db.get_price_history(product_name)
            
            if df.empty:
                continue
            
            # Filter to period
            if 'Date' in df.columns:
                df_filtered = df[df['Date'] >= cutoff_date].copy()
            else:
                df_filtered = df.copy()
            
            if df_filtered.empty:
                continue
            
            # Calculate trend
            first_price = df_filtered['Price'].iloc[0]
            last_price = df_filtered['Price'].iloc[-1]
            price_change = last_price - first_price
            price_change_percent = (price_change / first_price) * 100
            
            # Determine trend direction
            if price_change_percent < -5:
                trend_direction = "decreasing"
            elif price_change_percent > 5:
                trend_direction = "increasing"
            else:
                trend_direction = "stable"
            
            trends['products'].append({
                'name': product_name,
                'start_price': float(first_price),
                'end_price': float(last_price),
                'price_change': float(price_change),
                'price_change_percent': float(price_change_percent),
                'trend_direction': trend_direction,
                'data_points': len(df_filtered)
            })
        
        return trends
    
    def find_best_deals(self, min_discount_percent: float = 10) -> List[Dict]:
        """Find products with significant price drops"""
        products = self.db.get_all_product_names()
        deals = []
        
        for product_name in products:
            df = self.db.get_price_history(product_name)
            
            if df.empty or len(df) < 2:
                continue
            
            # Calculate discount from highest to current
            max_price = df['Price'].max()
            current_price = df['Price'].iloc[-1]
            
            if max_price == 0:
                continue
            
            discount_percent = ((max_price - current_price) / max_price) * 100
            
            if discount_percent >= min_discount_percent:
                deals.append({
                    'product_name': product_name,
                    'current_price': float(current_price),
                    'maximum_price': float(max_price),
                    'discount_percent': float(discount_percent),
                    'savings': float(max_price - current_price)
                })
        
        # Sort by discount percentage
        deals.sort(key=lambda x: x['discount_percent'], reverse=True)
        return deals
    
    def _calculate_price_change(self, df: pd.DataFrame) -> float:
        """Calculate price change percentage"""
        if df.empty or len(df) < 2:
            return 0.0
        
        first_price = df['Price'].iloc[0]
        last_price = df['Price'].iloc[-1]
        
        if first_price == 0:
            return 0.0
        
        return ((last_price - first_price) / first_price) * 100
    
    def get_price_correlation(self, product_names: List[str]) -> Dict:
        """Calculate price correlation between products"""
        if len(product_names) < 2:
            return {'error': 'Need at least 2 products for correlation'}
        
        # Get price data for all products
        price_data = {}
        for product_name in product_names:
            df = self.db.get_price_history(product_name)
            if not df.empty:
                price_data[product_name] = df.set_index('Date')['Price'] if 'Date' in df.columns else df['Price']
        
        if len(price_data) < 2:
            return {'error': 'Insufficient data for correlation'}
        
        # Align data by date and calculate correlation
        try:
            df_aligned = pd.DataFrame(price_data)
            correlation_matrix = df_aligned.corr().to_dict()
            
            return {
                'products': product_names,
                'correlation_matrix': correlation_matrix,
                'note': 'Correlation values range from -1 (inverse) to 1 (direct), 0 means no correlation'
            }
        except Exception as e:
            return {'error': f'Error calculating correlation: {str(e)}'}



