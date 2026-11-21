"""O'chirilgan ESKI xabarlarni tez zaxiralash (guruhga hech narsa yuborilmaydi).

tiklash.py bilan saqlangan oxirgi oylik xabarlarga eski xabarlarni qo'shadi.
Bir vaqtda 8 ta faylni yuklaydi. To'xtab qolsa, qayta ishga tushirsangiz
saqlanganlarini o'tkazib yuborib davom etadi.
Ishga tushirish: zaxira.bat
"""
import asyncio
import csv
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from telethon import TelegramClient, types

from tiklash import BASE, OUT, SESSION, KUN, env, vaqt

PARALLEL = 8


async def main():
    e = env()
    client = TelegramClient(SESSION, int(e["TG_API_ID"]), e["TG_API_HASH"])
    await client.connect()
    if not await client.is_user_authorized():
        print("Avval tiklash.bat orqali akkauntga kiring.")
        return
    group_id = int(e.get("GROUP_ID", "0") or 0)
    guruh = await client.get_entity(group_id)

    jf = OUT / "ochirilgan_xabarlar.json"
    yozuvlar = json.loads(jf.read_text(encoding="utf-8")) if jf.exists() else []
    bor = {r["id"] for r in yozuvlar}
    (OUT / "media").mkdir(parents=True, exist_ok=True)

    print("Jurnal o'qilmoqda...")
    msgs, seen = [], set()
    async for ev in client.iter_admin_log(guruh, delete=True):
        m = getattr(ev, "old", None)
        if ev.deleted_message and m is not None and m.id not in seen and m.id not in bor:
            seen.add(m.id)
            msgs.append(m)
    msgs.sort(key=lambda m: (m.date, m.id))
    print(f"Zaxiralanadigan: {len(msgs)} ta (allaqachon saqlangan: {len(bor)} ta)")

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

    sem = asyncio.Semaphore(PARALLEL)
    start = max([r["n"] for r in yozuvlar], default=0)
    tayyor = 0

    def yoz():
        rows = sorted(yozuvlar, key=lambda r: r["n"])
        with open(OUT / "ochirilgan_xabarlar.csv", "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        jf.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")

    async def bitta(k, m):
        nonlocal tayyor
        n = start + k
        rec = {"n": n, "id": m.id, "vaqt": vaqt(m.date), "kim": await nom(m.sender_id or group_id),
               "matn": m.message or "", "tur": "matn", "fayl": "", "lat": "", "lon": "", "kontakt": "",
               "guruhga": False}
        if isinstance(m.media, (types.MessageMediaGeo, types.MessageMediaGeoLive, types.MessageMediaVenue)):
            rec["tur"] = "lokatsiya"
            rec["lat"], rec["lon"] = m.media.geo.lat, m.media.geo.long
        elif isinstance(m.media, types.MessageMediaContact):
            rec["tur"] = "kontakt"
            rec["kontakt"] = f"{m.media.first_name} {m.media.last_name} {m.media.phone_number}".strip()
        elif m.media and not isinstance(m.media, types.MessageMediaWebPage):
            rec["tur"] = "voice" if m.voice else ("video_note" if m.video_note else
                         ("rasm" if m.photo else ("video" if m.video else "fayl")))
            async with sem:
                try:
                    p = await client.download_media(m, file=str(OUT / "media" / f"{n:05d}_"))
                    rec["fayl"] = os.path.relpath(p, OUT) if p else ""
                except Exception as ex:
                    print(f"  #{n} media yuklab bo'lmadi: {ex}")
        yozuvlar.append(rec)
        tayyor += 1
        if tayyor % 100 == 0:
            print(f"  saqlandi {tayyor}/{len(msgs)}")
            yoz()

    # 200 tadan bo'lak-bo'lak, har bo'lakdan keyin faylga yoziladi
    for i in range(0, len(msgs), 200):
        await asyncio.gather(*(bitta(i + j + 1, m) for j, m in enumerate(msgs[i:i + 200])))
        yoz()
    print(f"\n✅ Zaxira tayyor: jami {len(yozuvlar)} ta xabar. Endi korish.bat ni bosing.")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
