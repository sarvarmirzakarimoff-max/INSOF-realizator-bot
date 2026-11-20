# INSOF realizator boti

Realizatorlar uchun Telegram bot. U 4 ta ishni bajaradi:

| Tugma | Nima qiladi |
|---|---|
| 💼 Tijorat taklifi | Beton yoki plita uchun PDF taklif yasaydi: narx, ҚҚС, yo'l kirasi, avtokran, avans va qoldiq. PDF guruhga ham tushadi |
| 🏗 Yangi obyekt | Rasm, uy egasi, telefon, ehtiyojlar (✅/❓) va lokatsiyani bitta kartochka qilib guruhga tashlaydi |
| 💰 To'lov | Buyurtmaga to'lov yozadi (so'm yoki $), chekni guruhga tashlaydi, qolgan qarzni ko'rsatadi |
| 📋 Qarzdorlar | Kim qancha qarzligini ko'rsatadi. Har kuni soat 9:00 da guruhga avtomatik tashlaydi |

## 1. Bot yaratilgan ✅

Bot: **@insof_realizator_bot** (INSOF Realizator). U **INSOF JBI | 2026** guruhiga qo'shilgan.
Token **@BotFather** chatida, "Done! Congratulations..." xabarida turibdi (`9279...:AA...` ko'rinishida). Uni hech kimga bermang.

## 2. Kompyuterga o'rnatish (Windows)

1. **Python** o'rnating: https://www.python.org/downloads/. O'rnatishda **"Add python.exe to PATH"** belgisini qo'ying.
2. Shu papkani istalgan joyga qo'ying (masalan: `C:\insof_bot`).
3. `.env.example` faylidan nusxa olib, nomini **`.env`** qiling. BotFather'dagi tokenni nusxalab, ichiga yozing:
   ```
   BOT_TOKEN=123456789:AA...
   GROUP_ID=0
   ```
4. **`ishga_tushirish.bat`** ni ikki marta bosing. Birinchi marta kerakli kutubxonalar o'rnatiladi (1–2 daqiqa), keyin "Bot ishga tushdi" degan yozuv chiqadi.

## 3. Guruhga ulash

1. Bot guruhga qo'shilgan.
2. Bot ishlab turgan paytda guruhda `/chatid` deb yozing. Bot `-100...` ko'rinishidagi sonni yuboradi.
3. O'sha sonni `.env` faylidagi `GROUP_ID=` ga yozing va botni qayta ishga tushiring (oynani yopib, `.bat` ni qayta bosing).

Realizatorlar botga **shaxsiy chatda** `/start` deb yozib ishlaydi, natija esa guruhga tushadi.

## 4. Narx va tariflarni o'zgartirish

Hamma narsa **`config.py`** faylida. Uni Notepad yoki VS Code bilan ochib tahrirlang, keyin botni qayta ishga tushiring.

- `BETON_NARX` — beton markalari narxi (ҚҚСsiz).
- `PLITA_NARX` — 50 ta ковакли плита (ПК) narxi (ҚҚСsiz, 1 dona).
- `MIKSER` — miksyer 10 m³. To'liq miksyerga yo'l kira olinmaydi, chala miksyerga 10 km gacha 600 000 so'm (ҚҚСsiz) qo'shiladi.
- `AVTOKRAN` — 700 000 so'm/soat, soatiga 10 ta plita, kamida 3 soat.
- `TOLOV_SHAKLI` — naqd yoki perechisleniye bo'lganda ҚҚС qo'shiladimi (hozir ikkalasida ham qo'shiladi).
- `ZAVOD_LAT / ZAVOD_LON` — zavod koordinatasi, masofa shu nuqtadan o'lchanadi.
- `ALLOWED_USERS` — botdan faqat shu odamlar foydalansin desangiz, ularning Telegram ID sini yozing.

⚠️ **Hali aniqlanmagan (taxminiy) qiymatlar**: zavod koordinatasi, 10 km dan uzoqqa chala miksyer uchun km narxi, plitani tashish tarifi.

## 5. Ma'lumotlar qayerda

- `insof.db` — barcha obyektlar, takliflar va to'lovlar (SQLite). Uni **DB Browser for SQLite** dasturi bilan ochish mumkin.
- `takliflar\` — yaratilgan barcha PDF takliflar.

Bu ikkalasining nusxasini vaqti-vaqti bilan saqlab qo'ying.

## Muhim

- Bot faqat kompyuter yoniq va `.bat` oynasi ochiq turganda ishlaydi. 24/7 ishlashi uchun keyinroq serverga (VPS, oyiga ~3–5$) ko'chiramiz.
- Taklif → **"✅ Buyurtma bo'ldi"** bosilgandagina qarz hisobiga kiradi. Taklifdagi avans shu paytda birinchi to'lov sifatida yoziladi.
