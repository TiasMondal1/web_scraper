"""
Database Module for Price Tracking
Uses SQLite for storing price history data
"""
import sqlite3
import pandas as pd
from datetime import datetime
import os
from typing import Optional, List, Dict

class PriceDatabase:
    def __init__(self, db_file='price_history.db'):
        self.db_file = db_file
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_file)
    
    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                url TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create price_history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                price REAL NOT NULL,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_product_id ON price_history(product_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_recorded_at ON price_history(recorded_at)
        ''')
        
        conn.commit()
        conn.close()
    
    def add_product(self, name: str, url: str) -> int:
        """Add a product to the database, returns product_id"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO products (name, url, updated_at)
                VALUES (?, ?, ?)
            ''', (name, url, datetime.now()))
            
            # Get the product_id
            cursor.execute('SELECT id FROM products WHERE name = ?', (name,))
            result = cursor.fetchone()
            product_id = result[0] if result else None
            
            conn.commit()
            return product_id
        except sqlite3.IntegrityError:
            # Product already exists, get its ID
            cursor.execute('SELECT id FROM products WHERE name = ?', (name,))
            result = cursor.fetchone()
            return result[0] if result else None
        finally:
            conn.close()
    
    def get_product_id(self, name: str) -> Optional[int]:
        """Get product ID by name"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM products WHERE name = ?', (name,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    def add_price_record(self, product_name: str, price: float, recorded_at: Optional[datetime] = None) -> bool:
        """Add a price record for a product"""
        if recorded_at is None:
            recorded_at = datetime.now()
        
        # Ensure product exists
        product_id = self.get_product_id(product_name)
        if product_id is None:
            print(f"Product '{product_name}' not found. Please add it first.")
            return False
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO price_history (product_id, price, recorded_at)
                VALUES (?, ?, ?)
            ''', (product_id, price, recorded_at))
            
            # Update product's updated_at timestamp
            cursor.execute('''
                UPDATE products SET updated_at = ? WHERE id = ?
            ''', (recorded_at, product_id))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding price record: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_latest_price(self, product_name: str) -> Optional[float]:
        """Get the latest price for a product"""
        product_id = self.get_product_id(product_name)
        if product_id is None:
            return None
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT price FROM price_history
            WHERE product_id = ?
            ORDER BY recorded_at DESC
            LIMIT 1
        ''', (product_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    def get_price_history(self, product_name: str, limit: Optional[int] = None) -> pd.DataFrame:
        """Get price history for a product as pandas DataFrame"""
        product_id = self.get_product_id(product_name)
        if product_id is None:
            return pd.DataFrame(columns=['Date', 'Time', 'Price'])
        
        conn = self.get_connection()
        
        query = '''
            SELECT 
                DATE(recorded_at) as Date,
                TIME(recorded_at) as Time,
                price as Price
            FROM price_history
            WHERE product_id = ?
            ORDER BY recorded_at ASC
        '''
        
        if limit:
            query += f' LIMIT {limit}'
        
        df = pd.read_sql_query(query, conn, params=(product_id,))
        conn.close()
        
        if not df.empty:
            df['Date'] = pd.to_datetime(df['Date'])
        
        return df
    
    def get_all_products(self) -> List[Dict]:
        """Get all products from database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, name, url, created_at, updated_at FROM products')
        rows = cursor.fetchall()
        conn.close()
        
        products = []
        for row in rows:
            products.append({
                'id': row[0],
                'name': row[1],
                'url': row[2],
                'created_at': row[3],
                'updated_at': row[4]
            })
        
        return products
    
    def get_all_product_names(self) -> List[str]:
        """Get list of all product names"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT name FROM products ORDER BY name')
        rows = cursor.fetchall()
        conn.close()
        
        return [row[0] for row in rows]
    
    def delete_product(self, product_name: str) -> bool:
        """Delete a product and all its price history"""
        product_id = self.get_product_id(product_name)
        if product_id is None:
            return False
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Delete price history first (foreign key constraint)
            cursor.execute('DELETE FROM price_history WHERE product_id = ?', (product_id,))
            # Delete product
            cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting product: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_statistics(self, product_name: str) -> Dict:
        """Get price statistics for a product"""
        df = self.get_price_history(product_name)
        
        if df.empty:
            return {}
        
        return {
            'count': len(df),
            'min_price': df['Price'].min(),
            'max_price': df['Price'].max(),
            'avg_price': df['Price'].mean(),
            'std_price': df['Price'].std(),
            'first_price': df['Price'].iloc[0],
            'last_price': df['Price'].iloc[-1],
            'first_date': df['Date'].min(),
            'last_date': df['Date'].max()
        }

