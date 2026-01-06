import sqlite3
import pandas as pd
from datetime import datetime
import os
from typing import List, Optional, Dict, Any

class DatabaseManager:
    def __init__(self, db_path: str = 'price_history.db'):
        """Initialize database manager with SQLite database"""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create products table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
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
                    scraped_at TIMESTAMP NOT NULL,
                    date_only DATE NOT NULL,
                    time_only TIME NOT NULL,
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_price_history_product_id 
                ON price_history(product_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_price_history_date 
                ON price_history(date_only)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_price_history_scraped_at 
                ON price_history(scraped_at)
            ''')
            
            conn.commit()
    
    def add_product(self, name: str, url: str) -> int:
        """Add a new product to track"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO products (name, url) 
                    VALUES (?, ?)
                ''', (name, url))
                conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                # Product already exists, get its ID
                cursor.execute('SELECT id FROM products WHERE name = ?', (name,))
                result = cursor.fetchone()
                return result[0] if result else None
    
    def get_product_id(self, product_name: str) -> Optional[int]:
        """Get product ID by name"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM products WHERE name = ?', (product_name,))
            result = cursor.fetchone()
            return result[0] if result else None
    
    def add_price_record(self, product_name: str, price: float, timestamp: Optional[datetime] = None) -> bool:
        """Add a new price record for a product"""
        if timestamp is None:
            timestamp = datetime.now()
        
        product_id = self.get_product_id(product_name)
        if not product_id:
            print(f"Product '{product_name}' not found in database")
            return False
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            date_only = timestamp.strftime('%Y-%m-%d')
            time_only = timestamp.strftime('%H:%M:%S')
            
            cursor.execute('''
                INSERT INTO price_history (product_id, price, scraped_at, date_only, time_only)
                VALUES (?, ?, ?, ?, ?)
            ''', (product_id, price, timestamp, date_only, time_only))
            
            conn.commit()
            return True
    
    def get_product_data(self, product_name: str) -> Optional[pd.DataFrame]:
        """Get all price data for a specific product"""
        product_id = self.get_product_id(product_name)
        if not product_id:
            return None
        
        with sqlite3.connect(self.db_path) as conn:
            query = '''
                SELECT date_only as Date, time_only as Time, price as Price
                FROM price_history
                WHERE product_id = ?
                ORDER BY scraped_at ASC
            '''
            df = pd.read_sql_query(query, conn, params=(product_id,))
            
            if not df.empty:
                df['Date'] = pd.to_datetime(df['Date'])
            
            return df
    
    def get_all_products(self) -> List[str]:
        """Get list of all tracked products"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM products ORDER BY name')
            return [row[0] for row in cursor.fetchall()]
    
    def get_latest_price(self, product_name: str) -> Optional[Dict[str, Any]]:
        """Get the latest price for a product"""
        product_id = self.get_product_id(product_name)
        if not product_id:
            return None
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT price, scraped_at
                FROM price_history
                WHERE product_id = ?
                ORDER BY scraped_at DESC
                LIMIT 1
            ''', (product_id,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'price': result[0],
                    'timestamp': result[1]
                }
            return None
    
    def get_price_statistics(self, product_name: str) -> Optional[Dict[str, Any]]:
        """Get price statistics for a product"""
        product_id = self.get_product_id(product_name)
        if not product_id:
            return None
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    COUNT(*) as record_count,
                    AVG(price) as avg_price,
                    MIN(price) as min_price,
                    MAX(price) as max_price,
                    MIN(scraped_at) as first_recorded,
                    MAX(scraped_at) as last_recorded
                FROM price_history
                WHERE product_id = ?
            ''', (product_id,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'record_count': result[0],
                    'avg_price': result[1],
                    'min_price': result[2],
                    'max_price': result[3],
                    'first_recorded': result[4],
                    'last_recorded': result[5]
                }
            return None
    
    def migrate_from_excel(self, excel_file: str = 'price_history.xlsx') -> bool:
        """Migrate existing Excel data to database"""
        if not os.path.exists(excel_file):
            print(f"Excel file '{excel_file}' not found")
            return False
        
        try:
            excel_data = pd.ExcelFile(excel_file)
            migrated_count = 0
            
            for sheet_name in excel_data.sheet_names:
                print(f"Migrating sheet: {sheet_name}")
                
                # Add product to database
                self.add_product(sheet_name, "")  # URL will need to be updated manually
                
                # Read the sheet data
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                
                if not df.empty:
                    for _, row in df.iterrows():
                        # Combine date and time into datetime
                        try:
                            date_str = str(row['Date'])
                            time_str = str(row['Time'])
                            
                            # Handle different date formats
                            if 'T' in date_str:
                                timestamp = pd.to_datetime(date_str)
                            else:
                                timestamp = pd.to_datetime(f"{date_str} {time_str}")
                            
                            # Convert pandas timestamp to Python datetime
                            if hasattr(timestamp, 'to_pydatetime'):
                                timestamp = timestamp.to_pydatetime()
                            
                            # Add price record
                            if self.add_price_record(sheet_name, float(row['Price']), timestamp):
                                migrated_count += 1
                        except Exception as e:
                            print(f"Error migrating row in {sheet_name}: {e}")
                            continue
            
            print(f"Migration completed. {migrated_count} records migrated.")
            return True
            
        except Exception as e:
            print(f"Migration failed: {e}")
            return False
    
    def export_to_excel(self, output_file: str = 'exported_price_history.xlsx') -> bool:
        """Export database data back to Excel format"""
        try:
            products = self.get_all_products()
            
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                for product in products:
                    df = self.get_product_data(product)
                    if df is not None and not df.empty:
                        df.to_excel(writer, sheet_name=product, index=False)
            
            print(f"Data exported to {output_file}")
            return True
            
        except Exception as e:
            print(f"Export failed: {e}")
            return False
    
    def cleanup_old_records(self, days_to_keep: int = 365) -> int:
        """Remove price records older than specified days"""
        cutoff_date = datetime.now() - pd.Timedelta(days=days_to_keep)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM price_history
                WHERE scraped_at < ?
            ''', (cutoff_date,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
        print(f"Cleaned up {deleted_count} old records")
        return deleted_count
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get general database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get product count
            cursor.execute('SELECT COUNT(*) FROM products')
            product_count = cursor.fetchone()[0]
            
            # Get total records
            cursor.execute('SELECT COUNT(*) FROM price_history')
            total_records = cursor.fetchone()[0]
            
            # Get date range
            cursor.execute('SELECT MIN(scraped_at), MAX(scraped_at) FROM price_history')
            date_range = cursor.fetchone()
            
            # Get database size
            db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            
            return {
                'database_path': self.db_path,
                'database_size_mb': round(db_size / (1024 * 1024), 2),
                'product_count': product_count,
                'total_records': total_records,
                'date_range': {
                    'first_record': date_range[0],
                    'last_record': date_range[1]
                }
            }


def main():
    """Example usage and testing"""
    db = DatabaseManager()
    
    # Display database info
    info = db.get_database_info()
    print("Database Info:")
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    # Test migration from Excel
    if os.path.exists('price_history.xlsx'):
        print("\nMigrating from Excel...")
        db.migrate_from_excel()
    
    # Display updated info
    info = db.get_database_info()
    print("\nUpdated Database Info:")
    for key, value in info.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main() 