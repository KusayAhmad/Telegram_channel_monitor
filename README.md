# 📡 Telegram Channel Monitor

A comprehensive system for monitoring Telegram channels and searching for specific keywords with instant multi-channel notifications.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Pyrogram](https://img.shields.io/badge/Pyrogram-2.0+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Features

### 🔍 Monitoring and Search
- ✅ Monitor multiple channels simultaneously
- ✅ Search with regular keywords
- ✅ Regex support for advanced searching
- ✅ Avoid duplicate notifications for detected messages

### 📢 Notifications
- ✅ Instant Telegram notifications
- ✅ Discord Webhooks support
- ✅ Email notifications
- ✅ Ability to add new providers

### 🤖 Control Bot
- ✅ Channel management (add/remove/toggle)
- ✅ Keyword management
- ✅ Display statistics
- ✅ Export data

### 🌐 Web Dashboard
- ✅ Clean and elegant interface
- ✅ Statistics and charts
- ✅ Complete management via browser
- ✅ Export data (CSV/JSON)

### ⚙️ Technical Features
- ✅ SQLite database
- ✅ Comprehensive logging system
- ✅ Auto-restart on failure
- ✅ Schedule monitoring at specific times

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/channel_monitor.git
cd channel_monitor
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Requirements

```bash
pip install -r requirements.txt
```

### 4. Setup Environment File

```bash
# Copy example file
copy .env.example .env

# Edit settings
notepad .env
```

### 5. Get Telegram API Credentials

1. Go to [my.telegram.org](https://my.telegram.org)
2. Login with your phone number
3. Click on "API Development Tools"
4. Create a new application
5. Copy `API_ID` and `API_HASH`

### 6. Create Session

```bash
python main.py session
```

## 📖 Usage

### Run Monitoring System

```bash
python main.py monitor
```

### Run Dashboard

```bash
python main.py dashboard
```

### Run Both Together

```bash
python main.py both
```

### Display Subscribed Channels

```bash
python main.py channels
```

### Export Data

```bash
# Export CSV
python main.py export --format csv

# Export JSON
python main.py export --format json
```

## ⚙️ Configuration

### `.env` File

```env
# Telegram API (required)
API_ID=123456
API_HASH=your_api_hash_here
NOTIFY_USER_ID=your_telegram_id

# Bot (optional)
BOT_TOKEN=your_bot_token

# Discord (optional)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# Email (optional)
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your@email.com
EMAIL_PASSWORD=your_app_password
EMAIL_TO=recipient@email.com

# Dashboard
DASHBOARD_SECRET_KEY=your_secret_key
DASHBOARD_PORT=5000
```

## 🤖 Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Main menu |
| `/help` | Show help |
| `/status` | System status |
| `/channels` | Display channels |
| `/addchannel @username` | Add channel |
| `/removechannel @username` | Remove channel |
| `/keywords` | Display keywords |
| `/addkeyword word` | Add keyword |
| `/removekeyword word` | Remove keyword |
| `/stats` | Statistics |
| `/recent` | Recent messages |
| `/export` | Export data |

### Adding Regex Keyword

```
/addkeyword regex:\d+%\s*off
```

## 📁 Project Structure

```
channel_monitor/
├── main.py              # Main entry point
├── monitor.py           # Monitoring system
├── config.py            # Settings management
├── database.py          # Database
├── logger.py            # Logging system
├── notifications.py     # Notifications system
├── search_engine.py     # Search engine
├── scheduler.py         # Scheduling and auto-restart
├── bot.py               # Control bot
├── exporter.py          # Data export
├── requirements.txt     # Requirements
├── .env                 # Settings (not committed)
├── .env.example         # Settings example
├── .gitignore           # Excluded files
└── dashboard/           # Control panel
    ├── app.py
    └── templates/
        ├── base.html
        ├── index.html
        ├── channels.html
        ├── keywords.html
        ├── messages.html
        └── stats.html
```

## 🔧 Development

### Adding a New Notification Provider

```python
from notifications import NotificationProvider, NotificationMessage

class SlackNotifier(NotificationProvider):
    name = "slack"
    
    def is_configured(self) -> bool:
        return bool(self.webhook_url)
    
    async def send(self, message: NotificationMessage) -> bool:
        # Implement sending
        pass
```

### Adding Custom Search Pattern

```python
from search_engine import SearchEngine, MatchType

engine = SearchEngine()
engine.add_pattern(r'\$\d+\.?\d*', MatchType.REGEX)  # Dollar prices
engine.add_pattern('discount', MatchType.CONTAINS)   # Regular word
```

## 🛡️ Security

- ⚠️ Never share `.env` file
- ⚠️ Never share `.session` files
- ✅ Use `.gitignore` to protect sensitive files
- ✅ Use strong passwords for dashboard

## 📝 License

This project is licensed under [MIT License](LICENSE).

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the project
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

- 📧 Email: your@email.com
- 💬 Telegram: @yourusername
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/channel_monitor/issues)

---

⭐ If you like the project, don't forget to give it a star!
