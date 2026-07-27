"""
Build the local Planco 3D-roof video player (YouTube-embed based) from a
channel-uploads dump.

Usage:
    python tools/youtube/gen_planco_player.py
    python tools/youtube/gen_planco_player.py --data other.json --out custom.html

Default input is roof_channel_recent.json sitting next to this script.
Writes to ~/.config/media-players/planco-roof-player.html (where /media-players
and the browser expect it) and mirrors a copy to the durable study folder.
"""

import argparse, json, pathlib

HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_DATA = HERE / "roof_channel_recent.json"
DEFAULT_OUT = pathlib.Path.home() / ".config/media-players/planco-roof-player.html"
MIRROR = pathlib.Path.home() / "Study/ryu/3droof/planco-roof-player.html"

ap = argparse.ArgumentParser()
ap.add_argument("--data", default=str(DEFAULT_DATA), help="channel dump JSON")
ap.add_argument("--out", default=str(DEFAULT_OUT), help="player HTML destination")
args = ap.parse_args()

data = json.loads(pathlib.Path(args.data).read_text(encoding="utf-8"))
vids = data["videos"]
cats = sorted(set(v["cat"] for v in vids))
order = {c: i for i, c in enumerate(cats)}
vids.sort(key=lambda v: (order[v["cat"]], v["date"], v["title"]))


def fmt(s):
    s = int(s); h = s // 3600; m = (s % 3600) // 60; sec = s % 60
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m}:{sec:02d}"


js = [{"id": v["id"], "t": v["title"], "c": v["cat"], "d": v["date"],
       "dur": fmt(v["dur"]), "desc": v.get("desc", "")} for v in vids]
total_min = sum(v["dur"] for v in vids) // 60
DATA = json.dumps(js, ensure_ascii=False)

