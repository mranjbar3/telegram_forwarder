"""ترجمه سه‌زبانه: fa / en / ar"""

LANGS = ("fa", "en", "ar")
DEFAULT_LANG = "fa"

_TR = {
    # menu
    "dashboard":        ("داشبورد", "Dashboard", "لوحة التحكم"),
    "channels":         ("مدیریت کانال‌ها", "Channels", "القنوات"),
    "publish":          ("انتشار پست", "Publish", "نشر"),
    "records":          ("سوابق ارسال", "History", "السجل"),
    "reports":          ("گزارش‌ها", "Reports", "التقارير"),
    "cleaning":         ("پاکسازی و فیلتر", "Cleaning & Filters", "التنظيف والفلاتر"),
    "notifications":    ("اعلان‌ها", "Notifications", "الإشعارات"),
    "users":            ("کاربران", "Users", "المستخدمون"),
    "logs":             ("لاگ فعالیت", "Activity Log", "سجل النشاط"),
    "health":           ("سلامت سیستم", "Health", "الحالة"),
    "settings":         ("تنظیمات", "Settings", "الإعدادات"),
    # common
    "save":             ("ذخیره", "Save", "حفظ"),
    "delete":           ("حذف", "Delete", "حذف"),
    "add":              ("افزودن", "Add", "إضافة"),
    "cancel":           ("لغو", "Cancel", "إلغاء"),
    "search":           ("جست‌وجو", "Search", "بحث"),
    "country":          ("کشور", "Country", "الدولة"),
    "category":         ("دسته", "Category", "الفئة"),
    "status":           ("وضعیت", "Status", "الحالة"),
    "actions":          ("عملیات", "Actions", "الإجراءات"),
    "all":              ("همه", "All", "الكل"),
    "export_csv":       ("خروجی CSV", "Export CSV", "تصدير CSV"),
    # channels
    "chat_id":          ("شناسه کانال", "Channel ID", "معرف القناة"),
    "display_name":     ("نام نمایشی", "Display Name", "الاسم المعروض"),
    "add_source":       ("افزودن کانال مبدأ", "Add source channel", "إضافة قناة مصدر"),
    "add_destination":  ("افزودن مقصد", "Add destination", "إضافة وجهة"),
    "destinations":     ("مقصدها", "Destinations", "الوجهات"),
    "import_excel":     ("ایمپورت Excel", "Import Excel", "استيراد Excel"),
    "active":           ("فعال", "Active", "نشط"),
    "inactive":         ("غیرفعال", "Inactive", "غير نشط"),
    # publish
    "publish_now":      ("فوری", "Now", "الآن"),
    "publish_schedule": ("زمان‌بندی", "Schedule", "جدولة"),
    "message_text":     ("متن پیام", "Message text", "نص الرسالة"),
    "apply_filters":    ("اعمال فیلترها و LLM", "Apply filters & LLM", "تطبيق الفلاتر"),
    "select_all":       ("انتخاب همه", "Select all", "تحديد الكل"),
    "selected_count":   ("انتخاب‌شده", "selected", "مختار"),
    "submit":           ("ثبت", "Submit", "إرسال"),
    # dashboard
    "channels_by_country": ("تفکیک کانال‌ها بر اساس کشور", "Channels by country", "القنوات حسب الدولة"),
    "top_channels":     ("پرتولیدترین کانال‌ها", "Top producing channels", "أكثر القنوات إنتاجاً"),
    "active_links":     ("کانال‌های فعال", "Active channels", "القنوات النشطة"),
    "inactive_links":   ("کانال‌های غیرفعال", "Inactive channels", "القنوات غير النشطة"),
    "total_sent":       ("کل ارسال‌شده", "Total sent", "إجمالي المرسل"),
    "sent_today":       ("ارسال امروز", "Sent today", "المرسل اليوم"),
    "total_channels":   ("کل کانال‌ها", "Total channels", "إجمالي القنوات"),
    # cleaning
    "blocking_rules":   ("قوانین مسدودسازی", "Blocking rules", "قواعد الحجب"),
    "llm_prompts":      ("پرامپت‌های LLM", "LLM prompts", "أوامر LLM"),
    "classify_prompt":  ("تشخیص اسپم", "Spam detection", "كشف السبام"),
    "clean_prompt":     ("پاکسازی متن", "Text cleaning", "تنظيف النص"),
    # login
    "login":            ("ورود", "Login", "تسجيل الدخول"),
    "username":         ("نام کاربری", "Username", "اسم المستخدم"),
    "password":         ("رمز عبور", "Password", "كلمة المرور"),
}


def t(key: str, lang: str = DEFAULT_LANG) -> str:
    row = _TR.get(key)
    if not row:
        return key
    idx = {"fa": 0, "en": 1, "ar": 2}.get(lang, 0)
    return row[idx]


def get_lang(request) -> str:
    """زبان جاری — از session، پیش‌فرض fa."""
    try:
        return request.session.get("lang", DEFAULT_LANG)
    except Exception:
        return DEFAULT_LANG


def is_rtl(lang: str) -> bool:
    return lang in ("fa", "ar")
