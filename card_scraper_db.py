import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import os
import json
from urllib.parse import urlparse
from database_manager import DatabaseManager
from price_analysis_db import PriceAnalyzerDB

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

def initialize_database_with_products(db_manager):
    """Initialize database with products from JSON config"""
    products = load_products()
    
    for product in products:
        product_id = db_manager.add_product(product['name'], product['url'])
        if product_id:
            print(f"Added/Updated product: {product['name']} (ID: {product_id})")
        else:
            print(f"Failed to add product: {product['name']}")

def update_price_data(product, db_manager):
    """Update price data using database instead of Excel"""
    
    # Get current price
    current_price = get_price(product['url'])
    
    if current_price:
        # Add price record to database
        success = db_manager.add_price_record(product['name'], current_price)
        
        if success:
            now = datetime.now()
            date = now.strftime('%Y-%m-%d')
            time_str = now.strftime('%H:%M:%S')
            print(f"Price updated for {product['name']}: ₹{current_price} at {date} {time_str}")
            
            # Show latest statistics
            stats = db_manager.get_price_statistics(product['name'])
            if stats:
                print(f"  Total records: {stats['record_count']}")
                print(f"  Average price: ₹{stats['avg_price']:.2f}")
                print(f"  Price range: ₹{stats['min_price']:.2f} - ₹{stats['max_price']:.2f}")
        else:
            print(f"Failed to save price for {product['name']}")
    else:
        print(f"Failed to get price for {product['name']}")

def track_all_products():
    """Track all products using database storage"""
    # Initialize database manager
    db_manager = DatabaseManager()
    
    # Display database info
    info = db_manager.get_database_info()
    print(f"Database: {info['database_path']} ({info['database_size_mb']} MB)")
    print(f"Tracked products: {info['product_count']}, Total records: {info['total_records']}")
    
    # Initialize products in database
    initialize_database_with_products(db_manager)
    
    products = load_products()
    if not products:
        print("No products found in configuration. Please check products.json")
        return
    
    print(f"\nPrice tracking started for {len(products)} products!\n")
    
    for product in products:
        try:
            print(f"\nTracking {product['name']}...")
            update_price_data(product, db_manager)
            # Add a small delay between products to avoid rate limiting
            time.sleep(5)
        except Exception as e:
            print(f"Error tracking {product['name']}: {str(e)}")

def run_price_analysis():
    """Generate price analysis using database data"""
    print("\nGenerating price analysis from database...")
    
    db_manager = DatabaseManager()
    analyzer = PriceAnalyzerDB(db_manager)
    
    # Get all product names from database
    product_names = db_manager.get_all_products()
    
    if not product_names:
        print("No products found in database")
        return
    
    # Generate analysis for each product
    for product_name in product_names:
        print(f"\nAnalyzing {product_name}...")
        report_path = analyzer.generate_analysis_report(product_name)
        if report_path:
            print(f"Analysis report generated: {report_path}")

def database_management_menu():
    """Interactive menu for database management"""
    db_manager = DatabaseManager()
    
    while True:
        print("\n" + "="*50)
        print("DATABASE MANAGEMENT MENU")
        print("="*50)
        print("1. Show database info")
        print("2. List all products")
        print("3. Show product statistics")
        print("4. Migrate from Excel")
        print("5. Export to Excel")
        print("6. Cleanup old records")
        print("7. Back to main menu")
        print("="*50)
        
        choice = input("Enter your choice (1-7): ").strip()
        
        if choice == '1':
            info = db_manager.get_database_info()
            print("\nDatabase Information:")
            for key, value in info.items():
                print(f"  {key}: {value}")
        
        elif choice == '2':
            products = db_manager.get_all_products()
            print(f"\nTracked Products ({len(products)}):")
            for i, product in enumerate(products, 1):
                print(f"  {i}. {product}")
        
        elif choice == '3':
            products = db_manager.get_all_products()
            if products:
                print("\nSelect a product:")
                for i, product in enumerate(products, 1):
                    print(f"  {i}. {product}")
                
                try:
                    product_idx = int(input("Enter product number: ")) - 1
                    if 0 <= product_idx < len(products):
                        product_name = products[product_idx]
                        stats = db_manager.get_price_statistics(product_name)
                        if stats:
                            print(f"\nStatistics for {product_name}:")
                            for key, value in stats.items():
                                print(f"  {key}: {value}")
                    else:
                        print("Invalid product number")
                except ValueError:
                    print("Please enter a valid number")
            else:
                print("No products found")
        
        elif choice == '4':
            print("\nMigrating from Excel...")
            success = db_manager.migrate_from_excel()
            if success:
                print("Migration completed successfully")
            else:
                print("Migration failed")
        
        elif choice == '5':
            output_file = input("Enter output filename (default: exported_price_history.xlsx): ").strip()
            if not output_file:
                output_file = "exported_price_history.xlsx"
            success = db_manager.export_to_excel(output_file)
            if success:
                print(f"Data exported to {output_file}")
            else:
                print("Export failed")
        
        elif choice == '6':
            try:
                days = int(input("Enter days to keep (default: 365): ") or "365")
                deleted_count = db_manager.cleanup_old_records(days)
                print(f"Cleaned up {deleted_count} old records")
            except ValueError:
                print("Please enter a valid number")
        
        elif choice == '7':
            break
        
        else:
            print("Invalid choice. Please try again.")

def main():
    """Main function with menu system"""
    print("Card Scraper with Database Integration")
    print("=====================================")
    
    while True:
        print("\nMAIN MENU")
        print("---------")
        print("1. Track all product prices")
        print("2. Generate price analysis")
        print("3. Database management")
        print("4. Track prices + Generate analysis")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            track_all_products()
        
        elif choice == '2':
            run_price_analysis()
        
        elif choice == '3':
            database_management_menu()
        
        elif choice == '4':
            try:
                # First track prices
                track_all_products()
                
                # Then run analysis
                run_price_analysis()
                
            except Exception as e:
                print(f'Error message: {str(e)}')
        
        elif choice == '5':
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main() 