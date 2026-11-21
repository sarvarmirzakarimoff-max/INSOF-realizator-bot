"""Telefonda ochiladigan arxiv: har oy uchun bitta mustaqil HTML fayl.

Rasmlar kichraytirilib fayl ichiga joylanadi, ovozli xabarlar ham ichida.
JavaScript kerak emas — Telegram'dan ochganda ham, iPhone/Android'da ham ko'rinadi.
Natija: tiklash\\telefon\\INSOF_arxiv_2025-08.html ...
Ishga tushirish: telefon_arxiv.bat
"""
import base64
import html
import io
import json
from collections import defaultdict
from pathlib import Path

from PIL import Image

BASE = Path(__file__).parent
SRC = BASE / "tiklash"
OUT = SRC / "telefon"
MAX_MB_ICHIGA = 4  # bundan katta video/fayl ichiga joylanmaydi
OYLAR = ["", "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun", "Iyul", "Avgust",
         "Sentabr", "Oktabr", "Noyabr", "Dekabr"]
TUR = {"matn": "", "rasm": "Rasm", "video": "Video", "voice": "Ovozli xabar", "video_note": "Dumaloq video",
       "fayl": "Fayl", "lokatsiya": "Lokatsiya", "kontakt": "Kontakt"}

CSS = """*{box-sizing:border-box}body{margin:0;font:15px/1.45 -apple-system,system-ui,"Segoe UI",Roboto,sans-serif;
background:#e7ebe0;color:#1d2733}header{background:#1f3a63;color:#fff;padding:14px 14px 10px;position:sticky;top:0}
header h1{margin:0;font-size:17px}header p{margin:4px 0 0;font-size:13px;opacity:.85}
main{max-width:720px;margin:0 auto;padding:8px 10px 60px}.day{text-align:center;margin:16px 0 6px}
.day span{background:rgba(0,0,0,.2);color:#fff;border-radius:12px;padding:3px 12px;font-size:13px}
.m{background:#fff;border-radius:12px;padding:8px 11px 5px;margin:6px 0;box-shadow:0 1px 2px rgba(0,0,0,.08)}
.g{border-left:3px solid #4caf50}.w{font-weight:600;color:#e8771e;font-size:14px}.t{white-space:pre-wrap;word-wrap:break-word}
.s{text-align:right;color:#6b7785;font-size:12px}img{display:block;max-width:100%;border-radius:8px;margin:4px 0}
audio,video{width:100%;margin:4px 0}a.b{display:inline-block;background:#eef3f8;border-radius:8px;padding:6px 10px;
color:#1f3a63;text-decoration:none;margin:3px 3px 3px 0}.n{color:#6b7785;font-style:italic}
nav{display:flex;justify-content:space-between;gap:8px;margin:18px 0}nav a{flex:1;text-align:center;background:#1f3a63;
color:#fff;border-radius:10px;padding:10px;text-decoration:none}"""


def e(s):
    return html.escape(str(s or ""))


def rasm_b64(p: Path):
    try:
        im = Image.open(p)
        im = im.convert("RGB")
        im.thumbnail((720, 720))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=62, optimize=True)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return None


def fayl_b64(p: Path, mime):
    if p.stat().st_size > MAX_MB_ICHIGA * 1024 * 1024:
        return None
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def mime(p: Path):
    x = p.suffix.lower()
    return {".ogg": "audio/ogg", ".oga": "audio/ogg", ".mp3": "audio/mpeg", ".m4a": "audio/mp4",
            ".mp4": "video/mp4", ".mov": "video/quicktime", ".pdf": "application/pdf"}.get(x, "application/octet-stream")


