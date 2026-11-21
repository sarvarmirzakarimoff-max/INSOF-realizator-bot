"""INSOF JBI | 2026 guruhida o'chirilgan xabarlarni qayta tiklash.

Telegram guruh jurnalida («Недавние действия») o'chirilgan xabarlar 48 soat saqlanadi.
Bu dastur sizning akkauntingiz orqali shu jurnalni o'qiydi:
  1) o'chgan xabarlarni (matn, rasm, video, ovoz, fayl, lokatsiya, kontakt) tiklash\\ papkasiga saqlaydi;
  2) so'ng, «ha» desangiz, ularni guruhga asl tartibda qayta joylaydi
     (har birining boshida kim va qachon yozgani ko'rsatiladi).

Ishga tushirish: tiklash.bat
Kirish ma'lumotlari (API ID/HASH, telefon, SMS kod) faqat shu kompyuterda qoladi.
"""
import asyncio
import csv
import json
import os
from datetime import timedelta
from pathlib import Path

from telethon import TelegramClient, errors, types

BASE = Path(__file__).parent
OUT = BASE / "tiklash"
SESSION = str(BASE / "tiklash_sessiya")
TZ = timedelta(hours=5)  # Toshkent vaqti
KUN = 30  # guruhga necha kunlik xabar qayta joylanadi


def env():
    d = {}
    for f in (BASE / ".env", BASE / "tiklash_api.txt"):
        if not f.exists():
            continue
        for line in f.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                d[k.strip()] = v.strip()
    return d


def vaqt(dt):
    return (dt + TZ).strftime("%d.%m.%Y %H:%M")


