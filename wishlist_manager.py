"""
Wishlist Management Module
Manages product wishlists and tracking preferences
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from database import PriceDatabase

class WishlistManager:
    def __init__(self, wishlist_file='wishlist.json', db_file='price_history.db'):
        self.wishlist_file = wishlist_file
        self.db = PriceDatabase(db_file)
        self.wishlist = self._load_wishlist()
    
    def _load_wishlist(self) -> Dict:
        """Load wishlist from file"""
        if os.path.exists(self.wishlist_file):
            try:
                with open(self.wishlist_file, 'r') as f:
                    return json.load(f)
            except:
                return {'wishlists': {}, 'products': []}
        return {'wishlists': {}, 'products': []}
    
    def _save_wishlist(self):
        """Save wishlist to file"""
        with open(self.wishlist_file, 'w') as f:
            json.dump(self.wishlist, f, indent=4)
    
    def create_wishlist(self, name: str, description: Optional[str] = None) -> bool:
        """Create a new wishlist"""
        if name in self.wishlist['wishlists']:
            return False  # Wishlist already exists
        
        self.wishlist['wishlists'][name] = {
            'description': description or '',
            'created_at': datetime.now().isoformat(),
            'product_ids': []
        }
        self._save_wishlist()
        return True
    
    def add_to_wishlist(self, wishlist_name: str, product_name: str) -> bool:
        """Add a product to a wishlist"""
        if wishlist_name not in self.wishlist['wishlists']:
            self.create_wishlist(wishlist_name)
        
        # Get product from database
        products = self.db.get_all_products()
        product_id = None
        for p in products:
            if p['name'] == product_name:
                product_id = p['id']
                break
        
        if product_id is None:
            return False  # Product not found
        
        if product_id not in self.wishlist['wishlists'][wishlist_name]['product_ids']:
            self.wishlist['wishlists'][wishlist_name]['product_ids'].append(product_id)
            self._save_wishlist()
            return True
        
        return False  # Already in wishlist
    
    def remove_from_wishlist(self, wishlist_name: str, product_name: str) -> bool:
        """Remove a product from a wishlist"""
        if wishlist_name not in self.wishlist['wishlists']:
            return False
        
        # Get product ID
        products = self.db.get_all_products()
        product_id = None
        for p in products:
            if p['name'] == product_name:
                product_id = p['id']
                break
        
        if product_id is None:
            return False
        
        if product_id in self.wishlist['wishlists'][wishlist_name]['product_ids']:
            self.wishlist['wishlists'][wishlist_name]['product_ids'].remove(product_id)
            self._save_wishlist()
            return True
        
        return False
    
    def get_wishlist_products(self, wishlist_name: str) -> List[Dict]:
        """Get all products in a wishlist"""
        if wishlist_name not in self.wishlist['wishlists']:
            return []
        
        product_ids = self.wishlist['wishlists'][wishlist_name]['product_ids']
        products = self.db.get_all_products()
        
        result = []
        for product in products:
            if product['id'] in product_ids:
                latest_price = self.db.get_latest_price(product['name'])
                result.append({
                    'id': product['id'],
                    'name': product['name'],
                    'url': product['url'],
                    'latest_price': latest_price
                })
        
        return result
    
    def get_all_wishlists(self) -> Dict:
        """Get all wishlists with summary"""
        result = {}
        for name, wishlist_data in self.wishlist['wishlists'].items():
            product_count = len(wishlist_data['product_ids'])
            result[name] = {
                'description': wishlist_data['description'],
                'created_at': wishlist_data['created_at'],
                'product_count': product_count
            }
        return result
    
    def delete_wishlist(self, wishlist_name: str) -> bool:
        """Delete a wishlist"""
        if wishlist_name in self.wishlist['wishlists']:
            del self.wishlist['wishlists'][wishlist_name]
            self._save_wishlist()
            return True
        return False

