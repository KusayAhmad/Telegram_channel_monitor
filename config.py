"""
Central project settings
Reads settings from .env file and provides them to other files
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')


class Config:
    """Application configuration"""
    
    # Telegram API
    API_ID = int(os.getenv('API_ID', 0))
    API_HASH = os.getenv('API_HASH', '')
    SESSION_NAME = os.getenv('SESSION_NAME', 'my_account')
    NOTIFY_USER_ID = int(os.getenv('NOTIFY_USER_ID', 0))
    
    # Notification destination (can be username like @channel or numeric ID)
    # If not set, defaults to NOTIFY_USER_ID (Saved Messages)
    NOTIFY_CHAT_ID = os.getenv('NOTIFY_CHAT_ID', '')
    
    # Bot
    BOT_TOKEN = os.getenv('BOT_TOKEN', '')
    
    # Discord
    DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL', '')
    
    # Email
    EMAIL_SMTP_SERVER = os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
    EMAIL_SMTP_PORT = int(os.getenv('EMAIL_SMTP_PORT', 587))
    EMAIL_USERNAME = os.getenv('EMAIL_USERNAME', '')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
    EMAIL_TO = os.getenv('EMAIL_TO', '')
    
    # Dashboard
    DASHBOARD_SECRET_KEY = os.getenv('DASHBOARD_SECRET_KEY', 'change_this_secret')
    DASHBOARD_PORT = int(os.getenv('DASHBOARD_PORT', 5000))
    DASHBOARD_HOST = os.getenv('DASHBOARD_HOST', '127.0.0.1')
    
    # Database
    DATABASE_PATH = BASE_DIR / 'data' / 'channel_monitor.db'
    
    # Logs
    LOG_DIR = BASE_DIR / 'logs'
    LOG_FILE = LOG_DIR / 'monitor.log'
    
    # Exports
    EXPORT_DIR = BASE_DIR / 'exports'
    
    @classmethod
    def validate(cls):
        """Validate basic configuration settings"""
        errors = []
        
        if not cls.API_ID:
            errors.append("API_ID is not set")
        if not cls.API_HASH:
            errors.append("API_HASH is not set")
        if not cls.NOTIFY_USER_ID:
            errors.append("NOTIFY_USER_ID is not set")
            
        return errors
    
    @classmethod
    def ensure_directories(cls):
        """Create required directories"""
        cls.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)
        cls.EXPORT_DIR.mkdir(parents=True, exist_ok=True)


# Create instance for direct use
config = Config()
