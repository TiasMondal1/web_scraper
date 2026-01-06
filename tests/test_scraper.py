"""
Unit tests for scraper module with mocked responses
"""
import unittest
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup

class TestScraper(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.amazon_html = '''
        <html>
            <body>
                <span class="a-price-whole">999</span>
            </body>
        </html>
        '''
        
        self.flipkart_html = '''
        <html>
            <body>
                <div class="_30jeq3 _16Jk6d">₹1,499</div>
            </body>
        </html>
        '''
    
    @patch('card_scraper.requests.get')
    def test_amazon_price_extraction(self, mock_get):
        """Test Amazon price extraction"""
        from card_scraper import get_price
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = self.amazon_html
        mock_get.return_value = mock_response
        
        price = get_price("https://www.amazon.in/test-product")
        self.assertEqual(price, 999.0)
    
    @patch('card_scraper.requests.get')
    def test_flipkart_price_extraction(self, mock_get):
        """Test Flipkart price extraction"""
        from card_scraper import get_price
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = self.flipkart_html
        mock_get.return_value = mock_response
        
        price = get_price("https://www.flipkart.com/test-product")
        self.assertEqual(price, 1499.0)
    
    @patch('card_scraper.requests.get')
    def test_invalid_url(self, mock_get):
        """Test handling of invalid URL"""
        from card_scraper import get_price
        
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        price = get_price("https://example.com/invalid")
        self.assertIsNone(price)
    
    @patch('card_scraper.requests.get')
    def test_enhanced_scraper(self, mock_get):
        """Test enhanced scraper"""
        from scraper_enhanced import EnhancedScraper
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = self.amazon_html
        mock_get.return_value = mock_response
        
        scraper = EnhancedScraper(use_selenium=False)
        price = scraper.get_price("https://www.amazon.in/test-product")
        self.assertEqual(price, 999.0)
        scraper.close()

if __name__ == '__main__':
    unittest.main()




