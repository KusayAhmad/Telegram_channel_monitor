from pyrogram import Client, filters

# Your Telegram API account information
api_id = 24327631      # ← Replace this with API ID from my.telegram.org
api_hash = "9336fcbafd7ad01f90942a554343504c"  # ← Replace with API Hash

# Monitoring settings
keywords = ["Only Order", "Only Buy", "Only rating",]  # ← Keywords you want to search for
channels_to_monitor = ["@Ninja_Tester", "@CollectManiaa","@AmzGoldenDeals","@kingi_amz","@leepremiumde"]  # ← Channels you want to monitor
notify_user_id = 1641576293  # ← Your personal ID on Telegram (use @userinfobot to get it)

# Session setup
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
