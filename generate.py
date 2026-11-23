#!/usr/bin/env python3
"""THE WORLD IN ONE DAY - Monday 23 November 2026. R3 blind rewrite.

Deterministic, no network. PIL + DejaVu only.
R3 changes: (A) sc_libya densified, (B) sc_bepi densified, (C) sc_robots
replaced with UN assembly scene, (D) map contrast up, (E) DATE CHECK
timezone qualifier. Everything else identical to the R2 spec.
"""
import os
from PIL import Image, ImageDraw, ImageFont

RISKS = []

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
PANEL_BG = (255, 253, 247)
PANEL_LINE = (170, 160, 140)

FONT_DIR = "/usr/share/fonts/truetype/dejavu"


def _f(name, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size)


def sans(size, bold=False):
    return _f("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size)


def serif(size, bold=False):
    return _f("DejaVuSerif-Bold.ttf" if bold else "DejaVuSerif.ttf", size)


# ---------------------------------------------------------------- helpers
def wrap(text, font, max_w):
    """Greedy word wrap; returns list of lines."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if font.getlength(trial) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    # hard-split any single over-wide line
    out = []
    for ln in lines:
        while font.getlength(ln) > max_w and len(ln) > 1:
            cut = len(ln) - 1
            while cut > 0 and font.getlength(ln[:cut]) > max_w:
                cut -= 1
            out.append(ln[:cut])
            ln = ln[cut:]
        out.append(ln)
    return out


def block(draw, x, y, lines, font, fill, align="left", center_x=None, leading=None):
    """Draw lines of text; returns height used."""
    lh = leading if leading is not None else int(font.size * 1.2)
    for i, ln in enumerate(lines):
        if align == "center":
            lx = center_x - font.getlength(ln) / 2
        else:
            lx = x
        draw.text((lx, y + i * lh), ln, font=font, fill=fill)
    return len(lines) * lh


def fit_lines(draw, text, start, max_w, maxlines, avail_h, bold=True, use_serif=False):
    """Shrink font until text fits maxlines + avail_h. Records RISK on overflow."""
    for size in range(start, 7, -1):
        font = serif(size, bold) if use_serif else sans(size, bold)
        lines = wrap(text, font, max_w)
        lh = int(size * 1.15)
        if len(lines) <= maxlines and len(lines) * lh <= avail_h:
            return font, lines, lh
    font = serif(8, bold) if use_serif else sans(8, bold)
    lines = wrap(text, font, max_w)
    lh = int(8 * 1.15)
    RISKS.append("OVERFLOW: %s" % text[:40])
    return font, lines, lh


def chip(draw, x, y, text, size, h):
    font = sans(size, bold=True)
    w = int(font.getlength(text)) + 12
    draw.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, fill=RED)
    draw.text((x + 6, y + (h - size) // 2 - 1), text, font=font, fill=LIGHT)
    return w


def hline(draw, x, y, w, fill=INK, width=1):
    draw.line([(x, y), (x + w, y)], fill=fill, width=width)


def sky(draw, box, top, bottom):
    x0, y0, x1, y1 = box
    n = max(1, y1 - y0)
    for yy in range(y0, y1):
        t = (yy - y0) / n
        c = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        draw.line([(x0, yy), (x1, yy)], fill=c)


def burst(draw, cx, cy, r):
    colors = [(255, 140, 0), (250, 200, 60), (255, 230, 150)]
    import math
    for i in range(12):
        a = math.radians(i * 30)
        a2 = math.radians(i * 30 + 14)
        ox, oy = cx + math.cos(a) * r, cy + math.sin(a) * r
        ix, iy = cx + math.cos(a2) * r * 0.45, cy + math.sin(a2) * r * 0.45
        draw.polygon([(cx, cy), (ox, oy), (ix, iy)], fill=colors[i % 3])
    draw.ellipse([cx - r * 0.32, cy - r * 0.32, cx + r * 0.32, cy + r * 0.32],
                 fill=(255, 200, 60))


def smoke(draw, cx, cy, r):
    g = (195, 195, 195)
    for dx, dy, rr in [(-0.6, -0.15, 0.7), (0.0, -0.5, 0.85),
                       (0.6, -0.15, 0.7), (0.1, 0.15, 0.6)]:
        x, y = cx + dx * r, cy + dy * r
        draw.ellipse([x - rr * r, y - rr * r, x + rr * r, y + rr * r], fill=g)


def people_row(draw, x, y, w, h, n, palette=None):
    palette = palette or [BLUE, RED, TEAL, GOLD, (96, 64, 150), (60, 120, 60)]
    fw = w / n
    hr = fw * 0.24
    for i in range(n):
        cx = x + fw * (i + 0.5)
        hy = y + h * 0.16
        draw.ellipse([cx - hr, hy - hr, cx + hr, hy + hr], fill=(230, 200, 170))
        draw.polygon([(cx - fw * 0.32, y + h), (cx - fw * 0.28, y + h * 0.38),
                      (cx + fw * 0.28, y + h * 0.38), (cx + fw * 0.32, y + h)],
                     fill=palette[i % len(palette)])


def draw_italic(img, x, y, text, font, fill):
    """Fake oblique: render text to a layer, shear it, paste."""
    w = int(font.getlength(text)) + 30
    h = font.size + 12
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.text((0, 0), text, font=font, fill=fill + (255,))
    sheared = layer.transform(layer.size, Image.AFFINE, (1, -0.18, 0, 0, 1, 0),
                              resample=Image.BICUBIC)
    img.paste(sheared, (x, y), sheared)


# ---------------------------------------------------------------- scenes
# Every scene draws into a tile of size (bw, bh); normalized coords 0..1.

def sc_cop(d, bw, bh):
    sky(d, (0, 0, bw, bh), (178, 226, 235), (120, 190, 205))
    d.ellipse([0.80 * bw, 0.04 * bh, 0.96 * bw, 0.28 * bh], fill=(250, 210, 60))
    d.ellipse([0.08 * bw, 0.10 * bh, 0.38 * bw, 0.58 * bh], fill=(40, 110, 180))
    d.ellipse([0.13 * bw, 0.18 * bh, 0.24 * bw, 0.34 * bh], fill=(60, 160, 80))
    d.ellipse([0.24 * bw, 0.36 * bh, 0.33 * bw, 0.50 * bh], fill=(60, 160, 80))
    d.ellipse([0.08 * bw, 0.10 * bh, 0.38 * bw, 0.58 * bh], outline=LIGHT, width=2)
    d.rectangle([0.62 * bw, 0.12 * bh, 0.70 * bw, 0.58 * bh], fill=LIGHT,
                outline=(150, 150, 150))
    d.rectangle([0.64 * bw, 0.30 * bh, 0.68 * bw, 0.56 * bh], fill=RED)
    d.ellipse([0.615 * bw, 0.54 * bh, 0.705 * bw, 0.64 * bh], fill=RED)
    d.rectangle([0.02 * bw, 0.66 * bh, 0.98 * bw, 0.74 * bh], fill=(120, 70, 30))
    people_row(d, 0.06 * bw, 0.74 * bh, 0.88 * bw, 0.24 * bh, 5)


def sc_hormuz(d, bw, bh):
    sky(d, (0, 0, bw, int(0.55 * bh)), (150, 205, 230), (200, 225, 235))
    d.rectangle([0, 0.55 * bh, bw, bh], fill=(25, 90, 140))
    for fy in (0.62, 0.72, 0.84):
        d.line([(0.02 * bw, fy * bh), (0.98 * bw, fy * bh)], fill=(140, 190, 220), width=2)
    d.polygon([(0.03 * bw, 0.68 * bh), (0.03 * bw, 0.55 * bh), (0.10 * bw, 0.52 * bh),
               (0.40 * bw, 0.52 * bh), (0.46 * bw, 0.60 * bh), (0.46 * bw, 0.68 * bh)],
              fill=(185, 40, 40))
    for cx, col in [(0.08, (250, 200, 60)), (0.16, (40, 120, 180)), (0.24, (60, 160, 80))]:
        d.rectangle([cx * bw, 0.44 * bh, (cx + 0.07) * bw, 0.52 * bh], fill=col)
    d.polygon([(0.58 * bw, 0.66 * bh), (0.60 * bw, 0.56 * bh), (0.94 * bw, 0.56 * bh),
               (0.97 * bw, 0.66 * bh)], fill=(150, 155, 160))
    d.rectangle([0.78 * bw, 0.46 * bh, 0.90 * bw, 0.56 * bh], fill=(110, 115, 120))
    burst(d, 0.82 * bw, 0.38 * bh, bw * 0.10)
    smoke(d, 0.86 * bw, 0.24 * bh, bw * 0.07)
    mx, my = 0.52 * bw, 0.80 * bh
    d.ellipse([mx - bw * 0.045, my - bw * 0.045, mx + bw * 0.045, my + bw * 0.045],
              fill=(20, 20, 20))
    import math
    for i in range(8):
        a = math.radians(i * 45)
        d.line([(mx + math.cos(a) * bw * 0.04, my + math.sin(a) * bw * 0.04),
                (mx + math.cos(a) * bw * 0.065, my + math.sin(a) * bw * 0.065)],
               fill=(20, 20, 20), width=2)


def sc_libya(d, bw, bh):
    # R3-A: densified - funnel, mast, waterline, bigger smoke, debris, lifeboat.
    sky(d, (0, 0, bw, int(0.60 * bh)), (250, 190, 110), (200, 110, 60))
    d.rectangle([0, 0.60 * bh, bw, bh], fill=(30, 70, 110))
    for fy in (0.68, 0.80, 0.92):
        d.line([(0.02 * bw, fy * bh), (0.98 * bw, fy * bh)], fill=(140, 190, 220), width=2)
    d.polygon([(0.10 * bw, 0.52 * bh), (0.62 * bw, 0.52 * bh), (0.58 * bw, 0.66 * bh),
               (0.14 * bw, 0.66 * bh)], fill=(120, 125, 130))
    d.rectangle([0.24 * bw, 0.34 * bh, 0.44 * bw, 0.52 * bh], fill=(150, 155, 160))
    d.rectangle([0.46 * bw, 0.30 * bh, 0.52 * bw, 0.52 * bh], fill=(70, 75, 80))
    for wx in (0.27, 0.33, 0.39):
        d.rectangle([wx * bw, 0.38 * bh, (wx + 0.04) * bw, 0.44 * bh],
                    fill=(250, 220, 120))
    d.line([(0.12 * bw, 0.60 * bh), (0.60 * bw, 0.60 * bh)], fill=LIGHT, width=2)
    d.line([(0.34 * bw, 0.34 * bh), (0.34 * bw, 0.16 * bh)], fill=(40, 40, 40), width=3)
    d.line([(0.34 * bw, 0.16 * bh), (0.40 * bw, 0.20 * bh)], fill=(40, 40, 40), width=2)
    burst(d, 0.72 * bw, 0.42 * bh, bw * 0.09)
    smoke(d, 0.78 * bw, 0.22 * bh, bw * 0.10)
    smoke(d, 0.88 * bw, 0.16 * bh, bw * 0.06)
    # floating debris near the hull
    d.rectangle([0.64 * bw, 0.74 * bh, 0.69 * bw, 0.77 * bh], fill=(255, 140, 0))
    d.rectangle([0.70 * bw, 0.82 * bh, 0.74 * bw, 0.84 * bh], fill=LIGHT)
    d.rectangle([0.60 * bw, 0.86 * bh, 0.65 * bw, 0.88 * bh], fill=(255, 140, 0))
    # orange lifeboat
    d.ellipse([0.76 * bw, 0.74 * bh, 0.88 * bw, 0.82 * bh], fill=(255, 120, 0))
    d.line([(0.77 * bw, 0.78 * bh), (0.87 * bw, 0.78 * bh)], fill=LIGHT, width=2)
    # rescue marker kept from R2: black triangle + white line
    d.polygon([(0.68 * bw, 0.62 * bh), (0.72 * bw, 0.62 * bh), (0.70 * bw, 0.57 * bh)],
              fill=(20, 20, 20))
    d.line([(0.70 * bw, 0.62 * bh), (0.76 * bw, 0.70 * bh)], fill=LIGHT, width=2)


def sc_dymer(d, bw, bh):
    sky(d, (0, 0, bw, bh), (30, 45, 90), (70, 90, 140))
    for sx, sy in [(0.08, 0.08), (0.2, 0.05), (0.85, 0.06), (0.92, 0.14),
                   (0.7, 0.08), (0.05, 0.2), (0.95, 0.3)]:
        d.ellipse([sx * bw - 1, sy * bh - 1, sx * bw + 1, sy * bh + 1], fill=LIGHT)
    d.rectangle([0.12 * bw, 0.22 * bh, 0.58 * bw, 0.92 * bh], fill=(150, 140, 125))
    for r in range(4):
        for c in range(4):
            wx = (0.16 + c * 0.10) * bw
            wy = (0.28 + r * 0.15) * bh
            col = (250, 210, 90) if (r * 4 + c) % 3 == 0 else (60, 60, 70)
            d.rectangle([wx, wy, wx + 0.05 * bw, wy + 0.07 * bh], fill=col)
    burst(d, 0.72 * bw, 0.40 * bh, bw * 0.12)
    smoke(d, 0.78 * bw, 0.22 * bh, bw * 0.08)
    d.polygon([(0.68 * bw, 0.88 * bh), (0.76 * bw, 0.88 * bh), (0.72 * bw, 0.78 * bh)],
              fill=LIGHT)
    d.line([(0.72 * bw, 0.88 * bh), (0.80 * bw, 0.80 * bh)], fill=LIGHT, width=2)


def sc_poland(d, bw, bh):
    sky(d, (0, 0, bw, bh), (140, 190, 225), (210, 225, 235))
    d.polygon([(0, bh), (0, 0.72 * bh), (0.45 * bw, 0.55 * bh), (bw, 0.75 * bh), (bw, bh)],
              fill=(90, 160, 90))
    d.polygon([(0, bh), (0, 0.85 * bh), (0.5 * bw, 0.70 * bh), (bw, 0.88 * bh), (bw, bh)],
              fill=(60, 130, 70))
    for mx, my in [(0.20, 0.30), (0.45, 0.22), (0.68, 0.32)]:
        x0, y0 = mx * bw, my * bh
        d.line([(x0, y0), (x0 + 0.16 * bw, y0 + 0.16 * bh)], fill=(240, 140, 40), width=3)
        d.ellipse([x0 + 0.15 * bw, y0 + 0.15 * bh, x0 + 0.20 * bw, y0 + 0.20 * bh],
                  fill=(120, 120, 120))
        burst(d, x0 + 0.17 * bw, y0 + 0.17 * bh, bw * 0.035)


def sc_markets(d, bw, bh):
    d.rectangle([0, 0, bw, bh], fill=LIGHT)
    for gy in (0.2, 0.4, 0.6, 0.8):
        d.line([(0, gy * bh), (bw, gy * bh)], fill=(220, 220, 220), width=1)
    d.line([(0, 0.9 * bh), (bw, 0.9 * bh)], fill=(220, 220, 220), width=1)
    pts = [(0.05, 0.25), (0.25, 0.30), (0.45, 0.42), (0.65, 0.60), (0.85, 0.85)]
    xy = [(u * bw, v * bh) for u, v in pts]
    d.line(xy, fill=RED, width=4, joint="curve")
    for x, y in xy:
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=RED)
    ex, ey = xy[-1]
    d.polygon([(ex, ey + 12), (ex - 9, ey - 2), (ex + 9, ey - 2)], fill=RED)


def sc_houthi(d, bw, bh):
    sky(d, (0, 0, bw, bh), (250, 200, 130), (210, 140, 80))
    d.polygon([(0, bh), (0, 0.62 * bh), (0.12 * bw, 0.62 * bh), (0.12 * bw, 0.52 * bh),
               (0.24 * bw, 0.52 * bh), (0.24 * bw, 0.66 * bh), (0.38 * bw, 0.66 * bh),
               (0.38 * bw, 0.48 * bh), (0.52 * bw, 0.48 * bh), (0.52 * bw, 0.64 * bh),
               (0.68 * bw, 0.64 * bh), (0.68 * bw, 0.55 * bh), (0.82 * bw, 0.55 * bh),
               (0.82 * bw, 0.68 * bh), (bw, 0.68 * bh), (bw, bh)], fill=(45, 40, 55))
    d.line([(0.15 * bw, 0.85 * bh), (0.75 * bw, 0.15 * bh)], fill=LIGHT, width=3)
    burst(d, 0.68 * bw, 0.45 * bh, bw * 0.11)
    smoke(d, 0.74 * bw, 0.28 * bh, bw * 0.08)
    d.polygon([(0.30 * bw, 0.80 * bh), (0.36 * bw, 0.80 * bh), (0.33 * bw, 0.72 * bh)],
              fill=(20, 20, 20))


def sc_sudan(d, bw, bh):
    sky(d, (0, 0, bw, bh), (235, 200, 150), (200, 160, 110))
    d.rectangle([0.06 * bw, 0.55 * bh, 0.30 * bw, 0.92 * bh], fill=(190, 160, 110))
    d.rectangle([0.66 * bw, 0.50 * bh, 0.94 * bw, 0.92 * bh], fill=(180, 150, 100))
    d.rectangle([0.34 * bw, 0.42 * bh, 0.58 * bw, 0.92 * bh], fill=LIGHT)
    d.line([(0.46 * bw, 0.42 * bh), (0.46 * bw, 0.22 * bh)], fill=(80, 80, 80), width=2)
    d.polygon([(0.46 * bw, 0.22 * bh), (0.58 * bw, 0.26 * bh), (0.46 * bw, 0.30 * bh)],
              fill=BLUE)
    for r in range(2):
        for c in range(3):
            d.rectangle([(0.37 + c * 0.07) * bw, (0.50 + r * 0.14) * bh,
                         (0.41 + c * 0.07) * bw, (0.58 + r * 0.14) * bh],
                        fill=BLUE)
    burst(d, 0.72 * bw, 0.40 * bh, bw * 0.10)
    smoke(d, 0.78 * bw, 0.24 * bh, bw * 0.08)


def sc_westbank(d, bw, bh):
    sky(d, (0, 0, bw, bh), (40, 50, 80), (90, 90, 110))
    for sx, sy in [(0.1, 0.1), (0.5, 0.06), (0.85, 0.12), (0.3, 0.18)]:
        d.ellipse([sx * bw - 1, sy * bh - 1, sx * bw + 1, sy * bh + 1], fill=LIGHT)
    d.rectangle([0, 0.72 * bh, bw, bh], fill=(35, 30, 28))
    for cx, col in [(0.12, RED), (0.42, BLUE), (0.70, RED)]:
        x0, y0 = cx * bw, 0.62 * bh
        w, h = 0.22 * bw, 0.14 * bh
        d.rectangle([x0, y0, x0 + w, y0 + h], fill=col)
        d.rectangle([x0 + 0.03 * bw, y0 + 0.02 * bh, x0 + 0.09 * bw, y0 + 0.06 * bh],
                    fill=(200, 220, 235))
        d.rectangle([x0 + 0.12 * bw, y0 + 0.02 * bh, x0 + 0.18 * bw, y0 + 0.06 * bh],
                    fill=(200, 220, 235))
        for wx in (0.04, 0.15):
            d.ellipse([(x0 + wx * bw) - 4, y0 + h - 2, (x0 + wx * bw) + 4, y0 + h + 6],
                      fill=(20, 20, 20))
    burst(d, 0.24 * bw, 0.52 * bh, bw * 0.09)
    burst(d, 0.82 * bw, 0.52 * bh, bw * 0.09)
    smoke(d, 0.28 * bw, 0.34 * bh, bw * 0.07)
    smoke(d, 0.86 * bw, 0.34 * bh, bw * 0.07)


def sc_factory(d, bw, bh):
    sky(d, (0, 0, bw, bh), (200, 220, 235), (235, 230, 210))
    d.polygon([(0.08 * bw, 0.42 * bh), (0.50 * bw, 0.18 * bh), (0.92 * bw, 0.42 * bh)],
              fill=(120, 55, 40))
    d.rectangle([0.12 * bw, 0.42 * bh, 0.88 * bw, 0.92 * bh], fill=(150, 80, 60))
    d.rectangle([0.20 * bw, 0.22 * bh, 0.28 * bw, 0.42 * bh], fill=(120, 60, 45))
    d.rectangle([0.68 * bw, 0.22 * bh, 0.76 * bw, 0.42 * bh], fill=(120, 60, 45))
    smoke(d, 0.24 * bw, 0.14 * bh, bw * 0.06)
    smoke(d, 0.72 * bw, 0.14 * bh, bw * 0.06)
    for wx in (0.20, 0.44, 0.68):
        d.rectangle([wx * bw, 0.55 * bh, (wx + 0.10) * bw, 0.72 * bh],
                    fill=(250, 210, 90))


def sc_castle(d, bw, bh):
    sky(d, (0, 0, bw, bh), (150, 205, 235), (220, 235, 245))
    d.ellipse([0.82 * bw, 0.05 * bh, 0.95 * bw, 0.22 * bh], fill=(250, 210, 60))
    d.rectangle([0, 0.78 * bh, bw, bh], fill=(90, 160, 90))
    d.rectangle([0.06 * bw, 0.55 * bh, 0.22 * bw, 0.78 * bh], fill=(165, 50, 45))
    d.polygon([(0.04 * bw, 0.55 * bh), (0.14 * bw, 0.42 * bh), (0.24 * bw, 0.55 * bh)],
              fill=(140, 35, 30))
    d.rectangle([0.78 * bw, 0.55 * bh, 0.94 * bw, 0.78 * bh], fill=(165, 50, 45))
    d.polygon([(0.76 * bw, 0.55 * bh), (0.86 * bw, 0.42 * bh), (0.96 * bw, 0.55 * bh)],
              fill=(140, 35, 30))
    d.rectangle([0.32 * bw, 0.45 * bh, 0.68 * bw, 0.78 * bh], fill=(185, 60, 50))
    d.polygon([(0.28 * bw, 0.45 * bh), (0.50 * bw, 0.26 * bh), (0.72 * bw, 0.45 * bh)],
              fill=(150, 35, 30))
    for wx in (0.38, 0.48, 0.58):
        d.rectangle([wx * bw, 0.55 * bh, (wx + 0.05) * bw, 0.66 * bh],
                    fill=(250, 210, 90))


def sc_bepi(d, bw, bh):
    # R3-B: bigger Mercury disc + surface band, bigger spacecraft.
    d.rectangle([0, 0, bw, bh], fill=(12, 16, 34))
    for sx, sy in [(0.08, 0.08), (0.2, 0.05), (0.6, 0.06), (0.9, 0.1),
                   (0.55, 0.14), (0.95, 0.2), (0.05, 0.2), (0.85, 0.3)]:
        d.ellipse([sx * bw - 1, sy * bh - 1, sx * bw + 1, sy * bh + 1], fill=LIGHT)
    d.ellipse([0.06 * bw, 0.24 * bh, 0.52 * bw, 0.92 * bh], fill=(205, 150, 90))
    for cx, cy, cr in [(0.18, 0.40, 0.035), (0.30, 0.55, 0.045), (0.20, 0.68, 0.03),
                       (0.36, 0.72, 0.035), (0.28, 0.34, 0.025)]:
        d.ellipse([(cx - cr) * bw, (cy - cr) * bh, (cx + cr) * bw, (cy + cr) * bh],
                  fill=(170, 115, 60))
    # Mercury surface band along the bottom (curved horizon, clipped by tile)
    d.ellipse([-0.10 * bw, 0.82 * bh, 1.10 * bw, 1.30 * bh], fill=(170, 115, 60))
    for cx, cy, cr in [(0.20, 0.90, 0.02), (0.50, 0.94, 0.025), (0.80, 0.90, 0.02)]:
        d.ellipse([(cx - cr) * bw, (cy - cr) * bh, (cx + cr) * bw, (cy + cr) * bh],
                  fill=(140, 90, 50))
    # spacecraft ~1.5x: body + blue panel + thin solar wings + gold antenna/trail
    d.line([(0.60 * bw, 0.30 * bh), (0.78 * bw, 0.18 * bh)], fill=GOLD, width=2)
    d.rectangle([0.48 * bw, 0.42 * bh, 0.60 * bw, 0.52 * bh], fill=(40, 90, 180))
    d.rectangle([0.44 * bw, 0.44 * bh, 0.48 * bw, 0.50 * bh], fill=(30, 80, 160))
    d.rectangle([0.76 * bw, 0.44 * bh, 0.88 * bw, 0.50 * bh], fill=(30, 80, 160))
    d.rectangle([0.60 * bw, 0.34 * bh, 0.76 * bw, 0.58 * bh], fill=LIGHT,
                outline=(150, 150, 150))
    d.line([(0.68 * bw, 0.34 * bh), (0.68 * bw, 0.26 * bh)], fill=GOLD, width=2)
    d.ellipse([0.66 * bw, 0.24 * bh, 0.70 * bw, 0.28 * bh], fill=GOLD)


def sc_robots(d, bw, bh):
    # R3-C: UN assembly session - replaces the thin blue panel + small "128".
    d.rectangle([0, 0, bw, bh], fill=(40, 90, 160))
    f128 = sans(16, bold=True)
    t = "128"
    d.text(((bw - f128.getlength(t)) / 2, 1), t, font=f128, fill=LIGHT)
    d.line([(0.30 * bw, 20), (0.70 * bw, 20)], fill=GOLD, width=1)
    people_row(d, 0.08 * bw, 22, 0.84 * bw, 16, 5,
               palette=[(200, 60, 60), (60, 140, 220), (90, 180, 90),
                        (230, 180, 60), (150, 90, 200)])
    d.line([(0.04 * bw, 39), (0.96 * bw, 39)], fill=(20, 50, 100), width=2)
    for i, col in enumerate([BLUE, RED, (40, 140, 60)]):
        px = (0.22 + i * 0.28) * bw
        d.line([(px, 41), (px, 49)], fill=(220, 220, 220), width=1)
        d.rectangle([px, 41, px + 0.10 * bw, 46], fill=col)


SCENES = {"cop": sc_cop, "hormuz": sc_hormuz, "libya": sc_libya,
          "dymer": sc_dymer, "poland": sc_poland, "bepi": sc_bepi,
          "markets": sc_markets, "houthi": sc_houthi, "robots": sc_robots,
          "sudan": sc_sudan, "westbank": sc_westbank, "factory": sc_factory,
          "castle": sc_castle}


# ---------------------------------------------------------------- data
# story: (num, region, scene, chips, headline, deck, source)
LEADS = [
    (1, "GLOBAL", "cop", ["COP31: NO DEAL", "$120BN CUT"],
     "COP31 collapses with no deal",
     "Two days of overtime end in failure in Antalya: the draft never mentions fossil fuels and the $120bn adaptation target is dropped.",
     "IPS / Global Issues, 22 Nov"),
    (2, "MIDDLE EAST", "hormuz", ["6 TANKERS", "BRENT $92.44"],
     "Mines hit tankers in Hormuz",
     "Iran claims two more tankers struck by sea mines, six in two days; UKMTO reports a vessel hit by an unknown projectile. Iran's claim is unverified.",
     "AP via OilPrice, 23 Nov"),
    (3, "AFRICA", "libya", ["10 INJURED", "SHIP CAPSIZED"],
     "Russian warship struck in Libya",
     "Suspected Ukrainian sea drones hit the corvette Merkury at Benghazi. The ship is badly damaged and capsizes; Kyiv and Moscow silent.",
     "AP / Reuters / BBC Verify, 22 Nov"),
]

BRIEFS = [
    (4, "EUROPE", "dymer", ["2 KILLED"],
     "Drone hits Kyiv apartment block",
     "Russian drone strikes a 5-storey block in Dymer: 2 dead, 11 missing, among them 2 children.",
     "Al Jazeera / AP, 22 Nov"),
    (5, "EUROPE", "poland", ["3 MISSILES"],
     "Poland: debris was Russian missiles",
     "Three objects that fell on 20 Nov are confirmed as Russian cruise missiles; NATO is to meet.",
     "Reported 23 Nov"),
    (6, "GLOBAL", "bepi", ["2ND EVER"],
     "BepiColombo enters Mercury orbit",
     "The ESA-JAXA probe becomes only the second mission in history to orbit Mercury, on 21 Nov.",
     "Reported 22 Nov"),
    (7, "ASIA", "markets", ["-17.5%"],
     "Markets plunge; Taiwan bans shorting",
     "US stocks tumble; Taiwan shares fall 17.5% in a week; regulator bans short-selling from Monday.",
     "23 Nov"),
    (8, "MIDDLE EAST", "houthi", ["INTERCEPTED", "2 HURT"],
     "Houthi drone downed; Bahrain hit",
     "Coalition downs Houthi drone over Riyadh, missile in west; Iran strike injures 2 in Bahrain.",
     "AFP / CNBC, 22 Nov"),
    (9, "GLOBAL", "robots", ["128 NATIONS"],
     "128 nations back killer-robot rules",
     "At a UN conference, 128 countries agree to pursue international rules on autonomous weapons by 2028.",
     "23 Nov"),
    (10, "AFRICA", "sudan", ["UN SITE HIT"],
     "Drone strike hits Khartoum",
     "A drone attack damages a UN facility in Khartoum while staff are inside; 3 killed in Omdurman.",
     "AFP, 22 Nov"),
    (11, "MIDDLE EAST", "westbank", ["12 CARS TORCHED"],
     "Settlers torch cars near Ramallah",
     "Suspected settlers burn 12 Palestinian vehicles and spray graffiti in 4 villages overnight.",
     "22 Nov"),
    (12, "ASIA", "factory", ["24 BODY BAGS"],
     "24 dead in Indonesian candy factory fire",
     "Twenty-four body bags are recovered from a burnt-out sweets factory in Cikande, Banten.",
     "22 Nov"),
    (13, "ASIA", "castle", ["REOPENS TODAY"],
     "Shuri Castle rises again",
     "Okinawa's main hall, rebuilt seven years after the 2019 fire, opens to the public on Monday.",
     "22 Nov"),
]

# also: (headline, source, region)
ALSO = [
    ("FIFA to confirm UK as 2035 Women's World Cup host", "BBC, 23 Nov", "EUROPE"),
    ("Alcaraz beats Zverev 6-2, 7-6 to win first ATP Finals", "ATP, 22 Nov", "EUROPE"),
    ("Marquez seals 8th MotoGP title, equalling Agostini", "MotoGP, 22 Nov", "EUROPE"),
    ("Lahore world's most polluted city as AQI hits 538", "Dawn / IQAir, 22 Nov", "ASIA"),
    ("Bolsonaro 'stable' in intensive care in Brasilia", "AFP, 22 Nov", "AMERICAS"),
    ("South Sudan: 24 civilians killed, 7 of them children", "AFP, 22 Nov", "AFRICA"),
    ("Kim: North Korea seeks security, not supremacy", "KCNA, 23 Nov", "ASIA"),
    ("WHO chief pleads for peace in Ebola-hit DR Congo", "AFP, 22 Nov", "AFRICA"),
    ("Samsung Securities hack exposes 8,241 clients", "Korea JoongAng Daily, 23 Nov", "ASIA"),
    ("Democrats win 258 House seats, most since 1992", "Reuters, 22 Nov", "AMERICAS"),
    ("Netanyahu, Eisenkot end 4 hours of talks with no deal", "AFP, 22 Nov", "MIDDLE EAST"),
    ("Nigeria: 35 Fulani killed in reprisal attacks", "AFP, 22 Nov", "AFRICA"),
    ("Thitikul wins third straight LPGA finale, $4m", "AP, 22 Nov", "AMERICAS"),
    ("Liverpool thrash 10-man Manchester United 4-0", "Sky Sports, 22 Nov", "EUROPE"),
    ("South Korea minister quits over AI exam cheating", "AFP, 22 Nov", "ASIA"),
    ("Iran claims it downed a US MQ-9 drone", "Iran media, 22 Nov", "MIDDLE EAST"),
    ("Iran FM says Tehran still open to a US deal", "22 Nov", "MIDDLE EAST"),
    ("Broncos beat Raiders 38-24", "22 Nov", "AMERICAS"),
    ("South Sudan vote pushed back to February", "22 Nov", "AFRICA"),
    ("Canada says it has seen no Hegseth memo", "Reuters, 22 Nov", "AMERICAS"),
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

REGION_ORDER = ["AMERICAS", "MIDDLE EAST", "AFRICA", "EUROPE", "ASIA", "GLOBAL"]
REGION_COLORS = {"AMERICAS": BLUE, "MIDDLE EAST": RED, "AFRICA": (150, 110, 20),
                 "EUROPE": TEAL, "ASIA": (96, 64, 150), "GLOBAL": (70, 70, 70)}

LAND = {
    "N America": [(-168, 66), (-140, 70), (-120, 72), (-95, 80), (-75, 73), (-60, 62),
                  (-55, 47), (-70, 42), (-75, 35), (-80, 26), (-85, 20), (-95, 16),
                  (-105, 20), (-115, 30), (-125, 40), (-125, 50), (-150, 60), (-168, 66)],
    "S America": [(-80, 10), (-75, 5), (-70, -5), (-60, -10), (-50, -5), (-40, -5),
                  (-35, -10), (-40, -20), (-50, -30), (-60, -35), (-70, -40),
                  (-75, -50), (-70, -55), (-75, -40), (-75, -20), (-80, -5), (-80, 10)],
    "Europe": [(-10, 50), (-5, 48), (0, 51), (5, 55), (10, 58), (20, 60), (30, 70),
               (40, 68), (45, 60), (40, 50), (30, 45), (20, 44), (15, 40), (5, 43),
               (-2, 44), (-10, 50)],
    "Asia": [(40, 70), (70, 72), (110, 73), (150, 71), (175, 66), (165, 60),
             (155, 55), (145, 50), (140, 42), (135, 35), (128, 30), (122, 25),
             (115, 18), (108, 8), (104, 2), (100, 8), (96, 14), (92, 20), (88, 21),
             (84, 16), (80, 8), (76, 10), (72, 20), (68, 24), (62, 25), (57, 26),
             (52, 28), (48, 29), (44, 30), (40, 32), (38, 38), (36, 45), (40, 55),
             (40, 70)],
    "Africa": [(10, 35), (20, 32), (30, 31), (35, 28), (40, 20), (43, 12), (48, 11),
               (51, 12), (48, 5), (42, -2), (40, -10), (35, -18), (30, -25),
               (25, -30), (20, -35), (15, -30), (12, -18), (10, -5), (8, 4),
               (-8, 5), (-15, 12), (-17, 15), (-10, 20), (-5, 28), (0, 32), (10, 35)],
    "Australia": [(113, -22), (120, -30), (130, -32), (140, -38), (150, -37),
                  (153, -27), (146, -19), (142, -11), (135, -12), (130, -13),
                  (122, -14), (114, -22)],
}

PINS = {1: (30.7, 36.9), 2: (56.3, 26.6), 3: (20.1, 32.1), 4: (30.3, 50.8),
        5: (19.4, 52.0), 6: (8.6, 49.9), 7: (121.0, 23.7), 8: (50.5, 26.2),
        9: (6.1, 46.2), 10: (32.5, 15.6), 11: (35.2, 31.9), 12: (106.3, -6.2),
        13: (127.7, 26.2)}
NUDGE = {1: (18, -8), 3: (-14, 6), 6: (-16, -8), 7: (-8, 6), 9: (6, 8),
         10: (0, 8), 11: (10, 10), 13: (12, -8), 8: (0, 14)}


# ---------------------------------------------------------------- panel
def panel(img, draw, x, y, w, h, story, big):
    num, region, scene, chips, headline, deck, source = story
    draw.rectangle([x, y, x + w, y + h], fill=PANEL_BG, outline=PANEL_LINE, width=1)
    art_h = 90 if big else 50
    chip_h = 16 if big else 14
    chip_size = 10 if big else 9
    by = y + 4
    # badge row: number box + region + chips
    draw.rectangle([x + 1, by, x + 25, by + 18], fill=RED)
    nf = sans(12, bold=True)
    nt = str(num)
    draw.text((x + 13 - nf.getlength(nt) / 2, by + 2), nt, font=nf, fill=LIGHT)
    rf = sans(9, bold=True)
    rx = x + 30
    draw.text((rx, by + 4), region, font=rf, fill=RED)
    inline = rx + rf.getlength(region)
    chips_w = sum(int(sans(chip_size, bold=True).getlength(c)) + 12 + 6 for c in chips)
    two_rows = (inline + 6 + chips_w) > (x + w - 4)
    if two_rows:
        cy = by + 20
        art_y = y + 40
        art_h -= 14
    else:
        cy = by
        art_y = y + 22
    cx = rx + rf.getlength(region) + 6 if not two_rows else x + 4
    for c in chips:
        cx += chip(draw, int(cx), int(cy), c, chip_size, chip_h) + 6
    # art tile (clipped by construction)
    bw, bh = w - 2, art_h
    tile = Image.new("RGB", (bw, bh))
    td = ImageDraw.Draw(tile)
    SCENES[scene](td, bw, bh)
    img.paste(tile, (x + 1, art_y))
    # headline
    hy = art_y + art_h + 2
    src_y = y + h - 13
    avail_head = 2 * 18
    hf, hlines, hlh = fit_lines(draw, headline, 15 if big else 12, w - 8, 2,
                                avail_head, bold=True)
    block(draw, x + 4, hy, hlines, hf, INK, leading=hlh)
    dy = hy + len(hlines) * hlh + 1
    avail_deck = src_y - dy - 2
    df, dlines, dlh = fit_lines(draw, deck, 11 if big else 10, w - 8, 3,
                                max(avail_deck, 10), bold=False)
    block(draw, x + 4, dy, dlines, df, INK, leading=dlh)
    sf = sans(9 if big else 8)
    draw.text((x + 4, src_y), source, font=sf, fill=GREY)


# ---------------------------------------------------------------- layout
def main():
    img = Image.new("RGB", (1024, 1024), PAPER)
    draw = ImageDraw.Draw(img)
    y = 10
    # masthead
    draw.text((24, 10), "THE WORLD IN ONE DAY", font=sans(19, bold=True), fill=RED)
    rf = sans(11, bold=True)
    rt = "35 STORIES · 6 REGIONS · EVERY ONE DATED MONDAY 23 NOVEMBER 2026"
    draw.text((1000 - rf.getlength(rt), 12), rt, font=rf, fill=INK)
    y += 24
    hline(draw, 24, y, 976, fill=INK, width=3)
    y += 6
    tf = serif(46, bold=True)
    title = "Monday 23 November 2026"
    draw.text((512 - tf.getlength(title) / 2, y), title, font=tf, fill=INK)
    y += 54
    sub = " · ".join(s[4] for s in LEADS)
    sf = serif(15)
    sub_lines = wrap(sub, sf, 976)
    sub_h = block(draw, 24, y, sub_lines, sf, INK, align="center", center_x=512)
    y += sub_h + 4
    # stat strip
    for i, (num, label) in enumerate(STATS):
        bx = 24 + i * 163
        draw.rectangle([bx, y, bx + 158, y + 42], outline=PANEL_LINE, width=1)
        nf = sans(20, bold=True)
        draw.text((bx + 79 - nf.getlength(num) / 2, y + 3), num, font=nf, fill=RED)
        lf = sans(9)
        ll = wrap(label, lf, 150)
        block(draw, bx + 4, y + 22, ll, lf, INK, align="center", center_x=bx + 79,
              leading=10)
    y += 48
    # region strip
    rx = 24
    regions = {}
    for s in LEADS + BRIEFS:
        regions[s[1]] = regions.get(s[1], 0) + 1
    for _, _, r in ALSO:
        regions[r] = regions.get(r, 0) + 1
    total = sum(regions.values())
    assert total == 35, total
    for name in REGION_ORDER:
        label = "%s %d" % (name, regions[name])
        f = sans(11, bold=True)
        w = int(f.getlength(label)) + 16
        draw.rectangle([rx, y, rx + w, y + 18], fill=REGION_COLORS[name])
        draw.text((rx + 8, y + 3), label, font=f, fill=LIGHT)
        rx += w + 8
    gf = sans(11)
    gt = "13 STORIES MAPPED BELOW"
    draw.text((1000 - gf.getlength(gt), y + 3), gt, font=gf, fill=GREY)
    y += 26
    # leads
    for i, s in enumerate(LEADS):
        panel(img, draw, 24 + i * 328, y, 318, 202, s, True)
    y += 207
    # briefs: 2 rows x 5
    for i, s in enumerate(BRIEFS):
        col, row = i % 5, i // 5
        panel(img, draw, 24 + col * 196, y + row * 156, 188, 150, s, False)
    y += 306
    # map
    draw.text((24, y), "WHERE IT HAPPENED", font=sans(15, bold=True), fill=INK)
    mf = sans(10)
    mt = "13 STORIES, NUMBERED 1–13"
    draw.text((1000 - mf.getlength(mt), y + 3), mt, font=mf, fill=GREY)
    y += 18
    my = y
    draw.rectangle([24, my, 1000, my + 78], fill=(198, 218, 236),
                   outline=PANEL_LINE, width=1)

    def proj(lon, lat):
        return 24 + (lon + 180) / 360 * 976, my + (75 - lat) / 130 * 78

    for pts in LAND.values():
        xy = [proj(lon, lat) for lon, lat in pts]
        draw.polygon(xy, fill=TAN)
        draw.line(xy + [xy[0]], fill=PAPER, width=3, joint="curve")
        draw.line(xy + [xy[0]], fill=(170, 145, 95), width=2, joint="curve")
    centers = {}
    for num, (lon, lat) in PINS.items():
        px, py = proj(lon, lat)
        dx, dy = NUDGE.get(num, (0, 0))
        cx = min(max(px + dx, 32), 992)
        cy = min(max(py + dy, my + 9), my + 69)
        centers[num] = (cx, cy)
        if (dx, dy) != (0, 0):
            draw.line([(px, py), (cx, cy)], fill=RED, width=1)
            draw.ellipse([px - 2, py - 2, px + 2, py + 2], fill=RED)
        draw.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=RED, outline=LIGHT, width=2)
        pf = sans(9, bold=True)
        t = str(num)
        draw.text((cx - pf.getlength(t) / 2, cy - 5), t, font=pf, fill=LIGHT)
    nums = sorted(centers)
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            a, b = centers[nums[i]], centers[nums[j]]
            dist = ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5
            if dist < 16:
                RISKS.append("PIN CLOSE: %d-%d %.1fpx" % (nums[i], nums[j], dist))
    y += 84
    # ALSO ON
    draw.text((24, y), "ALSO ON MONDAY — 22 MORE STORIES", font=sans(14, bold=True),
              fill=INK)
    y += 18
    af = sans(10)
    for i, (headline, source, _r) in enumerate(ALSO):
        col, row = i // 11, i % 11
        ix = 24 if col == 0 else 520
        iy = y + row * 10
        draw.text((ix, iy), "•", font=af, fill=RED)
        txt = "%s (%s)" % (headline, source)
        if af.getlength(txt) > 468:
            RISKS.append("ALSO WIDE: %s" % txt[:40])
        draw.text((ix + 12, iy), txt, font=af, fill=INK)
    y += 116
    # DATE CHECK
    draw.rectangle([24, y, 1000, y + 62], fill=(255, 240, 240), outline=RED, width=2)
    draw.text((34, y + 4), "DATE CHECK — LEFT OUT ON PURPOSE (NOT 23 NOVEMBER NEWS)",
              font=sans(11, bold=True), fill=RED)
    qual = ("Every story here was reported or still developing on Monday "
            "23 November 2026, in at least one time zone.")
    qsize = 9
    qf = sans(qsize)
    if qf.getlength(qual) > 966:
        qsize = 8
        qf = sans(qsize)
    draw_italic(img, 34, y + 16, qual, qf, INK)
    df9 = sans(9)
    for i, item in enumerate(DATE_CHECK):
        col, row = i // 3, i % 3
        ix = 34 if col == 0 else 520
        draw.text((ix, y + 28 + row * 11), "✕ " + item, font=df9, fill=INK)
    y += 68
    # footer
    hline(draw, 24, y, 976, fill=PANEL_LINE, width=1)
    ff = sans(9)
    draw.text((24, y + 3),
              "Sources: Reuters · AP · AFP · BBC · Al Jazeera · IPS · OilPrice · ATP · "
              "MotoGP · Dawn · IQAir · KCNA · Sky Sports", font=ff, fill=GREY)
    bf = sans(9, bold=True)
    bt = "quick-lynx-56 · make.fun"
    draw.text((1000 - bf.getlength(bt), y + 3), bt, font=bf, fill=GREY)
    y += 14
    final_y = y
    here = os.path.dirname(os.path.abspath(__file__))
    img.save(os.path.join(here, "entry.png"), optimize=True)
    print("final_y=%d regions=%s RISKS=%s" % (
        final_y, {k: regions[k] for k in REGION_ORDER},
        "none" if not RISKS else "; ".join(RISKS)))


if __name__ == "__main__":
    main()
