"""INSOF tijorat taklifi (plita / beton): hisob-kitob va PDF.

Bot `hisobla(data)` va `make_offer(data, out_path)` ni chaqiradi.
Qo'lda sinash:  python taklif.py namuna_beton.json chiqish.pdf
"""
import json
import math
import sys
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Flowable, Image, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle, KeepTogether)

BASE = Path(__file__).parent

# Sozlamalar (firma, narx, tariflar) — config.py da
from config import FIRMA, QQS, NARX_QQS_ICHIDA, AVTOKRAN, MIKSER, BETON_NARX, TOLOV_SHAKLI
from config import PLITA_TASHISH as PT

NAVY = colors.HexColor("#1F3A63")
ORANGE = colors.HexColor("#E8771E")
LIGHT = colors.HexColor("#EEF3F8")
GRID = colors.HexColor("#C9D3DF")
GREY = colors.HexColor("#4A5568")

TUR = {
    "plita": dict(
        sarlavha="Плиталар (ПК)",
        kirish="Компаниямиз таклиф этаётган плиталар стандартларга мувофиқ дастлабки сертификациядан ўтган бўлиб, "
               "уларни ҳар қандай мураккабликдаги объектларда қўллаш имконини беради. Биз учун ҳар бир мижоз муҳим, "
               "шунинг учун таклиф этилаётган маҳсулот сифатини кафолатлаймиз. Плиталарни «INSOF» Temir-Beton "
               "Mahsulotlari’дан харид қилинг — иншоотингиз мустаҳкам ва ишончли бўлади."),
    "beton": dict(
        sarlavha="Товар бетон",
        kirish="Компаниямиз таклиф этаётган маҳсулотлар стандартларга мувофиқ дастлабки сертификациядан ўтган бўлиб, "
               "уларни ҳар қандай мураккабликдаги объектларда қўллаш имконини беради. Биз учун ҳар бир мижоз муҳим, "
               "шунинг учун таклиф этилаётган маҳсулот сифатини кафолатлаймиз. Маҳсулотларни «INSOF» Temir-Beton "
               "Mahsulotlari’дан харид қилинг — иншоотингиз мустаҳкам ва ишончли бўлади."),
}


