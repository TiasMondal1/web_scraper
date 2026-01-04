"""
Configuration Management Module
Handles environment-based configuration and settings
"""
import os
import json
from typing import Dict, Any, Optional

class Config:
    def __init__(self, config_file='config.json', env_file='.env'):
        self.config_file = config_file
        self.env_file = env_file
        self.config = self._load_config()
        self._load_env_variables()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        default_config = {
            'database': {
                'file': 'price_history.db'
            },
            'scraper': {
                'use_selenium': False,
                'retry_count': 3,
                'timeout': 30,
                'delay_between_requests': 5
            },
            'alerts': {
                'enabled': True,
                'default_threshold': 10
            },
            'scheduler': {
                'interval_hours': 6,
                'daily_time': '09:00'
            },
            'export': {
                'directory': 'exports',
                'backup_directory': 'backups'
            },
            'logging': {
                'level': 'INFO',
                'directory': 'logs',
                'file': 'price_tracker.log'
            },
            'api': {
                'host': '0.0.0.0',
                'port': 5001,
                'debug': False
            },
            'web_dashboard': {
                'host': '0.0.0.0',
                'port': 5000,
                'debug': False
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)
                    # Merge with defaults
                    self._merge_dict(default_config, user_config)
            except Exception as e:
                print(f"Warning: Could not load config file: {e}. Using defaults.")
        
        return default_config
    
    def _merge_dict(self, base: Dict, update: Dict):
        """Recursively merge two dictionaries"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_dict(base[key], value)
            else:
                base[key] = value
    
    def _load_env_variables(self):
        """Load environment variables (override config)"""
        # Database
        if os.getenv('DB_FILE'):
            self.config['database']['file'] = os.getenv('DB_FILE')
        
        # Scraper
        if os.getenv('USE_SELENIUM'):
            self.config['scraper']['use_selenium'] = os.getenv('USE_SELENIUM').lower() == 'true'
        if os.getenv('SCRAPER_TIMEOUT'):
            self.config['scraper']['timeout'] = int(os.getenv('SCRAPER_TIMEOUT'))
        
        # API
        if os.getenv('API_HOST'):
            self.config['api']['host'] = os.getenv('API_HOST')
        if os.getenv('API_PORT'):
            self.config['api']['port'] = int(os.getenv('API_PORT'))
        
        # Web Dashboard
        if os.getenv('WEB_HOST'):
            self.config['web_dashboard']['host'] = os.getenv('WEB_HOST')
        if os.getenv('WEB_PORT'):
            self.config['web_dashboard']['port'] = int(os.getenv('WEB_PORT'))
        
        # Logging
        if os.getenv('LOG_LEVEL'):
            self.config['logging']['level'] = os.getenv('LOG_LEVEL')
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        
        Example: config.get('database.file') -> 'price_history.db'
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any):
        """Set configuration value using dot notation"""
        keys = key_path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    def save(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Get full configuration as dictionary"""
        return self.config.copy()

# Global config instance
_config = None

def get_config() -> Config:
    """Get global configuration instance"""
    global _config
    if _config is None:
        _config = Config()
    return _config

