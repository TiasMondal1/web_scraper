# Web Scraper - Price Tracker

A comprehensive price tracking system with web scraping, alerts, analytics, and web interface.

## Features

### ✅ Core Features

1. **Multi-Product Price Tracking** - Track prices from multiple e-commerce sites (Amazon, Flipkart, Snapdeal, Myntra, Nykaa, eBay)
2. **Price History Database** - SQLite database for efficient price storage and retrieval
3. **Price Analysis & Reports** - Statistical analysis with visualizations
4. **Alert System** - Email, Telegram, and desktop notifications for price drops
5. **Web Dashboard** - Flask-based web interface with real-time charts
6. **REST API** - Full API for programmatic access
7. **Scheduler/Automation** - Automated price checking with scheduling
8. **Enhanced Scraping** - Selenium support, proxy rotation, better error handling
9. **Data Export & Backup** - CSV/JSON export and automated backups
10. **Price Comparison** - Compare prices across products and sellers
11. **Advanced Analytics** - ML price prediction, volatility analysis, seasonal trends
12. **Configuration & Logging** - Comprehensive logging and configuration management
13. **Testing** - Unit tests, integration tests, and CI/CD
14. **Docker Deployment** - Containerized deployment with Docker Compose
15. **Browser Extension** - Chrome/Firefox extension for one-click tracking
16. **Additional Features** - Currency conversion, discount tracking, wishlist management

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd web_scraper
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Migrate existing Excel data to database:
```bash
python migrate_excel_to_db.py
```

## Usage

### Basic Usage

Track prices for all products:
```bash
python card_scraper.py
```

### CLI Commands

```bash
# Track prices
python cli.py track

# Export data
python cli.py export --all --format csv
python cli.py export --product "Product Name" --format json

# Backup database
python cli.py backup

# Compare products
python cli.py compare "Product 1" "Product 2"

# Analyze product
python cli.py analyze "Product Name" --volatility
python cli.py analyze "Product Name" --predict 7
python cli.py analyze "Product Name" --seasonal

# Find best time to buy
python cli.py best-time "Product Name" --days 30

# List all products
python cli.py list

# Show configuration
python cli.py config
```

### Web Dashboard

Start the web dashboard:
```bash
python web_dashboard.py
```

Access at: http://localhost:5000

### REST API

Start the API server:
```bash
python api.py
```

API runs at: http://localhost:5001

#### API Endpoints

- `GET /api/health` - Health check
- `GET /api/products` - Get all products
- `POST /api/products` - Add new product
- `GET /api/products/<id>` - Get specific product
- `DELETE /api/products/<id>` - Delete product
- `GET /api/products/<id>/prices` - Get price history
- `GET /api/products/<id>/stats` - Get statistics
- `POST /api/products/<id>/scrape` - Manually scrape price
- `POST /api/scrape/all` - Scrape all products
- `GET /api/stats` - Overall statistics

### Scheduler

Run scheduled price tracking:
```bash
# Daily at 9 AM
python scheduler.py --mode daily --hour 9

# Hourly
python scheduler.py --mode hourly

# Every N hours
python scheduler.py --mode interval --interval 6

# Run once
python scheduler.py --once

# Test mode (every 5 minutes)
python scheduler.py --test
```

### Background Service

Run as background service:
```bash
python run_background_service.py --interval 6
```

### Windows Task Scheduler

Set up Windows Task Scheduler:
```powershell
# PowerShell (run as Administrator)
.\setup_windows_scheduler.ps1

# Or use batch file
.\setup_windows_scheduler.bat
```

### Linux/Mac Cron

Set up cron job:
```bash
chmod +x setup_cron.sh
./setup_cron.sh
```

### Docker Deployment

Build and run with Docker Compose:
```bash
# Linux/Mac
chmod +x deploy.sh
./deploy.sh

# Windows
.\deploy.ps1

# Or manually
docker-compose up -d
```

## Configuration

### Products Configuration

Edit `products.json` to add/remove products:

```json
{
    "products": [
        {
            "name": "Product Name",
            "url": "https://example.com/product",
            "alert_threshold": 10
        }
    ]
}
```

### Alert Configuration

Edit `alert_config.json` to configure alerts:

