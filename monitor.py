"""
نظام مراقبة قنوات تيليغرام - النسخة المطورة
=========================================
يراقب القنوات المحددة ويبحث عن الكلمات المفتاحية
مع دعم قاعدة البيانات، الإشعارات المتعددة، والبحث المتقدم
"""
import asyncio
import sys
from typing import List, Set

from pyrogram import Client, filters
from pyrogram.types import Message

from config import config, Config
from database import db
from logger import monitor_logger, MonitorLogger
from notifications import notification_manager, NotificationMessage
from search_engine import SearchEngine, MatchType, parse_keyword_string
from scheduler import auto_restart, graceful_shutdown, schedule_manager
from bot import setup_bot


class ChannelMonitor:
    """نظام مراقبة القنوات الرئيسي"""
    
    def __init__(self):
        self.client: Client = None
        self.search_engine = SearchEngine()
        self.monitored_channels: Set[str] = set()
        self.is_running = False
        self.logger = MonitorLogger('monitor')
    
    async def initialize(self):
        """تهيئة النظام"""
        # التحقق من الإعدادات
        errors = Config.validate()
        if errors:
            for error in errors:
                self.logger.error(f"خطأ في الإعدادات: {error}")
            raise ValueError("إعدادات غير مكتملة - راجع ملف .env")
        
        # إنشاء المجلدات
        Config.ensure_directories()
        
        # الاتصال بقاعدة البيانات
        await db.connect()
        self.logger.info("تم الاتصال بقاعدة البيانات")
        
        # تحميل الكلمات والقنوات من قاعدة البيانات
        await self._load_keywords()
        await self._load_channels()
        
        # إنشاء عميل Telegram
        self.client = Client(
            config.SESSION_NAME,
            api_id=config.API_ID,
            api_hash=config.API_HASH
        )
        
        # إعداد معالج الرسائل
        self._setup_handlers()
        
        # إعداد نظام الإشعارات
        notification_manager.setup_all(self.client)
        
        # إعداد البوت
        setup_bot(self.client)
        
        self.logger.info("تم تهيئة النظام بنجاح")
    
    async def _load_keywords(self):
        """تحميل الكلمات من قاعدة البيانات"""
        keywords = await db.get_keywords(active_only=True)
        
        self.search_engine.clear_patterns()
        
        for kw in keywords:
            if kw['is_regex']:
                self.search_engine.add_regex(kw['keyword'])
            else:
                self.search_engine.add_keyword(kw['keyword'])
        
        self.logger.info(f"تم تحميل {len(keywords)} كلمة مفتاحية")
    
    async def _load_channels(self):
        """تحميل القنوات من قاعدة البيانات"""
        channels = await db.get_channels(active_only=True)
        
        self.monitored_channels.clear()
        
        for ch in channels:
            if ch['username']:
                self.monitored_channels.add(ch['username'])
            self.monitored_channels.add(ch['channel_id'])
        
        self.logger.info(f"تم تحميل {len(channels)} قناة للمراقبة")
    
    def _setup_handlers(self):
        """إعداد معالجات الرسائل"""
        @self.client.on_message(filters.channel)
        async def handle_channel_message(client: Client, message: Message):
            await self._process_message(message)
    
    async def _process_message(self, message: Message):
        """معالجة رسالة واردة"""
        try:
            # التحقق من القناة
            chat = message.chat
            channel_id = str(chat.id)
            channel_username = chat.username or ""
            
            # التحقق إذا كانت القناة مُراقبة
            if not self._is_monitored_channel(channel_id, channel_username):
                return
            
            # استخراج النص
            text = message.text or message.caption or ""
            if not text:
                return
            
            # البحث عن الكلمات
            matches = self.search_engine.search(text)
            
            if not matches:
                return
            
            # معالجة كل تطابق
            for match in matches:
                await self._handle_match(message, match.pattern, text)
        
        except Exception as e:
            self.logger.error(f"خطأ في معالجة الرسالة: {e}", exc_info=True)
    
    def _is_monitored_channel(self, channel_id: str, username: str) -> bool:
        """التحقق إذا كانت القناة مُراقبة"""
        if channel_id in self.monitored_channels:
            return True
        if username and username in self.monitored_channels:
            return True
        if username and f"@{username}" in self.monitored_channels:
            return True
        return False
    
    async def _handle_match(self, message: Message, keyword: str, text: str):
        """معالجة تطابق"""
        channel_id = str(message.chat.id)
        channel_username = message.chat.username or message.chat.title or ""
        message_id = message.id
        
        # التحقق من التكرار
        if await db.is_message_detected(message_id, channel_id, keyword):
            return
        
        # إنشاء رابط الرسالة
        message_link = f"https://t.me/{channel_username}/{message_id}" if channel_username else None
        
        # حفظ في قاعدة البيانات
        db_id = await db.add_detected_message(
            message_id=message_id,
            channel_id=channel_id,
            channel_username=channel_username,
            keyword_matched=keyword,
            message_text=text[:2000],
            message_link=message_link
        )
        
        # تسجيل
        self.logger.keyword_found(keyword, channel_username, message_id)
        
        # إرسال الإشعارات
        await notification_manager.notify_keyword_found(
            keyword=keyword,
            channel=channel_username,
            message_text=text,
            message_link=message_link
        )
        
        # تحديث حالة الإشعار
        if db_id:
            await db.mark_notification_sent(db_id)
    
    async def reload_config(self):
        """إعادة تحميل الإعدادات"""
        await self._load_keywords()
        await self._load_channels()
        self.logger.info("تم إعادة تحميل الإعدادات")
    
    async def start(self):
        """بدء المراقبة"""
        if self.is_running:
            return
        
        self.is_running = True
        channels_count = len(self.monitored_channels)
        keywords_count = len(self.search_engine.patterns)
        
        self.logger.monitor_started(channels_count, keywords_count)
        
        await self.client.start()
        
        # عرض معلومات الحساب
        me = await self.client.get_me()
        self.logger.info(f"تم تسجيل الدخول كـ: {me.first_name} (@{me.username})")
        
        # انتظار الإيقاف
        await graceful_shutdown.wait_for_shutdown()
    
    async def stop(self):
        """إيقاف المراقبة"""
        if not self.is_running:
            return
        
        self.is_running = False
        self.logger.monitor_stopped()
        
        await self.client.stop()
        await db.disconnect()
    
    async def run(self):
        """التشغيل الكامل"""
        try:
            await self.initialize()
            await self.start()
        except KeyboardInterrupt:
            pass
        except Exception as e:
            self.logger.error(f"خطأ: {e}", exc_info=True)
            raise
        finally:
            await self.stop()


async def main():
    """الدالة الرئيسية"""
    monitor = ChannelMonitor()
    
    # إعداد الإيقاف الآمن
    graceful_shutdown.setup_signals()
    graceful_shutdown.add_cleanup(monitor.stop)
    
    # التشغيل مع إعادة المحاولة
    await auto_restart.run_with_restart(monitor.run)


def run_monitor():
    """نقطة الدخول"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                  📡 مراقب قنوات تيليغرام                 ║
    ║                     النسخة المطورة 2.0                    ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 إلى اللقاء!")


if __name__ == "__main__":
    run_monitor()
