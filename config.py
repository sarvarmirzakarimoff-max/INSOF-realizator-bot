"""INSOF realizator boti — barcha sozlamalar shu faylda.

Narx yoki tarif o'zgarsa, faqat shu faylni tahrirlang va botni qayta ishga tushiring.
"""
import os
from pathlib import Path

BASE = Path(__file__).parent


def _env_fayl():
    """.env faylidan TOKEN va GROUP_ID ni o'qiydi (kodga yozib qo'ymaslik uchun)."""
    f = BASE / ".env"
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


_env_fayl()

# ------------------------------------------------------------------ TELEGRAM
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
# Realizatorlar guruhi ID si (manfiy son, masalan -1001234567890).
# Botni guruhga qo'shib, guruhda /chatid deb yozsangiz bot ID ni aytadi.
GROUP_ID = int(os.environ.get("GROUP_ID", "0") or 0)
# Botdan foydalana oladigan odamlar (Telegram user ID). Bo'sh = hamma.
ALLOWED_USERS: set[int] = set()

# ------------------------------------------------------------------ FIRMA
FIRMA = {
    "nomi": "«INSOF» МЧЖ",
    "manzil": "Тошкент вилояти, Янгийўл тумани,<br/>Эски Қовунчи ҚФЙ, Қирсадоқ маҳалласи",
    "tel": "+998 93 578 06 09",
    "stir": "200588569",
    "ifut": "23610",
    "hr": "20208000700529076001",
    "bank": "АТ «Алоқабанк» Бош офиси, Тошкент ш.",
    "mfo": "00401",
    "savol_tel": "+998 93 578-06-09",
}

# Zavod joylashuvi — masofa shu nuqtadan o'lchanadi.
# ⚠️ TAXMINIY: Telegramda zavod lokatsiyasini yuboring, aniq koordinatani qo'yamiz.
ZAVOD_LAT = 41.1170
ZAVOD_LON = 69.0440

QQS = 0.12

# ------------------------------------------------------------------ BETON
# Narxlar ҚҚСsiz (prays-list 17.11.2026). ҚҚС 12% ustiga qo'shiladi.
BETON_NARX = {
    "М 100": 480_000,
    "М 150": 500_000,
    "М 200": 520_000,
    "М 250": 550_000,
    "М 300": 580_000,
    "М 350": 600_000,
    "М 400": 620_000,
    "М 450": 640_000,
}
MIKSER = {
    "hajm_m3": 10,             # 1 miksyer 10 kub oladi; to'liq miksyerga yo'l kira yo'q
    "chala_yaqin_km": 10,      # 10 km gacha — yaqin
    "chala_min": 600_000,      # chala miksyer, 10 km gacha, 1 xodka (ҚҚСсиз)
    # ⚠️ TAXMINIY — 10 km dan keyingi har km uchun qo'shimcha (aniqlash kerak)
    "chala_km_narxi": 30_000,
}

