"""Tiklash dasturining Telegram seansini yakunlaydi va kalit fayllarini o'chiradi."""
import asyncio
from telethon import TelegramClient
from tiklash import BASE, SESSION, env


async def main():
    e = env()
    if e.get("TG_API_ID") and list(BASE.glob("tiklash_sessiya*.session")):
        c = TelegramClient(SESSION, int(e["TG_API_ID"]), e["TG_API_HASH"])
        await c.connect()
        if await c.is_user_authorized():
            await c.log_out()  # seans Telegram'da yakunlanadi, .session fayli o'chadi
            print("✅ Telegram'dagi 'INSOF tiklash' seansi yakunlandi.")
        else:
            await c.disconnect()
    for f in list(BASE.glob("tiklash_sessiya*")) + [BASE / "tiklash_api.txt"]:
        if f.exists():
            f.unlink()
            print(f"🗑 O'chirildi: {f.name}")
    print("Tayyor. tiklash papkasi (arxiv) joyida qoldi.")

asyncio.run(main())
