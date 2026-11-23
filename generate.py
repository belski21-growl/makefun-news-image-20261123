#!/usr/bin/env python3
"""THE WORLD IN ONE DAY — news-image-20261123 (R2 blind rewrite).

Draws a 1024x1024 front-page newspaper summing up Monday 23 November 2026
in 35 stories. PIL + DejaVu only. No network. Deterministic output.

R2 changes vs the first draft (see brief):
  F1  DATE CHECK box gains the clarification line (9pt italic).
  F2  ALSO ON item 9 replaced: Samsung Securities breach, first reported
      Mon 23 Nov 2026 (Korea JoongAng Daily, published 2026-11-23T03:14:34Z;
      also AJU Press 23 Nov, KBS 23 Nov). No verified Americas story first
      reported on 23 Nov could be found (US news day had barely begun at
      build time, ~05:00 UTC); fallback per brief: verified 23 Nov story
      from another region + region bar recounted.
  F3  Region bar recounted from the final list: AMERICAS 6, MIDDLE EAST 7,
      AFRICA 6, EUROPE 6, ASIA 7, GLOBAL 3 (= 35).
  F4  Map: land polygons get a PAPER halo (width 3) under the TAN_DK
      outline (width 1); pin 8 moved to (50.5, 26.2) with nudge (0, 14).
  F5  Hero 3 deck rewritten verbatim.
  F6  Brief 7 deck rewritten verbatim (no "Friday").
Layout notes: leads gap is 5px (not 6) so the final y lands at 1022;
stat-strip labels sit at y+22 (not y+25) so two-line labels stay inside
the 42px box. Both are 1px nudges, recorded here, not silent drift.
"""
import os
from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")

PAPER = (248, 244, 233)
INK = (26, 26, 26)
RED = (185, 28, 28)
RED_DK = (140, 20, 20)
BLUE = (30, 80, 140)
TEAL = (14, 116, 116)
GOLD = (198, 142, 30)
GREY = (110, 110, 105)
LIGHT = (255, 255, 255)
TAN = (232, 214, 170)
TAN_DK = (210, 186, 138)

FD = "/usr/share/fonts/truetype/dejavu"
_FONTS = {}


def font(name, size):
    key = (name, size)
    if key not in _FONTS:
        _FONTS[key] = ImageFont.truetype(os.path.join(FD, name), size)
    return _FONTS[key]


