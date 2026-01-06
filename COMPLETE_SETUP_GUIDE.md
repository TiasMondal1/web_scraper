# 🚀 Complete Setup Guide - Price Tracker Pro

**From Zero to Production in 30 Minutes**

This guide will take you from a fresh clone to a fully running Price Tracker Pro SaaS application.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (5 Minutes)](#quick-start-5-minutes)
3. [Detailed Setup](#detailed-setup)
4. [Configuration](#configuration)
5. [Running the Application](#running-the-application)
6. [Testing](#testing)
7. [Production Deployment](#production-deployment)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

Install these before starting:

1. **Python 3.11+**
   ```bash
   python --version  # Should be 3.11 or higher
   ```

2. **Docker & Docker Compose**
   ```bash
   docker --version
   docker-compose --version
   ```

3. **Node.js 18+** (for frontend)
   ```bash
   node --version  # Should be 18 or higher
   npm --version
   ```

4. **Git**
   ```bash
   git --version
   ```

### Required Accounts (Can set up later)

- **Razorpay** (Payment gateway) - https://razorpay.com
- **SendGrid** (Email service) - https://sendgrid.com
- **GitHub** (For CI/CD) - https://github.com

---

## Quick Start (5 Minutes)

For the fastest way to get started locally:

### 1. Clone & Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd web_scraper

# Run automated setup
./scripts/setup.sh
```

The setup script will:
- Create virtual environment
- Install all dependencies
- Generate secret keys
- Create `.env` file
- Build Docker images
- Initialize database
- Start all services

### 2. Access the Application

```bash
# Application is now running at:
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Frontend: http://localhost:3000 (if started)
```

That's it! Skip to [Testing](#testing) section.

---

## Detailed Setup

If you prefer manual setup or the script doesn't work:

### Step 1: Environment Setup

#### 1.1 Create Virtual Environment (Python)

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

#### 1.2 Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements_saas.txt
```

#### 1.3 Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

---

### Step 2: Configuration

#### 2.1 Create Environment File

```bash
cp env.production.example .env
```

#### 2.2 Generate Secret Key

```bash
# Generate a secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output and update `.env`:

```env
SECRET_KEY=<paste-generated-key-here>
```

#### 2.3 Configure Environment Variables

Edit `.env` file with your settings:

```env
# Application
APP_NAME=Price Tracker Pro
DEBUG=True  # Set to False in production

# Database (for local Docker)
DATABASE_URL=postgresql://price_tracker:changeme@localhost:5432/price_tracker_saas

# Security
SECRET_KEY=<your-generated-secret-key>

# Email (Get from SendGrid)
SENDGRID_API_KEY=  # Leave empty for now, will add later
FROM_EMAIL=noreply@yourdomain.com

# Payment (Get from Razorpay)
RAZORPAY_KEY_ID=  # Leave empty for now
RAZORPAY_KEY_SECRET=  # Leave empty for now

# Redis
REDIS_URL=redis://localhost:6379/0
```

---

### Step 3: Start Services

#### 3.1 Start Docker Services

```bash
# Start PostgreSQL and Redis
docker-compose -f docker-compose.saas.yml up -d db redis

# Wait for services to be ready (about 10 seconds)
sleep 10
```

#### 3.2 Initialize Database

```bash
# Create database tables
python -c "from app.database import init_db; init_db()"
```

Or run the SQL schema directly:

```bash
# If you have psql installed
docker-compose -f docker-compose.saas.yml exec db psql -U price_tracker -d price_tracker_saas -f saas_database_schema.sql
```

#### 3.3 Start Application Services

```bash
# Start all services (web, celery workers, celery beat)
docker-compose -f docker-compose.saas.yml up -d
```

Or start individually for development:

```bash
# Terminal 1: Web server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Celery worker
celery -A app.tasks:celery_app worker --loglevel=info

# Terminal 3: Celery beat (scheduler)
celery -A app.tasks:celery_app beat --loglevel=info
```

#### 3.4 Start Frontend (Optional)

```bash
cd frontend
npm run dev
# Frontend will start at http://localhost:3000
```

---

## Configuration

### Getting API Keys

#### SendGrid (Email Service)

1. Sign up at https://sendgrid.com (Free tier: 100 emails/day)
2. Go to Settings → API Keys
3. Create API Key with "Mail Send" permission
4. Copy the key and add to `.env`:
   ```env
   SENDGRID_API_KEY=SG.xxxxxxxxxxxxx
   ```
5. Verify sender email:
   - Go to Settings → Sender Authentication
   - Verify your email address

#### Razorpay (Payment Gateway)

1. Sign up at https://razorpay.com
2. For testing:
   - Use test mode keys from Dashboard
   - No KYC required for testing
3. Get keys:
   - Go to Settings → API Keys
   - Generate Test Keys
4. Add to `.env`:
   ```env
   RAZORPAY_KEY_ID=rzp_test_xxxxx
   RAZORPAY_KEY_SECRET=xxxxxxxxxxxxx
   ```
5. Set up webhook:
   - Go to Settings → Webhooks
   - Add webhook URL: `http://your-domain.com/api/payments/webhook`
   - Select events: payment.captured, payment.failed, subscription.charged
   - Copy webhook secret and add to `.env`:
     ```env
     RAZORPAY_WEBHOOK_SECRET=xxxxxxxxxxxxx
     ```

---

## Running the Application

### Verify Everything is Running

```bash
# Check running containers
docker-compose -f docker-compose.saas.yml ps

# Should show:
# - db (PostgreSQL)
# - redis
# - web (FastAPI)
# - celery_worker
# - celery_beat
# - nginx (optional)
```

### Access Points

1. **API Documentation**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

2. **API Endpoints**
   - Health Check: http://localhost:8000/health
   - Base URL: http://localhost:8000/api

3. **Frontend** (if started)
   - http://localhost:3000

4. **Monitoring** (if started)
   - Grafana: http://localhost:3001 (admin/admin)
   - Prometheus: http://localhost:9090

### View Logs

```bash
# All services
docker-compose -f docker-compose.saas.yml logs -f

# Specific service
docker-compose -f docker-compose.saas.yml logs -f web
docker-compose -f docker-compose.saas.yml logs -f celery_worker

# Application logs (if running locally)
tail -f logs/app.log
```

---

## Testing

### 1. Test API with Swagger UI

1. Open http://localhost:8000/docs
2. Click on "Authorize" button
3. Test the endpoints:

#### Register a User
```json
POST /api/auth/register
{
  "email": "test@example.com",
  "password": "testpass123",
  "full_name": "Test User"
}
```

#### Login
```json
POST /api/auth/login
{
  "email": "test@example.com",
  "password": "testpass123"
}
```

Copy the `access_token` from response.

#### Track a Product
```json
POST /api/products/track
Headers: Authorization: Bearer <your-token>
{
  "url": "https://www.amazon.in/product-url",
  "target_price": 25000,
  "alert_enabled": true
}
```

### 2. Run Automated Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html
```

### 3. Test Background Tasks

```bash
# Trigger a manual price scrape
docker-compose -f docker-compose.saas.yml exec celery_worker \
  celery -A app.tasks:celery_app call app.tasks.scrape_all_products_task

# Check Celery logs
docker-compose -f docker-compose.saas.yml logs -f celery_worker
```

### 4. Test Email Delivery

```bash
# Send a test email (requires SendGrid configured)
python -c "
from app.utils.email import send_welcome_email
send_welcome_email('your-email@example.com', 'Test User')
"
```

---

## Production Deployment

### Option 1: Railway (Easiest)

1. **Sign up** at https://railway.app
2. **Connect GitHub** repository
3. **Add services**:
   - PostgreSQL (from marketplace)
   - Redis (from marketplace)
4. **Deploy** from GitHub
5. **Set environment variables** in Railway dashboard
6. **Configure domain** in settings

Railway handles SSL, scaling, and monitoring automatically.

**Cost**: ~$5-20/month

### Option 2: DigitalOcean (Recommended)

1. **Create Droplet** (Ubuntu 22.04, $12/month)
2. **SSH into server**
3. **Run deployment**:
   ```bash
   # On your server
   git clone <your-repo>
   cd web_scraper
   
   # Copy and edit environment
   cp env.production.example .env
   nano .env
   
   # Deploy
   ./scripts/deploy.sh production
   ```

See `DEPLOYMENT_GUIDE.md` for detailed instructions.

### Option 3: AWS/GCP

See `DEPLOYMENT_GUIDE.md` for cloud platform deployment.

---

## Monitoring

### Start Monitoring Stack

```bash
# Start Prometheus, Grafana, Loki
docker-compose -f docker-compose.monitoring.yml up -d

# Access Grafana
open http://localhost:3001
# Login: admin/admin

# Import dashboards
# - Dashboard ID 1860: Node Exporter
# - Dashboard ID 7589: PostgreSQL
# - Dashboard ID 11835: Redis
```

See `MONITORING_GUIDE.md` for detailed setup.

---

## Troubleshooting

### Common Issues

#### 1. Port Already in Use

```bash
# Find process using port 8000
# Windows:
netstat -ano | findstr :8000
# Mac/Linux:
lsof -i :8000

# Kill the process or change port in docker-compose.yml
```

#### 2. Database Connection Error

```bash
# Check if PostgreSQL is running
docker-compose -f docker-compose.saas.yml ps db

# Check database logs
docker-compose -f docker-compose.saas.yml logs db

# Restart database
docker-compose -f docker-compose.saas.yml restart db
```

#### 3. Redis Connection Error

```bash
# Check if Redis is running
docker-compose -f docker-compose.saas.yml ps redis

# Test Redis connection
docker-compose -f docker-compose.saas.yml exec redis redis-cli ping
# Should return: PONG

# Restart Redis
docker-compose -f docker-compose.saas.yml restart redis
```

#### 4. Celery Workers Not Processing Tasks

```bash
# Check Celery worker status
docker-compose -f docker-compose.saas.yml logs celery_worker

# Check if Redis is accessible
docker-compose -f docker-compose.saas.yml exec celery_worker \
  python -c "import redis; r=redis.Redis(host='redis'); print(r.ping())"

# Restart Celery
docker-compose -f docker-compose.saas.yml restart celery_worker celery_beat
```

#### 5. Import Errors

```bash
# Reinstall dependencies
pip install -r requirements_saas.txt --force-reinstall

# Or rebuild Docker images
docker-compose -f docker-compose.saas.yml build --no-cache
```

#### 6. Frontend Not Starting

```bash
cd frontend

# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Start dev server
npm run dev
```

---

## Quick Reference

### Essential Commands

```bash
# Start everything
docker-compose -f docker-compose.saas.yml up -d

# Stop everything
docker-compose -f docker-compose.saas.yml down

# Restart a service
docker-compose -f docker-compose.saas.yml restart web

# View logs
docker-compose -f docker-compose.saas.yml logs -f web

# Run database backup
./scripts/backup.sh

# Deploy to production
./scripts/deploy.sh production

# Run tests
pytest tests/ -v

# Start frontend
cd frontend && npm run dev
```

### URLs

| Service | URL |
|---------|-----|
| API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Frontend | http://localhost:3000 |
| Grafana | http://localhost:3001 |
| Prometheus | http://localhost:9090 |

### Default Credentials

| Service | Username | Password |
|---------|----------|----------|
| Grafana | admin | admin |
| PostgreSQL | price_tracker | changeme |

---

## Next Steps

1. ✅ **Verify Setup**: Test all endpoints at http://localhost:8000/docs
2. 📧 **Configure Email**: Add SendGrid API key
3. 💳 **Configure Payments**: Add Razorpay keys
4. 🎨 **Complete Frontend**: Build remaining pages (optional)
5. 🚀 **Deploy**: Choose deployment platform
6. 🧪 **Beta Test**: Invite 10-50 users
7. 📣 **Launch**: Product Hunt submission

---

## Support & Resources

**Documentation:**
- API Documentation: `API_DOCUMENTATION.md`
- Deployment Guide: `DEPLOYMENT_GUIDE.md`
- Monitoring Guide: `MONITORING_GUIDE.md`
- Celery Setup: `CELERY_SETUP.md`
- TODO List: `TODO.md`

**Community:**
- GitHub Issues: Report bugs
- Discussions: Ask questions

**Need Help?**
- Check `TROUBLESHOOTING.md`
- Review logs: `docker-compose logs`
- Check health endpoint: `/health`

---

## Congratulations! 🎉

Your Price Tracker Pro SaaS is now running!

**You now have:**
- ✅ A production-ready backend API
- ✅ Automated background tasks
- ✅ Payment processing
- ✅ Admin dashboard
- ✅ CI/CD pipeline
- ✅ Monitoring setup
- ✅ Complete documentation

**Ready to get your first customers!** 🚀

---

*Setup Guide Version: 1.0*  
*Last Updated: January 2026*
