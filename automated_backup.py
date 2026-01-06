"""
Automated Backup Script
Can be scheduled to run periodically for database backups
"""
import os
import sys
from datetime import datetime
from data_export import DataExporter

def run_automated_backup():
    """Run automated backup"""
    exporter = DataExporter()
    
    try:
        # Create backup
        backup_file = exporter.backup_database()
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Backup created: {backup_file}")
        
        # Cleanup old backups (keep last 30 days)
        deleted_count = exporter.cleanup_old_backups(days_to_keep=30)
        if deleted_count > 0:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Cleaned up {deleted_count} old backups")
        
        return True
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Backup failed: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    success = run_automated_backup()
    sys.exit(0 if success else 1)





