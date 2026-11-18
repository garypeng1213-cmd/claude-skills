import json,sys
from shapely.geometry import box
from shapely.strtree import STRtree
d=json.load(open('p17.json'))
idx=[i for i,x in enumerate(d) if x['t']=='f' and max(x['r'][2]-x['r'][0],x['r'][3]-x['r'][1])<60]
def bb(x):
    r=x['r']; return (r[1],842-r[2],r[3],842-r[0])
G=float(sys.argv[1]) if len(sys.argv)>1 else 1.6
boxes=[box(*bb(d[i])) for i in idx]
tree=STRtree(boxes)
par=list(range(len(idx)))
def f(a):
    while par[a]!=a: par[a]=par[par[a]]; a=par[a]
    return a
for k,b in enumerate(boxes):
    for j in tree.query(b.buffer(G)):
        a,c=f(k),f(int(j))
        if a!=c: par[a]=c
cl={}
for k in range(len(idx)): cl.setdefault(f(k),[]).append(idx[k])
out=[]
for members in cl.values():
    xs=[bb(d[i]) for i in members]
    B=(min(a[0] for a in xs),min(a[1] for a in xs),max(a[2] for a in xs),max(a[3] for a in xs))
    out.append({'m':members,'b':B})
out.sort(key=lambda c:(round(c['b'][1]/10),c['b'][0]))
for n,c in enumerate(out): c['id']=n
json.dump(out,open('clusters.json','w'))
print(len(out))
# --- line merge pass
def h(c): return c['b'][3]-c['b'][1]
def w(c): return c['b'][2]-c['b'][0]
changed=True
while changed:
    changed=False
    out.sort(key=lambda c:c['b'][0])
    for a in out:
        if a.get('dead'): continue
        for b in out:
            if b is a or b.get('dead'): continue
            ha,hb=h(a),h(b)
            if min(ha,hb)<1.2 or max(ha,hb)>25: continue
            ov=min(a['b'][3],b['b'][3])-max(a['b'][1],b['b'][1])
            if ov<0.6*min(ha,hb): continue
            if abs(ha-hb)>0.45*max(ha,hb) and min(w(a),w(b))>0.6*min(ha,hb): continue
            gap=max(b['b'][0]-a['b'][2],a['b'][0]-b['b'][2])
            if gap<0.9*max(ha,hb):
                a['m']+=b['m']; a['b']=(min(a['b'][0],b['b'][0]),min(a['b'][1],b['b'][1]),max(a['b'][2],b['b'][2]),max(a['b'][3],b['b'][3]))
                b['dead']=True; changed=True
out=[c for c in out if not c.get('dead')]
out.sort(key=lambda c:(round(c['b'][1]/8),c['b'][0]))
for n,c in enumerate(out): c['id']=n
json.dump(out,open('clusters.json','w'))
print('merged',len(out))
