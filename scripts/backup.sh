#!/bin/bash
# Backup script for Price Tracker Pro
# Usage: ./scripts/backup.sh

set -e

BACKUP_DIR="backups"
DATE=$(date +%Y%m%d_%H%M%S)

echo "📦 Starting backup..."

# Create backup directory if not exists
mkdir -p "$BACKUP_DIR"

# Backup database
echo "Backing up database..."
docker-compose -f docker-compose.saas.yml exec -T db \
    pg_dump -U price_tracker price_tracker_saas | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

echo "✓ Database backed up: $BACKUP_DIR/db_$DATE.sql.gz"

# Backup uploads (if any)
if [ -d "uploads" ]; then
    echo "Backing up uploads..."
    tar -czf "$BACKUP_DIR/uploads_$DATE.tar.gz" uploads/
    echo "✓ Uploads backed up: $BACKUP_DIR/uploads_$DATE.tar.gz"
fi

# Backup .env file
if [ -f ".env" ]; then
    echo "Backing up environment file..."
    cp .env "$BACKUP_DIR/env_$DATE"
    echo "✓ Environment backed up: $BACKUP_DIR/env_$DATE"
fi

# Calculate sizes
DB_SIZE=$(du -h "$BACKUP_DIR/db_$DATE.sql.gz" | cut -f1)
echo ""
echo "✅ Backup complete!"
echo "Database backup size: $DB_SIZE"
echo "Location: $BACKUP_DIR/"

# Clean old backups (keep last 30 days)
echo ""
echo "Cleaning old backups (keeping last 30 days)..."
find "$BACKUP_DIR" -name "*.gz" -mtime +30 -delete
find "$BACKUP_DIR" -name "env_*" -mtime +30 -delete
echo "✓ Cleanup complete"
