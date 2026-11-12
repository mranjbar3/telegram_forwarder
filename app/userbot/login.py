"""
لاگین تعاملی یک‌باره userbot.
اجرا:
  docker compose run --rm -it userbot python -m app.userbot.login
"""
import asyncio
import os
from telethon import TelegramClient
from app.config import settings

SESSION_DIR = "/app/sessions"

async def main():
    os.makedirs(SESSION_DIR, exist_ok=True)
    session_path = os.path.join(SESSION_DIR, settings.TG_SESSION_NAME)
    client = TelegramClient(session_path, settings.TG_API_ID, settings.TG_API_HASH)

    print("→ در حال اتصال به تلگرام...")
    await client.start(phone=settings.TG_PHONE)
    me = await client.get_me()
    print(f"\n✅ لاگین موفق!")
    print(f"   نام: {me.first_name}")
    print(f"   یوزرنیم: @{me.username}")
    print(f"   id: {me.id}")
    print(f"   session: {session_path}.session\n")
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
