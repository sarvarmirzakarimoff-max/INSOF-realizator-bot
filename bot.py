"""INSOF realizator boti (aiogram 3).

Ishga tushirish:  python bot.py
Bot bilan realizator shaxsiy chatda ishlaydi, natijalar (taklif, obyekt, to'lov) guruhga tushadi.
"""
import asyncio
import html
import logging
import re
from datetime import date, datetime, timedelta

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatType, ParseMode
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (BotCommand, CallbackQuery, FSInputFile, KeyboardButton, Message,
                           ReplyKeyboardMarkup)
from aiogram.utils.keyboard import InlineKeyboardBuilder

import config as C
import db
from masofa import yol_masofa_km
from praylist import PRAYSLAR
from rasmiy import mahsulotlar_royxati, make_rasmiy
from taklif import hisobla, make_offer, som

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("insof")

# ------------------------------------------------------------------ TUGMALAR
B_TAKLIF = "💼 Tijorat taklifi"
B_OBYEKT = "🏗 Yangi obyekt"
B_TOLOV = "💰 To'lov"
B_QARZ = "📋 Qarzdorlar"
B_PRAYS = "📑 Prays-list"
B_BEKOR = "❌ Bekor qilish"
B_OTKAZ = "⏭ O'tkazib yuborish"
B_LOK = "📍 Lokatsiya yuborish"
B_KM = "✍️ Km ni o'zim yozaman"
B_MASOFASIZ = "Masofasiz"
B_RASMSIZ = "Rasmsiz"
B_LOKSIZ = "Lokatsiyasiz"
B_AVANSSIZ = "Avans yo'q"
B_CHEKSIZ = "Cheksiz"


def rk(*rows, bekor=True):
    """Pastki (reply) klaviatura."""
    kb = []
    for row in rows:
        kb.append([b if isinstance(b, KeyboardButton) else KeyboardButton(text=b) for b in row])
    if bekor:
        kb.append([KeyboardButton(text=B_BEKOR)])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


MENU = rk([B_TAKLIF, B_OBYEKT], [B_PRAYS], bekor=False)
FAQAT_BEKOR = rk()
LOK_TUGMA = KeyboardButton(text=B_LOK, request_location=True)


def e(x) -> str:
    return html.escape(str(x or ""))


def son(text: str | None):
    """'20 000 000', '1,5', '12 kub' -> float. Noto'g'ri bo'lsa None."""
    if not text:
        return None
    t = text.lower().replace(" ", "").replace(" ", "").replace(",", ".")
    t = re.sub(r"(so'?m|сўм|сум|\$|m3|м3|m³|м³|kub|ta|dona|km|км)$", "", t)
    try:
        v = float(t)
    except ValueError:
        return None
    return v if v >= 0 else None


def telefon(m: Message):
    """Kontakt yoki kamida 9 raqamli telefon; bo'lmasa None."""
    if m.contact:
        return m.contact.phone_number
    t = (m.text or "").strip()
    return t if len(re.sub(r"\D", "", t)) >= 9 else None


def ruxsat(user_id: int) -> bool:
    return not C.ALLOWED_USERS or user_id in C.ALLOWED_USERS


async def guruhga(bot: Bot, method: str, **kw):
    """Guruhga yuboradi; GROUP_ID qo'yilmagan bo'lsa jim o'tadi."""
    if not C.GROUP_ID:
        return None
    try:
        return await getattr(bot, method)(chat_id=C.GROUP_ID, **kw)
    except Exception as ex:  # guruhga yubora olmasa ham realizatorning ishi to'xtamasin
        log.warning("Guruhga yuborib bo'lmadi: %s", ex)
        return None


# ------------------------------------------------------------------ HOLATLAR
class T(StatesGroup):  # tijorat taklifi
    tur = State()
    mijoz = State()
    tel = State()
    prorab = State()
    prorab_tel = State()
    obyekt = State()
    mahsulot = State()
    plita_nomi = State()
    plita_narx = State()
    miqdor = State()
    yana = State()
    joy = State()
    km = State()
    qoshimcha = State()
    nasos_narx = State()
    tolov_shakli = State()
    avans = State()
    muddat = State()
    tasdiq = State()
    rasmiy = State()


class O(StatesGroup):  # yangi obyekt
    rasm = State()
    hudud = State()
    egasi = State()
    tel = State()
    prorab = State()
    prorab_tel = State()
    manzil = State()
    ehtiyoj = State()
    joy = State()


class P(StatesGroup):  # to'lov
    buyurtma = State()
    valyuta = State()
    kurs = State()
    summa = State()
    turi = State()
    chek = State()


r = Router()
r.message.filter(F.chat.type == ChatType.PRIVATE)
r.callback_query.filter(F.message.chat.type == ChatType.PRIVATE)
g = Router()  # guruhdagi buyruqlar


# ------------------------------------------------------------------ UMUMIY
@g.message(Command("chatid"))
async def chat_id(m: Message):
    await m.reply(f"Bu chat ID: <code>{m.chat.id}</code>\n.env faylidagi GROUP_ID ga shu sonni yozing.")


@r.message(CommandStart())
async def start(m: Message, state: FSMContext):
    await state.clear()
    if not ruxsat(m.from_user.id):
        await m.answer(f"Sizga ruxsat berilmagan. ID ingiz: <code>{m.from_user.id}</code> — rahbarga yuboring.")
        return
    await m.answer(f"Assalomu alaykum, {e(m.from_user.first_name)}! INSOF realizator boti.\n"
                   "Kerakli bo'limni tanlang 👇", reply_markup=MENU)


