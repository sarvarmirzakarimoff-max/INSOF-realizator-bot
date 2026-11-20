"""Prays-list PDF'lari (narxlar config.py dan olinadi)."""
from datetime import date

import config as C
from rasmiy import make_rasmiy
from taklif import make_offer


def beton_praylist(path):
    data = {"tur": "beton", "praylist": True, "tolov_shakli": "otkazma", "sana": date.today().strftime("%d.%m.%Y"),
            "mahsulotlar": [{"nomi": f"Бетон {m}", "birlik": "м³", "soni": 1, "narx": n} for m, n in C.BETON_NARX.items()],
            "yetkazish": {}, "avans": 0}
    make_offer(data, path)


def plita_praylist(path):
    data = {"tur": "plita", "praylist": True, "tolov_shakli": "otkazma", "sana": date.today().strftime("%d.%m.%Y"),
            "mahsulotlar": [{"nomi": f"{n}  ({C.plita_olcham(n)})", "birlik": "дона", "soni": 1, "narx": p}
                            for n, p in C.PLITA_NARX.items()],
            "yetkazish": {"avtokran": False}, "avans": 0}
    make_offer(data, path)


def boshqa_praylist(path):
    make_rasmiy({"raqam": "____", "sana": date.today()}, path)


PRAYSLAR = {
    "beton": ("🚛 Beton", "INSOF_beton_prays_list.pdf", beton_praylist),
    "plita": ("🧱 Kovakli plita (ПК)", "INSOF_plita_prays_list.pdf", plita_praylist),
    "boshqa": ("📄 Boshqa mahsulotlar", "INSOF_boshqa_mahsulotlar_prays_list.pdf", boshqa_praylist),
}
