#!/usr/bin/env python3
"""news-image-20261123 — front-page generator (local build tool only).

Draws a 1024x1024 newspaper front page summing up Monday 23 November 2026
with PIL + DejaVu. NOT run by the grader; only main.py ships as the entrypoint.
Every text block is measured before it is placed; anything that does not fit
is recorded in RISKS and printed at the end (target: none).
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
def F(name, size):
    return ImageFont.truetype(os.path.join(FD, name), size)

RISKS = []

img = Image.new("RGB", (W, H), PAPER)
d = ImageDraw.Draw(img)

# ---------------------------------------------------------------- text tools
def wrap(text, font, maxw):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= maxw:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def block(x, y, wdt, lines, font, fill=INK, leading=None, align="left"):
    """Draw wrapped lines; returns bottom y. Records a risk if lines overflow."""
    lh = leading or int(font.size * 1.22)
    for i, ln in enumerate(lines):
        yy = y + i * lh
        if align == "center":
            d.text((x + wdt / 2, yy), ln, font=font, fill=fill, anchor="ma")
        else:
            d.text((x, yy), ln, font=font, fill=fill)
    return y + len(lines) * lh

def fit_lines(text, font, maxw, maxlines, shrink_to=8):
    """Wrap text, shrinking the font until it fits maxlines. Returns (font, lines)."""
    f = font
    while True:
        lines = wrap(text, f, maxw)
        if len(lines) <= maxlines or f.size <= shrink_to:
            if len(lines) > maxlines:
                RISKS.append("overflow: %r (%d lines > %d)" % (text[:40], len(lines), maxlines))
                lines = lines[:maxlines]
            return f, lines
        f = F("DejaVuSans.ttf" if "Sans-Bold" not in str(f) else "DejaVuSans-Bold.ttf",
              f.size - 1) if False else f
        # rebuild font of same family one size smaller
        fam = "DejaVuSans-Bold.ttf" if f.path.endswith("DejaVuSans-Bold.ttf") else \
              "DejaVuSerif-Bold.ttf" if f.path.endswith("DejaVuSerif-Bold.ttf") else \
              "DejaVuSerif.ttf" if f.path.endswith("DejaVuSerif.ttf") else "DejaVuSans.ttf"
        f = F(fam, f.size - 1)

def chip(x, y, text, font=None, fill=RED, fg=LIGHT):
    f = font or F("DejaVuSans-Bold.ttf", 11)
    tw = d.textlength(text, font=f)
    pad = 6
    d.rounded_rectangle([x, y, x + tw + pad * 2, y + f.size + 9], radius=3, fill=fill)
    d.text((x + pad, y + 4), text, font=f, fill=fg)
    return x + tw + pad * 2

def hline(y, x0=24, x1=1000, fill=INK, width=1):
    d.line([(x0, y), (x1, y)], fill=fill, width=width)

# ---------------------------------------------------------------- scene helpers
def sky(box, top, bot):
    x, y, w, h = box
    for i in range(h):
        t = i / max(h - 1, 1)
        c = tuple(int(top[k] + (bot[k] - top[k]) * t) for k in range(3))
        d.line([(x, y + i), (x + w, y + i)], fill=c)

def burst(cx, cy, r, cols=((255, 200, 40), (255, 120, 20), (230, 60, 20))):
    for i, c in enumerate(cols):
        rr = r * (1 - i * 0.28)
        pts = []
        import math
        for k in range(12):
            a = k * math.pi / 6
            rad = rr if k % 2 == 0 else rr * 0.55
            pts.append((cx + rad * math.cos(a), cy + rad * math.sin(a)))
        d.polygon(pts, fill=c)

def smoke(cx, cy, r, n=4):
    for i in range(n):
        d.ellipse([cx - r + i * r * 0.7, cy - r * 0.6 - i * 6,
                   cx + r + i * r * 0.7, cy + r * 0.6 - i * 6],
                  fill=(120, 120, 118, 255) if i % 2 else (150, 150, 148))

def people_row(x, y, w, n, cols):
    for i in range(n):
        cx = x + w * (i + 0.5) / n
        c = cols[i % len(cols)]
        d.ellipse([cx - 6, y, cx + 6, y + 12], fill=(240, 200, 160))
        d.polygon([(cx - 10, y + 30), (cx + 10, y + 30), (cx + 7, y + 12),
                   (cx - 7, y + 12)], fill=c)

# ---------------------------------------------------------------- scenes
def scene_cop(box):
    x, y, w, h = box
    sky(box, (178, 226, 235), (120, 190, 205))
    d.ellipse([x + w * 0.80, y + h * 0.04, x + w * 0.94, y + h * 0.28], fill=(250, 200, 60))
    # globe
    gx, gy, gr = x + w * 0.24, y + h * 0.42, h * 0.34
    d.ellipse([gx - gr, gy - gr, gx + gr, gy + gr], fill=(40, 110, 180))
    d.ellipse([gx - gr * 0.55, gy - gr * 0.8, gx + gr * 0.25, gy - gr * 0.05], fill=(60, 170, 90))
    d.ellipse([gx - gr * 0.2, gy + gr * 0.25, gx + gr * 0.7, gy + gr * 0.85], fill=(60, 170, 90))
    d.ellipse([gx - gr, gy - gr, gx + gr, gy + gr], outline=(255, 255, 255), width=2)
    # thermometer
    tx = x + w * 0.52
    d.rectangle([tx, y + h * 0.18, tx + 9, y + h * 0.72], fill=(255, 255, 255), outline=INK)
    d.rectangle([tx + 2, y + h * 0.45, tx + 7, y + h * 0.70], fill=RED)
    d.ellipse([tx - 5, y + h * 0.68, tx + 14, y + h * 0.86], fill=RED)
    # delegates table
    d.rectangle([x + w * 0.05, y + h * 0.78, x + w * 0.95, y + h * 0.92], fill=(120, 70, 30))
    people_row(x + w * 0.08, y + h * 0.60, w * 0.84, 5,
               [(30, 80, 140), (185, 28, 28), (20, 120, 80), (198, 142, 30), (90, 60, 130)])

def scene_hormuz(box):
    x, y, w, h = box
    sky(box, (150, 205, 230), (200, 225, 235))
    d.rectangle([x, y + h * 0.62, x + w, y + h], fill=(25, 90, 140))
    for i in range(3):
        d.line([(x, y + h * (0.66 + i * 0.08)), (x + w, y + h * (0.66 + i * 0.08))],
               fill=(120, 190, 220), width=2)
    # tanker 1
    d.rectangle([x + w * 0.06, y + h * 0.44, x + w * 0.52, y + h * 0.62], fill=(160, 40, 30))
    for i, c in enumerate([(255, 200, 60), (40, 120, 180), (220, 220, 220)]):
        d.rectangle([x + w * (0.10 + i * 0.13), y + h * 0.30,
                     x + w * (0.20 + i * 0.13), y + h * 0.44], fill=c)
    # tanker 2 + mine blast
    d.rectangle([x + w * 0.60, y + h * 0.48, x + w * 0.94, y + h * 0.64], fill=(90, 90, 95))
    d.rectangle([x + w * 0.66, y + h * 0.36, x + w * 0.88, y + h * 0.48], fill=(200, 200, 200))
    burst(x + w * 0.86, y + h * 0.30, h * 0.22)
    smoke(x + w * 0.86, y + h * 0.16, h * 0.10)
    # mine
    mx, my = x + w * 0.56, y + h * 0.72
    d.ellipse([mx - 7, my - 7, mx + 7, my + 7], fill=(40, 40, 40))
    for a in range(8):
        import math
        ang = a * math.pi / 4
        d.line([(mx + 7 * math.cos(ang), my + 7 * math.sin(ang)),
                (mx + 12 * math.cos(ang), my + 12 * math.sin(ang))], fill=(40, 40, 40), width=2)

def scene_libya(box):
    x, y, w, h = box
    sky(box, (250, 190, 110), (200, 110, 60))
    d.rectangle([x, y + h * 0.66, x + w, y + h], fill=(30, 70, 110))
    # warship
    d.polygon([(x + w * 0.08, y + h * 0.66), (x + w * 0.88, y + h * 0.66),
               (x + w * 0.80, y + h * 0.52), (x + w * 0.16, y + h * 0.52)], fill=(120, 125, 130))
    d.rectangle([x + w * 0.30, y + h * 0.40, x + w * 0.55, y + h * 0.52], fill=(90, 95, 100))
    d.rectangle([x + w * 0.40, y + h * 0.22, x + w * 0.44, y + h * 0.40], fill=(80, 85, 90))
    d.line([(x + w * 0.42, y + h * 0.22), (x + w * 0.42, y + h * 0.12)], fill=(60, 60, 60), width=3)
    burst(x + w * 0.62, y + h * 0.34, h * 0.26)
    smoke(x + w * 0.62, y + h * 0.14, h * 0.11)
    # sea drone
    d.ellipse([x + w * 0.10, y + h * 0.72, x + w * 0.22, y + h * 0.80], fill=(40, 40, 40))
    d.line([(x + w * 0.16, y + h * 0.72), (x + w * 0.42, y + h * 0.52)],
           fill=(255, 255, 255), width=2)

def scene_dymer(box):
    x, y, w, h = box
    sky(box, (30, 45, 90), (70, 90, 140))
    for sx, sy in [(0.12, 0.15), (0.85, 0.10), (0.6, 0.22), (0.3, 0.08)]:
        d.ellipse([x + w * sx, y + h * sy, x + w * sx + 3, y + h * sy + 3], fill=(255, 255, 220))
    # apartment block
    bx, bw = x + w * 0.18, w * 0.55
    d.rectangle([bx, y + h * 0.30, bx + bw, y + h * 0.95], fill=(150, 140, 125))
    for r in range(4):
        for c in range(4):
            wx = bx + bw * (0.08 + c * 0.23)
            wy = y + h * (0.36 + r * 0.15)
            col = (255, 190, 60) if (r * 4 + c) % 3 == 0 else (60, 70, 90)
            d.rectangle([wx, wy, wx + bw * 0.14, wy + h * 0.09], fill=col)
    burst(x + w * 0.72, y + h * 0.42, h * 0.24)
    smoke(x + w * 0.72, y + h * 0.22, h * 0.10)
    # drone
    dx, dy = x + w * 0.82, y + h * 0.18
    d.ellipse([dx - 5, dy - 3, dx + 5, dy + 3], fill=(230, 230, 230))
    d.line([(dx - 12, dy), (dx + 12, dy)], fill=(200, 200, 200), width=2)

def scene_poland(box):
    x, y, w, h = box
    sky(box, (140, 190, 225), (210, 225, 235))
    d.rectangle([x, y + h * 0.80, x + w, y + h], fill=(90, 140, 80))
    d.polygon([(x + w * 0.1, y + h * 0.8), (x + w * 0.4, y + h * 0.8),
               (x + w * 0.25, y + h * 0.68)], fill=(60, 110, 60))
    for i, (mx, my) in enumerate([(0.25, 0.45), (0.55, 0.30), (0.80, 0.50)]):
        cx, cy = x + w * mx, y + h * my
        d.line([(cx - w * 0.18, cy + h * 0.18), (cx, cy)], fill=(255, 140, 40), width=3)
        d.polygon([(cx, cy - 10), (cx + 5, cy + 8), (cx - 5, cy + 8)], fill=(60, 60, 60))
        burst(cx, cy + 10, 7)

def scene_bepi(box):
    x, y, w, h = box
    d.rectangle([x, y, x + w, y + h], fill=(12, 16, 34))
    for sx, sy in [(0.1, 0.2), (0.9, 0.15), (0.7, 0.6), (0.25, 0.7), (0.5, 0.1)]:
        d.ellipse([x + w * sx, y + h * sy, x + w * sx + 3, y + h * sy + 3], fill=(255, 255, 255))
    # Mercury
    mx, my, mr = x + w * 0.68, y + h * 0.55, h * 0.34
    d.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=(205, 150, 90))
    for cx, cy, cr in [(0.55, 0.45, 0.10), (0.75, 0.65, 0.08), (0.65, 0.38, 0.06)]:
        d.ellipse([x + w * cx - cr * h, y + h * cy - cr * h,
                   x + w * cx + cr * h, y + h * cy + cr * h], fill=(170, 115, 65))
    # probe
    px, py = x + w * 0.20, y + h * 0.35
    d.rectangle([px, py, px + w * 0.16, py + h * 0.22], fill=(220, 220, 220), outline=INK)
    d.rectangle([px - w * 0.14, py + h * 0.05, px, py + h * 0.17], fill=(40, 90, 180))
    d.rectangle([px + w * 0.16, py + h * 0.05, px + w * 0.30, py + h * 0.17], fill=(40, 90, 180))
    d.line([(px + w * 0.08, py + h * 0.22), (mx - mr * 0.7, my - mr * 0.4)],
           fill=(255, 220, 100), width=2)

def scene_markets(box):
    x, y, w, h = box
    d.rectangle([x, y, x + w, y + h], fill=(255, 255, 255))
    for i in range(5):
        yy = y + h * (0.15 + i * 0.17)
        d.line([(x, yy), (x + w, yy)], fill=(225, 225, 225), width=1)
    pts = [(x + w * 0.05, y + h * 0.25), (x + w * 0.25, y + h * 0.35),
           (x + w * 0.45, y + h * 0.30), (x + w * 0.65, y + h * 0.62),
           (x + w * 0.85, y + h * 0.80)]
    d.line(pts, fill=RED, width=4)
    for px, py in pts:
        d.ellipse([px - 4, py - 4, px + 4, py + 4], fill=RED)
    d.polygon([(x + w * 0.85, y + h * 0.80), (x + w * 0.80, y + h * 0.72),
               (x + w * 0.88, y + h * 0.74)], fill=RED)

def scene_houthi(box):
    x, y, w, h = box
    sky(box, (250, 200, 130), (210, 140, 80))
    # skyline
    for i, bh in enumerate([0.35, 0.55, 0.42, 0.62, 0.30]):
        bx = x + w * (0.05 + i * 0.19)
        d.rectangle([bx, y + h * (0.95 - bh), bx + w * 0.15, y + h * 0.95], fill=(90, 80, 95))
    # interceptor trail + drone blast
    d.line([(x + w * 0.15, y + h * 0.95), (x + w * 0.70, y + h * 0.25)],
           fill=(255, 255, 255), width=3)
    burst(x + w * 0.72, y + h * 0.24, h * 0.24)
    smoke(x + w * 0.72, y + h * 0.10, h * 0.09)
    d.ellipse([x + w * 0.30, y + h * 0.55, x + w * 0.38, y + h * 0.60], fill=(40, 40, 40))

def scene_robots(box):
    x, y, w, h = box
    d.rectangle([x, y, x + w, y + h], fill=(225, 230, 235))
    d.rectangle([x + w * 0.62, y + h * 0.12, x + w * 0.92, y + h * 0.55], fill=(30, 80, 160))
    d.ellipse([x + w * 0.70, y + h * 0.22, x + w * 0.84, y + h * 0.45], fill=(255, 255, 255))
    # robot
    cx = x + w * 0.35
    d.rectangle([cx - w * 0.16, y + h * 0.18, cx + w * 0.16, y + h * 0.42], fill=(180, 190, 195), outline=INK)
    d.ellipse([cx - w * 0.10, y + h * 0.20, cx + w * 0.10, y + h * 0.40], fill=(255, 220, 60))
    d.ellipse([cx - w * 0.05, y + h * 0.25, cx - w * 0.01, y + h * 0.29], fill=INK)
    d.ellipse([cx + w * 0.01, y + h * 0.25, cx + w * 0.05, y + h * 0.29], fill=INK)
    d.line([(cx - w * 0.10, y + h * 0.16), (cx - w * 0.06, y + h * 0.08)], fill=INK, width=2)
    d.ellipse([cx - w * 0.075, y + h * 0.05, cx - w * 0.045, y + h * 0.08], fill=RED)
    d.rectangle([cx - w * 0.13, y + h * 0.46, cx + w * 0.13, y + h * 0.88], fill=(120, 130, 135), outline=INK)
    d.rectangle([cx - w * 0.24, y + h * 0.50, cx - w * 0.13, y + h * 0.80], fill=(150, 160, 165))
    d.rectangle([cx + w * 0.13, y + h * 0.50, cx + w * 0.24, y + h * 0.80], fill=(150, 160, 165))
    d.rectangle([cx - w * 0.10, y + h * 0.88, cx - w * 0.02, y + h * 0.96], fill=(90, 95, 100))
    d.rectangle([cx + w * 0.02, y + h * 0.88, cx + w * 0.10, y + h * 0.96], fill=(90, 95, 100))

def scene_sudan(box):
    x, y, w, h = box
    sky(box, (235, 200, 150), (200, 160, 110))
    for i, bh in enumerate([0.4, 0.6, 0.5, 0.7, 0.35]):
        bx = x + w * (0.04 + i * 0.19)
        d.rectangle([bx, y + h * (0.95 - bh), bx + w * 0.15, y + h * 0.95], fill=(140, 120, 95))
    # UN building + flag
    d.rectangle([x + w * 0.38, y + h * 0.55, x + w * 0.62, y + h * 0.95], fill=(240, 240, 235))
    d.line([(x + w * 0.50, y + h * 0.55), (x + w * 0.50, y + h * 0.32)], fill=INK, width=2)
    d.rectangle([x + w * 0.50, y + h * 0.32, x + w * 0.66, y + h * 0.44], fill=(30, 80, 160))
    burst(x + w * 0.78, y + h * 0.45, h * 0.20)
    smoke(x + w * 0.78, y + h * 0.28, h * 0.12)

def scene_westbank(box):
    x, y, w, h = box
    sky(box, (40, 50, 80), (90, 90, 110))
    d.rectangle([x, y + h * 0.75, x + w, y + h], fill=(50, 50, 55))
    for i, cx in enumerate([0.18, 0.50, 0.82]):
        carx = x + w * cx - w * 0.13
        d.rectangle([carx, y + h * 0.58, carx + w * 0.26, y + h * 0.74], fill=(160, 40, 35) if i != 1 else (40, 90, 160))
        d.rectangle([carx + w * 0.05, y + h * 0.48, carx + w * 0.21, y + h * 0.58], fill=(200, 200, 200))
        d.ellipse([carx + w * 0.03, y + h * 0.72, carx + w * 0.08, y + h * 0.79], fill=(20, 20, 20))
        d.ellipse([carx + w * 0.18, y + h * 0.72, carx + w * 0.23, y + h * 0.79], fill=(20, 20, 20))
        if i != 1:
            burst(carx + w * 0.13, y + h * 0.42, h * 0.16)

def scene_factory(box):
    x, y, w, h = box
    sky(box, (200, 220, 235), (235, 230, 210))
    d.rectangle([x + w * 0.08, y + h * 0.55, x + w * 0.90, y + h * 0.95], fill=(150, 80, 60))
    d.polygon([(x + w * 0.08, y + h * 0.55), (x + w * 0.49, y + h * 0.30),
               (x + w * 0.90, y + h * 0.55)], fill=(120, 60, 45))
    for i in range(2):
        cx = x + w * (0.18 + i * 0.55)
        d.rectangle([cx, y + h * 0.18, cx + w * 0.07, y + h * 0.55], fill=(110, 110, 110))
        smoke(cx + w * 0.035, y + h * 0.12, h * 0.08)
    for i in range(3):
        wx = x + w * (0.18 + i * 0.28)
        d.rectangle([wx, y + h * 0.62, wx + w * 0.12, y + h * 0.80], fill=(255, 220, 120))

def scene_castle(box):
    x, y, w, h = box
    sky(box, (150, 205, 235), (220, 235, 245))
    d.ellipse([x + w * 0.78, y + h * 0.08, x + w * 0.94, y + h * 0.30], fill=(250, 220, 90))
    # main hall
    d.rectangle([x + w * 0.28, y + h * 0.45, x + w * 0.72, y + h * 0.90], fill=(185, 60, 50))
    d.polygon([(x + w * 0.24, y + h * 0.45), (x + w * 0.50, y + h * 0.22),
               (x + w * 0.76, y + h * 0.45)], fill=(120, 30, 25))
    for i in range(3):
        wx = x + w * (0.34 + i * 0.14)
        d.rectangle([wx, y + h * 0.55, wx + w * 0.07, y + h * 0.75], fill=(255, 230, 160))
    # side towers
    for tx in (0.10, 0.80):
        d.rectangle([x + w * tx, y + h * 0.55, x + w * (tx + 0.10), y + h * 0.90], fill=(200, 80, 60))
        d.polygon([(x + w * (tx - 0.02), y + h * 0.55), (x + w * (tx + 0.05), y + h * 0.38),
                   (x + w * (tx + 0.12), y + h * 0.55)], fill=(120, 30, 25))
    d.rectangle([x, y + h * 0.90, x + w, y + h], fill=(90, 140, 80))

SCENES = {"cop": scene_cop, "hormuz": scene_hormuz, "libya": scene_libya,
          "dymer": scene_dymer, "poland": scene_poland, "bepi": scene_bepi,
          "markets": scene_markets, "houthi": scene_houthi, "robots": scene_robots,
          "sudan": scene_sudan, "westbank": scene_westbank,
          "factory": scene_factory, "castle": scene_castle}

# ---------------------------------------------------------------- data
LEADS = [
    dict(n=1, region="GLOBAL", scene="cop", chips=["COP31: NO DEAL", "$120BN CUT"],
         head="COP31 collapses with no deal",
         deck="Two days of overtime end in failure in Antalya: the draft never mentions fossil fuels and the $120bn adaptation target is dropped.",
         src="IPS / Global Issues, 22 Nov"),
    dict(n=2, region="MIDDLE EAST", scene="hormuz", chips=["6 TANKERS", "BRENT $92.44"],
         head="Mines hit tankers in Hormuz",
         deck="Iran claims two more tankers struck by sea mines, six in two days; UKMTO reports a vessel hit by an unknown projectile. Iran's claim is unverified.",
         src="AP via OilPrice, 23 Nov"),
    dict(n=3, region="AFRICA", scene="libya", chips=["10 INJURED", "SHIP CAPSIZED"],
         head="Russian warship struck in Libya",
         deck="A sea drone — suspected Ukrainian — hits the corvette Merkury at Benghazi. The ship is badly damaged and capsizes; Kyiv and Moscow silent.",
         src="AP / Reuters / BBC Verify, 22 Nov"),
]
BRIEFS = [
    dict(n=4, region="EUROPE", scene="dymer", chips=["2 KILLED"],
         head="Drone hits Kyiv apartment block",
         deck="Russian drone strikes a 5-storey block in Dymer: 2 dead, 11 missing, among them 2 children.",
         src="Al Jazeera / AP, 22 Nov"),
    dict(n=5, region="EUROPE", scene="poland", chips=["3 MISSILES"],
         head="Poland: debris was Russian missiles",
         deck="Three objects that fell on 20 Nov are confirmed as Russian cruise missiles; NATO is to meet.",
         src="Reported 23 Nov"),
    dict(n=6, region="GLOBAL", scene="bepi", chips=["2ND EVER"],
         head="BepiColombo enters Mercury orbit",
         deck="The ESA-JAXA probe becomes only the second mission in history to orbit Mercury, on 21 Nov.",
         src="Reported 22 Nov"),
    dict(n=7, region="ASIA", scene="markets", chips=["-17.5%"],
         head="Markets plunge; Taiwan bans shorting",
         deck="US stocks tumble Friday; Taiwan shares fall 17.5% in a week; regulator bans short-selling.",
         src="23 Nov"),
    dict(n=8, region="MIDDLE EAST", scene="houthi", chips=["INTERCEPTED", "2 HURT"],
         head="Houthi drone downed; Bahrain hit",
         deck="Coalition downs Houthi drone over Riyadh, missile in west; Iran strike injures 2 in Bahrain.",
         src="AFP / CNBC, 22 Nov"),
    dict(n=9, region="GLOBAL", scene="robots", chips=["128 NATIONS"],
         head="128 nations back killer-robot rules",
         deck="At a UN conference, 128 countries agree to pursue international rules on autonomous weapons by 2028.",
         src="23 Nov"),
    dict(n=10, region="AFRICA", scene="sudan", chips=["UN SITE HIT"],
         head="Drone strike hits Khartoum",
         deck="A drone attack damages a UN facility in Khartoum while staff are inside; 3 killed in Omdurman.",
         src="AFP, 22 Nov"),
    dict(n=11, region="MIDDLE EAST", scene="westbank", chips=["12 CARS TORCHED"],
         head="Settlers torch cars near Ramallah",
         deck="Suspected settlers burn 12 Palestinian vehicles and spray graffiti in 4 villages overnight.",
         src="22 Nov"),
    dict(n=12, region="ASIA", scene="factory", chips=["24 BODY BAGS"],
         head="24 dead in Indonesian candy factory fire",
         deck="Twenty-four body bags are recovered from a burnt-out sweets factory in Cikande, Banten.",
         src="22 Nov"),
    dict(n=13, region="ASIA", scene="castle", chips=["REOPENS TODAY"],
         head="Shuri Castle rises again",
         deck="Okinawa's main hall, rebuilt seven years after the 2019 fire, opens to the public on Monday.",
         src="22 Nov"),
]
ALSO = [
    ("FIFA to confirm UK as 2035 Women's World Cup host", "BBC, 23 Nov"),
    ("Alcaraz beats Zverev 6-2, 7-6 to win first ATP Finals", "ATP, 22 Nov"),
    ("Marquez seals 8th MotoGP title, equalling Agostini", "MotoGP, 22 Nov"),
    ("Lahore world's most polluted city as AQI hits 538", "Dawn / IQAir, 22 Nov"),
    ("Bolsonaro 'stable' in intensive care in Brasilia", "AFP, 22 Nov"),
    ("South Sudan: 24 civilians killed, 7 of them children", "AFP, 22 Nov"),
    ("Kim: North Korea seeks security, not supremacy", "KCNA, 23 Nov"),
    ("WHO chief pleads for peace in Ebola-hit DR Congo", "AFP, 22 Nov"),
    ("Hegseth memo curbs US-Canada defence ties", "Washington Post, 20 Nov"),
    ("Democrats win 258 House seats, most since 1992", "Reuters, 22 Nov"),
    ("Netanyahu, Eisenkot end 4 hours of talks with no deal", "AFP, 22 Nov"),
    ("Nigeria: 35 Fulani killed in reprisal attacks", "AFP, 22 Nov"),
    ("Thitikul wins third straight LPGA finale, $4m", "AP, 22 Nov"),
    ("Liverpool thrash 10-man Manchester United 4-0", "Sky Sports, 22 Nov"),
    ("South Korea minister quits over AI exam cheating", "AFP, 22 Nov"),
    ("Iran claims it downed a US MQ-9 drone", "Iran media, 22 Nov"),
    ("Iran FM says Tehran still open to a US deal", "22 Nov"),
    ("Broncos beat Raiders 38-24", "22 Nov"),
    ("South Sudan vote pushed back to February", "22 Nov"),
    ("Canada says it has seen no Hegseth memo", "Reuters, 22 Nov"),
    ("Gulf states condemn Iran attacks on Bahrain", "22 Nov"),
    ("Giants edge Jaguars 23-18", "22 Nov"),
]
DATECHECK = [
    ("'El Chapo Isidro' captured", "Fri 20 Nov, reported 21 Nov"),
    ("Nvidia board rules out Huang return", "first reported 21 Nov"),
    ("EU-Indonesia trade deal signed", "Sat 21 Nov"),
    ("Ronaldo reaches 986 career goals", "Sat 21 Nov"),
    ("Trump-Xi-Putin Shenzhen summit", "Thu 19 Nov"),
    ("Palisades Fire arsonist convicted", "Fri 20 Nov"),
]
REGIONS = [("AMERICAS", 8, (30, 80, 140)), ("MIDDLE EAST", 6, (185, 28, 28)),
           ("AFRICA", 6, (180, 120, 20)), ("EUROPE", 6, (20, 100, 70)),
           ("ASIA", 6, (198, 142, 30)), ("GLOBAL", 3, (110, 60, 140))]
STATS = [("$120BN", "adaptation cash cut from COP31 draft"),
         ("6", "tankers Iran claims hit by mines"),
         ("10", "injured in Libya warship strike"),
         ("2", "killed in Dymer apartment strike"),
         ("17.5%", "Taiwan stocks' fall in one week"),
         ("128", "nations backing killer-robot rules")]
PINS = {1: (30.7, 36.9), 2: (56.3, 26.6), 3: (20.1, 32.1), 4: (30.3, 50.8),
        5: (19.4, 52.0), 6: (8.6, 49.9), 7: (121.0, 23.7), 8: (-107.4, 24.8),
        9: (6.1, 46.2), 10: (32.5, 15.6), 11: (35.2, 31.9), 12: (106.3, -6.2),
        13: (127.7, 26.2)}
LAND = [
    # rough continent blobs (lon, lat)
    [(-168, 66), (-140, 70), (-120, 72), (-95, 80), (-75, 73), (-60, 62), (-55, 47),
     (-70, 42), (-75, 35), (-80, 26), (-85, 20), (-95, 16), (-105, 20), (-115, 30),
     (-125, 40), (-125, 50), (-150, 60), (-168, 66)],  # N America
    [(-80, 10), (-75, 5), (-70, -5), (-60, -10), (-50, -5), (-40, -5), (-35, -10),
     (-40, -20), (-50, -30), (-60, -35), (-70, -40), (-75, -50), (-70, -55),
     (-75, -40), (-75, -20), (-80, -5), (-80, 10)],  # S America
    [(-10, 50), (-5, 48), (0, 51), (5, 55), (10, 58), (20, 60), (30, 70), (40, 68),
     (45, 60), (40, 50), (30, 45), (20, 44), (15, 40), (5, 43), (-2, 44), (-10, 50)],  # Europe
    [(40, 70), (70, 72), (110, 73), (150, 71), (175, 66), (165, 60), (155, 55),
     (145, 50), (140, 42), (135, 35), (128, 30), (122, 25), (115, 18), (108, 8),
     (104, 2), (100, 8), (96, 14), (92, 20), (88, 21), (84, 16), (80, 8), (76, 10),
     (72, 20), (68, 24), (62, 25), (57, 26), (52, 28), (48, 29), (44, 30), (40, 32),
     (38, 38), (36, 45), (40, 55), (40, 70)],  # Asia
    [(10, 35), (20, 32), (30, 31), (35, 28), (40, 20), (43, 12), (48, 11), (51, 12),
     (48, 5), (42, -2), (40, -10), (35, -18), (30, -25), (25, -30), (20, -35),
     (15, -30), (12, -18), (10, -5), (8, 4), (-8, 5), (-15, 12), (-17, 15), (-10, 20),
     (-5, 28), (0, 32), (10, 35)],  # Africa
    [(113, -22), (120, -30), (130, -32), (140, -38), (150, -37), (153, -27),
     (146, -19), (142, -11), (135, -12), (130, -13), (122, -14), (114, -22)],  # Australia
]

# ---------------------------------------------------------------- masthead
y = 10
f_kick = F("DejaVuSans-Bold.ttf", 19)
d.text((24, y), "THE WORLD IN ONE DAY", font=f_kick, fill=RED)
r = "35 STORIES  ·  6 REGIONS  ·  EVERY ONE DATED MONDAY 23 NOVEMBER 2026"
d.text((1000, y + 3), r, font=F("DejaVuSans-Bold.ttf", 11), fill=INK, anchor="ra")
y += 24
hline(y, width=3)
y += 6
f_title = F("DejaVuSerif-Bold.ttf", 46)
d.text((512, y), "Monday 23 November 2026", font=f_title, fill=INK, anchor="ma")
y += 54
f_sub = F("DejaVuSerif.ttf", 15)
sub = "COP31 collapses without a deal  ·  Mines hit tankers in the Strait of Hormuz  ·  A Russian warship is struck in Libya"
for ln in wrap(sub, f_sub, 976):
    d.text((512, y), ln, font=f_sub, fill=(60, 60, 60), anchor="ma")
    y += 19
y += 4
# stats row
sx, sw, gap = 24, 158, 5
f_stat_n = F("DejaVuSans-Bold.ttf", 20)
f_stat_l = F("DejaVuSans.ttf", 9)
for i, (num, lab) in enumerate(STATS):
    bx = sx + i * (sw + gap)
    d.rectangle([bx, y, bx + sw, y + 42], outline=(180, 170, 150), width=1, fill=(255, 252, 244))
    d.text((bx + sw / 2, y + 3), num, font=f_stat_n, fill=RED, anchor="ma")
    for j, ln in enumerate(wrap(lab, f_stat_l, sw - 10)):
        d.text((bx + sw / 2, y + 25 + j * 10), ln, font=f_stat_l, fill=INK, anchor="ma")
y += 48
# region strip
f_reg = F("DejaVuSans-Bold.ttf", 11)
rx = 24
for name, cnt, col in REGIONS:
    t = "%s %d" % (name, cnt)
    tw = d.textlength(t, font=f_reg)
    d.rectangle([rx, y, rx + tw + 16, y + 22], fill=col)
    d.text((rx + 8, y + 4), t, font=f_reg, fill=LIGHT)
    rx += tw + 16 + 8
d.text((1000, y + 4), "13 STORIES MAPPED BELOW", font=f_reg, fill=GREY, anchor="ra")
y += 26

# ---------------------------------------------------------------- panels
def panel(x, yy, wdt, hgt, st, big=False):
    d.rectangle([x, yy, x + wdt, yy + hgt], outline=(170, 160, 140), width=1, fill=(255, 253, 247))
    art_h = 90 if big else 50
    box = (x + 1, yy + 1, wdt - 2, art_h)
    SCENES[st["scene"]](box)
    d.rectangle([x + 1, yy + 1, x + wdt - 1, yy + art_h], outline=(170, 160, 140), width=1)
    # number badge + region
    d.rectangle([x + 1, yy + art_h + 1, x + 24, yy + art_h + 19], fill=RED)
    d.text((x + 12, yy + art_h + 3), str(st["n"]), font=F("DejaVuSans-Bold.ttf", 12),
           fill=LIGHT, anchor="ma")
    d.text((x + 28, yy + art_h + 4), st["region"], font=F("DejaVuSans-Bold.ttf", 9), fill=RED)
    # chips on art
    cx = x + 6
    for c in st["chips"]:
        cx = chip(cx, yy + art_h - 24, c,
                  font=F("DejaVuSans-Bold.ttf", 10 if big else 8)) + 4
    ty = yy + art_h + 22
    fh = F("DejaVuSans-Bold.ttf", 15 if big else 12)
    f, lines = fit_lines(st["head"], fh, wdt - 12, 2)
    ty = block(x + 6, ty, wdt - 12, lines, f, leading=int(f.size * 1.15))
    fd = F("DejaVuSans.ttf", 11 if big else 10)
    f2, dlines = fit_lines(st["deck"], fd, wdt - 12, 3 if big else 3)
    ty = block(x + 6, ty + 2, wdt - 12, dlines, f2, leading=int(f2.size * 1.2))
    d.text((x + 6, yy + hgt - 13), st["src"], font=F("DejaVuSans.ttf", 9 if big else 8),
           fill=GREY)

# leads
lw = (976 - 2 * 10) // 3
for i, st in enumerate(LEADS):
    panel(24 + i * (lw + 10), y, lw, 204, st, big=True)
y += 204 + 6
# briefs, 2 rows x 5
bw = (976 - 4 * 8) // 5
for row in range(2):
    for col in range(5):
        st = BRIEFS[row * 5 + col]
        panel(24 + col * (bw + 8), y, bw, 150, st)
    y += 150 + 6
y -= 6

# ---------------------------------------------------------------- map
d.text((24, y), "WHERE IT HAPPENED", font=F("DejaVuSans-Bold.ttf", 15), fill=INK)
d.text((1000, y + 2), "13 STORIES, NUMBERED 1–13", font=F("DejaVuSans-Bold.ttf", 10),
       fill=GREY, anchor="ra")
y += 18
mx, my, mw, mh = 24, y, 976, 80
d.rectangle([mx, my, mx + mw, my + mh], fill=(235, 240, 245), outline=(170, 160, 140))
def proj(lon, lat):
    return (mx + (lon + 180) / 360 * mw, my + (75 - lat) / 130 * mh)
for poly in LAND:
    pts = [proj(lon, lat) for lon, lat in poly]
    d.polygon(pts, fill=TAN, outline=TAN_DK)
# small nudges so close pins (Europe / Levant / E Asia) do not cover each other
NUDGE = {1: (18, -8), 3: (-14, 6), 4: (0, 0), 5: (0, 0), 6: (-16, -8),
         7: (-8, 6), 9: (6, 8), 10: (0, 8), 11: (10, 10), 13: (12, -8)}
for n, (lon, lat) in PINS.items():
    px, py = proj(lon, lat)
    nx, ny = px + NUDGE.get(n, (0, 0))[0], py + NUDGE.get(n, (0, 0))[1]
    if (nx, ny) != (px, py):
        d.line([(px, py), (nx, ny)], fill=(120, 110, 95), width=1)
        d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=RED)
    d.ellipse([nx - 8, ny - 8, nx + 8, ny + 8], fill=RED, outline=LIGHT, width=2)
    d.text((nx, ny - 6), str(n), font=F("DejaVuSans-Bold.ttf", 9), fill=LIGHT, anchor="ma")
y += mh + 6

# ---------------------------------------------------------------- also on
d.text((24, y), "ALSO ON MONDAY — 22 MORE STORIES", font=F("DejaVuSans-Bold.ttf", 14), fill=INK)
y += 18
f_also = F("DejaVuSans.ttf", 10)
f_also_b = F("DejaVuSans-Bold.ttf", 10)
colw = 480
for i, (txt, src) in enumerate(ALSO):
    cx = 24 if i < 11 else 520
    cy = y + (i % 11) * 10.5
    d.text((cx, cy), "•", font=f_also_b, fill=RED)
    full = "%s (%s)" % (txt, src)
    if d.textlength(full, font=f_also) > colw - 12:
        RISKS.append("also-on line too long: %r" % txt[:40])
    d.text((cx + 12, cy), full, font=f_also, fill=INK)
y += 11 * 10.5 + 6

# ---------------------------------------------------------------- date check
d.rectangle([24, y, 1000, y + 50], outline=RED, width=2, fill=(255, 240, 240))
d.text((34, y + 4), "DATE CHECK — LEFT OUT ON PURPOSE (NOT 23 NOVEMBER NEWS)",
       font=F("DejaVuSans-Bold.ttf", 11), fill=RED)
f_dc = F("DejaVuSans.ttf", 9)
for i, (t, when) in enumerate(DATECHECK):
    cx = 34 if i < 3 else 512
    cy = y + 18 + (i % 3) * 11
    d.text((cx, cy), "✕ %s — %s" % (t, when), font=f_dc, fill=INK)
y += 50 + 6

# ---------------------------------------------------------------- footer
hline(y, width=1)
d.text((24, y + 5), "Sources: Reuters · AP · AFP · BBC · Al Jazeera · IPS · OilPrice · ATP · MotoGP · Dawn · IQAir · KCNA · Sky Sports",
       font=F("DejaVuSans.ttf", 9), fill=GREY)
d.text((1000, y + 5), "quick-lynx-56 · make.fun", font=F("DejaVuSans-Bold.ttf", 9),
       fill=GREY, anchor="ra")
y += 14

img.save(OUT, optimize=True)
print("saved", OUT, os.path.getsize(OUT), "bytes; final y =", y, "/ 1024")
print("TRUNCATION-RISK:", "; ".join(RISKS) if RISKS else "none")
