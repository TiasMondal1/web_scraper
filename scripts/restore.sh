#!/bin/bash
# Restore script for Price Tracker Pro
# Usage: ./scripts/restore.sh <backup_file>

set -e

if [ -z "$1" ]; then
    echo "Usage: ./scripts/restore.sh <backup_file>"
    echo ""
    echo "Available backups:"
    ls -lh backups/*.sql.gz 2>/dev/null || echo "No backups found"
    exit 1
fi

BACKUP_FILE=$1

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "⚠️  WARNING: This will overwrite the current database!"
read -p "Are you sure you want to continue? (yes/no): " -r
echo

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Restore cancelled"
    exit 0
fi

echo "📥 Restoring from backup: $BACKUP_FILE"

# Stop application
echo "Stopping application..."
docker-compose -f docker-compose.saas.yml stop web celery_worker celery_beat

# Restore database
echo "Restoring database..."
gunzip < "$BACKUP_FILE" | docker-compose -f docker-compose.saas.yml exec -T db \
    psql -U price_tracker price_tracker_saas

echo "✓ Database restored"

# Start application
echo "Starting application..."
docker-compose -f docker-compose.saas.yml start web celery_worker celery_beat

echo ""
echo "✅ Restore complete!"
echo "Application is starting up..."
sleep 5
echo "Health check: http://localhost:8000/health"
