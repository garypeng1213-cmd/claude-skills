"""v4 追加：填充、草叢圖塊、鋼軌圖塊、線型（紙 mm 單位）"""
import math
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union, polygonize

S = 25.4 / 72
K = S * 5

def dbox(x):
    r = x['r']; return (r[1], 842 - r[2], r[3], 842 - r[0])

def segs_disp(x):
    out = []
    for k, v in x['i']:
        if k == 'l':
            out.append(((v[1], 842 - v[0]), (v[3], 842 - v[2])))
    return out

def dang(p, q):
    return math.degrees(math.atan2(q[1] - p[1], q[0] - p[0])) % 180

# ---------- 排除集合 ----------
BF_BOX = (263.5, 385, 358.3, 561)
WALL_IDS = set(range(8640, 8660))
SLOPE = [(244.3, 565.3), (179.9, 594.1), (101.6, 664.1)]
RAILS = [[8706], [6647], [2834], [2496], [6330], [6046], [6060], [6073]]

def above_slope(X, Y):
    # 回傳點在坡面線上方的距離（pt），不在範圍回 None
    for (a, b), (c, e) in zip(SLOPE, SLOPE[1:]):
        lo, hi = min(a, c), max(a, c)
        if lo - 3 <= X <= hi + 3:
            t = (X - a) / (c - a)
            yl = b + t * (e - b)
            return yl - Y
    return None

def classify(d, text_members):
    bf, wall, grass = set(), set(WALL_IDS), set()
    for i, x in enumerate(d):
        if x['t'] != 's' or i in text_members: continue
        X0, Y0, X1, Y1 = dbox(x)
        if x['w'] == 0.36 and len(x['i']) == 1 and x['i'][0][0] == 'l':
            if BF_BOX[0] <= X0 and X1 <= BF_BOX[2] and BF_BOX[1] <= Y0 and Y1 <= BF_BOX[3]:
                p, q = segs_disp(x)[0]
                a = dang(p, q)
                if abs(a - 45) < 1.6 or abs(a - 135) < 1.2:
                    bf.add(i)
        if x['w'] == 0.72 and max(X1 - X0, Y1 - Y0) <= 12 and 95 <= X0 and X1 <= 247:
            h = above_slope((X0 + X1) / 2, (Y0 + Y1) / 2)
            if h is not None and -0.5 < h < 15:
                grass.add(i)
    return bf, wall, grass

# ---------- 回填土填充圖樣（紙 mm，CAD 座標 Y 向上） ----------
def mm(Xd, Yd):          # 顯示 pt -> 紙 mm (CAD)
    return (Xd * S, (842 - Yd) * S)

def backfill_pattern(d, bf):
    """回傳 (定義, 邊界(模型cm))；定義以紙 mm 為單位、絕對基準點對齊原圖"""
    A, B = [], []
    for i in bf:
        p, q = segs_disp(d[i])[0]
        P, Q = mm(*p), mm(*q)
        a = math.degrees(math.atan2(Q[1] - P[1], Q[0] - P[0])) % 180
        (A if abs(a - 135) < 2 else B).append((P, Q, math.dist(P, Q)))
    sp = 3.605 * S                       # 線距 1.27mm
    # B：CAD 45° 連續線
    ub = (math.cos(math.radians(45)), math.sin(math.radians(45)))
    nb = (-ub[1], ub[0])
    P0 = max(B, key=lambda s: s[2])[0]
    # A：CAD 135° 短線 3.175 / 間隙 1.905
    ua = (math.cos(math.radians(135)), math.sin(math.radians(135)))
    na = (-ua[1], ua[0])
    full = [s for s in A if abs(s[2] - 3.175) < 0.05]
    def start(s):   # 沿 ua 方向較小的一端
        P, Q, L = s
        return P if (P[0] * ua[0] + P[1] * ua[1]) < (Q[0] * ua[0] + Q[1] * ua[1]) else Q
    st = [start(s) for s in full]
    st.sort(key=lambda p: p[0] * na[0] + p[1] * na[1])
    A0 = st[0]
    o0 = A0[0] * na[0] + A0[1] * na[1]; t0 = A0[0] * ua[0] + A0[1] * ua[1]
    per = 5.08
    # 相鄰線的錯位：取下一條線上的起點
    nxt = [p for p in st if abs((p[0] * na[0] + p[1] * na[1]) - o0 - sp) < 0.1]
    shift = ((nxt[0][0] * ua[0] + nxt[0][1] * ua[1]) - t0) % per if nxt else 0.0
    offA = (ua[0] * shift + na[0] * sp, ua[1] * shift + na[1] * sp)
    offB = (nb[0] * sp, nb[1] * sp)
    defn = [
        [45.0, (P0[0], P0[1]), offB, []],
        [135.0, (A0[0], A0[1]), offA, [3.175, -1.905]],
    ]
    bnd_d = [(264.11, 522.55), (281.65, 522.55), (357.65, 389.6), (357.65, 560.11), (264.11, 560.11)]
    bnd = [(X * K, (842 - Y) * K) for X, Y in bnd_d]
    return defn, bnd, shift

