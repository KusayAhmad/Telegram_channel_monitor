"""
Telegram bot for controlling the monitoring system
Allows management of channels, keywords, and statistics
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
    """Bot for controlling the monitoring system"""
    
    def __init__(self, client: Client):
        self.client = client
        self.admin_id = config.NOTIFY_USER_ID
        self.monitor_instance = None  # Will be set later
        self._setup_handlers()
    
    def set_monitor_instance(self, monitor):
        """Set the monitor instance for reload command"""
        self.monitor_instance = monitor
    
    def _setup_handlers(self):
        """Setup command handlers"""
        # Basic commands
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
        
        # Channel management
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
        
        # Keyword management
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
        
        # Statistics and export
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
        
        # System control
        self.client.add_handler(MessageHandler(
            self._cmd_reload,
            filters.command("reload") & filters.user(self.admin_id)
        ))
        
        # Callback Query Handler
        self.client.add_handler(CallbackQueryHandler(
            self._callback_handler
        ))
    
    # ================== Basic Commands ==================
    
    async def _cmd_start(self, client: Client, message: Message):
        """Start command"""
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📢 Channels", callback_data="menu_channels"),
                InlineKeyboardButton("🔑 Keywords", callback_data="menu_keywords")
            ],
            [
                InlineKeyboardButton("📊 Statistics", callback_data="menu_stats"),
                InlineKeyboardButton("📋 Recent Messages", callback_data="menu_recent")
            ],
            [
                InlineKeyboardButton("ℹ️ Help", callback_data="menu_help")
            ]
        ])
        
        await message.reply(
            "🤖 **Welcome to Channel Monitor Bot!**\n\n"
            "Use the buttons below or type /help to see available commands.",
            reply_markup=keyboard
        )
    
    async def _cmd_help(self, client: Client, message: Message):
        """Help command"""
        help_text = """
📚 **Available Commands:**

**Basic Commands:**
• /start - Main menu
• /help - Show help
• /status - System status

**Channel Management:**
• /channels - Show monitored channels
• /addchannel @username - Add channel
• /removechannel @username - Remove channel

**Keyword Management:**
• /keywords - Show keywords
• /addkeyword word - Add keyword
• /removekeyword word - Remove keyword

**Statistics:**
• /stats - General statistics
• /recent - Recently detected messages
• /export - Export data
"""
        await message.reply(help_text)
    
    async def _cmd_status(self, client: Client, message: Message):
        """Display system status"""
        channels = await db.get_channels()
        keywords = await db.get_keywords()
        stats = await db.get_stats(days=1)
        
        status_text = f"""
📊 **System Status:**

🟢 **Status:** Running
📢 **Monitored Channels:** {len(channels)}
🔑 **Keywords:** {len(keywords)}
📨 **Today's Messages:** {stats['today_messages']}
📈 **Total Messages:** {stats['total_messages']}
"""
        await message.reply(status_text)
    
    # ================== Channel Management ==================
    
    async def _cmd_channels(self, client: Client, message: Message):
        """Display monitored channels"""
        channels = await db.get_channels()
        
        if not channels:
            await message.reply("📢 No channels are currently being monitored.\n\nUse /addchannel @username to add a channel.")
            return
        
        text = "📢 **Monitored Channels:**\n\n"
        for i, ch in enumerate(channels, 1):
            status = "🟢" if ch['is_active'] else "🔴"
            text += f"{i}. {status} @{ch['username'] or ch['channel_id']}\n"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add Channel", callback_data="add_channel")]
        ])
        
        await message.reply(text, reply_markup=keyboard)
    
    async def _cmd_add_channel(self, client: Client, message: Message):
        """Add a new channel"""
        args = message.text.split(maxsplit=1)
        
        if len(args) < 2:
            await message.reply("⚠️ **Usage:** /addchannel @username\n\nExample: `/addchannel @TechNews`")
            return
        
        channel = args[1].strip().lstrip('@')
        
        try:
            # Attempt to get channel information
            chat = await client.get_chat(channel)
            await db.add_channel(
                channel_id=str(chat.id),
                username=chat.username,
                title=chat.title
            )
            
            await message.reply(
                f"✅ Channel added successfully!\n\n"
                f"📢 **Channel:** @{chat.username}\n"
                f"📝 **Name:** {chat.title}"
            )
            monitor_logger.info(f"Channel added: @{channel}")
            
        except Exception as e:
            await message.reply(f"❌ Failed to add channel: {str(e)}")
    
    async def _cmd_remove_channel(self, client: Client, message: Message):
        """Remove a channel"""
        args = message.text.split(maxsplit=1)
        
        if len(args) < 2:
            await message.reply("⚠️ **Usage:** /removechannel @username")
            return
        
        channel = args[1].strip().lstrip('@')
        
        # Search for the channel in the database
        channels = await db.get_channels(active_only=False)
        found = None
        for ch in channels:
            if ch['username'] == channel or ch['channel_id'] == channel:
                found = ch
                break
        
        if found:
            await db.remove_channel(found['channel_id'])
            await message.reply(f"✅ Channel @{channel} removed successfully!")
            monitor_logger.info(f"Channel removed: @{channel}")
        else:
            await message.reply(f"❌ Channel @{channel} not found")
    
    # ================== Keyword Management ==================
    
    async def _cmd_keywords(self, client: Client, message: Message):
        """Display keywords"""
        keywords = await db.get_keywords()
        
        if not keywords:
            await message.reply("🔑 No keywords found.\n\nUse /addkeyword word to add a keyword.")
            return
        
        text = "🔑 **Keywords:**\n\n"
        for i, kw in enumerate(keywords, 1):
            status = "🟢" if kw['is_active'] else "🔴"
            regex_tag = " (regex)" if kw['is_regex'] else ""
            text += f"{i}. {status} `{kw['keyword']}`{regex_tag}\n"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add Keyword", callback_data="add_keyword")]
        ])
        
        await message.reply(text, reply_markup=keyboard)
    
    async def _cmd_add_keyword(self, client: Client, message: Message):
        """Add a keyword"""
        args = message.text.split(maxsplit=1)
        
        if len(args) < 2:
            await message.reply(
                "⚠️ **Usage:** /addkeyword word\n\n"
                "To add regex use:\n"
                "/addkeyword regex:search_pattern"
            )
            return
        
        keyword = args[1].strip()
        is_regex = keyword.startswith("regex:")
        
        if is_regex:
            keyword = keyword[6:]  # Remove "regex:"
        
        await db.add_keyword(keyword, is_regex)
        
        await message.reply(
            f"✅ Keyword added successfully!\n\n"
            f"🔑 **Keyword:** `{keyword}`\n"
            f"🔤 **Type:** {'Regex' if is_regex else 'Normal'}"
        )
        monitor_logger.info(f"Keyword added: {keyword}")
    
    async def _cmd_remove_keyword(self, client: Client, message: Message):
        """Remove a keyword"""
        args = message.text.split(maxsplit=1)
        
        if len(args) < 2:
            await message.reply("⚠️ **Usage:** /removekeyword word")
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
            await message.reply(f"✅ Keyword `{keyword}` removed successfully!")
            monitor_logger.info(f"Keyword removed: {keyword}")
        else:
            await message.reply(f"❌ Keyword `{keyword}` not found")
    
    # ================== Statistics ==================
    
    async def _cmd_stats(self, client: Client, message: Message):
        """Display statistics"""
        stats = await db.get_stats(days=7)
        
        text = f"""
