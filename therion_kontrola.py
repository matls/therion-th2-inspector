#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lokální kontrola Therion TH2. Spuštění: py therion_kontrola.py "D:\\Jeskyne"""
import argparse, json, math, os, re, shutil, threading, webbrowser, hashlib
from datetime import datetime
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse
from kontrola_th2_smycek_v6 import flatten, detect, dist

SKIP={'data','_therion_zalohy'}
CLOSURE_TYPES={'chimney','pit','border','rock-border'}
ROOT=None
CACHE={}
TOL=0.15
NEAR=1.0

def bezier_loop_proposal(points):
    """Suggest a minimally blended, self-intersection-free cubic with fixed endpoints.

    Blend handles towards the straight chord. This is a geometric proposal, not
    a guarantee of matching the original hand-drawn wall.
    """
    p0, c1, c2, p3 = points
    chord1=[p0[k]+(p3[k]-p0[k])/3 for k in range(2)]
    chord2=[p0[k]+2*(p3[k]-p0[k])/3 for k in range(2)]
    if dist(p0,p3)<1e-8:
        return None  # closed/collapsed cubic: handled as duplicate, not a loop fix
    for step in range(1,21):
        alpha=step/20
        h1=[(1-alpha)*c1[k]+alpha*chord1[k] for k in range(2)]
        h2=[(1-alpha)*c2[k]+alpha*chord2[k] for k in range(2)]
        proposal=[list(p0),h1,h2,list(p3)]
        if not detect(flatten(tuple(proposal),TOL)):
            # Margin of a full extra step avoids numerical grazing.
            if step<20:
                alpha=min(1,(step+1)/20)
                h1=[(1-alpha)*c1[k]+alpha*chord1[k] for k in range(2)]
                h2=[(1-alpha)*c2[k]+alpha*chord2[k] for k in range(2)]
                proposal=[list(p0),h1,h2,list(p3)]
            if detect(flatten(tuple(proposal),TOL)):
                return None
            return proposal
    return None

def parse_file(path):
    raw=path.read_bytes(); encoding='utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
    try: text=raw.decode(encoding)
    except UnicodeDecodeError: encoding='cp1250';text=raw.decode(encoding)
    lines=text.splitlines(keepends=True)
    scrap=''; scrap_index=0; current=None; shapes=[]; findings=[]
    def endline():
        if current is None:return
        nodes=current['nodes'];seen={}
        for i,node in enumerate(nodes):
            key=tuple(node['p'])
            if key in seen:
                first=seen[key]
                if current['close'] and first==0 and i==len(nodes)-1: continue
                prev=nodes[i-1] if i else None
                # A straight endpoint duplicate is a zero-length segment even if
                # the preceding point was curved. A repeated-end cubic can be
                # removed only if its entire loop is small.
                safe=(i>0 and first==i-1 and prev is not None and
                      (node['kind']=='straight' or
                       (node['kind']=='bezier' and
                        max(dist(node['p'],cp) for cp in current['segments'][i-1]['points'][1:3])<=30)))
                reason=('Překrývající se přímý bod (nulový úsek)' if safe and node['kind']=='straight'
                        else 'Malá Bézierova smyčka se shodnými konci' if safe
                        else 'Větší Bézierova smyčka nebo nesousedící duplicitní body')
                add(current,'dup',node['row'],key,first_row=nodes[first]['row'],safe=safe,reason=reason)
            else: seen[key]=i
        if current['type'].split(':')[0] in CLOSURE_TYPES and len(nodes)>=2:
            a,b=nodes[0]['p'],nodes[-1]['p']
            if not current['close'] and a==b:
                add(current,'open',current['start'],a,safe=True)
        for seg in current['segments']:
            if seg['kind']=='bezier':
                poly=flatten(tuple(seg['points']),TOL)
                for hit in detect(poly):
                    proposal=bezier_loop_proposal(seg['points'])
                    add(current,'loop',seg['row'],hit,safe=bool(proposal),
                        reason='Návrh úpravy řídicích bodů – schválit po vizuální kontrole' if proposal else 'Automatický návrh nebyl nalezen',
                        proposed_points=proposal)
    def add(shape,kind,row,point,first_row=None,safe=False,reason="",proposed_points=None):
        index=len(findings)
        findings.append({'id':hashlib.sha1(f'{path}:{shape["start"]}:{kind}:{row}:{first_row}:{round(point[0],4)}:{round(point[1],4)}'.encode()).hexdigest()[:16],
                         'file':str(path.relative_to(ROOT)),'scrap':shape['scrap'],'type':shape['type'],'line_id':shape['id'],
                         'start':shape['start'],'row':row,'first_row':first_row,'kind':kind,'x':round(point[0],4),'y':round(point[1],4),
                         'safe':safe,'reason':reason,'proposed_points':proposed_points,'shape_key':shape['key'],
                         'close_setting':shape['close_setting'],'endpoints_equal':len(shape['nodes'])>1 and shape['nodes'][0]['p']==shape['nodes'][-1]['p'],
                         'first_point':shape['nodes'][0]['p'] if shape['nodes'] else None,'last_point':shape['nodes'][-1]['p'] if shape['nodes'] else None})
    for lineno,rawline in enumerate(lines,1):
        s=rawline.split('#',1)[0].strip();parts=s.split()
        if not parts:continue
        cmd=parts[0]
        if cmd=='line':
            endline()
            opts=parts[2:];line_id=opts[opts.index('-id')+1] if '-id' in opts and opts.index('-id')+1<len(opts) else ''
            close=any(opts[i:i+2]==['-close','on'] for i in range(len(opts)-1))
            current={'key':f'{path.relative_to(ROOT)}:{lineno}','start':lineno,'scrap':scrap,'scrap_index':scrap_index,'type':parts[1] if len(parts)>1 else '', 'id':line_id,'close':close,'close_setting':'on' if close else ('off' if '-close' in opts and 'off' in opts else 'auto'), 'nodes':[],'segments':[],'end':None,'header':s,'simple':True}
            shapes.append(current)
        elif cmd=='endline':current['end']=lineno;endline();current=None
        elif current is not None:
            if cmd=='-close' and len(parts)>1:current['close']=parts[1]=='on';current['close_setting']=parts[1];continue
            if cmd=='-id' and len(parts)>1:current['id']=parts[1];continue
            if len(parts) not in (2,6):
                current['simple']=False
                continue
            try: nums=[float(n) for n in parts]
            except ValueError:continue
            p=[nums[-2],nums[-1]];kind='bezier' if len(nums)==6 else 'straight'
            if current['nodes']:
                prev=current['nodes'][-1]['p']; pts=[prev,p] if kind=='straight' else [prev,nums[:2],nums[2:4],p]
                current['segments'].append({'kind':kind,'points':pts,'row':lineno})
            current['nodes'].append({'p':p,'row':lineno,'kind':kind})
        elif cmd=='scrap':scrap=parts[1] if len(parts)>1 else '';scrap_index+=1
        elif cmd=='endscrap':scrap=''
    endline()
    findings.extend(find_joins(path,shapes,lines))
    findings.extend(find_chains(path,findings,shapes))
    return {'shapes':shapes,'findings':findings,'lines':lines,'encoding':encoding,'hash':hashlib.sha256(raw).hexdigest()}