# ---------------------------------------------------------------- SHRIFTLAR
FD = str(BASE / "fonts") + "/"
pdfmetrics.registerFont(TTFont("LS", FD + "LiberationSans-Regular.ttf"))
pdfmetrics.registerFont(TTFont("LS-B", FD + "LiberationSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("LS-I", FD + "LiberationSans-Italic.ttf"))
pdfmetrics.registerFont(TTFont("LS-BI", FD + "LiberationSans-BoldItalic.ttf"))
pdfmetrics.registerFont(TTFont("DJ", FD + "DejaVuSans.ttf"))
pdfmetrics.registerFontFamily("LS", normal="LS", bold="LS-B", italic="LS-I", boldItalic="LS-BI")


def S(name, **kw):
    base = dict(fontName="LS", fontSize=9.5, leading=12.5, textColor=colors.black)
    base.update(kw)
    return ParagraphStyle(name, **base)


st_firm_title = S("ft", fontName="LS-B", fontSize=14, leading=18, textColor=NAVY, alignment=TA_RIGHT)
st_firm = S("f", fontSize=9, leading=11.5, textColor=NAVY, alignment=TA_RIGHT)
st_title = S("t", fontName="LS-B", fontSize=21, leading=26, textColor=NAVY, alignment=TA_CENTER)
st_sub = S("s", fontName="LS-B", fontSize=10.5, leading=14, textColor=ORANGE, alignment=TA_CENTER)
st_body = S("b", fontSize=9.5, leading=12.5, alignment=TA_JUSTIFY)
st_h2 = S("h2", fontName="LS-B", fontSize=12, leading=16, textColor=NAVY)
st_th = S("th", fontName="LS-B", fontSize=8.5, leading=10, textColor=colors.white, alignment=TA_CENTER)
st_td = S("td", fontSize=9.5, leading=11.5)
st_tdname = S("tdn", fontName="LS-B", fontSize=9.5, leading=11.5, textColor=NAVY)
st_tdsub = S("tds", fontSize=8, leading=10, textColor=GREY)
st_bullet = S("bl", fontSize=9.3, leading=12.3)
st_note = S("n", fontName="LS-I", fontSize=9, leading=12, textColor=NAVY)
st_lbl = S("l", fontSize=9, leading=12, textColor=GREY)
st_val = S("v", fontName="LS-B", fontSize=10, leading=12.5, textColor=NAVY)


def som(x):
    return f"{round(x):,}".replace(",", " ")


class HLine(Flowable):
    def __init__(self, width, color=ORANGE, thick=2.2):
        super().__init__()
        self.width, self.color, self.thick = width, color, thick

    def wrap(self, *a):
        return self.width, self.thick

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thick)
        self.canv.line(0, 0, self.width, 0)


# ---------------------------------------------------------------- HISOB-KITOB
def _qator(nomi, izoh, birlik, soni, narx, qqs_ichida, mahsulot, qqs_bor=True):
    if not qqs_bor:  # ҚҚСsiz hisob: narx o'zicha
        return dict(nomi=nomi, izoh=izoh, birlik=birlik, soni=soni, sof=narx, qqs=0,
                    narx_qqs=narx, jami=narx * soni, mahsulot=mahsulot)
    if qqs_ichida:
        narx_qqs, sof = narx, narx / (1 + QQS)
    else:
        sof, narx_qqs = narx, narx * (1 + QQS)
    return dict(nomi=nomi, izoh=izoh, birlik=birlik, soni=soni, sof=sof, qqs=narx_qqs - sof,
                narx_qqs=narx_qqs, jami=narx_qqs * soni, mahsulot=mahsulot)


def rows_plita(rows):
    """Plita qatorlaridan [(uzunlik_dm, eni_dm, soni), ...]"""
    import re as _re
    out = []
    for r in rows:
        if not r.get("mahsulot"):
            continue
        m = _re.search(r"(\d+)-(\d+)-", r["nomi"])
        L, W = (int(m[1]), int(m[2])) if m else (71, 12)  # noma'lum bo'lsa eng og'ir holat
        out.append((L, W, int(round(r["soni"]))))
    return out


def _shalanda_cap(L):
    for lo, hi, cap in PT["shalanda"]:
        if lo <= L <= hi:
            return cap
    return PT["shalanda"][0][2] if L > PT["shalanda"][0][1] else PT["shalanda"][-1][2]


def _xovo_xodka(items):
    n = sum(c for _, _, c in items)
    n12 = sum(c for _, W, c in items if W >= 12)
    if not n:
        return 0
    return max(math.ceil(n / PT["xovo_jami"]), math.ceil(n12 / PT["xovo_12_max"]))


def _shalanda_xodka(items):
    yuk = sum(c / _shalanda_cap(L) for L, _, c in items)
    return math.ceil(yuk - 1e-9) if yuk else 0


def xodka_narxi(km):
    for gacha, narx in PT["narxlar"]:
        if km <= gacha:
            return narx
    return PT["narxlar"][-1][1]


def plita_tashish(items, km):
    """Eng kam xodka bo'ladigan variantni tanlaydi: (xodka, 1 xodka narxi, izoh) yoki None."""
    if not items:
        return None
    variantlar = [(_shalanda_xodka(items), 0, "шаланда")]
    qisqa = [x for x in items if PT["xovo_min"] <= x[0] <= PT["xovo_max"]]
    uzun = [x for x in items if not (PT["xovo_min"] <= x[0] <= PT["xovo_max"])]
    if qisqa:
        sh, xv = _shalanda_xodka(uzun), _xovo_xodka(qisqa)
        variantlar.append((sh + xv, sh, xv))
    best = min(variantlar, key=lambda v: (v[0], isinstance(v[2], int)))
    jami = best[0]
    if isinstance(best[2], int):
        qism = []
        if best[1]:
            qism.append(f"{best[1]} шаланда")
        if best[2]:
            qism.append(f"{best[2]} хово")
        tur = " + ".join(qism)
    else:
        tur = f"{jami} шаланда"
    izoh = f"{tur} · {km:g} км".replace(".", ",")
    if km > PT["narxlar"][-1][0]:
        izoh += " (130 км дан узоқ — нарх келишилади)"
    return jami, xodka_narxi(km), izoh


def hisobla(data):
    """Qatorlar, yetkazib berish va jami summalarni hisoblaydi."""
    tur = data.get("tur", "plita")
    ichida = NARX_QQS_ICHIDA[tur]
    qb = TOLOV_SHAKLI.get(data.get("tolov_shakli", "otkazma"), {"qqs": True})["qqs"]
    _q = _qator
    def _qator_(*a):  # noqa: E306 — har qatorga to'lov shakli bo'yicha ҚҚС qoidasi
        return _q(*a, qqs_bor=qb)
    def_birlik = "м³" if tur == "beton" else "дона"
    rows = [_qator_(it["nomi"], it.get("izoh", ""), it.get("birlik", def_birlik), it["soni"], it["narx"], ichida, True)
            for it in data["mahsulotlar"]]
    miqdor = sum(r["soni"] for r in rows)
    yetk = data.get("yetkazish", {})
    km = yetk.get("masofa_km") or 0

    if tur == "plita":
        if yetk.get("avtokran", True) and miqdor:
            soat = max(AVTOKRAN["min_soat"], math.ceil(miqdor / AVTOKRAN["soatiga_plita"]))
            rows.append(_qator_("Автокран хизмати", f"{miqdor:g} та плита · {soat} соат", "соат", soat,
                               AVTOKRAN["soat_narxi"], True, False))
        if km > 0:
            tashish = plita_tashish(rows_plita(rows), km)
            if tashish:
                xodka, narx, izoh = tashish
                rows.append(_qator_("Етказиб бериш (йўл кираси)", izoh, "ходка", xodka, narx, False, False))
    else:  # beton
        h = MIKSER["hajm_m3"]
        toliq, chala = int(miqdor // h), round(miqdor - (miqdor // h) * h, 2)
        if chala > 0 and km > 0:
            narx = MIKSER["chala_min"] + max(0, km - MIKSER["chala_yaqin_km"]) * MIKSER["chala_km_narxi"]
            izoh = (f"{toliq} та тўлиқ миксер ({h:g} м³) + 1 та чала ({chala:g} м³) · {km:g} км"
                    if toliq else f"чала юк ({chala:g} м³) · {km:g} км")
            rows.append(_qator_("Йўл кира хизмати", izoh, "ходка", 1, narx, False, False))
        nasos = yetk.get("nasos")  # {"soni": 1, "narx": ...}
        if nasos:
            rows.append(_qator_("Бетон насоси", nasos.get("izoh", ""), nasos.get("birlik", "хизмат"),
                               nasos.get("soni", 1), nasos["narx"], ichida, False))

    jami = sum(r["jami"] for r in rows)
    avans = data.get("avans", 0) or 0
    return rows, miqdor, jami, avans, jami - avans


# ---------------------------------------------------------------- PDF
def make_offer(data, out_path, header_img=None):
    header_img = header_img or BASE / ("header_plita.jpg" if data.get("tur") == "plita" else "header.jpg")
    rows, plita_soni, jami, avans, qoldiq = hisobla(data)
    sana = data.get("sana") or date.today().strftime("%d.%m.%Y")

    doc = SimpleDocTemplate(str(out_path), pagesize=A4, leftMargin=17 * mm, rightMargin=17 * mm,
                            topMargin=11 * mm, bottomMargin=11 * mm,
                            title=f"Тижорат таклифи {data.get('raqam', '')}", author=FIRMA["nomi"])
    W = doc.width
    story = []

    # --- sarlavha: rasm + rekvizitlar
    img = Image(str(header_img), width=W * 0.40, height=W * 0.40 * 941 / 1496)
    f = FIRMA
    rekv = [
        Paragraph(f["nomi"], st_firm_title),
        Paragraph(f["manzil"], st_firm),
        Spacer(1, 4),
        Paragraph(f'<font name="LS-B">Тел:</font> <font name="LS-B" color="#E8771E">{f["tel"]}</font>', st_firm),
        Spacer(1, 5),
        Paragraph(f'<font name="LS-B">СТИР:</font> {f["stir"]}<br/><font name="LS-B">ИФУТ:</font> {f["ifut"]}<br/>'
                  f'<font name="LS-B">Ҳ/р:</font> {f["hr"]}<br/><font name="LS-B">Банк:</font> {f["bank"]}<br/>'
                  f'<font name="LS-B">МФО:</font> {f["mfo"]}', S("rk", fontSize=8.5, leading=11, textColor=NAVY, alignment=TA_RIGHT)),
    ]
    head = Table([[img, rekv]], colWidths=[W * 0.55, W * 0.45])
    head.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                              ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    story += [head, Spacer(1, 4), HLine(W), Spacer(1, 8)]

    # --- nom
    raqam = data.get("raqam", "")
    tur = data.get("tur", "plita")
    sar = TUR[tur]["sarlavha"]
    qqs_bor = TOLOV_SHAKLI.get(data.get("tolov_shakli", "otkazma"), {"qqs": True})["qqs"]
    story += [Paragraph("ТИЖОРАТ ТАКЛИФИ", st_title),
              Paragraph(f"{sar} · нархлар рўйхати · {sana}" if data.get("praylist")
                        else (f"{sar} · № {raqam} · {sana}" if raqam else f"{sar} · {sana}"), st_sub),
              Spacer(1, 7)]

    # --- mijoz kartochkasi
    m = data.get("mijoz", {})
    def kv(l, v):
        return [Paragraph(l, st_lbl), Paragraph(v or "—", st_val)]
    card = Table([
        kv("Мижоз", m.get("nomi")) + kv("Объект", m.get("obyekt")),
        kv("Телефон", m.get("tel")) + kv("Етказиш муддати", m.get("muddat")),
        kv("Менежер", m.get("menejer")) + kv("Масофа", f'{data.get("yetkazish", {}).get("masofa_km", 0):g} км' if data.get("yetkazish", {}).get("masofa_km") else None),
        kv("Тўлов шакли", TOLOV_SHAKLI.get(data.get("tolov_shakli", ""), {}).get("nomi"))
        + kv("Прораб", ", ".join(x for x in (m.get("prorab"), m.get("prorab_tel")) if x) or None),
    ], colWidths=[W * 0.15, W * 0.33, W * 0.2, W * 0.32])
    card.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("LINEBEFORE", (0, 0), (0, -1), 3, ORANGE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LEFTPADDING", (0, 0), (0, -1), 9),
    ]))
    if not data.get("praylist"):
        story += [card, Spacer(1, 8)]

    story += [Paragraph(TUR[tur]["kirish"], st_body), Spacer(1, 8)]

    # --- jadval
    hdr = ["№", "Маҳсулот номи, тури", "Ўлчов\nбирлиги", "Сони", "Нархи", "ҚҚС 12%", "Нархи ҚҚС\nбилан", "Умумий сумма\nҚҚС билан"]
    if not qqs_bor:  # naqd: ҚҚС ustunlari yo'q
        hdr[7] = "Умумий\nсумма"
    tdata = [[Paragraph(h.replace("\n", "<br/>"), st_th) for h in hdr]]
    num = S("num", fontSize=9.5, leading=11.5, alignment=TA_RIGHT)
    cen = S("cen", fontSize=9.5, leading=11.5, alignment=TA_CENTER)
    tot = S("tot", fontName="LS-B", fontSize=9.5, leading=11.5, alignment=TA_RIGHT, textColor=ORANGE)
    for i, r in enumerate(rows, 1):
        nm = [Paragraph(r["nomi"], st_tdname if r["mahsulot"] else S("tdx", fontName="LS-B", fontSize=9.5, leading=11.5, textColor=GREY))]
        if r["izoh"]:
            nm.append(Paragraph(r["izoh"], st_tdsub))
        tdata.append([Paragraph(str(i), cen), nm, Paragraph(r["birlik"], cen), Paragraph(f'{r["soni"]:g}', cen),
                      Paragraph(som(r["sof"]), num), Paragraph(som(r["qqs"]), num),
                      Paragraph(som(r["narx_qqs"]), num), Paragraph(som(r["jami"]), tot)])
    n = len(tdata)
    big_l = S("bl2", fontName="LS-B", fontSize=10.5, leading=13, textColor=NAVY, alignment=TA_RIGHT)
    big_v = S("bv2", fontName="LS-B", fontSize=11, leading=13, textColor=ORANGE, alignment=TA_RIGHT)
    tdata.append(["", Paragraph("Жами", S("j", fontName="LS-B", fontSize=10.5, leading=13, textColor=NAVY)), "",
                  Paragraph(f"{plita_soni:g}", S("jc", fontName="LS-B", fontSize=10, leading=12, alignment=TA_CENTER, textColor=NAVY)),
                  "", "", "", Paragraph(som(jami), big_v)])
    extra = []
    if avans:
        extra = [["", "", "", "", "", Paragraph("Аванс", big_l), "", Paragraph(som(avans), S("av", fontName="LS-B", fontSize=10, leading=12, alignment=TA_RIGHT))],
                 ["", "", "", "", "", Paragraph("Қолдиқ", big_l), "", Paragraph(som(qoldiq), big_v)]]
    tdata += extra
    if data.get("praylist"):  # prays-listda Жами/Аванс qatorlari yo'q
        tdata = tdata[:n]
    cw = [8 * mm, None, 18 * mm, 12 * mm, 21 * mm, 19 * mm, 22 * mm, 26 * mm]
    if not qqs_bor:
        for row in tdata[n + 1:]:  # Аванс/Қолдиқ yorlig'ini "Нархи" ustuniga suramiz
            row[4] = row[5]
        for row in tdata:
            del row[6]
            del row[5]
        cw = [8 * mm, None, 18 * mm, 14 * mm, 30 * mm, 32 * mm]
    cw[1] = W - sum(c for c in cw if c)
    t = Table(tdata, colWidths=cw, repeatRows=1)
    ts = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, n - 1), 0.5, GRID),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LINEABOVE", (0, n), (-1, n), 1.4, NAVY),
        ("BACKGROUND", (0, n), (-1, n), LIGHT),
    ]
    if data.get("praylist"):
        ts = [x for x in ts if x[1] != (0, n)]
    for i in range(1, n):
        if i % 2 == 0:
            ts.append(("BACKGROUND", (0, i), (-1, i), LIGHT))
    if qqs_bor:
        for j in range(len(extra)):
            ts.append(("SPAN", (5, n + 1 + j), (6, n + 1 + j)))
    t.setStyle(TableStyle(ts))
    story += [t, Spacer(1, 8)]

    # --- shartlar
    dia = '<font name="DJ" size="8" color="#E8771E">◆</font>&nbsp;&nbsp;'
    if tur == "plita":
        shartlar = [
            ("Ишлаб чиқариш қуввати:", "кунига 80 тагача плита."),
            ("Автокран:", f"2 та (30–50 тонна), 1 соатда {AVTOKRAN['soatiga_plita']} та плита туширади; "
                          f"камида {AVTOKRAN['min_soat']} соат, 1 соат — {som(AVTOKRAN['soat_narxi'])} сўм."),
            ("Етказиб бериш:", f"шаланда ёки хово билан, 1 ходка масофага қараб {som(PT['narxlar'][0][1])} "
                               f"сўмдан {som(PT['narxlar'][-1][1])} сўмгача{' + ҚҚС' if qqs_bor else ''}."),
            ("Сифат кафолати:", "плиталар давлат стандартлари талабларига мувофиқ ишлаб чиқарилади, ОТК назорати ва паспорт билан."),
            ("Барча нархлар ҚҚС 12% билан кўрсатилган." if qqs_bor else "Нархлар ҚҚСсиз кўрсатилган.", ""),
        ]
    else:
        shartlar = [
            ("Сифат кафолати:", "бетон давлат стандартлари талабларига мувофиқ ишлаб чиқарилади."),
            ("Лаборатория назорати:", "ҳар бир партия учун сифат паспорти берилади."),
            ("Етказиб бериш:", f"бетон ўз миксерларимизда объектгача етказилади. Тўлиқ миксер ({MIKSER['hajm_m3']} м³) учун "
                               f"йўл кираси олинмайди, чала юкли миксерга йўл кира хизмати қўшилади "
                               f"({MIKSER['chala_yaqin_km']} км гача — {som(MIKSER['chala_min'])} сўм{' + ҚҚС' if qqs_bor else ''})."),
            ("Бетон насоси:", "хизмат келишув асосида кўрсатилади."),
            ("Қўшимчалар:", "қишки (совуққа чидамли) ва махсус қўшимчали бетон буюртма асосида тайёрланади."),
            ("Барча нархлар ҚҚС 12% билан кўрсатилган." if qqs_bor else "Нархлар ҚҚСсиз кўрсатилган.", ""),
        ]
    blk = [Paragraph("Шартлар ва имкониятлар", st_h2), Spacer(1, 2)]
    for a, b in shartlar:
        blk.append(Paragraph(f"{dia}<b>{a}</b> {b}", st_bullet))
    story += [KeepTogether(blk), Spacer(1, 7)]

    note = Table([[[Paragraph("ТМБ ёки фойдаланиладиган ресурслар нархи ўзгарганда, юклаб жўнатиладиган маҳсулот "
                              "нархини мос равишда ўзгартириш ҳуқуқини ўзимизда сақлаб қоламиз. Таклиф 5 иш куни давомида амал қилади.", st_note),
                    Spacer(1, 4),
                    Paragraph(f'<b>Харид бўйича саволлар учун:</b> <font name="LS-B" color="#E8771E">{FIRMA["savol_tel"]}</font>', st_bullet)]]],
                 colWidths=[W])
    note.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), LIGHT), ("LINEBEFORE", (0, 0), (0, -1), 3, ORANGE),
                              ("LEFTPADDING", (0, 0), (-1, -1), 10), ("TOPPADDING", (0, 0), (-1, -1), 7),
                              ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    sign = [Paragraph("Ҳурмат билан,", S("hb", fontName="LS-I", fontSize=10.5, leading=13, alignment=TA_RIGHT)),
            Paragraph(FIRMA["nomi"], S("hn", fontName="LS-B", fontSize=12, leading=15, textColor=NAVY, alignment=TA_RIGHT))]
    story += [KeepTogether([note, Spacer(1, 8)] + sign)]

    doc.build(story)
    return dict(jami=jami, avans=avans, qoldiq=qoldiq, miqdor=plita_soni)


if __name__ == "__main__":
    src = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(make_offer(src, sys.argv[2]))
