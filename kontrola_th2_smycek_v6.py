#!/usr/bin/env python3
"""Kontrola smyček a opakovaných uzlových souřadnic v Therion .th2.
Použití: py kontrola_th2_smycek_v6.py "D:\\Jeskyne" --tolerance 0.15
"""
import argparse
import csv
from pathlib import Path
import os
import math

def dist(a,b): return math.hypot(a[0]-b[0],a[1]-b[1])
def mid(a,b): return ((a[0]+b[0])/2,(a[1]+b[1])/2)
def flatness(p):
    a,b,c,d=p
    v=(d[0]-a[0],d[1]-a[1]); length=math.hypot(*v)
    if length<1e-10: return max(dist(a,b),dist(a,c))
    return max(abs(v[0]*(q[1]-a[1])-v[1]*(q[0]-a[0]))/length for q in (b,c))
def flatten(p,tol,depth=0):
    if flatness(p)<=tol or depth>=18: return [p[0],p[3]]
    a,b,c,d=p; ab=mid(a,b);bc=mid(b,c);cd=mid(c,d);abc=mid(ab,bc);bcd=mid(bc,cd);m=mid(abc,bcd)
    l=flatten((a,ab,abc,m),tol,depth+1);r=flatten((m,bcd,cd,d),tol,depth+1)
    return l[:-1]+r

def cross(a,b):return a[0]*b[1]-a[1]*b[0]
def intersection(a,b,c,d):
    r=(b[0]-a[0],b[1]-a[1]);s=(d[0]-c[0],d[1]-c[1]);den=cross(r,s)
    if abs(den)<1e-12:return None
    ca=(c[0]-a[0],c[1]-a[1]);t=cross(ca,s)/den;u=cross(ca,r)/den
    if 1e-7<t<1-1e-7 and 1e-7<u<1-1e-7:return (a[0]+t*r[0],a[1]+t*r[1])
    return None

def detect(poly):
    # Nesousední úsečky téže Bézierovy křivky se nesmějí protínat.
    hits=[]
    for i in range(len(poly)-1):
        for j in range(i+2,len(poly)-1):
            q=intersection(poly[i],poly[i+1],poly[j],poly[j+1])
            if q and all(dist(q,h)>1e-4 for h in hits):hits.append(q)
    return hits



HEADERS=['soubor','cesta_relativni','scrap','typ_cary','id_cary','radek_zacatku_cary','radek_segmentu','segment','problem','x','y','pocet_usecek','radek_prvniho_bodu','radek_opakovaneho_bodu']

def inspect(path,tol):
    results=[]; scrap=''; current=None
    def finish():
        if current is None:return
        # U -close on je povolena pouze shoda PRVNIHO a POSLEDNIHO bodu.
        # Vsechny ostatni duplicity se hlasí, vcetne opakovani uvnitr uzavrene cary.
        nodes=current['nodes']
        seen={}
        for i,(xy,row) in enumerate(nodes):
            if xy in seen:
                first_i,first_row=seen[xy]
                permitted=(current['close'] and first_i==0 and i==len(nodes)-1)
                if not permitted:
                    results.append([str(path),scrap_for_line[0],current['type'],current['id'],current['start'],row,'','DUPLICITNÍ BOD',xy[0],xy[1],'',first_row,row])
            else:
                seen[xy]=(i,row)
    scrap_for_line=['']
    for number,raw in enumerate(path.read_text(encoding='utf-8-sig',errors='replace').splitlines(),1):
        s=raw.split('#',1)[0].strip()
        if not s:continue
        parts=s.split();cmd=parts[0]
        if cmd=='line':
            finish()
            opts=parts[2:]
            lid=opts[opts.index('-id')+1] if '-id' in opts and opts.index('-id')+1<len(opts) else ''
            current={'type':parts[1] if len(parts)>1 else '', 'id':lid,'start':number,'close':any(opts[i:i+2]==['-close','on'] for i in range(len(opts)-1)), 'nodes':[],'prev':None,'segment':0}
            scrap_for_line[0]=scrap
        elif cmd=='endline':
            finish();current=None
        elif current is not None:
            if cmd=='-close' and len(parts)>1:
                current['close']=parts[1].lower()=='on'
                continue
            if cmd=='-id' and len(parts)>1:
                current['id']=parts[1]
                continue
            if len(parts) not in (2,6):continue
            try:nums=[float(x) for x in parts]
            except ValueError:continue
            xy=(nums[-2],nums[-1])
            current['nodes'].append((xy,number))
            if len(nums)==6 and current['prev'] is not None:
                p=(current['prev'],(nums[0],nums[1]),(nums[2],nums[3]),xy)
                current['segment']+=1
                poly=flatten(p,tol)
                for hit in detect(poly):
                    results.append([str(path),scrap_for_line[0],current['type'],current['id'],current['start'],number,current['segment'],'SAMOPRŮSEČÍK',round(hit[0],3),round(hit[1],3),len(poly)-1,'',''])
            current['prev']=xy
        elif cmd=='scrap':scrap=parts[1] if len(parts)>1 else ''
        elif cmd=='endscrap':scrap=''
    finish()
    return results

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder',nargs='?',default='.',help='Složka projektu nebo jeden .th2 soubor')
    parser.add_argument('--tolerance',type=float,default=0.15,help='Přesnost aproximace Bézierovy křivky (výchozí 0.15)')
    parser.add_argument('--output',default='nalezy_th2.csv')
    args=parser.parse_args()
    if args.tolerance<=0:parser.error('Tolerance musí být kladná')
    source=Path(args.folder)
    if not source.exists():parser.error('Zadaná cesta neexistuje')
    if source.is_dir():
        files=[]
        for directory, subdirs, filenames in os.walk(source):
            subdirs[:] = [name for name in subdirs if name.lower() != 'data']
            files.extend(Path(directory) / name for name in filenames if name.lower().endswith('.th2'))
        files.sort()
    else:
        files=[source]
    root=source.resolve() if source.is_dir() else source.resolve().parent
    findings=[]
    for f in files:
        try:
            for row in inspect(f,args.tolerance):
                row.insert(1,str(f.resolve().relative_to(root)))
                findings.append(row)
        except OSError as e:print('Nelze přečíst:',f,e)
    with Path(args.output).open('w',newline='',encoding='utf-8-sig') as handle:
        writer=csv.writer(handle,delimiter=';');writer.writerow(HEADERS);writer.writerows(findings)
    print(f'Zkontrolováno souborů: {len(files)}; nalezeno problémů: {len(findings)}')
    print(f'Výsledky: {Path(args.output).resolve()}')

if __name__=='__main__':main()