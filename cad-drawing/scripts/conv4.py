"""把第 17 頁 PDF 向量轉成 DXF（模型空間 cm、1:50；圖框在 A3 配置）"""
import json, math, sys, os
import ezdxf
from ezdxf.enums import TextEntityAlignment
from shapely.geometry import MultiPoint

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from texts import TEXTS
import extra4 as X4

W = os.path.join(HERE, 'work')
d = json.load(open(os.path.join(W, 'p17.json')))
cl = {c['id']: c for c in json.load(open(os.path.join(W, 'clusters.json')))}
CAL = json.load(open(os.path.join(W, 'cal.json'))) if os.path.exists(os.path.join(W, 'cal.json')) else {}

S = 25.4 / 72          # pt -> 圖紙 mm
K = S * 5              # pt -> 模型 cm (1:50)

def disp(x, y):        # 原始座標 -> 顯示座標 (X 右, Y 下)
    return y, 842 - x

def mdl(x, y):  return (y * K, x * K)
def pap(x, y):  return (y * S, x * S)

# ---------------- 圖層 ----------------
LAYERS = {
    # 名稱: (顏色, 線寬 1/100mm, 說明)
    '構造物':     (4, 30, '擋土牆、L溝、矮牆、微型樁外框'),
    '尺寸標註':   (1, 25, '尺寸線、延伸線、箭頭、文字底線'),
    '鋼軌樁':     (30, 20, '鋼軌樁、微型樁、地錨'),
    '引線及詳圖': (5, 15, '引出線、詳圖圈、虛線框、表格'),
    '細線':       (140, 5, '細引出線'),
    '填充':       (3, 13, '回填料剖面線'),
    '臨時設施':   (3, 13, '臨時擋土鋼軌樁'),
    '地形線':     (8, 9, '原地面線'),
    '鋼筋':       (6, 40, '鋼筋、鋼線網點'),
    '植生':       (1, 25, '掛網植生草叢(圖塊)'),
    '文字-說明':  (7, 0, '說明文字'),
    '文字-尺寸':  (2, 0, '尺寸數字'),
    '文字-圖名':  (2, 0, '圖名'),
    '圖框':       (7, 25, '圖框、標題欄'),
    '圖框-文字':  (7, 0, '標題欄文字'),
    '視埠':       (8, 0, '視埠框(不出圖)'),
}
WMAP = {0.84: '構造物', 0.72: '尺寸標註', 0.54: '鋼軌樁', 0.42: '引線及詳圖',
        0.12: '細線', 0.36: '臨時設施', 0.24: '地形線', 1.14: '鋼筋'}
LWPT = {0.84: 30, 0.72: 25, 0.54: 20, 0.42: 15, 0.36: 13, 0.24: 9, 0.12: 5, 1.14: 40}

doc = ezdxf.new('R2018', setup=True)
doc.header['$INSUNITS'] = 5        # cm
doc.header['$MEASUREMENT'] = 1
doc.header['$LTSCALE'] = 5.0       # 線型以紙面 mm 定義，1:50、模型 cm
doc.header['$PSLTSCALE'] = 0
doc.header['$LWDISPLAY'] = 1
for n, (c, lw, desc) in LAYERS.items():
    ly = doc.layers.add(n, color=c)   # 線寬不設，交給 CTB
    ly.description = desc
doc.layers.get('視埠').dxf.plot = 0

# 文字樣式：儷宋 Pro（接近細明體）
st = doc.styles.add('明體', font='LiSongPro.ttf')
st.dxf.width = 1.0

msp = doc.modelspace()

# ---------------- 圖紙空間判斷 ----------------
def dbox(x):
    r = x['r']
    return (r[1], 842 - r[2], r[3], 842 - r[0])

def is_paper(x):
    X0, Y0, X1, Y1 = dbox(x)
    if Y0 >= 771.0: return True
    if max(X1 - X0, Y1 - Y0) > 600: return True
    return False

# ---------------- 文字字形集合 ----------------
text_members = set()
for ids, txt, rot, cat, opt in TEXTS:
    for i in ids:
        for m in cl[i]['m']:
            if 'maxy' in opt and dbox(d[m])[1] >= opt['maxy']:
                continue
            text_members.add(m)

