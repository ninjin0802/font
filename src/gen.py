#!/usr/bin/env python3
"""骨格 → VectorCraft の鉛筆ツールでなぞるマウスの軌跡（ウィンドウ座標）と、線の一覧。
usage: gen.py sheet scale offx offy outdir  → outdir/strokes-N.json, ../work/manifest-N.json"""
import json, math, os, random, sys
from glyphs import GLYPHS, ORDER, SMALL, NOLEAF, PER_SHEET, VC_COUNT, VC_SHEETS
sheet = int(sys.argv[1]); scale, ox, oy = map(float, sys.argv[2:5]); outdir = sys.argv[5]

def spline(pts, step=1.6):
    """Catmull-Rom。角で区切って、区間ごとになめらかにつなぐ。"""
    segs, cur = [], []
    for p in pts:
        cur.append(p[:2])
        if len(p) > 2 and len(cur) > 1:
            segs.append(cur); cur = [p[:2]]
    if len(cur) > 1: segs.append(cur)
    out = []
    for seg in segs:
        q = [seg[0]] + seg + [seg[-1]]
        for i in range(1, len(q) - 2):
            p0, p1, p2, p3 = q[i-1], q[i], q[i+1], q[i+2]
            n = max(2, int(math.dist(p1, p2) / step))
            for k in range(n):
                t = k / n
                out.append(tuple(0.5 * ((2*p1[j]) + (-p0[j]+p2[j])*t + (2*p0[j]-5*p1[j]+4*p2[j]-p3[j])*t*t + (-p0[j]+3*p1[j]-3*p2[j]+p3[j])*t**3) for j in (0, 1)))
        out.append(seg[-1])
    return out

strokes, manifest = [], []
chars = ORDER[:VC_COUNT][(sheet - 1) * PER_SHEET: sheet * PER_SHEET] if sheet <= VC_SHEETS else ORDER[VC_COUNT:][(sheet - VC_SHEETS - 1) * PER_SHEET: (sheet - VC_SHEETS) * PER_SHEET]
for idx, ch in enumerate(chars):
    rnd = random.Random(ord(ch) * 7 + 1)
    cx, cy = (idx % 8) * 110 + 5, (idx // 8) * 110 + 5
    rot = math.radians(rnd.uniform(-2.5, 2.5)); k = rnd.uniform(0.96, 1.03)
    def place(x, y):
        dx, dy = (x - 50) * k, (y - 50) * k
        x, y = 50 + dx * math.cos(rot) - dy * math.sin(rot), 50 + dx * math.sin(rot) + dy * math.cos(rot)
        return [round((cx + x) * scale + ox, 1), round((cy + y) * scale + oy, 1)], [round(cx + x, 2), round(cy + y, 2)]
    def emit(pts, kind):
        strokes.append([place(x, y)[0] for x, y in pts])
        manifest.append({"ch": ch, "cell": idx, "kind": kind, "start": place(*pts[0])[1]})
    for st in GLYPHS[ch]:
        pts = spline(st["pts"])
        ph = [rnd.uniform(0, 6.28) for _ in range(4)]; amp = 0.0 if st["kind"] == "ring" else 0.5   # 手のゆらぎ
        emit([(x + amp * math.sin(i * 0.23 + ph[0]) + 0.2 * math.sin(i * 0.61 + ph[1]),
               y + amp * math.sin(i * 0.19 + ph[2]) + 0.2 * math.sin(i * 0.53 + ph[3])) for i, (x, y) in enumerate(pts)], st["kind"])
    if ch in NOLEAF: continue
    # 葉っぱ: いちばん上の書き始めに 3 枚
    st = min((s for s in GLYPHS[ch] if s["kind"] == "carrot"), key=lambda s: s["pts"][0][1])
    (x0, y0), (x1, y1) = st["pts"][0][:2], st["pts"][1][:2]
    tl = math.hypot(x1 - x0, y1 - y0); tx, ty = (x1 - x0) / tl, (y1 - y0) / tl
    dx, dy = -tx, -ty - 1.0
    dl = math.hypot(dx, dy); dx, dy = dx / dl, dy / dl
    size = 0.72 if ch in SMALL else 1.0
    r2 = random.Random(ord(ch) * 13 + 5)
    for ang, ln, off in ((-36, 11, -2.6), (2, 15, 0), (38, 11.5, 2.6)):
        a = math.radians(ang + r2.uniform(-7, 7)); ln *= size * r2.uniform(0.9, 1.1)
        ux, uy = dx * math.cos(a) - dy * math.sin(a), dx * math.sin(a) + dy * math.cos(a)
        bx, by = x0 + (-dy) * off * size + ux * 1.5, y0 + dx * off * size + uy * 1.5
        bend = (1 if ang > 0 else -1 if ang < 0 else r2.choice((-1, 1))) * 1.6 * size
        emit([(bx + ux * ln * t + uy * bend * math.sin(math.pi * t), by + uy * ln * t - ux * bend * math.sin(math.pi * t)) for t in (i / 12 for i in range(13))], "sprout")
json.dump(strokes, open(os.path.join(outdir, f"strokes-{sheet}.json"), "w"))
json.dump(manifest, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"../work/manifest-{sheet}.json"), "w"), ensure_ascii=False)
print(sheet, "".join(chars), len(strokes), "strokes", sum(map(len, strokes)), "points")
