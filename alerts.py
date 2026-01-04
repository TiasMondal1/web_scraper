"""
Price Alert System
Supports Email, Desktop Notifications, and Telegram Bot alerts
"""
import smtplib
import os
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import requests
try:
    from win10toast import ToastNotifier
    DESKTOP_NOTIF_AVAILABLE = True
except ImportError:
    DESKTOP_NOTIF_AVAILABLE = False
    print("Desktop notifications not available. Install win10toast: pip install win10toast")

class AlertManager:
    def __init__(self, config_file='alert_config.json'):
        self.config_file = config_file
        self.config = self.load_config()
        
    def load_config(self):
        """Load alert configuration from file"""
        default_config = {
            "email": {
                "enabled": False,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "sender_email": "",
                "sender_password": "",
                "recipient_email": ""
            },
            "telegram": {
                "enabled": False,
                "bot_token": "",
                "chat_id": ""
            },
            "desktop": {
                "enabled": True
            },
            "default_alert_threshold": 10  # Percentage drop to trigger alert
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)
                    # Merge with defaults
                    for key in default_config:
                        if key in user_config:
                            default_config[key].update(user_config[key])
                    return default_config
            except Exception as e:
                print(f"Error loading alert config: {e}. Using defaults.")
                return default_config
        else:
            # Create default config file
            self.save_config(default_config)
            return default_config
    
    def save_config(self, config=None):
        """Save configuration to file"""
        if config is None:
            config = self.config
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=4)
    
    def send_email_alert(self, product_name, current_price, previous_price, url, drop_percentage):
        """Send email alert when price drops"""
        if not self.config['email']['enabled']:
            return False
        
        try:
            sender_email = self.config['email']['sender_email']
            sender_password = self.config['email']['sender_password']
            recipient_email = self.config['email']['recipient_email']
            
            if not sender_email or not sender_password or not recipient_email:
                print("Email configuration incomplete. Please check alert_config.json")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = f"Price Drop Alert: {product_name}"
            
            body = f"""
Price Drop Alert!

Product: {product_name}
Current Price: ₹{current_price:,.2f}
Previous Price: ₹{previous_price:,.2f}
Price Drop: {drop_percentage:.2f}%
Savings: ₹{previous_price - current_price:,.2f}

Product URL: {url}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This is an automated alert from your price tracker.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.config['email']['smtp_server'], self.config['email']['smtp_port'])
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            server.quit()
            
            print(f"Email alert sent for {product_name}")
            return True
        except Exception as e:
            print(f"Error sending email alert: {e}")
            return False
    
    def send_telegram_alert(self, product_name, current_price, previous_price, url, drop_percentage):
        """Send Telegram alert when price drops"""
        if not self.config['telegram']['enabled']:
            return False
        
        try:
            bot_token = self.config['telegram']['bot_token']
            chat_id = self.config['telegram']['chat_id']
            
            if not bot_token or not chat_id:
                print("Telegram configuration incomplete. Please check alert_config.json")
                return False
            
            message = f"""
🔔 *Price Drop Alert!*

*Product:* {product_name}
*Current Price:* ₹{current_price:,.2f}
*Previous Price:* ₹{previous_price:,.2f}
*Price Drop:* {drop_percentage:.2f}%
*Savings:* ₹{previous_price - current_price:,.2f}

[View Product]({url})

_Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_
            """
            
            url_telegram = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': False
            }
            
            response = requests.post(url_telegram, data=data)
            if response.status_code == 200:
                print(f"Telegram alert sent for {product_name}")
                return True
            else:
                print(f"Error sending Telegram alert: {response.text}")
                return False
        except Exception as e:
            print(f"Error sending Telegram alert: {e}")
            return False
    
    def send_desktop_notification(self, product_name, current_price, previous_price, drop_percentage):
        """Send desktop notification when price drops"""
        if not self.config['desktop']['enabled']:
            return False
        
        if not DESKTOP_NOTIF_AVAILABLE:
            return False
        
        try:
            toaster = ToastNotifier()
            title = f"Price Drop: {product_name}"
            message = f"Price dropped by {drop_percentage:.2f}%!\nCurrent: ₹{current_price:,.2f}\nPrevious: ₹{previous_price:,.2f}"
            toaster.show_toast(title, message, duration=10, threaded=True)
            print(f"Desktop notification sent for {product_name}")
            return True
        except Exception as e:
            print(f"Error sending desktop notification: {e}")
            return False
    
    def check_and_send_alerts(self, product_name, current_price, previous_price, url, alert_threshold=None):
        """Check if price drop meets threshold and send alerts"""
        if previous_price is None:
            return  # No previous price to compare
        
        drop_percentage = ((previous_price - current_price) / previous_price) * 100
        
        if alert_threshold is None:
            alert_threshold = self.config['default_alert_threshold']
        
        # Only alert if price dropped (not increased)
        if drop_percentage < 0:
            return  # Price increased, no alert
        
        # Check if drop meets threshold
        if drop_percentage >= alert_threshold:
            print(f"\n🚨 Alert triggered for {product_name}: {drop_percentage:.2f}% price drop!")
            
            # Send all enabled alerts
            self.send_email_alert(product_name, current_price, previous_price, url, drop_percentage)
            self.send_telegram_alert(product_name, current_price, previous_price, url, drop_percentage)
            self.send_desktop_notification(product_name, current_price, previous_price, drop_percentage)
            
            return True
        
        return False

