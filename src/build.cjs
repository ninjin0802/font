// VectorCraft で描いた線（work/sheet.svg）→ にんじん形に肉付け → フォント（out/Ninfont.otf）
// usage: NODE_PATH=<node_modules> node build.cjs
const fs = require("fs"), path = require("path");
const paper = require("paper/dist/paper-core"), opentype = require("opentype.js");
paper.setup(new paper.Size(100, 100));
const ROOT = path.join(__dirname, "..");
// work/sheet-N.svg（VectorCraft で描いた線）と work/manifest-N.json（どの線がどの文字か）を読む
const ORDER = [], cells = [], leaves = [], marks = new Map();
const SMALL = new Set([..."ぁぃぅぇぉっゃゅょゎァィゥェォッャュョヮ"]), isKanji = ch => /[\u4e00-\u9fff]/.test(ch);
const isLatin = ch => /[A-Za-z.,!?'\-:\/&()]/.test(ch); // 英字と半角の記号: 幅は線の端から決める
const ADV = { "%": 820, "（": 520, "）": 520 }; for (const c of "0123456789") ADV[c] = 620;
for (let n = 1; fs.existsSync(path.join(ROOT, `work/manifest-${n}.json`)); n++) {
  const man = JSON.parse(fs.readFileSync(path.join(ROOT, `work/manifest-${n}.json`), "utf8"));
  const svg = fs.readFileSync(path.join(ROOT, `work/sheet-${n}.svg`), "utf8");
  const ds = [...svg.matchAll(/<path d="([^"]+)"[^>]*stroke="#000000"/g)].map(m => m[1]);
  if (ds.length !== man.length) throw new Error(`sheet ${n}: ${ds.length} paths, ${man.length} expected`);
  const base = ORDER.length;
  man.forEach((m, j) => {
    const gi = base + m.cell;
    if (!ORDER[gi]) { ORDER[gi] = m.ch; cells[gi] = []; leaves[gi] = []; }
    const p = new paper.Path(ds[j]);
    const d = Math.min(p.firstSegment.point.getDistance(new paper.Point(m.start)), p.lastSegment.point.getDistance(new paper.Point(m.start)));
    if (d > 14) throw new Error(`sheet ${n} stroke ${j} (${m.ch}) is off by ${d.toFixed(1)}`);
    if (p.lastSegment.point.getDistance(new paper.Point(m.start)) < p.firstSegment.point.getDistance(new paper.Point(m.start)) - 0.01 && m.kind !== "ring") p.reverse();
    p.translate(new paper.Point(-(m.cell % 8) * 110 - 5, -Math.floor(m.cell / 8) * 110 - 5));
    p.data.kind = m.kind;
    (m.kind === "sprout" ? leaves : cells)[gi].push(p);
  });
}
const R = 6.0;
function kindOf(ch, p) { return p.data.kind; }
function radius(kind, t, len, k) {
  if (kind === "ring") return R * 0.6 * k;
  if (kind === "sprout") return 5.4 * k * (0.26 + 0.42 * Math.pow(Math.sin(Math.PI * Math.pow(t, 0.75)), 0.9));
  if (kind === "even") return R * 0.85 * k;
  if (kind === "mark") k *= 0.82;
  if (kind === "ring" && len < 30) return R * 0.75 * k;
  // にんじん: 頭は丸く太く、先へ向かって細くなる
  const taper = 0.56 + 0.44 * Math.pow(1 - t, 1.2);
  const head = 1 + 0.12 * Math.exp(-Math.pow(t * len / 7, 2));
  return R * k * taper * head;
}
function flesh(p, kind, k, passes = 6) {
  const len = p.length, n = Math.max(3, Math.ceil(len / 1.5));
  let pts = [];
  for (let j = 0; j <= n; j++) pts.push(p.getPointAt(Math.min(len * j / n, len - 1e-6)) || p.lastSegment.point);
  // 角をまるめて、やわらかい線にする（端は動かさない）
  if (kind !== "ring") for (let pass = 0; pass < passes; pass++)
    pts = pts.map((q, j) => (j === 0 || j === n) ? q : pts[j - 1].add(q.multiply(2)).add(pts[j + 1]).divide(4));
  let acc = null, prev = null;
  pts.forEach((pt, j) => {
    const t = j / n, r = radius(kind, t, len, k);
    const parts = [new paper.Path.Circle(pt, r)];
    if (prev && pt.getDistance(prev.pt) > 0.01) {
      const nrm = pt.subtract(prev.pt).normalize().rotate(90);
      parts.push(new paper.Path({ segments: [prev.pt.add(nrm.multiply(prev.r)), pt.add(nrm.multiply(r)), pt.subtract(nrm.multiply(r)), prev.pt.subtract(nrm.multiply(prev.r))], closed: true }));
    }
    for (const q of parts) acc = acc ? acc.unite(q, { insert: false }) : q;
    prev = { pt, r };
  });
  return acc;
}
const LEAF_GREEN = [0x5f, 0x8a, 0x4a]; // 葉の色（R,G,B）
const glyphs = [new opentype.Glyph({ name: ".notdef", unicode: 0, advanceWidth: 1000, path: new opentype.Path() }),
                new opentype.Glyph({ name: "space", unicode: 32, advanceWidth: 400, path: new opentype.Path() }),
                new opentype.Glyph({ name: "ideospace", unicode: 0x3000, advanceWidth: 1000, path: new opentype.Path() })];
const layerGlyphs = [], colr = []; // colr: {base, body, leaf}（グリフ番号はあとで決める）
const preview = []; let pvRows = 0;
const uni = (a, b) => (a ? a.unite(b, { insert: false }) : b);
ORDER.forEach((ch, i) => {
  const k = isLatin(ch) ? 0.92 : isKanji(ch) ? Math.max(0.6, Math.min(0.76, 0.88 - 0.014 * cells[i].length)) : SMALL.has(ch) ? 0.85 : cells[i].some(p => p.data.kind === "mark") ? 0.94 : 1;
  if (!cells[i].length) throw new Error("no strokes: " + ch);
  let body = null, leaf = null;
  for (const p of cells[i]) {
    const kind = kindOf(ch, p), f = flesh(p, kind, k, isKanji(ch) ? 3 : 6);
    body = uni(body, f);
  }
  for (const lf of leaves[i]) {
    leaf = uni(leaf, flesh(lf, "sprout", k));
  }
  const narrow = "、。".includes(ch);
  const bb = body.bounds, LSB = 42;
  const adv = isLatin(ch) ? Math.round(bb.width * 10.6 + LSB * 2) : narrow ? 600 : (ADV[ch] || 960), G = isKanji(ch) ? 0.97 : 1.06; // 漢字は線が端まであるので、少し小さく組む
  const X = x => Math.round(isLatin(ch) ? (x - bb.left) * 10 * G + LSB : (narrow ? x * 10 * G - 60 : (x - 50) * 10 * G + adv / 2)), Y = y => Math.round((50 - y) * 10 * G + 355);
  const toPath = src => {
    // 合成でできた細かい点を間引いて、輪郭を軽くする
    const shape = src.clone({ insert: false });
    for (const sp of (shape.children ? shape.children : [shape])) sp.simplify(0.03);
    const op = new opentype.Path();
    for (const sp of (shape.children ? shape.children : [shape])) {
      sp.curves.forEach((c, j) => {
        if (j === 0) op.moveTo(X(c.point1.x), Y(c.point1.y));
        if (c.isStraight()) op.lineTo(X(c.point2.x), Y(c.point2.y));
        else op.curveTo(X(c.point1.x + c.handle1.x), Y(c.point1.y + c.handle1.y), X(c.point2.x + c.handle2.x), Y(c.point2.y + c.handle2.y), X(c.point2.x), Y(c.point2.y));
      });
      op.close();
    }
    return op;
  };
  const hex = ch.codePointAt(0).toString(16).toUpperCase();
  const whole = leaf ? body.unite(leaf, { insert: false }) : body;
  glyphs.push(new opentype.Glyph({ name: "uni" + hex, unicode: ch.codePointAt(0), advanceWidth: adv, path: toPath(whole) }));
  if (leaf) {
    const rec = { base: glyphs.length - 1 };
    layerGlyphs.push(new opentype.Glyph({ name: "uni" + hex + ".leaf", advanceWidth: adv, path: toPath(leaf) })); rec.leaf = layerGlyphs.length - 1;
    layerGlyphs.push(new opentype.Glyph({ name: "uni" + hex + ".body", advanceWidth: adv, path: toPath(body) })); rec.body = layerGlyphs.length - 1;
    colr.push(rec);
  }
  const tr = `transform="translate(${(i % 16) * 110 + 5},${Math.floor(i / 16) * 110 + 5})"`; pvRows = Math.floor(i / 16) + 1;
  if (leaf) preview.push(`<path ${tr} fill="#5f8a4a" d="${leaf.pathData}"/>`);
  preview.push(`<path ${tr} d="${body.pathData}"/>`);
  
});
const nBase = glyphs.length;
glyphs.push(...layerGlyphs);
fs.mkdirSync(path.join(ROOT, "out"), { recursive: true });
const font = new opentype.Font({ familyName: "Ninfont", styleName: "Regular", unitsPerEm: 1000, ascender: 880, descender: -120, glyphs,
  designer: "ninjin", designerURL: "https://2nj.lol/", manufacturer: "ninjin", manufacturerURL: "https://github.com/ninjin0802/font",
  description: "にんふぉんと — にんじんの形をした手書きのフォント", version: "Version 1.201",
  copyright: "Copyright (c) 2026 ninjin (https://2nj.lol/)",
  license: "This font is licensed under the Creative Commons Attribution 4.0 International License (CC BY 4.0). You may use, modify and redistribute it, including commercially, as long as you give credit: Ninfont (c) ninjin (https://2nj.lol/).",
  licenseURL: "https://creativecommons.org/licenses/by/4.0/" });
font.names.fontFamily.ja = "にんふぉんと"; font.names.fullName.ja = "にんふぉんと";
let buf = Buffer.from(font.toArrayBuffer());

// 色の表（COLR / CPAL）を足す: 下に葉（緑）、上に本体（文字色のまま）
function colorTables() {
  const COLR = Buffer.alloc(14 + colr.length * 6 + colr.length * 2 * 4);
  COLR.writeUInt16BE(0, 0); COLR.writeUInt16BE(colr.length, 2); COLR.writeUInt32BE(14, 4);
  COLR.writeUInt32BE(14 + colr.length * 6, 8); COLR.writeUInt16BE(colr.length * 2, 12);
  colr.forEach((r, j) => {
    COLR.writeUInt16BE(r.base, 14 + j * 6); COLR.writeUInt16BE(j * 2, 16 + j * 6); COLR.writeUInt16BE(2, 18 + j * 6);
    const o = 14 + colr.length * 6 + j * 8;
    COLR.writeUInt16BE(nBase + r.leaf, o); COLR.writeUInt16BE(0, o + 2);
    COLR.writeUInt16BE(nBase + r.body, o + 4); COLR.writeUInt16BE(0xffff, o + 6);
  });
  const CPAL = Buffer.alloc(18);
  CPAL.writeUInt16BE(0, 0); CPAL.writeUInt16BE(1, 2); CPAL.writeUInt16BE(1, 4); CPAL.writeUInt16BE(1, 6);
  CPAL.writeUInt32BE(14, 8); CPAL.writeUInt16BE(0, 12);
  CPAL.set([LEAF_GREEN[2], LEAF_GREEN[1], LEAF_GREEN[0], 0xff], 14);
  return { COLR, CPAL };
}
function addTables(src, extra) {
  const n = src.readUInt16BE(4), tables = {};
  for (let j = 0; j < n; j++) {
    const o = 12 + j * 16, tag = src.toString("latin1", o, o + 4);
    tables[tag] = Buffer.from(src.subarray(src.readUInt32BE(o + 8), src.readUInt32BE(o + 8) + src.readUInt32BE(o + 12)));
  }
  Object.assign(tables, extra);
  tables.head.writeUInt32BE(0, 8);
  const tags = Object.keys(tables).sort(), m = tags.length, e = Math.floor(Math.log2(m));
  const sum = b => { let s = 0; const p = Buffer.concat([b, Buffer.alloc((4 - b.length % 4) % 4)]); for (let j = 0; j < p.length; j += 4) s = (s + p.readUInt32BE(j)) >>> 0; return s; };
  const hdr = Buffer.alloc(12 + m * 16); src.copy(hdr, 0, 0, 4);
  hdr.writeUInt16BE(m, 4); hdr.writeUInt16BE(16 << e, 6); hdr.writeUInt16BE(e, 8); hdr.writeUInt16BE(m * 16 - (16 << e), 10);
  let off = hdr.length; const parts = [];
  tags.forEach((tag, j) => {
    const b = tables[tag], o = 12 + j * 16;
    hdr.write(tag, o, "latin1"); hdr.writeUInt32BE(sum(b), o + 4); hdr.writeUInt32BE(off, o + 8); hdr.writeUInt32BE(b.length, o + 12);
    const padded = Buffer.concat([b, Buffer.alloc((4 - b.length % 4) % 4)]); parts.push(padded); off += padded.length;
  });
  const out = Buffer.concat([hdr, ...parts]);
  const headOff = out.readUInt32BE(12 + tags.indexOf("head") * 16 + 8);
  out.writeUInt32BE((0xb1b0afba - sum(out)) >>> 0, headOff + 8);
  return out;
}
buf = addTables(buf, colorTables());
fs.writeFileSync(path.join(ROOT, "out/Ninfont.otf"), buf);
fs.writeFileSync(path.join(ROOT, "out/glyphs.svg"), `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1760 ${pvRows * 110}" fill="#3d332c" fill-rule="nonzero">${preview.join("")}</svg>`);
const chk = opentype.parse(buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.length));
console.log(JSON.stringify(chk.names.fontFamily), JSON.stringify(chk.names.licenseURL), JSON.stringify(chk.names.copyright), "glyphs", chk.glyphs.length, "base", nBase, "check", chk.glyphs.get(nBase).name, chk.glyphs.get(3).name);
