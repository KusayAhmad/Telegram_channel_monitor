"""
نظام التسجيل (Logging) للمشروع
يوفر تسجيل ملون للـ console وتسجيل للملفات
"""
import logging
import sys
from datetime import datetime
from pathlib import Path

try:
    import colorlog
    HAS_COLORLOG = True
except ImportError:
    HAS_COLORLOG = False

from config import config


def setup_logger(name: str = 'channel_monitor', level: int = logging.INFO) -> logging.Logger:
    """
    Setup and return a configured logger
    
    Args:
        name: Logger name
        level: Logging level
    
    Returns:
        logging.Logger: Configured logger
    """
    logger = logging.getLogger(name)
    
    # Avoid adding duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Message format
    log_format = '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    if HAS_COLORLOG:
        color_format = '%(log_color)s%(asctime)s | %(levelname)-8s | %(name)s | %(message)s%(reset)s'
        console_formatter = colorlog.ColoredFormatter(
            color_format,
            datefmt=date_format,
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red',
            }
        )
    else:
        console_formatter = logging.Formatter(log_format, datefmt=date_format)
    
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File Handler
    try:
        config.ensure_directories()
        file_handler = logging.FileHandler(
            config.LOG_FILE,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(log_format, datefmt=date_format)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Failed to create log file: {e}")
    
    return logger


# Default logger for direct use
logger = setup_logger()


class MonitorLogger:
    """Helper class for logging monitoring events"""
    
    def __init__(self, name: str = 'channel_monitor'):
        self.logger = setup_logger(name)
    
    def keyword_found(self, keyword: str, channel: str, message_id: int):
        """Log keyword found event"""
        self.logger.info(f"🎯 كلمة مفتاحية '{keyword}' في @{channel} (رسالة #{message_id})")
    
    def notification_sent(self, method: str, destination: str):
        """Log notification sent event"""
        self.logger.info(f"📤 إشعار {method} أُرسل إلى {destination}")
    
    def notification_failed(self, method: str, error: str):
        """Log notification failure"""
        self.logger.error(f"❌ فشل إرسال {method}: {error}")
    
    def monitor_started(self, channels_count: int, keywords_count: int):
        """Log monitoring start"""
        self.logger.info(f"🚀 بدأت المراقبة: {channels_count} قناة، {keywords_count} كلمة")
    
    def monitor_stopped(self):
        """Log monitoring stop"""
        self.logger.info("🛑 توقفت المراقبة")
    
    def error(self, message: str, exc_info: bool = False):
        """Log error"""
        self.logger.error(message, exc_info=exc_info)
    
    def warning(self, message: str):
        """Log warning"""
        self.logger.warning(message)
    
    def info(self, message: str):
        """Log info"""
        self.logger.info(message)
    
    def debug(self, message: str):
        """Log debug"""
        self.logger.debug(message)


# Default instance
monitor_logger = MonitorLogger()
