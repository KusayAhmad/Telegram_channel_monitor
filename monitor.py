"""
Telegram Channel Monitoring System - Advanced Version
=========================================
Monitors specified channels and searches for keywords
with database support, multiple notifications, and advanced search
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
    """Main channel monitoring system"""
    
    def __init__(self):
        self.client: Client = None
        self.search_engine = SearchEngine()
        self.monitored_channels: Set[str] = set()
        self.is_running = False
        self.logger = MonitorLogger('monitor')
    
    async def initialize(self):
        """Initialize the system"""
        # Clean up stale session journal files
        import os
        session_journal = f"{config.SESSION_NAME}.session-journal"
        if os.path.exists(session_journal):
            try:
                os.remove(session_journal)
                self.logger.info("Removed stale session journal file")
            except Exception as e:
                self.logger.warning(f"Could not remove session journal: {e}")
        
        # Validate configuration
        errors = Config.validate()
        if errors:
            for error in errors:
                self.logger.error(f"Configuration error: {error}")
            raise ValueError("Incomplete configuration - check .env file")
        
        # Create directories
        Config.ensure_directories()
        
        # Connect to database
        await db.connect()
        self.logger.info("Connected to database")
        
        # Load keywords and channels from database
        await self._load_keywords()
        await self._load_channels()
        
        # Create Telegram client
        self.client = Client(
            config.SESSION_NAME,
            api_id=config.API_ID,
            api_hash=config.API_HASH
        )
        
        # Setup message handler
        self._setup_handlers()
        
        # Setup notification system
        notification_manager.setup_all(self.client)
        
        # Setup bot
        setup_bot(self.client)
        
        self.logger.info("System initialized successfully")
    
    async def _load_keywords(self):
        """Load keywords from database"""
        keywords = await db.get_keywords(active_only=True)
        
        self.search_engine.clear_patterns()
        
        for kw in keywords:
            if kw['is_regex']:
                self.search_engine.add_regex(kw['keyword'])
            else:
                self.search_engine.add_keyword(kw['keyword'])
        
        self.logger.info(f"Loaded {len(keywords)} keywords")
    
    async def _load_channels(self):
        """Load channels from database"""
        channels = await db.get_channels(active_only=True)
        
        self.monitored_channels.clear()
        
        for ch in channels:
            if ch['username']:
                self.monitored_channels.add(ch['username'])
            self.monitored_channels.add(ch['channel_id'])
        
        self.logger.info(f"Loaded {len(channels)} channels for monitoring")
    
    def _setup_handlers(self):
        """Setup message handlers"""
        @self.client.on_message(filters.channel)
        async def handle_channel_message(client: Client, message: Message):
            await self._process_message(message)
    
    async def _process_message(self, message: Message):
        """Process incoming message"""
        try:
            # Check channel
            chat = message.chat
            channel_id = str(chat.id)
            channel_username = chat.username or ""
            
            # Check if channel is monitored
            if not self._is_monitored_channel(channel_id, channel_username):
                return
            
            # Extract text
            text = message.text or message.caption or ""
            if not text:
                return
            
            # Search for keywords
            matches = self.search_engine.search(text)
            
            if not matches:
                return
            
            # Process each match
            for match in matches:
                await self._handle_match(message, match.pattern, text)
        
        except Exception as e:
            self.logger.error(f"Error processing message: {e}", exc_info=True)
    
    def _is_monitored_channel(self, channel_id: str, username: str) -> bool:
        """Check if channel is monitored"""
        if channel_id in self.monitored_channels:
            return True
        if username and username in self.monitored_channels:
            return True
        if username and f"@{username}" in self.monitored_channels:
            return True
        return False
    
    async def _handle_match(self, message: Message, keyword: str, text: str):
        """Handle match"""
        channel_id = str(message.chat.id)
        channel_username = message.chat.username or message.chat.title or ""
        message_id = message.id
        
        # Check for duplicates
        if await db.is_message_detected(message_id, channel_id, keyword):
            return
        
        # Create message link
        message_link = f"https://t.me/{channel_username}/{message_id}" if channel_username else None
        
        # Save to database
        db_id = await db.add_detected_message(
            message_id=message_id,
            channel_id=channel_id,
            channel_username=channel_username,
            keyword_matched=keyword,
            message_text=text[:2000],
            message_link=message_link
        )
        
        # Log
        self.logger.keyword_found(keyword, channel_username, message_id)
        
        # Send notifications
        await notification_manager.notify_keyword_found(
            keyword=keyword,
            channel=channel_username,
            message_text=text,
            message_link=message_link
        )
        
        # Update notification status
        if db_id:
            await db.mark_notification_sent(db_id)
    
    async def reload_config(self):
        """Reload configuration"""
        await self._load_keywords()
        await self._load_channels()
        self.logger.info("Configuration reloaded")
    
    async def start(self):
        """Start monitoring"""
        if self.is_running:
            return
        
        self.is_running = True
        channels_count = len(self.monitored_channels)
        keywords_count = len(self.search_engine.patterns)
        
        self.logger.monitor_started(channels_count, keywords_count)
        
        await self.client.start()
        
        # Display account information
        me = await self.client.get_me()
        self.logger.info(f"Logged in as: {me.first_name} (@{me.username})")
        
        # Wait for shutdown
        await graceful_shutdown.wait_for_shutdown()
    
    async def stop(self):
        """Stop monitoring"""
        if not self.is_running:
            return
        
        self.is_running = False
        self.logger.monitor_stopped()
        
        # Close client with error handling
        try:
            if self.client and self.client.is_connected:
                await self.client.stop()
        except Exception as e:
            self.logger.error(f"Error stopping client: {e}")
        
        # Close database connection
        try:
            await db.disconnect()
        except Exception as e:
            self.logger.error(f"Error closing database: {e}")
    
    async def run(self):
        """Full run"""
        try:
            await self.initialize()
            await self.start()
        except KeyboardInterrupt:
            pass
        except Exception as e:
            self.logger.error(f"Error: {e}", exc_info=True)
            raise
        finally:
            await self.stop()


async def main():
    """Main function"""
    monitor = ChannelMonitor()
    
    # Setup graceful shutdown
    graceful_shutdown.setup_signals()
    graceful_shutdown.add_cleanup(monitor.stop)
    
    # Run with restart
    await auto_restart.run_with_restart(monitor.run)


def run_monitor():
    """Entry point"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║              📡 Telegram Channel Monitor                 ║
    ║                  Advanced Version 2.0                    ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")


if __name__ == "__main__":
    run_monitor()