```json
{
    "email": {
        "enabled": true,
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "sender_email": "your-email@gmail.com",
        "sender_password": "your-app-password",
        "recipient_email": "recipient@example.com"
    },
    "telegram": {
        "enabled": true,
        "bot_token": "your-bot-token",
        "chat_id": "your-chat-id"
    },
    "desktop": {
        "enabled": true
    },
    "default_alert_threshold": 10
}
```

### Application Configuration

Edit `config.json` or set environment variables:

- `DB_FILE` - Database file path
- `USE_SELENIUM` - Enable Selenium (true/false)
- `SCRAPER_TIMEOUT` - Request timeout in seconds
- `API_HOST` - API host
- `API_PORT` - API port
- `WEB_HOST` - Web dashboard host
- `WEB_PORT` - Web dashboard port
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)

## Browser Extension

### Installation

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select the `browser_extension` folder

### Usage

1. Navigate to a product page
2. Click the extension icon
3. Enter product name (auto-filled from page title)
4. Set API URL (default: http://localhost:5001)
5. Click "Track This Product"

## Testing

Run tests:
```bash
pytest tests/ -v
```

Run tests with coverage:
```bash
pytest tests/ -v --cov=. --cov-report=html
```

## Project Structure

```
web_scraper/
├── card_scraper.py          # Main scraper script
├── price_analysis.py        # Price analysis and reports
├── database.py              # Database operations
├── alerts.py                # Alert system
├── scraper_enhanced.py      # Enhanced scraper with Selenium
├── scheduler.py             # Scheduling system
├── web_dashboard.py         # Flask web dashboard
├── api.py                   # REST API
├── data_export.py           # Data export and backup
├── price_comparison.py      # Price comparison tools
├── advanced_analytics.py    # ML and advanced analytics
├── currency_converter.py    # Currency conversion
├── discount_tracker.py      # Discount tracking
├── wishlist_manager.py      # Wishlist management
├── config.py                # Configuration management
├── logging_config.py        # Logging setup
├── cli.py                   # Command-line interface
├── products.json            # Product configuration
├── requirements.txt         # Python dependencies
├── Dockerfile               # Docker image
├── docker-compose.yml       # Docker Compose configuration
├── tests/                   # Test files
├── templates/               # Web dashboard templates
├── static/                  # Static files (CSS, JS)
├── browser_extension/       # Browser extension files
├── logs/                    # Log files
├── exports/                 # Exported data
├── backups/                 # Database backups
└── analysis/                # Analysis reports
```

## Features Overview

### 1. Price Alert System
- Email notifications
- Telegram bot integration
- Desktop notifications (Windows)
- Configurable price drop thresholds

### 2. Database Migration
- SQLite database for better performance
- Migration script from Excel
- Efficient data storage and retrieval

### 3. Web Dashboard
- Real-time price charts
- Product management UI
- Interactive visualizations
- Add/remove products

### 4. Scheduler/Automation
- Windows Task Scheduler integration
- Cron job support (Linux/Mac)
- Background service mode
- Configurable intervals

### 5. REST API
- Complete RESTful API
- Product management endpoints
- Price query endpoints
- Manual scraping triggers

### 6. Enhanced Scraping
- Selenium support for JavaScript sites
- Proxy rotation
- Better error handling and retries
- Support for multiple e-commerce sites

### 7. Data Export & Backup
- CSV/JSON export
- Excel export (multi-sheet)
- Automated backups
- Data archival

### 8. Price Comparison
- Compare multiple products
- Trend comparison
- Best time to buy analysis
- Price correlation

### 9. Advanced Analytics
- ML price prediction
- Volatility analysis
- Seasonal trend detection
- Moving averages
- Support/resistance levels

### 10. Configuration & Logging
- Comprehensive logging system
- Environment-based configuration
- CLI interface
- Log rotation

### 11. Testing & Quality
- Unit tests
- Integration tests
- Mock responses
- CI/CD pipeline (GitHub Actions)

### 12. Docker & Deployment
- Docker containerization
- Docker Compose setup
- Deployment scripts
- Multi-service architecture

### 13. Browser Extension
- Chrome/Firefox extension
- One-click product tracking
- Auto-fill product information
- API integration

### 14. Additional Features
- Currency conversion
- Discount tracking
- Wishlist management
- Price drop history

## License

See LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please open an issue on the repository.
