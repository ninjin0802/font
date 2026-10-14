"""VectorCraft の鉛筆ツールで、五・黒・紙の骨格を手書きする（制御チャネルの ui.pointer でマウスと同じに動かす）"""
import json, math, random, socket, sys
def call(m, p):
    with socket.create_connection(("127.0.0.1", 7979), timeout=65) as s:
        s.sendall((json.dumps({"id": 1, "method": m, "params": p}) + "\n").encode()); return json.loads(s.makefile().readline())
C = "c"
GLY = {
 "五": [[(6,10),(50,10),(94,10)], [(48,12),(40,45),(28,92)], [(12,45),(50,45),(79,45),(79,68),(79,92)], [(3,92),(50,92),(97,92)]],
 "黒": [[(20,6),(20,28),(20,48)], [(20,6),(50,5),(80,6,C),(80,28),(80,48)], [(21,27),(50,26),(79,26)], [(50,6),(50,40),(50,74)],
        [(21,48),(50,48),(79,48)], [(24,61),(50,60),(76,60)], [(8,75),(50,74),(92,73)],
        [(18,84),(14,89),(10,94)], [(36,84),(35,89),(34,94)], [(60,84),(62,89),(64,94)], [(80,84),(85,89),(90,94)]],
 "紙": [[(24,4),(18,14),(12,24,C),(20,28),(28,31)], [(32,20),(22,34),(12,47,C),(24,45),(38,42)], [(30,34),(34,39),(38,44)], [(24,46),(24,72),(24,96)],
        [(14,62),(11,71),(8,80)], [(32,62),(35,70),(38,78)],
        [(90,8),(72,13),(54,18)], [(54,18),(54,50),(54,78,C),(60,75),(67,71)], [(46,46),(72,45),(96,43)], [(64,20),(68,40),(76,60),(86,78),(96,92)]],
}
def interp(pts, step=2.0):
    out = []
    for a, b in zip(pts, pts[1:]):
        n = max(2, int(math.dist(a[:2], b[:2]) / step))
        out += [(a[0] + (b[0]-a[0])*k/n, a[1] + (b[1]-a[1])*k/n) for k in range(n)]
    return out + [pts[-1][:2]]
rnd = random.Random(7)
for i, ch in enumerate(GLY):
    ox = i * 110 + 5; oy = 5
    for st in GLY[ch]:
        ph = rnd.uniform(0, 6.28)
        pts = [(ox + x + 0.6*math.sin(j*0.35+ph), oy + y + 0.6*math.cos(j*0.29+ph)) for j, (x, y) in enumerate(interp(st))]
        ev = [{"kind": "down", "x": pts[0][0], "y": pts[0][1], "space": "doc"}] + \
             [{"kind": "drag", "x": x, "y": y, "space": "doc"} for x, y in pts[1:]] + \
             [{"kind": "up", "x": pts[-1][0], "y": pts[-1][1], "space": "doc"}]
        r = call("ui.pointer", {"events": ev})
        if not r.get("ok"): sys.exit(r)
        call("engine.execute", {"command": "select.none", "params": {}})
print("drawn")