def find_joins(path,shapes,source_lines):
    """Detect end->start continuation (regardless of position in source file).

    Automatic merge is allowed only for strict coordinate-only lines whose
    headers match, with no IDs/reverse-direction modifications or branches.
    Other near/exact matches remain advisory.
    """
    result=[]
    byscrap={}
    for sh in shapes:
        if sh['nodes'] and sh['end'] is not None:
            byscrap.setdefault(sh['scrap'],[]).append(sh)
    for scrap,items in byscrap.items():
        degree={}
        for sh in items:
            for node in sh['nodes']:
                key=tuple(node['p']);degree[key]=degree.get(key,0)+1
        for a in items:
            if len(a['nodes'])<2 or a['close'] or a['nodes'][0]['p']==a['nodes'][-1]['p']:continue
            for b in items:
                if a is b or len(b['nodes'])<2 or b['close'] or b['nodes'][0]['p']==b['nodes'][-1]['p']:continue
                if a['type']!=b['type'] or a['scrap_index']!=b['scrap_index']:continue
                opts_equal=a['header'].split()==b['header'].split()
                if not opts_equal:continue
                end=a['nodes'][-1]['p'];start=b['nodes'][0]['p'];gap=dist(end,start)
                if gap>NEAR:continue
                exact=(end==start)
                # All internal line directives / comments are handled conservatively.
                # To avoid transferring an inherited smooth/subtype state, only
                # coordinate-only bodies and plain endline are eligible.
                safe=(exact and degree.get(tuple(end),0)==2
                      and a['simple'] and b['simple'] and not a['id'] and not b['id']
                      and a['end'] is not None and b['end'] is not None
                      and not a['header'].split('#')[0].split()[2:].count('-reverse')
                      and all(sh['end']-sh['start']-1==len(sh['nodes']) and
                          all('#' not in row and len(row.split()) in (2,6)
                              for row in source_lines[sh['start']:sh['end']-1])
                          for sh in (a,b)))
                reason=('Identické parametry, bez ID a větvení, stejný směr' if safe else
                        'Nutná ruční kontrola (větvení, direktivy, ID nebo nejasné parametry)')
                uid=hashlib.sha1(f'{path}:{a["start"]}:{b["start"]}:join'.encode()).hexdigest()[:16]
                result.append({'id':uid,'file':str(path.relative_to(ROOT)),'scrap':scrap,
                    'type':a['type'],'line_id':a['id'] or b['id'],'start':a['start'],
                    'row':b['start'],'first_row':a['start'],'kind':'merge' if exact else 'near',
                    'x':round((end[0]+start[0])/2,4),'y':round((end[1]+start[1])/2,4),
                    'gap':round(gap,6),'safe':safe,'reason':reason,'shape_key':a['key'],'other_key':b['key'],
                    'close_setting':a['close_setting'],'endpoints_equal':exact,
                    'first_point':end,'last_point':start})
    return result

