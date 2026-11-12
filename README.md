# 📨 Telegram Mirror Pro — سامانه‌ی انتقال و مدیریت پیام تلگرام

> نسخه‌ی جاری: v10 — رابط کاربری MADAR · چندزبانه (فارسی / انگلیسی / عربی)

---

## 📖 درباره‌ی پروژه

**Telegram Mirror Pro** یک سامانه‌ی کامل و متن‌باز برای مدیریت و انتقال پیام از کانال‌های مبدأ تلگرام به کانال‌های مقصد است. این سامانه برای خبرگزاری‌ها، رسانه‌ها، تیم‌های محتوایی و هر کسی که نیاز به مدیریت چندین کانال تلگرام به صورت همزمان و با فیلترهای هوشمند دارد، طراحی شده است.

### ✨ قابلیت‌های اصلی

| دسته | قابلیت |
|---|---|
| **انتقال پیام** | انتقال خودکار از کانال مبدأ به یک یا چند کانال مقصد، بدون نیاز به ادمین بودن ربات در کانال‌های مبدأ |
| **پشتیبانی مدیا** | متن، عکس، ویدئو، فایل، ویس و استیکر |
| **فیلتر هوشمند** | کلمات ممنوعه، الگوهای Regex، هدر/فوتر اختصاصی، فیلتر محتوا بر اساس LLM |
| **پاکسازی خودکار** | حذف لینک‌ها و تبلیغات با استفاده از LLM محلی (llama.cpp) |
| **پایگاه داده‌ی کامل** | ثبت تمام پیام‌ها، وضعیت ارسال، متن نهایی، زمان و خطاها |
| **صف پایدار** | عدم از دست رفتن پیام‌ها حتی هنگام خاموش شدن سرویس |
| **پنل مدیریت مدرن** | رابط کاربری تیره با نمودار، داشبورد و پشتیبانی کامل RTL |
| **چندزبانه** | فارسی (پیش‌فرض)، انگلیسی، عربی — قابل تغییر در لحظه |
| **مدیریت کشورها** | اختصاص کشور به هر کانال، فیلتر و توزیع بر اساس کشور |
| **انتشار دستی** | ارسال پیام از پنل به یک یا چند کانال مقصد |
| **زمان‌بندی** | ارسال فوری یا زمان‌بندی با تقویم شمسی |
| **سیستم اعلان** | ارسال اعلان به کاربران، با هدف‌گیری بر اساس نقش |
| **لاگ کامل** | ثبت و نمایش تمام اقدامات کاربران با نمودار فعالیت |
| **خروجی CSV** | دریافت گزارش کامل از سوابق ارسال |
| **بکاپ خودکار** | پشتیبان‌گیری روزانه از دیتابیس با چرخش فایل |

### 🏗️ معماری

```
┌──────────────┐    ┌───────────────┐    ┌──────────────┐
│  bot         │    │  userbot      │    │  llama.cpp   │
│  (aiogram)   │    │  (Telethon)   │    │  (LLM)       │
│  Bot API     │    │  MTProto      │    │  GGUF model  │
└──────┬───────┘    └───────┬───────┘    └──────┬───────┘
       │                    │                   │
       │   ┌────────────────┴───────────────────┘
       │   │
       ▼   ▼
  ┌───────────────────┐    ┌──────────────┐
  │  PostgreSQL       │    │  Redis       │
  │  (کل داده‌ها)      │    │  (صف + کش)   │
  └────────┬──────────┘    └──────┬───────┘
           │                      │
           ▼                      ▼
    ┌─────────────────────────────────────┐
    │  Worker (Celery) + Beat             │
    │  ارسال واقعی به کانال‌های مقصد       │
    └──────────────────┬──────────────────┘
                       │
                       ▼
    ┌─────────────────────────────────────┐
    │  API (FastAPI) — پنل مدیریت فارسی   │
    └─────────────────────────────────────┘
```

### 📦 سرویس‌های Docker

