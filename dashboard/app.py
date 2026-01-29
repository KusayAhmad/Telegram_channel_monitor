"""
Flask Dashboard for the Project
Web interface for managing the monitoring system
"""
import asyncio
from functools import wraps
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import config
from database import db
from logger import monitor_logger


# Create the application
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.secret_key = config.DASHBOARD_SECRET_KEY

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin):
    """Dummy user for authentication"""
    def __init__(self, id):
        self.id = id


# Default user (can be improved later)
ADMIN_USER = User(1)


@login_manager.user_loader
def load_user(user_id):
    if user_id == '1':
        return ADMIN_USER
    return None


def async_action(f):
    """Decorator to run async functions"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(f(*args, **kwargs))
        finally:
            loop.close()
    return wrapper


# ==================== Pages ====================

@app.route('/')
@login_required
@async_action
async def index():
    """Main page"""
    await db.connect()
    stats = await db.get_stats(days=7)
    channels = await db.get_channels()
    keywords = await db.get_keywords()
    recent = await db.get_detected_messages(limit=5)
    await db.disconnect()
    
    return render_template('index.html',
                          stats=stats,
                          channels=channels,
                          keywords=keywords,
                          recent=recent)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        password = request.form.get('password')
        # Simple password (can be improved)
        if password == config.DASHBOARD_SECRET_KEY:
            login_user(ADMIN_USER)
            return redirect(url_for('index'))
        flash('كلمة المرور غير صحيحة', 'error')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Logout"""
    logout_user()
    return redirect(url_for('login'))


@app.route('/channels')
@login_required
@async_action
async def channels():
    """Channels page"""
    await db.connect()
    channels_list = await db.get_channels(active_only=False)
    await db.disconnect()
    return render_template('channels.html', channels=channels_list)


@app.route('/keywords')
@login_required
@async_action
async def keywords():
    """Keywords page"""
    await db.connect()
    keywords_list = await db.get_keywords(active_only=False)
    await db.disconnect()
    return render_template('keywords.html', keywords=keywords_list)


@app.route('/messages')
@login_required
@async_action
async def messages():
    """Messages page"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    await db.connect()
    messages_list = await db.get_detected_messages(
        limit=per_page, 
        offset=(page - 1) * per_page
    )
    await db.disconnect()
    
    return render_template('messages.html', 
                          messages=messages_list,
                          page=page)


@app.route('/stats')
@login_required
@async_action
async def stats():
    """Statistics page"""
    await db.connect()
    stats_data = await db.get_stats(days=30)
    await db.disconnect()
    return render_template('stats.html', stats=stats_data)


# ==================== API Endpoints ====================

@app.route('/api/channels', methods=['GET', 'POST', 'DELETE'])
@login_required
@async_action
async def api_channels():
    """API for channels"""
    await db.connect()
    
    if request.method == 'GET':
        channels = await db.get_channels(active_only=False)
        await db.disconnect()
        return jsonify(channels)
    
    elif request.method == 'POST':
        data = request.json
        channel_id = data.get('channel_id')
        username = data.get('username')
        title = data.get('title')
        
        result = await db.add_channel(channel_id, username, title)
        await db.disconnect()
        return jsonify({'success': bool(result), 'id': result})
    
    elif request.method == 'DELETE':
        channel_id = request.args.get('channel_id')
        await db.remove_channel(channel_id)
        await db.disconnect()
        return jsonify({'success': True})


@app.route('/api/channels/<channel_id>/toggle', methods=['POST'])
@login_required
@async_action
async def api_toggle_channel(channel_id):
    """Enable/disable a channel"""
    await db.connect()
    data = request.json
    is_active = data.get('is_active', True)
    await db.toggle_channel(channel_id, is_active)
    await db.disconnect()
    return jsonify({'success': True})


@app.route('/api/keywords', methods=['GET', 'POST', 'DELETE'])
@login_required
@async_action
async def api_keywords():
    """API for keywords"""
    await db.connect()
    
    if request.method == 'GET':
        keywords = await db.get_keywords(active_only=False)
        await db.disconnect()
        return jsonify(keywords)
    
    elif request.method == 'POST':
        data = request.json
        keyword = data.get('keyword')
        is_regex = data.get('is_regex', False)
        
        result = await db.add_keyword(keyword, is_regex)
        await db.disconnect()
        return jsonify({'success': bool(result), 'id': result})
    
    elif request.method == 'DELETE':
        keyword_id = request.args.get('id', type=int)
        await db.remove_keyword(keyword_id)
        await db.disconnect()
        return jsonify({'success': True})


@app.route('/api/keywords/<int:keyword_id>/toggle', methods=['POST'])
@login_required
@async_action
async def api_toggle_keyword(keyword_id):
    """Enable/disable a keyword"""
    await db.connect()
    data = request.json
    is_active = data.get('is_active', True)
    await db.toggle_keyword(keyword_id, is_active)
    await db.disconnect()
    return jsonify({'success': True})


@app.route('/api/messages', methods=['GET'])
@login_required
@async_action
async def api_messages():
    """API for messages"""
    await db.connect()
    
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    channel = request.args.get('channel')
    keyword = request.args.get('keyword')
    
    messages = await db.get_detected_messages(
        limit=limit,
        offset=offset,
        channel_id=channel,
        keyword=keyword
    )
    await db.disconnect()
    return jsonify(messages)


@app.route('/api/stats', methods=['GET'])
@login_required
@async_action
async def api_stats():
    """API for statistics"""
    await db.connect()
    days = request.args.get('days', 7, type=int)
    stats = await db.get_stats(days=days)
    await db.disconnect()
    return jsonify(stats)


@app.route('/api/export/<format>')
@login_required
@async_action
async def api_export(format):
    """API for export"""
    from exporter import DataExporter
    
    await db.connect()
    messages = await db.get_detected_messages(limit=10000)
    await db.disconnect()
    
    exporter = DataExporter()
    
    if format == 'csv':
        filepath = await exporter.export_to_csv(messages)
    elif format == 'json':
        filepath = await exporter.export_to_json(messages)
    else:
        return jsonify({'error': 'صيغة غير مدعومة'}), 400
    
    if filepath:
        return jsonify({'success': True, 'file': str(filepath)})
    return jsonify({'error': 'فشل التصدير'}), 500


def run_dashboard():
    """Run the dashboard"""
    monitor_logger.info(f"🌐 Starting dashboard on http://{config.DASHBOARD_HOST}:{config.DASHBOARD_PORT}")
    app.run(
        host=config.DASHBOARD_HOST,
        port=config.DASHBOARD_PORT,
        debug=False
    )


if __name__ == '__main__':
    run_dashboard()