def find_chains(path, findings, shapes):
    """Maximal unbranched, noncyclic chains from individually safe, directed joins."""
    edges=[f for f in findings if f['kind']=='merge' and f['safe']]
    successors={}; predecessors={}
    for f in edges:
        successors.setdefault(f['shape_key'],[]).append(f)
        predecessors.setdefault(f['other_key'],[]).append(f)
    result=[]; visited=set()
    bykey={sh['key']:sh for sh in shapes}
    for edge in edges:
        start=edge['shape_key']
        if start in predecessors or start in visited: continue
        nodes=[start]; at=start; included=[]
        while len(successors.get(at,[]))==1:
            e=successors[at][0]; nxt=e['other_key']
            if len(predecessors.get(nxt,[]))!=1 or nxt in nodes: break
            included.append(e); nodes.append(nxt); at=nxt
        visited.update(nodes)
        if len(nodes)<3: continue
        members=[bykey[k] for k in nodes]
        if len({(m['scrap_index'],m['header']) for m in members})!=1: continue
        uid=hashlib.sha1(f'{path}:chain:{": ".join(nodes)}'.encode()).hexdigest()[:16]
        result.append({'id':uid,'file':str(path.relative_to(ROOT)),
            'scrap':members[0]['scrap'],'type':members[0]['type'],'line_id':'',
            'start':members[0]['start'],'row':members[-1]['start'],
            'first_row':members[0]['start'],'kind':'chain',
            'x':included[0]['x'],'y':included[0]['y'],'gap':0,'safe':True,
            'reason':f'Celý řetězec {len(nodes)} čar; pořadí řádků: '+', '.join(str(m['start']) for m in members),
            'shape_key':nodes[0], 'other_key':nodes[-1], 'chain_keys':nodes,
            'close_setting':members[0]['close_setting'],'endpoints_equal':True,
            'first_point':members[0]['nodes'][-1]['p'],
            'last_point':members[-1]['nodes'][0]['p']})
    return result

def scan():
    CACHE.clear();found=[];errors=[];files=0
    for base,dirs,names in os.walk(ROOT):
        dirs[:]=[d for d in dirs if d.lower() not in SKIP]
        for name in sorted(names):
            if not name.lower().endswith('.th2'):continue
            p=Path(base)/name;files+=1
            try:
                obj=parse_file(p);CACHE[str(p.relative_to(ROOT))]=obj;found+=obj['findings']
            except Exception as exc:errors.append(f'{p.relative_to(ROOT)}: {exc}')
    return {'files':files,'findings':found,'errors':errors}

def preview(file,shape_key,x,y,scope,other_key=None,chain_keys=None):
    obj=CACHE[file];shapes=[s for s in obj['shapes'] if s['scrap']==next((q['scrap'] for q in obj['shapes'] if q['key']==shape_key),'')]
    if scope=='line':shapes=[s for s in shapes if s['key'] in (chain_keys or [shape_key,other_key])]
    out=[]
    for s in shapes:
        segs=[]
        for seg in s['segments']:
            pts=seg['points'];flat=flatten(tuple(pts),0.8) if seg['kind']=='bezier' else pts
            if scope not in ('all','line') and not any(abs(p[0]-x)<300 and abs(p[1]-y)<300 for p in flat):continue
            segs.append({'points':flat,'handles':pts if s['key']==shape_key and seg['kind']=='bezier' else None})
        if segs:out.append({'key':s['key'],'segments':segs,'selected':s['key']==shape_key,'other':s['key']==other_key or s['key'] in (chain_keys or [])[1:],'type':s['type'], 'endpoints':[s['nodes'][0]['p'],s['nodes'][-1]['p']] if s['nodes'] else [],'chain_index':(chain_keys.index(s['key']) if chain_keys and s['key'] in chain_keys else -1)})
    return out