| سرویس | نقش |
|---|---|
| `api` | پنل مدیریت + REST API (FastAPI + Jinja2) |
| `bot` | ربات تلگرام (aiogram) — برای webhook و دستورات تعاملی |
| `userbot` | اکانت کاربری (Telethon) — برای خواندن کانال‌های عمومی |
| `worker` | Celery Worker — ارسال واقعی پیام‌ها با رعایت Rate Limit |
| `beat` | Celery Beat — زمان‌بند (بازیابی UNKNOWN، بکاپ) |
| `db` | PostgreSQL 16 |
| `redis` | Redis 7 — صف Celery و rate limiter |
| `llama` | llama.cpp server — تحلیل محتوا با LLM سبک |
| `backup` | پشتیبان‌گیری خودکار روزانه |

---

## 🚀 موارد لازم برای اجرا

### پیش‌نیازهای سیستم

| مورد | حداقل | توصیه‌شده |
|---|---|---|
| CPU | ۲ هسته | ۴ هسته |
| RAM | ۴ گیگابایت | ۸ گیگابایت |
| Disk | ۲۰ گیگابایت | ۵۰ گیگابایت |
| OS | Linux (Ubuntu 22.04+) | Ubuntu 24.04 |
| Docker | 24.0+ | 26.0+ |
| Docker Compose | v2.20+ | v2.25+ |

### کلیدها و توکن‌های لازم

