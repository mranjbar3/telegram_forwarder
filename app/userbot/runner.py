import asyncio
import logging
import os
from datetime import datetime

from telethon import TelegramClient, events
from telethon.tl.types import Channel, Chat

from app.config import settings
from app.database import SyncSessionLocal
from app.models import SourceChannel, MessageQueue, MessageStatus, LLMPrompt
from app.services.chat_id import to_telethon
from app.services.filter import FilterService
from app.services.llm import LLMService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("userbot")

SESSION_DIR = "/app/sessions"
MEDIA_DIR = "/app/media"
os.makedirs(SESSION_DIR, exist_ok=True)
os.makedirs(MEDIA_DIR, exist_ok=True)
SESSION_PATH = os.path.join(SESSION_DIR, settings.TG_SESSION_NAME)


# ─────────── helpers ───────────
def _get_active_prompt(db, prompt_type: str, chat_id_str: str):
    q = db.query(LLMPrompt).filter_by(prompt_type=prompt_type, is_active=True)
    numeric = None
    if not str(chat_id_str).startswith("@"):
        try:
            numeric = int(chat_id_str)
        except (ValueError, TypeError):
            pass
    if numeric is not None:
        spec = q.filter(LLMPrompt.applies_to_chat_id == numeric).order_by(LLMPrompt.order).first()
        if spec:
            return spec.prompt
    gen = q.filter(LLMPrompt.applies_to_chat_id.is_(None)).order_by(LLMPrompt.order).first()
    return gen.prompt if gen else None


def _find_source(db, chat_id_str: str, username: str | None):
    for cand in [chat_id_str, f"@{username}" if username else None]:
        if not cand:
            continue
        src = db.query(SourceChannel).filter_by(chat_id=cand, is_active=True).first()
        if src:
            return src
    return None


async def _download_media(message) -> tuple[str, str]:
    if not message.media:
        return "", ""
    if message.photo:
        mtype = "photo"
    elif message.video_note:
        mtype = "video_note"
    elif message.voice:
        mtype = "voice"
    elif message.video:
        mtype = "video"
    elif message.audio:
        mtype = "audio"
    elif message.gif:
        mtype = "animation"
    else:
        mtype = "document"

    unique = f"{message.chat_id}_{message.id}_{int(datetime.now().timestamp())}"
    try:
        path = await message.download_media(file=os.path.join(MEDIA_DIR, unique))
        return (path or "", mtype)
    except Exception as e:
        logger.warning("Media download failed msg=%s: %s", message.id, e)
        return "", ""


# ─────────── shared message processing ───────────
async def process_message(message, source_id: int, chat_title: str):
    """منطق مشترک پردازش یک پیام — از event و poller استفاده می‌شود."""
    with SyncSessionLocal() as db:
        src = db.get(SourceChannel, source_id)
        if not src or not src.is_active:
            return

        text = message.text or message.caption or ""
        filter_svc = FilterService(db)
        skip, reason = filter_svc.should_skip(text)

        llm = LLMService()
        llm_reason = ""
        if not skip and text:
            prompt = _get_active_prompt(db, "classify", src.chat_id)
            if prompt:
                r = await llm.classify(text, prompt)
                if r["is_spam"]:
                    skip = True
                    llm_reason = r["reason"]
                    reason = f"llm_spam: {llm_reason}"

        # ─── ۳. LLM clean + هدر/فوتر ───
        cleaned = text
        if not skip and text:
            # ۳-الف. LLM clean (اختیاری — اگر پرامپت وجود دارد)
            prompt = _get_active_prompt(db, "clean", src.chat_id)
            if prompt:
                try:
                    cleaned = await llm.clean(text, prompt)
                except Exception as e:
                    logger.warning("LLM clean failed: %s", e)
                    cleaned = text

            # ۳-ب. هدر/فوتر از FilterService (همیشه اعمال می‌شود)
            cleaned = filter_svc.apply_decorations(cleaned)

        media_path, media_type = await _download_media(message)

        saved = 0
        for dest in src.destinations:
            if not dest.is_active:
                continue
            exists = db.query(MessageQueue).filter_by(
                source_chat_id=src.chat_id,
                source_message_id=message.id,
                dest_chat_id=dest.chat_id,
            ).first()
            if exists:
                continue
            db.add(MessageQueue(
                source_chat_id=src.chat_id,
                source_message_id=message.id,
                dest_chat_id=dest.chat_id,
                source_chat_title=src.title or chat_title,
                dest_chat_title=dest.title,
                content_preview=text[:300],
                cleaned_text=cleaned[:3000],
                media_path=media_path,
                media_type=media_type,
                status=MessageStatus.SPAM.value if skip else MessageStatus.PENDING.value,
                error_message=reason if skip else "",
                llm_reason=llm_reason,
            ))
            saved += 1
        db.commit()
        if saved:
            logger.info("Queued msg=%s from %s → %d dests (skip=%s)",
                        message.id, src.title, saved, skip)


