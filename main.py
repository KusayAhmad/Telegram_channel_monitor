"""
Main entry point for the project
Run the monitoring system or dashboard
"""
import argparse
import asyncio
import sys
from pathlib import Path

# Add project path
sys.path.insert(0, str(Path(__file__).parent))


def run_monitor():
    """Run the monitoring system"""
    from monitor import run_monitor as start_monitor
    start_monitor()


def run_dashboard():
    """Run the dashboard"""
    from dashboard.app import run_dashboard as start_dashboard
    start_dashboard()


def run_both():
    """Run both together"""
    import threading
    
    # Run Dashboard in a separate thread
    dashboard_thread = threading.Thread(target=run_dashboard, daemon=True)
    dashboard_thread.start()
    
    # Run Monitor in the main thread
    run_monitor()


def generate_session():
    """Generate a new session"""
    from pyrogram import Client
    from config import config
    
    print("🔐 Creating new Telegram session")
    print("-" * 40)
    
    api_id = input("Enter API ID: ") or config.API_ID
    api_hash = input("Enter API Hash: ") or config.API_HASH
    session_name = input(f"Session name [{config.SESSION_NAME}]: ") or config.SESSION_NAME
    
    with Client(session_name, api_id=int(api_id), api_hash=api_hash) as app:
        me = app.get_me()
        print(f"\n✅ Session created successfully!")
        print(f"👤 Account: {me.first_name} (@{me.username})")
        print(f"🆔 ID: {me.id}")


def list_channels():
    """Display subscribed channels"""
    import asyncio
    from pyrogram import Client
    from pyrogram.enums import ChatType
    from config import config
    
    async def _list():
        async with Client(config.SESSION_NAME, config.API_ID, config.API_HASH) as app:
            print("\n📢 Subscribed channels:\n")
            print("-" * 50)
            
            async for dialog in app.get_dialogs():
                if dialog.chat.type in [ChatType.CHANNEL, ChatType.SUPERGROUP]:
                    username = f"@{dialog.chat.username}" if dialog.chat.username else "no username"
                    print(f"📣 {dialog.chat.title}")
                    print(f"   {username}")
                    print(f"   ID: {dialog.chat.id}")
                    print("-" * 50)
    
    asyncio.run(_list())


def init_database():
    """Initialize the database"""
    import asyncio
    from database import db
    from config import config
    
    async def _init():
        await db.connect()
        print(f"✅ Database created: {config.DATABASE_PATH}")
        await db.disconnect()
    
    asyncio.run(_init())


def export_data(format: str = 'csv'):
    """Export data"""
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
            print(f"✅ Exported to: {filepath}")
        else:
            print("❌ No data to export")
    
    asyncio.run(_export())


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Telegram Channel Monitoring System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available commands:
  monitor      Run the monitoring system
  dashboard    Run the web dashboard
  both         Run both monitoring and dashboard together
  session      Create a new Telegram session
  channels     Display subscribed channels
  init-db      Initialize the database
  export       Export data (csv or json)

Examples:
  python main.py monitor
  python main.py dashboard
  python main.py export --format json
        """
    )
    
    parser.add_argument(
        'command',
        choices=['monitor', 'dashboard', 'both', 'session', 'channels', 'init-db', 'export'],
        help='Command to execute'
    )
    
    parser.add_argument(
        '--format',
        choices=['csv', 'json'],
        default='csv',
        help='Export format (for export command)'
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
        print("\n👋 Stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
