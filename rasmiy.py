"""Rasmiy tijorat taklifi (INSOF_Tijorat_taklifi.docx dizayni) — PDF.

O'zgaradigan joylar: №, sana, mijoz (murojaat), tanlangan mahsulotlar, amal qilish muddati, direktor.
Qolgan matn Word shablondagidek.

Sinash:  python rasmiy.py chiqish.pdf
"""
import sys
from datetime import date

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

import taklif  # shriftlarni ro'yxatdan o'tkazadi (LS, LS-B, DJ)
from config import BOSHQA_MAHSULOTLAR, FIRMA, QQS, RASMIY

NAVY = colors.HexColor("#1F3864")
CAT = colors.HexColor("#DCE6F2")
ALT = colors.HexColor("#F5F8FC")
GREY = colors.HexColor("#595959")
GRID = colors.HexColor("#A6A6A6")

OYLAR = ["январ", "феврал", "март", "апрел", "май", "июн", "июл", "август",
         "сентябр", "октябр", "ноябр", "декабр"]


def S(name, **kw):
    base = dict(fontName="LS", fontSize=10, leading=14)
    base.update(kw)
    return ParagraphStyle(name, **base)


def som(x):
    return f"{round(x):,}".replace(",", " ")


def mahsulotlar_royxati():
    """[(kategoriya, nomi, birlik, narx), ...] — bot shu tartib bo'yicha indeks bilan tanlaydi."""
    out = []
    for kat, items in BOSHQA_MAHSULOTLAR.items():
        for nomi, birlik, narx in items:
            out.append((kat, nomi, birlik, narx))
    return out