# ─────────── real-time event handler ───────────
async def handle_new_message(event):
    chat = await event.get_chat()
    if not isinstance(chat, (Channel, Chat)):
        return

    chat_id_str = str(event.chat_id)
    username = getattr(chat, "username", None)

    with SyncSessionLocal() as db:
        src = _find_source(db, chat_id_str, username)
        if not src:
            return
        src_id = src.id
        src_title = src.title
    await process_message(event.message, src_id, getattr(chat, "title", src_title))


# ─────────── periodic poller ───────────
async def poll_loop(client):
    logger.info("Poller started (interval=%ss, batch=%s, max_catchup=%s)",
                settings.POLL_INTERVAL, settings.POLL_BATCH, settings.POLL_MAX_CATCHUP)

    # ─── startup: initialize cursors for NEW sources only ───
    with SyncSessionLocal() as db:
        for s in db.query(SourceChannel).filter(
            SourceChannel.is_active.is_(True),
            SourceChannel.last_message_id == 0,
        ).all():
            try:
                ent = await client.get_entity(to_telethon(s.chat_id))
                latest = await client.get_messages(ent, limit=1)
                if latest:
                    s.last_message_id = latest[0].id
                    db.commit()
                    logger.info("Cursor init %s → %d (skip backlog)", s.chat_id, s.last_message_id)
            except Exception as e:
                logger.warning("Init failed %s: %s", s.chat_id, e)

    # ─── immediate first poll (catch-up) ───
    await _poll_once(client)

    while True:
        await asyncio.sleep(settings.POLL_INTERVAL)
        try:
            await _poll_once(client)
        except Exception:
            logger.exception("Poller loop error")


async def _poll_once(client):
    """یک دور پیمایش همه‌ی منابع. اگر ستون last_message_id قدیمی باشد، کچ‌آپ می‌کند."""
    with SyncSessionLocal() as db:
        sources = db.query(SourceChannel).filter(
            SourceChannel.is_active.is_(True),
            SourceChannel.last_message_id > 0,
        ).all()

        for s in sources:
            try:
                ent = await client.get_entity(to_telethon(s.chat_id))

                # ─── catch-up detection ───
                latest = await client.get_messages(ent, limit=1)
                if not latest:
                    continue
                latest_id = latest[0].id
                gap = latest_id - s.last_message_id
                fetch_limit = settings.POLL_BATCH

                if gap > settings.POLL_BATCH:
                    if settings.POLL_MAX_CATCHUP and gap > settings.POLL_MAX_CATCHUP:
                        # صف خیلی قدیمی است → فقط آخرین POLL_MAX_CATCHUP را بگیر
                        s.last_message_id = latest_id - settings.POLL_MAX_CATCHUP
                        db.commit()
                        logger.warning("Cursor %s too old (gap=%d), capped to %d",
                                       s.chat_id, gap, s.last_message_id)
                    fetch_limit = min(gap, settings.POLL_MAX_CATCHUP or gap)
                    logger.info("Catch-up %s: gap=%d, fetching %d",
                                s.chat_id, gap, fetch_limit)

                new_msgs = await client.get_messages(
                    ent, limit=fetch_limit, min_id=s.last_message_id
                )
                if not new_msgs:
                    continue

                for msg in reversed(new_msgs):
                    await process_message(msg, s.id, s.title)

                s.last_message_id = max(m.id for m in new_msgs)
                db.commit()
                logger.info("Polled %s: %d new (cursor=%d)",
                            s.chat_id, len(new_msgs), s.last_message_id)
            except Exception as e:
                logger.warning("Poll %s failed: %s", s.chat_id, e)


# ─────────── main ───────────
async def main():
    client = TelegramClient(SESSION_PATH, settings.TG_API_ID, settings.TG_API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        logger.error("Session invalid. Run: docker compose run --rm -it userbot python -m app.userbot.login")
        await client.disconnect()
        return

    me = await client.get_me()
    logger.info("Userbot logged in as @%s (id=%s)", me.username, me.id)

    # Resolve sources
    with SyncSessionLocal() as db:
        for s in db.query(SourceChannel).filter_by(is_active=True).all():
            try:
                ent = await client.get_entity(to_telethon(s.chat_id))
                logger.info("Resolved %s → %s", s.chat_id, getattr(ent, "title", "?"))
            except Exception as e:
                logger.warning("Cannot resolve %s: %s", s.chat_id, e)

    # Real-time event handler
    client.add_event_handler(handle_new_message, events.NewMessage())

    # Periodic poller as backup
    poller_task = None
    if settings.POLL_ENABLED:
        poller_task = asyncio.create_task(poll_loop(client))

    try:
        await client.run_until_disconnected()
    finally:
        if poller_task:
            poller_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