def karta(r):
    p = SRC / r["fayl"] if r.get("fayl") else None
    b = ""
    if r["tur"] == "rasm" and p and p.exists():
        src = rasm_b64(p)
        b = f'<img src="{src}" alt="">' if src else '<div class="n">[rasm ochilmadi]</div>'
    elif r["tur"] == "voice" and p and p.exists():
        src = fayl_b64(p, mime(p))
        b = f'<audio controls src="{src}"></audio>' if src else '<div class="n">[ovozli xabar katta]</div>'
    elif r["tur"] in ("video", "video_note") and p and p.exists():
        src = fayl_b64(p, mime(p))
        b = (f'<video controls playsinline preload="metadata" src="{src}"></video>' if src
             else f'<div class="n">[video katta — kompyuterdagi arxivda: {e(p.name)}]</div>')
    elif r["tur"] == "fayl" and p and p.exists():
        src = fayl_b64(p, mime(p))
        b = (f'<a class="b" download="{e(p.name)}" href="{src}">📎 {e(p.name)}</a>' if src
             else f'<div class="n">[fayl katta: {e(p.name)}]</div>')
    elif r["tur"] == "lokatsiya":
        b = (f'<a class="b" href="https://maps.google.com/?q={r["lat"]},{r["lon"]}">📍 Google xarita</a>'
             f'<a class="b" href="https://yandex.uz/maps/?pt={r["lon"]},{r["lat"]}&z=16">📍 Yandex xarita</a>')
    elif r["tur"] == "kontakt":
        b = f'<div class="t">📇 {e(r["kontakt"])}</div>'
    g = r.get("guruhga") in (True, "True")
    matn = f'<div class="t">{e(r["matn"])}</div>' if r.get("matn") else ""
    tur = TUR.get(r["tur"], "")
    return (f'<div class="m{" g" if g else ""}"><div class="w">{e(r["kim"])}</div>{b}{matn}'
            f'<div class="s">{e(r["vaqt"][11:])}{" · " + tur if tur else ""}</div></div>')


def main():
    data = json.loads((SRC / "ochirilgan_xabarlar.json").read_text(encoding="utf-8"))
    OUT.mkdir(exist_ok=True)
    oy = defaultdict(list)
    for r in data:
        d, m, y = r["vaqt"][:10].split(".")
        r["_k"] = f"{y}-{m}"
        r["_d"] = f"{y}{m}{d}{r['vaqt'][11:]}"
        oy[r["_k"]].append(r)
    keys = sorted(oy)
    for i, k in enumerate(keys):
        rows = sorted(oy[k], key=lambda r: (r["_d"], r["n"]))
        y, m = k.split("-")
        nomi = f"{OYLAR[int(m)]} {y}"
        parts, last = [], None
        for r in rows:
            kun = r["vaqt"][:10]
            if kun != last:
                parts.append(f'<div class="day"><span>{kun}</span></div>')
                last = kun
            parts.append(karta(r))
        nav = "<nav>"
        if i > 0:
            nav += f'<a href="INSOF_arxiv_{keys[i-1]}.html">← {OYLAR[int(keys[i-1][5:])]} {keys[i-1][:4]}</a>'
        if i < len(keys) - 1:
            nav += f'<a href="INSOF_arxiv_{keys[i+1]}.html">{OYLAR[int(keys[i+1][5:])]} {keys[i+1][:4]} →</a>'
        nav += "</nav>"
        doc = (f'<!DOCTYPE html><html lang="uz"><head><meta charset="utf-8">'
               f'<meta name="viewport" content="width=device-width, initial-scale=1">'
               f'<title>INSOF JBI arxiv — {nomi}</title><style>{CSS}</style></head><body>'
               f'<header><h1>INSOF JBI | 2026 — arxiv</h1><p>{nomi} · {len(rows)} ta xabar</p></header>'
               f'<main>{"".join(parts)}{nav}</main></body></html>')
        f = OUT / f"INSOF_arxiv_{k}.html"
        f.write_text(doc, encoding="utf-8")
        print(f"  {f.name}: {len(rows)} ta xabar, {f.stat().st_size / 1024 / 1024:.1f} MB")
    print(f"\n✅ Tayyor: {OUT}  ({len(keys)} ta fayl)")


if __name__ == "__main__":
    main()