# ------------------------------------------------------------------ PLITA
# Плиталар (ПК), 1 dona narxi ҚҚСsiz (prays-list «54 yangi narx»).
# ҚҚС 12% ustiga qo'shiladi. Nomi: ПК uzunlik(dm)-eni(dm)-yuklama
PLITA_NARX = {
    "ПК 71-12-8": 1_950_000,
    "ПК 71-10-8": 1_900_000,
    "ПК 70-12-8": 1_950_000,
    "ПК 70-10-8": 1_900_000,
    "ПК 69-12-8": 1_950_000,
    "ПК 69-10-8": 1_900_000,
    "ПК 68-12-8": 1_900_000,
    "ПК 68-10-8": 1_850_000,
    "ПК 67-12-8": 1_900_000,
    "ПК 66-12-8": 1_900_000,
    "ПК 65-12-8": 1_800_000,
    "ПК 65-10-8": 1_750_000,
    "ПК 64-12-8": 1_800_000,
    "ПК 63-12-8": 1_500_000,
    "ПК 63-10-8": 1_450_000,
    "ПК 62-12-8": 1_400_000,
    "ПК 62-10-8": 1_350_000,
    "ПК 61-12-8": 1_400_000,
    "ПК 60-12-8": 1_400_000,
    "ПК 59-12-8": 1_250_000,
    "ПК 59-10-8": 1_200_000,
    "ПК 58-12-8": 1_250_000,
    "ПК 57-12-8": 1_250_000,
    "ПК 57-10-8": 1_200_000,
    "ПК 56-12-8": 1_250_000,
    "ПК 55-12-8": 1_250_000,
    "ПК 55-10-8": 1_200_000,
    "ПК 54-12-8": 1_150_000,
    "ПК 54-10-8": 1_130_000,
    "ПК 53-12-8": 1_150_000,
    "ПК 52-12-8": 1_150_000,
    "ПК 52-10-8": 1_130_000,
    "ПК 51-12-8": 1_100_000,
    "ПК 51-10-8": 1_050_000,
    "ПК 50-12-8": 1_100_000,
    "ПК 50-10-8": 1_050_000,
    "ПК 49-12-8": 1_050_000,
    "ПК 49-10-8": 1_000_000,
    "ПК 48-12-8": 1_050_000,
    "ПК 47-12-8": 1_050_000,
    "ПК 47-10-8": 1_000_000,
    "ПК 46-12-8": 1_050_000,
    "ПК 45-12-8": 1_050_000,
    "ПК 45-10-8": 1_000_000,
    "ПК 44-12-8": 1_050_000,
    "ПК 43-12-8": 1_050_000,
    "ПК 43-10-8": 1_000_000,
    "ПК 42-12-8": 1_050_000,
    "ПК 41-12-8": 1_000_000,
    "ПК 41-10-8": 950_000,
    "ПК 40-12-8": 1_000_000,
    "ПК 40-10-8": 950_000,
    "ПК 39-12-8": 950_000,
    "ПК 39-10-8": 900_000,
    "ПК 38-12-8": 950_000,
    "ПК 37-12-8": 950_000,
    "ПК 35-12-8": 950_000,
    "ПК 35-10-8": 900_000,
    "ПК 34-12-8": 950_000,
    "ПК 33-12-8": 900_000,
    "ПК 33-10-8": 850_000,
    "ПК 32-12-8": 900_000,
    "ПК 31-12-8": 850_000,
    "ПК 31-10-8": 800_000,
    "ПК 30-12-8": 850_000,
    "ПК 29-12-8": 850_000,
    "ПК 29-10-8": 800_000,
    "ПК 28-12-8": 850_000,
    "ПК 27-12-8": 850_000,
    "ПК 26-12-8": 850_000,
    "ПК 25-12-8": 850_000,
    "ПК 24-12-8": 850_000,
    "ПК 23-12-8": 850_000,
    "ПК 22-12-8": 850_000,
    "ПК 21-12-8": 850_000,
}

def plita_olcham(nomi: str) -> str:
    """'ПК 71-12-8' -> '7,1 × 1,2 м'"""
    import re as _re
    m = _re.search(r"(\d+)-(\d+)-", nomi)
    if not m:
        return ""
    return (f"{int(m[1]) / 10:.1f} × {int(m[2]) / 10:.1f} м").replace(".", ",")


AVTOKRAN = {
    "soat_narxi": 700_000,     # 1 soat (ҚҚС bilan)
    "soatiga_plita": 10,       # 1 soatda 10 ta plita
    "min_soat": 3,             # kamida 3 soat
}
# Plitani tashish (1 xodka narxi, ҚҚСsiz). Masofa zavoddan, km.
PLITA_TASHISH = {
    # (km gacha, 1 xodka narxi)
    "narxlar": [(10, 1_000_000), (20, 1_300_000), (25, 1_500_000), (35, 1_700_000), (50, 2_000_000),
                (75, 2_400_000), (100, 2_800_000), (130, 3_200_000)],
    # Shalanda: plita uzunligi (dm) oralig'i -> 1 xodkada necha dona
    "shalanda": [(63, 71, 10), (50, 62, 12), (39, 49, 14), (32, 38, 16), (21, 31, 24)],
    # Xovo: faqat 21..63 uzunlik; 1 xodkada jami 12 ta, shundan eni 1,2 li ko'pi bilan 8 ta
    "xovo_min": 21, "xovo_max": 63, "xovo_jami": 12, "xovo_12_max": 8,
}
NARX_QQS_ICHIDA = {"plita": False, "beton": False}  # ikkalasi ҚҚСsiz kiritiladi

