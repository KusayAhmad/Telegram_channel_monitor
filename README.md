# 📡 Telegram Channel Monitor

نظام متكامل لمراقبة قنوات تيليغرام والبحث عن كلمات مفتاحية محددة مع إشعارات فورية متعددة.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Pyrogram](https://img.shields.io/badge/Pyrogram-2.0+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ المميزات

### 🔍 المراقبة والبحث
- ✅ مراقبة قنوات متعددة في آن واحد
- ✅ بحث بالكلمات المفتاحية العادية
- ✅ دعم التعابير النمطية (Regex) للبحث المتقدم
- ✅ تجنب تكرار الإشعارات للرسائل المكتشفة

### 📢 الإشعارات
- ✅ إشعارات Telegram فورية
- ✅ دعم Discord Webhooks
- ✅ إشعارات البريد الإلكتروني
- ✅ إمكانية إضافة مزودين جدد

### 🤖 بوت التحكم
- ✅ إدارة القنوات (إضافة/حذف/تفعيل)
- ✅ إدارة الكلمات المفتاحية
- ✅ عرض الإحصائيات
- ✅ تصدير البيانات

### 🌐 لوحة تحكم ويب
- ✅ واجهة عربية أنيقة
- ✅ إحصائيات ورسوم بيانية
- ✅ إدارة كاملة عبر المتصفح
- ✅ تصدير البيانات (CSV/JSON)

### ⚙️ خصائص تقنية
- ✅ قاعدة بيانات SQLite
- ✅ نظام تسجيل شامل (Logging)
- ✅ إعادة تشغيل تلقائي عند الفشل
- ✅ جدولة المراقبة بأوقات محددة

## 🚀 التثبيت

### 1. استنساخ المشروع

```bash
git clone https://github.com/yourusername/channel_monitor.git
cd channel_monitor
```

### 2. إنشاء البيئة الافتراضية

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. تثبيت المتطلبات

```bash
pip install -r requirements.txt
```

### 4. إعداد ملف البيئة

```bash
# نسخ ملف المثال
copy .env.example .env

# تعديل الإعدادات
notepad .env
```

### 5. الحصول على بيانات Telegram API

1. اذهب إلى [my.telegram.org](https://my.telegram.org)
2. سجل دخول برقم هاتفك
3. انقر على "API Development Tools"
4. أنشئ تطبيق جديد
5. انسخ `API_ID` و `API_HASH`

### 6. إنشاء الجلسة

```bash
python main.py session
```

## 📖 الاستخدام

### تشغيل نظام المراقبة

```bash
python main.py monitor
```

### تشغيل لوحة التحكم

```bash
python main.py dashboard
```

### تشغيل كلاهما معاً

```bash
python main.py both
```

### عرض القنوات المشترك بها

```bash
python main.py channels
```

### تصدير البيانات

```bash
# تصدير CSV
python main.py export --format csv

# تصدير JSON
python main.py export --format json
```

## ⚙️ الإعدادات

### ملف `.env`

```env
# Telegram API (مطلوب)
API_ID=123456
API_HASH=your_api_hash_here
NOTIFY_USER_ID=your_telegram_id

# البوت (اختياري)
BOT_TOKEN=your_bot_token

# Discord (اختياري)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# البريد الإلكتروني (اختياري)
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your@email.com
EMAIL_PASSWORD=your_app_password
EMAIL_TO=recipient@email.com

# لوحة التحكم
DASHBOARD_SECRET_KEY=your_secret_key
DASHBOARD_PORT=5000
```

## 🤖 أوامر البوت

| الأمر | الوصف |
|-------|-------|
| `/start` | القائمة الرئيسية |
| `/help` | عرض المساعدة |
| `/status` | حالة النظام |
| `/channels` | عرض القنوات |
| `/addchannel @username` | إضافة قناة |
| `/removechannel @username` | حذف قناة |
| `/keywords` | عرض الكلمات |
| `/addkeyword كلمة` | إضافة كلمة |
| `/removekeyword كلمة` | حذف كلمة |
| `/stats` | الإحصائيات |
| `/recent` | آخر الرسائل |
| `/export` | تصدير البيانات |

### إضافة كلمة Regex

```
/addkeyword regex:\d+%\s*off
```

## 📁 هيكل المشروع

```
channel_monitor/
├── main.py              # نقطة الدخول الرئيسية
├── monitor.py           # نظام المراقبة
├── config.py            # إدارة الإعدادات
├── database.py          # قاعدة البيانات
├── logger.py            # نظام التسجيل
├── notifications.py     # نظام الإشعارات
├── search_engine.py     # محرك البحث
├── scheduler.py         # الجدولة والإعادة التلقائية
├── bot.py               # بوت التحكم
├── exporter.py          # تصدير البيانات
├── requirements.txt     # المتطلبات
├── .env                 # الإعدادات (لا يُرفع)
├── .env.example         # مثال الإعدادات
├── .gitignore           # الملفات المستثناة
└── dashboard/           # لوحة التحكم
    ├── app.py
    └── templates/
        ├── base.html
        ├── index.html
        ├── channels.html
        ├── keywords.html
        ├── messages.html
        └── stats.html
```

## 🔧 التطوير

### إضافة مزود إشعارات جديد

```python
from notifications import NotificationProvider, NotificationMessage

class SlackNotifier(NotificationProvider):
    name = "slack"
    
    def is_configured(self) -> bool:
        return bool(self.webhook_url)
    
    async def send(self, message: NotificationMessage) -> bool:
        # تنفيذ الإرسال
        pass
```

### إضافة نمط بحث مخصص

```python
from search_engine import SearchEngine, MatchType

engine = SearchEngine()
engine.add_pattern(r'\$\d+\.?\d*', MatchType.REGEX)  # أسعار بالدولار
engine.add_pattern('خصم', MatchType.CONTAINS)        # كلمة عادية
```

## 🛡️ الأمان

- ⚠️ لا تشارك ملف `.env` أبداً
- ⚠️ لا تشارك ملفات `.session`
- ✅ استخدم `.gitignore` لحماية الملفات الحساسة
- ✅ استخدم كلمات مرور قوية للوحة التحكم

## 📝 الترخيص

هذا المشروع مرخص تحت [MIT License](LICENSE).

## 🤝 المساهمة

المساهمات مرحب بها! يرجى:

1. Fork المشروع
2. أنشئ branch للميزة (`git checkout -b feature/amazing-feature`)
3. Commit التغييرات (`git commit -m 'Add amazing feature'`)
4. Push إلى الـ branch (`git push origin feature/amazing-feature`)
5. افتح Pull Request

## 📞 الدعم

- 📧 Email: your@email.com
- 💬 Telegram: @yourusername
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/channel_monitor/issues)

---

⭐ إذا أعجبك المشروع، لا تنسَ إعطاءه نجمة!