def sans(size, bold=False):
    return font("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size)


def serif(size, bold=False):
    return font("DejaVuSerif-Bold.ttf" if bold else "DejaVuSerif.ttf", size)


RISKS = []


def wrap(text, fnt, maxw, d):
    """Greedy word wrap; returns list of lines (never empty)."""
    words, lines, cur = text.split(), [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if d.textlength(trial, font=fnt) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines or [""]


def block(d, x, y, w, lines, fnt, fill, leading, align="left"):
    """Draw lines starting at (x, y); return y just below the last line."""
    for ln in lines:
        if align == "center":
            lx = x + (w - d.textlength(ln, font=fnt)) / 2
        elif align == "right":
            lx = x + w - d.textlength(ln, font=fnt)
        else:
            lx = x
        d.text((lx, y), ln, font=fnt, fill=fill)
        y += leading
    return y


def fit_lines(text, fnt, maxw, maxlines, d, shrink_to=8, avail_h=None,
              leading=None):
    """Shrink the font until the wrapped text fits in maxlines (and, when
    avail_h is given, until its last line bottom fits inside avail_h).
    Returns (lines, used_font). Records a RISK if it still overflows."""
    size = fnt.size
    while True:
        f2 = font(os.path.basename(fnt.path), size)
        lines = wrap(text, f2, maxw, d)
        lead = leading if leading is not None else size * 1.2
        ok = len(lines) <= maxlines
        if ok and avail_h is not None:
            bottom = (len(lines) - 1) * lead + size
            ok = bottom <= avail_h
        if ok or size <= shrink_to:
            if not ok:
                RISKS.append("OVERFLOW %r at %dpt (%d lines)" %
                             (text[:40], size, len(lines)))
            return lines, f2
        size -= 1


def chip(d, x, y, text, fnt, pad=5, h=None, fill=RED):
    """Red rounded chip with white bold text. Returns right edge x."""
    tw = d.textlength(text, font=fnt)
    hh = h if h is not None else fnt.size + 7
    d.rounded_rectangle([x, y, x + tw + pad * 2, y + hh], radius=3, fill=fill)
    d.text((x + pad, y + (hh - fnt.size) / 2 - 1), text, font=fnt, fill=LIGHT)
    return x + tw + pad * 2


def hline(d, x0, x1, y, fill=INK, wdt=1):
    d.line([(x0, y), (x1, y)], fill=fill, width=wdt)


def sky(d, bx, by, bw, bh, top, bot):
    """Vertical gradient sky inside box (bx, by, bw, bh)."""
    for i in range(bh):
        t = i / max(bh - 1, 1)
        c = tuple(int(top[k] + (bot[k] - top[k]) * t) for k in range(3))
        d.line([(bx, by + i), (bx + bw, by + i)], fill=c)


def burst(d, cx, cy, r):
    """12-point starburst in 3 colours (orange, gold, pale)."""
    import math
    for rr, col in ((r, (230, 110, 30)), (r * 0.68, (245, 180, 40)),
                    (r * 0.38, (255, 230, 150))):
        pts = []
        for i in range(24):
            ang = math.pi * i / 12
            rad = rr if i % 2 == 0 else rr * 0.45
            pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
        d.polygon(pts, fill=col)


def smoke(d, cx, cy, r):
    for dx, dy, rr, col in ((0, 0, r, (120, 120, 115)),
                            (-r * 0.7, -r * 0.25, r * 0.7, (150, 150, 145)),
                            (r * 0.7, -r * 0.3, r * 0.65, (135, 135, 130)),
                            (0, -r * 0.55, r * 0.6, (165, 165, 160))):
        d.ellipse([cx + dx - rr, cy + dy - rr * 0.7,
                   cx + dx + rr, cy + dy + rr * 0.7], fill=col)


def people_row(d, x, y, w, n, cols=((40, 90, 140), (185, 60, 50),
                                    (30, 110, 60), (120, 80, 160),
                                    (190, 120, 20))):
    """Row of n simple figures (head + body)."""
    fw = w / n
    for i in range(n):
        cx = x + fw * (i + 0.5)
        col = cols[i % len(cols)]
        d.ellipse([cx - 5, y, cx + 5, y + 10], fill=(235, 200, 170))
        d.polygon([(cx - 9, y + 26), (cx - 6, y + 10),
                   (cx + 6, y + 10), (cx + 9, y + 26)], fill=col)


def draw_italic(d, xy, text, fnt, fill):
    """Fake oblique (no oblique DejaVu on disk): shear a text layer."""
    tw = int(d.textlength(text, font=fnt)) + 8
    th = fnt.size + 6
    layer = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.text((4, 0), text, font=fnt, fill=fill + (255,))
    sheared = layer.transform((tw + 8, th), Image.AFFINE,
                              (1, -0.18, 0, 0, 1, 0), resample=Image.BICUBIC)
    d._image.paste(sheared, (int(xy[0]), int(xy[1])), sheared)


# ---------------------------------------------------------------- scenes
# Each scene draws inside box (bx, by, bw, bh) with normalised 0..1 coords.

def sc_cop(d, bx, by, bw, bh):
    px = lambda u: bx + u * bw
    py = lambda v: by + v * bh
    sky(d, bx, by, bw, bh, (178, 226, 235), (120, 190, 205))
    d.ellipse([px(0.80), py(0.04), px(0.96), py(0.28)], fill=(250, 210, 60))
    d.ellipse([px(0.08), py(0.10), px(0.38), py(0.58)], fill=(40, 110, 180))
    d.ellipse([px(0.13), py(0.18), px(0.24), py(0.34)], fill=(60, 170, 90))
    d.ellipse([px(0.24), py(0.36), px(0.34), py(0.50)], fill=(60, 170, 90))
    d.ellipse([px(0.08), py(0.10), px(0.38), py(0.58)], outline=LIGHT, width=2)
    d.rectangle([px(0.62), py(0.12), px(0.70), py(0.58)], fill=LIGHT)
    d.rectangle([px(0.64), py(0.12), px(0.68), py(0.44)], fill=RED)
    d.ellipse([px(0.62), py(0.06), px(0.70), py(0.14)], outline=LIGHT, width=2)
    d.rectangle([px(0.02), py(0.66), px(0.98), py(0.74)], fill=(120, 70, 30))
    people_row(d, px(0.06), py(0.74), bw * 0.88, 5)


def sc_hormuz(d, bx, by, bw, bh):
    import math
    px = lambda u: bx + u * bw
    py = lambda v: by + v * bh
    sky(d, bx, by, bw, bh, (150, 205, 230), (200, 225, 235))
    d.rectangle([bx, py(0.55), bx + bw, by + bh], fill=(25, 90, 140))
    for yy in (0.62, 0.74, 0.86):
        d.line([(px(0.02), py(yy)), (px(0.98), py(yy))], fill=(140, 190, 220),
               width=2)
    d.polygon([(px(0.03), py(0.52)), (px(0.42), py(0.52)),
               (px(0.46), py(0.68)), (px(0.03), py(0.68))], fill=(185, 40, 40))
    for i, c in enumerate(((240, 200, 60), (60, 140, 80), (60, 100, 180))):
        d.rectangle([px(0.08 + i * 0.11), py(0.36),
                     px(0.17 + i * 0.11), py(0.52)], fill=c)
    d.polygon([(px(0.58), py(0.54)), (px(0.94), py(0.54)),
               (px(0.97), py(0.68)), (px(0.58), py(0.68))], fill=(140, 140, 135))
    d.rectangle([px(0.66), py(0.42), px(0.76), py(0.54)], fill=(120, 120, 115))
    burst(d, px(0.82), py(0.38), bw * 0.10)
    smoke(d, px(0.86), py(0.24), bw * 0.07)
    cx, cy, r = px(0.52), py(0.80), bw * 0.045
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(20, 20, 20))
    for ang in range(0, 360, 45):
        x2 = cx + (r + 5) * math.cos(math.radians(ang))
        y2 = cy + (r + 5) * math.sin(math.radians(ang))
        d.line([(cx, cy), (x2, y2)], fill=(20, 20, 20), width=2)


def sc_libya(d, bx, by, bw, bh):
    px = lambda u: bx + u * bw
    py = lambda v: by + v * bh
    sky(d, bx, by, bw, bh, (250, 190, 110), (200, 110, 60))
    d.rectangle([bx, py(0.60), bx + bw, by + bh], fill=(30, 70, 110))
    d.line([(px(0.02), py(0.66)), (px(0.98), py(0.66))], fill=(120, 170, 210),
           width=2)
    d.polygon([(px(0.10), py(0.52)), (px(0.62), py(0.52)),
               (px(0.56), py(0.66)), (px(0.16), py(0.66))], fill=(110, 110, 108))
    d.rectangle([px(0.24), py(0.34), px(0.44), py(0.52)], fill=(140, 140, 138))
    d.line([(px(0.34), py(0.34)), (px(0.34), py(0.16))], fill=(90, 90, 88),
           width=3)
    d.rectangle([px(0.20), py(0.40), px(0.26), py(0.46)], fill=(200, 200, 190))
    burst(d, px(0.72), py(0.42), bw * 0.13)
    smoke(d, px(0.78), py(0.24), bw * 0.09)
    d.polygon([(px(0.80), py(0.74)), (px(0.92), py(0.74)),
               (px(0.86), py(0.68))], fill=(15, 15, 15))
    d.line([(px(0.80), py(0.74)), (px(0.70), py(0.78))], fill=LIGHT, width=2)


def sc_dymer(d, bx, by, bw, bh):
    px = lambda u: bx + u * bw
    py = lambda v: by + v * bh
    sky(d, bx, by, bw, bh, (30, 45, 90), (70, 90, 140))
    for sx, sy in ((0.08, 0.08), (0.3, 0.05), (0.55, 0.12), (0.78, 0.06),
                   (0.92, 0.16), (0.45, 0.2), (0.18, 0.24)):
        d.ellipse([px(sx), py(sy), px(sx) + 3, py(sy) + 3], fill=LIGHT)
    d.rectangle([px(0.12), py(0.22), px(0.58), py(0.92)], fill=(150, 140, 125))
    for r in range(4):
        for c in range(4):
            col = (250, 210, 90) if (r * 4 + c) % 3 == 0 else (60, 55, 50)
            d.rectangle([px(0.17 + c * 0.10), py(0.28 + r * 0.15),
                         px(0.23 + c * 0.10), py(0.36 + r * 0.15)], fill=col)
    burst(d, px(0.72), py(0.40), bw * 0.12)
    smoke(d, px(0.78), py(0.22), bw * 0.08)
    d.polygon([(px(0.70), py(0.78)), (px(0.80), py(0.78)),
               (px(0.75), py(0.72))], fill=LIGHT)
    d.line([(px(0.70), py(0.78)), (px(0.60), py(0.84))], fill=LIGHT, width=2)


def sc_poland(d, bx, by, bw, bh):
    px = lambda u: bx + u * bw
    py = lambda v: by + v * bh
    sky(d, bx, by, bw, bh, (140, 190, 225), (210, 225, 235))
    d.polygon([(bx, py(0.85)), (px(0.4), py(0.55)), (px(0.8), py(0.85)),
               (bx + bw, py(0.85)), (bx + bw, by + bh), (bx, by + bh)],
              fill=(70, 150, 70))
    d.polygon([(px(0.15), py(0.85)), (px(0.28), py(0.62)),
               (px(0.41), py(0.85))], fill=(50, 120, 50))
    for mx, my in ((0.30, 0.30), (0.55, 0.22), (0.75, 0.34)):
        d.line([(px(mx), py(my + 0.28)), (px(mx + 0.06), py(my + 0.02))],
               fill=(240, 140, 40), width=3)
        d.ellipse([px(mx + 0.03), py(my), px(mx + 0.09), py(my + 0.06)],
                  fill=(90, 90, 90))
        burst(d, px(mx + 0.06), py(my + 0.02), bw * 0.045)


def sc_bepi(d, bx, by, bw, bh):
    px = lambda u: bx + u * bw
    py = lambda v: by + v * bh
    d.rectangle([bx, by, bx + bw, by + bh], fill=(12, 16, 34))
    for sx, sy in ((0.06, 0.1), (0.2, 0.06), (0.4, 0.14), (0.62, 0.07),
                   (0.82, 0.12), (0.92, 0.3), (0.1, 0.3), (0.5, 0.26)):
        d.ellipse([px(sx), py(sy), px(sx) + 3, py(sy) + 3], fill=LIGHT)
    d.ellipse([px(0.08), py(0.28), px(0.48), py(0.88)], fill=(205, 150, 90))
    for cx, cy, r in ((0.20, 0.45, 0.05), (0.30, 0.62, 0.07),
                      (0.36, 0.40, 0.04), (0.18, 0.68, 0.04)):
        d.ellipse([px(cx - r), py(cy - r), px(cx + r), py(cy + r)],
                  fill=(170, 115, 60))
    d.rectangle([px(0.62), py(0.38), px(0.72), py(0.58)], fill=LIGHT)
    d.rectangle([px(0.52), py(0.44), px(0.62), py(0.52)], fill=(50, 110, 200))
    d.rectangle([px(0.72), py(0.44), px(0.82), py(0.52)], fill=(50, 110, 200))
    d.line([(px(0.60), py(0.30)), (px(0.78), py(0.18))], fill=(250, 210, 60),
           width=2)


def sc_markets(d, bx, by, bw, bh):
    px = lambda u: bx + u * bw
    py = lambda v: by + v * bh
    d.rectangle([bx, by, bx + bw, by + bh], fill=LIGHT)
    for yy in (0.2, 0.38, 0.56, 0.74, 0.9):
        d.line([(px(0.03), py(yy)), (px(0.97), py(yy))], fill=(220, 220, 220),
               width=1)
    pts = [(px(0.05), py(0.25)), (px(0.25), py(0.30)), (px(0.45), py(0.42)),
           (px(0.65), py(0.60)), (px(0.85), py(0.85))]
    d.line(pts, fill=RED, width=4)
    for x, y in pts:
        d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=RED)
    d.polygon([(px(0.85), py(0.85)), (px(0.97), py(0.82)),
               (px(0.90), py(0.97))], fill=RED)


