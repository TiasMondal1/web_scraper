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
                price_selectors = [
                    {'tag': 'div', 'class': '_30jeq3 _16Jk6d'},
                    {'tag': 'div', 'class': '_30jeq3'},
                    {'tag': 'div', 'class': '_16Jk6d'},
                    {'tag': 'div', 'class': 'Nx9bqj CxhGGd'},
                    {'tag': 'div', 'class': 'Nx9bqj'},
                    {'tag': 'span', 'class': '_30jeq3'},
                    {'tag': 'div', 'class': 'aMaAEs'},
                    {'tag': 'div', 'class': '_25b18c'},
                ]
                
                price_element = None
                for selector in price_selectors:
                    if 'class' in selector:
                        # Try exact class match first
                        price_element = soup.find(selector['tag'], {'class': selector['class']})
                        if not price_element and ' ' in selector['class']:
                            # Try with class split (for multiple classes)
                            classes = selector['class'].split()
                            price_element = soup.find(selector['tag'], class_=lambda x: x and all(c in x for c in classes))
                    if price_element:
                        break
                
                # If still not found, try searching by text pattern and JSON data
                if not price_element:
                    import re
                    import json
                    
                    # Method 1: Look in JSON data FIRST (more reliable for Flipkart)
                    # Prioritize finalPrice as it's usually the main product price
                    # Note: JSON numbers can be with or without quotes
                    json_price_patterns = [
                        (r'"finalPrice"\s*:\s*(\d+(?:,\d+)*)', True),  # Priority pattern, no quotes for number
                        (r'"finalPrice"\s*:\s*"?(\d+(?:,\d+)*)"?', True),  # Fallback with optional quotes
                        (r'"sellingPrice"\s*:\s*(\d+(?:,\d+)*)', True),
                    ]
                    
                    # Check priority patterns first
                    for pattern, is_priority in json_price_patterns:
                        matches = re.findall(pattern, response.text, re.IGNORECASE)
                        if matches:
                            # Take the first match (usually the main product price)
                            price_text = matches[0].replace(',', '').strip()
                            try:
                                price_val = float(price_text)
                                if 1000 < price_val < 10000000:
                                    return price_val
                            except ValueError:
                                continue
                    
                    # Method 2: Look for price patterns in the HTML (fallback)
                    price_pattern = r'₹[\d,]+'
                    matches = re.findall(price_pattern, response.text)
                    if matches:
                        # Filter for reasonable prices (likely product prices)
                        # Take the highest reasonable price found
                        found_prices = []
                        for match in matches[:20]:  # Check first 20 matches
                            price_text = match.replace('₹', '').replace(',', '').strip()
                            try:
                                price_val = float(price_text)
                                # Validate it's a reasonable price (between 1000 and 10 million for phones/electronics)
                                if 1000 < price_val < 10000000:
                                    found_prices.append(price_val)
                            except ValueError:
                                continue
                        if found_prices:
                            # Return the highest price (likely the main product price)
                            return max(found_prices)
                    
                    # Also check script tags with JSON
                    scripts = soup.find_all('script', type='application/json')
                    for script in scripts:
                        try:
                            data = json.loads(script.string)
                            json_str = json.dumps(data)
                            # Look for price in JSON structure
                            price_matches = re.findall(r'"price"\s*:\s*"?(\d+(?:,\d+)*)"?', json_str, re.IGNORECASE)
                            if price_matches:
                                for price_match in price_matches:
                                    price_text = price_match.replace(',', '').strip()
                                    try:
                                        price_val = float(price_text)
                                        if 1000 < price_val < 10000000:
                                            return price_val
                                    except ValueError:
                                        continue
                        except:
                            continue
                    
                    # Method 3: Look for price in data attributes or meta tags
                    meta_price = soup.find('meta', property='product:price:amount')
                    if meta_price and meta_price.get('content'):
                        try:
                            return float(meta_price.get('content'))
                        except:
                            pass
                
                if price_element:
                    price_text = price_element.get_text()
                    # Remove currency symbol and commas
                    price = price_text.replace('₹', '').replace(',', '').strip()
                    try:
                        return float(price)
                    except ValueError:
                        print(f"Could not convert price '{price_text}' to number")
                        return None
                else:
                    print("Could not find price element on Flipkart page. The page structure may have changed.")
                    print("Tip: Try using the enhanced scraper with Selenium for JavaScript-heavy sites.")
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