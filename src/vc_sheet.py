#!/usr/bin/env python3
"""骨格 → VectorCraft（vectorcraft-cli）で線を引いて work/sheet-N.svg を書き出す。usage: vc_sheet.py N [N...]
VectorCraft の GUI は使わない。線は gen.py が出す座標（ゆらぎ・葉っぱ込み）を、そのままパスにする。"""
import json, os, re, subprocess, sys, tempfile
here = os.path.dirname(os.path.abspath(__file__))
work = os.path.join(here, "..", "work")
for n in sys.argv[1:]:
    with tempfile.TemporaryDirectory() as t:
        subprocess.run([sys.executable, os.path.join(here, "gen.py"), n, "1", "0", "0", t], check=True, cwd=here)
        strokes = json.load(open(os.path.join(t, f"strokes-{n}.json")))
        args = ["vectorcraft-cli", "run", "--cmd", "file.new", "--params", json.dumps({"width": 880, "height": 440, "units": "Pixels"})]
        for st in strokes:
            d = "M" + " L".join(f"{x} {y}" for x, y in st)
            args += ["--cmd", "path.create", "--params", json.dumps({"d": d}),
                     "--cmd", "paint.setFill", "--params", '{"none":true}',
                     "--cmd", "paint.setStroke", "--params", '{"color":"#000000"}']
        raw = os.path.join(t, "raw.svg")
        r = subprocess.run(args + ["--export", raw], capture_output=True, text=True)
        if r.returncode: sys.exit(r.stderr or r.stdout)
        svg = open(raw).read()
    # build.cjs が読む形（<path d="..." fill="none" stroke="#000000"/>）にそろえる
    ds = re.findall(r'<path[^>]*\sd="([^"]+)"', svg)
    if len(ds) != len(strokes): sys.exit(f"sheet {n}: VectorCraft wrote {len(ds)} paths, expected {len(strokes)}")
    with open(os.path.join(work, f"sheet-{n}.svg"), "w") as f:
        f.write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 880 440" width="880" height="440">\n')
        f.writelines(f'<path d="{d}" fill="none" stroke="#000000"/>\n' for d in ds)
        f.write("</svg>\n")
    print("sheet", n, len(ds), "paths via VectorCraft")
