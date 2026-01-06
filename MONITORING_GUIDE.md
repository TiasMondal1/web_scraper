# 📊 Monitoring & Observability Guide

Complete guide to monitoring your Price Tracker Pro SaaS application.

## Table of Contents

1. [Overview](#overview)
2. [Metrics with Prometheus](#metrics-with-prometheus)
3. [Visualization with Grafana](#visualization-with-grafana)
4. [Logging with Loki](#logging-with-loki)
5. [Alerts](#alerts)
6. [Application Performance Monitoring](#application-performance-monitoring)

---

## Overview

Our monitoring stack includes:

- **Prometheus** - Metrics collection
- **Grafana** - Visualization dashboards
- **Loki** - Log aggregation
- **Promtail** - Log shipping
- **Exporters** - PostgreSQL, Redis, Node metrics

---

## Quick Start

### 1. Start Monitoring Stack

```bash
# Start monitoring services
docker-compose -f docker-compose.monitoring.yml up -d

# Access services:
# - Grafana: http://localhost:3001 (admin/admin)
# - Prometheus: http://localhost:9090
# - AlertManager: http://localhost:9093
```

### 2. Import Grafana Dashboards

1. Open Grafana at http://localhost:3001
2. Login with admin/admin
3. Go to Dashboards → Import
4. Import these dashboard IDs:
   - **1860** - Node Exporter Full
   - **7589** - PostgreSQL Database
   - **11835** - Redis Dashboard
   - **763** - FastAPI

---

## Metrics with Prometheus

### Application Metrics

FastAPI automatically exposes metrics at `/metrics` endpoint:

```python
# Add to app/main.py
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(...)

# Instrument app
Instrumentator().instrument(app).expose(app)
```

### Custom Metrics

```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
request_count = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint']
)

active_users = Gauge(
    'active_users_total',
    'Number of active users'
)

# Use metrics
@app.get("/api/products")
async def get_products():
    request_count.labels(method='GET', endpoint='/api/products', status='200').inc()
    with request_duration.labels(method='GET', endpoint='/api/products').time():
        # Your code here
        pass
```

### Key Metrics to Monitor

**Application:**
- Request rate (requests/second)
- Error rate (errors/second)
- Request duration (p50, p95, p99)
- Active users
- Database connections

**Business:**
- Signups per day
- Active subscriptions
- Products tracked
- Alerts sent
- Revenue (MRR)

**Infrastructure:**
- CPU usage
- Memory usage
- Disk I/O
- Network I/O

---

## Visualization with Grafana

### Create Custom Dashboard

1. **Create Dashboard**
   - Click "+" → Dashboard
   - Add Panel

2. **Query Metrics**
   ```promql
   # Request rate
   rate(api_requests_total[5m])
   
   # Error rate
   rate(api_requests_total{status=~"5.."}[5m])
   
   # Average response time
   rate(api_request_duration_seconds_sum[5m]) /
   rate(api_request_duration_seconds_count[5m])
   
   # Active users
   active_users_total
   
   # Database connections
   pg_stat_database_numbackends
   ```

3. **Set up Variables**
   - Environment (staging, production)
   - Time range
   - Refresh interval

### Sample Dashboards

**Application Overview:**
- Request rate graph
- Error rate graph
- Response time heatmap
- Active users gauge
- Top endpoints by requests

**Business Metrics:**
- Daily signups
- Active subscriptions
- Products tracked
- Alerts sent
- Revenue trend

**Infrastructure:**
- CPU usage per service
- Memory usage per service
- Disk usage
- Network I/O

---

## Logging with Loki

### Configure Application Logging

```python
# app/utils/logger.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Use in code
logger.info("User logged in", extra={"user_id": 123})
logger.error("Payment failed", extra={"error": str(e)})
```

### Query Logs in Grafana

```logql
# All application logs
{job="fastapi"}

# Error logs only
{job="fastapi"} |= "ERROR"

# Logs for specific user
{job="fastapi"} | json | user_id="123"

# Rate of errors
rate({job="fastapi"} |= "ERROR" [5m])
```

### Structured Logging

```python
import structlog

# Configure structlog
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

# Log with context
logger.info("user_login", user_id=123, ip="1.2.3.4")
logger.error("payment_failed", user_id=123, amount=199, error="card_declined")
```

---

## Alerts

### Define Alert Rules

Create `alerts.yml`:

```yaml
groups:
  - name: application_alerts
    interval: 1m
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: rate(api_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} requests/second"
      
      # Slow response time
      - alert: SlowResponseTime
        expr: histogram_quantile(0.95, rate(api_request_duration_seconds_bucket[5m])) > 1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Slow API response time"
          description: "P95 response time is {{ $value }} seconds"
      
      # Database connection pool full
      - alert: DatabaseConnectionsHigh
        expr: pg_stat_database_numbackends / pg_settings_max_connections > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Database connection pool nearly full"
      
      # Celery queue backed up
      - alert: CeleryQueueBacklog
        expr: celery_queue_length > 100
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Celery queue has backlog"
```

### Configure AlertManager

Create `alertmanager.yml`:

```yaml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'email'

receivers:
  - name: 'email'
    email_configs:
      - to: 'alerts@your-domain.com'
        from: 'prometheus@your-domain.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'your-email@gmail.com'
        auth_password: 'your-app-password'
  
  - name: 'slack'
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK_URL'
        channel: '#alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

---

## Application Performance Monitoring

### Add Sentry for Error Tracking

```python
# app/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="YOUR_SENTRY_DSN",
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,  # 10% of transactions
    environment="production"
)
```

### Track Custom Events

```python
from sentry_sdk import capture_message, capture_exception

# Track events
capture_message("User upgraded to Pro plan", level="info")

# Track exceptions
try:
    process_payment()
except PaymentError as e:
    capture_exception(e)
```

---

## Health Checks

### Implement Health Endpoint

```python
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Comprehensive health check"""
    health = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # Database check
    try:
        db.execute("SELECT 1")
        health["checks"]["database"] = "healthy"
    except Exception as e:
        health["checks"]["database"] = f"unhealthy: {str(e)}"
        health["status"] = "unhealthy"
    
    # Redis check
    try:
        redis_client.ping()
        health["checks"]["redis"] = "healthy"
    except Exception as e:
        health["checks"]["redis"] = f"unhealthy: {str(e)}"
        health["status"] = "degraded"
    
    # Celery check
    try:
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        health["checks"]["celery"] = "healthy" if stats else "no workers"
    except Exception as e:
        health["checks"]["celery"] = f"unhealthy: {str(e)}"
    
    status_code = 200 if health["status"] == "healthy" else 503
    return JSONResponse(content=health, status_code=status_code)
```

---

## Best Practices

1. **Metric Naming**: Use consistent naming (e.g., `app_requests_total`)
2. **Labels**: Keep labels low-cardinality
3. **Retention**: Configure appropriate data retention (e.g., 30 days)
4. **Sampling**: Sample traces in production (10-20%)
5. **Dashboards**: Create role-specific dashboards (dev, ops, business)
6. **Alerts**: Set meaningful thresholds, avoid alert fatigue
7. **Documentation**: Document what each metric means

---

## Monitoring Checklist

- [ ] Prometheus collecting metrics
- [ ] Grafana dashboards configured
- [ ] Loki aggregating logs
- [ ] Alerts configured and tested
- [ ] Health checks implemented
- [ ] Sentry error tracking set up
- [ ] On-call rotation defined
- [ ] Runbooks created for alerts
- [ ] Weekly metrics review scheduled

---

## Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Loki Documentation](https://grafana.com/docs/loki/)
- [FastAPI Metrics](https://github.com/trallnag/prometheus-fastapi-instrumentator)
- [Sentry Python SDK](https://docs.sentry.io/platforms/python/)

---

**With proper monitoring, you can ensure 99.9% uptime and catch issues before users notice!** 📊
