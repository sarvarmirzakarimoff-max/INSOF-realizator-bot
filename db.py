"""SQLite baza: obyektlar, takliflar (buyurtmalar), to'lovlar.

Fayl: insof.db (bot papkasida). Uni DB Browser for SQLite yoki Excel bilan ochib ko'rish mumkin.
"""
import json
import sqlite3
from contextlib import closing
from datetime import datetime

from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS obyektlar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vaqt TEXT, realizator_id INTEGER, realizator TEXT,
    egasi TEXT, tel TEXT, manzil TEXT, ehtiyojlar TEXT,
    lat REAL, lon REAL, rasm_file_id TEXT
);
CREATE TABLE IF NOT EXISTS takliflar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vaqt TEXT, realizator_id INTEGER, realizator TEXT,
    tur TEXT, mijoz TEXT, tel TEXT, obyekt TEXT,
    masofa_km REAL, jami REAL, data TEXT,
    holat TEXT DEFAULT 'taklif'          -- taklif | buyurtma | bekor
);
CREATE TABLE IF NOT EXISTS tolovlar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vaqt TEXT, realizator_id INTEGER, realizator TEXT,
    taklif_id INTEGER, summa_som REAL, valyuta TEXT, summa_asl REAL, kurs REAL,
    turi TEXT, chek_file_id TEXT, izoh TEXT
);
"""


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init():
    with closing(_conn()) as c, c:
        c.executescript(SCHEMA)
        # eski bazaga yangi ustunlar (prorab)
        for col in ("prorab", "prorab_tel"):
            try:
                c.execute(f"ALTER TABLE obyektlar ADD COLUMN {col} TEXT")
            except sqlite3.OperationalError:
                pass


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def obyekt_qosh(**kw) -> int:
    kw["vaqt"] = _now()
    kw["ehtiyojlar"] = json.dumps(kw.get("ehtiyojlar", []), ensure_ascii=False)
    cols = ",".join(kw)
    with closing(_conn()) as c, c:
        cur = c.execute(f"INSERT INTO obyektlar ({cols}) VALUES ({','.join('?' * len(kw))})", list(kw.values()))
        return cur.lastrowid


def taklif_qosh(realizator_id, realizator, data: dict, jami: float) -> int:
    m = data.get("mijoz", {})
    with closing(_conn()) as c, c:
        cur = c.execute(
            "INSERT INTO takliflar (vaqt, realizator_id, realizator, tur, mijoz, tel, obyekt, masofa_km, jami, data)"
            " VALUES (?,?,?,?,?,?,?,?,?,?)",
            (_now(), realizator_id, realizator, data.get("tur"), m.get("nomi"), m.get("tel"), m.get("obyekt"),
             data.get("yetkazish", {}).get("masofa_km"), jami, json.dumps(data, ensure_ascii=False)))
        return cur.lastrowid


def taklif_holat(taklif_id: int, holat: str):
    with closing(_conn()) as c, c:
        c.execute("UPDATE takliflar SET holat=? WHERE id=?", (holat, taklif_id))


def taklif_ol(taklif_id: int):
    with closing(_conn()) as c:
        return c.execute("SELECT * FROM takliflar WHERE id=?", (taklif_id,)).fetchone()


def tolov_qosh(**kw) -> int:
    kw["vaqt"] = _now()
    cols = ",".join(kw)
    with closing(_conn()) as c, c:
        cur = c.execute(f"INSERT INTO tolovlar ({cols}) VALUES ({','.join('?' * len(kw))})", list(kw.values()))
        return cur.lastrowid


def buyurtmalar_qarz(realizator_id: int | None = None):
    """Buyurtma holatidagi takliflar: jami, to'langan, qarz (qarz > 0 bo'lganlari)."""
    q = """
    SELECT t.id, t.mijoz, t.tel, t.obyekt, t.realizator, t.vaqt, t.jami,
           COALESCE((SELECT SUM(summa_som) FROM tolovlar p WHERE p.taklif_id=t.id), 0) AS tolangan
    FROM takliflar t WHERE t.holat='buyurtma'
    """
    args = []
    if realizator_id:
        q += " AND t.realizator_id=?"
        args.append(realizator_id)
    with closing(_conn()) as c:
        rows = [dict(r) for r in c.execute(q, args)]
    for r in rows:
        r["qarz"] = r["jami"] - r["tolangan"]
    return sorted([r for r in rows if r["qarz"] > 0.5], key=lambda r: -r["qarz"])


def buyurtmalar_royxat(realizator_id: int | None = None, limit=10):
    """To'lov kiritish uchun so'nggi buyurtmalar (qarzi bor yoki yo'q)."""
    q = "SELECT id, mijoz, obyekt, jami FROM takliflar WHERE holat='buyurtma'"
    args = []
    if realizator_id:
        q += " AND realizator_id=?"
        args.append(realizator_id)
    q += " ORDER BY id DESC LIMIT ?"
    args.append(limit)
    with closing(_conn()) as c:
        return [dict(r) for r in c.execute(q, args)]