def make_rasmiy(data: dict, out_path):
    """data: raqam, sana (date|str), mijoz {"nomi"}, tanlangan [indekslar] | None (hammasi), amal_kun."""
    royxat = mahsulotlar_royxati()
    tanlangan = data.get("tanlangan")
    if tanlangan is None:
        tanlangan = list(range(len(royxat)))
    sana = data.get("sana") or date.today()
    if isinstance(sana, str):
        d, m_, y = (int(x) for x in sana.split("."))
        sana = date(y, m_, d)
    amal = data.get("amal_kun") or RASMIY["amal_kun"]

    doc = SimpleDocTemplate(str(out_path), pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                            topMargin=15 * mm, bottomMargin=15 * mm,
                            title=f"Тижорат таклифи № {data.get('raqam', '')}", author=FIRMA["nomi"])
    W = doc.width
    st = []

    # --- sarlavha: lotin | INSOF | kirill
    c = S("c", fontSize=8.5, leading=10.5, alignment=TA_CENTER)
    cb = S("cb", fontName="LS-B", fontSize=8.5, leading=10.5, alignment=TA_CENTER)
    cn = S("cn", fontName="LS-B", fontSize=8.5, leading=10.5, alignment=TA_CENTER, textColor=NAVY)
    chap = [Paragraph("O‘ZBEKISTON RESPUBLIKASI", c), Paragraph("TOSHKENT VILOYATI", cb),
            Paragraph("YANGIYO‘L TUMANI", cb), Paragraph("«INSOF» MAS’ULIYATI CHEKLANGAN JAMIYATI", cn)]
    orta = [Paragraph("INSOF", S("logo", fontName="LS-B", fontSize=26, leading=30, alignment=TA_CENTER, textColor=NAVY)),
            Paragraph("BETON ZAVODI", S("lz", fontSize=7.5, leading=9, alignment=TA_CENTER, textColor=colors.HexColor("#7F7F7F")))]
    ong = [Paragraph("ЎЗБЕКИСТОН РЕСПУБЛИКАСИ", c), Paragraph("ТОШКЕНТ ВИЛОЯТИ", cb),
           Paragraph("ЯНГИЙЎЛ ТУМАНИ", cb), Paragraph("«ИНСОФ» МАСЪУЛИЯТИ ЧЕКЛАНГАН ЖАМИЯТИ", cn)]
    h = Table([[chap, orta, ong]], colWidths=[W * 0.38, W * 0.24, W * 0.38])
    h.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("LINEBELOW", (0, 0), (-1, 0), 1.5, NAVY),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    st.append(h)
    rk = S("rk", fontSize=8, leading=10, alignment=TA_CENTER)
    rekv = Table([[[
        Paragraph(f"<b>Manzil:</b> Toshkent viloyati, Yangiyo‘l tumani, Eski Qovunchi QFY, Qirsadoq mahallasi"
                  f"&nbsp;&nbsp;&nbsp;<b>Tel:</b> {FIRMA['tel']}", rk),
        Paragraph(f"<b>STIR (INN):</b> {FIRMA['stir']}&nbsp;&nbsp;&nbsp;<b>OKED:</b> {FIRMA['ifut']}"
                  f"&nbsp;&nbsp;&nbsp;<b>H/r:</b> {FIRMA['hr']}", rk),
        Paragraph(f"<b>Bank:</b> Toshkent sh., «Aloqabank» ATB Bosh ofisi&nbsp;&nbsp;&nbsp;<b>MFO:</b> {FIRMA['mfo']}", rk),
    ]]], colWidths=[W])
    rekv.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.6, NAVY),
                              ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    st += [rekv, Spacer(1, 10)]

    # --- №, sana, sarlavha
    st.append(Paragraph(f"№ {data.get('raqam', '____')}&nbsp;&nbsp;&nbsp;«{sana.day:02d}» {OYLAR[sana.month - 1]} {sana.year} й.",
                        S("no", fontSize=9, textColor=GREY)))
    st += [Spacer(1, 8),
           Paragraph("ТИЖОРАТ ТАКЛИФИ", S("t", fontName="LS-B", fontSize=16, leading=20, alignment=TA_CENTER, textColor=NAVY)),
           Spacer(1, 10)]
    mijoz = (data.get("mijoz") or {}).get("nomi")
    murojaat = f"Ҳурматли «{mijoz}» раҳбарияти!" if mijoz else "Ҳурматли раҳбарият!"
    st += [Paragraph(murojaat, S("m", fontName="LS-B", fontSize=11, leading=15)), Spacer(1, 6)]
    body = S("body", fontSize=10, leading=15, alignment=TA_JUSTIFY)
    st += [Paragraph("«INSOF» МЧЖ юқори сифатли бетон маҳсулотлари ва темир-бетон буюмларини ишлаб чиқарувчи "
                     "замонавий завод сифатида Сизга ҳамкорлик қилишни таклиф этади. Мақсадимиз – қурилиш соҳасини "
                     "мустаҳкам ва ишончли материаллар билан таъминлаш орқали лойиҳаларингиз муваффақиятига ҳисса қўшиш.",
                     body), Spacer(1, 8)]
    st.append(Paragraph("Биз таклиф қиламиз:", S("h", fontName="LS-B", fontSize=11, leading=15)))
    tick = '<font name="DJ" color="#1F3864">✔</font>&nbsp;&nbsp;'
    bl = S("bl", fontSize=10, leading=13.5, leftIndent=14, firstLineIndent=-12, spaceBefore=1.5)
    for a, b in [("Турли маркадаги бетон", "йирик ва кичик қурилиш объектлари учун, сифат ва мустаҳкамлик кафолати билан."),
                 ("Темир-бетон буюмлари", "йўл қурилиши, саноат ва фуқаролик иншоотлари учун ҳар хил ўлчамларда."),
                 ("Ўз вақтида етказиб бериш", "логистика хизмати орқали тезкор етказиб бериш."),
                 ("Имтиёзли шартлар", "доимий ҳамкорлар учун махсус нархлар ва чегирмалар.")]:
        st.append(Paragraph(f"{tick}<b>{a}</b> – {b}", bl))
    st.append(Spacer(1, 12))

    # --- jadval
    th = S("th", fontName="LS-B", fontSize=8, leading=9.5, alignment=TA_CENTER, textColor=colors.white)
    td = S("td", fontSize=8.5, leading=10.5)
    tc = S("tc", fontSize=8.5, leading=10.5, alignment=TA_CENTER)
    tr = S("tr", fontSize=8.5, leading=10.5, alignment=TA_RIGHT)
    trb = S("trb", fontName="LS-B", fontSize=8.5, leading=10.5, alignment=TA_RIGHT)
    tk = S("tk", fontName="LS-B", fontSize=8.5, leading=10.5, textColor=NAVY)
    rows = [[Paragraph(x, th) for x in ("№", "Маҳсулот номи", "Ўлч. бир.", "Нархи<br/>(ҚҚСсиз), сўм",
                                         "ҚҚС 12%,<br/>сўм", "ҚҚС билан<br/>нархи, сўм")]]
    style = [("BACKGROUND", (0, 0), (-1, 0), NAVY), ("GRID", (0, 0), (-1, -1), 0.4, GRID),
             ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
             ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]
    joriy_kat, n, alt = None, 0, False
    for i in sorted(set(tanlangan)):
        kat, nomi, birlik, narx = royxat[i]
        if kat != joriy_kat:
            rows.append([Paragraph(kat, tk), "", "", "", "", ""])
            r = len(rows) - 1
            style += [("SPAN", (0, r), (-1, r)), ("BACKGROUND", (0, r), (-1, r), CAT)]
            joriy_kat, alt = kat, False
        n += 1
        rows.append([Paragraph(str(n), tc), Paragraph(nomi, td), Paragraph(birlik, tc), Paragraph(som(narx), tr),
                     Paragraph(som(narx * QQS), tr), Paragraph(som(narx * (1 + QQS)), trb)])
        if alt:
            style.append(("BACKGROUND", (0, len(rows) - 1), (-1, len(rows) - 1), ALT))
        alt = not alt
    cw = [10 * mm, None, 18 * mm, 26 * mm, 22 * mm, 27 * mm]
    cw[1] = W - sum(x for x in cw if x)
    t = Table(rows, colWidths=cw, repeatRows=1)
    t.setStyle(TableStyle(style))
    st.append(t)
    st.append(Spacer(1, 3))
    st.append(Paragraph(f"Нархлар ҚҚС (12%) билан ва ҚҚСсиз кўрсатилган. Етказиб бериш нархи алоҳида келишилади. "
                        f"Таклиф эълон қилинган кундан бошлаб {amal} кун амал қилади.",
                        S("note", fontName="LS-I", fontSize=8, leading=10, textColor=GREY)))
    st.append(Spacer(1, 12))

    # --- nega biz, aloqa, imzo
    dot = '<font color="#1F3864">•</font>&nbsp;&nbsp;'
    nega = [Paragraph("Нега айнан биз?", S("h2", fontName="LS-B", fontSize=11, leading=15))]
    for x in ("Янги технологиялар асосида ишлаб чиқариш", "Юқори сифатли хомашё ва экологик тозалик",
              "Рақобатбардош нархлар ва энг мақбул шартлар", "Мижозларга индивидуал ёндашув"):
        nega.append(Paragraph(dot + x, S("nb", fontSize=10, leading=13.5, leftIndent=8)))
    nega += [Spacer(1, 6), Paragraph("Сиз билан ҳамкорлик қилишдан мамнун бўлардик! Ҳар қандай саволлар бўйича "
                                     "биз билан боғланишингизни сўраймиз.", body), Spacer(1, 8),
             Paragraph("<b>Боғланиш учун:</b>", S("b1", fontSize=10, leading=14)),
             Paragraph(f"<b>Тел:</b> {RASMIY['boglanish_tel']}", S("b2", fontSize=10, leading=14)),
             Paragraph(f"<b>Email:</b> {RASMIY['email']}", S("b3", fontSize=10, leading=14)),
             Spacer(1, 14),
             Paragraph("Ҳурмат билан,", S("hb", fontSize=10, leading=14)),
             Paragraph(f"<b>«INSOF» МЧЖ директори</b>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;____________________"
                       f"&nbsp;&nbsp;&nbsp;{RASMIY['direktor'] or 'Ф.И.Ш.'}", S("im", fontSize=10, leading=14)),
             Paragraph("М.Ў.", S("mo", fontSize=8, leading=10, textColor=GREY))]
    st.append(KeepTogether(nega))
    doc.build(st)
    return n


if __name__ == "__main__":
    print(make_rasmiy({"raqam": "0005", "sana": "20.11.2026", "mijoz": {"nomi": "Бунёдкор Қурилиш"}},
                      sys.argv[1] if len(sys.argv) > 1 else "rasmiy_namuna.pdf"))
