"""從原圖找出每道尺寸：尺寸線、延伸線、定義點、箭頭、文字位置"""
import json, math
exec(open('dims.py').read().split('out = []')[0])
K = 25.4 / 72 * 5
SKIP = {'37', '42', '86', '100'}          # 0.3 / 1.0 是坡度符號，不是尺寸
EXTRA = [('w1', 'w1', 0)]                  # 說明類文字但其實是尺寸
cl = {c['id']: c for c in json.load(open('work/clusters.json'))}
F = [(i, dbox(x)) for i, x in enumerate(d) if x['t'] == 'f']
GV = []                                     # 幾何頂點（顯示座標）
for i, x in enumerate(d):
    if x['t'] != 's': continue
    for k, v in x['i']:
        if k in ('l', 'c'):
            GV.append((i, (v[1], 842 - v[0]))); GV.append((i, (v[-1], 842 - v[-2])))
def find_line(bb, rot):
    X0, Y0, X1, Y1 = bb
    best = None
    for s in SEG:
        p, q = s[1], s[2]
        if rot == 0 and horiz(p, q) and min(p[0], q[0]) - 0.5 <= (X0 + X1) / 2 <= max(p[0], q[0]) + 0.5:
            dd = p[1] - Y1
        elif rot == 90 and vert(p, q) and min(p[1], q[1]) - 0.5 <= (Y0 + Y1) / 2 <= max(p[1], q[1]) + 0.5:
            dd = p[0] - X1
        else: continue
        if -0.5 < dd < (5 if abs(bb[0]-311.63) < 0.1 else 4) and (best is None or abs(dd) < best[0]): best = (abs(dd), s)
    return best and best[1]
res = []; used_seg = set(); used_fill = set()
items = [(k, t, c, r, b) for k, t, c, r, b, h, w in keys if c == 'D' and k not in SKIP]
items += [(k, t, 'N', r, b) for k, t, c, r, b, h, w in keys if k == '151']
for key, txt, cat, rot, bb in items:
    s = find_line(bb, rot)
    if not s: print('!! 找不到', key, txt); continue
    used_seg.add((s[0], s[1], s[2]))
    p, q = s[1], s[2]
    ends = sorted([p, q])
    ax = 0 if rot == 0 else 1                       # 尺寸線方向軸
    defs = []
    def perp_at(pos, lvl):
        r = []
        for t in SEG:
            a, b = t[1], t[2]
            if ax == 0 and vert(a, b) and min(a[1], b[1]) - 0.3 <= lvl <= max(a[1], b[1]) + 0.3: r.append(a[0])
            if ax == 1 and horiz(a, b) and min(a[0], b[0]) - 0.3 <= lvl <= max(a[0], b[0]) + 0.3: r.append(a[1])
        return r
    lvl = p[1 - ax]
    xs = perp_at(None, lvl)
    new_ends = []
    for n, e in enumerate(ends):
        out = -1 if n == 0 else 1
        c_out = [x for x in xs if 0 <= (x - e[ax]) * out < 7.5]
        c_in = [x for x in xs if 0 < (e[ax] - x) * out < 7.5]
        z = [x for x in c_out if abs(x - e[ax]) < 0.2]
        if z: v = z[0]
        elif c_out: v = min(c_out, key=lambda x: abs(abs(x - e[ax]) - 5.67))
        elif c_in: v = min(c_in, key=lambda x: abs(x - e[ax]))
        else: v = e[ax]
        new_ends.append((v, lvl) if ax == 0 else (lvl, v))
    ends = new_ends
    for e in ends:
        # 延伸線：垂直於尺寸線、通過端點
        ext = None
        for t in SEG:
            a, b = t[1], t[2]
            if (rot == 0 and vert(a, b) and abs(a[0] - e[0]) < 0.1 and min(a[1], b[1]) - 0.3 <= e[1] <= max(a[1], b[1]) + 0.3) or \
               (rot == 90 and horiz(a, b) and abs(a[1] - e[1]) < 0.1 and min(a[0], b[0]) - 0.3 <= e[0] <= max(a[0], b[0]) + 0.3):
                far = max([a, b], key=lambda z: abs(z[1 - ax] - e[1 - ax]))
                L = abs(far[1 - ax] - e[1 - ax])
                if ext is None or L > ext[1]: ext = (t, L, far)
        if ext and ext[1] > 1.0:
            used_seg.add((ext[0][0], ext[0][1], ext[0][2]))
            far = ext[2]; sgn = 1 if far[1 - ax] > e[1 - ax] else -1
            # 往物件方向找最近的幾何頂點（同一直線上、距離 0~4pt）
            cand = []
            for gi, g in GV:
                if gi == ext[0][0]: continue
                if abs(g[ax] - e[ax]) < 0.15:
                    dd = (g[1 - ax] - far[1 - ax]) * sgn
                    if -0.05 <= dd < 4: cand.append((dd, g))
            dp = min(cand)[1] if cand else far
            defs.append({'end': e, 'far': far, 'def': (e[0], dp[1]) if ax == 0 else (dp[0], e[1]), 'snap': bool(cand)})
        else:
            defs.append({'end': e, 'far': e, 'def': e, 'snap': False})
    for fi, fb in F:
        for e in ends:
            if fb[0] - 0.3 <= e[0] <= fb[2] + 0.3 and fb[1] - 0.3 <= e[1] <= fb[3] + 0.3 and max(fb[2] - fb[0], fb[3] - fb[1]) < 6:
                used_fill.add(fi)
    meas = abs((ends[1][ax] - ends[0][ax])) * K
    res.append({'key': key, 'txt': txt, 'rot': rot, 'w': s[3], 'line': [p, q], 'defs': defs,
                'tc': ((bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2), 'meas': round(meas, 1)})
for r in res:
    print(r['key'], r['txt'], r['w'], r['meas'], [ (round(x['def'][0],2), round(x['def'][1],2), x['snap']) for x in r['defs']])
json.dump({'dims': res, 'seg': [list(map(lambda z: z if isinstance(z, int) else list(z), u)) for u in used_seg], 'fill': sorted(used_fill)},
          open('work/dims.json', 'w'), ensure_ascii=False)
print('fills', len(used_fill), 'segs', len(used_seg))
