import logging
import os
from datetime import datetime, timezone

from aiogram import Bot
from aiogram.exceptions import (
    TelegramRetryAfter, TelegramBadRequest, TelegramNetworkError, TelegramForbiddenError,
)
from aiogram.types import FSInputFile
from sqlalchemy.orm import Session

from app.models import MessageQueue, MessageStatus
from app.services.chat_id import to_aiogram

logger = logging.getLogger(__name__)


async def _send_media(bot, dest, item):
    path = item.media_path
    caption = (item.cleaned_text or "")[:1024]
    media = FSInputFile(path)
    t = (item.media_type or "").lower()
    if t == "photo":     return await bot.send_photo(dest, media, caption=caption)
    if t == "video":     return await bot.send_video(dest, media, caption=caption, supports_streaming=True)
    if t == "voice":     return await bot.send_voice(dest, media, caption=caption)
    if t == "audio":     return await bot.send_audio(dest, media, caption=caption)
    if t == "animation": return await bot.send_animation(dest, media, caption=caption)
    if t == "video_note":return await bot.send_video_note(dest, media)
    return await bot.send_document(dest, media, caption=caption)


async def forward_one(bot: Bot, db: Session, item: MessageQueue, rate_limiter) -> None:
    if item.status not in (MessageStatus.PENDING.value, MessageStatus.UNKNOWN.value):
        return

    dest = to_aiogram(item.dest_chat_id)
    await rate_limiter.acquire(str(item.dest_chat_id))

    try:
        if item.media_path and os.path.exists(item.media_path):
            sent = await _send_media(bot, dest, item)
        elif (item.cleaned_text or item.content_preview or "").strip():
            # ← این خط مهم است: هرگز copy_message نمی‌زنیم
            sent = await bot.send_message(
                chat_id=dest,
                text=(item.cleaned_text or item.content_preview)[:4096],
                disable_web_page_preview=True,
            )
        else:
            item.status = MessageStatus.FAILED.value
            item.error_message = "empty_content"
            db.commit()
            return

        item.status = MessageStatus.SENT.value
        item.sent_message_id = sent.message_id
        item.sent_at = datetime.now(timezone.utc)
        item.error_message = ""

        if item.media_path and os.path.exists(item.media_path):
            try:
                os.remove(item.media_path)
            except OSError:
                pass
            item.media_path = ""

    except TelegramRetryAfter as e:
        item.retry_count += 1
        item.error_message = f"429 retry after {e.retry_after}s"
        db.commit()
        import asyncio
        await asyncio.sleep(min(e.retry_after, 60))
        return
    except (TelegramBadRequest, TelegramForbiddenError) as e:
        item.status = MessageStatus.FAILED.value
        item.error_message = str(e)
        logger.error("Bad request (%s): %s", dest, e)
    except TelegramNetworkError as e:
        item.status = MessageStatus.UNKNOWN.value
        item.error_message = f"Network: {e}"
    except Exception as e:
        item.retry_count += 1
        if item.retry_count >= 5:
            item.status = MessageStatus.FAILED.value
        else:
            item.status = MessageStatus.UNKNOWN.value
        item.error_message = f"Unknown: {e}"
        logger.exception("Forward error")
    finally:
        db.commit()