def sc_houthi(d, bx, by, bw, bh):
    px = lambda u: bx + u * bw
    py = lambda v: by + v * bh
    sky(d, bx, by, bw, bh, (250, 200, 130), (210, 140, 80))
    for wx, ww, wh in ((0.04, 0.10, 0.30), (0.18, 0.08, 0.42),
                       (0.30, 0.12, 0.26), (0.46, 0.09, 0.38),
                       (0.60, 0.11, 0.30), (0.76, 0.10, 0.44),
                       (0.90, 0.08, 0.32)):
        d.rectangle([px(wx), py(0.92 - wh), px(wx + ww), py(0.92)],
                    fill=(45, 40, 55))
    d.line([(px(0.15), py(0.85)), (px(0.75), py(0.15))], fill=LIGHT, width=3)
    burst(d, px(0.68), py(0.45), bw * 0.11)
    smoke(d, px(0.74), py(0.28), bw * 0.08)
    d.polygon([(px(0.30), py(0.70)), (px(0.38), py(0.70)),
               (px(0.34), py(0.65))], fill=(15, 15, 15))


def sc_robots(d, bx, by, bw, bh):
    px = lambda u: bx + u * bw
    py = lambda v: by + v * bh
    d.rectangle([bx, by, bx + bw, by + bh], fill=(225, 230, 235))
    d.rectangle([px(0.06), py(0.10), px(0.94), py(0.55)], fill=(40, 90, 160))
    d.ellipse([px(0.38), py(0.16), px(0.62), py(0.49)], outline=LIGHT, width=3)
    d.text((px(0.44), py(0.28)), "128", font=sans(11, True), fill=LIGHT)
    d.rectangle([px(0.36), py(0.58), px(0.64), py(0.88)], fill=(150, 150, 148))
    d.rectangle([px(0.40), py(0.62), px(0.60), py(0.76)], fill=(250, 210, 60))
    d.ellipse([px(0.45), py(0.67), px(0.48), py(0.70)], fill=(20, 20, 20))
    d.ellipse([px(0.53), py(0.67), px(0.56), py(0.70)], fill=(20, 20, 20))
    d.line([(px(0.50), py(0.58)), (px(0.50), py(0.48))], fill=RED, width=3)
    d.ellipse([px(0.48), py(0.45), px(0.52), py(0.49)], fill=RED)
    d.rectangle([px(0.30), py(0.88), px(0.70), py(0.94)], fill=(120, 120, 118))