@r.message(StateFilter("*"), F.text == B_BEKOR)
@r.message(StateFilter("*"), Command("bekor"))
async def bekor(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("Bekor qilindi.", reply_markup=MENU)


@r.message(F.text.in_({B_TAKLIF, B_OBYEKT, B_PRAYS}), lambda m: not ruxsat(m.from_user.id))
async def ruxsatsiz(m: Message):
    await m.answer(f"Sizga ruxsat berilmagan. ID ingiz: <code>{m.from_user.id}</code>")


# ================================================================== TIJORAT TAKLIFI
@r.message(StateFilter(None), F.text == B_TAKLIF)
async def t_start(m: Message, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardBuilder()
    kb.button(text="🚛 Beton", callback_data="tur:beton")
    kb.button(text="🧱 Plita", callback_data="tur:plita")
    kb.button(text="📄 Boshqa mahsulotlar (rasmiy)", callback_data="tur:rasmiy")
    kb.adjust(2, 1)
    await m.answer("Tijorat taklifi. Qaysi mahsulot?", reply_markup=FAQAT_BEKOR)
    await m.answer("Tanlang:", reply_markup=kb.as_markup())
    await state.set_state(T.tur)


@r.callback_query(T.tur, F.data.startswith("tur:"))
async def t_tur(cb: CallbackQuery, state: FSMContext):
    tur = cb.data.split(":")[1]
    await state.update_data(t={"tur": tur, "mijoz": {}, "mahsulotlar": [], "yetkazish": {}, "avans": 0})
    nom = {"beton": "Beton", "plita": "Plita", "rasmiy": "Boshqa mahsulotlar (rasmiy taklif)"}[tur]
    await cb.message.edit_text(f"Mahsulot: <b>{nom}</b>")
    if tur == "rasmiy":
        await cb.message.answer("🏢 Firma nomi? (taklifda «Ҳурматли «...» раҳбарияти!» deb yoziladi)",
                                reply_markup=FAQAT_BEKOR)
    else:
        await cb.message.answer("👤 Mijozning ismi yoki firma nomi?")
    await state.set_state(T.mijoz)
    await cb.answer()


async def _t(state):
    return (await state.get_data())["t"]


@r.message(T.mijoz, F.text)
async def t_mijoz(m: Message, state: FSMContext):
    t = await _t(state)
    if t["tur"] == "rasmiy":
        t["mijoz"]["nomi"] = m.text.strip()
        t["tanlangan"] = list(range(len(mahsulotlar_royxati())))
        await state.update_data(t=t)
        await m.answer("Taklifga kiradigan mahsulotlarni belgilang (hammasi belgilangan):", reply_markup=FAQAT_BEKOR)
        await m.answer("Mahsulotlar:", reply_markup=rasmiy_kb(t["tanlangan"]))
        await state.set_state(T.rasmiy)
        return
    t["mijoz"]["nomi"] = m.text.strip()
    await state.update_data(t=t)
    await m.answer("📞 Mijozning telefoni?", reply_markup=FAQAT_BEKOR)
    await state.set_state(T.tel)


@r.message(T.tel)
async def t_tel(m: Message, state: FSMContext):
    tel = telefon(m)
    if not tel:
        await m.answer("Telefon raqami majburiy 📞 To'liq raqamni yozing, masalan: +998 90 123 45 67")
        return
    t = await _t(state)
    t["mijoz"]["tel"] = tel
    await state.update_data(t=t)
    await m.answer("👷 Prorabning ismi?", reply_markup=rk([B_OTKAZ]))
    await state.set_state(T.prorab)


@r.message(T.prorab, F.text)
async def t_prorab(m: Message, state: FSMContext):
    t = await _t(state)
    if m.text == B_OTKAZ:
        await state.update_data(t=t)
        await m.answer("🏗 Obyekt nomi yoki manzili? (masalan: Gulbahor, Yunusobod 4-kvartal)", reply_markup=FAQAT_BEKOR)
        await state.set_state(T.obyekt)
        return
    t["mijoz"]["prorab"] = m.text.strip()
    await state.update_data(t=t)
    await m.answer("📞 Prorabning telefoni?", reply_markup=rk([B_OTKAZ]))
    await state.set_state(T.prorab_tel)


@r.message(T.prorab_tel)
async def t_prorab_tel(m: Message, state: FSMContext):
    t = await _t(state)
    if m.contact:
        t["mijoz"]["prorab_tel"] = m.contact.phone_number
    elif m.text and m.text != B_OTKAZ:
        t["mijoz"]["prorab_tel"] = m.text.strip()
    await state.update_data(t=t)
    await m.answer("🏗 Obyekt nomi yoki manzili? (masalan: Gulbahor, Yunusobod 4-kvartal)", reply_markup=FAQAT_BEKOR)
    await state.set_state(T.obyekt)


@r.message(T.obyekt, F.text)
async def t_obyekt(m: Message, state: FSMContext):
    t = await _t(state)
    t["mijoz"]["obyekt"] = m.text.strip()
    await state.update_data(t=t)
    await mahsulot_sora(m, state)


async def mahsulot_sora(m: Message, state: FSMContext):
    t = await _t(state)
    kb = InlineKeyboardBuilder()
    if t["tur"] == "beton":
        for marka in C.BETON_NARX:
            kb.button(text=marka, callback_data=f"mb:{marka}")
        kb.adjust(4)
        await m.answer("Beton markasini tanlang:", reply_markup=kb.as_markup())
    else:
        uzunliklar = sorted({int(re.search(r"ПК (\d+)-", n)[1]) for n in C.PLITA_NARX}, reverse=True)
        for L in uzunliklar:
            kb.button(text=f"{L / 10:g} м".replace(".", ","), callback_data=f"pL:{L}")
        kb.button(text="✍️ Boshqa", callback_data="mp:x")
        kb.adjust(5)
        await m.answer("Ковакли плита (ПК). Uzunligini tanlang:", reply_markup=kb.as_markup())
    await state.set_state(T.mahsulot)


@r.callback_query(T.mahsulot, F.data.startswith("mb:"))
async def t_marka(cb: CallbackQuery, state: FSMContext):
    marka = cb.data[3:]
    await state.update_data(joriy={"nomi": f"Бетон {marka}", "narx": C.BETON_NARX[marka], "birlik": "м³"})
    await cb.message.edit_text(f"Marka: <b>{marka}</b> — {som(C.BETON_NARX[marka])} so'm/m³ (ҚҚСsiz)")
    await cb.message.answer("Necha kub (m³)?")
    await state.set_state(T.miqdor)
    await cb.answer()


@r.callback_query(T.mahsulot, F.data.startswith("pL:"))
async def t_plita_uzunlik(cb: CallbackQuery, state: FSMContext):
    L = cb.data[3:]
    nomlar = list(C.PLITA_NARX)
    kb = InlineKeyboardBuilder()
    for i, n in enumerate(nomlar):
        if n.startswith(f"ПК {L}-"):
            kb.button(text=f"{n} — {som(C.PLITA_NARX[n])}", callback_data=f"mp:{i}")
    kb.button(text="⬅️ Orqaga", callback_data="mp:orqa")
    kb.adjust(1)
    await cb.message.edit_text("Enini tanlang (narx 1 dona, ҚҚСsiz):", reply_markup=kb.as_markup())
    await cb.answer()


@r.callback_query(T.mahsulot, F.data.startswith("mp:"))
async def t_plita(cb: CallbackQuery, state: FSMContext):
    k = cb.data[3:]
    await cb.answer()
    if k == "orqa":
        await cb.message.delete()
        await mahsulot_sora(cb.message, state)
    elif k == "x":
        await cb.message.edit_text("Ro'yxatda yo'q plita.")
        await cb.message.answer("Plita nomini yozing (masalan: ПК 60-12-8):")
        await state.set_state(T.plita_nomi)
    else:
        nomi = list(C.PLITA_NARX)[int(k)]
        narx = C.PLITA_NARX[nomi]
        await state.update_data(joriy={"nomi": nomi, "narx": narx, "izoh": C.plita_olcham(nomi), "birlik": "дона"})
        await cb.message.edit_text(f"Plita: <b>{e(nomi)}</b> ({C.plita_olcham(nomi)}) — {som(narx)} so'm/dona, ҚҚСsiz")
        await cb.message.answer("Necha dona?")
        await state.set_state(T.miqdor)


@r.message(T.plita_nomi, F.text)
async def t_plita_nomi(m: Message, state: FSMContext):
    nomi = m.text.strip()
    await state.update_data(joriy={"nomi": nomi, "birlik": "дона", "izoh": C.plita_olcham(nomi)})
    await m.answer("1 dona narxi (ҚҚСsiz, so'mda)?")
    await state.set_state(T.plita_narx)


@r.message(T.plita_narx, F.text)
async def t_plita_narx(m: Message, state: FSMContext):
    v = son(m.text)
    if not v:
        await m.answer("Narxni son bilan yozing, masalan: 1300000")
        return
    d = await state.get_data()
    j = d["joriy"]
    j["narx"] = v
    await state.update_data(joriy=j)
    await m.answer("Necha dona?")
    await state.set_state(T.miqdor)


@r.message(T.miqdor, F.text)
async def t_miqdor(m: Message, state: FSMContext):
    v = son(m.text)
    if not v:
        await m.answer("Miqdorni son bilan yozing, masalan: 12")
        return
    d = await state.get_data()
    t, j = d["t"], d["joriy"]
    j["soni"] = v
    t["mahsulotlar"].append(j)
    await state.update_data(t=t, joriy=None)
    royxat = "\n".join(f"• {e(x['nomi'])} — {x['soni']:g} {x['birlik']}" for x in t["mahsulotlar"])
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Yana mahsulot", callback_data="yana:1")
    kb.button(text="➡️ Davom etish", callback_data="yana:0")
    await m.answer(f"Taklifdagi mahsulotlar:\n{royxat}", reply_markup=kb.as_markup())
    await state.set_state(T.yana)


@r.callback_query(T.yana, F.data.startswith("yana:"))
async def t_yana(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_reply_markup(reply_markup=None)
    await cb.answer()
    if cb.data == "yana:1":
        await mahsulot_sora(cb.message, state)
        return
    await cb.message.answer(
        "📍 Obyekt lokatsiyasini yuboring — bot zavoddan masofani o'zi o'lchaydi.\n"
        "(Mijoz yuborgan lokatsiyani shu yerga forward qilsangiz ham bo'ladi.)",
        reply_markup=rk([LOK_TUGMA], [B_KM]))
    await state.set_state(T.joy)


@r.message(T.joy, F.location)
async def t_joy_lok(m: Message, state: FSMContext):
    lat, lon = m.location.latitude, m.location.longitude
    km, manba = await yol_masofa_km(lat, lon)
    t = await _t(state)
    t["yetkazish"].update(masofa_km=km, lat=lat, lon=lon)
    await state.update_data(t=t)
    izoh = "yo'l bo'yicha" if manba == "yo'l" else "taxminiy (to'g'ri chiziq × 1,3)"
    await m.answer(f"Masofa: <b>{km:g} km</b> ({izoh}).")
    await qoshimcha_sora(m, state)


@r.message(T.joy, F.text == B_KM)
async def t_joy_km(m: Message, state: FSMContext):
    await m.answer("Masofani km da yozing (masalan: 18):", reply_markup=FAQAT_BEKOR)
    await state.set_state(T.km)


@r.message(T.joy, F.text == "__masofasiz_ochirilgan__")
async def t_joy_yoq(m: Message, state: FSMContext):
    await qoshimcha_sora(m, state)


@r.message(T.joy)
async def t_joy_boshqa(m: Message):
    await m.answer("Lokatsiya majburiy 📍 «📍 Lokatsiya yuborish» ni bosing yoki «✍️ Km ni o'zim yozaman» ni tanlang.")


@r.message(T.km, F.text)
async def t_km(m: Message, state: FSMContext):
    v = son(m.text)
    if v is None:
        await m.answer("Km ni son bilan yozing, masalan: 18")
        return
    t = await _t(state)
    t["yetkazish"]["masofa_km"] = v
    await state.update_data(t=t)
    await qoshimcha_sora(m, state)


async def qoshimcha_sora(m: Message, state: FSMContext):
    t = await _t(state)
    kb = InlineKeyboardBuilder()
    if t["tur"] == "beton":
        kb.button(text="Nasos kerak emas", callback_data="q:yoq")
        kb.button(text="Nasos kerak", callback_data="q:nasos")
        savol = "🏗 Beton nasosi kerakmi?"
    else:
        kb.button(text="Avtokran bilan", callback_data="q:kran")
        kb.button(text="Avtokransiz", callback_data="q:yoq")
        savol = "🏗 Avtokran xizmati qo'shilsinmi?"
    await m.answer(savol, reply_markup=FAQAT_BEKOR)
    await m.answer("Tanlang:", reply_markup=kb.as_markup())
    await state.set_state(T.qoshimcha)


@r.callback_query(T.qoshimcha, F.data.startswith("q:"))
async def t_qoshimcha(cb: CallbackQuery, state: FSMContext):
    k = cb.data[2:]
    t = await _t(state)
    await cb.answer()
    if t["tur"] == "plita":
        t["yetkazish"]["avtokran"] = (k == "kran")
        await state.update_data(t=t)
        await cb.message.edit_text("Avtokran: " + ("bor" if k == "kran" else "yo'q"))
        await avans_sora(cb.message, state)
    elif k == "nasos":
        await cb.message.edit_text("Nasos: kerak")
        await cb.message.answer("Nasos xizmati narxi (ҚҚСsiz, so'mda)? Kelishilgan summani yozing:")
        await state.set_state(T.nasos_narx)
    else:
        await cb.message.edit_text("Nasos: kerak emas")
        await avans_sora(cb.message, state)


@r.message(T.nasos_narx, F.text)
async def t_nasos(m: Message, state: FSMContext):
    v = son(m.text)
    if not v:
        await m.answer("Narxni son bilan yozing, masalan: 1500000")
        return
    t = await _t(state)
    t["yetkazish"]["nasos"] = {"narx": v, "soni": 1}
    await state.update_data(t=t)
    await avans_sora(m, state)


async def avans_sora(m: Message, state: FSMContext):
    """Avval to'lov shaklini so'raydi (ҚҚС shunga bog'liq), keyin avansni."""
    kb = InlineKeyboardBuilder()
    kb.button(text="💵 Naqd", callback_data="ts:naqd")
    kb.button(text="🏦 Perechisleniye", callback_data="ts:otkazma")
    await m.answer("To'lov shakli qanday? (ҚҚС 12% shunga qarab hisoblanadi)", reply_markup=kb.as_markup())
    await state.set_state(T.tolov_shakli)


@r.callback_query(T.tolov_shakli, F.data.startswith("ts:"))
async def t_tolov_shakli(cb: CallbackQuery, state: FSMContext):
    k = cb.data[3:]
    t = await _t(state)
    t["tolov_shakli"] = k
    await state.update_data(t=t)
    sh = C.TOLOV_SHAKLI[k]
    await cb.message.edit_text(f"To'lov shakli: <b>{'Naqd' if k == 'naqd' else 'Perechisleniye'}</b>"
                               f" — {'ҚҚС 12% qo' + chr(39) + 'shiladi' if sh['qqs'] else 'ҚҚСsiz'}")
    await cb.answer()
    await cb.message.answer("💵 Avans olindimi? Summani yozing (so'mda):", reply_markup=rk([B_AVANSSIZ]))
    await state.set_state(T.avans)


@r.message(T.avans, F.text)
async def t_avans(m: Message, state: FSMContext):
    v = 0 if m.text == B_AVANSSIZ else son(m.text)
    if v is None:
        await m.answer("Summani son bilan yozing yoki «Avans yo'q» ni bosing.")
        return
    t = await _t(state)
    t["avans"] = v
    await state.update_data(t=t)
    await m.answer("📅 Yetkazish muddati? (masalan: 25.11.2026 yoki «3 kun ichida»)", reply_markup=rk([B_OTKAZ]))
    await state.set_state(T.muddat)


@r.message(T.muddat, F.text)
async def t_muddat(m: Message, state: FSMContext):
    t = await _t(state)
    if m.text != B_OTKAZ:
        t["mijoz"]["muddat"] = m.text.strip()
    t["mijoz"]["menejer"] = m.from_user.full_name
    await state.update_data(t=t)

    rows, miqdor, jami, avans, qoldiq = hisobla(t)
    lines = [f"<b>Tekshiring:</b>",
             f"👤 {e(t['mijoz'].get('nomi'))}  📞 {e(t['mijoz'].get('tel', '—'))}",
             f"👷 {e(t['mijoz'].get('prorab', '—'))}  📞 {e(t['mijoz'].get('prorab_tel', '—'))}",
             f"🏗 {e(t['mijoz'].get('obyekt'))}", ""]
    for x in rows:
        lines.append(f"• {e(x['nomi'])}: {x['soni']:g} {x['birlik']} × {som(x['narx_qqs'])} = <b>{som(x['jami'])}</b>")
    qqs_jami = sum(x["qqs"] * x["soni"] for x in rows)
    lines += ["", f"To'lov shakli: {'Naqd' if t.get('tolov_shakli') == 'naqd' else 'Perechisleniye'}",
              f"ҚҚСsiz: {som(jami - qqs_jami)} · ҚҚС 12%: {som(qqs_jami)}",
              f"Jami: <b>{som(jami)}</b> so'm"]
    if avans:
        lines += [f"Avans: {som(avans)}", f"Qoldiq: <b>{som(qoldiq)}</b>"]
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ PDF yaratish", callback_data="ok:pdf")
    kb.button(text="❌ Bekor", callback_data="ok:bekor")
    await m.answer("\n".join(lines), reply_markup=kb.as_markup())
    await state.set_state(T.tasdiq)


@r.callback_query(T.tasdiq, F.data.startswith("ok:"))
async def t_tasdiq(cb: CallbackQuery, state: FSMContext, bot: Bot):
    await cb.message.edit_reply_markup(reply_markup=None)
    await cb.answer()
    if cb.data == "ok:bekor":
        await state.clear()
        await cb.message.answer("Bekor qilindi.", reply_markup=MENU)
        return
    t = await _t(state)
    await state.clear()
    _, _, jami, avans, qoldiq = hisobla(t)
    tid = db.taklif_qosh(cb.from_user.id, cb.from_user.full_name, t, jami)
    t["raqam"] = f"{tid:04d}"
    t["sana"] = date.today().strftime("%d.%m.%Y")
    C.TAKLIF_PAPKA.mkdir(exist_ok=True)
    nom = re.sub(r"[^\w]+", "_", t["mijoz"].get("nomi") or "mijoz").strip("_")[:30]
    path = C.TAKLIF_PAPKA / f"Taklif_{tid:04d}_{nom}.pdf"
    make_offer(t, path)

    caption = (f"💼 Tijorat taklifi <b>#{tid:04d}</b>\n👤 {e(t['mijoz'].get('nomi'))} · 🏗 {e(t['mijoz'].get('obyekt'))}\n"
               f"Jami: <b>{som(jami)}</b> so'm")
    await cb.message.answer_document(FSInputFile(path, filename=path.name), caption=caption,
                                     reply_markup=MENU)
    await guruhga(bot, "send_document", document=FSInputFile(path, filename=path.name),
                  caption=caption + f"\nRealizator: {e(cb.from_user.full_name)}")


@r.callback_query(F.data.startswith("buy:") | F.data.startswith("rad:"))
async def t_holat_ochiq(cb: CallbackQuery):
    # To'lov/qarz bo'limi o'chirilgan: eski xabarlardagi tugmalar endi hech narsa qilmaydi
    await cb.answer("Bu bo'lim o'chirilgan", show_alert=True)
    await cb.message.edit_reply_markup(reply_markup=None)


async def t_holat(cb: CallbackQuery, bot: Bot):  # hozir ishlatilmaydi
    k, tid = cb.data.split(":")
    tid = int(tid)
    row = db.taklif_ol(tid)
    if not row:
        await cb.answer("Taklif topilmadi", show_alert=True)
        return
    if row["holat"] != "taklif":
        await cb.answer(f"Bu taklif allaqachon: {row['holat']}", show_alert=True)
        return
    await cb.message.edit_reply_markup(reply_markup=None)
    if k == "rad":
        db.taklif_holat(tid, "bekor")
        await cb.answer("Rad etildi deb belgilandi")
        return
    db.taklif_holat(tid, "buyurtma")
    import json
    avans = (json.loads(row["data"]) or {}).get("avans") or 0
    if avans:
        db.tolov_qosh(realizator_id=cb.from_user.id, realizator=cb.from_user.full_name, taklif_id=tid,
                      summa_som=avans, valyuta="som", summa_asl=avans, kurs=1, turi="Avans (taklifda)")
    await cb.answer("Buyurtma ✅")
    qarz = row["jami"] - avans
    await cb.message.answer(f"✅ #{tid:04d} buyurtmaga aylandi. Qarz: <b>{som(qarz)}</b> so'm")
    await guruhga(bot, "send_message",
                  text=f"✅ Buyurtma <b>#{tid:04d}</b> — {e(row['mijoz'])} ({e(row['obyekt'])})\n"
                       f"Jami: {som(row['jami'])} · Avans: {som(avans)} · Qarz: <b>{som(qarz)}</b>\n"
                       f"Realizator: {e(cb.from_user.full_name)}")


# ------------------------------------------------------------------ RASMIY TAKLIF
def rasmiy_kb(tanlangan):
    kb = InlineKeyboardBuilder()
    for i, (_, nomi, _, narx) in enumerate(mahsulotlar_royxati()):
        kb.button(text=("✅ " if i in tanlangan else "▫️ ") + f"{nomi} — {som(narx)}", callback_data=f"rx:{i}")
    kb.button(text="☑️ Hammasi", callback_data="rx:all")
    kb.button(text="⬜ Hech biri", callback_data="rx:none")
    kb.button(text="📄 PDF yaratish", callback_data="rx:ok")
    kb.adjust(*([1] * len(mahsulotlar_royxati())), 2, 1)
    return kb.as_markup()


@r.callback_query(T.rasmiy, F.data.startswith("rx:"))
async def t_rasmiy(cb: CallbackQuery, state: FSMContext, bot: Bot):
    k = cb.data[3:]
    t = await _t(state)
    if k != "ok":
        if k == "all":
            t["tanlangan"] = list(range(len(mahsulotlar_royxati())))
        elif k == "none":
            t["tanlangan"] = []
        else:
            s_ = set(t["tanlangan"])
            s_ ^= {int(k)}
            t["tanlangan"] = sorted(s_)
        await state.update_data(t=t)
        await cb.message.edit_reply_markup(reply_markup=rasmiy_kb(t["tanlangan"]))
        await cb.answer()
        return
    if not t["tanlangan"]:
        await cb.answer("Kamida bitta mahsulot belgilang", show_alert=True)
        return
    await cb.message.edit_reply_markup(reply_markup=None)
    await cb.answer()
    await state.clear()
    tid = db.taklif_qosh(cb.from_user.id, cb.from_user.full_name, t, 0)
    db.taklif_holat(tid, "rasmiy")
    t["raqam"] = f"{tid:04d}"
    C.TAKLIF_PAPKA.mkdir(exist_ok=True)
    nom = re.sub(r"[^\w]+", "_", t["mijoz"].get("nomi") or "rasmiy").strip("_")[:30]
    path = C.TAKLIF_PAPKA / f"Rasmiy_taklif_{tid:04d}_{nom}.pdf"
    n = make_rasmiy(t, path)
    caption = (f"📄 Rasmiy tijorat taklifi <b>№ {tid:04d}</b>\n🏢 {e(t['mijoz'].get('nomi') or '—')} · {n} ta mahsulot")
    await cb.message.answer_document(FSInputFile(path, filename=path.name), caption=caption, reply_markup=MENU)
    await guruhga(bot, "send_document", document=FSInputFile(path, filename=path.name),
                  caption=caption + f"\nRealizator: {e(cb.from_user.full_name)}")


# ================================================================== PRAYS-LIST
@r.message(StateFilter(None), F.text == B_PRAYS)
async def prays_menu(m: Message):
    kb = InlineKeyboardBuilder()
    for k, (nomi, _, _) in PRAYSLAR.items():
        kb.button(text=nomi, callback_data=f"pr:{k}")
    kb.adjust(1)
    await m.answer("Qaysi prays-list kerak?", reply_markup=kb.as_markup())


@r.callback_query(F.data.startswith("pr:"))
async def prays_yubor(cb: CallbackQuery):
    k = cb.data[3:]
    if k not in PRAYSLAR:
        await cb.answer()
        return
    await cb.answer("Tayyorlanmoqda...")
    nomi, fayl, fn = PRAYSLAR[k]
    C.TAKLIF_PAPKA.mkdir(exist_ok=True)
    path = C.TAKLIF_PAPKA / fayl
    fn(path)
    await cb.message.answer_document(FSInputFile(path, filename=fayl),
                                     caption=f"📑 Prays-list: {nomi} · {date.today():%d.%m.%Y}")


# ================================================================== YANGI OBYEKT
@r.message(StateFilter(None), F.text == B_OBYEKT)
async def o_start(m: Message, state: FSMContext):
    await state.clear()
    await state.update_data(o={"ehtiyojlar": []})
    await m.answer("🏗 Yangi obyekt. Obyekt rasmini yuboring (📎 orqali):", reply_markup=FAQAT_BEKOR)
    await state.set_state(O.rasm)


async def _o(state):
    return (await state.get_data())["o"]


@r.message(O.rasm, ~F.photo)
async def o_rasmsiz(m: Message):
    await m.answer("Obyekt rasmi majburiy 📷 Rasmni 📎 orqali yuboring.")


@r.message(O.rasm, F.photo)
async def o_rasm(m: Message, state: FSMContext):
    o = await _o(state)
    o["rasm_file_id"] = m.photo[-1].file_id
    await state.update_data(o=o)
    await m.answer("👤 Uy egasi (mijoz) ismi?", reply_markup=FAQAT_BEKOR)
    await state.set_state(O.egasi)


@r.message(O.egasi, F.text)
async def o_egasi(m: Message, state: FSMContext):
    o = await _o(state)
    o["egasi"] = m.text.strip()
    await state.update_data(o=o)
    await m.answer("📞 Telefoni?")
    await state.set_state(O.tel)


@r.message(O.tel)
async def o_tel(m: Message, state: FSMContext):
    tel = telefon(m)
    if not tel:
        await m.answer("Telefon raqami majburiy 📞 To'liq raqamni yozing, masalan: +998 90 123 45 67")
        return
    o = await _o(state)
    o["tel"] = tel
    await state.update_data(o=o)
    await m.answer("👷 Prorabning ismi?", reply_markup=rk([B_OTKAZ]))
    await state.set_state(O.prorab)


@r.message(O.prorab, F.text)
async def o_prorab(m: Message, state: FSMContext):
    o = await _o(state)
    if m.text == B_OTKAZ:
        await m.answer("📌 Hududni tanlang:", reply_markup=FAQAT_BEKOR)
        await m.answer("Hudud:", reply_markup=hudud_kb())
        await state.set_state(O.hudud)
        return
    o["prorab"] = m.text.strip()
    await state.update_data(o=o)
    await m.answer("📞 Prorabning telefoni?", reply_markup=rk([B_OTKAZ]))
    await state.set_state(O.prorab_tel)


@r.message(O.prorab_tel)
async def o_prorab_tel(m: Message, state: FSMContext):
    o = await _o(state)
    if m.contact:
        o["prorab_tel"] = m.contact.phone_number
    elif m.text and m.text != B_OTKAZ:
        o["prorab_tel"] = m.text.strip()
    await state.update_data(o=o)
    await m.answer("📌 Hududni tanlang:", reply_markup=FAQAT_BEKOR)
    await m.answer("Hudud:", reply_markup=hudud_kb())
    await state.set_state(O.hudud)


def hudud_kb():
    kb = InlineKeyboardBuilder()
    for i, v in enumerate(C.HUDUDLAR):
        kb.button(text=v, callback_data=f"vl:{i}")
    kb.adjust(1)
    return kb.as_markup()


@r.callback_query(O.hudud, F.data.startswith("vl:") | F.data.startswith("tm:"))
async def o_hudud(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    viloyatlar = list(C.HUDUDLAR)
    if cb.data == "vl:orqa":
        await cb.message.edit_text("📌 Hududni tanlang:", reply_markup=hudud_kb())
        return
    if cb.data.startswith("vl:"):
        i = int(cb.data[3:])
        kb = InlineKeyboardBuilder()
        for j, t in enumerate(C.HUDUDLAR[viloyatlar[i]]):
            kb.button(text=t, callback_data=f"tm:{i}:{j}")
        kb.button(text="⬅️ Orqaga", callback_data="vl:orqa")
        kb.adjust(2)
        await cb.message.edit_text(f"📌 {viloyatlar[i]} — tumanni tanlang:", reply_markup=kb.as_markup())
        return
    _, i, j = cb.data.split(":")
    vil = viloyatlar[int(i)]
    tuman = C.HUDUDLAR[vil][int(j)]
    o = await _o(state)
    o["manzil"] = f"{vil}, {tuman}"
    await state.update_data(o=o)
    await cb.message.edit_text(f"📌 {vil}, <b>{tuman}</b>")
    await cb.message.answer("Mo'ljal? (mahalla, ko'cha)", reply_markup=rk([B_OTKAZ]))
    await state.set_state(O.manzil)


def ehtiyoj_kb(tanlangan):
    kb = InlineKeyboardBuilder()
    for i, n in enumerate(C.EHTIYOJLAR):
        kb.button(text=("✅ " if i in tanlangan else "▫️ ") + n, callback_data=f"eh:{i}")
    kb.button(text="➡️ Tayyor", callback_data="eh:ok")
    kb.adjust(2)
    return kb.as_markup()


@r.message(O.manzil, F.text)
async def o_manzil(m: Message, state: FSMContext):
    o = await _o(state)
    if m.text != B_OTKAZ:
        o["manzil"] = f'{o.get("manzil", "")}, {m.text.strip()}'.strip(", ")
    await state.update_data(o=o)
    await m.answer("Obyektga nimalar kerak? Belgilang (kerak bo'lmagan yoki noma'lumlar ❓ bo'lib chiqadi):",
                   reply_markup=ehtiyoj_kb([]))
    await state.set_state(O.ehtiyoj)


@r.callback_query(O.ehtiyoj, F.data.startswith("eh:"))
async def o_ehtiyoj(cb: CallbackQuery, state: FSMContext):
    o = await _o(state)
    k = cb.data[3:]
    if k != "ok":
        i = int(k)
        s = set(o["ehtiyojlar"])
        s ^= {i}
        o["ehtiyojlar"] = sorted(s)
        await state.update_data(o=o)
        await cb.message.edit_reply_markup(reply_markup=ehtiyoj_kb(o["ehtiyojlar"]))
        await cb.answer()
        return
    await cb.message.edit_reply_markup(reply_markup=None)
    await cb.answer()
    await cb.message.answer("📍 Obyekt lokatsiyasini yuboring (📎 → Lokatsiya yoki pastdagi tugma):",
                            reply_markup=rk([LOK_TUGMA]))
    await state.set_state(O.joy)


@r.message(O.joy, ~F.location)
async def o_joysiz(m: Message):
    await m.answer("Lokatsiya majburiy 📍 Pastdagi «📍 Lokatsiya yuborish» tugmasini bosing yoki 📎 → Lokatsiya.")


@r.message(O.joy, F.location)
async def o_joy(m: Message, state: FSMContext, bot: Bot):
    o = await _o(state)
    await state.clear()
    lat = m.location.latitude if m.location else None
    lon = m.location.longitude if m.location else None
    nomlar = [C.EHTIYOJLAR[i] for i in o["ehtiyojlar"]]
    oid = db.obyekt_qosh(realizator_id=m.from_user.id, realizator=m.from_user.full_name,
                        egasi=o["egasi"], tel=o["tel"], prorab=o.get("prorab"), prorab_tel=o.get("prorab_tel"),
                        manzil=o["manzil"], ehtiyojlar=nomlar,
                        lat=lat, lon=lon, rasm_file_id=o["rasm_file_id"])
    qator = "\n".join(("✅ " if i in o["ehtiyojlar"] else "❓ ") + n for i, n in enumerate(C.EHTIYOJLAR))
    km = ""
    if lat is not None:
        k, _ = await yol_masofa_km(lat, lon)
        km = f"\n🚚 Zavoddan: ~{k:g} km"
    prorab = ""
    if o.get("prorab") or o.get("prorab_tel"):
        prorab = f"👷 Prorab: {e(o.get('prorab') or '—')} · {e(o.get('prorab_tel') or '—')}\n"
    matn = (f"🏗 <b>Yangi obyekt #{oid:04d}</b>\n"
            f"👤 {e(o['egasi'])} (uy egasi)\n📞 {e(o['tel'])}\n{prorab}📌 {e(o['manzil'])}{km}\n"
            f"📅 {date.today():%d.%m.%Y}\n\n{qator}\n\nRealizator: {e(m.from_user.full_name)}")
    await m.answer(f"Saqlandi ✅ Obyekt #{oid:04d}", reply_markup=MENU)
    if o["rasm_file_id"]:
        await guruhga(bot, "send_photo", photo=o["rasm_file_id"], caption=matn[:1024])
    else:
        await guruhga(bot, "send_message", text=matn)
    if lat is not None:
        await guruhga(bot, "send_location", latitude=lat, longitude=lon)


# ================================================================== TO'LOV
@r.message(StateFilter(None), F.text == "__tolov_ochirilgan__")
async def p_start(m: Message, state: FSMContext):
    await state.clear()
    royxat = db.buyurtmalar_royxat(m.from_user.id) or db.buyurtmalar_royxat()
    kb = InlineKeyboardBuilder()
    for b in royxat:
        kb.button(text=f"#{b['id']:04d} {b['mijoz']} · {b['obyekt']}"[:60], callback_data=f"pb:{b['id']}")
    kb.adjust(1)
    await m.answer("💰 To'lov. Qaysi buyurtma uchun? Ro'yxatdan tanlang yoki buyurtma raqamini yozing (masalan: 12).",
                   reply_markup=FAQAT_BEKOR)
    if royxat:
        await m.answer("So'nggi buyurtmalar:", reply_markup=kb.as_markup())
    else:
        await m.answer("Hali buyurtmalar yo'q. Avval taklifda «✅ Buyurtma bo'ldi» ni bosing.")
    await state.set_state(P.buyurtma)


async def p_buyurtma_tanlandi(m: Message, state: FSMContext, tid: int):
    row = db.taklif_ol(tid)
    if not row or row["holat"] != "buyurtma":
        await m.answer("Bunday buyurtma topilmadi (yoki u hali «taklif» holatida). Raqamni tekshiring.")
        return
    await state.update_data(p={"taklif_id": tid, "mijoz": row["mijoz"], "obyekt": row["obyekt"]})
    kb = InlineKeyboardBuilder()
    kb.button(text="So'm", callback_data="v:som")
    kb.button(text="Dollar ($)", callback_data="v:usd")
    await m.answer(f"Buyurtma #{tid:04d}: {e(row['mijoz'])} · {e(row['obyekt'])}\nValyuta?", reply_markup=kb.as_markup())
    await state.set_state(P.valyuta)


@r.callback_query(P.buyurtma, F.data.startswith("pb:"))
async def p_buyurtma_cb(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_reply_markup(reply_markup=None)
    await cb.answer()
    await p_buyurtma_tanlandi(cb.message, state, int(cb.data[3:]))


@r.message(P.buyurtma, F.text)
async def p_buyurtma_txt(m: Message, state: FSMContext):
    v = son(m.text.lstrip("#"))
    if not v:
        await m.answer("Buyurtma raqamini son bilan yozing, masalan: 12")
        return
    await p_buyurtma_tanlandi(m, state, int(v))


@r.callback_query(P.valyuta, F.data.startswith("v:"))
async def p_valyuta(cb: CallbackQuery, state: FSMContext):
    d = (await state.get_data())["p"]
    d["valyuta"] = cb.data[2:]
    await state.update_data(p=d)
    await cb.message.edit_reply_markup(reply_markup=None)
    await cb.answer()
    if d["valyuta"] == "usd":
        await cb.message.answer("Dollar kursi (1$ = ? so'm)?")
        await state.set_state(P.kurs)
    else:
        await cb.message.answer("Summa (so'mda)?")
        await state.set_state(P.summa)


@r.message(P.kurs, F.text)
async def p_kurs(m: Message, state: FSMContext):
    v = son(m.text)
    if not v:
        await m.answer("Kursni son bilan yozing, masalan: 12800")
        return
    d = (await state.get_data())["p"]
    d["kurs"] = v
    await state.update_data(p=d)
    await m.answer("Summa ($)?")
    await state.set_state(P.summa)


@r.message(P.summa, F.text)
async def p_summa(m: Message, state: FSMContext):
    v = son(m.text)
    if not v:
        await m.answer("Summani son bilan yozing.")
        return
    d = (await state.get_data())["p"]
    d["summa_asl"] = v
    d.setdefault("kurs", 1)
    d["summa_som"] = v * d["kurs"]
    await state.update_data(p=d)
    kb = InlineKeyboardBuilder()
    for x in ("Avans", "Qoldiq", "To'liq"):
        kb.button(text=x, callback_data=f"pt:{x}")
    await m.answer("To'lov turi?", reply_markup=kb.as_markup())
    await state.set_state(P.turi)


@r.callback_query(P.turi, F.data.startswith("pt:"))
async def p_turi(cb: CallbackQuery, state: FSMContext):
    d = (await state.get_data())["p"]
    d["turi"] = cb.data[3:]
    await state.update_data(p=d)
    await cb.message.edit_text(f"To'lov turi: {d['turi']}")
    await cb.answer()
    await cb.message.answer("🧾 Chek (skrinshot) rasmini yuboring:", reply_markup=rk([B_CHEKSIZ]))
    await state.set_state(P.chek)


@r.message(P.chek, F.photo | F.document | (F.text == B_CHEKSIZ))
async def p_chek(m: Message, state: FSMContext, bot: Bot):
    d = (await state.get_data())["p"]
    await state.clear()
    chek = m.photo[-1].file_id if m.photo else (m.document.file_id if m.document else None)
    pid = db.tolov_qosh(realizator_id=m.from_user.id, realizator=m.from_user.full_name, taklif_id=d["taklif_id"],
                        summa_som=d["summa_som"], valyuta=d["valyuta"], summa_asl=d["summa_asl"],
                        kurs=d["kurs"], turi=d["turi"], chek_file_id=chek)
    qarz = next((x["qarz"] for x in db.buyurtmalar_qarz() if x["id"] == d["taklif_id"]), 0)
    summa = f"{som(d['summa_asl'])} $ (kurs {som(d['kurs'])})" if d["valyuta"] == "usd" else f"{som(d['summa_som'])} so'm"
    matn = (f"💰 <b>To'lov</b> — buyurtma #{d['taklif_id']:04d}\n👤 {e(d['mijoz'])} · {e(d['obyekt'])}\n"
            f"Summa: <b>{summa}</b> ({e(d['turi'])})\n"
            f"Qolgan qarz: <b>{som(qarz)}</b> so'm" + (" ✅ yopildi" if qarz <= 0.5 else "") +
            f"\nRealizator: {e(m.from_user.full_name)}")
    await m.answer(f"Saqlandi ✅\n\n{matn}", reply_markup=MENU)
    if m.photo:
        await guruhga(bot, "send_photo", photo=chek, caption=matn)
    elif m.document:
        await guruhga(bot, "send_document", document=chek, caption=matn)
    else:
        await guruhga(bot, "send_message", text=matn)


# ================================================================== QARZDORLAR
def qarz_matni() -> list[str]:
    rows = db.buyurtmalar_qarz()
    if not rows:
        return ["📋 Qarzdorlar yo'q ✅"]
    jami = sum(x["qarz"] for x in rows)
    out = [f"📋 <b>Qarzdorlar</b> ({len(rows)} ta) — jami <b>{som(jami)}</b> so'm\n"]
    for x in rows:
        out.append(f"#{x['id']:04d} {e(x['mijoz'])} · {e(x['obyekt'])}\n"
                   f"   📞 {e(x['tel'] or '—')} · qarz <b>{som(x['qarz'])}</b> / {som(x['jami'])} · {e(x['realizator'])}")
    # Telegram 4096 belgidan uzun xabarni bo'laklarga ajratamiz
    qismlar, joriy = [], ""
    for s in out:
        if len(joriy) + len(s) > 3800:
            qismlar.append(joriy)
            joriy = ""
        joriy += s + "\n"
    qismlar.append(joriy)
    return qismlar


@r.message(StateFilter(None), F.text == "__qarz_ochirilgan__")
async def q_royxat(m: Message):
    for q in qarz_matni():
        await m.answer(q, reply_markup=MENU)


async def har_kuni_qarzlar(bot: Bot, soat=9):
    """Har kuni ertalab soat 9:00 da guruhga qarzdorlar ro'yxatini tashlaydi."""
    while True:
        now = datetime.now()
        keyingi = now.replace(hour=soat, minute=0, second=0, microsecond=0)
        if keyingi <= now:
            keyingi += timedelta(days=1)
        await asyncio.sleep((keyingi - now).total_seconds())
        try:
            for q in qarz_matni():
                await guruhga(bot, "send_message", text=q)
        except Exception as ex:
            log.warning("Ertalabki hisobot xatosi: %s", ex)


# ------------------------------------------------------------------ ISHGA TUSHIRISH
async def main():
    if not C.BOT_TOKEN:
        raise SystemExit("BOT_TOKEN topilmadi. .env faylga BOT_TOKEN=... yozing (README ga qarang).")
    db.init()
    bot = Bot(C.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(g)
    dp.include_router(r)
    await bot.set_my_commands([BotCommand(command="start", description="Bosh menyu"),
                               BotCommand(command="bekor", description="Bekor qilish"),
                               BotCommand(command="chatid", description="Guruh ID sini bilish")])
    log.info("Bot ishga tushdi")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
