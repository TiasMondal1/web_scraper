"""
Enhanced Web Scraper with Selenium support, proxy rotation, and better error handling
Supports multiple e-commerce sites
"""
import requests
from bs4 import BeautifulSoup
import time
import random
from urllib.parse import urlparse
from typing import Optional, Dict, List
import logging

# Try to import Selenium (optional)
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

logger = logging.getLogger(__name__)

class EnhancedScraper:
    def __init__(self, use_selenium=False, proxies=None, retry_count=3, timeout=30):
        """
        Initialize enhanced scraper
        
        Args:
            use_selenium: Use Selenium for JavaScript-heavy sites
            proxies: List of proxy dictionaries [{'http': 'http://proxy:port', 'https': 'https://proxy:port'}]
            retry_count: Number of retry attempts
            timeout: Request timeout in seconds
        """
        self.use_selenium = use_selenium and SELENIUM_AVAILABLE
        self.proxies = proxies or []
        self.current_proxy_index = 0
        self.retry_count = retry_count
        self.timeout = timeout
        self.driver = None
        
        if self.use_selenium:
            self._init_selenium_driver()
    
    def _init_selenium_driver(self):
        """Initialize Selenium WebDriver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("Selenium WebDriver initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Selenium: {e}. Falling back to requests.")
            self.use_selenium = False
    
    def _get_proxy(self):
        """Get next proxy from the list"""
        if not self.proxies:
            return None
        proxy = self.proxies[self.current_proxy_index % len(self.proxies)]
        self.current_proxy_index += 1
        return proxy
    
    def _get_headers(self):
        """Get randomized headers"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
        ]
        return {
            'User-Agent': random.choice(user_agents),
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
    
    def _scrape_with_requests(self, url: str) -> Optional[BeautifulSoup]:
        """Scrape using requests library"""
        for attempt in range(self.retry_count):
            try:
                proxy = self._get_proxy()
                headers = self._get_headers()
                
                response = requests.get(url, headers=headers, proxies=proxy, timeout=self.timeout)
                
                if response.status_code == 200:
                    return BeautifulSoup(response.text, 'html.parser')
                elif response.status_code == 403:
                    logger.warning(f"Access forbidden (403) for {url}. Attempt {attempt + 1}/{self.retry_count}")
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.warning(f"HTTP {response.status_code} for {url}. Attempt {attempt + 1}/{self.retry_count}")
                    time.sleep(1)
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout for {url}. Attempt {attempt + 1}/{self.retry_count}")
                time.sleep(2 ** attempt)
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request error for {url}: {e}. Attempt {attempt + 1}/{self.retry_count}")
                time.sleep(2 ** attempt)
        
        return None
    
    def _scrape_with_selenium(self, url: str) -> Optional[BeautifulSoup]:
        """Scrape using Selenium"""
        if not self.driver:
            return None
        
        try:
            self.driver.get(url)
            # Wait for page to load (adjust selector based on site)
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(2)  # Additional wait for JavaScript execution
            html = self.driver.page_source
            return BeautifulSoup(html, 'html.parser')
        except TimeoutException:
            logger.warning(f"Selenium timeout for {url}")
            return BeautifulSoup(self.driver.page_source, 'html.parser')  # Return what we have
        except Exception as e:
            logger.error(f"Selenium error for {url}: {e}")
            return None
    
    def scrape(self, url: str) -> Optional[BeautifulSoup]:
        """Scrape a URL using the configured method"""
        if self.use_selenium:
            return self._scrape_with_selenium(url)
        else:
            return self._scrape_with_requests(url)
    
    def get_price(self, url: str) -> Optional[float]:
        """Get price from URL using enhanced scraping"""
        soup = self.scrape(url)
        if not soup:
            return None
        
        site_name = urlparse(url).netloc.lower()
        
        # Route to site-specific price extractors
        if 'amazon' in site_name:
            return self._extract_amazon_price(soup)
        elif 'flipkart' in site_name:
            return self._extract_flipkart_price(soup)
        elif 'snapdeal' in site_name:
            return self._extract_snapdeal_price(soup)
        elif 'myntra' in site_name:
            return self._extract_myntra_price(soup)
        elif 'nykaa' in site_name:
            return self._extract_nykaa_price(soup)
        elif 'ebay' in site_name:
            return self._extract_ebay_price(soup)
        else:
            logger.warning(f"Unsupported site: {site_name}. Trying generic extraction.")
            return self._extract_generic_price(soup)
    
    def _extract_amazon_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract price from Amazon"""
        selectors = [
            {'tag': 'span', 'class': 'a-price-whole'},
            {'tag': 'span', 'id': 'priceblock_dealprice'},
            {'tag': 'span', 'id': 'priceblock_saleprice'},
            {'tag': 'span', 'id': 'priceblock_ourprice'},
            {'tag': 'span', 'class': 'a-price'},
        ]
        return self._try_selectors(soup, selectors)
    
    def _extract_flipkart_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract price from Flipkart"""
        selectors = [
            {'tag': 'div', 'class': '_30jeq3 _16Jk6d'},
            {'tag': 'div', 'class': '_30jeq3'},
            {'tag': 'div', 'class': '_16Jk6d'},
            {'tag': 'div', 'class': 'Nx9bqj CxhGGd'},
            {'tag': 'div', 'class': 'Nx9bqj'},
        ]
        return self._try_selectors(soup, selectors)
    
    def _extract_snapdeal_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract price from Snapdeal"""
        selectors = [
            {'tag': 'span', 'class': 'payBlkBig'},
            {'tag': 'span', 'class': 'product-price'},
            {'tag': 'span', 'id': 'buyPriceBox'},
        ]
        return self._try_selectors(soup, selectors)
    
    def _extract_myntra_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract price from Myntra"""
        selectors = [
            {'tag': 'span', 'class': 'pdp-price'},
            {'tag': 'span', 'class': 'product-discountedPrice'},
            {'tag': 'div', 'class': 'pdp-price'},
        ]
        return self._try_selectors(soup, selectors)
    
    def _extract_nykaa_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract price from Nykaa"""
        selectors = [
            {'tag': 'span', 'class': 'css-1jczs19'},
            {'tag': 'span', 'class': 'price'},
        ]
        return self._try_selectors(soup, selectors)
    
    def _extract_ebay_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract price from eBay"""
        selectors = [
            {'tag': 'span', 'id': 'prcIsum'},
            {'tag': 'span', 'class': 'notranslate'},
            {'tag': 'span', 'itemprop': 'price'},
        ]
        return self._try_selectors(soup, selectors)
    
    def _extract_generic_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Generic price extraction - looks for common price patterns"""
        # Look for common price patterns
        price_patterns = [
            r'₹[\d,]+\.?\d*',
            r'Rs\.?\s*[\d,]+\.?\d*',
            r'\$[\d,]+\.?\d*',
            r'[\d,]+\.?\d*\s*(?:INR|USD|Rs|₹)'
        ]
        
        import re
        text = soup.get_text()
        
        for pattern in price_patterns:
            matches = re.findall(pattern, text)
            if matches:
                # Try to extract the first reasonable price
                for match in matches[:5]:  # Check first 5 matches
                    try:
                        price_str = re.sub(r'[^\d.]', '', match)
                        price = float(price_str)
                        if 10 < price < 10000000:  # Reasonable price range
                            return price
                    except:
                        continue
        
        return None
    
    def _try_selectors(self, soup: BeautifulSoup, selectors: List[Dict]) -> Optional[float]:
        """Try multiple selectors to find price"""
        for selector in selectors:
            try:
                tag = selector.get('tag', 'span')
                class_name = selector.get('class')
                id_name = selector.get('id')
                
                if class_name:
                    element = soup.find(tag, {'class': class_name})
                elif id_name:
                    element = soup.find(tag, {'id': id_name})
                else:
                    continue
                
                if element:
                    price_text = element.get_text()
                    price = self._parse_price(price_text)
                    if price:
                        return price
            except Exception as e:
                logger.debug(f"Selector failed: {e}")
                continue
        
        return None
    
    def _parse_price(self, price_text: str) -> Optional[float]:
        """Parse price from text"""
        try:
            # Remove currency symbols and commas
            price_text = price_text.replace('₹', '').replace('Rs.', '').replace('Rs', '')
            price_text = price_text.replace(',', '').replace('$', '').strip()
            
            # Extract numeric value
            import re
            match = re.search(r'[\d]+\.?\d*', price_text)
            if match:
                return float(match.group())
        except Exception as e:
            logger.debug(f"Price parsing error: {e}")
        
        return None
    
    def get_stock_status(self, url: str) -> Optional[str]:
        """Get stock status (in stock, out of stock, etc.)"""
        soup = self.scrape(url)
        if not soup:
            return None
        
        site_name = urlparse(url).netloc.lower()
        text = soup.get_text().lower()
        
        # Common out of stock indicators
        out_of_stock_keywords = ['out of stock', 'sold out', 'unavailable', 'not available', 'out of stock']
        in_stock_keywords = ['in stock', 'available', 'add to cart', 'buy now']
        
        for keyword in out_of_stock_keywords:
            if keyword in text:
                return 'out_of_stock'
        
        for keyword in in_stock_keywords:
            if keyword in text:
                return 'in_stock'
        
        return 'unknown'
    
    def close(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None

# Convenience function for backward compatibility
def get_price_enhanced(url: str, use_selenium: bool = False, proxies: List[Dict] = None) -> Optional[float]:
    """
    Enhanced price fetching function
    
    Args:
        url: Product URL
        use_selenium: Use Selenium for JavaScript-heavy sites
        proxies: List of proxy configurations
    
    Returns:
        Price as float or None
    """
    scraper = EnhancedScraper(use_selenium=use_selenium, proxies=proxies)
    try:
        return scraper.get_price(url)
    finally:
        scraper.close()




