"""
SQLite database for the project
Stores messages, keywords, channels, and statistics
"""
import aiosqlite
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from config import config
from logger import monitor_logger


class Database:
    """Database management"""
    
    def __init__(self, db_path: Path = None):
        self.db_path = db_path or config.DATABASE_PATH
        self._connection = None
    
    async def connect(self):
        """Connect to database"""
        config.ensure_directories()
        self._connection = await aiosqlite.connect(
            self.db_path,
            timeout=30.0,  # 30 seconds timeout to avoid locks
            isolation_level=None  # Auto-commit mode
        )
        self._connection.row_factory = aiosqlite.Row
        # Enable WAL mode for better concurrent access
        await self._connection.execute("PRAGMA journal_mode=WAL")
        await self._create_tables()
        monitor_logger.info(f"Connected to database: {self.db_path}")
    
    async def disconnect(self):
        """Disconnect"""
        if self._connection:
            await self._connection.close()
            self._connection = None
    
    async def _create_tables(self):
        """Create tables"""
        await self._connection.executescript('''
            -- Channels table
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT UNIQUE,
                username TEXT,
                title TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Keywords table
            CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT UNIQUE NOT NULL,
                is_regex INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Detected messages table
            CREATE TABLE IF NOT EXISTS detected_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER NOT NULL,
                channel_id TEXT NOT NULL,
                channel_username TEXT,
                keyword_matched TEXT NOT NULL,
                message_text TEXT,
                message_link TEXT,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notification_sent INTEGER DEFAULT 0,
                UNIQUE(message_id, channel_id, keyword_matched)
            );
            
            -- Notifications table
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                detected_message_id INTEGER,
                notification_type TEXT NOT NULL,
                destination TEXT,
                status TEXT DEFAULT 'pending',
                error_message TEXT,
                sent_at TIMESTAMP,
                FOREIGN KEY (detected_message_id) REFERENCES detected_messages(id)
            );
            
            -- Daily statistics table
            CREATE TABLE IF NOT EXISTS daily_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE UNIQUE NOT NULL,
                messages_detected INTEGER DEFAULT 0,
                notifications_sent INTEGER DEFAULT 0,
                keywords_matched TEXT,
                channels_active TEXT
            );
            
            -- Schedule settings table
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                start_time TEXT,
                end_time TEXT,
                days_of_week TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Create indexes
            CREATE INDEX IF NOT EXISTS idx_detected_messages_channel ON detected_messages(channel_id);
            CREATE INDEX IF NOT EXISTS idx_detected_messages_keyword ON detected_messages(keyword_matched);
            CREATE INDEX IF NOT EXISTS idx_detected_messages_date ON detected_messages(detected_at);
        ''')
        await self._connection.commit()
    
    # ===================== Channels =====================
    
    async def add_channel(self, channel_id: str, username: str = None, title: str = None) -> int:
        """Add new channel"""
        try:
            cursor = await self._connection.execute(
                '''INSERT OR REPLACE INTO channels (channel_id, username, title, updated_at) 
                   VALUES (?, ?, ?, ?)''',
                (channel_id, username, title, datetime.now())
            )
            await self._connection.commit()
            return cursor.lastrowid
        except Exception as e:
            monitor_logger.error(f"Error adding channel: {e}")
            return 0
    
    async def get_channels(self, active_only: bool = True) -> List[Dict]:
        """Fetch channels"""
        query = 'SELECT * FROM channels'
        if active_only:
            query += ' WHERE is_active = 1'
        
        cursor = await self._connection.execute(query)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    
    async def toggle_channel(self, channel_id: str, is_active: bool) -> bool:
        """Enable/disable channel"""
        await self._connection.execute(
            'UPDATE channels SET is_active = ?, updated_at = ? WHERE channel_id = ?',
            (1 if is_active else 0, datetime.now(), channel_id)
        )
        await self._connection.commit()
        return True
    
    async def remove_channel(self, channel_id: str) -> bool:
        """Delete channel"""
        await self._connection.execute('DELETE FROM channels WHERE channel_id = ?', (channel_id,))
        await self._connection.commit()
        return True
    
    # ===================== Keywords =====================
    
    async def add_keyword(self, keyword: str, is_regex: bool = False) -> int:
        """Add keyword"""
        try:
            cursor = await self._connection.execute(
                'INSERT OR IGNORE INTO keywords (keyword, is_regex) VALUES (?, ?)',
                (keyword, 1 if is_regex else 0)
            )
            await self._connection.commit()
            return cursor.lastrowid
        except Exception as e:
            monitor_logger.error(f"Error adding keyword: {e}")
            return 0
    
    async def get_keywords(self, active_only: bool = True) -> List[Dict]:
        """Fetch keywords"""
        query = 'SELECT * FROM keywords'
        if active_only:
            query += ' WHERE is_active = 1'
        
        cursor = await self._connection.execute(query)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    
    async def toggle_keyword(self, keyword_id: int, is_active: bool) -> bool:
        """Enable/disable keyword"""
        await self._connection.execute(
            'UPDATE keywords SET is_active = ? WHERE id = ?',
            (1 if is_active else 0, keyword_id)
        )
        await self._connection.commit()
        return True
    
    async def remove_keyword(self, keyword_id: int) -> bool:
        """Delete keyword"""
        await self._connection.execute('DELETE FROM keywords WHERE id = ?', (keyword_id,))
        await self._connection.commit()
        return True
    
    # ===================== Detected Messages =====================
    
    async def add_detected_message(
        self,
        message_id: int,
        channel_id: str,
        channel_username: str,
        keyword_matched: str,
        message_text: str,
        message_link: str = None
    ) -> int:
        """Add detected message"""
        try:
            cursor = await self._connection.execute(
                '''INSERT OR IGNORE INTO detected_messages 
                   (message_id, channel_id, channel_username, keyword_matched, message_text, message_link)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (message_id, channel_id, channel_username, keyword_matched, message_text, message_link)
            )
            await self._connection.commit()
            return cursor.lastrowid
        except Exception as e:
            monitor_logger.error(f"Error saving message: {e}")
            return 0
    
    async def is_message_detected(self, message_id: int, channel_id: str, keyword: str) -> bool:
        """Check if message was previously detected"""
        cursor = await self._connection.execute(
            '''SELECT 1 FROM detected_messages 
               WHERE message_id = ? AND channel_id = ? AND keyword_matched = ?''',
            (message_id, channel_id, keyword)
        )
        return await cursor.fetchone() is not None
    
    async def get_detected_messages(
        self,
        limit: int = 100,
        offset: int = 0,
        channel_id: str = None,
        keyword: str = None,
        date_from: datetime = None,
        date_to: datetime = None
    ) -> List[Dict]:
        """Fetch detected messages with filtering"""
        query = 'SELECT * FROM detected_messages WHERE 1=1'
        params = []
        
        if channel_id:
            query += ' AND channel_id = ?'
            params.append(channel_id)
        
        if keyword:
            query += ' AND keyword_matched = ?'
            params.append(keyword)
        
        if date_from:
            query += ' AND detected_at >= ?'
            params.append(date_from)
        
        if date_to:
            query += ' AND detected_at <= ?'
            params.append(date_to)
        
        query += ' ORDER BY detected_at DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        cursor = await self._connection.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    
    async def mark_notification_sent(self, message_id: int):
        """Update notification status"""
        await self._connection.execute(
            'UPDATE detected_messages SET notification_sent = 1 WHERE id = ?',
            (message_id,)
        )
        await self._connection.commit()
    
    # ===================== Notifications =====================
    
    async def add_notification(
        self,
        detected_message_id: int,
        notification_type: str,
        destination: str,
        status: str = 'pending',
        error_message: str = None
    ) -> int:
        """Add notification record"""
        cursor = await self._connection.execute(
            '''INSERT INTO notifications 
               (detected_message_id, notification_type, destination, status, error_message, sent_at)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (detected_message_id, notification_type, destination, status, error_message,
             datetime.now() if status == 'sent' else None)
        )
        await self._connection.commit()
        return cursor.lastrowid
    
    # ===================== Statistics =====================
    
    async def get_stats(self, days: int = 7) -> Dict[str, Any]:
        """Fetch general statistics"""
        # Total messages
        cursor = await self._connection.execute('SELECT COUNT(*) FROM detected_messages')
        total_messages = (await cursor.fetchone())[0]
        
        # Today's messages
        cursor = await self._connection.execute(
            "SELECT COUNT(*) FROM detected_messages WHERE DATE(detected_at) = DATE('now')"
        )
        today_messages = (await cursor.fetchone())[0]
        
        # Most matched keywords
        cursor = await self._connection.execute(
            '''SELECT keyword_matched, COUNT(*) as count 
               FROM detected_messages 
               GROUP BY keyword_matched 
               ORDER BY count DESC LIMIT 10'''
        )
        top_keywords = [dict(row) for row in await cursor.fetchall()]
        
        # Most active channels
        cursor = await self._connection.execute(
            '''SELECT channel_username, COUNT(*) as count 
               FROM detected_messages 
               GROUP BY channel_id 
               ORDER BY count DESC LIMIT 10'''
        )
        top_channels = [dict(row) for row in await cursor.fetchall()]
        
        # Recent days statistics
        cursor = await self._connection.execute(
            f'''SELECT DATE(detected_at) as date, COUNT(*) as count 
                FROM detected_messages 
                WHERE detected_at >= DATE('now', '-{days} days')
                GROUP BY DATE(detected_at)
                ORDER BY date DESC'''
        )
        daily_counts = [dict(row) for row in await cursor.fetchall()]
        
        return {
            'total_messages': total_messages,
            'today_messages': today_messages,
            'top_keywords': top_keywords,
            'top_channels': top_channels,
            'daily_counts': daily_counts
        }
    
    # ===================== Scheduling =====================
    
    async def add_schedule(
        self,
        name: str,
        start_time: str,
        end_time: str,
        days_of_week: str = "0,1,2,3,4,5,6"
    ) -> int:
        """Add schedule"""
        cursor = await self._connection.execute(
            '''INSERT INTO schedules (name, start_time, end_time, days_of_week)
               VALUES (?, ?, ?, ?)''',
            (name, start_time, end_time, days_of_week)
        )
        await self._connection.commit()
        return cursor.lastrowid
    
    async def get_schedules(self, active_only: bool = True) -> List[Dict]:
        """Fetch schedules"""
        query = 'SELECT * FROM schedules'
        if active_only:
            query += ' WHERE is_active = 1'
        
        cursor = await self._connection.execute(query)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


# Singleton instance
db = Database()