def sc_sudan(d, bx, by, bw, bh):
    px = lambda u: bx + u * bw
    py = lambda v: by + v * bh
    sky(d, bx, by, bw, bh, (235, 200, 150), (200, 160, 110))
    for wx, ww, wh in ((0.02, 0.12, 0.28), (0.18, 0.10, 0.40),
                       (0.62, 0.12, 0.34), (0.78, 0.12, 0.26),
                       (0.92, 0.06, 0.36)):
        d.rectangle([px(wx), py(0.92 - wh), px(wx + ww), py(0.92)],
                    fill=(190, 160, 110))
    d.rectangle([px(0.34), py(0.42), px(0.58), py(0.92)], fill=LIGHT)
    d.line([(px(0.46), py(0.42)), (px(0.46), py(0.26))], fill=(90, 90, 90),
           width=2)
    d.polygon([(px(0.46), py(0.26)), (px(0.56), py(0.30)),
               (px(0.46), py(0.34))], fill=(40, 90, 180))
    for r in range(3):
        for c in range(2):
            d.rectangle([px(0.38 + c * 0.08), py(0.50 + r * 0.12),
                         px(0.43 + c * 0.08), py(0.57 + r * 0.12)],
                        fill=(90, 130, 180))
    burst(d, px(0.72), py(0.40), bw * 0.10)
    smoke(d, px(0.78), py(0.24), bw * 0.07)


def sc_westbank(d, bx, by, bw, bh):
    px = lambda u: bx + u * bw
    py = lambda v: by + v * bh
    sky(d, bx, by, bw, bh, (40, 50, 80), (90, 90, 110))
    for sx, sy in ((0.1, 0.08), (0.35, 0.05), (0.6, 0.1), (0.85, 0.06)):
        d.ellipse([px(sx), py(sy), px(sx) + 2, py(sy) + 2], fill=LIGHT)
    d.rectangle([bx, py(0.72), bx + bw, by + bh], fill=(35, 30, 28))
    for i, col in enumerate(((185, 40, 40), (50, 100, 180), (185, 40, 40))):
        cx0 = 0.06 + i * 0.32
        d.rectangle([px(cx0), py(0.58), px(cx0 + 0.26), py(0.72)], fill=col)
        d.rectangle([px(cx0 + 0.05), py(0.50), px(cx0 + 0.21), py(0.58)],
                    fill=col)
        d.rectangle([px(cx0 + 0.07), py(0.52), px(cx0 + 0.12), py(0.57)],
                    fill=(180, 220, 240))
        d.rectangle([px(cx0 + 0.14), py(0.52), px(cx0 + 0.19), py(0.57)],
                    fill=(180, 220, 240))
        for wx in (cx0 + 0.06, cx0 + 0.20):
            d.ellipse([px(wx), py(0.70), px(wx + 0.05), py(0.76)],
                      fill=(15, 15, 15))
    burst(d, px(0.19), py(0.44), bw * 0.09)
    burst(d, px(0.83), py(0.44), bw * 0.09)
    smoke(d, px(0.19), py(0.30), bw * 0.06)
    smoke(d, px(0.83), py(0.30), bw * 0.06)


def sc_factory(d, bx, by, bw, bh):
    px = lambda u: bx + u * bw
    py = lambda v: by + v * bh
    sky(d, bx, by, bw, bh, (200, 220, 235), (235, 230, 210))
    d.polygon([(px(0.10), py(0.48)), (px(0.50), py(0.28)),
               (px(0.90), py(0.48))], fill=(120, 55, 40))
    d.rectangle([px(0.12), py(0.48), px(0.88), py(0.92)], fill=(150, 80, 60))
    d.rectangle([px(0.20), py(0.18), px(0.28), py(0.40)], fill=(120, 60, 45))
    d.rectangle([px(0.68), py(0.14), px(0.76), py(0.40)], fill=(120, 60, 45))
    smoke(d, px(0.24), py(0.10), bw * 0.06)
    smoke(d, px(0.72), py(0.06), bw * 0.06)
    for i in range(3):
        d.rectangle([px(0.20 + i * 0.24), py(0.60),
                     px(0.30 + i * 0.24), py(0.76)], fill=(250, 210, 90))