# To'lov shakli: ҚҚС 12% qo'shiladimi?
# Naqd — ҚҚСsiz, perechisleniye — ҚҚС qo'shiladi.
TOLOV_SHAKLI = {
    "naqd": {"nomi": "Нақд пул", "qqs": False},
    "otkazma": {"nomi": "Пул ўтказиш (перечисление)", "qqs": True},
}

# ------------------------------------------------------------------ OBYEKT
# Guruhdagi kartochkadagi ro'yxat (realizatorlar shunday yozadi)
EHTIYOJLAR = ["Beton", "Plita", "Shpaklofka, Rodmond", "Qum, Sheben, Klines",
              "Kolsa", "Lotok", "Bardyor", "Akfa", "Stolba"]

DB_PATH = BASE / "insof.db"
TAKLIF_PAPKA = BASE / "takliflar"

# ------------------------------------------------------------------ RASMIY TAKLIF (Word shablon)
# "Boshqa mahsulotlar" — rasmiy tijorat taklifi (INSOF_Tijorat_taklifi.docx asosida).
# Narxlar ҚҚСsiz. Kategoriya: [(nomi, o'lchov birligi, narx), ...]
BOSHQA_MAHSULOTLAR = {
    "ТЕМИР-БЕТОН БУЮМЛАРИ": [
        ("Опора СВ 110-3,5", "дона", 1_250_000),
        ("Опора СВ 95-2,0", "дона", 1_150_000),
        ("Зинапоя марши 2ЛМ 57-12-17", "дона", 4_500_000),
        ("ФБС 24-4-6", "дона", 320_000),
        ("ФБС 12-4-6", "дона", 180_000),
        ("ФБС 9-4-6", "дона", 160_000),
        ("Ҳалқа (кольцо) КС 1,5", "дона", 750_000),
        ("Ҳалқа (кольцо) КС 1,0", "дона", 550_000),
        ("Қопқоқ (крышка) 1,5", "дона", 500_000),
        ("Қопқоқ (крышка) 1,0", "дона", 400_000),
        ("Лоток Л-5", "дона", 850_000),
        ("Бордюр 30×18×30", "дона", 260_000),
        ("Газоблок", "м³", 500_000),
    ],
    "ҚУРУҚ ҚУРИЛИШ ҚОРИШМАЛАРИ": [
        ("Шпаклёвка", "кг", 1_300),
        ("Ротбанд (гипс штукатурка)", "кг", 1_300),
        ("Кафель елими (плиточный клей)", "кг", 1_300),
        ("Наливной пол", "кг", 1_300),
    ],
    "ИНЕРТ МАТЕРИАЛЛАР": [
        ("Клинец", "м³", 2_600_000),
        ("Шағал (щебень)", "м³", 1_400_000),
        ("Финский (отсев)", "м³", 2_400_000),
        ("Қум (песок)", "м³", 2_600_000),
    ],
}
RASMIY = {
    "amal_kun": 10,            # taklif necha kun amal qiladi
    "direktor": "",            # direktor F.I.Sh. (bo'sh bo'lsa chiziq qoladi)
    "boglanish_tel": "+998 93 578 06 09 (Сарвар),  +998 97 883 60 00 (Азиз)",
    "email": "insofbetonzavod@gmail.com",
}

# ------------------------------------------------------------------ HUDUDLAR (obyekt manzili)
HUDUDLAR = {
    "Toshkent shahri": ["Bektemir", "Chilonzor", "Mirobod", "Mirzo Ulug'bek", "Olmazor", "Sergeli",
                        "Shayxontohur", "Uchtepa", "Yakkasaroy", "Yangihayot", "Yashnobod", "Yunusobod"],
    "Toshkent viloyati": ["Yangiyo'l tumani", "Yangiyo'l sh.", "Zangiota", "Toshkent tumani", "Qibray",
                          "O'rta Chirchiq", "Yuqori Chirchiq", "Quyi Chirchiq", "Chinoz", "Bo'ka",
                          "Bekobod tumani", "Bekobod sh.", "Bo'stonliq", "Parkent", "Piskent",
                          "Oqqo'rg'on", "Ohangaron tumani", "Ohangaron sh.", "Angren", "Olmaliq",
                          "Chirchiq", "Nurafshon"],
    "Sirdaryo viloyati": ["Guliston sh.", "Guliston tumani", "Boyovut", "Mirzaobod", "Oqoltin", "Sardoba",
                          "Sayxunobod", "Sirdaryo tumani", "Xovos", "Yangiyer", "Shirin"],
}