📊 **Monitoring Statistics:**

📈 **Total Messages:** {stats['total_messages']}
📅 **Today's Messages:** {stats['today_messages']}

🏆 **Most Matched Keywords:**
"""
        for i, kw in enumerate(stats['top_keywords'][:5], 1):
            text += f"  {i}. `{kw['keyword_matched']}` - {kw['count']} times\n"
        
        text += "\n📢 **Most Active Channels:**\n"
        for i, ch in enumerate(stats['top_channels'][:5], 1):
            text += f"  {i}. @{ch['channel_username']} - {ch['count']} messages\n"
        
        await message.reply(text)
    
    async def _cmd_recent(self, client: Client, message: Message):
        """Display recently detected messages"""
        messages = await db.get_detected_messages(limit=10)
        
        if not messages:
            await message.reply("📭 No messages detected yet.")
            return
        
        text = "📋 **Recently Detected Messages:**\n\n"
        
        for msg in messages:
            text += f"🔹 **Channel:** @{msg['channel_username']}\n"
            text += f"   **Keyword:** `{msg['keyword_matched']}`\n"
            text += f"   **Time:** {msg['detected_at']}\n"
            preview = (msg['message_text'] or "")[:100]
            if preview:
                text += f"   **Content:** {preview}...\n"
            text += "\n"
        
        await message.reply(text)
    
    async def _cmd_export(self, client: Client, message: Message):
        """Export data"""
        from exporter import DataExporter
        
        exporter = DataExporter()
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📊 CSV", callback_data="export_csv"),
                InlineKeyboardButton("📋 JSON", callback_data="export_json")
            ]
        ])
        
        await message.reply(
            "📤 **Choose export format:**",
            reply_markup=keyboard
        )
    
    # ================== Callback Handler ==================
    
    async def _callback_handler(self, client: Client, callback: CallbackQuery):
        """Handle button clicks"""
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
        """Execute export"""
        from exporter import DataExporter
        
        await callback.message.edit_text("⏳ Exporting...")
        
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
                caption=f"📤 Exported {len(messages)} messages"
            )
        else:
            await callback.message.edit_text("❌ Export failed")
    
    # ================== System Control ==================
    
    async def _cmd_reload(self, client: Client, message: Message):
        """Reload configuration"""
        if not self.monitor_instance:
            await message.reply("❌ Cannot reload - system not connected")
            return
        
        try:
            await message.reply("⏳ Reloading configuration...")
            await self.monitor_instance.reload_config()
            
            channels_count = len(self.monitor_instance.monitored_channels)
            keywords_count = len(self.monitor_instance.search_engine.patterns)
            
            await message.reply(
                f"✅ Configuration reloaded successfully!\n\n"
                f"📢 Active Channels: {channels_count}\n"
                f"🔑 Keywords: {keywords_count}"
            )
        except Exception as e:
            await message.reply(f"❌ Reload error: {str(e)}")


# Helper function to create the bot
def setup_bot(client: Client, monitor=None) -> MonitorBot:
    """Create and setup the bot"""
    bot = MonitorBot(client)
    if monitor:
        bot.set_monitor_instance(monitor)
    return bot
