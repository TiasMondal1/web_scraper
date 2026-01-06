# Celery Background Tasks Setup Guide

## Overview

Celery is used for running background tasks like:
- Daily price scraping for all products
- Sending price alert emails
- Cleaning up old data
- Updating usage statistics

## Prerequisites

1. **Redis** must be running (used as message broker)
   ```bash
   # macOS
   brew install redis
   brew services start redis
   
   # Ubuntu/Debian
   sudo apt install redis-server
   sudo systemctl start redis
   
   # Windows
   # Download from: https://github.com/microsoftarchive/redis/releases
   # Or use WSL
   ```

2. **Environment Variables** in `.env`:
   ```
   CELERY_BROKER_URL=redis://localhost:6379/0
   CELERY_RESULT_BACKEND=redis://localhost:6379/0
   REDIS_URL=redis://localhost:6379/0
   ```

## Running Celery

### 1. Start Celery Worker

The worker processes background tasks:

```bash
# Option 1: Using the script
python run_celery_worker.py

# Option 2: Direct command
celery -A app.tasks:celery_app worker --loglevel=info --concurrency=4
```

### 2. Start Celery Beat (Scheduler)

The beat scheduler runs periodic tasks:

```bash
# Option 1: Using the script
python run_celery_beat.py

# Option 2: Direct command
celery -A app.tasks:celery_app beat --loglevel=info
```

### 3. Run Both Together (Development)

In separate terminals:

```bash
# Terminal 1: Worker
celery -A app.tasks:celery_app worker --loglevel=info

# Terminal 2: Beat
celery -A app.tasks:celery_app beat --loglevel=info
```

## Scheduled Tasks

Tasks are automatically scheduled via `celery_config.py`:

| Task | Schedule | Description |
|------|----------|-------------|
| `scrape_all_products` | Daily at 9 AM UTC | Scrapes prices for all active products |
| `send_all_pending_alerts` | Every 15 minutes | Sends queued price alerts |
| `update_usage_stats` | Daily at midnight UTC | Resets daily usage counters |
| `cleanup_old_data` | Weekly (Sunday 2 AM UTC) | Removes old price history |

## Manual Task Execution

You can also trigger tasks manually:

```python
from app.tasks import scrape_all_products_task, send_price_alert_task

# Scrape all products now
result = scrape_all_products_task.delay()
print(result.get())  # Wait for result

# Send specific alert
send_price_alert_task.delay(alert_id=123)
```

## Monitoring

### Check Worker Status

```bash
celery -A app.tasks:celery_app inspect active
celery -A app.tasks:celery_app inspect scheduled
celery -A app.tasks:celery_app inspect stats
```

### Flower (Web UI for Monitoring)

Install Flower:
```bash
pip install flower
```

Run:
```bash
celery -A app.tasks:celery_app flower
```

Access at: http://localhost:5555

## Production Deployment

### Using Supervisor (Linux)

Create `/etc/supervisor/conf.d/celery.conf`:

```ini
[program:celery_worker]
command=/path/to/venv/bin/celery -A app.tasks:celery_app worker --loglevel=info
directory=/path/to/project
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/celery/worker.log

[program:celery_beat]
command=/path/to/venv/bin/celery -A app.tasks:celery_app beat --loglevel=info
directory=/path/to/project
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/celery/beat.log
```

Reload supervisor:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start celery_worker
sudo supervisorctl start celery_beat
```

### Using systemd (Linux)

Create `/etc/systemd/system/celery-worker.service`:

```ini
[Unit]
Description=Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=www-data
Group=www-data
EnvironmentFile=/path/to/project/.env
WorkingDirectory=/path/to/project
ExecStart=/path/to/venv/bin/celery -A app.tasks:celery_app worker --loglevel=info --detach
ExecStop=/bin/kill -s TERM $MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable celery-worker
sudo systemctl start celery-worker
```

### Docker Compose

Add to `docker-compose.yml`:

```yaml
services:
  celery_worker:
    build: .
    command: celery -A app.tasks:celery_app worker --loglevel=info
    volumes:
      - .:/app
    depends_on:
      - redis
      - db
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379/0

  celery_beat:
    build: .
    command: celery -A app.tasks:celery_app beat --loglevel=info
    volumes:
      - .:/app
    depends_on:
      - redis
      - db
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379/0
```

## Troubleshooting

### Worker not processing tasks

1. Check Redis is running: `redis-cli ping` (should return PONG)
2. Check worker logs for errors
3. Verify task is registered: `celery -A app.tasks:celery_app inspect registered`

### Tasks failing

1. Check database connection
2. Verify environment variables
3. Check logs: `tail -f /var/log/celery/worker.log`

### Beat not scheduling

1. Check beat is running: `ps aux | grep celery`
2. Verify schedule in `celery_config.py`
3. Check beat logs

## Testing

Test tasks manually:

```python
# In Python shell
from app.tasks import scrape_all_products_task
result = scrape_all_products_task.apply()
print(result.result)
```

## Resources

- [Celery Documentation](https://docs.celeryproject.org/)
- [Celery Best Practices](https://docs.celeryproject.org/en/stable/userguide/tasks.html#best-practices)
- [Flower Monitoring](https://flower.readthedocs.io/)