HTML=r'''<!doctype html><html lang="cs"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Therion – kontrola TH2</title><style>
:root{font-family:system-ui,Segoe UI,sans-serif;color:#182536;background:#f4f6f9}*{box-sizing:border-box}body{margin:0}header{background:#17283d;color:white;padding:16px 24px}header h2{margin:0 0 6px}header small{color:#c8d4e3}main{display:grid;grid-template-columns:minmax(280px,380px) 1fr;height:calc(100vh - 103px)}aside{overflow:auto;border-right:1px solid #ccd4df;background:white;padding:12px}section{min-width:0;overflow:auto;padding:16px}button,select,input{font:inherit}button{border:1px solid #c2ccd8;background:white;border-radius:7px;padding:7px 11px;cursor:pointer}button:hover{background:#e8f0fa}button.primary{background:#1463a0;color:white;border-color:#1463a0}button.danger{background:#9b3535;color:white}button:disabled{opacity:.45;cursor:default}.entry{border:1px solid #d6dfe8;padding:10px;border-radius:9px;margin:8px 0;cursor:pointer}.entry.active{border:2px solid #1870b9;background:#edf6ff}.entry strong{display:block}.meta{font-size:12px;color:#617082;overflow-wrap:anywhere}.pill{display:inline-block;padding:2px 7px;background:#e7edf5;border-radius:6px;font-size:12px}.warn{color:#a32f2f}.good{color:#137a50}#canvas{width:100%;height:min(62vh,610px);border:1px solid #cad4df;background:white;border-radius:10px;touch-action:none;cursor:grab}.toolbar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:10px 0}.panel{background:white;border:1px solid #d7dfe9;border-radius:10px;padding:14px;margin-bottom:12px}.panel p{margin:6px 0}.spacer{flex:1}#status{white-space:pre-wrap;font-size:13px}.hidden{display:none}label{cursor:pointer}@media(max-width:760px){main{display:block;height:auto}aside{max-height:35vh}#canvas{height:45vh}}</style></head><body>
<header><h2>Therion · kontrola kresby</h2><small id="root"></small></header><main><aside><div class="toolbar"><button onclick="rescan()">Znovu prohledat</button><span id="count"></span><small id="repairCount" class="meta"></small></div><input id="filter" placeholder="Hledat soubor, scrap, ID…" style="width:100%;padding:8px" oninput="renderList()"><div class="toolbar"><select id="kind" onchange="renderList()"><option value="">Všechny nálezy</option><option value="dup">Duplicitní body</option><option value="loop">Smyčky</option><option value="open">Chybějící uzavření</option><option value="merge">Přesné návaznosti (dvojice)</option><option value="chain">Celé řetězce</option><option value="near">Blízké konce</option></select><select id="repairFilter" onchange="renderList()"><option value="">Všechny možnosti</option><option value="safe">Lze opravit</option><option value="review">Pouze kontrola</option></select><select id="decisionFilter" onchange="renderList()"><option value="">Všechna rozhodnutí</option><option value="fix">Ke změně</option><option value="later">Neprohlédnuté</option><option value="skip">Přeskočené</option></select></div><div id="list"></div></aside><section><div class="panel"><strong id="heading">Vyber nález vlevo</strong><p class="meta" id="detail"></p><div class="toolbar"><label><input type="checkbox" id="surround" checked onchange="draw()"> Okolní čáry</label><button onclick="zoom(0.6)">+ Přiblížit</button><button onclick="zoom(1.6)">− Oddálit</button><button onclick="resetView()">Vycentrovat</button><button onclick="fullScrap()">Celý scrap</button></div><svg id="canvas" viewBox="0 0 900 550" xmlns="http://www.w3.org/2000/svg"></svg><p class="meta">Červená: původní čára · zelená přerušovaná: návrh opravy Bézierovy smyčky · tyrkysová přerušovaná: navržené uzavření · šedá: okolí · oranžová: táhla Bézierových křivek · červený kroužek: nález. Posouvání tažením myši, zoom kolečkem.</p><div class="toolbar"><button onclick="choose('skip')">Přeskočit</button><button onclick="choose('later')">Později</button><button id="fix" class="primary" onclick="choose('fix')">Schválit odstranění bodu</button><span id="decision"></span></div></div><div class="panel"><strong>Hromadné opravy</strong><p class="meta">Uzavření je povoleno jen při přesné shodě prvního a posledního bodu. Zkontroluj náhled před schválením. U sousedních shodných bodů lze odstranit i celý Bézierův segment tvořící smyčku. Její tvar se tím změní; schvaluj jednotlivě.</p><div class="toolbar"><button onclick="exportCsv()">Export CSV</button><button onclick="showPlan()">Zobrazit plán změn</button><button class="danger" onclick="apply()">Zálohovat a provést schválené změny</button></div><div id="status"></div></div></section></main>
<script>
let data=[], decisions={}, selected=null, shapes=[], view=null, full=false, dragging=null;
const $=id=>document.getElementById(id), esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function api(path,body){let r=await fetch(path,{method:body?'POST':'GET',headers:{'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined});let v=await r.json();if(!r.ok)throw Error(v.error||r.status);return v}
async function init(){let r=await api('/api/scan');data=r.findings;$('root').textContent=r.root+' · '+r.files+' souborů';$('count').textContent=data.length+' nálezů';$('repairCount').textContent=data.filter(f=>f.safe).length+' opravitelných / '+data.filter(f=>!f.safe).length+' ke kontrole';try{decisions=JSON.parse(localStorage.getItem('therion_decisions_'+r.root)||'{}')}catch(e){}for(let f of data){if(!f.safe)delete decisions[f.id]}renderList();if(data.length)selectItem(data[0].id);if(r.errors.length)$('status').textContent=r.errors.join('\n')}
function save(){localStorage.setItem('therion_decisions_'+$('root').textContent.split(' · ')[0],JSON.stringify(decisions))}
function affected(f){return f.kind==='chain'?f.chain_keys:(f.kind==='merge'?[f.shape_key,f.other_key]:[f.shape_key])}
function conflicts(f){if(!f.safe)return [];let mine=affected(f);return data.filter(o=>o.id!==f.id&&decisions[o.id]==='fix'&&(['merge','chain'].includes(f.kind)||['merge','chain'].includes(o.kind))&&affected(o).some(k=>mine.includes(k))).map(o=>o)}
function conflictLabel(f){let c=conflicts(f);return c.length?'Konflikt se schváleným návrhem: '+c.map(o=>o.kind==='chain'?'řetězec '+o.start:o.kind+' ř. '+o.start).join(', '):''}
function renderList(){let q=$('filter').value.toLowerCase(),k=$('kind').value,d=$('decisionFilter').value,repair=$('repairFilter').value;let arr=data.filter(f=>(!k||f.kind===k)&&(!repair||(repair==='safe'?f.safe:!f.safe))&&(!d||(decisions[f.id]||'later')===d)&&(!q||[f.file,f.scrap,f.line_id,f.type,f.row].join(' ').toLowerCase().includes(q)));$('list').innerHTML=arr.map(f=>`<div class="entry ${selected===f.id?'active':''}" onclick="selectItem('${f.id}')"><strong>${f.kind==='dup'?'Duplicitní bod':f.kind==='open'?'Chybí uzavření':f.kind==='merge'?'Sloučení čar':f.kind==='chain'?'Sloučení řetězce':f.kind==='near'?'Blízké konce':'Smyčka'} <span class="pill">${esc(decisions[f.id]||'později')}</span></strong><div class="meta">${esc(f.file)}<br>${esc(f.scrap)} · ${esc(f.type)} ${esc(f.line_id)} · ř. ${f.row}${f.first_row?' / '+f.first_row:''}</div><small class="${f.safe&&!conflicts(f).length?'good':'warn'}">${f.kind==='open'?'Možnost uzavřít':f.kind==='near'?'Odchylka '+f.gap+' (jen kontrola)':f.kind==='chain'?'Řetězec '+f.chain_keys.length+' čar':f.kind==='merge'?(f.safe?'Lze schválit sloučení':'Pouze kontrola sloučení'):f.safe?'Lze schválit':'Pouze kontrola'}${conflictLabel(f)?'<br>'+esc(conflictLabel(f)):''}</small></div>`).join('')||'<p>Žádné nálezy.</p>'}
async function selectItem(id){selected=id;let f=data.find(x=>x.id===id);if(!f)return;full=false;$('heading').textContent=(f.kind==='dup'?'Duplicitní bod':f.kind==='open'?'Chybí uzavření':f.kind==='merge'?'Přesná návaznost':f.kind==='chain'?'Celý řetězec':f.kind==='near'?'Blízké konce':'Bézierova smyčka')+' · '+f.type+' '+(f.line_id||'bez ID');$('detail').textContent=(f.kind==='chain'?'Řetězec '+f.chain_keys.length+' čar · ':'')+f.file+' · scrap '+f.scrap+' · line řádek '+f.start+' · nález řádek '+f.row+(f.first_row?' / '+f.first_row:'')+' · XY '+f.x+', '+f.y+' · -close '+f.close_setting+' · '+(f.reason||'')+' · koncové body '+(f.endpoints_equal?'shodné':'rozdílné')+(f.gap!==undefined?' · odchylka '+f.gap:'');$('fix').disabled=!f.safe||conflicts(f).length>0;$('fix').textContent=f.kind==='open'?'Schválit uzavření (-close on)':f.kind==='merge'?'Schválit sloučení':f.kind==='chain'?'Schválit celý řetězec ('+f.chain_keys.length+' čar)':f.kind==='loop'?'Schválit navrženou opravu smyčky':'Schválit odstranění bodu / smyčky';$('decision').textContent='Rozhodnutí: '+(decisions[id]||'později')+(conflictLabel(f)?' · '+conflictLabel(f):'');view=null;await draw();renderList()}
async function draw(){let f=data.find(x=>x.id===selected);if(!f)return;shapes=await api('/api/preview',{id:f.id,scope:full?'all':f.kind==='chain'?'line':$('surround').checked?'near':'line'});if(!view){if(f.kind==='chain'&&shapes.length){let pts=shapes.flatMap(x=>x.segments.flatMap(z=>z.points));if(pts.length){let xs=pts.map(p=>p[0]),ys=pts.map(p=>p[1]);let x=Math.min(...xs),y=Math.min(...ys),w=Math.max(30,Math.max(...xs)-x),h=Math.max(20,Math.max(...ys)-y);view={x:x-w*.15,y:y-h*.15,w:w*1.3,h:h*1.3}}else resetView()}else resetView()}renderSvg()}
function resetView(){let f=data.find(x=>x.id===selected);if(!f)return;view={x:f.x-160,y:f.y-98,w:320,h:196};renderSvg()}
function fullScrap(){full=true;view=null;api('/api/preview',{id:selected,scope:'all'}).then(s=>{shapes=s;let pts=s.flatMap(x=>x.segments.flatMap(z=>z.points));if(pts.length){let xs=pts.map(p=>p[0]),ys=pts.map(p=>p[1]),xmin=Math.min(...xs),xmax=Math.max(...xs),ymin=Math.min(...ys),ymax=Math.max(...ys);let w=Math.max(30,xmax-xmin),h=Math.max(20,ymax-ymin);view={x:xmin-w*.08,y:ymin-h*.08,w:w*1.16,h:h*1.16}}renderSvg()})}
function renderSvg(){if(!view)return;let f=data.find(x=>x.id===selected);let svg=$('canvas');let {x,y,w,h}=view;let aspect=900/550;if(w/h>aspect){let nh=w/aspect;y-=(nh-h)/2;h=nh}else{let nw=h*aspect;x-=(nw-w)/2;w=nw}view={x,y,w,h};let xx=p=>(900*(p[0]-x)/w).toFixed(2),yy=p=>(550-550*(p[1]-y)/h).toFixed(2);let out='';for(let s of shapes){for(let seg of s.segments){let p=seg.points;if(p.length<2)continue;out+=`<polyline points="${p.map(q=>xx(q)+','+yy(q)).join(' ')}" fill="none" stroke="${f.kind==='chain'&&s.chain_index>=0?['#d63135','#1485c5','#16a085','#c08427','#8b5cf6'][s.chain_index%5]:s.selected?'#d63135':s.other?'#1485c5':'#a8b0b9'}" stroke-width="${s.selected||s.other?3:1.4}" stroke-linejoin="round"/>`;if(s.selected&&seg.handles){let c=seg.handles;for(let pair of [[c[0],c[1]],[c[2],c[3]]])out+=`<line x1="${xx(pair[0])}" y1="${yy(pair[0])}" x2="${xx(pair[1])}" y2="${yy(pair[1])}" stroke="#dc9b32" stroke-width="1" stroke-dasharray="4 3"/>`;for(let q of [c[1],c[2]])out+=`<circle cx="${xx(q)}" cy="${yy(q)}" r="3" fill="#dc9b32"/>`}}}if(f.kind==='loop' && f.proposed_points){let p=f.proposed_points;let ps=[];for(let j=0;j<=80;j++){let t=j/80,u=1-t;ps.push([u*u*u*p[0][0]+3*u*u*t*p[1][0]+3*u*t*t*p[2][0]+t*t*t*p[3][0],u*u*u*p[0][1]+3*u*u*t*p[1][1]+3*u*t*t*p[2][1]+t*t*t*p[3][1]])}out+=`<polyline points="${ps.map(q=>xx(q)+','+yy(q)).join(' ')}" fill="none" stroke="#0e9b65" stroke-width="3.5" stroke-dasharray="7 3"/>`;}if(f.kind==='near'){let a=f.first_point,b=f.last_point;out+=`<line x1="${xx(a)}" y1="${yy(a)}" x2="${xx(b)}" y2="${yy(b)}" stroke="#e7a02d" stroke-width="3" stroke-dasharray="4 3"/>`}if(f.kind==='open'){let sh=shapes.find(q=>q.selected);if(sh&&sh.endpoints.length===2){let a=sh.endpoints[0],b=sh.endpoints[1];out+=`<line x1="${xx(a)}" y1="${yy(a)}" x2="${xx(b)}" y2="${yy(b)}" stroke="#0d9488" stroke-width="3" stroke-dasharray="8 5"/>`}}out+=`<circle cx="${xx([f.x,f.y])}" cy="${yy([f.x,f.y])}" r="10" fill="none" stroke="#d63135" stroke-width="2.5"/><circle cx="${xx([f.x,f.y])}" cy="${yy([f.x,f.y])}" r="2.5" fill="#d63135"/>`;svg.innerHTML=out}
function zoom(f){if(!view)return;let cx=view.x+view.w/2,cy=view.y+view.h/2;view={x:cx-view.w*f/2,y:cy-view.h*f/2,w:view.w*f,h:view.h*f};renderSvg()}
$('canvas').addEventListener('wheel',e=>{e.preventDefault();zoom(e.deltaY<0?.8:1.25)},{passive:false});$('canvas').addEventListener('pointerdown',e=>{dragging={x:e.clientX,y:e.clientY,v:{...view}};$('canvas').setPointerCapture(e.pointerId)});$('canvas').addEventListener('pointermove',e=>{if(!dragging)return;let r=$('canvas').getBoundingClientRect();view={...dragging.v,x:dragging.v.x-(e.clientX-dragging.x)*dragging.v.w/r.width,y:dragging.v.y+(e.clientY-dragging.y)*dragging.v.h/r.height};renderSvg()});$('canvas').addEventListener('pointerup',()=>dragging=null);
function choose(v){if(!selected)return;let f=data.find(x=>x.id===selected);if(v==='fix'&&(!f.safe||conflicts(f).length)){ $('status').textContent=conflictLabel(f)||'Oprava není povolena';return;}decisions[selected]=v;save();$('decision').textContent='Rozhodnutí: '+v;renderList();if(v==='fix')selectItem(selected)}
function selectedFixes(){return data.filter(f=>f.safe&&decisions[f.id]==='fix').map(f=>f.id)}
function showPlan(){let a=data.filter(f=>selectedFixes().includes(f.id));$('status').textContent=a.length?`Připraveno ${a.length} schválených změn v ${new Set(a.map(f=>f.file)).size} souborech:\n`+a.map(f=>f.file+' · ř. '+f.row).join('\n'):'Žádné schválené bezpečné opravy.'}
async function apply(){let ids=selectedFixes();if(!ids.length){$('status').textContent='Žádné schválené bezpečné opravy.';return}if(!confirm(`Zálohovat a změnit ${ids.length} nálezů? Změny se provedou přímo v původních souborech.`))return;try{let r=await api('/api/apply',{ids});$('status').textContent=JSON.stringify(r,null,2);decisions={};save();await init()}catch(e){$('status').textContent='CHYBA: '+e.message}}
function exportCsv(){let h=['soubor','scrap','typ','id','radek','prvni_radek','problem','close','shodne_konce','odchylka','druha_cara','x','y','rozhodnuti'];let rows=data.map(f=>[f.file,f.scrap,f.type,f.line_id,f.row,f.first_row||'',f.kind,f.close_setting,f.endpoints_equal,f.gap??'',f.other_key??'',f.x,f.y,decisions[f.id]||'later']);let csv=[h,...rows].map(r=>r.map(v=>'"'+String(v).replaceAll('"','""')+'"').join(';')).join('\r\n');let a=document.createElement('a');a.href=URL.createObjectURL(new Blob(['\ufeff'+csv],{type:'text/csv;charset=utf-8'}));a.download='therion_nalezy.csv';a.click();URL.revokeObjectURL(a.href)}
async function rescan(){if(!confirm('Znovu načíst soubory? Rozhodnutí zůstanou uložená, ale změněné nálezy mohou mít nové identifikátory.'))return;await init()}
init().catch(e=>$('status').textContent=e.message);
</script></body></html>'''

