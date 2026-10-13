#!/usr/bin/env python3
"""VectorCraft を使わず、骨格から work/sheet-N.svg を直接つくる。usage: direct.py N [N...]"""
import json, os, subprocess, sys, tempfile
here = os.path.dirname(os.path.abspath(__file__))
work = os.path.join(here, "work") if os.path.isdir(os.path.join(here, "work")) else os.path.join(here, "../work")
for n in sys.argv[1:]:
    with tempfile.TemporaryDirectory() as t:
        subprocess.run([sys.executable, os.path.join(here, "gen.py"), n, "1", "0", "0", t], check=True, cwd=here)
        strokes = json.load(open(os.path.join(t, f"strokes-{n}.json")))
    with open(os.path.join(work, f"sheet-{n}.svg"), "w") as f:
        f.write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 880 440" width="880" height="440">\n')
        for s in strokes:
            f.write('<path d="M' + " L".join(f"{x} {y}" for x, y in s) + '" fill="none" stroke="#000000"/>\n')
        f.write("</svg>\n")
