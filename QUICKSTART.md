# Quick Start Guide

## Initial Setup

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: Some dependencies are optional:
- `selenium` - Only needed if you want to use Selenium for JavaScript-heavy sites
- `scikit-learn`, `scipy` - Only needed for advanced ML analytics
- `win10toast` - Only needed for Windows desktop notifications

### Step 2: Configure Products

Edit `products.json` to add products you want to track:

```json
{
    "products": [
        {
            "name": "Your Product Name",
            "url": "https://amazon.in/your-product-url",
            "alert_threshold": 10
        }
    ]
}
```

The `alert_threshold` is optional - it's the percentage drop that triggers alerts (default: 10%).

### Step 3: (Optional) Configure Alerts

Edit `alert_config.json` to set up email/Telegram alerts (optional):

```json
{
    "email": {
        "enabled": false,
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "sender_email": "your-email@gmail.com",
        "sender_password": "your-app-password",
        "recipient_email": "recipient@example.com"
    },
    "telegram": {
        "enabled": false,
        "bot_token": "your-bot-token",
        "chat_id": "your-chat-id"
    },
    "desktop": {
        "enabled": true
    },
    "default_alert_threshold": 10
}
```

## Running the Application

### Option 1: Basic Usage (One-time Run)

Run the scraper once to track all products:

```bash
python card_scraper.py
```

**What happens:**
1. Loads products from `products.json`
2. Fetches current prices from each product URL
3. Saves prices to SQLite database (`price_history.db`)
4. Sends alerts if price drops meet threshold
5. Generates analysis reports in `analysis/` folder

### Option 2: Using CLI (Recommended)

The CLI provides more control:

```bash
# Track prices (with analysis)
python cli.py track

# Track prices (without analysis)
python cli.py track --no-analysis

# View all products
python cli.py list

# Export data
python cli.py export --all --format csv

# Backup database
python cli.py backup
```

### Option 3: Scheduled/Automated

#### Windows Task Scheduler

Run as Administrator:
```powershell
.\setup_windows_scheduler.ps1
```

This sets up daily price checks at 9 AM.

#### Linux/Mac Cron

```bash
chmod +x setup_cron.sh
./setup_cron.sh
```

#### Manual Scheduling

```bash
# Run every 6 hours
python scheduler.py --mode interval --interval 6

# Run daily at 9 AM
python scheduler.py --mode daily --hour 9

# Run hourly
python scheduler.py --mode hourly

# Background service
python run_background_service.py --interval 6
```

### Option 4: Web Dashboard

Start the web interface:

```bash
python web_dashboard.py
```

Then open your browser: http://localhost:5000

**Features:**
- View all tracked products
- See price charts
- Add/remove products
- View statistics

### Option 5: REST API

Start the API server:

```bash
python api.py
```

API runs at: http://localhost:5001

Use it programmatically or with the browser extension.

### Option 6: Docker (All Services)

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Understanding the Process

### What Happens When You Run `python card_scraper.py`?

```
1. Load Configuration
   ├── Reads products.json
   ├── Initializes database (creates price_history.db if needed)
   └── Sets up alert manager

2. For Each Product:
   ├── Scrape Price
   │   ├── Makes HTTP request to product URL
   │   ├── Parses HTML to extract price
   │   └── Returns price value
   │
   ├── Save to Database
   │   ├── Adds/updates product in database
   │   └── Records price with timestamp
   │
   ├── Check Alerts
   │   ├── Compares with previous price
   │   ├── Calculates price drop percentage
   │   └── Sends alerts if threshold met
   │
   └── Wait 5 seconds (to avoid rate limiting)

3. Generate Analysis
   ├── For each product:
   │   ├── Load price history from database
   │   ├── Calculate statistics
   │   ├── Generate charts
   │   └── Create report in analysis/ folder
   │
   └── Done!
```

### Data Flow

```
Products (products.json)
    ↓
Scraper (card_scraper.py)
    ↓
Database (price_history.db)
    ├── Price History Table
    └── Products Table
    ↓
Analysis (price_analysis.py)
    ↓
Reports (analysis/ folder)
    ├── analysis_report.txt
    ├── price_history.png
    └── price_distribution.png
```

### File Structure After Running

```
web_scraper/
├── price_history.db          ← SQLite database (created on first run)
├── products.json             ← Your product list
├── alert_config.json         ← Alert settings (optional)
├── config.json               ← App config (optional)
├── logs/
│   └── price_tracker.log     ← Application logs
├── analysis/
│   └── [Product Name]/
│       ├── analysis_report.txt
│       ├── price_history.png
│       └── price_distribution.png
├── exports/                  ← Export files (if you export)
└── backups/                  ← Database backups (if you backup)
```

## Common Workflows

### Daily Price Tracking

1. **Set up scheduler** (one-time):
   ```bash
   python scheduler.py --mode daily --hour 9
   ```

2. **Let it run automatically** - Prices are checked daily at 9 AM

3. **Check dashboard**: http://localhost:5000

### Manual Price Check

1. **Check prices now**:
   ```bash
   python cli.py track
   ```

2. **View results**:
   ```bash
   python cli.py list
   ```

3. **Export data**:
   ```bash
   python cli.py export --all --format csv
   ```

### Adding New Products

**Method 1: Edit products.json**
- Edit `products.json` file
- Add new product entry
- Run scraper: `python card_scraper.py`

**Method 2: Web Dashboard**
- Start dashboard: `python web_dashboard.py`
- Open http://localhost:5000
- Click "Add Product"
- Enter name and URL

**Method 3: REST API**
```bash
curl -X POST http://localhost:5001/api/products \
  -H "Content-Type: application/json" \
  -d '{"name": "Product Name", "url": "https://example.com/product"}'
```

**Method 4: Browser Extension**
- Install extension from `browser_extension/` folder
- Navigate to product page
- Click extension icon
- Click "Track This Product"

## Troubleshooting

### Database Not Created?
- Run the scraper once - it will create the database automatically
- Or run: `python -c "from database import PriceDatabase; PriceDatabase()"`

### Migration from Excel?
If you have existing Excel data:
```bash
python migrate_excel_to_db.py
```

### Prices Not Fetching?
- Check internet connection
- Verify product URLs are correct
- Check if the website structure changed (scrapers may need updates)
- Enable Selenium for JavaScript-heavy sites: Set `use_selenium: true` in config

### Alerts Not Working?
- Check `alert_config.json` configuration
- For email: Use app password (not regular password) for Gmail
- For Telegram: Get bot token from @BotFather on Telegram
- Desktop notifications: Install `win10toast` package

### Port Already in Use?
- Change port in `config.json` or environment variables
- Or stop the service using the port

## Next Steps

1. **Customize alerts** - Set up email/Telegram notifications
2. **Set up automation** - Configure scheduler for automatic tracking
3. **Explore analytics** - Use advanced analytics features
4. **Set up backups** - Configure automated backups
5. **Deploy** - Use Docker for production deployment

## Getting Help

- Check logs: `logs/price_tracker.log`
- Use CLI help: `python cli.py --help`
- Check configuration: `python cli.py config`

