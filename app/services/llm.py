import json
import logging
import re
from typing import Optional
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """ارتباط با llama.cpp server برای طبقه‌بندی و پاکسازی متن."""

    def __init__(self):
        self.base = settings.LLAMA_SERVER_URL.rstrip("/")
        self.enabled = settings.LLM_ENABLED
        self.timeout = settings.LLM_TIMEOUT

    async def _complete(self, prompt: str, n_predict: int = 256) -> str:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base}/completion",
                json={
                    "prompt": prompt,
                    "n_predict": n_predict,
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "stop": ["</answer>", "<|im_end|>", "\n\n\n"],
                },
            )
            resp.raise_for_status()
            return resp.json().get("content", "").strip()

    @staticmethod
    def _extract_json(text: str) -> Optional[dict]:
        # مدل ممکن است JSON را داخل متن بگذارد؛ اولین { ... } را می‌گیریم.
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if not m:
            return None
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            return None

    async def classify(self, text: str, prompt_template: str) -> dict:
        """آیا پیام تبلیغاتی/اسپم است؟"""
        if not self.enabled or not text.strip():
            return {"is_spam": False, "reason": ""}

        prompt = (
            f"{prompt_template}\n\n"
            "متن پیام:\n"
            f"«{text[:2000]}»\n\n"
            "فقط یک JSON به شکل زیر برگردان و هیچ توضیح اضافه نده:\n"
            '{"is_spam": true/false, "reason": "دلیل کوتاه"}'
        )
        try:
            raw = await self._complete(prompt)
            data = self._extract_json(raw) or {}
            return {
                "is_spam": bool(data.get("is_spam", False)),
                "reason": str(data.get("reason", ""))[:300],
            }
        except Exception as e:
            logger.warning("LLM classify failed: %s", e)
            return {"is_spam": False, "reason": f"llm_error: {e}"}

    async def clean(self, text: str, prompt_template: str) -> str:
      if not self.enabled or not text.strip():
        return text

      prompt = (
        f"{prompt_template}\n\n"
        "متن اصلی:\n"
        f"«{text[:3000]}»\n\n"
        "فقط متن پاک‌سازی‌شده را بدون هیچ تگ، برچسب یا توضیح اضافه برگردان."
      )
      try:
        raw = await self._complete(prompt, n_predict=512)
        # ۱. اگر داخل <answer>...</answer> بود، محتوا را بیرون بکش
        m = re.search(r"<answer>(.*?)</answer>", raw, re.DOTALL)
        out = m.group(1) if m else raw
        # ۲. هر تگ <answer> یا </answer> باقی‌مانده را پاک کن
        out = re.sub(r"</?answer>", "", out)
        # ۳. تگ‌های HTML/XML دیگر را هم حذف کن (احتیاط)
        out = re.sub(r"</?(?:response|output|result)>", "", out, flags=re.I)
        out = out.strip()
        return out or text
      except Exception as e:
        logger.warning("LLM clean failed: %s", e)
        return text
