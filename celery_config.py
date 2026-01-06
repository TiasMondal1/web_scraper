"""
Celery configuration and beat schedule
Run this to start Celery worker and beat scheduler
"""
from app.tasks import celery_app
from celery.schedules import crontab

# Configure Celery Beat schedule
celery_app.conf.beat_schedule = {
    # Scrape all products daily at 9 AM
    'scrape-all-products-daily': {
        'task': 'scrape_all_products',
        'schedule': crontab(hour=9, minute=0),  # 9 AM UTC
    },
    
    # Send pending alerts every 15 minutes
    'send-pending-alerts': {
        'task': 'send_all_pending_alerts',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
    
    # Update usage stats daily at midnight
    'update-usage-stats': {
        'task': 'update_usage_stats',
        'schedule': crontab(hour=0, minute=0),  # Midnight UTC
    },
    
    # Cleanup old data weekly on Sunday at 2 AM
    'cleanup-old-data': {
        'task': 'cleanup_old_data',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),  # Sunday 2 AM
    },
}

# Timezone
celery_app.conf.timezone = 'UTC'

if __name__ == '__main__':
    celery_app.start()