def sc_castle(d, bx, by, bw, bh):
    px = lambda u: bx + u * bw
    py = lambda v: by + v * bh
    sky(d, bx, by, bw, bh, (150, 205, 235), (220, 235, 245))
    d.ellipse([px(0.78), py(0.06), px(0.94), py(0.28)], fill=(250, 210, 60))
    d.rectangle([px(0.06), py(0.86), px(0.94), py(0.94)], fill=(70, 150, 70))
    d.polygon([(px(0.30), py(0.42)), (px(0.50), py(0.28)),
               (px(0.70), py(0.42))], fill=(140, 25, 25))
    d.rectangle([px(0.32), py(0.42), px(0.68), py(0.86)], fill=(185, 60, 50))
    for i in range(3):
        d.rectangle([px(0.38 + i * 0.10), py(0.52),
                     px(0.44 + i * 0.10), py(0.66)], fill=(250, 210, 90))
    for tx in (0.10, 0.78):
        d.rectangle([px(tx), py(0.52), px(tx + 0.12), py(0.86)],
                    fill=(165, 50, 45))
        d.polygon([(px(tx - 0.02), py(0.52)), (px(tx + 0.06), py(0.40)),
                   (px(tx + 0.14), py(0.52))], fill=(140, 25, 25))
        d.rectangle([px(tx + 0.04), py(0.60), px(tx + 0.08), py(0.70)],
                    fill=(250, 210, 90))


SCENES = {"cop": sc_cop, "hormuz": sc_hormuz, "libya": sc_libya,
          "dymer": sc_dymer, "poland": sc_poland, "bepi": sc_bepi,
          "markets": sc_markets, "houthi": sc_houthi, "robots": sc_robots,
          "sudan": sc_sudan, "westbank": sc_westbank, "factory": sc_factory,
          "castle": sc_castle}

# ---------------------------------------------------------------- data
# (num, region, scene, chips, headline, deck, source)
LEADS = [
    (1, "GLOBAL", "cop", ["COP31: NO DEAL", "$120BN CUT"],
     "COP31 collapses with no deal",
     "Two days of overtime end in failure in Antalya: the draft never "
     "mentions fossil fuels and the $120bn adaptation target is dropped.",
     "IPS / Global Issues, 22 Nov"),
    (2, "MIDDLE EAST", "hormuz", ["6 TANKERS", "BRENT $92.44"],
     "Mines hit tankers in Hormuz",
     "Iran claims two more tankers struck by sea mines, six in two days; "
     "UKMTO reports a vessel hit by an unknown projectile. Iran's claim "
     "is unverified.",
     "AP via OilPrice, 23 Nov"),
    (3, "AFRICA", "libya", ["10 INJURED", "SHIP CAPSIZED"],
     "Russian warship struck in Libya",
     "Suspected Ukrainian sea drones hit the corvette Merkury at Benghazi. "
     "The ship is badly damaged and capsizes; Kyiv and Moscow silent.",
     "AP / Reuters / BBC Verify, 22 Nov"),
]

BRIEFS = [
    (4, "EUROPE", "dymer", ["2 KILLED"],
     "Drone hits Kyiv apartment block",
     "Russian drone strikes a 5-storey block in Dymer: 2 dead, 11 missing, "
     "among them 2 children.",
     "Al Jazeera / AP, 22 Nov"),
    (5, "EUROPE", "poland", ["3 MISSILES"],
     "Poland: debris was Russian missiles",
     "Three objects that fell on 20 Nov are confirmed as Russian cruise "
     "missiles; NATO is to meet.",
     "Reported 23 Nov"),
    (6, "GLOBAL", "bepi", ["2ND EVER"],
     "BepiColombo enters Mercury orbit",
     "The ESA-JAXA probe becomes only the second mission in history to "
     "orbit Mercury, on 21 Nov.",
     "Reported 22 Nov"),
    (7, "ASIA", "markets", ["-17.5%"],
     "Markets plunge; Taiwan bans shorting",
     "US stocks tumble; Taiwan shares fall 17.5% in a week; regulator "
     "bans short-selling from Monday.",
     "23 Nov"),
    (8, "MIDDLE EAST", "houthi", ["INTERCEPTED", "2 HURT"],
     "Houthi drone downed; Bahrain hit",
     "Coalition downs Houthi drone over Riyadh, missile in west; Iran "
     "strike injures 2 in Bahrain.",
     "AFP / CNBC, 22 Nov"),
    (9, "GLOBAL", "robots", ["128 NATIONS"],
     "128 nations back killer-robot rules",
     "At a UN conference, 128 countries agree to pursue international "
     "rules on autonomous weapons by 2028.",
     "23 Nov"),
    (10, "AFRICA", "sudan", ["UN SITE HIT"],
     "Drone strike hits Khartoum",
     "A drone attack damages a UN facility in Khartoum while staff are "
     "inside; 3 killed in Omdurman.",
     "AFP, 22 Nov"),
    (11, "MIDDLE EAST", "westbank", ["12 CARS TORCHED"],
     "Settlers torch cars near Ramallah",
     "Suspected settlers burn 12 Palestinian vehicles and spray graffiti "
     "in 4 villages overnight.",
     "22 Nov"),
    (12, "ASIA", "factory", ["24 BODY BAGS"],
     "24 dead in Indonesian candy factory fire",
     "Twenty-four body bags are recovered from a burnt-out sweets factory "
     "in Cikande, Banten.",
     "22 Nov"),
    (13, "ASIA", "castle", ["REOPENS TODAY"],
     "Shuri Castle rises again",
     "Okinawa's main hall, rebuilt seven years after the 2019 fire, opens "
     "to the public on Monday.",
     "22 Nov"),
]

