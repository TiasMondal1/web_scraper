"""
Data Export and Backup Module
Supports CSV/JSON export, automated backups, and data archival
"""
import pandas as pd
import json
import os
import shutil
from datetime import datetime, timedelta
from database import PriceDatabase
from typing import Optional, List
import sqlite3

class DataExporter:
    def __init__(self, db_file='price_history.db'):
        self.db = PriceDatabase(db_file)
        self.export_dir = 'exports'
        self.backup_dir = 'backups'
        
        # Create directories if they don't exist
        os.makedirs(self.export_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def export_product_to_csv(self, product_name: str, output_file: Optional[str] = None) -> str:
        """Export product price history to CSV"""
        df = self.db.get_price_history(product_name)
        
        if df.empty:
            raise ValueError(f"No data found for product: {product_name}")
        
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_name = product_name.replace('/', '_').replace('\\', '_')
            output_file = os.path.join(self.export_dir, f"{safe_name}_{timestamp}.csv")
        
        df.to_csv(output_file, index=False)
        return output_file
    
    def export_product_to_json(self, product_name: str, output_file: Optional[str] = None) -> str:
        """Export product price history to JSON"""
        df = self.db.get_price_history(product_name)
        
        if df.empty:
            raise ValueError(f"No data found for product: {product_name}")
        
        # Convert DataFrame to list of records
        records = []
        for _, row in df.iterrows():
            records.append({
                'date': row['Date'].isoformat() if hasattr(row['Date'], 'isoformat') else str(row['Date']),
                'time': str(row['Time']),
                'price': float(row['Price'])
            })
        
        data = {
            'product_name': product_name,
            'export_date': datetime.now().isoformat(),
            'record_count': len(records),
            'data': records
        }
        
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_name = product_name.replace('/', '_').replace('\\', '_')
            output_file = os.path.join(self.export_dir, f"{safe_name}_{timestamp}.json")
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        return output_file
    
    def export_all_to_csv(self, output_file: Optional[str] = None) -> str:
        """Export all products to a single CSV file with multiple sheets (Excel) or separate CSV files"""
        products = self.db.get_all_product_names()
        
        if not products:
            raise ValueError("No products found in database")
        
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = os.path.join(self.export_dir, f"all_products_{timestamp}.xlsx")
        
        # Use Excel format to support multiple sheets
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            for product_name in products:
                df = self.db.get_price_history(product_name)
                if not df.empty:
                    # Clean sheet name (Excel has restrictions)
                    sheet_name = product_name[:31].replace('/', '_').replace('\\', '_')
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        return output_file
    
    def export_all_to_json(self, output_file: Optional[str] = None) -> str:
        """Export all products to a single JSON file"""
        products = self.db.get_all_product_names()
        
        if not products:
            raise ValueError("No products found in database")
        
        all_data = {
            'export_date': datetime.now().isoformat(),
            'products': []
        }
        
        for product_name in products:
            df = self.db.get_price_history(product_name)
            if not df.empty:
                records = []
                for _, row in df.iterrows():
                    records.append({
                        'date': row['Date'].isoformat() if hasattr(row['Date'], 'isoformat') else str(row['Date']),
                        'time': str(row['Time']),
                        'price': float(row['Price'])
                    })
                
                stats = self.db.get_statistics(product_name)
                all_data['products'].append({
                    'name': product_name,
                    'record_count': len(records),
                    'stats': stats,
                    'data': records
                })
        
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = os.path.join(self.export_dir, f"all_products_{timestamp}.json")
        
        with open(output_file, 'w') as f:
            json.dump(all_data, f, indent=2)
        
        return output_file
    
    def backup_database(self, backup_file: Optional[str] = None) -> str:
        """Create a backup of the SQLite database"""
        db_file = self.db.db_file
        
        if not os.path.exists(db_file):
            raise FileNotFoundError(f"Database file not found: {db_file}")
        
        if backup_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(self.backup_dir, f"price_history_backup_{timestamp}.db")
        
        shutil.copy2(db_file, backup_file)
        return backup_file
    
    def restore_database(self, backup_file: str, restore_file: Optional[str] = None) -> str:
        """Restore database from backup"""
        if not os.path.exists(backup_file):
            raise FileNotFoundError(f"Backup file not found: {backup_file}")
        
        if restore_file is None:
            restore_file = self.db.db_file
        
        # Create backup of current database before restoring
        if os.path.exists(restore_file):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            pre_restore_backup = os.path.join(self.backup_dir, f"pre_restore_backup_{timestamp}.db")
            shutil.copy2(restore_file, pre_restore_backup)
        
        shutil.copy2(backup_file, restore_file)
        return restore_file
    
    def archive_old_data(self, days_old: int = 90, archive_file: Optional[str] = None) -> str:
        """
        Archive price data older than specified days to a separate file
        Original data is removed from main database
        """
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        conn = sqlite3.connect(self.db.db_file)
        cursor = conn.cursor()
        
        # Get old records
        cursor.execute('''
            SELECT ph.id, p.name, ph.price, ph.recorded_at
            FROM price_history ph
            JOIN products p ON ph.product_id = p.id
            WHERE ph.recorded_at < ?
        ''', (cutoff_date,))
        
        old_records = cursor.fetchall()
        
        if not old_records:
            conn.close()
            return "No old records to archive"
        
        # Create archive data structure
        archive_data = {
            'archive_date': datetime.now().isoformat(),
            'cutoff_date': cutoff_date.isoformat(),
            'record_count': len(old_records),
            'records': []
        }
        
        # Group by product
        products_data = {}
        for record_id, product_name, price, recorded_at in old_records:
            if product_name not in products_data:
                products_data[product_name] = []
            products_data[product_name].append({
                'id': record_id,
                'price': price,
                'recorded_at': recorded_at
            })
        
        archive_data['products'] = [
            {'name': name, 'records': records}
            for name, records in products_data.items()
        ]
        
        # Save archive file
        if archive_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            archive_file = os.path.join(self.backup_dir, f"archive_{days_old}days_{timestamp}.json")
        
        with open(archive_file, 'w') as f:
            json.dump(archive_data, f, indent=2)
        
        # Delete old records from database
        cursor.execute('DELETE FROM price_history WHERE recorded_at < ?', (cutoff_date,))
        conn.commit()
        conn.close()
        
        return archive_file
    
    def cleanup_old_backups(self, days_to_keep: int = 30):
        """Delete backup files older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        deleted_count = 0
        
        for filename in os.listdir(self.backup_dir):
            filepath = os.path.join(self.backup_dir, filename)
            if os.path.isfile(filepath):
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                if file_time < cutoff_date:
                    os.remove(filepath)
                    deleted_count += 1
        
        return deleted_count
    
    def get_export_summary(self) -> dict:
        """Get summary of export and backup files"""
        exports = []
        backups = []
        
        if os.path.exists(self.export_dir):
            for filename in os.listdir(self.export_dir):
                filepath = os.path.join(self.export_dir, filename)
                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    exports.append({
                        'filename': filename,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
        
        if os.path.exists(self.backup_dir):
            for filename in os.listdir(self.backup_dir):
                filepath = os.path.join(self.backup_dir, filename)
                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    backups.append({
                        'filename': filename,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
        
        return {
            'exports': exports,
            'backups': backups,
            'export_count': len(exports),
            'backup_count': len(backups)
        }

def main():
    """CLI interface for data export"""
    import argparse
    
    exporter = DataExporter()
    
    parser = argparse.ArgumentParser(description='Data Export and Backup Tool')
    parser.add_argument('--export-product', help='Export specific product (CSV)')
    parser.add_argument('--export-all', action='store_true', help='Export all products')
    parser.add_argument('--format', choices=['csv', 'json', 'excel'], default='csv', help='Export format')
    parser.add_argument('--backup', action='store_true', help='Backup database')
    parser.add_argument('--archive', type=int, help='Archive data older than N days')
    parser.add_argument('--cleanup', type=int, help='Cleanup backups older than N days')
    parser.add_argument('--summary', action='store_true', help='Show export/backup summary')
    
    args = parser.parse_args()
    
    if args.export_product:
        try:
            if args.format == 'csv':
                file = exporter.export_product_to_csv(args.export_product)
            else:
                file = exporter.export_product_to_json(args.export_product)
            print(f"Exported to: {file}")
        except Exception as e:
            print(f"Error: {e}")
    
    elif args.export_all:
        try:
            if args.format == 'excel':
                file = exporter.export_all_to_csv()
            elif args.format == 'json':
                file = exporter.export_all_to_json()
            else:
                file = exporter.export_all_to_csv()
            print(f"Exported to: {file}")
        except Exception as e:
            print(f"Error: {e}")
    
    elif args.backup:
        try:
            file = exporter.backup_database()
            print(f"Backup created: {file}")
        except Exception as e:
            print(f"Error: {e}")
    
    elif args.archive:
        try:
            file = exporter.archive_old_data(args.archive)
            print(f"Archived to: {file}")
        except Exception as e:
            print(f"Error: {e}")
    
    elif args.cleanup:
        count = exporter.cleanup_old_backups(args.cleanup)
        print(f"Deleted {count} old backup files")
    
    elif args.summary:
        summary = exporter.get_export_summary()
        print(json.dumps(summary, indent=2))
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()





