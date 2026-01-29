import asyncio
import nest_asyncio
from pyrogram import Client
from pyrogram.types import ChatType

api_id = 24327631  # ← Put your API_ID here
api_hash  = "9336fcbafd7ad01f90942a554343504c"  # ← Put your API_HASH here
session_name = "my_account"  # ← Session name you want to use




app = Client("my_account", api_id=api_id, api_hash=api_hash)

async def main():
    await app.start()

    print("📢 Channels you are subscribed to:\n")

    async for dialog in app.get_dialogs():
        if dialog.chat.type in [ChatType.CHANNEL, ChatType.SUPERGROUP]:
            print(f"📣 {dialog.chat.title} - @{dialog.chat.username}")

    await app.stop()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())