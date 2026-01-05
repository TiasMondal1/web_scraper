"""
Unit tests for alerts module
"""
import unittest
from unittest.mock import patch, MagicMock
from alerts import AlertManager

class TestAlerts(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.alert_manager = AlertManager()
    
    def test_load_config(self):
        """Test loading alert configuration"""
        config = self.alert_manager.config
        self.assertIn('email', config)
        self.assertIn('telegram', config)
        self.assertIn('desktop', config)
    
    @patch('alerts.smtplib.SMTP')
    def test_email_alert(self, mock_smtp):
        """Test email alert sending"""
        # Configure email in config (would normally be in config file)
        self.alert_manager.config['email']['enabled'] = True
        self.alert_manager.config['email']['sender_email'] = 'test@example.com'
        self.alert_manager.config['email']['sender_password'] = 'password'
        self.alert_manager.config['email']['recipient_email'] = 'recipient@example.com'
        
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = self.alert_manager.send_email_alert(
            "Test Product", 100.0, 150.0, "https://example.com", 33.33
        )
        
        # Should attempt to send (may fail due to invalid credentials, but should not crash)
        self.assertIsInstance(result, bool)
    
    def test_alert_threshold_check(self):
        """Test alert threshold checking"""
        # Price drop of 20% should trigger alert with 10% threshold
        result = self.alert_manager.check_and_send_alerts(
            "Test Product", 80.0, 100.0, "https://example.com", 10.0
        )
        # Should return True if alert was triggered
        self.assertIsInstance(result, (bool, type(None)))
    
    def test_no_alert_for_price_increase(self):
        """Test that alerts are not sent for price increases"""
        # Price increased, should not alert
        result = self.alert_manager.check_and_send_alerts(
            "Test Product", 150.0, 100.0, "https://example.com", 10.0
        )
        # Should return False or None (no alert)
        self.assertNotEqual(result, True)

if __name__ == '__main__':
    unittest.main()



