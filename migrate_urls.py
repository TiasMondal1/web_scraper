#!/usr/bin/env python3
"""
Migration script to update product URLs in the database from products.json
"""

import json
import sqlite3
from database_manager import DatabaseManager

def update_product_urls():
    """Update product URLs from products.json"""
    
    # Load products from JSON
    try:
        with open('products.json', 'r') as file:
            config = json.load(file)
            products = config['products']
    except Exception as e:
        print(f"Error loading products.json: {e}")
        return False
    
    # Initialize database manager
    db = DatabaseManager()
    
    # Update URLs for each product
    updated_count = 0
    
    with sqlite3.connect(db.db_path) as conn:
        cursor = conn.cursor()
        
        for product in products:
            try:
                cursor.execute('''
                    UPDATE products 
                    SET url = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE name = ?
                ''', (product['url'], product['name']))
                
                if cursor.rowcount > 0:
                    print(f"Updated URL for: {product['name']}")
                    updated_count += 1
                else:
                    print(f"Product not found in database: {product['name']}")
                    
            except Exception as e:
                print(f"Error updating {product['name']}: {e}")
        
        conn.commit()
    
    print(f"\nMigration completed. Updated {updated_count} product URLs.")
    return True

def main():
    print("Updating product URLs from products.json...")
    update_product_urls()
    
    # Show updated database info
    db = DatabaseManager()
    info = db.get_database_info()
    print(f"\nDatabase Info:")
    print(f"  Products: {info['product_count']}")
    print(f"  Total records: {info['total_records']}")

if __name__ == "__main__":
    main() 