"""tiklash\\ochirilgan_xabarlar.json dan tiklash\\korish.html sahifasini yasaydi.

Sahifa brauzerda guruh chatiga o'xshab ochiladi: qidiruv, muallif/tur/sana filtrlari,
rasmlar, ovoz va videolar, lokatsiyalar (xaritada ochish). Internet kerak emas.
Ishga tushirish: korish.bat
"""
import json
from pathlib import Path

BASE = Path(__file__).parent
OUT = BASE / "tiklash"

HTML = r"""<!DOCTYPE html>
<html lang="uz"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>INSOF JBI | 2026 — o'chirilgan xabarlar arxivi</title>
<style>
:root{--bg:#e7ebe0;--card:#fff;--ink:#1d2733;--muted:#6b7785;--accent:#1f3a63;--org:#e8771e;--line:#d9dee5}
*{box-sizing:border-box}body{margin:0;font:15px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;background:var(--bg);color:var(--ink)}
header{position:sticky;top:0;z-index:5;background:var(--accent);color:#fff;padding:12px 16px;box-shadow:0 2px 8px rgba(0,0,0,.15)}
header h1{margin:0 0 8px;font-size:17px;font-weight:600}header h1 small{font-weight:400;opacity:.8}
.f{display:flex;flex-wrap:wrap;gap:8px}.f input,.f select{border:0;border-radius:8px;padding:7px 10px;font:inherit;min-width:0}
.f input[type=search]{flex:1 1 220px}.cnt{font-size:13px;opacity:.85;margin-top:6px}
main{max-width:820px;margin:0 auto;padding:12px 12px 80px}
.day{text-align:center;margin:18px 0 8px}.day span{background:rgba(0,0,0,.18);color:#fff;border-radius:12px;padding:3px 12px;font-size:13px}
.m{background:var(--card);border-radius:12px;padding:8px 12px 6px;margin:6px 0;max-width:640px;box-shadow:0 1px 2px rgba(0,0,0,.08)}
.who{font-weight:600;color:var(--org);font-size:14px}.t{white-space:pre-wrap;word-wrap:break-word}
.meta{text-align:right;color:var(--muted);font-size:12px;margin-top:2px}
.m img,.m video{display:block;max-width:100%;max-height:420px;border-radius:8px;margin:4px 0;cursor:zoom-in}
.m audio{width:100%;margin:4px 0}.loc a,.file a{display:inline-block;background:#eef3f8;border-radius:8px;padding:6px 10px;color:var(--accent);text-decoration:none;margin:3px 0}
.badge{display:inline-block;font-size:11px;background:#eef3f8;color:var(--accent);border-radius:6px;padding:1px 6px;margin-left:6px}
.g{border-left:3px solid #4caf50}.more{display:block;margin:16px auto;padding:10px 18px;border:0;border-radius:10px;background:var(--accent);color:#fff;font:inherit;cursor:pointer}
#lb{position:fixed;inset:0;background:rgba(0,0,0,.85);display:none;align-items:center;justify-content:center;z-index:9}#lb img{max-width:95vw;max-height:95vh}
.empty{text-align:center;color:var(--muted);margin:40px 0}
</style></head><body>
<header><h1>INSOF JBI | 2026 <small>— o'chirilgan xabarlar arxivi</small></h1>
<div class="f">
<input id="q" type="search" placeholder="Qidirish: matn, telefon, ism...">
<select id="who"><option value="">Hamma mualliflar</option></select>
<select id="tur"><option value="">Hamma turlar</option></select>
<input id="d1" type="date" title="Sanadan"><input id="d2" type="date" title="Sanagacha">
</div><div class="cnt" id="cnt"></div></header>
<main id="list"></main><div id="lb"><img alt=""></div>
<script id="data" type="application/json">__DATA__</script>
<script>
const D=JSON.parse(document.getElementById('data').textContent);
const TUR={matn:"Matn",rasm:"Rasm",video:"Video",voice:"Ovozli xabar",video_note:"Dumaloq video",fayl:"Fayl",lokatsiya:"Lokatsiya",kontakt:"Kontakt"};
const iso=v=>{const[d,t]=v.split(' ');const[a,b,c]=d.split('.');return `${c}-${b}-${a}`};
D.forEach(r=>{r._d=iso(r.vaqt);r._s=(r.kim+' '+r.matn+' '+r.kontakt).toLowerCase()});
const $=id=>document.getElementById(id);
[...new Set(D.map(r=>r.kim))].sort().forEach(k=>$('who').add(new Option(k,k)));
Object.entries(TUR).forEach(([k,v])=>{if(D.some(r=>r.tur==k))$('tur').add(new Option(v,k))});
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const link=s=>esc(s).replace(/(https?:\/\/[^\s<]+)/g,'<a href="$1" target="_blank" rel="noopener">$1</a>');
let F=[],shown=0;const STEP=150;
function card(r){const p=r.fayl?encodeURI(r.fayl.replace(/\\/g,'/')):'';let b='';
 if(r.tur=='rasm'&&p)b=`<img loading="lazy" src="${p}" alt="">`;
 else if(r.tur=='video'||r.tur=='video_note')b=p?`<video controls preload="none" src="${p}"></video>`:'';
 else if(r.tur=='voice'&&p)b=`<audio controls preload="none" src="${p}"></audio>`;
 else if(r.tur=='fayl'&&p)b=`<div class="file"><a href="${p}" target="_blank">📎 ${esc(p.split('/').pop())}</a></div>`;
 else if(r.tur=='lokatsiya')b=`<div class="loc"><a target="_blank" rel="noopener" href="https://maps.google.com/?q=${r.lat},${r.lon}">📍 Google xarita</a> <a target="_blank" rel="noopener" href="https://yandex.uz/maps/?pt=${r.lon},${r.lat}&z=16">📍 Yandex xarita</a></div>`;
 else if(r.tur=='kontakt')b=`<div class="t">📇 ${esc(r.kontakt)}</div>`;
 const g=(r.guruhga===true||r.guruhga==='True')?'<span class="badge">guruhga qaytarildi</span>':'';
 return `<div class="m${g?' g':''}"><div class="who">${esc(r.kim)}${g}</div>${b}${r.matn?`<div class="t">${link(r.matn)}</div>`:''}<div class="meta">${esc(r.vaqt)} · ${TUR[r.tur]||r.tur}</div></div>`}
function render(reset){if(reset){$('list').innerHTML='';shown=0}
 let h='',last=shown?F[shown-1]._d:null;const end=Math.min(F.length,shown+STEP);
 for(let i=shown;i<end;i++){const r=F[i];if(r._d!==last){h+=`<div class="day"><span>${r.vaqt.split(' ')[0]}</span></div>`;last=r._d}h+=card(r)}
 const old=document.querySelector('.more');if(old)old.remove();
 $('list').insertAdjacentHTML('beforeend',h||(shown?'':'<div class="empty">Hech narsa topilmadi</div>'));shown=end;
 if(shown<F.length)$('list').insertAdjacentHTML('beforeend',`<button class="more" onclick="render()">Yana ko'rsatish (${F.length-shown} ta qoldi)</button>`)}
function apply(){const q=$('q').value.trim().toLowerCase(),w=$('who').value,t=$('tur').value,a=$('d1').value,b=$('d2').value;
 F=D.filter(r=>(!q||r._s.includes(q))&&(!w||r.kim==w)&&(!t||r.tur==t)&&(!a||r._d>=a)&&(!b||r._d<=b));
 F.sort((x,y)=>x._d<y._d?1:x._d>y._d?-1:(y.n-x.n));
 $('cnt').textContent=`${F.length} ta xabar (jami ${D.length}) · yangilari tepada`;render(true)}
['q','who','tur','d1','d2'].forEach(id=>$(id).addEventListener('input',apply));
document.addEventListener('click',e=>{if(e.target.matches('.m img')){$('lb').querySelector('img').src=e.target.src;$('lb').style.display='flex'}else if(e.target.closest('#lb'))$('lb').style.display='none'});
window.addEventListener('scroll',()=>{if(innerHeight+scrollY>document.body.offsetHeight-600&&shown<F.length)render()});
apply();
</script></body></html>"""


def main():
    src = OUT / "ochirilgan_xabarlar.json"
    if not src.exists():
        print("tiklash\\ochirilgan_xabarlar.json topilmadi. Avval tiklash.bat ni ishga tushiring.")
        return
    data = json.loads(src.read_text(encoding="utf-8"))
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    (OUT / "korish.html").write_text(HTML.replace("__DATA__", blob), encoding="utf-8")
    print(f"✅ Tayyor: {OUT / 'korish.html'}  ({len(data)} ta xabar)")
    print("Uni ikki marta bosing — brauzerda ochiladi. Boshqalarga butun tiklash papkasini bering.")


if __name__ == "__main__":
    main()
