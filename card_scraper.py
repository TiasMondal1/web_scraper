import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import os
import json
from urllib.parse import urlparse
from price_analysis import PriceAnalyzer # type: ignore
from alerts import AlertManager # type: ignore
from database import PriceDatabase # type: ignore
from scraper_enhanced import EnhancedScraper # type: ignore

def load_products():
    try:
        with open('products.json', 'r') as file:
            config = json.load(file)
            return config['products']
    except Exception as e:
        print(f"Error loading products: {str(e)}")
        return []

def get_price(url):
    # Headers to mimic a browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    try:
        # Extract site name from the URL
        site_name = urlparse(url).netloc.replace('www.', '')
        site_name = site_name.split('.')[0].capitalize()
        
        print(f"Fetching price from {site_name}")
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Handle different websites
            if 'amazon' in url.lower():
                price_element = soup.find('span', {'class': 'a-price-whole'})
                if price_element:
                    price = price_element.text.replace(',', '').strip()
                    return float(price)
            elif 'flipkart' in url.lower():
                # Try different possible class names for Flipkart price
                price_element = soup.find('div', {'class': '_30jeq3 _16Jk6d'})
                if not price_element:
                    price_element = soup.find('div', {'class': '_30jeq3'})
                if not price_element:
                    price_element = soup.find('div', {'class': '_16Jk6d'})
                if not price_element:
                    price_element = soup.find('div', {'class': 'Nx9bqj CxhGGd'})
                if not price_element:
                    price_element = soup.find('div', {'class': 'Nx9bqj'})
                
                if price_element:
                    price_text = price_element.text
                    # Remove currency symbol and commas
                    price = price_text.replace('₹', '').replace(',', '').strip()
                    try:
                        return float(price)
                    except ValueError:
                        print(f"Could not convert price '{price_text}' to number")
                        return None
                else:
                    print("Could not find price element on Flipkart page")
                    # Print the page content for debugging
                    print("Page content preview:", response.text[:500])
                    return None
            
            return None
        else:
            print(f"Failed to fetch page. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return None

# Initialize database (global instance)
_db = None

def get_database():
    """Get database instance (singleton pattern)"""
    global _db
    if _db is None:
        _db = PriceDatabase()
    return _db

def update_price_data(product, alert_manager=None, db=None):
    """Update price data in database"""
    if db is None:
        db = get_database()
    
    # Ensure product exists in database
    db.add_product(product['name'], product['url'])
    
    # Get current price
    current_price = get_price(product['url'])
    
    if current_price:
        # Get previous price for alert checking
        previous_price = db.get_latest_price(product['name'])
        
        # Add price record to database
        db.add_price_record(product['name'], current_price)
        
        now = datetime.now()
        date_str = now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H:%M:%S')
        
        print(f"Price updated for {product['name']}: ₹{current_price} at {date_str} {time_str}")
        
        # Check and send alerts if alert manager is provided
        if alert_manager and previous_price is not None:
            alert_threshold = product.get('alert_threshold', None)
            alert_manager.check_and_send_alerts(
                product['name'], 
                current_price, 
                previous_price, 
                product['url'],
                alert_threshold
            )
    else:
        print(f"Failed to get price for {product['name']}")

def track_all_products():
    products = load_products()
    if not products:
        print("No products found in configuration. Please check products.json")
        return
    
    # Initialize alert manager
    alert_manager = AlertManager()
    
    print("Price tracking started for all products!\n")
    
    for product in products:
        try:
            print(f"\nTracking {product['name']}...")
            update_price_data(product, alert_manager)
            # Add a small delay between products to avoid rate limiting
            time.sleep(5)
        except Exception as e:
            print(f"Error tracking {product['name']}: {str(e)}")

def run_price_analysis():
    print("\nGenerating price analysis...")
    analyzer = PriceAnalyzer()
    
    # Get all product names from database
    db = get_database()
    product_names = db.get_all_product_names()
    
    if not product_names:
        print("No products found in database.")
        return
    
    # Generate analysis for each product
    for product_name in product_names:
        print(f"\nAnalyzing {product_name}...")
        report_path = analyzer.generate_analysis_report(product_name)
        if report_path:
            print(f"Analysis report generated: {report_path}")

def main():
    try:
        # First track prices
        track_all_products()
        
        # Then run analysis
        run_price_analysis()
        
    except Exception as e:
        print(f'Error message: {str(e)}')

if __name__ == "__main__":
    main()