def scaled(defn, f):
    out = []
    for ang, b, o, dash in defn:
        out.append([ang, (b[0] * f, b[1] * f), (o[0] * f, o[1] * f), [x * f for x in dash]])
    return out

PAT_TEXT = """*BACKFILL, Backfill soil (P17, paper mm, scale 5 at 1:50 cm)
45, 0,0, 0,1.27
135, 0,0, {shift:.4f},1.27, 3.175,-1.905
"""

# ---------- 鋼軌外框：多段線段聯集成單一封閉外框 ----------
def outline(d, ids):
    lines = []; seen = []
    def snap(p):
        for q in seen:
            if abs(p[0] - q[0]) < 0.08 and abs(p[1] - q[1]) < 0.08: return q
        seen.append(p); return p
    for i in ids:
        for k, v in d[i]['i']:
            if k == 'l':
                a = snap((v[0], v[1])); b = snap((v[2], v[3]))
                if a != b: lines.append(LineString([(a[1] * K, a[0] * K), (b[1] * K, b[0] * K)]))
            elif k == 'c':
                a = snap((v[0], v[1])); b = snap((v[6], v[7]))
                P = [a]
                for n in range(1, 8):
                    t = n / 8; c0 = (1 - t) ** 3; c1 = 3 * t * (1 - t) ** 2; c2 = 3 * t * t * (1 - t); c3 = t ** 3
                    P.append((c0 * v[0] + c1 * v[2] + c2 * v[4] + c3 * v[6], c0 * v[1] + c1 * v[3] + c2 * v[5] + c3 * v[7]))
                P.append(b)
                lines.append(LineString([(p[1] * K, p[0] * K) for p in P]))
            elif k == 're':
                x0, y0, x1, y1 = v
                lines.append(LineString([(y0 * K, x0 * K), (y0 * K, x1 * K), (y1 * K, x1 * K), (y1 * K, x0 * K), (y0 * K, x0 * K)]))
    faces = list(polygonize(unary_union(lines)))
    if not faces: return None
    u = unary_union(faces)
    if u.geom_type != 'Polygon':
        u = max(u.geoms, key=lambda g: g.area)
    return list(u.exterior.coords)[:-1]

def grow(d, seed, tol=0.06):
    """從種子路徑沿端點相接擴張，找出同線寬、相連的全部路徑"""
    w = d[seed[0]]['w']
    def ends(i):
        e = []
        for k, v in d[i]['i']:
            if k == 'l': e += [(v[0], v[1]), (v[2], v[3])]
        return e
    X0, Y0, X1, Y1 = dbox(d[seed[0]])
    cand = [i for i, x in enumerate(d) if x['t'] == 's' and x['w'] == w
            and dbox(x)[0] > X0 - 40 and dbox(x)[2] < X1 + 40 and dbox(x)[1] > Y0 - 40 and dbox(x)[3] < Y1 + 40]
    got = list(seed); pts = [p for i in seed for p in ends(i)]
    changed = True
    while changed:
        changed = False
        for i in cand:
            if i in got: continue
            e = ends(i)
            if any(abs(a[0] - b[0]) < tol and abs(a[1] - b[1]) < tol for a in e for b in pts):
                got.append(i); pts += e; changed = True
    return got
