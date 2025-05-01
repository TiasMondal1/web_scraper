import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import os
import json
from urllib.parse import urlparse

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

def load_or_create_excel(product_name):
    filename = 'price_history.xlsx'
    if os.path.exists(filename):
        try:
            # Try to read the existing sheet
            return pd.read_excel(filename, sheet_name=product_name)
        except:
            # If sheet doesn't exist, create new DataFrame
            return pd.DataFrame(columns=['Date', 'Time', 'Price'])
    else:
        return pd.DataFrame(columns=['Date', 'Time', 'Price'])

def update_price_data(product):
    # Load existing data or create new DataFrame for this product
    df = load_or_create_excel(product['name'])
    
    # Get current price
    current_price = get_price(product['url'])
    
    if current_price:
        # Get current date and time
        now = datetime.now()
        date = now.strftime('%Y-%m-%d')
        time = now.strftime('%H:%M:%S')
        
        # Add new row to DataFrame
        new_row = pd.DataFrame({
            'Date': [date],
            'Time': [time],
            'Price': [current_price]
        })
        
        df = pd.concat([df, new_row], ignore_index=True)
        
        # Save to Excel with multiple sheets
        filename = 'price_history.xlsx'
        if os.path.exists(filename):
            with pd.ExcelWriter(filename, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                df.to_excel(writer, sheet_name=product['name'], index=False)
        else:
            df.to_excel(filename, sheet_name=product['name'], index=False)
            
        print(f"Price updated for {product['name']}: ₹{current_price} at {date} {time}")
    else:
        print(f"Failed to get price for {product['name']}")

def track_all_products():
    products = load_products()
    if not products:
        print("No products found in configuration. Please check products.json")
        return
    
    print("Price tracking started for all products!\n")
    
    for product in products:
        try:
            print(f"\nTracking {product['name']}...")
            update_price_data(product)
            # Add a small delay between products to avoid rate limiting
            time.sleep(2)
        except Exception as e:
            print(f"Error tracking {product['name']}: {str(e)}")

def main():
    try:
        track_all_products()
    except Exception as e:
        print(f'Error message: {str(e)}')

if __name__ == "__main__":
    main()