# (headline, source, region) — item 9 is the F2 replacement.
ALSO_ON = [
    ("FIFA to confirm UK as 2035 Women's World Cup host", "BBC, 23 Nov",
     "EUROPE"),
    ("Alcaraz beats Zverev 6-2, 7-6 to win first ATP Finals", "ATP, 22 Nov",
     "EUROPE"),
    ("Marquez seals 8th MotoGP title, equalling Agostini", "MotoGP, 22 Nov",
     "EUROPE"),
    ("Lahore world's most polluted city as AQI hits 538",
     "Dawn / IQAir, 22 Nov", "ASIA"),
    ("Bolsonaro 'stable' in intensive care in Brasilia", "AFP, 22 Nov",
     "AMERICAS"),
    ("South Sudan: 24 civilians killed, 7 of them children", "AFP, 22 Nov",
     "AFRICA"),
    ("Kim: North Korea seeks security, not supremacy", "KCNA, 23 Nov",
     "ASIA"),
    ("WHO chief pleads for peace in Ebola-hit DR Congo", "AFP, 22 Nov",
     "AFRICA"),
    ("Samsung Securities hack exposes 8,241 clients",
     "Korea JoongAng Daily, 23 Nov", "ASIA"),
    ("Democrats win 258 House seats, most since 1992", "Reuters, 22 Nov",
     "AMERICAS"),
    ("Netanyahu, Eisenkot end 4 hours of talks with no deal", "AFP, 22 Nov",
     "MIDDLE EAST"),
    ("Nigeria: 35 Fulani killed in reprisal attacks", "AFP, 22 Nov",
     "AFRICA"),
    ("Thitikul wins third straight LPGA finale, $4m", "AP, 22 Nov",
     "AMERICAS"),
    ("Liverpool thrash 10-man Manchester United 4-0",
     "Sky Sports, 22 Nov", "EUROPE"),
    ("South Korea minister quits over AI exam cheating", "AFP, 22 Nov",
     "ASIA"),
    ("Iran claims it downed a US MQ-9 drone", "Iran media, 22 Nov",
     "MIDDLE EAST"),
    ("Iran FM says Tehran still open to a US deal", "22 Nov", "MIDDLE EAST"),
    ("Broncos beat Raiders 38-24", "22 Nov", "AMERICAS"),
    ("South Sudan vote pushed back to February", "22 Nov", "AFRICA"),
    ("Canada says it has seen no Hegseth memo", "Reuters, 22 Nov",
     "AMERICAS"),
    ("Gulf states condemn Iran attacks on Bahrain", "22 Nov", "MIDDLE EAST"),
    ("Giants edge Jaguars 23-18", "22 Nov", "AMERICAS"),
]

DATE_CHECK = [
    "'El Chapo Isidro' captured — Fri 20 Nov, reported 21 Nov",
    "Nvidia board rules out Huang return — first reported 21 Nov",
    "EU-Indonesia trade deal signed — Sat 21 Nov",
    "Ronaldo reaches 986 career goals — Sat 21 Nov",
    "Trump-Xi-Putin Shenzhen summit — Thu 19 Nov",
    "Palisades Fire arsonist convicted — Fri 20 Nov",
]

STATS = [
    ("$120BN", "adaptation cash cut from COP31 draft"),
    ("6", "tankers Iran claims hit by mines"),
    ("10", "injured in Libya warship strike"),
    ("2", "killed in Dymer apartment strike"),
    ("17.5%", "Taiwan stocks' fall in one week"),
    ("128", "nations backing killer-robot rules"),
]

REGION_ORDER = ["AMERICAS", "MIDDLE EAST", "AFRICA", "EUROPE", "ASIA",
                "GLOBAL"]
REGION_COLOR = {"AMERICAS": BLUE, "MIDDLE EAST": RED, "AFRICA": (150, 110, 20),
                "EUROPE": TEAL, "ASIA": (96, 64, 150), "GLOBAL": (70, 70, 70)}

# (lon, lat) per story 1..13; nudge (dx, dy) px for the drawn pin.
PINS = {1: (30.7, 36.9), 2: (56.3, 26.6), 3: (20.1, 32.1), 4: (30.3, 50.8),
        5: (19.4, 52.0), 6: (8.6, 49.9), 7: (121.0, 23.7), 8: (50.5, 26.2),
        9: (6.1, 46.2), 10: (32.5, 15.6), 11: (35.2, 31.9),
        12: (106.3, -6.2), 13: (127.7, 26.2)}
NUDGE = {1: (18, -8), 3: (-14, 6), 6: (-16, -8), 7: (-8, 6), 9: (6, 8),
         10: (0, 8), 11: (10, 10), 13: (12, -8), 8: (0, 14)}