BF, WALL, GRASS = X4.classify(d, text_members)
EXCL = BF | WALL | GRASS
DJ = json.load(open(os.path.join(W, 'dims.json')))
DIMKEYS = {r['key'] for r in DJ['dims']}
_used = {}
for idx, p, q in DJ['seg']:
    _used.setdefault(idx, []).append((p, q))
def _same(v, p, q):
    a = (v[1], 842 - v[0]); b = (v[3], 842 - v[2])
    m = lambda u, w: abs(u[0] - w[0]) < 0.02 and abs(u[1] - w[1]) < 0.02
    return (m(a, p) and m(b, q)) or (m(a, q) and m(b, p))
for idx, lst in _used.items():
    keep = [it for it in d[idx]['i'] if not (it[0] == 'l' and any(_same(it[1], p, q) for p, q in lst))]
    if keep: d[idx] = dict(d[idx], i=keep, close=False)
    else: EXCL.add(idx)
DIMFILL = set(DJ['fill'])
print('排除: 回填', len(BF), '牆', len(WALL), '草', len(GRASS))

# ---------------- 路徑轉點 ----------------
def bez(v, n=8):
    x0, y0, x1, y1, x2, y2, x3, y3 = v
    out = []
    for k in range(1, n + 1):
        t = k / n; a = (1 - t) ** 3; b = 3 * t * (1 - t) ** 2; c = 3 * t * t * (1 - t); e = t ** 3
        out.append((a * x0 + b * x1 + c * x2 + e * x3, a * y0 + b * y1 + c * y2 + e * y3))
    return out

def chains(x):
    """回傳 [(點列, 是否含曲線)]"""
    res = []; cur = None; curved = False
    for k, v in x['i']:
        if k == 're':
            res.append(([(v[0], v[1]), (v[2], v[1]), (v[2], v[3]), (v[0], v[3]), (v[0], v[1])], False)); continue
        if k == 'qu':
            res.append(([(v[i], v[i + 1]) for i in range(0, 8, 2)] + [(v[0], v[1])], False)); continue
        start = (v[0], v[1])
        pts = [(v[2], v[3])] if k == 'l' else bez(v)
        if cur and abs(cur[-1][0] - start[0]) < 1e-3 and abs(cur[-1][1] - start[1]) < 1e-3:
            cur += pts; curved = curved or k == 'c'
        else:
            if cur: res.append((cur, curved))
            cur = [start] + pts; curved = k == 'c'
    if cur: res.append((cur, curved))
    return res

def circle_of(x):
    its = x['i']
    if len(its) != 4 or any(k != 'c' for k, v in its): return None
    pts = [(v[0], v[1]) for k, v in its]
    cx = sum(p[0] for p in pts) / 4; cy = sum(p[1] for p in pts) / 4
    rs = [math.hypot(p[0] - cx, p[1] - cy) for p in pts]
    if max(rs) - min(rs) > 0.02 * max(rs) + 0.01: return None
    return (cx, cy, sum(rs) / 4)

RAIL_IDS = {i for g in X4.RAILS for i in X4.grow(d, g)}
# ---------------- 虛線合併 ----------------
segs = []      # (index, 線寬, p0, p1)
solid = []     # 其餘路徑
for idx, x in enumerate(d):
    if x['t'] != 's' or is_paper(x) or idx in EXCL or idx in RAIL_IDS:
        continue
    if len(x['i']) == 1 and x['i'][0][0] == 'l':
        v = x['i'][0][1]
        L = math.hypot(v[2] - v[0], v[3] - v[1])
        if 0.2 < L < 14:
            segs.append((idx, x['w'], (v[0], v[1]), (v[2], v[3]), L)); continue
    solid.append(idx)

from collections import defaultdict
buckets = defaultdict(list)
for s in segs:
    idx, w, p, q, L = s
    a = math.atan2(q[1] - p[1], q[0] - p[0]) % math.pi
    ux, uy = math.cos(a), math.sin(a)
    off = -uy * p[0] + ux * p[1]
    buckets[(w, round(a, 2), round(off, 0))].append(s)

