"""
نظام الإشعارات المتعدد
يدعم Telegram، Discord، Email
"""
import asyncio
import aiohttp
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from abc import ABC, abstractmethod
from typing import Optional, List
from dataclasses import dataclass

from config import config
from logger import monitor_logger


@dataclass
class NotificationMessage:
    """بنية رسالة الإشعار"""
    title: str
    body: str
    keyword: str
    channel: str
    message_link: Optional[str] = None
    
    def to_telegram_format(self) -> str:
        """تنسيق لتيليغرام"""
        text = f"**🎯 {self.title}**\n\n"
        text += f"📌 **الكلمة:** `{self.keyword}`\n"
        text += f"📢 **القناة:** @{self.channel}\n\n"
        text += f"💬 **الرسالة:**\n{self.body}"
        if self.message_link:
            text += f"\n\n🔗 [رابط الرسالة]({self.message_link})"
        return text
    
    def to_discord_format(self) -> dict:
        """تنسيق لـ Discord Embed"""
        return {
            "embeds": [{
                "title": f"🎯 {self.title}",
                "description": self.body[:2000],
                "color": 0x00ff00,
                "fields": [
                    {"name": "📌 الكلمة", "value": self.keyword, "inline": True},
                    {"name": "📢 القناة", "value": f"@{self.channel}", "inline": True}
                ],
                "url": self.message_link
            }]
        }
    
    def to_email_format(self) -> tuple:
        """تنسيق للبريد الإلكتروني"""
        subject = f"🎯 تنبيه: تم العثور على '{self.keyword}' في @{self.channel}"
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; direction: rtl;">
            <h2 style="color: #2e7d32;">🎯 {self.title}</h2>
            <p><strong>📌 الكلمة:</strong> {self.keyword}</p>
            <p><strong>📢 القناة:</strong> @{self.channel}</p>
            <hr>
            <p><strong>💬 الرسالة:</strong></p>
            <div style="background: #f5f5f5; padding: 15px; border-radius: 5px;">
                {self.body}
            </div>
            {f'<p><a href="{self.message_link}">🔗 رابط الرسالة</a></p>' if self.message_link else ''}
        </body>
        </html>
        """
        
        return subject, html


class NotificationProvider(ABC):
    """الفئة الأساسية لمزودي الإشعارات"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @abstractmethod
    async def send(self, message: NotificationMessage) -> bool:
        pass
    
    @abstractmethod
    def is_configured(self) -> bool:
        pass


class TelegramNotifier(NotificationProvider):
    """إشعارات تيليغرام عبر حساب المستخدم"""
    
    name = "telegram"
    
    def __init__(self, client=None):
        self.client = client
        self.user_id = config.NOTIFY_USER_ID
    
    def is_configured(self) -> bool:
        return bool(self.user_id and self.client)
    
    async def send(self, message: NotificationMessage) -> bool:
        if not self.is_configured():
            monitor_logger.warning("Telegram غير مُهيأ")
            return False
        
        try:
            await self.client.send_message(
                self.user_id,
                message.to_telegram_format()
            )
            monitor_logger.notification_sent("Telegram", str(self.user_id))
            return True
        except Exception as e:
            monitor_logger.notification_failed("Telegram", str(e))
            return False


class DiscordNotifier(NotificationProvider):
    """إشعارات Discord عبر Webhook"""
    
    name = "discord"
    
    def __init__(self):
        self.webhook_url = config.DISCORD_WEBHOOK_URL
    
    def is_configured(self) -> bool:
        return bool(self.webhook_url)
    
    async def send(self, message: NotificationMessage) -> bool:
        if not self.is_configured():
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=message.to_discord_format()
                ) as response:
                    if response.status in [200, 204]:
                        monitor_logger.notification_sent("Discord", "webhook")
                        return True
                    else:
                        monitor_logger.notification_failed(
                            "Discord", 
                            f"Status: {response.status}"
                        )
                        return False
        except Exception as e:
            monitor_logger.notification_failed("Discord", str(e))
            return False


class EmailNotifier(NotificationProvider):
    """إشعارات البريد الإلكتروني"""
    
    name = "email"
    
    def __init__(self):
        self.smtp_server = config.EMAIL_SMTP_SERVER
        self.smtp_port = config.EMAIL_SMTP_PORT
        self.username = config.EMAIL_USERNAME
        self.password = config.EMAIL_PASSWORD
        self.to_email = config.EMAIL_TO
    
    def is_configured(self) -> bool:
        return all([
            self.smtp_server,
            self.username,
            self.password,
            self.to_email
        ])
    
    async def send(self, message: NotificationMessage) -> bool:
        if not self.is_configured():
            return False
        
        try:
            subject, html_body = message.to_email_format()
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.username
            msg['To'] = self.to_email
            
            html_part = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(html_part)
            
            await aiosmtplib.send(
                msg,
                hostname=self.smtp_server,
                port=self.smtp_port,
                username=self.username,
                password=self.password,
                start_tls=True
            )
            
            monitor_logger.notification_sent("Email", self.to_email)
            return True
            
        except Exception as e:
            monitor_logger.notification_failed("Email", str(e))
            return False


class NotificationManager:
    """مدير الإشعارات - يُنسق بين جميع المزودين"""
    
    def __init__(self):
        self.providers: List[NotificationProvider] = []
    
    def add_provider(self, provider: NotificationProvider):
        """إضافة مزود إشعارات"""
        if provider.is_configured():
            self.providers.append(provider)
            monitor_logger.info(f"تم تفعيل مزود الإشعارات: {provider.name}")
    
    def setup_telegram(self, client):
        """إعداد تيليغرام"""
        self.add_provider(TelegramNotifier(client))
    
    def setup_discord(self):
        """إعداد Discord"""
        self.add_provider(DiscordNotifier())
    
    def setup_email(self):
        """إعداد البريد"""
        self.add_provider(EmailNotifier())
    
    def setup_all(self, telegram_client=None):
        """إعداد جميع المزودين المتاحين"""
        if telegram_client:
            self.setup_telegram(telegram_client)
        self.setup_discord()
        self.setup_email()
    
    async def notify(self, message: NotificationMessage) -> dict:
        """إرسال إشعار لجميع المزودين"""
        results = {}
        
        if not self.providers:
            monitor_logger.warning("لا توجد مزودات إشعارات مُهيأة")
            return results
        
        tasks = []
        for provider in self.providers:
            tasks.append(self._send_with_provider(provider, message))
        
        await asyncio.gather(*tasks)
        
        return results
    
    async def _send_with_provider(
        self, 
        provider: NotificationProvider, 
        message: NotificationMessage
    ) -> tuple:
        """إرسال إشعار عبر مزود محدد"""
        success = await provider.send(message)
        return provider.name, success
    
    async def notify_keyword_found(
        self,
        keyword: str,
        channel: str,
        message_text: str,
        message_link: str = None
    ):
        """إشعار عند العثور على كلمة مفتاحية"""
        notification = NotificationMessage(
            title="تم العثور على كلمة مفتاحية!",
            body=message_text[:1000] if message_text else "",
            keyword=keyword,
            channel=channel,
            message_link=message_link
        )
        await self.notify(notification)


# Singleton instance
notification_manager = NotificationManager()