TPL = r'''<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>3D Roof Training - Robbie Cian Planco</title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{background:#0f0f0f;color:#e5e5e5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:14px;display:flex;flex-direction:column;height:100vh;overflow:hidden}
header{padding:10px 16px;background:#111;border-bottom:1px solid #222;flex-shrink:0;display:flex;align-items:center;justify-content:space-between;gap:12px}
header .title{font-size:14px;font-weight:600}
header .title .accent{color:#4ade80}
header .sub{font-size:12px;color:#777}
header .prog{font-size:11px;color:#888;display:flex;align-items:center;gap:8px}
.bar{width:110px;height:6px;background:#222;border-radius:3px;overflow:hidden}
.bar>i{display:block;height:100%;background:#4ade80;width:0}
#menuBtn{display:none;background:none;border:1px solid #333;color:#aaa;border-radius:6px;padding:4px 9px;cursor:pointer;font-size:13px}
.layout{display:flex;flex:1;overflow:hidden}
.sidebar{width:320px;min-width:320px;background:#1a1a1a;border-right:1px solid #222;overflow-y:auto;flex-shrink:0;display:flex;flex-direction:column}
.searchwrap{padding:10px;position:sticky;top:0;background:#1a1a1a;border-bottom:1px solid #222;z-index:2}
#search{width:100%;background:#0f0f0f;border:1px solid #2a2a2a;color:#e5e5e5;border-radius:7px;padding:8px 11px;font-size:13px;outline:none}
#search:focus{border-color:#4ade80}
.cat{border-bottom:1px solid #222}
.cat-h{display:flex;align-items:center;justify-content:space-between;padding:9px 14px;cursor:pointer;user-select:none}
.cat-h:hover{background:#222}
.cat-l{font-size:10px;letter-spacing:1.1px;text-transform:uppercase;color:#6b7280;font-weight:700}
.cat-n{font-size:10px;color:#4ade80;background:#14311f;padding:1px 7px;border-radius:9px}
.cat-t{font-size:10px;color:#444;transition:transform .15s;margin-left:8px}
.cat.open .cat-t{transform:rotate(90deg)}
.cat .items{display:none}.cat.open .items{display:block}
.row{display:flex;gap:10px;align-items:flex-start;padding:8px 14px 8px 16px;cursor:pointer;border-left:3px solid transparent}
.row:hover{background:#222}
.row.active{background:#1f2937;border-left-color:#4ade80}
.row.done .r-t{color:#6b7280}
.r-chk{flex:0 0 16px;width:16px;height:16px;border:1.5px solid #3a3a3a;border-radius:4px;margin-top:2px;font-size:11px;line-height:14px;text-align:center;color:#4ade80;cursor:pointer}
.row.done .r-chk{background:#14311f;border-color:#4ade80}
.r-body{flex:1;min-width:0}
.r-t{font-size:13px;line-height:1.35;color:#e5e5e5}
.r-m{font-size:11px;color:#666;margin-top:2px;display:flex;gap:8px}
.main{flex:1;display:flex;flex-direction:column;overflow:hidden;background:#0f0f0f}
.videowrap{position:relative;width:100%;background:#000;aspect-ratio:16/9;max-height:72vh}
.videowrap iframe{position:absolute;inset:0;width:100%;height:100%;border:0}
.placeholder{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:#555;font-size:14px;text-align:center;padding:20px}
.info{padding:14px 20px;overflow-y:auto}
.info h1{font-size:17px;font-weight:600;margin-bottom:6px}
.info .meta{font-size:12px;color:#777;display:flex;gap:12px;flex-wrap:wrap;margin-bottom:10px}
.info .meta a{color:#4ade80;text-decoration:none}
.info .desc{font-size:13px;color:#9ca3af;line-height:1.5;white-space:pre-wrap;max-width:80ch}
.nav{display:flex;gap:8px;margin-bottom:12px}
.nav button{background:#1a1a1a;border:1px solid #2a2a2a;color:#ddd;border-radius:7px;padding:7px 14px;cursor:pointer;font-size:13px}
.nav button:hover{border-color:#4ade80;color:#4ade80}
.nav button:disabled{opacity:.4;cursor:default}
@media (max-width:760px){
  .layout{flex-direction:column}
  #menuBtn{display:block}
  .sidebar{width:100%;min-width:0;position:absolute;top:49px;bottom:0;left:0;z-index:10;display:none}
  .sidebar.show{display:flex}
  .videowrap{max-height:40vh}
  header .sub{display:none}
}
</style></head><body>
<header>
  <div style="display:flex;align-items:center;gap:10px">
    <button id="menuBtn">&#9776;</button>
    <div class="title"><span class="accent">3D Roof</span> Training <span class="sub">&middot; Robbie Cian Planco</span></div>
  </div>
  <div class="prog"><span id="pcount">0/__N__</span><div class="bar"><i id="pbar"></i></div><span class="sub">__MIN__ min &middot; last 2 mo</span></div>
</header>
<div class="layout">
  <aside class="sidebar" id="sidebar"><div class="searchwrap"><input id="search" placeholder="Search __N__ videos..." autocomplete="off"></div><div id="list"></div></aside>
  <main class="main">
    <div class="videowrap"><div class="placeholder" id="ph">Pick a video from the list to start &#9654;</div><div id="player"></div></div>
    <div class="info">
      <div class="nav"><button id="prev">&larr; Prev</button><button id="next">Next &rarr;</button></div>
      <h1 id="vtitle">3D Roof Training</h1>
      <div class="meta" id="vmeta"></div>
      <div class="desc" id="vdesc"></div>
    </div>
  </main>
</div>
<script>
const DATA=__DATA__;
const WK='planco_roof_watched';
let watched=JSON.parse(localStorage.getItem(WK)||'{}');
let cur=-1;
const listEl=document.getElementById('list');
const cats={};DATA.forEach((v,i)=>{(cats[v.c]=cats[v.c]||[]).push(i)});
function esc(s){return s.replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
function updProg(){const n=DATA.filter(v=>watched[v.id]).length;document.getElementById('pcount').textContent=n+'/'+DATA.length;document.getElementById('pbar').style.width=(100*n/DATA.length)+'%';}
function render(filter){
  filter=(filter||'').toLowerCase();listEl.innerHTML='';
  Object.keys(cats).sort().forEach(c=>{
    const idxs=cats[c].filter(i=>!filter||DATA[i].t.toLowerCase().includes(filter));
    if(!idxs.length)return;
    const sec=document.createElement('div');sec.className='cat open';
    sec.innerHTML='<div class="cat-h"><span class="cat-l">'+c.replace(/^\d+ . /,'')+'</span><span style="display:flex;align-items:center"><span class="cat-n">'+idxs.length+'</span><span class="cat-t">&#9654;</span></span></div>';
    const items=document.createElement('div');items.className='items';
    idxs.forEach(i=>{
      const v=DATA[i];const row=document.createElement('div');
      row.className='row'+(watched[v.id]?' done':'')+(i===cur?' active':'');row.dataset.i=i;
      row.innerHTML='<div class="r-chk">'+(watched[v.id]?'&#10003;':'')+'</div><div class="r-body"><div class="r-t">'+esc(v.t)+'</div><div class="r-m"><span>'+v.dur+'</span><span>'+v.d+'</span></div></div>';
      row.querySelector('.r-chk').addEventListener('click',e=>{e.stopPropagation();toggle(v.id);});
      row.addEventListener('click',()=>play(i));
      items.appendChild(row);
    });
    sec.appendChild(items);
    sec.querySelector('.cat-h').addEventListener('click',()=>sec.classList.toggle('open'));
    listEl.appendChild(sec);
  });
}
function toggle(id){watched[id]=!watched[id];if(!watched[id])delete watched[id];localStorage.setItem(WK,JSON.stringify(watched));render(document.getElementById('search').value);updProg();}
function play(i){
  cur=i;const v=DATA[i];
  document.getElementById('ph').style.display='none';
  document.getElementById('player').innerHTML='<iframe src="https://www.youtube-nocookie.com/embed/'+v.id+'?rel=0&autoplay=1" allow="autoplay; encrypted-media; picture-in-picture" allowfullscreen></iframe>';
  document.getElementById('vtitle').textContent=v.t;
  document.getElementById('vmeta').innerHTML=v.c.replace(/^\d+ . /,'')+' &middot; '+v.dur+' &middot; '+v.d+' &middot; <a href="https://youtu.be/'+v.id+'" target="_blank" rel="noopener">Open on YouTube &#8599;</a>';
  document.getElementById('vdesc').textContent=v.desc||'';
  document.getElementById('prev').disabled=(i<=0);document.getElementById('next').disabled=(i>=DATA.length-1);
  if(!watched[v.id]){watched[v.id]=true;localStorage.setItem(WK,JSON.stringify(watched));updProg();}
  render(document.getElementById('search').value);
  const active=listEl.querySelector('.row.active');if(active)active.scrollIntoView({block:'nearest'});
  if(window.innerWidth<=760)document.getElementById('sidebar').classList.remove('show');
}
document.getElementById('prev').addEventListener('click',()=>{if(cur>0)play(cur-1)});
document.getElementById('next').addEventListener('click',()=>{if(cur<DATA.length-1)play(cur+1)});
document.getElementById('search').addEventListener('input',e=>render(e.target.value));
document.getElementById('menuBtn').addEventListener('click',()=>document.getElementById('sidebar').classList.toggle('show'));
document.addEventListener('keydown',e=>{if(e.target.tagName==='INPUT')return;if(e.key==='ArrowLeft'&&cur>0)play(cur-1);if(e.key==='ArrowRight'&&cur<DATA.length-1)play(cur+1);});
render('');updProg();
</script></body></html>'''

out = TPL.replace("__DATA__", DATA).replace("__N__", str(len(js))).replace("__MIN__", str(total_min))
dest = pathlib.Path(args.out)
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(out, encoding="utf-8")
if MIRROR.parent.exists():
    MIRROR.write_text(out, encoding="utf-8")
print("wrote:", dest)
print("size: %.1f KB" % (len(out.encode()) / 1024))
print("videos:", len(js), "| total min:", total_min)
print("categories:", cats)
