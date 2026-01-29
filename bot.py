"""
بوت تيليغرام للتحكم في نظام المراقبة
يتيح إدارة القنوات والكلمات المفتاحية والإحصائيات
"""
import asyncio
from pyrogram import Client, filters
from pyrogram.types import (
    Message, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    CallbackQuery
)
from pyrogram.handlers import MessageHandler, CallbackQueryHandler

from config import config
from database import db
from logger import monitor_logger


class MonitorBot:
    """بوت التحكم في نظام المراقبة"""
    
    def __init__(self, client: Client):
        self.client = client
        self.admin_id = config.NOTIFY_USER_ID
        self._setup_handlers()
    
    def _setup_handlers(self):
        """إعداد معالجات الأوامر"""
        # الأوامر الأساسية
        self.client.add_handler(MessageHandler(
            self._cmd_start, 
            filters.command("start") & filters.user(self.admin_id)
        ))
        self.client.add_handler(MessageHandler(
            self._cmd_help,
            filters.command("help") & filters.user(self.admin_id)
        ))
        self.client.add_handler(MessageHandler(
            self._cmd_status,
            filters.command("status") & filters.user(self.admin_id)
        ))
        
        # إدارة القنوات
        self.client.add_handler(MessageHandler(
            self._cmd_channels,
            filters.command("channels") & filters.user(self.admin_id)
        ))
        self.client.add_handler(MessageHandler(
            self._cmd_add_channel,
            filters.command("addchannel") & filters.user(self.admin_id)
        ))
        self.client.add_handler(MessageHandler(
            self._cmd_remove_channel,
            filters.command("removechannel") & filters.user(self.admin_id)
        ))
        
        # إدارة الكلمات
        self.client.add_handler(MessageHandler(
            self._cmd_keywords,
            filters.command("keywords") & filters.user(self.admin_id)
        ))
        self.client.add_handler(MessageHandler(
            self._cmd_add_keyword,
            filters.command("addkeyword") & filters.user(self.admin_id)
        ))
        self.client.add_handler(MessageHandler(
            self._cmd_remove_keyword,
            filters.command("removekeyword") & filters.user(self.admin_id)
        ))
        
        # الإحصائيات والتصدير
        self.client.add_handler(MessageHandler(
            self._cmd_stats,
            filters.command("stats") & filters.user(self.admin_id)
        ))
        self.client.add_handler(MessageHandler(
            self._cmd_recent,
            filters.command("recent") & filters.user(self.admin_id)
        ))
        self.client.add_handler(MessageHandler(
            self._cmd_export,
            filters.command("export") & filters.user(self.admin_id)
        ))
        
        # Callback Query Handler
        self.client.add_handler(CallbackQueryHandler(
            self._callback_handler
        ))
    
    # ================== الأوامر الأساسية ==================
    
    async def _cmd_start(self, client: Client, message: Message):
        """أمر البداية"""
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📢 القنوات", callback_data="menu_channels"),
                InlineKeyboardButton("🔑 الكلمات", callback_data="menu_keywords")
            ],
            [
                InlineKeyboardButton("📊 الإحصائيات", callback_data="menu_stats"),
                InlineKeyboardButton("📋 آخر الرسائل", callback_data="menu_recent")
            ],
            [
                InlineKeyboardButton("ℹ️ المساعدة", callback_data="menu_help")
            ]
        ])
        
        await message.reply(
            "🤖 **مرحباً بك في بوت مراقبة القنوات!**\n\n"
            "استخدم الأزرار أدناه أو اكتب /help لرؤية الأوامر المتاحة.",
            reply_markup=keyboard
        )
    
    async def _cmd_help(self, client: Client, message: Message):
        """أمر المساعدة"""
        help_text = """
📚 **قائمة الأوامر المتاحة:**

**الأوامر الأساسية:**
• /start - القائمة الرئيسية
• /help - عرض المساعدة
• /status - حالة النظام

**إدارة القنوات:**
• /channels - عرض القنوات المُراقبة
• /addchannel @username - إضافة قناة
• /removechannel @username - حذف قناة

**إدارة الكلمات المفتاحية:**
• /keywords - عرض الكلمات
• /addkeyword كلمة - إضافة كلمة
• /removekeyword كلمة - حذف كلمة

**الإحصائيات:**
• /stats - إحصائيات عامة
• /recent - آخر الرسائل المكتشفة
• /export - تصدير البيانات
"""
        await message.reply(help_text)
    
    async def _cmd_status(self, client: Client, message: Message):
        """عرض حالة النظام"""
        channels = await db.get_channels()
        keywords = await db.get_keywords()
        stats = await db.get_stats(days=1)
        
        status_text = f"""
📊 **حالة النظام:**

🟢 **الحالة:** يعمل
📢 **القنوات المُراقبة:** {len(channels)}
🔑 **الكلمات المفتاحية:** {len(keywords)}
📨 **رسائل اليوم:** {stats['today_messages']}
📈 **إجمالي الرسائل:** {stats['total_messages']}
"""
        await message.reply(status_text)
    
    # ================== إدارة القنوات ==================
    
    async def _cmd_channels(self, client: Client, message: Message):
        """عرض القنوات المُراقبة"""
        channels = await db.get_channels()
        
        if not channels:
            await message.reply("📢 لا توجد قنوات مُراقبة حالياً.\n\nاستخدم /addchannel @username لإضافة قناة.")
            return
        
        text = "📢 **القنوات المُراقبة:**\n\n"
        for i, ch in enumerate(channels, 1):
            status = "🟢" if ch['is_active'] else "🔴"
            text += f"{i}. {status} @{ch['username'] or ch['channel_id']}\n"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ إضافة قناة", callback_data="add_channel")]
        ])
        
        await message.reply(text, reply_markup=keyboard)
    
    async def _cmd_add_channel(self, client: Client, message: Message):
        """إضافة قناة جديدة"""
        args = message.text.split(maxsplit=1)
        
        if len(args) < 2:
            await message.reply("⚠️ **الاستخدام:** /addchannel @username\n\nمثال: `/addchannel @TechNews`")
            return
        
        channel = args[1].strip().lstrip('@')
        
        try:
            # محاولة الحصول على معلومات القناة
            chat = await client.get_chat(channel)
            await db.add_channel(
                channel_id=str(chat.id),
                username=chat.username,
                title=chat.title
            )
            
            await message.reply(
                f"✅ تمت إضافة القناة بنجاح!\n\n"
                f"📢 **القناة:** @{chat.username}\n"
                f"📝 **الاسم:** {chat.title}"
            )
            monitor_logger.info(f"تمت إضافة قناة: @{channel}")
            
        except Exception as e:
            await message.reply(f"❌ فشل في إضافة القناة: {str(e)}")
    
    async def _cmd_remove_channel(self, client: Client, message: Message):
        """حذف قناة"""
        args = message.text.split(maxsplit=1)
        
        if len(args) < 2:
            await message.reply("⚠️ **الاستخدام:** /removechannel @username")
            return
        
        channel = args[1].strip().lstrip('@')
        
        # البحث عن القناة في قاعدة البيانات
        channels = await db.get_channels(active_only=False)
        found = None
        for ch in channels:
            if ch['username'] == channel or ch['channel_id'] == channel:
                found = ch
                break
        
        if found:
            await db.remove_channel(found['channel_id'])
            await message.reply(f"✅ تم حذف القناة @{channel} بنجاح!")
            monitor_logger.info(f"تم حذف قناة: @{channel}")
        else:
            await message.reply(f"❌ لم يتم العثور على القناة @{channel}")
    
    # ================== إدارة الكلمات ==================
    
    async def _cmd_keywords(self, client: Client, message: Message):
        """عرض الكلمات المفتاحية"""
        keywords = await db.get_keywords()
        
        if not keywords:
            await message.reply("🔑 لا توجد كلمات مفتاحية.\n\nاستخدم /addkeyword كلمة لإضافة كلمة.")
            return
        
        text = "🔑 **الكلمات المفتاحية:**\n\n"
        for i, kw in enumerate(keywords, 1):
            status = "🟢" if kw['is_active'] else "🔴"
            regex_tag = " (regex)" if kw['is_regex'] else ""
            text += f"{i}. {status} `{kw['keyword']}`{regex_tag}\n"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ إضافة كلمة", callback_data="add_keyword")]
        ])
        
        await message.reply(text, reply_markup=keyboard)
    
    async def _cmd_add_keyword(self, client: Client, message: Message):
        """إضافة كلمة مفتاحية"""
        args = message.text.split(maxsplit=1)
        
        if len(args) < 2:
            await message.reply(
                "⚠️ **الاستخدام:** /addkeyword كلمة\n\n"
                "لإضافة regex استخدم:\n"
                "/addkeyword regex:نمط_البحث"
            )
            return
        
        keyword = args[1].strip()
        is_regex = keyword.startswith("regex:")
        
        if is_regex:
            keyword = keyword[6:]  # إزالة "regex:"
        
        await db.add_keyword(keyword, is_regex)
        
        await message.reply(
            f"✅ تمت إضافة الكلمة بنجاح!\n\n"
            f"🔑 **الكلمة:** `{keyword}`\n"
            f"🔤 **النوع:** {'Regex' if is_regex else 'عادية'}"
        )
        monitor_logger.info(f"تمت إضافة كلمة: {keyword}")
    
    async def _cmd_remove_keyword(self, client: Client, message: Message):
        """حذف كلمة مفتاحية"""
        args = message.text.split(maxsplit=1)
        
        if len(args) < 2:
            await message.reply("⚠️ **الاستخدام:** /removekeyword كلمة")
            return
        
        keyword = args[1].strip()
        
        keywords = await db.get_keywords(active_only=False)
        found = None
        for kw in keywords:
            if kw['keyword'] == keyword:
                found = kw
                break
        
        if found:
            await db.remove_keyword(found['id'])
            await message.reply(f"✅ تم حذف الكلمة `{keyword}` بنجاح!")
            monitor_logger.info(f"تم حذف كلمة: {keyword}")
        else:
            await message.reply(f"❌ لم يتم العثور على الكلمة `{keyword}`")
    
    # ================== الإحصائيات ==================
    
    async def _cmd_stats(self, client: Client, message: Message):
        """عرض الإحصائيات"""
        stats = await db.get_stats(days=7)
        
        text = f"""
📊 **إحصائيات المراقبة:**

📈 **إجمالي الرسائل:** {stats['total_messages']}
📅 **رسائل اليوم:** {stats['today_messages']}

🏆 **أكثر الكلمات تطابقاً:**
"""
        for i, kw in enumerate(stats['top_keywords'][:5], 1):
            text += f"  {i}. `{kw['keyword_matched']}` - {kw['count']} مرة\n"
        
        text += "\n📢 **أكثر القنوات نشاطاً:**\n"
        for i, ch in enumerate(stats['top_channels'][:5], 1):
            text += f"  {i}. @{ch['channel_username']} - {ch['count']} رسالة\n"
        
        await message.reply(text)
    
    async def _cmd_recent(self, client: Client, message: Message):
        """عرض آخر الرسائل المكتشفة"""
        messages = await db.get_detected_messages(limit=10)
        
        if not messages:
            await message.reply("📭 لا توجد رسائل مكتشفة بعد.")
            return
        
        text = "📋 **آخر الرسائل المكتشفة:**\n\n"
        
        for msg in messages:
            text += f"🔹 **القناة:** @{msg['channel_username']}\n"
            text += f"   **الكلمة:** `{msg['keyword_matched']}`\n"
            text += f"   **الوقت:** {msg['detected_at']}\n"
            preview = (msg['message_text'] or "")[:100]
            if preview:
                text += f"   **المحتوى:** {preview}...\n"
            text += "\n"
        
        await message.reply(text)
    
    async def _cmd_export(self, client: Client, message: Message):
        """تصدير البيانات"""
        from exporter import DataExporter
        
        exporter = DataExporter()
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📊 CSV", callback_data="export_csv"),
                InlineKeyboardButton("📋 JSON", callback_data="export_json")
            ]
        ])
        
        await message.reply(
            "📤 **اختر صيغة التصدير:**",
            reply_markup=keyboard
        )
    
    # ================== Callback Handler ==================
    
    async def _callback_handler(self, client: Client, callback: CallbackQuery):
        """معالجة الضغط على الأزرار"""
        data = callback.data
        
        if data == "menu_channels":
            await self._cmd_channels(client, callback.message)
        elif data == "menu_keywords":
            await self._cmd_keywords(client, callback.message)
        elif data == "menu_stats":
            await self._cmd_stats(client, callback.message)
        elif data == "menu_recent":
            await self._cmd_recent(client, callback.message)
        elif data == "menu_help":
            await self._cmd_help(client, callback.message)
        elif data == "export_csv":
            await self._do_export(client, callback, "csv")
        elif data == "export_json":
            await self._do_export(client, callback, "json")
        
        await callback.answer()
    
    async def _do_export(self, client: Client, callback: CallbackQuery, format: str):
        """تنفيذ التصدير"""
        from exporter import DataExporter
        
        await callback.message.edit_text("⏳ جاري التصدير...")
        
        exporter = DataExporter()
        messages = await db.get_detected_messages(limit=10000)
        
        if format == "csv":
            file_path = await exporter.export_to_csv(messages)
        else:
            file_path = await exporter.export_to_json(messages)
        
        if file_path and file_path.exists():
            await client.send_document(
                callback.message.chat.id,
                document=str(file_path),
                caption=f"📤 تم تصدير {len(messages)} رسالة"
            )
        else:
            await callback.message.edit_text("❌ فشل في التصدير")


# دالة مساعدة لإنشاء البوت
def setup_bot(client: Client) -> MonitorBot:
    """إنشاء وإعداد البوت"""
    return MonitorBot(client)