| متغیر | نحوه‌ی دریافت |
|---|---|
| `BOT_TOKEN` | [@BotFather](https://t.me/BotFather) → `/newbot` → کپی توکن |
| `TG_API_ID` | [my.telegram.org](https://my.telegram.org) → API development tools |
| `TG_API_HASH` | همان‌جا، در کنار `api_id` |
| `TG_PHONE` | شماره‌ی موبایل اکانت userbot با فرمت بین‌المللی (`+989123456789`) |
| `SECRET_KEY` | یک رشته‌ی تصادفی بلند — مثلاً `openssl rand -hex 32` |
| `ADMIN_PASSWORD` | رمز مدیر (پیش‌فرض `admin123` — حتماً تغییر دهید) |

### مراحل اجرا

```bash
# ۱. کلون پروژه
git clone <repo-url> telegram-forwarder
cd telegram-forwarder

# ۲. کپی فایل تنظیمات
cp .env.example .env

# ۳. ویرایش .env — حداقل این موارد را پر کنید:
#    BOT_TOKEN, TG_API_ID, TG_API_HASH, TG_PHONE,
#    SECRET_KEY, ADMIN_PASSWORD
nano .env

# ۴. آماده‌سازی پوشه‌ها روی host
mkdir -p sessions backups media models
sudo chown -R 1000:1000 sessions media 2>/dev/null || true

# ۵. دریافت مدل LLM (پیشنهاد: Qwen2.5-1.5B)
cd models
wget https://huggingface.co/bartowski/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/Qwen2.5-1.5B-Instruct-Q4_K_M.gguf -O model.gguf
cd ..

# ۶. ساخت و اجرا
docker compose up -d --build

# ۷. لاگین یک‌باره‌ی userbot (تعاملی)
docker compose run --rm -it userbot python -m app.userbot.login
# کد تایید و رمز دو مرحله‌ای (اگر فعال است) را وارد کنید

# ۸. ری‌استارت userbot
docker compose restart userbot

# ۹. مشاهده‌ی لاگ‌ها
docker compose logs -f api worker userbot

# ۱۰. ورود به پنل
# http://localhost:8000/auth/login
# نام کاربری: admin
# رمز عبور: از ADMIN_PASSWORD در .env
```

### 🐢 اگر در ایران هستید — دور زدن فیلترینگ

Docker از پروکسی میزبان به صورت خودکار استفاده نمی‌کند. سه گزینه دارید:

**گزینه‌ی A — استفاده از پروکسی HTTP میزبان (توصیه‌شده):**

در `docker-compose.yml` برای سرویس‌های `bot` و `worker` و `userbot`:

```yaml
environment:
  HTTP_PROXY: http://host.docker.internal:8080
  HTTPS_PROXY: http://host.docker.internal:8080
  NO_PROXY: localhost,127.0.0.1,db,redis,llama,api,worker,beat,userbot
extra_hosts:
  - "host.docker.internal:host-gateway"
```

> پورت `8080` را با پورت پروکسی خود (مثلاً Clash `7890`، V2Ray `10809`) جایگزین کنید.

**گزینه‌ی B — اجرای پروژه روی VPS خارج از ایران** (ساده‌ترین و پایدارترین).

**گزینه‌ی C — پروکسی SOCKS5 در کد** (برای Telethon، در `app/userbot/runner.py`).

> ⚠️ **توجه:** `network_mode: host` را استفاده نکنید — به دلیل قطع دسترسی به `db` و `redis` در شبکه‌ی داخلی Docker.

---

## 🖥️ اجرای مدل LLM (llama.cpp) روی GPU و CPU

مدل پیش‌فرض در `models/model.gguf` قرار می‌گیرد. سرویس `llama` در `docker-compose.yml` به صورت پیش‌فرض **روی CPU** اجرا می‌شود.

### 📌 حالت پیش‌فرض — CPU

```yaml
llama:
  image: ghcr.io/ggml-org/llama.cpp:server
  command: >
    -m /models/model.gguf
    --host 0.0.0.0 --port 8080
    -c 2048 --threads 4 --parallel 2
```

برای تنظیم تعداد Threads بر اساس CPU واقعی:

```bash
# تعداد هسته‌ها
nproc

# در docker-compose.yml، مقدار --threads را با تعداد هسته ست کنید
```

### ⚡ حالت GPU — NVIDIA

**پیش‌نیاز:**

1. کارت گرافیک NVIDIA (GTX 1660 یا بالاتر توصیه‌شده)
2. درایور NVIDIA نصب باشد (`nvidia-smi` جواب بدهد)
3. **NVIDIA Container Toolkit** نصب باشد:

```bash
# Ubuntu
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

**تغییر `docker-compose.yml` سرویس `llama`:**

```yaml
llama:
  image: ghcr.io/ggml-org/llama.cpp:server-cuda   # ← نسخه‌ی CUDA
  restart: unless-stopped
  command: >
    -m /models/model.gguf
    --host 0.0.0.0 --port 8080
    -c 2048 --threads 4 --parallel 2
    --n-gpu-layers 99                             # ← همه‌ی لایه‌ها روی GPU
  volumes:
    - ./models:/models:ro
  networks: [app_net]
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

**تست موفقیت:**

```bash
# بعد از اجرا
docker compose up -d llama
docker compose logs llama | grep -i "gpu\\|cuda"

# باید ببینید:
# llama_model_load_internal: using CUDA for GPU acceleration
# llama_model_load_internal: offloading 28 repeating layers to GPU
```

**تنظیم `--n-gpu-layers` بر اساس VRAM:**

| VRAM کارت | مدل Qwen 1.5B | `--n-gpu-layers` |
|---|---|---|
| ۴ GB | Q4_K_M | 99 (کامل) |
| ۲ GB | Q4_K_M | 20 |
| ۸ GB+ | Qwen 7B Q4 | 99 (کامل) |

> اگر خطای `out of memory` گرفتید، عدد را کم کنید (مثلاً ۲۰ یا ۱۵).

### 🍎 حالت GPU — Apple Silicon (M1/M2/M3)

Docker Desktop روی Mac از Metal پشتیبانی می‌کند اما با محدودیت. دو راه دارید:

**راه ۱ (توصیه‌شده) — اجرای llama.cpp خارج از Docker روی Mac:**

```bash
# نصب llama.cpp با Metal
brew install llama.cpp

# اجرا روی پورت 8080
llama-server -m ./models/model.gguf --host 0.0.0.0 --port 8080 -ngl 99
```

سپس در `docker-compose.yml`، سرویس `llama` را **حذف یا غیرفعال** کنید و در `.env`:

```env
LLAMA_SERVER_URL=http://host.docker.internal:8080
```

و در `docker-compose.yml` برای سرویس‌های `api` و `worker` و `userbot`:

```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

**راه ۲ — Docker Desktop با GPU Passthrough:** در تنظیمات Docker Desktop → Resources → Enable GPU. اما Metal در Docker Desktop محدود است و معمولاً ۲-۳ برابر کندتر از اجرای بومی.

### 🎛️ تنظیمات `llama` در `.env`

```env
LLAMA_SERVER_URL=http://llama:8080    # آدرس داخلی Docker
LLM_ENABLED=true                       # فعال/غیرفعال کردن LLM
LLM_TIMEOUT=60                          # ثانیه
```

### 📊 پیشنهاد مدل‌ها بر اساس سخت‌افزار

| سخت‌افزار | مدل پیشنهادی | حجم | کیفیت فارسی |
|---|---|---|---|
| CPU فقط (۴ هسته) | Qwen2.5-0.5B-Instruct-Q4 | ~۳۵۰ MB | متوسط |
| CPU فقط (۸ هسته) | Qwen2.5-1.5B-Instruct-Q4 | ~۱ GB | خوب |
| GPU 4GB+ | Qwen2.5-1.5B-Instruct-Q4 | ~۱ GB | عالی |
| GPU 8GB+ | Qwen2.5-7B-Instruct-Q4 | ~۴.۵ GB | بسیار عالی |
| GPU 16GB+ | Qwen2.5-14B-Instruct-Q4 | ~۹ GB | حرفه‌ای |

> **توصیه:** برای فارسی، **Qwen2.5** به‌طور مشخص از Gemma و Llama بهتر عمل می‌کند.

---

## 🤖 فعال‌سازی ربات تلگرام و Session

پروژه از **دو نوع اتصال** به تلگرام استفاده می‌کند که هر کدام تنظیمات جداگانه دارند:

### ۱) ربات (Bot API) — `BOT_TOKEN`

**گام ۱ — ساخت ربات:**

1. در تلگرام به [@BotFather](https://t.me/BotFather) پیام دهید
2. `/newbot` را بزنید
3. یک نام (مثلاً `Mirror Pro`) و یک username (مثلاً `mirror_pro_bot`) انتخاب کنید
4. توکن دریافت می‌کنید — چیزی شبیه `1234567890:AAH-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
5. توکن را در `.env` قرار دهید:

```env
BOT_TOKEN=1234567890:AAH-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**گام ۲ — ادمین کردن ربات در کانال‌های مقصد:**

> ⚠️ **بسیار مهم:** ربات **باید** در تمام کانال‌های **مقصد** ادمین باشد (با دسترسی «ارسال پیام»). بدون این، ارسال با خطای `Forbidden: bot is not a member` شکست می‌خورد.

روش ادمین کردن:

1. کانال مقصد → Settings → Administrators → Add Administrator
2. جست‌وجوی username ربات (`@mirror_pro_bot`)
3. دسترسی «Post messages» را فعال کنید

> **نکته:** ربات **نیازی نیست** در کانال‌های **مبدأ** ادمین باشد — userbot این کار را انجام می‌دهد.

### ۲) Userbot (MTProto) — `TG_API_ID` و `TG_SESSION`

**گام ۱ — دریافت `api_id` و `api_hash`:**

1. به [my.telegram.org](https://my.telegram.org) بروید
2. شماره موبایل خود را وارد کنید (همان شماره‌ای که می‌خواهید userbot با آن کار کند)
3. کد تایید تلگرام را وارد کنید
4. **API development tools** را باز کنید
5. یک اپلیکیشن جدید بسازید (نام و platform دلخواه — مثلاً `Mirror Pro`, `Desktop`)
6. `api_id` (عدد) و `api_hash` (رشته) دریافت می‌کنید

در `.env`:

```env
TG_API_ID=1234567
TG_API_HASH=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
TG_PHONE=+989123456789
TG_SESSION_NAME=userbot
```

**گام ۲ — لاگین یک‌باره (تعاملی):**

```bash
docker compose run --rm -it userbot python -m app.userbot.login
```

خروجی نمونه:

```
→ در حال اتصال به تلگرام...
Please enter the code you received: 12345
Please enter your password: ****    ← فقط اگر 2FA فعال است
✅ لاگین موفق!
   نام: Your Name
   یوزرنیم: @yourusername
   id: 123456789
   session: /app/sessions/userbot.session
```

**گام ۳ — ری‌استارت سرویس userbot:**

```bash
docker compose restart userbot
docker compose logs -f userbot
```

باید ببینید:

```
INFO userbot Userbot logged in as @yourusername (id=...)
INFO userbot Resolved @farsna → خبرگزاری فارس (id=...)
INFO userbot Poller started (interval=15s, batch=100, max_catchup=500)
```

### 📁 محل فایل Session

فایل session در پوشه‌ی `./sessions/` روی host ذخیره می‌شود:

```
sessions/
└── userbot.session       ← فایل SQLite — حاوی کلیدهای ورود
```

> ⚠️ **امنیت:** این فایل مثل رمز عبور است. **هرگز** آن را در git commit نکنید، با کسی به اشتراک نگذارید، و در `.gitignore` قرار دهید:

```gitignore
sessions/
backups/
media/
models/
.env
```

### 🔄 اگر session منقضی شد

اگر پیام `session معتبر نیست` دیدید:

```bash
# پاک کردن session قدیمی
docker compose down
sudo rm -rf sessions/*

# لاگین مجدد
docker compose up -d
docker compose run --rm -it userbot python -m app.userbot.login
docker compose restart userbot
```

### 🛡️ نکات امنیتی مهم

| مورد | توصیه |
|---|---|
| `BOT_TOKEN` | فقط در `.env`، هرگز در کد یا chat |
| `TG_SESSION` | فقط روی سرور، با مجوز `600` |
| `SECRET_KEY` | تصادفی و طولانی (حداقل ۳۲ کاراکتر) |
| `ADMIN_PASSWORD` | حتماً تغییر دهید از `admin123` |
| دسترسی SSH | کلید عمومی، نه رمز؛ فایروال فعال |
| HTTPS | در production، پشت Nginx + Let's Encrypt |
| پنل | روی `127.0.0.1:8000` (فقط SSH tunnel) یا پشت auth |

### 🧪 تست نهایی setup

```bash
# ۱. تست توکن ربات
docker compose exec bot python -c "
import asyncio
from aiogram import Bot
from app.config import settings
async def t():
    b = Bot(settings.BOT_TOKEN)
    me = await b.me()
    print(f'✅ Bot: @{me.username}')
    await b.session.close()
asyncio.run(t())
"

# ۲. تست session userbot
docker compose exec userbot python -c "
import asyncio
from telethon import TelegramClient
from app.config import settings
async def t():
    c = TelegramClient('/app/sessions/' + settings.TG_SESSION_NAME, settings.TG_API_ID, settings.TG_API_HASH)
    await c.connect()
    if await c.is_user_authorized():
        me = await c.get_me()
        print(f'✅ Userbot: @{me.username} (id={me.id})')
    else:
        print('❌ Not authorized — run: docker compose run --rm -it userbot python -m app.userbot.login')
    await c.disconnect()
asyncio.run(t())
"

# ۳. تست LLM
docker compose exec api python -c "
import httpx, asyncio
async def t():
    r = await httpx.AsyncClient().get('http://llama:8080/health', timeout=5)
    print(f'✅ LLM status: {r.status_code}')
asyncio.run(t())
"
```

---

## 📊 تغییرات آتی (Roadmap)

### 🔴 اولویت بالا (نسخه‌ی ۱۱)

- [ ] **ویرایشگر Markdown برای انتشار دستی** — پشتیبانی از bold, italic, link, code و پیش‌نمایش زنده
- [ ] **پشتیبانی کامل از آلبوم (Media Group)** — ارسال چند عکس/ویدئوی همزمان با caption مشترک
- [ ] **Webhook به‌جای Polling** — برای کاهش تأخیر و بار سرور
- [ ] **Retry دستی + Bulk** — انتخاب چند پیام و تلاش مجدد گروهی
- [ ] **آپلود مستقیم مدیا از پنل** — بدون نیاز به کانال مبدأ
- [ ] **پشتیبانی از Reaction و Poll** — انتقال نظرسنجی و ری‌اکشن‌ها
- [ ] **مدیریت چند اکانت userbot** — برای توزیع بار روی چند اکانت (جلوگیری از rate limit)

### 🟡 اولویت متوسط (نسخه‌ی ۱۲)

- [ ] **آمار پیشرفته** — نمودار زمانی، مقایسه‌ی کانال‌ها، export به Excel با نمودار
- [ ] **ویرایشگر قوانین Regex** — با تست زنده در پنل
- [ ] **پروفایلینگ عملکرد LLM** — نمایش latency و تعداد tokens مصرفی
- [ ] **مدیریت نسخه‌ی مدل LLM از پنل** — آپلود مدل جدید بدون rebuild
- [ ] **جست‌وجوی پیشرفته در پیام‌ها** — بر اساس کلمه، تاریخ، کانال، وضعیت
- [ ] **تبدیل voice به متن** — با Whisper برای پیام‌های صوتی
- [ ] **جلوگیری از تکرار بر اساس محتوا** — نه فقط ID (کپی‌های دستی)

### 🟢 اولویت پایین (آینده)

- [ ] **PWA** — نصب پنل روی موبایل به‌عنوان اپ
- [ ] **WebSocket برای بروزرسانی زنده** — بدون refresh
- [ ] **پشتیبانی از کانال‌های خصوصی** با Invite Link
- [ ] **مدیریت چند-سازمانی (multi-tenant)** — چند تیم مستقل روی یک نصب
- [ ] **پلاگین‌های خارجی** — webhook برای اتصال به سیستم‌های دیگر
- [ ] **متریک‌های Prometheus + Grafana** — برای مانیتورینگ پیشرفته
- [ ] **مدل LLM چندزبانه‌ی اختصاصی** — fine-tune روی محتوای فارسی
- [ ] **تشخیص تصویر (Vision LLM)** — تحلیل محتوای تصاویر

### 🐛 بدهی فنی شناخته‌شده

- [ ] **تست‌های خودکار** — در حال حاضر تست‌های integration وجود ندارد
- [ ] **مستندات OpenAPI** — endpointها بدون description کامل
- [ ] **CI/CD** — pipeline build و test خودکار وجود ندارد
- [ ] **Type hints کامل** — برخی توابع بدون annotation
- [ ] **مدیریت خطای LLM** — در حال حاضر خطای LLM ارسال را متوقف نمی‌کند، اما بهتر است fallback صریح داشته باشد
- [ ] **Migration rollback** — downgrade‌ها تست نشده‌اند

### 🧩 ایده‌های بلندمدت

- **پنل تحلیلی هوشمند** با LLM: پیشنهاد زمان انتشار بر اساس تعاملات گذشته
- **تولید خودکار محتوا**: خلاصه‌سازی چند پیام در یک پست
- **ترجمه‌ی خودکار** بین فارسی/عربی/انگلیسی برای انتشار چندزبانه
- **تشخیص خودکار موضوع** و تخصیص به کانال مناسب
- **A/B Testing** — ارسال نسخه‌های مختلف و اندازه‌گیری تعامل

---

## 🧰 دستورات مفید

```bash
# مشاهده‌ی لاگ‌ها
docker compose logs -f api
docker compose logs -f worker
docker compose logs -f userbot

# وضعیت سرویس‌ها
docker compose ps

# ری‌استارت یک سرویس
docker compose restart api

# اجرای migration
docker compose exec api alembic upgrade head

# دسترسی به psql
docker compose exec db psql -U postgres -d forwarder

# دسترسی به redis-cli
docker compose exec redis redis-cli

# بکاپ دستی
docker compose exec api python -c "from app.workers.tasks import run_backup; print(run_backup())"

# بازیابی (روی host)
bash scripts/restore.sh ./backups/backup_YYYYMMDD_HHMMSS.sql.gz

# بیلد سریع (با cache)
docker compose build api worker userbot

# بیلد کامل (بدون cache)
docker compose build --no-cache api
```

### 🔍 تست سلامت

```bash
# پنل
curl -sS http://localhost:8000/healthz

# LLM
curl -sS http://localhost:8080/health

# Redis
docker compose exec redis redis-cli ping

# Postgres
docker compose exec db pg_isready -U postgres
```

---

## 📞 پشتیبانی و مشارکت

- **مسائل گزارش‌شده:** از بخش Issues استفاده کنید
- **پیشنهاد قابلیت:** با برچسب `feature-request`
- **پول ریکوئست:** قبل از شروع، در Issues هماهنگ کنید

---

## 📜 مجوز

این پروژه تحت مجوز MIT منتشر شده است. استفاده‌ی تجاری آزاد است.

---

**آخرین به‌روزرسانی:** ۱۴۰۴/۰۸/۲۲ — v10
