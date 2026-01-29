"""
إعدادات المشروع المركزية
يقرأ الإعدادات من ملف .env ويوفرها لباقي الملفات
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# تحميل متغيرات البيئة
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')


class Config:
    """إعدادات التطبيق"""
    
    # Telegram API
    API_ID = int(os.getenv('API_ID', 0))
    API_HASH = os.getenv('API_HASH', '')
    SESSION_NAME = os.getenv('SESSION_NAME', 'my_account')
    NOTIFY_USER_ID = int(os.getenv('NOTIFY_USER_ID', 0))
    
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
        """التحقق من صحة الإعدادات الأساسية"""
        errors = []
        
        if not cls.API_ID:
            errors.append("API_ID غير محدد")
        if not cls.API_HASH:
            errors.append("API_HASH غير محدد")
        if not cls.NOTIFY_USER_ID:
            errors.append("NOTIFY_USER_ID غير محدد")
            
        return errors
    
    @classmethod
    def ensure_directories(cls):
        """إنشاء المجلدات المطلوبة"""
        cls.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)
        cls.EXPORT_DIR.mkdir(parents=True, exist_ok=True)


# إنشاء instance للاستخدام المباشر
config = Config()
