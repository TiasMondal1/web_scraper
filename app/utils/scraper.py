"""
Product scraping utilities
Integrates with existing card_scraper.py functionality
"""
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from typing import Dict, Any
from decimal import Decimal


async def scrape_product_info(url: str) -> Dict[str, Any]:
    """
    Scrape product information from URL
    Supports Amazon and Flipkart
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    # Determine platform
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    
    if 'amazon' in domain:
        return await scrape_amazon(url, headers)
    elif 'flipkart' in domain:
        return await scrape_flipkart(url, headers)
    else:
        raise ValueError(f"Unsupported platform: {domain}")


async def scrape_amazon(url: str, headers: Dict) -> Dict[str, Any]:
    """Scrape Amazon product"""
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract product name
        name_element = soup.find('span', {'id': 'productTitle'})
        name = name_element.text.strip() if name_element else "Unknown Product"
        
        # Extract price
        price = None
        price_element = soup.find('span', {'class': 'a-price-whole'})
        if price_element:
            price_text = price_element.text.replace(',', '').replace('₹', '').strip()
            try:
                price = Decimal(price_text)
            except:
                pass
        
        # Extract image
        image_url = None
        image_element = soup.find('img', {'id': 'landingImage'})
        if image_element and 'src' in image_element.attrs:
            image_url = image_element['src']
        
        # Extract brand
        brand = None
        brand_element = soup.find('a', {'id': 'bylineInfo'})
        if brand_element:
            brand = brand_element.text.strip().replace('Visit the ', '').replace(' Store', '')
        
        # Check availability
        availability_element = soup.find('div', {'id': 'availability'})
        in_stock = True
        if availability_element and 'unavailable' in availability_element.text.lower():
            in_stock = False
        
        return {
            'name': name,
            'price': price,
            'platform': 'amazon',
            'image_url': image_url,
            'brand': brand,
            'in_stock': in_stock
        }
        
    except Exception as e:
        raise Exception(f"Failed to scrape Amazon: {str(e)}")


async def scrape_flipkart(url: str, headers: Dict) -> Dict[str, Any]:
    """Scrape Flipkart product"""
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract product name
        name_element = soup.find('span', {'class': 'VU-ZEz'}) or soup.find('span', {'class': 'B_NuCI'})
        name = name_element.text.strip() if name_element else "Unknown Product"
        
        # Extract price
        price = None
        price_selectors = [
            {'class': 'Nx9bqj CxhGGd'},
            {'class': '_30jeq3 _16Jk6d'},
            {'class': '_30jeq3'},
            {'class': 'Nx9bqj'}
        ]
        
        for selector in price_selectors:
            price_element = soup.find('div', selector)
            if price_element:
                price_text = price_element.text.replace('₹', '').replace(',', '').strip()
                try:
                    price = Decimal(price_text)
                    break
                except:
                    pass
        
        # Extract image
        image_url = None
        image_element = soup.find('img', {'class': '_396cs4 _2amPTt _3qGmMb'})
        if image_element and 'src' in image_element.attrs:
            image_url = image_element['src']
        
        # Check availability
        in_stock = True
        out_of_stock_element = soup.find('div', text=lambda t: t and 'out of stock' in t.lower())
        if out_of_stock_element:
            in_stock = False
        
        return {
            'name': name,
            'price': price,
            'platform': 'flipkart',
            'image_url': image_url,
            'brand': None,  # Flipkart brand extraction is complex
            'in_stock': in_stock
        }
        
    except Exception as e:
        raise Exception(f"Failed to scrape Flipkart: {str(e)}")


def get_platform_from_url(url: str) -> str:
    """Determine platform from URL"""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    
    if 'amazon' in domain:
        return 'amazon'
    elif 'flipkart' in domain:
        return 'flipkart'
    else:
        return 'unknown'

