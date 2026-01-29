from pyrogram import Client, filters

# معلومات حساب Telegram API الخاصة بك
api_id = 24327631      # ← استبدل هذا بـ API ID من my.telegram.org
api_hash = "9336fcbafd7ad01f90942a554343504c"  # ← استبدله بـ API Hash

# إعدادات المراقبة
keywords = ["Only Order", "Only Buy", "Only rating",]  # ← الكلمات التي تريد البحث عنها
channels_to_monitor = ["@Ninja_Tester", "@CollectManiaa","@AmzGoldenDeals","@kingi_amz","@leepremiumde"]  # ← القنوات التي تريد مراقبتها
notify_user_id = 1641576293  # ← معرّفك الشخصي في تيليغرام (استخدم @userinfobot للحصول عليه)

# تهيئة الجلسة
app = Client("my_account", api_id=api_id, api_hash=api_hash)

@app.on_message(filters.chat(channels_to_monitor))
async def check_keywords(client, message):
    text = message.text or message.caption or ""
    for keyword in keywords:
        if keyword.lower() in text.lower():
            channel_name = message.chat.username or message.chat.title
            await client.send_message(
                notify_user_id,
                f"**Word Found** `{keyword}` **In Channel** @{channel_name}:\n\n{text}"
            )
            break

print("Monitoring started... Press Ctrl+C to stop.")
app.run()
