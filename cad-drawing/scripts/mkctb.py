"""依顏色給筆寬、全部出黑的 CTB 產生器（避開 ezdxf save() 的 bug）。
用法：python mkctb.py 輸出.ctb    —— 改 W 字典即可。"""
import sys, zlib, struct, re
from io import StringIO
from ezdxf.addons import acadctb

W = {4: 0.30, 1: 0.25, 30: 0.20, 5: 0.15, 140: 0.05, 3: 0.13, 8: 0.09, 6: 0.40, 7: 0.25, 2: 0.25}
DEFAULT = 0.13
STD = [0.0,0.05,0.09,0.1,0.13,0.15,0.18,0.2,0.25,0.3,0.35,0.4,0.45,0.5,0.53,0.6,0.65,0.7,0.8,0.9,1.0,1.06,1.2,1.4,1.58,2.0,2.11]

ctb = acadctb.new_ctb()
ctb.description = 'color-based lineweights, all black'
m = StringIO(); ctb.write_content(m); t = m.getvalue()

def fix(mm):
    blk = mm.group(0); n = int(re.search(r'name="Color_(\d+)', blk).group(1))
    blk = re.sub(r'lineweight=\d+', 'lineweight=%d' % STD.index(W.get(n, DEFAULT)), blk)
    blk = re.sub(r'  color=-?\d+\n(  mode_color=-?\d+\n)?  color_policy=\d+\n', '  color=-16777216\n  color_policy=5\n', blk)
    return blk
t = re.sub(r' \d+\{\n  name="Color_\d+\n.*?\n \}', fix, t, flags=re.S)
i = t.find('custom_lineweight_table{'); j = t.find('}', i)
t = t[:i] + 'custom_lineweight_table{\n' + ''.join(' %d=%s\n' % (k, v) for k, v in enumerate(STD)) + t[j:]
body = (t + chr(0)).encode('cp1252'); comp = zlib.compress(body, 9)
out = sys.argv[1] if len(sys.argv) > 1 else 'LW.ctb'
with open(out, 'wb') as f:
    f.write(b'PIAFILEVERSION_2.0,CTBVER1,compress\r\npmzlibcodec')
    f.write(struct.pack('<III', zlib.adler32(comp) & 0xffffffff, len(body), len(comp)))
    f.write(comp)
c = acadctb.load(out)
print(out, {k: c[k].get_lineweight() for k in (4, 1, 140, 6, 9)}, 'color', c[4].color)