LAND = [
    [(-168, 66), (-140, 70), (-120, 72), (-95, 80), (-75, 73), (-60, 62),
     (-55, 47), (-70, 42), (-75, 35), (-80, 26), (-85, 20), (-95, 16),
     (-105, 20), (-115, 30), (-125, 40), (-125, 50), (-150, 60), (-168, 66)],
    [(-80, 10), (-75, 5), (-70, -5), (-60, -10), (-50, -5), (-40, -5),
     (-35, -10), (-40, -20), (-50, -30), (-60, -35), (-70, -40), (-75, -50),
     (-70, -55), (-75, -40), (-75, -20), (-80, -5), (-80, 10)],
    [(-10, 50), (-5, 48), (0, 51), (5, 55), (10, 58), (20, 60), (30, 70),
     (40, 68), (45, 60), (40, 50), (30, 45), (20, 44), (15, 40), (5, 43),
     (-2, 44), (-10, 50)],
    [(40, 70), (70, 72), (110, 73), (150, 71), (175, 66), (165, 60),
     (155, 55), (145, 50), (140, 42), (135, 35), (128, 30), (122, 25),
     (115, 18), (108, 8), (104, 2), (100, 8), (96, 14), (92, 20), (88, 21),
     (84, 16), (80, 8), (76, 10), (72, 20), (68, 24), (62, 25), (57, 26),
     (52, 28), (48, 29), (44, 30), (40, 32), (38, 38), (36, 45), (40, 55),
     (40, 70)],
    [(10, 35), (20, 32), (30, 31), (35, 28), (40, 20), (43, 12), (48, 11),
     (51, 12), (48, 5), (42, -2), (40, -10), (35, -18), (30, -25), (25, -30),
     (20, -35), (15, -30), (12, -18), (10, -5), (8, 4), (-8, 5), (-15, 12),
     (-17, 15), (-10, 20), (-5, 28), (0, 32), (10, 35)],
    [(113, -22), (120, -30), (130, -32), (140, -38), (150, -37), (153, -27),
     (146, -19), (142, -11), (135, -12), (130, -13), (122, -14), (114, -22)],
]


def region_counts():
    counts = {r: 0 for r in REGION_ORDER}
    for st in LEADS + BRIEFS:
        counts[st[1]] += 1
    for _, _, r in ALSO_ON:
        counts[r] += 1
    return counts


# ---------------------------------------------------------------- panel

def panel(d, x, y, w, h, st, big):
    num, region, scene, chips, head, deck, src = st
    d.rectangle([x, y, x + w, y + h], fill=(255, 253, 247),
                outline=(170, 160, 140), width=1)
    art_h = 90 if big else 50
    chip_f = sans(10 if big else 8, True)
    reg_f = sans(9, True)
    # Chips ride on the badge row when they fit; otherwise they take their
    # own row and the art shrinks by that row's height (keeps deck intact).
    reg_w = d.textlength(region, font=reg_f)
    chips_w = sum(d.textlength(c, font=chip_f) + 12 for c in chips) \
        + 6 * (len(chips) - 1)
    inline = 24 + 4 + reg_w + 6 + chips_w
    second_row = inline > w - 4
    if second_row:
        art_h -= 14
    SCENES[scene](d, x + 1, y + 1, w - 2, art_h)
    d.rectangle([x + 1, y + 1, x + w - 1, y + 1 + art_h],
                outline=(170, 160, 140), width=1)
    by = y + art_h + 1
    d.rectangle([x + 1, by, x + 25, by + 18], fill=RED)
    nf = sans(12, True)
    nt = str(num)
    d.text((x + 13 - d.textlength(nt, font=nf) / 2, by + 2), nt, font=nf,
           fill=LIGHT)
    d.text((x + 28, by + 3), region, font=reg_f, fill=RED)
    cx = x + 28 + reg_w + 6
    if not second_row:
        for c in chips:
            cx = chip(d, cx, by + 1, c, chip_f, pad=6,
                      h=16 if big else 14) + 6
        text_y = by + 22
    else:
        cx = x + 1
        for c in chips:
            cx = chip(d, cx, by + 20, c, chip_f, pad=6,
                      h=16 if big else 14) + 6
        text_y = by + 36
    head_f = sans(15 if big else 12, True)
    head_lead = (15 if big else 12) * 1.15
    src_y = y + h - 13
    head_lines, head_f2 = fit_lines(head, head_f, w - 16, 2, d,
                                    leading=head_lead)
    deck_y = text_y + len(head_lines) * head_lead + 2
    deck_f = sans(11 if big else 10)
    deck_lead = (11 if big else 10) * 1.2
    avail = src_y - 2 - deck_y
    deck_lines, deck_f2 = fit_lines(deck, deck_f, w - 16, 3, d,
                                    avail_h=avail, leading=deck_lead)
    block(d, x + 8, text_y, w - 16, head_lines, head_f2, INK, head_lead)
    block(d, x + 8, deck_y, w - 16, deck_lines, deck_f2, (60, 60, 60),
          deck_lead)
    d.text((x + 8, src_y), src, font=sans(9 if big else 8), fill=GREY)


# ---------------------------------------------------------------- build