async def main():
    e = env()
    api_id = e.get("TG_API_ID", "")
    while not api_id.isdigit():
        api_id = input("API ID (faqat raqam, my.telegram.org -> App api_id): ").strip()
    api_hash = e.get("TG_API_HASH", "")
    while len(api_hash) != 32:
        api_hash = input("API HASH (32 belgili matn, App api_hash): ").strip()
    # keyingi safar qayta so'ramasligi uchun shu kompyuterda saqlab qo'yamiz
    kf = BASE / "tiklash_api.txt"
    if not kf.exists():
        kf.write_text(f"TG_API_ID={api_id}\nTG_API_HASH={api_hash}\n", encoding="utf-8")
    group_id = int(e.get("GROUP_ID", "0") or 0)
    if not group_id:
        group_id = int(input("Guruh ID (masalan -1002155598275): ").strip())

    client = TelegramClient(SESSION, int(api_id), api_hash, connection_retries=10, timeout=20)
    print("Telegram serveriga ulanmoqda (30 soniyagacha kutish mumkin)...")
    try:
        await client.connect()
        if not await client.is_user_authorized():
            while True:
                raw = input("Telefon raqam (masalan 901234567 yoki +998901234567): ")
                raqam = "".join(ch for ch in raw if ch.isdigit())
                if len(raqam) == 9:
                    raqam = "998" + raqam
                raqam = "+" + raqam
                try:
                    await client.send_code_request(raqam)
                    break
                except errors.PhoneNumberInvalidError:
                    print(f"  ❌ {raqam} — noto'g'ri raqam. Qaytadan kiriting.")
                except errors.FloodWaitError as fw:
                    print(f"  Ko'p urinish. {fw.seconds} soniya kuting...")
                    await asyncio.sleep(fw.seconds + 1)
            while True:
                kod = "".join(ch for ch in input("Telegram'ga kelgan kod: ") if ch.isdigit())
                try:
                    await client.sign_in(raqam, kod)
                    break
                except (errors.PhoneCodeInvalidError, errors.PhoneCodeEmptyError):
                    print("  ❌ Kod noto'g'ri. Qaytadan kiriting.")
                except errors.PhoneCodeExpiredError:
                    print("  Kod eskirgan, yangisi yuborildi.")
                    await client.send_code_request(raqam)
                except errors.SessionPasswordNeededError:
                    from telethon import functions
                    try:
                        hint = (await client(functions.account.GetPasswordRequest())).hint
                    except Exception:
                        hint = None
                    if hint:
                        print(f"  Parol eslatmasi (подсказка): {hint}")
                    print("  Klaviatura tili ENG va Caps Lock o'chiq ekanini tekshiring.")
                    while True:
                        try:
                            pw = input("Ikki bosqichli (bulutli) parol: ")
                            await client.sign_in(password=pw.strip("\r\n"))
                            print("\n" * 30)  # parolni ekrandan surib yuborish
                            break
                        except errors.PasswordHashInvalidError:
                            print(f"  ❌ Parol noto'g'ri ({len(pw)} belgi kiritildi). Qaytadan yozing.")
                        except errors.FloodWaitError as fw:
                            print(f"  Ko'p urinish. {fw.seconds} soniya kuting...")
                            await asyncio.sleep(fw.seconds + 1)
                    break
    except (errors.ApiIdInvalidError, errors.ApiIdPublishedFloodError):
        print("\n❌ API ID yoki API HASH noto'g'ri. tiklash.bat ni qayta ishga tushirib, to'g'ri kiriting.")
        await client.disconnect()
        for f in list(BASE.glob("tiklash_sessiya*")) + [BASE / "tiklash_api.txt"]:
            f.unlink(missing_ok=True)
        return
    me = await client.get_me()
    print(f"\nKirildi: {me.first_name} (@{me.username})")

    guruh = await client.get_entity(group_id)
    print(f"Guruh: {guruh.title}\nJurnaldan o'chirilgan xabarlar o'qilmoqda...")

    voqealar = []
    async for ev in client.iter_admin_log(guruh, delete=True):
        # Telethon: ev.deleted_message — bool, o'chgan xabarning o'zi esa ev.old da
        if ev.deleted_message and getattr(ev, "old", None) is not None:
            voqealar.append(ev)
    msgs = sorted((ev.old for ev in voqealar), key=lambda m: (m.date, m.id))
    # bir xil xabar ikki marta kelsa
    seen, uniq = set(), []
    for m in msgs:
        if m.id not in seen:
            seen.add(m.id)
            uniq.append(m)
    msgs = uniq
    print(f"Topildi: {len(msgs)} ta o'chirilgan xabar")
    if not msgs:
        await client.disconnect()
        return

    # ---------- Oxirgi 30 kun — guruhga qaytadi, qolgani faqat zaxira
    from datetime import datetime, timezone
    chegara = datetime.now(timezone.utc) - timedelta(days=KUN)
    yangi = [m for m in msgs if m.date >= chegara]
    eski = [m for m in msgs if m.date < chegara]
    print(f"Oxirgi {KUN} kun: {len(yangi)} ta (guruhga qayta joylanadi), undan eski: {len(eski)} ta (faqat zaxira)")

    OUT.mkdir(exist_ok=True)
    (OUT / "media").mkdir(exist_ok=True)
    nomlar = {}

    async def nom(uid):
        if uid not in nomlar:
            try:
                u = await client.get_entity(uid)
                nomlar[uid] = getattr(u, "title", None) or " ".join(
                    x for x in (getattr(u, "first_name", ""), getattr(u, "last_name", "")) if x) or str(uid)
            except Exception:
                nomlar[uid] = str(uid)
        return nomlar[uid]

    yozuvlar = []

    async def saqla(royxat, nomi):
        out = []
        for k, m in enumerate(royxat, 1):
            n = len(yozuvlar) + 1
            uid = m.sender_id or group_id
            rec = {"n": n, "id": m.id, "vaqt": vaqt(m.date), "kim": await nom(uid), "matn": m.message or "",
                   "tur": "matn", "fayl": "", "lat": "", "lon": "", "kontakt": "", "guruhga": nomi == "yangi"}
            if isinstance(m.media, (types.MessageMediaGeo, types.MessageMediaGeoLive, types.MessageMediaVenue)):
                rec["tur"] = "lokatsiya"
                rec["lat"], rec["lon"] = m.media.geo.lat, m.media.geo.long
            elif isinstance(m.media, types.MessageMediaContact):
                rec["tur"] = "kontakt"
                rec["kontakt"] = f"{m.media.first_name} {m.media.last_name} {m.media.phone_number}".strip()
            elif m.media and not isinstance(m.media, types.MessageMediaWebPage):
                rec["tur"] = "voice" if m.voice else ("video_note" if m.video_note else
                             ("rasm" if m.photo else ("video" if m.video else "fayl")))
                try:
                    p = await client.download_media(m, file=str(OUT / "media" / f"{n:05d}_"))
                    rec["fayl"] = os.path.relpath(p, OUT) if p else ""
                except Exception as ex:
                    print(f"  #{n} media yuklab bo'lmadi: {ex}")
            yozuvlar.append(rec)
            out.append(rec)
            if k % 25 == 0:
                print(f"  {nomi}: saqlandi {k}/{len(royxat)}")
        yoz_fayl()
        return out

    def yoz_fayl():
        if not yozuvlar:
            return
        with open(OUT / "ochirilgan_xabarlar.csv", "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(yozuvlar[0].keys()))
            w.writeheader()
            w.writerows(yozuvlar)
        (OUT / "ochirilgan_xabarlar.json").write_text(json.dumps(yozuvlar, ensure_ascii=False, indent=1),
                                                     encoding="utf-8")

    # 1) oxirgi oy: saqlash va guruhga joylash
    joylash = await saqla(yangi, "yangi")
    print(f"\n✅ Oxirgi {KUN} kunlik {len(joylash)} ta xabar saqlandi.")
    javob = input(f"Shu {len(joylash)} ta xabarni '{guruh.title}' guruhiga qayta joylaymi? (ha/yo'q): ").strip().lower()
    if javob in ("ha", "h", "yes", "y") and joylash:
        await client.send_message(guruh, f"♻️ O'chirilib ketgan oxirgi {KUN} kunlik {len(joylash)} ta xabar "
                                         f"qayta tiklanmoqda ({joylash[0]['vaqt']} — {joylash[-1]['vaqt']}).")
        for k, r in enumerate(joylash, 1):
            sarlavha = f"♻️ {r['kim']} · {r['vaqt']}"
            matn = f"{sarlavha}\n{r['matn']}".strip()
            while True:
                try:
                    if r["tur"] == "lokatsiya":
                        await client.send_message(guruh, sarlavha)
                        await client.send_message(guruh, file=types.InputMediaGeoPoint(
                            types.InputGeoPoint(float(r["lat"]), float(r["lon"]))))
                    elif r["tur"] == "kontakt":
                        await client.send_message(guruh, f"{matn}\n📇 {r['kontakt']}")
                    elif r["fayl"]:
                        await client.send_file(guruh, str(OUT / r["fayl"]), caption=matn[:1024],
                                               voice_note=r["tur"] == "voice", video_note=r["tur"] == "video_note")
                    else:
                        await client.send_message(guruh, matn[:4096])
                    break
                except errors.FloodWaitError as fw:
                    print(f"  Telegram cheklovi: {fw.seconds} soniya kutamiz...")
                    await asyncio.sleep(fw.seconds + 2)
                except Exception as ex:
                    print(f"  #{r['n']} joylab bo'lmadi: {ex}")
                    break
            if k % 20 == 0:
                print(f"  guruhga joylandi {k}/{len(joylash)}")
            await asyncio.sleep(1.5)
        print("✅ Oxirgi oylik xabarlar guruhga qayta joylandi.")
    else:
        print("Guruhga joylanmadi.")

    # 2) eskilari — faqat zaxira
    if eski:
        print(f"\nEski {len(eski)} ta xabar zaxiraga saqlanmoqda (guruhga joylanmaydi). Oynani yopmang...")
        await saqla(eski, "eski")
        print(f"✅ Zaxira tayyor: {OUT}")
    print("\n✅ Tugadi.")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
