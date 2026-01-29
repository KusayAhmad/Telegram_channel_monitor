"""
نقطة الدخول الرئيسية للمشروع
تشغيل نظام المراقبة أو لوحة التحكم
"""
import argparse
import asyncio
import sys
from pathlib import Path

# إضافة مسار المشروع
sys.path.insert(0, str(Path(__file__).parent))


def run_monitor():
    """تشغيل نظام المراقبة"""
    from monitor import run_monitor as start_monitor
    start_monitor()


def run_dashboard():
    """تشغيل لوحة التحكم"""
    from dashboard.app import run_dashboard as start_dashboard
    start_dashboard()


def run_both():
    """تشغيل كلاهما معاً"""
    import threading
    
    # تشغيل Dashboard في thread منفصل
    dashboard_thread = threading.Thread(target=run_dashboard, daemon=True)
    dashboard_thread.start()
    
    # تشغيل Monitor في الـ thread الرئيسي
    run_monitor()


def generate_session():
    """إنشاء جلسة جديدة"""
    from pyrogram import Client
    from config import config
    
    print("🔐 إنشاء جلسة Telegram جديدة")
    print("-" * 40)
    
    api_id = input("أدخل API ID: ") or config.API_ID
    api_hash = input("أدخل API Hash: ") or config.API_HASH
    session_name = input(f"اسم الجلسة [{config.SESSION_NAME}]: ") or config.SESSION_NAME
    
    with Client(session_name, api_id=int(api_id), api_hash=api_hash) as app:
        me = app.get_me()
        print(f"\n✅ تم إنشاء الجلسة بنجاح!")
        print(f"👤 الحساب: {me.first_name} (@{me.username})")
        print(f"🆔 المعرّف: {me.id}")


def list_channels():
    """عرض القنوات المشترك بها"""
    import asyncio
    from pyrogram import Client
    from pyrogram.enums import ChatType
    from config import config
    
    async def _list():
        async with Client(config.SESSION_NAME, config.API_ID, config.API_HASH) as app:
            print("\n📢 القنوات المشترك بها:\n")
            print("-" * 50)
            
            async for dialog in app.get_dialogs():
                if dialog.chat.type in [ChatType.CHANNEL, ChatType.SUPERGROUP]:
                    username = f"@{dialog.chat.username}" if dialog.chat.username else "بدون username"
                    print(f"📣 {dialog.chat.title}")
                    print(f"   {username}")
                    print(f"   ID: {dialog.chat.id}")
                    print("-" * 50)
    
    asyncio.run(_list())


def init_database():
    """تهيئة قاعدة البيانات"""
    import asyncio
    from database import db
    from config import config
    
    async def _init():
        await db.connect()
        print(f"✅ تم إنشاء قاعدة البيانات: {config.DATABASE_PATH}")
        await db.disconnect()
    
    asyncio.run(_init())


def export_data(format: str = 'csv'):
    """تصدير البيانات"""
    import asyncio
    from database import db
    from exporter import DataExporter
    
    async def _export():
        await db.connect()
        messages = await db.get_detected_messages(limit=10000)
        
        exporter = DataExporter()
        
        if format == 'json':
            filepath = await exporter.export_to_json(messages)
        else:
            filepath = await exporter.export_to_csv(messages)
        
        await db.disconnect()
        
        if filepath:
            print(f"✅ تم التصدير إلى: {filepath}")
        else:
            print("❌ لا توجد بيانات للتصدير")
    
    asyncio.run(_export())


def main():
    """نقطة الدخول الرئيسية"""
    parser = argparse.ArgumentParser(
        description='نظام مراقبة قنوات تيليغرام',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
الأوامر المتاحة:
  monitor      تشغيل نظام المراقبة
  dashboard    تشغيل لوحة التحكم الويب
  both         تشغيل المراقبة ولوحة التحكم معاً
  session      إنشاء جلسة Telegram جديدة
  channels     عرض القنوات المشترك بها
  init-db      تهيئة قاعدة البيانات
  export       تصدير البيانات (csv أو json)

أمثلة:
  python main.py monitor
  python main.py dashboard
  python main.py export --format json
        """
    )
    
    parser.add_argument(
        'command',
        choices=['monitor', 'dashboard', 'both', 'session', 'channels', 'init-db', 'export'],
        help='الأمر المراد تنفيذه'
    )
    
    parser.add_argument(
        '--format',
        choices=['csv', 'json'],
        default='csv',
        help='صيغة التصدير (للأمر export)'
    )
    
    args = parser.parse_args()
    
    commands = {
        'monitor': run_monitor,
        'dashboard': run_dashboard,
        'both': run_both,
        'session': generate_session,
        'channels': list_channels,
        'init-db': init_database,
        'export': lambda: export_data(args.format)
    }
    
    try:
        commands[args.command]()
    except KeyboardInterrupt:
        print("\n👋 تم الإيقاف")
    except Exception as e:
        print(f"❌ خطأ: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
