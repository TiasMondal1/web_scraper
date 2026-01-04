"""
Migration script to move data from Excel to SQLite database
"""
import pandas as pd
import os
from database import PriceDatabase

def migrate_excel_to_database(excel_file='price_history.xlsx', db_file='price_history.db'):
    """Migrate data from Excel file to SQLite database"""
    
    if not os.path.exists(excel_file):
        print(f"Excel file '{excel_file}' not found. Nothing to migrate.")
        return
    
    print(f"Starting migration from {excel_file} to {db_file}...")
    
    # Initialize database
    db = PriceDatabase(db_file)
    
    try:
        # Read Excel file
        excel_file_obj = pd.ExcelFile(excel_file)
        sheet_names = excel_file_obj.sheet_names
        
        print(f"Found {len(sheet_names)} product sheets in Excel file.")
        
        migrated_count = 0
        for sheet_name in sheet_names:
            try:
                # Read sheet data
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                
                if df.empty:
                    print(f"  Sheet '{sheet_name}' is empty. Skipping...")
                    continue
                
                # Get product URL from products.json (if available)
                url = "Unknown"
                try:
                    import json
                    with open('products.json', 'r') as f:
                        products = json.load(f).get('products', [])
                        for product in products:
                            if product['name'] == sheet_name:
                                url = product['url']
                                break
                except:
                    pass
                
                # Add product to database
                product_id = db.add_product(sheet_name, url)
                print(f"  Processing '{sheet_name}'... ({len(df)} records)")
                
                # Migrate price records
                records_added = 0
                for _, row in df.iterrows():
                    # Combine date and time if both exist
                    if 'Date' in row and 'Time' in row:
                        try:
                            date_str = str(row['Date'])
                            time_str = str(row['Time'])
                            # Handle different date formats
                            if isinstance(row['Date'], pd.Timestamp):
                                recorded_at = row['Date']
                                if pd.notna(row['Time']):
                                    time_part = pd.to_datetime(row['Time']).time()
                                    recorded_at = pd.Timestamp.combine(recorded_at.date(), time_part)
                            else:
                                recorded_at_str = f"{date_str} {time_str}"
                                recorded_at = pd.to_datetime(recorded_at_str)
                        except:
                            recorded_at = pd.to_datetime(row['Date'])
                    elif 'Date' in row:
                        recorded_at = pd.to_datetime(row['Date'])
                    else:
                        continue
                    
                    price = row['Price']
                    if pd.notna(price):
                        db.add_price_record(sheet_name, float(price), recorded_at)
                        records_added += 1
                
                print(f"    Added {records_added} price records for '{sheet_name}'")
                migrated_count += 1
                
            except Exception as e:
                print(f"  Error migrating sheet '{sheet_name}': {e}")
                continue
        
        print(f"\nMigration completed! Migrated {migrated_count} products to database.")
        print(f"Database file: {db_file}")
        
        # Optionally backup Excel file
        backup_file = excel_file + '.backup'
        if not os.path.exists(backup_file):
            import shutil
            shutil.copy2(excel_file, backup_file)
            print(f"Excel file backed up to: {backup_file}")
        
    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == "__main__":
    migrate_excel_to_database()

