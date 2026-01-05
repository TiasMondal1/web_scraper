"""Debug script to find exact price location in Flipkart JSON"""
import requests
import re
import json

url = "https://www.flipkart.com/google-pixel-10-obsidian-256-gb/p/itm06bd3add90074?pid=MOBHEXHRCFEKF6DH&lid=LSTMOBHEXHRCFEKF6DHZ9XHID&marketplace=FLIPKART&q=pixel&store=search.flipkart.com&srno=s_1_2&otracker=search&otracker1=search&fm=Search&iid=dbb096e5-745a-4ada-a65b-85e602a95f6b.MOBHEXHRCFEKF6DH.SEARCH&ppt=sp&ppn=sp&ssid=0oaag18fcg0000001767639658297&qH=ab4086ecd47c568d"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

response = requests.get(url, headers=headers, timeout=30)

# Find all finalPrice occurrences with context
final_price_matches = list(re.finditer(r'"finalPrice"\s*:\s*"?(\d+(?:,\d+)*)"?', response.text, re.IGNORECASE))
print(f"Found {len(final_price_matches)} 'finalPrice' matches:")
for i, match in enumerate(final_price_matches[:5]):
    start = max(0, match.start() - 100)
    end = min(len(response.text), match.end() + 100)
    context = response.text[start:end]
    price_val = match.group(1).replace(',', '')
    print(f"\n[{i+1}] Price: {price_val}")
    print(f"Context: ...{context}...")

# Find all price occurrences
price_matches = list(re.finditer(r'"price"\s*:\s*"?(\d+(?:,\d+)*)"?', response.text, re.IGNORECASE))
print(f"\n\nFound {len(price_matches)} 'price' matches (showing first 10):")
for i, match in enumerate(price_matches[:10]):
    price_val = match.group(1).replace(',', '')
    try:
        val = float(price_val)
        if 1000 < val < 200000:
            print(f"  [{i+1}] Price: {price_val} (Rs {val:,.0f})")
    except:
        pass

