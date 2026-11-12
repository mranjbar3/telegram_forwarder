from typing import Union


def normalize_input(raw: str) -> str:
    """ورودی کاربر → فرمت استاندارد ذخیره."""
    raw = raw.strip()
    if not raw:
        return ""
    if raw.startswith("@") or raw.startswith("-"):
        return raw
    try:
        int(raw)
        return raw
    except ValueError:
        pass
    if all(c.isalnum() or c == "_" for c in raw):
        return f"@{raw}"
    raise ValueError(f"شناسه نامعتبر: {raw}")


def to_aiogram(stored: str) -> Union[int, str]:
    """فرمت مناسب برای aiogram."""
    stored = str(stored).strip()
    if stored.startswith("@"):
        return stored
    try:
        return int(stored)
    except ValueError:
        return f"@{stored}"


def to_telethon(stored: str) -> Union[int, str]:
    """
    فرمت مناسب برای Telethon.
    - @username → همان رشته با @
    - -1001234567890 (Bot API channel) → 1234567890 (Telethon channel id، بدون -100)
    - -987654321 (گروه قدیمی) → 987654321
    - 1234567890 (کاربر) → 1234567890
    """
    stored = str(stored).strip()
    if stored.startswith("@"):
        return stored
    try:
        n = int(stored)
    except ValueError:
        return f"@{stored}"
    if n < 0 and str(n).startswith("-100"):
        return int(str(n)[4:])
    if n < 0:
        return abs(n)
    return n
