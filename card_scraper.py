import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import os
import logging

def get_price(url):
    # Headers to mimic a browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    try:
        print("Fetching price from Amazon")
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try different price element selectors as Amazon's structure might vary
            price_element = soup.find('span', {'class': 'a-price-whole'})
            if price_element:
                price = price_element.text.replace(',', '').strip()
                return float(price)
            
            return None
        else:
            print(f"Failed to fetch page. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return None

def load_or_create_excel(filename):
    if os.path.exists(filename):
        return pd.read_excel(filename)
    else:
        return pd.DataFrame(columns=['Date', 'Time', 'Price'])

def update_price_data(url, filename='price_history.xlsx'):
    # Load existing data or create new DataFrame
    df = load_or_create_excel(filename)
    
    # Get current price
    current_price = get_price(url)
    
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
        
        # Save updated DataFrame to Excel
        df.to_excel(filename, index=False)
        print(f"Price updated: ₹{current_price} at {date} {time}")
    else:
        print("Failed to get price")

def main():
    url = "https://www.amazon.in/Zotac-GDDR6-pci_Express_x16-Gaming-GEFORCE/dp/B08WRF18SC/"

    try:
        print("Price tracking started !!!")
    
        update_price_data(url)
        # Wait for 24 hours before next check
        #time.sleep(24 * 60 * 60)  # 24 hours in seconds
    except Exception as e:
        print('Error message: {0}'.format(e))

if __name__ == "__main__":
    main()