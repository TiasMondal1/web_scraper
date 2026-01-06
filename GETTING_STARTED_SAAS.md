# 🚀 Getting Started with SaaS Development

## What We've Built So Far

You now have a production-ready FastAPI application with:

✅ **User Authentication System**
- User registration with email verification
- Login with JWT tokens
- Token refresh mechanism
- Password hashing with bcrypt

✅ **Multi-Tenancy Database Schema**
- Users and subscriptions
- Product tracking per user
- Usage limits and quotas
- Price history tracking

✅ **Product Tracking API**
- Add products to track
- Get user's tracked products
- Update tracking settings
- View price history
- Stop tracking products

✅ **Subscription System**
- 4 tiers: Free, Basic, Pro, Enterprise
- Usage limits per plan
- Automatic plan enforcement

✅ **Core Infrastructure**
- FastAPI with async support
- SQLAlchemy ORM
- Pydantic validation
- CORS configuration
- Error handling

---

## Step 1: Set Up Local Development Environment

### 1.1 Install PostgreSQL

**macOS:**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### 1.2 Create Database

```bash
# Access PostgreSQL
psql postgres

# Create database
CREATE DATABASE price_tracker_saas;

# Create user (optional)
CREATE USER price_tracker WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE price_tracker_saas TO price_tracker;

# Exit
\q
```

### 1.3 Install Redis (for caching & celery)

**macOS:**
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt install redis-server
sudo systemctl start redis
```

### 1.4 Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv_saas

# Activate it
source venv_saas/bin/activate  # On macOS/Linux
# OR
venv_saas\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements_saas.txt
```

### 1.5 Configure Environment Variables

```bash
# Copy example environment file
cp env.example .env

# Edit .env with your settings
nano .env  # or use your favorite editor
```

**Important settings to change:**
- `SECRET_KEY`: Generate a secure key
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
- `DATABASE_URL`: Your PostgreSQL connection string
- `DEBUG`: Set to `False` in production

---

## Step 2: Initialize Database

### 2.1 Create Database Tables

The app will automatically create tables on first run, but you can also use SQL:

```bash
# Run the schema SQL file
psql price_tracker_saas < saas_database_schema.sql
```

### 2.2 Or Use Alembic (Recommended for Production)

```bash
# Initialize alembic
alembic init alembic

# Create first migration
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head
```

---

## Step 3: Run the Application

### 3.1 Start the API Server

```bash
# Development mode (with auto-reload)
cd /Users/tiasmondal166/card_scraper
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Or run directly:**
```bash
python app/main.py
```

### 3.2 Access the API

- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

## Step 4: Test the API

### 4.1 Register a User

```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepassword123",
    "full_name": "Test User"
  }'
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### 4.2 Login

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepassword123"
  }'
```

### 4.3 Get Current User (with token)

```bash
curl -X GET "http://localhost:8000/api/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4.4 Track a Product

```bash
curl -X POST "http://localhost:8000/api/products/track" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.amazon.in/product-url",
    "target_price": 25000,
    "alert_enabled": true
  }'
```

### 4.5 Get My Products

```bash
curl -X GET "http://localhost:8000/api/products/my" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## Step 5: Interactive API Testing

Visit http://localhost:8000/docs for interactive Swagger UI where you can:

1. Click **"Authorize"** button
2. Enter: `Bearer YOUR_ACCESS_TOKEN`
3. Click **"Authorize"**
4. Now you can test all endpoints interactively!

---

## Project Structure

```
card_scraper/
├── app/
│   ├── __init__.py
│   ├── main.py              # Main FastAPI app
│   ├── config.py            # Configuration
│   ├── database.py          # Database connection
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── auth.py              # Authentication utilities
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── products.py      # Product endpoints
│   │   ├── subscriptions.py # Subscription endpoints (TODO)
│   │   └── dashboard.py     # Dashboard endpoints (TODO)
│   └── utils/
│       ├── __init__.py
│       ├── scraper.py       # Scraping utilities
│       └── limits.py        # Usage limits checking
├── requirements_saas.txt    # Python dependencies
├── env.example              # Environment variables template
└── saas_database_schema.sql # Database schema
```

---

## Next Steps

### Immediate (This Week):
1. ✅ Test all authentication endpoints
2. ✅ Test product tracking
3. 🔨 Add subscription management endpoints
4. 🔨 Add Razorpay payment integration
5. 🔨 Add dashboard endpoints
6. 🔨 Set up Celery for background tasks

### Short-term (Next Week):
1. 🔨 Add email notifications
2. 🔨 Create admin panel
3. 🔨 Add API rate limiting
4. 🔨 Write tests
5. 🔨 Deploy to Railway/DigitalOcean

### Medium-term (Next Month):
1. 🔨 Build frontend (React/Vue)
2. 🔨 Add more notification channels (WhatsApp, Telegram)
3. 🔨 Implement ML price predictions
4. 🔨 Create mobile apps
5. 🔨 Launch on Product Hunt

---

## Common Issues & Solutions

### Issue: "ModuleNotFoundError: No module named 'app'"

**Solution:** Make sure you're running from the project root:
```bash
cd /Users/tiasmondal166/card_scraper
python -m uvicorn app.main:app --reload
```

### Issue: "Connection refused" to PostgreSQL

**Solution:** Check if PostgreSQL is running:
```bash
brew services list  # macOS
sudo systemctl status postgresql  # Linux
```

### Issue: "could not connect to server: Connection refused"

**Solution:** Update DATABASE_URL in `.env`:
```
DATABASE_URL=postgresql://localhost/price_tracker_saas
```

### Issue: Import errors for new packages

**Solution:** Reinstall requirements:
```bash
pip install -r requirements_saas.txt
```

---

## Development Workflow

### 1. Make Changes
Edit files in `app/` directory

### 2. Test Locally
The server auto-reloads when you save files (with `--reload` flag)

### 3. Test API
Use http://localhost:8000/docs or curl

### 4. Check Logs
Terminal shows all logs and errors

### 5. Commit Changes
```bash
git add .
git commit -m "Added feature X"
```

---

## Environment-Specific Configurations

### Development (.env)
```
DEBUG=True
DATABASE_URL=postgresql://localhost/price_tracker_saas
```

### Production
```
DEBUG=False
DATABASE_URL=postgresql://user:pass@prod-host:5432/price_tracker_saas
SECRET_KEY=<strong-random-key>
SENDGRID_API_KEY=<your-key>
RAZORPAY_KEY_ID=rzp_live_xxxxx
```

---

## Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com
- **SQLAlchemy Tutorial**: https://docs.sqlalchemy.org/en/20/tutorial/
- **Pydantic Docs**: https://docs.pydantic.dev
- **Razorpay Docs**: https://razorpay.com/docs/
- **PostgreSQL Docs**: https://www.postgresql.org/docs/

---

## Support & Help

If you encounter issues:

1. Check the terminal logs
2. Verify all services are running (PostgreSQL, Redis)
3. Check `.env` configuration
4. Try the interactive docs at `/docs`
5. Search FastAPI documentation
6. Ask on Stack Overflow with tag `fastapi`

---

## Ready to Continue?

Your FastAPI backend is now ready! Next steps:

1. **Test all endpoints** using the interactive docs
2. **Add subscription routes** (see TODO list)
3. **Integrate Razorpay payments**
4. **Build a simple frontend** or use Postman/Thunder Client
5. **Deploy to production** when ready

**You're making great progress! 🚀**

