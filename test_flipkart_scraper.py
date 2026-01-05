"""
Test script to debug Flipkart price extraction
"""
import requests
from bs4 import BeautifulSoup
import re
import sys
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def test_flipkart_price(url):
    """Test Flipkart price extraction with detailed debugging"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    print(f"Testing URL: {url}\n")
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}\n")
        
        if response.status_code != 200:
            print(f"Failed to fetch page. Status: {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try multiple selectors
        selectors_to_try = [
            ('div', {'class': '_30jeq3 _16Jk6d'}),
            ('div', {'class': '_30jeq3'}),
            ('div', {'class': '_16Jk6d'}),
            ('div', {'class': 'Nx9bqj CxhGGd'}),
            ('div', {'class': 'Nx9bqj'}),
            ('span', {'class': '_30jeq3'}),
            ('div', {'class': 'aMaAEs'}),
            ('div', {'class': '_25b18c'}),
            ('div', {'class': 'a-price-whole'}),
            ('span', {'class': 'a-price-whole'}),
        ]
        
        print("Trying selectors:")
        for tag, attrs in selectors_to_try:
            elements = soup.find_all(tag, attrs)
            if elements:
                print(f"  [OK] Found {len(elements)} element(s) with {tag} {attrs}")
                for i, elem in enumerate(elements[:3]):  # Show first 3
                    text = elem.get_text().strip()
                    print(f"    [{i+1}] Text: '{text}'")
            else:
                print(f"  [X] No elements found with {tag} {attrs}")
        
        # Try regex pattern matching
        print("\nTrying regex patterns:")
        price_patterns = [
            r'₹[\d,]+',
            r'Rs\.?\s*[\d,]+',
            r'price["\']?\s*[:=]\s*["\']?₹?[\d,]+',
            r'finalPrice["\']?\s*[:=]\s*["\']?₹?[\d,]+',
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, response.text, re.IGNORECASE)
            if matches:
                pattern_str = pattern.replace('₹', 'Rs')
                print(f"  [OK] Pattern found {len(matches)} match(es):")
                for match in matches[:5]:  # Show first 5
                    match_str = match.replace('₹', 'Rs')
                    print(f"    - {match_str}")
        
        # Try to find price in script tags (JSON data)
        print("\nChecking script tags for price data:")
        scripts = soup.find_all('script', type='application/json')
        for script in scripts[:3]:
            try:
                import json
                data = json.loads(script.string)
                # Look for price in JSON
                json_str = json.dumps(data)
                price_matches = re.findall(r'₹[\d,]+', json_str)
                if price_matches:
                    print(f"  [OK] Found prices in JSON: {price_matches[:3]}")
            except:
                pass
        
        # Try data attributes
        print("\nChecking data attributes:")
        price_elements = soup.find_all(attrs={"data-price": True})
        if price_elements:
            for elem in price_elements[:3]:
                print(f"  [OK] data-price: {elem.get('data-price')}")
        
        # Final attempt: search all text for price pattern
        print("\nSearching all text content:")
        all_text = soup.get_text()
        price_matches = re.findall(r'₹[\d,]+\.?\d*', all_text)
        if price_matches:
            unique_prices = list(set(price_matches))[:10]
            print(f"  [OK] Found {len(price_matches)} price mentions:")
            for price in unique_prices:
                clean_price = price.replace('₹', '').replace(',', '').strip()
                try:
                    price_val = float(clean_price)
                    if 1000 < price_val < 200000:  # Reasonable phone price range
                        print(f"    -> {price} (Rs {price_val:,.0f}) - Possible match!")
                except:
                    pass
        
        return None
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    url = "https://www.flipkart.com/google-pixel-10-obsidian-256-gb/p/itm06bd3add90074?pid=MOBHEXHRCFEKF6DH&lid=LSTMOBHEXHRCFEKF6DHZ9XHID&marketplace=FLIPKART&q=pixel&store=search.flipkart.com&srno=s_1_2&otracker=search&otracker1=search&fm=Search&iid=dbb096e5-745a-4ada-a65b-85e602a95f6b.MOBHEXHRCFEKF6DH.SEARCH&ppt=sp&ppn=sp&ssid=0oaag18fcg0000001767639658297&qH=ab4086ecd47c568d"
    test_flipkart_price(url)

