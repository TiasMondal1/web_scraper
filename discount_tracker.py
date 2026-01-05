"""
Discount Tracking Module
Tracks discounts, price drops, and savings
"""
from database import PriceDatabase
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class DiscountTracker:
    def __init__(self, db_file='price_history.db'):
        self.db = PriceDatabase(db_file)
    
    def calculate_discount(self, product_name: str) -> Dict:
        """Calculate current discount percentage and savings"""
        df = self.db.get_price_history(product_name)
        
        if df.empty or len(df) < 2:
            return {'error': 'Insufficient data'}
        
        max_price = df['Price'].max()
        current_price = df['Price'].iloc[-1]
        min_price = df['Price'].min()
        avg_price = df['Price'].mean()
        
        # Calculate discounts
        discount_from_max = ((max_price - current_price) / max_price) * 100 if max_price > 0 else 0
        discount_from_avg = ((avg_price - current_price) / avg_price) * 100 if avg_price > 0 else 0
        
        savings_from_max = max_price - current_price
        savings_from_avg = avg_price - current_price
        
        return {
            'product_name': product_name,
            'current_price': float(current_price),
            'maximum_price': float(max_price),
            'minimum_price': float(min_price),
            'average_price': float(avg_price),
            'discount_from_max_percent': float(discount_from_max),
            'discount_from_avg_percent': float(discount_from_avg),
            'savings_from_max': float(savings_from_max),
            'savings_from_avg': float(savings_from_avg),
            'is_lowest_price': current_price == min_price,
            'is_below_average': current_price < avg_price
        }
    
    def get_price_drops(self, product_name: str, days_back: int = 30) -> List[Dict]:
        """Get list of price drops in the last N days"""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        df = self.db.get_price_history(product_name)
        
        if df.empty or len(df) < 2:
            return []
        
        if 'Date' in df.columns:
            df_filtered = df[df['Date'] >= cutoff_date].copy()
        else:
            df_filtered = df.tail(days_back).copy()
        
        if df_filtered.empty:
            df_filtered = df.copy()
        
        price_drops = []
        for i in range(1, len(df_filtered)):
            prev_price = df_filtered['Price'].iloc[i-1]
            current_price = df_filtered['Price'].iloc[i]
            
            if current_price < prev_price:
                drop_amount = prev_price - current_price
                drop_percent = (drop_amount / prev_price) * 100
                
                date = df_filtered['Date'].iloc[i] if 'Date' in df_filtered.columns else None
                
                price_drops.append({
                    'date': date.isoformat() if date and hasattr(date, 'isoformat') else str(date),
                    'previous_price': float(prev_price),
                    'new_price': float(current_price),
                    'drop_amount': float(drop_amount),
                    'drop_percent': float(drop_percent)
                })
        
        return sorted(price_drops, key=lambda x: x.get('drop_amount', 0), reverse=True)
    
    def get_best_discount_period(self, product_name: str) -> Dict:
        """Find the period with the best discount"""
        df = self.db.get_price_history(product_name)
        
        if df.empty:
            return {'error': 'No data available'}
        
        min_price = df['Price'].min()
        min_price_row = df[df['Price'] == min_price].iloc[0]
        min_price_date = min_price_row['Date'] if 'Date' in min_price_row else None
        
        max_price = df['Price'].max()
        max_price_row = df[df['Price'] == max_price].iloc[0]
        max_price_date = max_price_row['Date'] if 'Date' in max_price_row else None
        
        best_discount = ((max_price - min_price) / max_price) * 100 if max_price > 0 else 0
        
        return {
            'product_name': product_name,
            'best_price': float(min_price),
            'best_price_date': min_price_date.isoformat() if min_price_date and hasattr(min_price_date, 'isoformat') else str(min_price_date),
            'highest_price': float(max_price),
            'highest_price_date': max_price_date.isoformat() if max_price_date and hasattr(max_price_date, 'isoformat') else str(max_price_date),
            'best_discount_percent': float(best_discount),
            'potential_savings': float(max_price - min_price)
        }