class Handler(BaseHTTPRequestHandler):
    def respond(self,code,obj):
        b=json.dumps(obj,ensure_ascii=False).encode('utf-8');self.send_response(code);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
    def do_GET(self):
        if urlparse(self.path).path=='/':
            b=HTML.encode();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
        elif self.path=='/api/scan':
            r=scan();r['root']=str(ROOT);self.respond(200,r)
        else:self.respond(404,{'error':'Nenalezeno'})
    def do_POST(self):
        try:
            size=int(self.headers.get('Content-Length',0));assert 0<size<2000000
            req=json.loads(self.rfile.read(size));route=urlparse(self.path).path
            if route=='/api/preview':
                f=next((f for o in CACHE.values() for f in o['findings'] if f['id']==req['id']),None)
                if not f:raise ValueError('Nález nebyl nalezen')
                self.respond(200,preview(f['file'],f['shape_key'],f['x'],f['y'],req.get('scope','near'),f.get('other_key'),f.get('chain_keys')))
            elif route=='/api/apply':self.respond(200,apply_fixes(req['ids']))
            else:self.respond(404,{'error':'Neznámý požadavek'})
        except Exception as e:self.respond(400,{'error':str(e)})
    def log_message(self,*args):pass

def apply_fixes(ids):
    if not isinstance(ids,list) or not ids:raise ValueError('Žádné vybrané opravy')
    byid={f['id']:f for obj in CACHE.values() for f in obj['findings']}
    chosen=[]
    for id in set(ids):
        f=byid.get(id)
        if f is None or f['kind'] not in ('dup','open','merge','chain','loop') or not f['safe']:raise ValueError('Nález není povoleno automaticky opravit: '+str(id))
        chosen.append(f)
    # A line may participate in exactly one selected merge operation.
    merged_keys=[key for f in chosen if f['kind'] in ('merge','chain')
                 for key in (f['chain_keys'] if f['kind']=='chain' else (f['shape_key'],f['other_key']))]
    if len(merged_keys)!=len(set(merged_keys)):
        raise ValueError('Konfliktní slučování: jedna čára patří do více schválených návrhů')
    if any(f['shape_key'] in merged_keys for f in chosen if f['kind'] not in ('merge','chain')):
        raise ValueError('Sloučení a další opravy téže čáry proveď v oddělených dávkách')
    segment_targets=[(f['shape_key'],f['row']) for f in chosen if f['kind'] in ('dup','loop')]
    if len(segment_targets)!=len(set(segment_targets)):
        raise ValueError('Konfliktní opravy stejného segmentu')
    grouped={}
    for f in chosen:grouped.setdefault(f['file'],[]).append(f)
    changes=[]
    # Validate all sources before writing any file.
    for rel,fs in grouped.items():
        path=(ROOT/rel).resolve()
        if not path.is_relative_to(ROOT.resolve()):raise ValueError('Cesta mimo projekt')
        original=path.read_bytes();obj=CACHE[rel]
        if hashlib.sha256(original).hexdigest()!=obj['hash']:raise ValueError('Soubor se mezitím změnil, spusť novou kontrolu: '+rel)
        lines=obj['lines'][:]
        # All source ranges refer to the untouched parse; perform atomic group edits.
        occupied=set()
        for f in fs:
            if f['kind'] not in ('merge','chain'):continue
            keys=f['chain_keys'] if f['kind']=='chain' else [f['shape_key'],f['other_key']]
            members=[next(sh for sh in obj['shapes'] if sh['key']==k) for k in keys]
            if len(members)<2 or len(set(keys))!=len(keys):raise ValueError('Neplatný řetězec')
            reference=members[0]
            for i,sh in enumerate(members):
                rows=set(range(sh['start'],sh['end']+1))
                if rows & occupied:raise ValueError('Překryv slučovaných bloků')
                occupied |= rows
                if sh['header'].split()!=reference['header'].split() or sh['id'] or '-reverse' in sh['header'].split():
                    raise ValueError('Nekompatibilní atributy')
                if sh['scrap_index']!=reference['scrap_index']:
                    raise ValueError('Čáry z různých scrapů')
                if i and members[i-1]['nodes'][-1]['p']!=sh['nodes'][0]['p']:
                    raise ValueError('Návaznost už není platná')
            def body_coords(sh):
                body=obj['lines'][sh['start']:sh['end']-1]
                if len(body)!=len(sh['nodes']):
                    raise ValueError('Čára obsahuje direktivy či komentáře')
                for line in body:
                    tokens=line.split('#',1)[0].split()
                    if '#' in line or len(tokens) not in (2,6):
                        raise ValueError('Nejednoznačné vnitřní atributy')
                return body
            joined=[obj['lines'][reference['start']-1]]+body_coords(reference)
            for sh in members[1:]:joined+=body_coords(sh)[1:]
            newline='\r\n' if obj['lines'][reference['start']-1].endswith('\r\n') else '\n'
            joined+=['endline'+newline]
            lines[reference['start']-1]=''.join(joined)
            for sh in members:
                for row in range(sh['start'],sh['end']+1):
                    if row!=reference['start']:lines[row-1]=''
        for f in fs:
            if f['kind'] in ('merge','chain'):continue
            if f['kind']=='open':
                row=f['start']
                # Existing -close option can appear on a separate line inside the line block.
                nextline=next((i for i in range(row, len(lines)) if lines[i].split('#',1)[0].strip()=='endline'),None)
                if nextline is None:raise ValueError('Chybí endline: '+rel+':'+str(row))
                optrow=next((i for i in range(row,nextline) if re.match(r'^\s*-close\s+(?:on|off|auto)\s*(?:#.*)?$',lines[i].strip())),None)
                if optrow is not None:
                    lines[optrow]=re.sub(r'(-close\s+)(?:on|off|auto)',r'\1on',lines[optrow],count=1)
                    continue
                header=lines[row-1];base,sep,comment=header.partition('#')
                if re.search(r'(?<!\S)-close\s+(?:on|off|auto)(?!\S)',base):
                    base=re.sub(r'(?<!\S)-close\s+(?:on|off|auto)(?!\S)','-close on',base,count=1)
                else:base=base.rstrip('\r\n').rstrip()+' -close on'+('\r\n' if header.endswith('\r\n') else '\n' if header.endswith('\n') else '')
                lines[row-1]=base+('#'+comment if sep else '')
                continue
            if f['kind']=='loop':
                row=f['row'];old=lines[row-1];parts=old.split('#',1)[0].split()
                proposal=f.get('proposed_points')
                if len(parts)!=6 or not proposal:raise ValueError('Nelze upravit Bézierův segment: '+rel+':'+str(row))
                # Protect the endpoint and only change control handles.
                if [float(z) for z in parts[-2:]]!=proposal[3]:
                    raise ValueError('Neshoda koncového bodu')
                indent=re.match(r'^\s*',old).group(0)
                comment='#'+old.partition('#')[2].rstrip('\r\n') if '#' in old else ''
                newline='\r\n' if old.endswith('\r\n') else '\n' if old.endswith('\n') else ''
                coords=[*proposal[1],*proposal[2]]
                fmt=lambda v: ('%.6f'%v).rstrip('0').rstrip('.')
                lines[row-1]=indent+' '.join([*(fmt(z) for z in coords),*parts[-2:]])+(' '+comment if comment else '')+newline
                continue
            row=f['row'];txt=lines[row-1].split('#',1)[0].strip().split()
            if len(txt) not in (2,6) or not all(re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?',v) for v in txt):raise ValueError('Řádek není jednoduchý bod: '+rel+':'+str(row))
            lines[row-1]=''
        new=''.join(lines).encode(obj['encoding'])
        changes.append((path,rel,original,new,fs))
    folder=ROOT/'_Therion_zalohy'/datetime.now().strftime('%Y-%m-%d_%H-%M-%S_%f')
    folder.mkdir(parents=True,exist_ok=False)
    for path,rel,original,new,fs in changes:
        dest=folder/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(original)
    log={'created':datetime.now().isoformat(),'root':str(ROOT),'changes':[{'file':rel,'rows_removed':[f['row'] for f in fs if f['kind']=='dup'],'lines_closed':[f['start'] for f in fs if f['kind']=='open'],'merged_lines':[[f['start'],f['row']] for f in fs if f['kind']=='merge'],'merged_chains':[[k for k in f['chain_keys']] for f in fs if f['kind']=='chain'],'curves_adjusted':[f['row'] for f in fs if f['kind']=='loop']} for _,rel,_,_,fs in changes]}
    (folder/'protokol.json').write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding='utf-8')
    written=[]
    try:
        for path,rel,original,new,fs in changes:
            temp=path.with_name(path.name+'.therion_tmp');temp.write_bytes(new);os.replace(temp,path);written.append((path,original))
    except Exception:
        for path,original in written:path.write_bytes(original)
        raise
    return {'upraveno_souboru':len(changes),'odstraneno_bodu_a_smycek':sum(f['kind']=='dup' for f in chosen),'uzavreno_car':sum(f['kind']=='open' for f in chosen),'slouceno_dvojic':sum(f['kind']=='merge' for f in chosen),'slouceno_retezcu':sum(f['kind']=='chain' for f in chosen),'opraveno_krivkovych_smycek':sum(f['kind']=='loop' for f in chosen),'zaloha':str(folder),'protokol':str(folder/'protokol.json')}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',nargs='?',default='.');p.add_argument('--port',type=int,default=0);p.add_argument('--tolerance',type=float,default=.15);p.add_argument('--near',type=float,default=1.0);args=p.parse_args()
    ROOT=Path(args.folder).expanduser().resolve();TOL=args.tolerance;NEAR=max(0,args.near)
    if not ROOT.is_dir():p.error('Zadaný adresář neexistuje')
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    url=f'http://127.0.0.1:{server.server_port}/';print('Therion kontrola:',url,flush=True);print('Ukončení: Ctrl+C',flush=True)
    threading.Timer(.6,lambda:webbrowser.open(url)).start()
    try:server.serve_forever()
    except KeyboardInterrupt:pass