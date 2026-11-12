"""فهرست کشورها: (کد، فارسی، انگلیسی، عربی، پرچم)"""

COUNTRIES = [
    ("ir", "ایران",       "Iran",        "إيران",      "🇮🇷"),
    ("il", "اسرائیل",     "Israel",      "إسرائيل",    "🇮🇱"),
    ("iq", "عراق",        "Iraq",        "العراق",     "🇮🇶"),
    ("ye", "یمن",         "Yemen",       "اليمن",      "🇾🇪"),
    ("sa", "عربستان",     "Saudi Arabia","السعودية",   "🇸🇦"),
    ("ru", "روسیه",       "Russia",      "روسيا",      "🇷🇺"),
    ("pk", "پاکستان",     "Pakistan",    "باكستان",    "🇵🇰"),
    ("sy", "سوریه",       "Syria",       "سوريا",      "🇸🇾"),
    ("jo", "اردن",        "Jordan",      "الأردن",     "🇯🇴"),
    ("eg", "مصر",         "Egypt",       "مصر",        "🇪🇬"),
    ("ae", "امارات",      "UAE",         "الإمارات",   "🇦🇪"),
    ("lb", "لبنان",       "Lebanon",     "لبنان",      "🇱🇧"),
    ("tr", "ترکیه",       "Türkiye",     "تركيا",      "🇹🇷"),
    ("af", "افغانستان",   "Afghanistan", "أفغانستان",  "🇦🇫"),
    ("es", "اسپانیا",     "Spain",       "إسبانيا",    "🇪🇸"),
]


def country_by_code(code: str):
    for c in COUNTRIES:
        if c[0] == code:
            return c
    return None


def country_name(code: str, lang: str = "fa") -> str:
    c = country_by_code(code)
    if not c:
        return ""
    return {"fa": c[1], "en": c[2], "ar": c[3]}.get(lang, c[1])


def country_flag(code: str) -> str:
    c = country_by_code(code)
    return c[4] if c else "🌐"
