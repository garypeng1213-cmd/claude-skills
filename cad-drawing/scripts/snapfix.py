import json, math, ezdxf
from shapely.geometry import LineString, Point
doc = ezdxf.readfile('work/p17v4.dxf'); msp = doc.modelspace()
L = json.load(open('work/dimlog.json'))
st = {'E11':1,'E02':0,'DF3':0,'DE4':1,'DD5':3,'DC6':3,'DB7':3,'DA6':3,'D97':3,'D88':3,'D79':2,'D6A':3,'D5B':3,'D4C':0,'D3D':2,'D2E':3,'D1F':1,'D0E':3,'CFF':1,'CF0':2,'CE1':1,'CD2':2}
geo = []
def addent(e):
    t = e.dxftype()
    if t == 'LINE': geo.append(LineString([(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]))
    elif t == 'LWPOLYLINE':
        P = [p[:2] for p in e.get_points()]
        if e.closed: P.append(P[0])
        if len(P) > 1: geo.append(LineString(P))
for e in msp:
    if e.dxftype() == 'INSERT':
        for v in e.virtual_entities(): addent(v)
    elif e.dxf.layer not in ('文字-說明',): addent(e)
for r in L:
    s = st[r['handle']]
    for n, key in ((0, 'p1'), (1, 'p2')):
        ok = s & (1 << n)
        if ok: continue
        p = Point(r[key])
        best = min(((g.distance(p), g) for g in geo), key=lambda t: t[0])
        # nearest vertex
        vb = min(((math.dist(c, r[key]), c) for g in geo for c in g.coords), key=lambda t: t[0])
        print(r['key'], r['txt'], key, 'seg %.2f' % best[0], 'vtx %.2f' % vb[0], [round(c, 2) for c in vb[1]])

# ---- 產生改良版關聯 LISP ----
dims = {e.dxf.handle: e for e in msp.query('DIMENSION')}
lines = ['(defun c:P17ASSOC2 ( / e)', '  (setvar "CMDECHO" 0) (setvar "OSMODE" 0) (setvar "OSOPTIONS" 7)']
report = []
for r in L:
    e = dims[r['handle']]
    base = e.dxf.defpoint; ang = e.dxf.get('angle', 0)
    ax = 0 if abs(ang) < 1 else 1          # 0: 水平尺寸（延伸線垂直）
    args = []
    for key in ('p1', 'p2'):
        p = r[key]
        dirv = (0, 1 if p[1] > base.y else -1) if ax == 0 else (1 if p[0] > base.x else -1, 0)
        ray = LineString([p, (p[0] + dirv[0] * 15, p[1] + dirv[1] * 15)])
        hit = None
        if min(g.distance(Point(p)) for g in geo) < 0.01:
            hit = tuple(p)
        else:
            best = None
            for g in geo:
                x = ray.intersection(g)
                if x.is_empty: continue
                pts = [x] if x.geom_type == 'Point' else list(getattr(x, 'geoms', [])) or [Point(c) for c in x.coords]
                for q in pts:
                    if q.geom_type != 'Point': continue
                    dd = q.distance(Point(p))
                    if best is None or dd < best[0]: best = (dd, (q.x, q.y))
            hit = best and best[1]
        if hit is None:
            args.append('""'); report.append((r['key'], key, 'skip')); continue
        isv = min(math.dist(c, hit) for g in geo for c in g.coords) < 0.01
        args.append('"%s" (list %.4f %.4f 0.0)' % ('_endp' if isv else '_nea', hit[0], hit[1]))
        report.append((r['key'], key, round(math.dist(hit, p), 2)))
    xs = [r['p1'][0], r['p2'][0]]; ys = [r['p1'][1], r['p2'][1]]
    lines.append('  (command "_ZOOM" "_W" (list %.3f %.3f) (list %.3f %.3f))' % (min(xs) - 25, min(ys) - 25, max(xs) + 25, max(ys) + 25))
    lines.append('  (if (setq e (handent "%s")) (command "_DIMREASSOCIATE" e "" %s))' % (r['handle'], ' '.join(args)))
lines.append('  (command "_ZOOM" "_E") (princ))')
open('work/assoc2.lsp', 'w').write('\n'.join(lines) + '\n')
print([x for x in report if x[2] != 0.0])
