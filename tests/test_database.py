"""
Unit tests for database module
"""
import unittest
import os
import tempfile
from database import PriceDatabase

class TestPriceDatabase(unittest.TestCase):
    def setUp(self):
        """Set up test database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = PriceDatabase(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test database"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_add_product(self):
        """Test adding a product"""
        product_id = self.db.add_product("Test Product", "https://example.com/product")
        self.assertIsNotNone(product_id)
        
        # Adding same product should return existing ID
        product_id2 = self.db.add_product("Test Product", "https://example.com/product")
        self.assertEqual(product_id, product_id2)
    
    def test_add_price_record(self):
        """Test adding price record"""
        self.db.add_product("Test Product", "https://example.com/product")
        
        from datetime import datetime
        result = self.db.add_price_record("Test Product", 100.0, datetime.now())
        self.assertTrue(result)
    
    def test_get_latest_price(self):
        """Test getting latest price"""
        self.db.add_product("Test Product", "https://example.com/product")
        self.db.add_price_record("Test Product", 100.0)
        self.db.add_price_record("Test Product", 150.0)
        
        latest_price = self.db.get_latest_price("Test Product")
        self.assertEqual(latest_price, 150.0)
    
    def test_get_price_history(self):
        """Test getting price history"""
        self.db.add_product("Test Product", "https://example.com/product")
        self.db.add_price_record("Test Product", 100.0)
        self.db.add_price_record("Test Product", 150.0)
        
        df = self.db.get_price_history("Test Product")
        self.assertEqual(len(df), 2)
        self.assertEqual(df['Price'].iloc[0], 100.0)
        self.assertEqual(df['Price'].iloc[1], 150.0)
    
    def test_get_all_products(self):
        """Test getting all products"""
        self.db.add_product("Product 1", "https://example.com/1")
        self.db.add_product("Product 2", "https://example.com/2")
        
        products = self.db.get_all_products()
        self.assertEqual(len(products), 2)
    
    def test_delete_product(self):
        """Test deleting a product"""
        self.db.add_product("Test Product", "https://example.com/product")
        self.db.add_price_record("Test Product", 100.0)
        
        result = self.db.delete_product("Test Product")
        self.assertTrue(result)
        
        products = self.db.get_all_products()
        self.assertEqual(len(products), 0)

if __name__ == '__main__':
    unittest.main()


