import pymupdf, json, math, os, sys
from PIL import ImageFont
HERE=os.path.dirname(os.path.abspath(__file__)); W=os.path.join(HERE,'work')
FONT='/System/Library/AssetsV2/com_apple_MobileAsset_Font8/6372627020b45393e500bb1661c460d4a93aff49.asset/AssetData/LiSongPro.ttf'
F=ImageFont.truetype(FONT,400)
def ink(txt):   # 字級 1 時，相對基線起點的墨跡框 (l,t,r,b)，y 向下
    l,t,r,b=F.getbbox(txt,anchor='ls'); return (l/400,t/400,r/400,b/400)
keys=json.load(open(os.path.join(W,'keys.json')))
p=pymupdf.open(os.path.join(W,sys.argv[1]))[0]
spans=[]
for bl in p.get_text('rawdict')['blocks']:
    for ln in bl.get('lines',[]):
        for s in ln['spans']:
            spans.append((''.join(c['c'] for c in s['chars']),s['size'],s['origin'],ln['dir']))
used=set(); out={}; ratios=[]
for key,txt,cat,rot,bb,h,wf in keys:
    if bb is None: continue
    X0,Y0,X1,Y1=bb; cx,cy=(X0+X1)/2,(Y0+Y1)/2
    cands=[(math.dist(s[2],(cx,cy)),i) for i,s in enumerate(spans) if i not in used and s[0].strip()==txt.strip()]
    if not cands: print('no span',key,txt); continue
    _,i=min(cands); used.add(i); s=spans[i]; size=s[1]
    ratios.append(size/h)
    l,t,r,b=ink(txt)
    if rot==0:
        k=(Y1-Y0)/(b-t); wf2=(X1-X0)/((r-l)*k)
    else:
        k=(X1-X0)/(b-t); wf2=(Y1-Y0)/((r-l)*k)
    out[key]={'k':k,'wf':wf2,'rot':rot,'ink':(l,t,r,b),'bb':bb,'cat':cat,'txt':txt}
q=sorted(ratios)[len(ratios)//2]
print('pdf字級/AutoCAD字高 =',round(q,4),'範圍',round(min(ratios),4),round(max(ratios),4))
# 字高（PDF 字級 k）分群取中位數
items=sorted(out.items(),key=lambda kv:kv[1]['k'])
groups=[]
for kk,v in items:
    if groups and v['k']<=groups[-1][0]*1.06: groups[-1][1].append(kk)
    else: groups.append([v['k'],[kk]])
for g in groups:
    ks=[out[kk]['k'] for kk in g[1]]; med=sorted(ks)[len(ks)//2]
    for kk in g[1]: out[kk]['ks']=med
    print('字級 %.2f pt (AutoCAD 字高 %.2f pt) ×%d'%(med,med/q,len(g[1])), [out[kk]['txt'][:6] for kk in g[1]][:8])
per={}
for kk,v in out.items():
    k=v['ks']; l,t,r,b=v['ink']; X0,Y0,X1,Y1=v['bb']
    wf=v['wf']*v['k']/k
    wf=round(wf,2)
    if abs(wf-1)<0.015: wf=1.0
    if v['rot']==0:
        ox=X0-l*k*wf; oy=Y1-b*k
    else:
        ox=X1-b*k; oy=Y1+l*k*wf
    per[kk]={'h':k/q,'wf':wf,'ox':ox,'oy':oy}
gs=sorted(per[kk]['h']/dict((k[0],k[5]) for k in keys)[kk] for kk in per)
json.dump({'per':per,'q':q,'g':gs[len(gs)//2]},open(os.path.join(W,'cal.json'),'w'),ensure_ascii=False,indent=0)
print('calibrated',len(per))