dashed = []    # (線寬, 起點, 終點, 平均線段, 平均間隙)
used = set()
for key, lst in buckets.items():
    w = key[0]
    a0 = key[1]
    ux, uy = math.cos(a0), math.sin(a0)
    # 依偏移精細分組
    lst.sort(key=lambda s: -uy * s[2][0] + ux * s[2][1])
    groups = []
    for s in lst:
        o = -uy * s[2][0] + ux * s[2][1]
        a = math.atan2(s[3][1] - s[2][1], s[3][0] - s[2][0]) % math.pi
        if abs((a - a0 + math.pi / 2) % math.pi - math.pi / 2) > 0.01:
            continue
        for g in groups:
            if abs(g[0] - o) < 0.15:
                g[1].append(s); break
        else:
            groups.append([o, [s]])
    for o, g in groups:
        def t(p): return ux * p[0] + uy * p[1]
        items = sorted([(min(t(s[2]), t(s[3])), max(t(s[2]), t(s[3])), s) for s in g])
        run = [items[0]]
        def flush(run):
            if len(run) >= 3:
                gaps = [run[i + 1][0] - run[i][1] for i in range(len(run) - 1)]
                lens = [r[1] - r[0] for r in run]
                if min(gaps) > 0.15 and max(gaps) < 6:
                    t0, t1 = run[0][0], run[-1][1]
                    p0 = (ux * t0 - uy * o, uy * t0 + ux * o)
                    p1 = (ux * t1 - uy * o, uy * t1 + ux * o)
                    # 用實際端點避免偏移誤差
                    s0, s1 = run[0][2], run[-1][2]
                    e0 = min([s0[2], s0[3]], key=t); e1 = max([s1[2], s1[3]], key=t)
                    lens_m = sorted(lens[1:-1]) or lens
                    gaps_m = sorted(gaps)
                    dashed.append((w, e0, e1, lens_m[len(lens_m) // 2], gaps_m[len(gaps_m) // 2]))
                    for r in run: used.add(r[2][0])
        for it in items[1:]:
            if it[0] - run[-1][1] < 6 and it[0] - run[-1][1] > -0.05:
                run.append(it)
            else:
                flush(run); run = [it]
        flush(run)
for s in segs:
    if s[0] not in used:
        solid.append(s[0])

# 虛線線型：依 (線段, 間隙) 歸類
patterns = {}
LIN = []
def ltype_for(dash, gap):
    key = (round(dash * 2) / 2, round(gap * 2) / 2)
    if key not in patterns:
        dm, gm = round(key[0] * S, 3), round(key[1] * S, 3)   # 紙面 mm
        name = 'DASH_%02d_%02d' % (round(dm * 10), round(gm * 10))
        doc.linetypes.add(name, pattern=[dm + gm, dm, -gm],
                          description='Dashed %.1f/%.1f mm __ __ __' % (dm, gm))
        LIN.append((name, dm, gm))
        patterns[key] = name
    return patterns[key]

# ---------------- 圖層判斷（綠色線分填充/臨時設施） ----------------
HATCH_BOX = [(255, 380, 365, 566)]   # 顯示座標：回填剖面線範圍
def in_hatch(x):
    X0, Y0, X1, Y1 = dbox(x)
    for a, b, c, e in HATCH_BOX:
        if X0 >= a and X1 <= c and Y0 >= b and Y1 <= e: return True
    return False

def layer_of(x):
    if x['w'] == 0.36 and in_hatch(x):
        return '填充'
    return WMAP.get(x['w'], '尺寸標註')

# ---------------- 輸出線條 ----------------
doc.layouts.rename('Layout1', 'A3出圖')
psp = doc.layouts.get('A3出圖')

def add_chain(space, conv, pts, layer, closed=False, lw=None):
    P = [conv(*p) for p in pts]
    attrs = {'layer': layer}
    if len(P) == 2:
        space.add_line(P[0], P[1], dxfattribs=attrs)
    else:
        isclosed = closed or (math.dist(P[0], P[-1]) < 1e-6)
        if isclosed and len(P) > 2: P = P[:-1]
        space.add_lwpolyline(P, close=isclosed, dxfattribs=attrs)

n_line = n_circ = 0
for idx in solid:
    x = d[idx]
    lay = layer_of(x)
    c = circle_of(x)
    if c:
        cx, cy = mdl(c[0], c[1])
        msp.add_circle((cx, cy), c[2] * K, dxfattribs={'layer': lay}); n_circ += 1; continue
    for pts, curved in chains(x):
        add_chain(msp, mdl, pts, lay, closed=x.get('close', False)); n_line += 1

for w, p0, p1, dash, gap in dashed:
    lay = WMAP.get(w, '尺寸標註')
    msp.add_line(mdl(*p0), mdl(*p1), dxfattribs={'layer': lay, 'linetype': ltype_for(dash, gap)})

# ---------------- v4：回填土填充（自訂 BACKFILL） ----------------
defn, bnd, shift = X4.backfill_pattern(d, BF)
h = msp.add_hatch(color=256, dxfattribs={'layer': '填充'})
h.paths.add_polyline_path(bnd, is_closed=True)
h.set_pattern_fill('BACKFILL', color=256, scale=5.0, pattern_type=2, definition=defn)
open(os.path.join(W, 'BACKFILL.pat'), 'w', encoding='utf-8').write(X4.PAT_TEXT.format(shift=shift))

# 牆面紅色交叉線 → ANSI37（線距配合原圖 2.715pt）
wx0, wy0, wx1, wy1 = 261.29, 522.55, 264.11, 560.11
wb = [(wx0 * K, (842 - wy0) * K), (wx1 * K, (842 - wy0) * K), (wx1 * K, (842 - wy1) * K), (wx0 * K, (842 - wy1) * K)]
h2 = msp.add_hatch(color=256, dxfattribs={'layer': '尺寸標註'})
h2.paths.add_polyline_path(wb, is_closed=True)
h2.set_pattern_fill('ANSI37', color=256, scale=round(2.715 * K / 3.175, 3))
h2.set_pattern_definition([[45.0, (0, 0), (-2.2450640303, 2.2450640303), []], [135.0, (0, 0), (-2.2450640303, -2.2450640303), []]], factor=round(2.715 * K / 3.175, 3))

# ---------------- v4：草叢 → 圖塊 ----------------
gx = min(dbox(d[i])[0] for i in GRASS); gy = max(dbox(d[i])[3] for i in GRASS)
gbase = mdl(842 - gy, gx)
blk = doc.blocks.new('植生草叢', base_point=gbase)
for i in sorted(GRASS):
    for pts, curved in chains(d[i]):
        P = [mdl(*p) for p in pts]
        if len(P) == 2: blk.add_line(P[0], P[1], dxfattribs={'layer': '0', 'color': 0})
        else: blk.add_lwpolyline(P, dxfattribs={'layer': '0', 'color': 0})
msp.add_blockref('植生草叢', gbase, dxfattribs={'layer': '植生'})

# ---------------- v4：鋼軌斷面 → 單一封閉聚合線 + 圖塊 ----------------
shapes = {}
RAILG = [X4.grow(d, g) for g in X4.RAILS]
for g in RAILG:
    P = X4.outline(d, g)
    lay = WMAP.get(d[g[0]]['w'], '構造物')
    xs = [p[0] for p in P]; ys = [p[1] for p in P]
    c = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
    rel = [(p[0] - c[0], p[1] - c[1]) for p in P]
    from shapely.geometry import Polygon as _Pg
    pg = _Pg(rel); hit = None
    for nm, (pg2, _) in shapes.items():
        if pg.hausdorff_distance(pg2) < 1.0: hit = nm; break
    if hit is None:
        hit = '鋼軌50kg-%d' % (len(shapes) + 1)
        b = doc.blocks.new(hit, base_point=(0, 0))
        b.add_lwpolyline(rel, close=True, dxfattribs={'layer': '0', 'color': 0})
        shapes[hit] = (pg, b)
    msp.add_blockref(hit, c, dxfattribs={'layer': lay})
print('鋼軌圖塊', len(shapes), '插入', len(X4.RAILS))

# ---------------- 非文字填色（箭頭、鋼筋點） ----------------
def add_fill(space, conv, x, layer, lw=None):
    for pts, curved in chains(x):
        P = [conv(*p) for p in pts]
        if len(P) < 3: continue
        if math.dist(P[0], P[-1]) < 1e-6: P = P[:-1]
        h = space.add_hatch(color=256, dxfattribs={'layer': layer})
        h.paths.add_polyline_path(P, is_closed=True)

for idx, x in enumerate(d):
    if x['t'] != 'f' or idx in text_members or idx in DIMFILL: continue
    if is_paper(x): continue
    X0, Y0, X1, Y1 = dbox(x)
    wv, hv = X1 - X0, Y1 - Y0
    if max(wv, hv) < 2.7 and abs(wv - hv) < 0.4:
        lay = '鋼筋'
    elif (345 < X0 < 368 and 285 < Y0 < 302) or (245 < X0 < 270 and 512 < Y0 < 524):
        lay = '構造物'
    else:
        lay = '尺寸標註'
    add_fill(msp, mdl, x, lay)

# ---------------- 圖紙空間：圖框與標題欄 ----------------
for idx, x in enumerate(d):
    if not is_paper(x) or idx in text_members: continue
    if x['t'] == 'f':
        add_fill(psp, pap, x, '圖框')
    else:
        for pts, curved in chains(x):
            add_chain(psp, pap, pts, '圖框', lw=LWPT.get(x['w'], 25))

# ---------------- 文字 ----------------
CJK = lambda s: any(ord(ch) > 0x2E80 for ch in s)

def pts_of(members, clipx=None):
    P = []
    for i in members:
        for pts, _ in chains(d[i]):
            for (a, b) in pts:
                X, Y = disp(a, b)
                if clipx and not (clipx[0] <= X <= clipx[1]): continue
                P.append((X, Y))
    return P

def split_by_gap(members, axis, gap):
    items = []
    for i in members:
        X0, Y0, X1, Y1 = dbox(d[i])
        items.append(((X0, X1) if axis == 0 else (Y0, Y1), i))
    items.sort()
    groups = [[items[0]]]
    for it in items[1:]:
        if it[0][0] - max(g[0][1] for g in groups[-1]) > gap: groups.append([it])
        else: groups[-1].append(it)
    return [[i for _, i in g] for g in groups]

LAYER_OF = {'N': '文字-說明', 'D': '文字-尺寸', 'T': '文字-圖名', 'P': '圖框-文字'}
HR = CAL.get('hr', 0.92)     # 字高 / 字形外框高（中文）
HRD = CAL.get('hrd', 1.33)   # 字高 / 字形外框高（純數字英文）
BL = CAL.get('bl', 0.10)     # 字形底到基線（以字高計）
per = CAL.get('per', {})

def u(s):
    return s

def place(key, txt, members, rot, cat, opt):
    clipx = opt.get('clipx')
    P = pts_of(members, clipx)
    if not P: return
    space, conv = (psp, lambda X, Y: (X * S, (842 - Y) * S)) if cat == 'P' else \
                  (msp, lambda X, Y: (X * K, (842 - Y) * K))
    if rot == 'auto':
        raise RuntimeError
    if rot == 0:
        X0 = min(p[0] for p in P); X1 = max(p[0] for p in P)
        Y0 = min(p[1] for p in P); Y1 = max(p[1] for p in P)
        gh = Y1 - Y0; gw = X1 - X0
        h = gh * (HR if CJK(txt) else HRD)
        base = (X0, Y1 - BL * h)       # 顯示座標 Y 向下，Y1 是底
    else:  # 90 度：由下往上讀
        X0 = min(p[0] for p in P); X1 = max(p[0] for p in P)
        Y0 = min(p[1] for p in P); Y1 = max(p[1] for p in P)
        gh = X1 - X0; gw = Y1 - Y0
        h = gh * (HR if CJK(txt) else HRD)
        base = (X1 - BL * h, Y1)
    c = per.get(key)
    wf = 1.0
    if c:   # 校正值：字高(pt)、寬度係數、基線起點(顯示 pt)
        h, wf, base = c['h'], c['wf'], (c['ox'], c['oy'])
    unit = S if cat == 'P' else K
    ins = conv(*base)
    t = space.add_text(txt, height=h * unit, rotation=rot,
                       dxfattribs={'layer': LAYER_OF[cat], 'style': '明體', 'width': wf})
    t.dxf.insert = ins
    t.set_xdata('PDFKEY', [(1000, key)]) if False else None
    KEYS.append((key, txt, cat, rot, (X0, Y0, X1, Y1), h, wf))

def place_slanted(key, lines, members, cat):
    P = pts_of(members)
    mr = MultiPoint(P).minimum_rotated_rectangle
    cs = list(mr.exterior.coords)[:4]
    # 取長邊方向
    e = max([(cs[i], cs[(i + 1) % 4]) for i in range(4)], key=lambda e: math.dist(*e))
    ang = math.atan2(-(e[1][1] - e[0][1]), e[1][0] - e[0][0])   # 轉成 Y 向上
    if math.cos(ang) < 0: ang += math.pi
    ux, uy = math.cos(ang), -math.sin(ang)   # 顯示座標中的閱讀方向
    nx, ny = -uy, ux                          # 法向（朝下為正? 依符號）
    # 以法向投影分行
    proj = sorted((p[0] * nx + p[1] * ny, p) for p in P)
    vals = [v for v, _ in proj]
    # 找最大間隙切成兩行
    gi = max(range(len(vals) - 1), key=lambda i: vals[i + 1] - vals[i])
    parts = [[p for v, p in proj[:gi + 1]], [p for v, p in proj[gi + 1:]]]
    # 第一行應在閱讀方向「上方」：法向值較小者
    for li, (txt, part) in enumerate(zip(lines, parts)):
        along = [p[0] * ux + p[1] * uy for p in part]
        acr = [p[0] * nx + p[1] * ny for p in part]
        a0, a1 = min(along), max(along); n0, n1 = min(acr), max(acr)
        gh = n1 - n0
        h = gh * (HR if CJK(txt) else HRD)
        k2 = '%s-%d' % (key, li)
        c = per.get(k2, {})
        h *= CAL.get('g', 1.0)
        # 基線點：閱讀起點、底邊（法向大的一側為下方）
        bx = a0 * ux + (n1 - BL * h) * nx
        by = a0 * uy + (n1 - BL * h) * ny
        bx += c.get('dx', 0.0); by += c.get('dy', 0.0)
        t = msp.add_text(txt, height=h * K, rotation=math.degrees(ang),
                         dxfattribs={'layer': LAYER_OF[cat], 'style': '明體', 'width': c.get('wf', 1.0)})
        t.dxf.insert = (bx * K, (842 - by) * K)
        KEYS.append((k2, txt, cat, math.degrees(ang), None, h, 1.0))

KEYS = []
for ids, txt, rot, cat, opt in TEXTS:
    if '-'.join(map(str, ids)) in DIMKEYS: continue
    members = [m for i in ids for m in cl[i]['m']]
    if 'maxy' in opt:
        members = [m for m in members if dbox(d[m])[1] < opt['maxy']]
    key = '-'.join(map(str, ids))
    if rot == 'auto':
        place_slanted(key, txt, members, cat)
    elif isinstance(txt, list):
        axis = 0 if rot == 0 else 1
        groups = split_by_gap(members, axis, opt.get('gap', 2.0))
        if len(groups) != len(txt):
            print('!! 切分數量不符', key, len(groups), txt)
        for n, (g, s) in enumerate(zip(groups, txt)):
            if '%s.%d' % (key, n) in DIMKEYS: continue
            place('%s.%d' % (key, n), s, g, rot, cat, opt)
    else:
        place(key, txt, members, rot, cat, opt)


# ---------------- v4：真正的尺寸標註（DIMENSION） ----------------
doc.styles.add('明體-尺寸', font='LiSongPro.ttf').dxf.width = 0.8
ds = doc.dimstyles.new('P17-1比50')
for k_, v_ in dict(dimscale=5.0, dimtxt=round(9.2 * S, 3), dimasz=2.0, dimexe=0.6, dimexo=0.0, dimgap=0.6,
                   dimtxsty='明體-尺寸', dimclrt=2, dimclrd=256, dimclre=256, dimdec=0, dimzin=8, dimlunit=2,
                   dimtad=1, dimtih=0, dimtoh=0, dimtofl=1, dimlfac=1.0, dimtmove=2, dimadec=0).items():
    ds.dxf.set(k_, v_)
doc.header['$DIMSTYLE'] = 'P17-1比50'
doc.header['$DIMASSOC'] = 2
DIMLOG = []
for r in DJ['dims']:
    ax = 0 if r['rot'] == 0 else 1
    e0, e1 = r['defs'][0], r['defs'][1]
    p1 = (e0['def'][0] * K, (842 - e0['def'][1]) * K)
    p2 = (e1['def'][0] * K, (842 - e1['def'][1]) * K)
    lv = r['line'][0]
    base = (lv[0] * K, (842 - lv[1]) * K)
    ov = {}
    txt = '<>'
    meas = round(r['meas'])
    if r['key'] == '45':
        ov['dimlfac'] = 0.2                       # 1/10 詳圖
    elif not (r['txt'].isdigit() and int(r['txt']) == meas):
        txt = r['txt']                            # 不照比例或代號：文字覆寫
    lay = WMAP.get(r['w'], '尺寸標註')
    dim = msp.add_linear_dim(base=base, p1=p1, p2=p2, angle=0 if ax == 0 else 90, text=txt,
                             dimstyle='P17-1比50', override=ov, dxfattribs={'layer': lay})
    tc = r['tc']
    dim.set_location((tc[0] * K, (842 - tc[1]) * K), leader=False, relative=False)
    dim.render()
    DIMLOG.append({'key': r['key'], 'txt': r['txt'], 'p1': p1, 'p2': p2, 'snap': [e0['snap'], e1['snap']], 'handle': dim.dimension.dxf.handle})
json.dump(DIMLOG, open(os.path.join(W, 'dimlog.json'), 'w'), ensure_ascii=False)
print('尺寸', len(DIMLOG))
json.dump(KEYS, open(os.path.join(W, 'keys.json'), 'w'), ensure_ascii=False)

# ---------------- 配置 A3 與視埠 ----------------
psp.page_setup(size=(420, 297), margins=(0, 0, 0, 0), units='mm', scale=(1, 1),
               name='ISO_full_bleed_A3_(420.00_x_297.00_MM)', device='DWG To PDF.pc3')
# 視埠：圖框內、標題欄以上
vx0, vy0, vx1, vy1 = 30.77, 34.99, 1160.21, 771.31        # 顯示 pt
pw, ph = (vx1 - vx0) * S, (vy1 - vy0) * S
pcx, pcy = (vx0 + vx1) / 2 * S, (842 - (vy0 + vy1) / 2) * S
vp = psp.add_viewport(center=(pcx, pcy), size=(pw, ph),
                      view_center_point=(pcx * 5, pcy * 5), view_height=ph * 5,
                      dxfattribs={'layer': '視埠'})
vp.dxf.flags = vp.dxf.flags | 16384   # 鎖定顯示
psp.dxf_layout.dxf.current_style_sheet = 'P17-LW.ctb'
psp.dxf_layout.dxf.plot_layout_flags |= 1 | 128   # 依線寬出圖、套用出圖型式

out = os.path.join(W, 'p17v4.dxf')
doc.saveas(out)
open(os.path.join(W, 'p17.lin'), 'w', encoding='utf-8').write(''.join('*%s,%s\nA,%.3f,-%.3f\n' % (n, 'Dashed %.1f/%.1f mm __ __ __' % (a, b), a, b) for n, a, b in LIN))
print('lines', n_line, 'circles', n_circ, 'dashed', len(dashed), 'patterns', patterns, 'texts', len(KEYS))
print(out)
