# 🚀 Production Deployment Guide

Complete guide to deploying Price Tracker Pro SaaS to production.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Docker Deployment](#local-docker-deployment)
3. [Cloud Deployment Options](#cloud-deployment-options)
4. [Environment Configuration](#environment-configuration)
5. [Database Setup](#database-setup)
6. [SSL/HTTPS Setup](#sslhttps-setup)
7. [Monitoring & Logging](#monitoring--logging)
8. [Backup & Recovery](#backup--recovery)
9. [Scaling](#scaling)

---

## Prerequisites

### Required Services

1. **Domain Name** - Purchase from Namecheap, Google Domains, etc.
2. **SSL Certificate** - Use Let's Encrypt (free) or CloudFlare
3. **Email Service** - SendGrid account (free tier available)
4. **Payment Gateway** - Razorpay account (Indian payments)
5. **Cloud Provider** - Choose one:
   - Railway.app (easiest)
   - DigitalOcean (good balance)
   - AWS (most powerful)
   - Google Cloud Platform

### Required Tools

```bash
# Install Docker & Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

---

## Local Docker Deployment

### 1. Prepare Environment

```bash
# Clone repository
git clone https://github.com/yourusername/price-tracker-pro.git
cd price-tracker-pro

# Copy environment file
cp env.production.example .env

# Edit .env with your actual values
nano .env
```

### 2. Build and Run

```bash
# Build containers
docker-compose -f docker-compose.saas.yml build

# Start services
docker-compose -f docker-compose.saas.yml up -d

# Check status
docker-compose -f docker-compose.saas.yml ps

# View logs
docker-compose -f docker-compose.saas.yml logs -f web
```

### 3. Initialize Database

```bash
# Run database migrations
docker-compose -f docker-compose.saas.yml exec web python -c "from app.database import init_db; init_db()"

# Verify tables created
docker-compose -f docker-compose.saas.yml exec db psql -U price_tracker -d price_tracker_saas -c "\dt"
```

### 4. Access Application

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## Cloud Deployment Options

### Option 1: Railway.app (Easiest)

Railway is the simplest deployment option with automatic SSL.

**Steps:**

1. **Sign up** at https://railway.app
2. **Create new project** → Deploy from GitHub
3. **Connect repository** and select branch
4. **Add services**:
   - PostgreSQL (from marketplace)
   - Redis (from marketplace)
5. **Set environment variables**:
   - Copy from `env.production.example`
   - Railway auto-generates DATABASE_URL
6. **Deploy**: Railway auto-deploys on git push

**Cost:** ~$5-20/month depending on usage

---

### Option 2: DigitalOcean (Recommended)

Best balance of cost, performance, and ease of use.

#### 2.1 Create Droplet

```bash
# Create Ubuntu 22.04 droplet (recommended: $12/month, 2GB RAM)
# Or use App Platform for managed deployment
```

#### 2.2 Server Setup

```bash
# SSH into server
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install git
apt install git -y
```

#### 2.3 Deploy Application

```bash
# Clone repository
cd /opt
git clone https://github.com/yourusername/price-tracker-pro.git
cd price-tracker-pro

# Set up environment
cp env.production.example .env
nano .env  # Edit with production values

# Start services
docker-compose -f docker-compose.saas.yml up -d

# Set up auto-restart
docker update --restart=always $(docker ps -aq)
```

#### 2.4 Set Up Nginx & SSL

```bash
# Install Certbot
apt install certbot python3-certbot-nginx -y

# Get SSL certificate
certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Copy certificates to project
mkdir -p ssl
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/cert.pem
cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/key.pem

# Restart nginx container
docker-compose -f docker-compose.saas.yml restart nginx
```

**Cost:** ~$12-24/month

---

### Option 3: AWS (Most Powerful)

Best for scaling and advanced features.

#### Services to Use:

- **ECS** (Elastic Container Service) - Run Docker containers
- **RDS** (PostgreSQL) - Managed database
- **ElastiCache** (Redis) - Managed Redis
- **ALB** (Application Load Balancer) - Load balancing & SSL
- **ECR** (Container Registry) - Store Docker images
- **CloudWatch** - Logging & monitoring

#### Quick Deploy with ECS:

1. Push Docker image to ECR
2. Create RDS PostgreSQL instance
3. Create ElastiCache Redis cluster
4. Create ECS Task Definition
5. Create ECS Service with ALB
6. Configure SSL certificate in ALB

**Cost:** ~$50-150/month (with reserved instances)

---

### Option 4: Google Cloud Platform

Similar to AWS, good for auto-scaling.

Use:
- **Cloud Run** - Serverless containers
- **Cloud SQL** - Managed PostgreSQL
- **Memorystore** - Managed Redis

**Cost:** ~$30-100/month

---

## Environment Configuration

### Critical Environment Variables

```bash
# Generate secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Set in .env:
SECRET_KEY=<generated-key>

# Database (use managed database URL from cloud provider)
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Redis (use managed Redis URL from cloud provider)
REDIS_URL=redis://host:6379/0

# Payment Gateway
RAZORPAY_KEY_ID=rzp_live_YOUR_KEY
RAZORPAY_KEY_SECRET=YOUR_SECRET

# Email Service
SENDGRID_API_KEY=SG.YOUR_API_KEY
```

### SendGrid Setup

1. Sign up at https://sendgrid.com
2. Create API Key with "Mail Send" permission
3. Verify sender email
4. Add API key to environment

### Razorpay Setup

1. Sign up at https://razorpay.com
2. Complete KYC verification
3. Get API keys from Dashboard
4. Set up webhook: `https://your-domain.com/api/payments/webhook`

---

## Database Setup

### Database Migrations with Alembic

```bash
# Initialize Alembic
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

### Database Backup

```bash
# Manual backup
docker-compose -f docker-compose.saas.yml exec db pg_dump -U price_tracker price_tracker_saas > backup.sql

# Automated daily backup (cron)
0 2 * * * cd /opt/price-tracker-pro && docker-compose exec -T db pg_dump -U price_tracker price_tracker_saas | gzip > /backups/db-$(date +\%Y\%m\%d).sql.gz
```

---

## SSL/HTTPS Setup

### Let's Encrypt (Free)

```bash
# Install Certbot
apt install certbot python3-certbot-nginx

# Get certificate
certbot certonly --standalone -d your-domain.com

# Auto-renewal (already set up by certbot)
certbot renew --dry-run
```

### CloudFlare (Recommended)

1. Add domain to CloudFlare
2. Update nameservers
3. Enable "Full (strict)" SSL mode
4. Enable "Always Use HTTPS"
5. Set up page rules for caching

**Benefits:**
- Free SSL
- DDoS protection
- CDN
- WAF

---

## Monitoring & Logging

### Application Logs

```bash
# View logs
docker-compose logs -f web
docker-compose logs -f celery_worker

# Save logs to file
docker-compose logs web > logs/web.log
```

### Sentry Setup (Error Tracking)

1. Sign up at https://sentry.io
2. Create project
3. Get DSN
4. Add to environment:

```bash
SENTRY_DSN=https://your-dsn@sentry.io/project-id
```

### Prometheus + Grafana (Advanced)

Add to docker-compose.saas.yml:

```yaml
prometheus:
  image: prom/prometheus
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
  ports:
    - "9090:9090"

grafana:
  image: grafana/grafana
  ports:
    - "3000:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=admin
```

---

## Backup & Recovery

### Automated Backup Script

Create `backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup database
docker-compose exec -T db pg_dump -U price_tracker price_tracker_saas | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# Backup uploads (if any)
tar -czf "$BACKUP_DIR/uploads_$DATE.tar.gz" uploads/

# Keep only last 30 days
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

Schedule with cron:
```bash
0 2 * * * /opt/price-tracker-pro/backup.sh >> /var/log/backup.log 2>&1
```

---

## Scaling

### Horizontal Scaling

1. **Add more web servers** behind load balancer
2. **Use managed database** (RDS, Cloud SQL)
3. **Use managed Redis** (ElastiCache, Memorystore)
4. **Add more Celery workers** for background tasks

### Vertical Scaling

- Increase droplet/instance size
- Add more CPU/RAM
- Use SSD storage

### Database Scaling

- Enable read replicas for queries
- Use connection pooling (PgBouncer)
- Add database indexes
- Archive old data

---

## Health Checks & Monitoring

### Setup Health Check Endpoint

Already available at `/health`

### Uptime Monitoring

Use services like:
- **UptimeRobot** (free)
- **Pingdom**
- **StatusCake**

---

## Post-Deployment Checklist

- [ ] Domain DNS configured
- [ ] SSL certificate installed
- [ ] Environment variables set
- [ ] Database initialized
- [ ] SendGrid configured & tested
- [ ] Razorpay configured & tested
- [ ] Celery worker running
- [ ] Celery beat running
- [ ] Nginx/Load balancer configured
- [ ] Firewall rules set (only 80, 443, 22)
- [ ] Backups automated
- [ ] Monitoring set up
- [ ] Error tracking (Sentry) configured
- [ ] Rate limiting tested
- [ ] API endpoints tested
- [ ] Email notifications tested
- [ ] Payment flow tested
- [ ] Documentation updated

---

## Troubleshooting

### Application won't start

```bash
# Check logs
docker-compose logs web

# Common issues:
# 1. Database connection - verify DATABASE_URL
# 2. Redis connection - verify REDIS_URL
# 3. Port conflicts - change ports in docker-compose
```

### Database connection errors

```bash
# Test database connection
docker-compose exec db psql -U price_tracker -d price_tracker_saas

# Reset database
docker-compose down -v
docker-compose up -d
```

### Celery tasks not running

```bash
# Check Redis
docker-compose exec redis redis-cli ping

# Check Celery worker
docker-compose logs celery_worker

# Restart Celery
docker-compose restart celery_worker celery_beat
```

---

## Support & Resources

- **Documentation**: https://fastapi.tiangolo.com
- **Community**: Join our Discord/Slack
- **Issues**: GitHub Issues
- **Email**: support@your-domain.com

---

**Ready to deploy? Start with Railway for fastest setup, then migrate to DigitalOcean/AWS when you need more control.**