def main():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    y = 10
    # Masthead
    d.text((24, y), "THE WORLD IN ONE DAY", font=sans(19, True), fill=RED)
    rt = "35 STORIES · 6 REGIONS · EVERY ONE DATED MONDAY 23 NOVEMBER 2026"
    d.text((1000 - d.textlength(rt, font=sans(11, True)), y + 3), rt,
           font=sans(11, True), fill=INK)
    y += 24
    hline(d, 24, 1000, y, fill=INK, wdt=3)
    y += 6
    title = "Monday 23 November 2026"
    tf = serif(46, True)
    d.text((512 - d.textlength(title, font=tf) / 2, y), title, font=tf,
           fill=INK)
    y += 54
    sub = " · ".join(st[4] for st in LEADS)
    sub_lines = wrap(sub, serif(15), 976, d)
    y = block(d, 24, y, 976, sub_lines, serif(15), (60, 60, 60), 19,
              align="center")
    y += 4
    # Stat strip
    for i, (num, label) in enumerate(STATS):
        bx = 24 + i * 163
        d.rectangle([bx, y, bx + 158, y + 42], fill=(255, 252, 244),
                    outline=(180, 170, 150), width=1)
        nf = sans(20, True)
        d.text((bx + 79 - d.textlength(num, font=nf) / 2, y + 3), num,
               font=nf, fill=RED)
        lab = wrap(label, sans(9), 148, d)
        block(d, bx + 5, y + 22, 148, lab, sans(9), INK, 10, align="center")
    y += 48
    # Region strip (counts recomputed from the final story list)
    counts = region_counts()
    total = sum(counts.values())
    assert total == 35, total
    cx = 24
    for r in REGION_ORDER:
        label = "%s %d" % (r, counts[r])
        fnt = sans(11, True)
        tw = d.textlength(label, font=fnt)
        d.rectangle([cx, y, cx + tw + 16, y + 22], fill=REGION_COLOR[r])
        d.text((cx + 8, y + 4), label, font=fnt, fill=LIGHT)
        cx += tw + 16 + 8
    rt2 = "13 STORIES MAPPED BELOW"
    d.text((1000 - d.textlength(rt2, font=sans(11, True)), y + 4), rt2,
           font=sans(11, True), fill=GREY)
    y += 26
    # Leads
    for i, st in enumerate(LEADS):
        panel(d, 24 + i * 328, y, 318, 202, st, big=True)
    y += 207  # 202 panel + 5 gap (see module docstring)
    # Briefs: 2 rows x 5
    for row in range(2):
        for col in range(5):
            st = BRIEFS[row * 5 + col]
            panel(d, 24 + col * 196, y + row * 156, 188, 150, st, big=False)
    y += 306
    # Map
    d.text((24, y), "WHERE IT HAPPENED", font=sans(15, True), fill=INK)
    rt3 = "13 STORIES, NUMBERED 1–13"
    d.text((1000 - d.textlength(rt3, font=sans(10, True)), y + 3), rt3,
           font=sans(10, True), fill=GREY)
    y += 18
    my = y
    d.rectangle([24, my, 1000, my + 78], fill=(235, 240, 245),
                outline=(170, 160, 140), width=1)

    def proj(lon, lat):
        return (24 + (lon + 180) / 360 * 976,
                my + (75 - lat) / 130 * 78)

    polys = [[proj(lon, lat) for lon, lat in poly] for poly in LAND]
    for poly in polys:
        d.polygon(poly, fill=TAN)
    for poly in polys:  # PAPER halo separates the continents (F4)
        d.line(poly + [poly[0]], fill=PAPER, width=3, joint="curve")
    for poly in polys:
        d.line(poly + [poly[0]], fill=TAN_DK, width=1, joint="curve")
    pin_xy = {}
    for n, (lon, lat) in PINS.items():
        tx, ty = proj(lon, lat)
        dx, dy = NUDGE.get(n, (0, 0))
        # Clamp the drawn pin inside the map box (pin 6's nudge would
        # otherwise poke 1px above the top edge).
        px = min(max(tx + dx, 32), 992)
        py = min(max(ty + dy, my + 9), my + 69)
        pin_xy[n] = (px, py)
        if (dx, dy) != (0, 0):
            d.line([(tx, ty), (px, py)], fill=RED, width=1)
            d.ellipse([tx - 2, ty - 2, tx + 2, ty + 2], fill=RED)
        d.ellipse([px - 8, py - 8, px + 8, py + 8], fill=RED,
                  outline=LIGHT, width=2)
        nt = str(n)
        nf = sans(9, True)
        d.text((px - d.textlength(nt, font=nf) / 2, py - 5), nt, font=nf,
               fill=LIGHT)
    # Pin-overlap self-check (centres must be >= 16px apart = 2 radii)
    nums = sorted(pin_xy)
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            ax, ay = pin_xy[nums[i]]
            bx2, by2 = pin_xy[nums[j]]
            dist = ((ax - bx2) ** 2 + (ay - by2) ** 2) ** 0.5
            if dist < 16:
                RISKS.append("PIN OVERLAP %d/%d dist %.1f" %
                             (nums[i], nums[j], dist))
    y += 84
    # ALSO ON
    d.text((24, y), "ALSO ON MONDAY — 22 MORE STORIES", font=sans(14, True),
           fill=INK)
    y += 18
    for i, (head, src, _r) in enumerate(ALSO_ON):
        col, row = divmod(i, 11)
        ix = 24 if col == 0 else 520
        iy = y + row * 10.0
        d.text((ix, iy), "•", font=sans(10, True), fill=RED)
        txt = "%s (%s)" % (head, src)
        wdt = d.textlength(txt, font=sans(10))
        if wdt > 468:
            RISKS.append("ALSO ON %d too wide: %.0fpx" % (i + 1, wdt))
        d.text((ix + 12, iy), txt, font=sans(10), fill=INK)
    y += 116
    # DATE CHECK (F1: clarification line added; box height 62)
    d.rectangle([24, y, 1000, y + 62], fill=(255, 240, 240),
                outline=RED, width=2)
    d.text((34, y + 4), "DATE CHECK — LEFT OUT ON PURPOSE (NOT 23 NOVEMBER "
           "NEWS)", font=sans(11, True), fill=RED)
    draw_italic(d, (34, y + 16),
                "Every story here was reported or still developing on Monday "
                "23 November 2026.", sans(9), INK)
    for i, item in enumerate(DATE_CHECK):
        col, row = divmod(i, 3)
        ix = 34 if col == 0 else 512
        d.text((ix, y + 28 + row * 11), "✕ " + item, font=sans(9), fill=INK)
    y += 68
    # Footer
    hline(d, 24, 1000, y, fill=(170, 160, 140), wdt=1)
    foot = ("Sources: Reuters · AP · AFP · BBC · Al Jazeera · IPS · "
            "OilPrice · ATP · MotoGP · Dawn · IQAir · KCNA · Sky Sports")
    d.text((24, y + 2), foot, font=sans(9), fill=GREY)
    rt4 = "quick-lynx-56 · make.fun"
    d.text((1000 - d.textlength(rt4, font=sans(9, True)), y + 2), rt4,
           font=sans(9, True), fill=GREY)
    y += 14
    img.save(OUT, optimize=True)
    print("saved %s  final_y=%d  regions=%s" % (OUT, y, counts))
    print("RISKS: %s" % (RISKS if RISKS else "none"))


if __name__ == "__main__":
    main()
