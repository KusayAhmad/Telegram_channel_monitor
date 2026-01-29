"""
نظام الجدولة وإعادة التشغيل التلقائي
يدير تشغيل المراقبة في أوقات محددة مع إعادة التشغيل عند الفشل
"""
import asyncio
import signal
import sys
from datetime import datetime, time
from typing import Callable, Optional, List
from dataclasses import dataclass
from enum import Enum

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from config import config
from logger import monitor_logger
from database import db


class ScheduleType(Enum):
    """نوع الجدولة"""
    DAILY = "daily"
    WEEKLY = "weekly"
    INTERVAL = "interval"
    CRON = "cron"


@dataclass
class Schedule:
    """بنية الجدول الزمني"""
    name: str
    schedule_type: ScheduleType
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    days_of_week: List[int] = None  # 0=الإثنين, 6=الأحد
    interval_minutes: int = 0
    cron_expression: str = ""
    is_active: bool = True


class ScheduleManager:
    """مدير الجدولة"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.schedules: List[Schedule] = []
        self._monitor_callback: Optional[Callable] = None
        self._is_monitoring = False
    
    def set_monitor_callback(self, callback: Callable):
        """تعيين دالة بدء/إيقاف المراقبة"""
        self._monitor_callback = callback
    
    def add_schedule(self, schedule: Schedule):
        """إضافة جدول زمني"""
        self.schedules.append(schedule)
        
        if schedule.schedule_type == ScheduleType.DAILY:
            # جدولة يومية
            self.scheduler.add_job(
                self._start_monitoring,
                CronTrigger(
                    hour=schedule.start_time.hour if schedule.start_time else 0,
                    minute=schedule.start_time.minute if schedule.start_time else 0
                ),
                id=f"{schedule.name}_start",
                replace_existing=True
            )
            
            if schedule.end_time:
                self.scheduler.add_job(
                    self._stop_monitoring,
                    CronTrigger(
                        hour=schedule.end_time.hour,
                        minute=schedule.end_time.minute
                    ),
                    id=f"{schedule.name}_stop",
                    replace_existing=True
                )
        
        elif schedule.schedule_type == ScheduleType.INTERVAL:
            self.scheduler.add_job(
                self._start_monitoring,
                IntervalTrigger(minutes=schedule.interval_minutes),
                id=f"{schedule.name}_interval",
                replace_existing=True
            )
        
        elif schedule.schedule_type == ScheduleType.CRON:
            self.scheduler.add_job(
                self._start_monitoring,
                CronTrigger.from_crontab(schedule.cron_expression),
                id=f"{schedule.name}_cron",
                replace_existing=True
            )
        
        monitor_logger.info(f"تمت إضافة جدول: {schedule.name}")
    
    async def _start_monitoring(self):
        """بدء المراقبة"""
        if self._monitor_callback and not self._is_monitoring:
            self._is_monitoring = True
            monitor_logger.info("🚀 بدء المراقبة المجدولة")
            await self._monitor_callback(start=True)
    
    async def _stop_monitoring(self):
        """إيقاف المراقبة"""
        if self._monitor_callback and self._is_monitoring:
            self._is_monitoring = False
            monitor_logger.info("🛑 إيقاف المراقبة المجدولة")
            await self._monitor_callback(start=False)
    
    def start(self):
        """تشغيل المجدول"""
        self.scheduler.start()
        monitor_logger.info("⏰ تم تشغيل نظام الجدولة")
    
    def stop(self):
        """إيقاف المجدول"""
        self.scheduler.shutdown()
        monitor_logger.info("⏰ تم إيقاف نظام الجدولة")
    
    def is_within_schedule(self) -> bool:
        """التحقق إذا كنا ضمن وقت المراقبة"""
        now = datetime.now().time()
        today = datetime.now().weekday()
        
        for schedule in self.schedules:
            if not schedule.is_active:
                continue
            
            # التحقق من اليوم
            if schedule.days_of_week and today not in schedule.days_of_week:
                continue
            
            # التحقق من الوقت
            if schedule.start_time and schedule.end_time:
                if schedule.start_time <= now <= schedule.end_time:
                    return True
            elif schedule.start_time:
                if now >= schedule.start_time:
                    return True
        
        return len(self.schedules) == 0  # إذا لا توجد جداول، دائماً ضمن الوقت


class AutoRestartManager:
    """مدير إعادة التشغيل التلقائي"""
    
    def __init__(
        self, 
        max_retries: int = 5,
        retry_delay: int = 30,
        backoff_multiplier: float = 2.0
    ):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.backoff_multiplier = backoff_multiplier
        self._current_retries = 0
        self._running = False
        self._main_task: Optional[asyncio.Task] = None
    
    async def run_with_restart(self, coroutine_func: Callable):
        """
        تشغيل دالة مع إعادة التشغيل التلقائي عند الفشل
        
        Args:
            coroutine_func: الدالة الـ async المراد تشغيلها
        """
        self._running = True
        
        while self._running and self._current_retries < self.max_retries:
            try:
                monitor_logger.info("🚀 بدء التشغيل...")
                self._current_retries = 0
                await coroutine_func()
                
            except asyncio.CancelledError:
                monitor_logger.info("تم إلغاء التشغيل")
                break
                
            except Exception as e:
                self._current_retries += 1
                delay = self.retry_delay * (self.backoff_multiplier ** (self._current_retries - 1))
                
                monitor_logger.error(
                    f"❌ خطأ في التشغيل (محاولة {self._current_retries}/{self.max_retries}): {e}"
                )
                
                if self._current_retries < self.max_retries:
                    monitor_logger.info(f"⏳ إعادة المحاولة بعد {delay:.0f} ثانية...")
                    await asyncio.sleep(delay)
                else:
                    monitor_logger.critical("🛑 تجاوز الحد الأقصى للمحاولات")
                    break
        
        self._running = False
    
    def stop(self):
        """إيقاف إعادة التشغيل"""
        self._running = False
        if self._main_task:
            self._main_task.cancel()
    
    def reset_retries(self):
        """إعادة تعيين عداد المحاولات"""
        self._current_retries = 0


class GracefulShutdown:
    """إدارة الإيقاف الآمن"""
    
    def __init__(self):
        self._shutdown_event = asyncio.Event()
        self._cleanup_callbacks: List[Callable] = []
    
    def setup_signals(self):
        """إعداد معالجات الإشارات"""
        if sys.platform != 'win32':
            loop = asyncio.get_event_loop()
            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(sig, self._signal_handler)
        else:
            # Windows
            signal.signal(signal.SIGINT, self._sync_signal_handler)
            signal.signal(signal.SIGTERM, self._sync_signal_handler)
    
    def _signal_handler(self):
        """معالج الإشارات (Unix)"""
        monitor_logger.info("📴 تم استقبال إشارة الإيقاف")
        self._shutdown_event.set()
    
    def _sync_signal_handler(self, signum, frame):
        """معالج الإشارات (Windows)"""
        monitor_logger.info("📴 تم استقبال إشارة الإيقاف")
        asyncio.get_event_loop().call_soon_threadsafe(self._shutdown_event.set)
    
    def add_cleanup(self, callback: Callable):
        """إضافة دالة تنظيف"""
        self._cleanup_callbacks.append(callback)
    
    async def wait_for_shutdown(self):
        """انتظار إشارة الإيقاف"""
        await self._shutdown_event.wait()
    
    async def cleanup(self):
        """تنفيذ عمليات التنظيف"""
        monitor_logger.info("🧹 جاري التنظيف...")
        
        for callback in self._cleanup_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                monitor_logger.error(f"خطأ في التنظيف: {e}")
        
        monitor_logger.info("✅ تم الإيقاف بنجاح")


# Singleton instances
schedule_manager = ScheduleManager()
auto_restart = AutoRestartManager()
graceful_shutdown = GracefulShutdown()
