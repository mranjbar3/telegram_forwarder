import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

from app.config import settings
from app.database import SyncSessionLocal
from app.models import SourceChannel, MessageQueue, MessageStatus
from app.services.filter import FilterService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bot")

dp = Dispatcher()


@dp.channel_post(F.chat.type == "channel")
async def handle_channel_post(message: Message, bot: Bot) -> None:
    """
    اگر ربات در کانال مبدأ ادمین باشد، پیام مستقیم از Bot API می‌آید.
    در حالت عادی (کاربر userbot)، این handler اجرا نمی‌شود چون ربات ادمین نیست.
    """
    chat_id_str = str(message.chat.id)   # ← فیکس: str، نه int
    chat_title = message.chat.title or chat_id_str

    with SyncSessionLocal() as db:
        source = (
            db.query(SourceChannel)
            .filter_by(chat_id=chat_id_str, is_active=True)
            .first()
        )
        if not source:
            logger.debug("Bot: no source for chat_id=%s", chat_id_str)
            return

        text = message.text or message.caption or ""
        filter_svc = FilterService(db)
        skip, reason = filter_svc.should_skip(text)

        created = 0
        for dest in source.destinations:
            if not dest.is_active:
                continue
            exists = db.query(MessageQueue).filter_by(
                source_chat_id=chat_id_str,
                source_message_id=message.message_id,
                dest_chat_id=dest.chat_id,
            ).first()
            if exists:
                continue
            db.add(MessageQueue(
                source_chat_id=chat_id_str,
                source_message_id=message.message_id,
                dest_chat_id=dest.chat_id,
                source_chat_title=chat_title,
                dest_chat_title=dest.title,
                content_preview=text[:300],
                cleaned_text=text[:3000],
                status=MessageStatus.SPAM.value if skip else MessageStatus.PENDING.value,
                error_message=reason if skip else "",
            ))
            created += 1
        db.commit()
        logger.info("Bot captured msg=%s from %s → %d dests",
                    message.message_id, source.title, created)


@dp.message(Command("ping"))
async def cmd_ping(message: Message) -> None:
    await message.answer("🏓 pong")


async def main() -> None:
    bot = Bot(token=settings.BOT_TOKEN)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
