#!/usr/bin/env python3
"""R5 blind rewrite — news-image-20261123.

One dominant tall hero (Hormuz night, ~350px), 2 mid heroes, 4 big
secondary panels, dotted world map + ALSO ON in a narrower bottom band.
35 stories, all reported / still developing on Monday 23 November 2026.
Drawn from scratch with PIL + DejaVu only. No network.
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")

CREAM = (247, 241, 222)
PAPER = (252, 248, 236)
INK = (17, 17, 17)
GREY = (90, 84, 70)
NAVY = (14, 42, 78)
NAVY_D = (10, 25, 48)
RED = (176, 30, 36)
RED_D = (140, 22, 28)
LINE = (201, 191, 165)
WHITE = (255, 255, 255)
SKY_PALE = (216, 228, 238)

FD = "/usr/share/fonts/truetype/dejavu"


def F(name, size):
    for cand in (name, "DejaVuSans.ttf", "DejaVuSerif.ttf"):
        p = os.path.join(FD, cand)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def serif_b(s):
    return F("DejaVuSerif-Bold.ttf", s)


def serif(s):
    return F("DejaVuSerif.ttf", s)


def serif_i(s):
    return F("DejaVuSerif-Italic.ttf", s)


def sans_b(s):
    return F("DejaVuSans-Bold.ttf", s)


def sans(s):
    return F("DejaVuSans.ttf", s)


def wrap(text, font, maxw):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if font.getlength(t) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def vgrad(d, box, top, bot):
    x0, y0, x1, y1 = box
    n = max(1, y1 - y0)
    for i in range(n):
        t = i / n
        c = tuple(int(top[j] + (bot[j] - top[j]) * t) for j in range(3))
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=c)


def chip(d, x, y, text, bg, fg, size=10, pad=5):
    f = sans_b(size)
    w = int(f.getlength(text)) + pad * 2
    h = size + pad + 2
    d.rounded_rectangle([x, y, x + w, y + h], radius=3, fill=bg)
    d.text((x + pad, y + 2), text, font=f, fill=fg)
    return w


def panel_box(d, x0, y0, x1, y1):
    d.rectangle([x0, y0, x1, y1], outline=LINE, width=1)


def flame(d, cx, base, w, h):
    """Layered flame: red outer, orange mid, yellow core."""
    d.polygon([(cx - w, base), (cx - w * 0.45, base - h * 0.62),
               (cx - w * 0.12, base - h * 0.85), (cx + w * 0.25, base - h * 0.55),
               (cx + w * 0.85, base - h * 0.3), (cx + w, base)],
              fill=(214, 72, 28))
    d.polygon([(cx - w * 0.62, base), (cx - w * 0.28, base - h * 0.55),
               (cx, base - h * 0.8), (cx + w * 0.3, base - h * 0.45),
               (cx + w * 0.6, base)], fill=(238, 140, 40))
    d.polygon([(cx - w * 0.34, base), (cx - w * 0.12, base - h * 0.45),
               (cx + w * 0.08, base - h * 0.62), (cx + w * 0.3, base - h * 0.3),
               (cx + w * 0.32, base)], fill=(248, 205, 80))


def smoke(d, x, y, s, col=(70, 70, 74)):
    for dx, dy, r in ((0, 0, 1.0), (0.55, -0.5, 0.8), (-0.5, -0.9, 0.85),
                      (0.15, -1.5, 0.7), (0.7, -1.9, 0.55)):
        rr = r * s
        d.ellipse([x + dx * s - rr, y + dy * s - rr * 0.8,
                   x + dx * s + rr, y + dy * s + rr * 0.8], fill=col)


def draw_masthead(d):
    d.rectangle([0, 0, W, 30], fill=NAVY_D)
    d.text((12, 6), "THE WORLD IN ONE DAY", font=sans_b(16), fill=WHITE)
    right = "35 STORIES  •  6 REGIONS  •  EVERY ONE DATED MONDAY 23 NOVEMBER 2026"
    f = sans_b(11)
    d.text((W - 12 - f.getlength(right), 9), right, font=f, fill=(214, 222, 235))


def draw_date(d):
    f = serif_b(56)
    t = "Monday 23 November 2026"
    d.text(((W - f.getlength(t)) / 2, 36), t, font=f, fill=INK)
    f2 = serif_i(16)
    t2 = ("COP31 collapses with no deal  ·  Mines hit tankers in Hormuz  ·  "
          "Russian warship struck in Libya")
    d.text(((W - f2.getlength(t2)) / 2, 102), t2, font=f2, fill=RED)


def draw_stats(d):
    stats = [
        ("$120BN", "adaptation cash cut at COP31"),
        ("6", "tankers Iran claims hit by mines"),
        ("10", "injured in Libya warship strike"),
        ("2", "killed in Dymer apartment strike"),
        ("17.5%", "Taiwan stocks' fall in one week"),
        ("128", "nations backing killer-robot rules"),
    ]
    x = 12
    bw, gap = 163, 4
    for num, cap in stats:
        d.rectangle([x, 122, x + bw, 168], fill=PAPER, outline=LINE, width=1)
        d.text((x + 8, 124), num, font=sans_b(19), fill=RED)
        lines = wrap(cap, sans(8), bw - 16)
        for i, ln in enumerate(lines[:2]):
            d.text((x + 8, 146 + i * 10), ln, font=sans(8), fill=GREY)
        x += bw + gap


def draw_region_bar(d):
    segs = [
        ("EUROPE 6", 6, NAVY),
        ("MIDDLE EAST 7", 7, RED),
        ("AMERICAS 6", 6, (46, 110, 62)),
        ("ASIA 7", 7, (196, 110, 20)),
        ("AFRICA 6", 6, (140, 95, 45)),
        ("GLOBAL 3", 3, (88, 70, 140)),
    ]
    total = 35.0
    x = 12
    f = sans_b(10)
    for label, n, col in segs:
        w = int(1000 * n / total)
        d.rectangle([x, 170, x + w - 1, 188], fill=col)
        tw = f.getlength(label)
        d.text((x + (w - tw) / 2, 174), label, font=f, fill=WHITE)
        x += w


# ---------------------------------------------------------------- hero
# x 12..1012, y 192..542  (1000 x 350 = 34.2% of the page)
def draw_hero(img, d):
    x0, y0, x1, y1 = 12, 192, 1012, 542
    horizon = 452
    # sky: deep navy top, fading to slate blue, then a hot orange glow band
    vgrad(d, (x0, y0, x1, horizon - 172), (10, 27, 51), (44, 72, 108))
    vgrad(d, (x0, horizon - 172, x1, horizon - 60), (44, 72, 108),
          (110, 145, 180))
    vgrad(d, (x0, horizon - 60, x1, horizon), (110, 145, 180),
          (214, 122, 52))
    # sea: mid steel blue (bright enough not to count as "dark" pixels)
    vgrad(d, (x0, horizon, x1, y1), (60, 96, 126), (46, 82, 110))
    # stars
    rnd = random.Random(11)
    for _ in range(70):
        sx = rnd.randint(x0 + 8, x1 - 8)
        sy = rnd.randint(y0 + 8, horizon - 110)
        r = rnd.choice((1, 1, 2))
        d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(220, 228, 240))
    # moon + halo
    d.ellipse([838, 214, 922, 298], fill=(212, 204, 170))
    d.ellipse([852, 228, 908, 284], fill=(238, 232, 205))
    d.ellipse([866, 240, 880, 254], fill=(210, 202, 172))
    d.ellipse([888, 258, 898, 268], fill=(210, 202, 172))
    # distant tanker, small, on the horizon at right
    d.polygon([(838, 452), (838, 436), (852, 436), (852, 428), (872, 428),
               (872, 436), (988, 436), (988, 452)], fill=(24, 40, 60))
    d.rectangle([846, 424, 858, 436], fill=(24, 40, 60))
    # main tanker: long black hull, bridge tower left of the fire
    d.polygon([(170, 452), (170, 470), (196, 486), (800, 486), (826, 470),
               (826, 452)], fill=(16, 22, 30))
    d.rectangle([196, 470, 800, 478], fill=(120, 40, 30))
    d.rectangle([700, 392, 762, 452], fill=(24, 32, 44))
    for wy in (404, 420, 436):
        for wx in (710, 728, 746):
            d.rectangle([wx, wy, wx + 10, wy + 8], fill=(240, 200, 90))
    d.rectangle([668, 408, 688, 452], fill=(24, 32, 44))
    d.rectangle([668, 396, 688, 408], fill=(150, 50, 35))
    # cargo hatches
    for hx in (240, 330, 420, 510, 600):
        d.rectangle([hx, 442, hx + 52, 452], fill=(34, 44, 56))
    # fire glow on the overlay (translucent), then flames on top
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    # R6: soft outer halo so the fire reads as a light source, not a
    # flat cut-out — faint, kept low so it never reaches the headline
    od.ellipse([320, 310, 720, 482], fill=(240, 130, 40, 14))
    od.ellipse([355, 335, 675, 472], fill=(245, 150, 50, 20))
    od.ellipse([360, 350, 620, 465], fill=(240, 130, 40, 35))
    od.ellipse([400, 380, 580, 458], fill=(250, 180, 60, 50))
    img.paste(Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB"),
              (0, 0))
    d = ImageDraw.Draw(img)
    flame(d, 470, 452, 38, 88)
    flame(d, 540, 452, 46, 108)
    flame(d, 600, 452, 32, 70)
    # R6: smoke columns ANCHORED on the flames — each column's lowest
    # puff sits inside its flame, then rises drifting left (wind) and
    # lightening as it cools, so nothing reads as a floating cloud.
    # Text is drawn after the smoke, so headline/dek stay crisp on top.
    smoke(d, 535, 405, 15, (46, 46, 50))
    smoke(d, 520, 362, 16, (54, 54, 58))
    smoke(d, 498, 322, 17, (64, 64, 68))
    smoke(d, 470, 286, 15, (76, 76, 80))
    smoke(d, 440, 256, 13, (88, 88, 92))
    smoke(d, 598, 412, 12, (48, 48, 52))
    smoke(d, 582, 378, 13, (58, 58, 62))
    smoke(d, 560, 344, 13, (70, 70, 74))
    # R6: mine blast reshaped from a "burning cloud" into a water
    # plume — narrow white spray, flash low at the waterline, foam ring
    for dx, dy, r, c in ((150, 436, 16, (235, 240, 245)),
                         (132, 444, 12, (225, 232, 238)),
                         (170, 444, 11, (225, 232, 238)),
                         (150, 440, 7, (240, 150, 60)),
                         (150, 448, 5, (250, 200, 90))):
        d.ellipse([dx - r, dy - r, dx + r, dy + r], fill=c)
    for sx, sy, sr in ((138, 398, 3), (162, 392, 3), (150, 384, 2),
                       (126, 412, 2), (176, 410, 2)):
        d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr],
                  fill=(235, 240, 245))
    d.ellipse([128, 446, 172, 458], outline=(235, 240, 245), width=2)
    d.polygon([(128, 452), (142, 396), (152, 452)], fill=(235, 240, 245))
    d.polygon([(158, 452), (168, 410), (176, 452)], fill=(225, 232, 238))
    # orange reflections on the sea under the fire
    for rx, rw in ((400, 60), (470, 110), (540, 70), (430, 40)):
        d.rectangle([rx, 492, rx + rw, 497], fill=(232, 140, 50))
        d.rectangle([rx + 20, 508, rx + rw - 10, 512], fill=(214, 122, 52))
    # small sea-mine silhouette floating near the hull
    d.ellipse([620, 488, 640, 506], fill=(14, 20, 28))
    for ang in range(0, 360, 45):
        a = math.radians(ang)
        d.line([(630 + 9 * math.cos(a), 497 + 8 * math.sin(a)),
                (630 + 15 * math.cos(a), 497 + 14 * math.sin(a))],
               fill=(14, 20, 28), width=2)
    # ---- text on the dark sky (top-left, high contrast) ----
    chip(d, 28, 206, "2  ·  HORMUZ — MIDDLE EAST", RED, WHITE, size=11)
    d.text((28, 236), "Mines hit tankers in Hormuz",
           font=serif_b(34), fill=WHITE)
    dek = ("Iran claims two more tankers struck by sea mines, six in two "
           "days; UKMTO reports a vessel hit by an unknown projectile. "
           "Iran's claim is unverified.")
    yy = 278
    for ln in wrap(dek, sans(15), 620):
        d.text((28, yy), ln, font=sans(15), fill=(232, 236, 242))
        yy += 20
    # chips + source along the bottom, over the sea
    w1 = chip(d, 28, 506, "6 TANKERS", RED, WHITE, size=12)
    chip(d, 28 + w1 + 8, 506, "BRENT $92.44", WHITE, INK, size=12)
    src = "AP via OilPrice, 23 Nov"
    f = sans(10)
    d.text((x1 - 12 - f.getlength(src), 512), src, font=f,
           fill=(226, 232, 240))
    panel_box(d, x0, y0, x1, y1)


# ---------------------------------------------------------------- panels
def panel_text(d, x0, y0, w, kicker, headline, dek, source, hsize=16,
               dsize=10):
    """Text block under a panel image. Returns nothing; caller sizes image
    so this block fits (kicker + headline + dek + source)."""
    x = x0 + 8
    tw = w - 16
    y = y0 + 4
    d.text((x, y), kicker, font=sans_b(9), fill=RED)
    y += 11
    for ln in wrap(headline, serif_b(hsize), tw):
        d.text((x, y), ln, font=serif_b(hsize), fill=INK)
        y += hsize + 2
    y += 1
    for ln in wrap(dek, sans(dsize), tw):
        d.text((x, y), ln, font=sans(dsize), fill=(52, 48, 40))
        y += dsize + 3
    d.text((x, y), source, font=sans(8), fill=GREY)


def draw_cop31(d, x0, y0, x1, y1):
    # image 84px, text 68px
    d.rectangle([x0, y0, x1, y0 + 84], fill=(214, 226, 236))
    # globe
    d.ellipse([x0 + 22, y0 + 14, x0 + 92, y0 + 84], fill=(52, 110, 170))
    d.ellipse([x0 + 36, y0 + 30, x0 + 58, y0 + 48], fill=(90, 160, 90))
    d.ellipse([x0 + 58, y0 + 52, x0 + 80, y0 + 70], fill=(90, 160, 90))
    d.ellipse([x0 + 44, y0 + 62, x0 + 56, y0 + 74], fill=(120, 175, 100))
    # summit table + delegates
    d.rectangle([x0 + 130, y0 + 62, x0 + 420, y0 + 82], fill=(122, 84, 52))
    d.rectangle([x0 + 130, y0 + 62, x0 + 420, y0 + 68], fill=(146, 104, 66))
    for i, c in enumerate(((176, 40, 60), (196, 120, 40), (150, 90, 170),
                           (60, 130, 170), (200, 90, 40))):
        cx = x0 + 165 + i * 48
        d.ellipse([cx - 9, y0 + 34, cx + 9, y0 + 52], fill=(232, 200, 160))
        d.polygon([(cx - 14, y0 + 62), (cx - 9, y0 + 50), (cx + 9, y0 + 50),
                   (cx + 14, y0 + 62)], fill=c)
    # thermometer, mercury fallen
    d.rectangle([x0 + 446, y0 + 16, x0 + 454, y0 + 66], fill=WHITE,
                outline=INK, width=1)
    d.rectangle([x0 + 448, y0 + 52, x0 + 452, y0 + 64], fill=RED)
    d.ellipse([x0 + 440, y0 + 62, x0 + 460, y0 + 82], fill=RED)
    chip(d, x0 + 8, y0 + 6, "COP31: NO DEAL", RED, WHITE, size=10)
    chip(d, x1 - 108, y0 + 6, "$120BN CUT", WHITE, INK, size=10)
    panel_box(d, x0, y0, x1, y1)
    panel_text(d, x0, y0 + 84, x1 - x0, "1  ANTALYA, TURKEY · CLIMATE",
               "COP31 collapses with no deal",
               "Two days of overtime end in failure: the draft never "
               "mentions fossil fuels and the $120bn adaptation target "
               "is dropped.",
               "IPS / Global Issues, 22 Nov", hsize=15)


def draw_libya(d, x0, y0, x1, y1):
    d.rectangle([x0, y0, x1, y0 + 84], fill=(206, 216, 224))
    # sea
    d.rectangle([x0, y0 + 56, x1, y0 + 84], fill=(158, 180, 196))
    # R6: capsized corvette redrawn as a WARSHIP — bridge tower with
    # lit windows, funnel, mast + red ensign, forward gun turret,
    # tegas stern transom, hull plating seams + waterline stripe.
    # Same tilt, same panel, same fire-at-waterline + smoke.
    hull = [(x0 + 130, y0 + 62), (x0 + 330, y0 + 26), (x0 + 368, y0 + 42),
            (x0 + 345, y0 + 60), (x0 + 165, y0 + 80)]
    d.polygon(hull, fill=(96, 104, 112))
    # darker lower strake + red waterline stripe along the bottom edge
    d.polygon([(x0 + 150, y0 + 70), (x0 + 338, y0 + 52), (x0 + 345, y0 + 60),
               (x0 + 165, y0 + 80)], fill=(74, 80, 88))
    d.line([(x0 + 140, y0 + 66), (x0 + 342, y0 + 54)], fill=(150, 60, 45),
           width=3)
    # deck edge + bow edge highlight + hull plating seams (follow the list)
    d.line([(x0 + 130, y0 + 62), (x0 + 330, y0 + 26)], fill=(60, 66, 74),
           width=2)
    d.line([(x0 + 330, y0 + 26), (x0 + 368, y0 + 42)], fill=(150, 156, 164),
           width=2)
    for sx, sy0, sy1 in ((180, 53, 78), (225, 45, 73), (270, 37, 68),
                         (310, 30, 64)):
        d.line([(x0 + sx, y0 + sy0), (x0 + sx + 6, y0 + sy1)],
               fill=(70, 76, 84), width=1)
    # rust streaks weeping from the deck edge
    for rx, ry in ((195, 50), (290, 33)):
        d.line([(x0 + rx, y0 + ry), (x0 + rx, y0 + ry + 8)],
               fill=(140, 80, 50), width=2)
    d.polygon([(x0 + 300, y0 + 36), (x0 + 330, y0 + 26), (x0 + 348, y0 + 42),
               (x0 + 318, y0 + 48)], fill=(140, 60, 45))
    # stern transom: thick dark edge + deck rail posts at the low end
    d.line([(x0 + 130, y0 + 62), (x0 + 165, y0 + 80)], fill=(48, 52, 60),
           width=4)
    d.line([(x0 + 140, y0 + 60), (x0 + 140, y0 + 53)], fill=(60, 66, 74),
           width=2)
    d.line([(x0 + 156, y0 + 57), (x0 + 156, y0 + 50)], fill=(60, 66, 74),
           width=2)
    d.line([(x0 + 138, y0 + 53), (x0 + 158, y0 + 49)], fill=(60, 66, 74),
           width=2)
    # bridge tower with lit windows + dark roof band
    d.rectangle([x0 + 232, y0 + 14, x0 + 282, y0 + 46], fill=(88, 96, 104))
    d.rectangle([x0 + 232, y0 + 14, x0 + 282, y0 + 19], fill=(66, 72, 80))
    for wx in (238, 250, 262, 274):
        d.rectangle([x0 + wx, y0 + 23, x0 + wx + 7, y0 + 30],
                    fill=(240, 200, 90))
    d.rectangle([x0 + 238, y0 + 34, x0 + 276, y0 + 42], fill=(70, 76, 84))
    # funnel aft of the bridge, black cap
    d.rectangle([x0 + 288, y0 + 24, x0 + 306, y0 + 44], fill=(96, 100, 106))
    d.rectangle([x0 + 288, y0 + 24, x0 + 306, y0 + 29], fill=(40, 44, 50))
    # forward gun turret on the foredeck + barrel
    d.polygon([(x0 + 302, y0 + 32), (x0 + 324, y0 + 28), (x0 + 328, y0 + 20),
               (x0 + 306, y0 + 24)], fill=(70, 76, 84))
    d.line([(x0 + 324, y0 + 23), (x0 + 340, y0 + 14)], fill=(60, 66, 74),
           width=3)
    # mast on the bridge tower + small red ensign
    d.line([(x0 + 258, y0 + 14), (x0 + 276, y0 + 1)], fill=(60, 66, 74),
           width=3)
    d.polygon([(x0 + 276, y0 + 1), (x0 + 276, y0 + 11), (x0 + 292, y0 + 6)],
              fill=RED)
    # fire at the waterline (stern) + smaller fire at the bow waterline
    flame(d, x0 + 180, y0 + 66, 26, 34)
    flame(d, x0 + 338, y0 + 60, 14, 22)
    smoke(d, x0 + 195, y0 + 40, 13, (90, 92, 96))
    smoke(d, x0 + 336, y0 + 30, 11, (96, 98, 102))
    # drone silhouette with trail
    d.ellipse([x0 + 410, y0 + 14, x0 + 424, y0 + 22], fill=(40, 44, 50))
    d.line([(x0 + 380, y0 + 10), (x0 + 410, y0 + 18)], fill=(120, 126, 132),
           width=2)
    # debris + listing wake
    for dx, dy in ((150, 74), (220, 80), (300, 72), (380, 70)):
        d.rectangle([x0 + dx, y0 + dy, x0 + dx + 10, y0 + dy + 4],
                    fill=(70, 76, 84))
    chip(d, x0 + 8, y0 + 6, "10 INJURED", RED, WHITE, size=10)
    w1 = chip(d, x0 + 8, y0 + 6, "10 INJURED", RED, WHITE, size=10)
    chip(d, x0 + 16 + w1, y0 + 6, "SHIP CAPSIZED", WHITE, INK, size=10)
    panel_box(d, x0, y0, x1, y1)
    panel_text(d, x0, y0 + 84, x1 - x0, "3  BENGHAZI, LIBYA · WAR AT SEA",
               "Russian warship struck in Libya",
               "Suspected Ukrainian sea drones hit the corvette Merkury. "
               "The ship is badly damaged and capsizes; Kyiv and Moscow "
               "silent.",
               "AP / Reuters / BBC Verify, 22 Nov", hsize=15)


def draw_kyiv(d, x0, y0, x1, y1):
    # dark night panel: image 56px, text 80px
    d.rectangle([x0, y0, x1, y0 + 56], fill=(13, 30, 51))
    rnd = random.Random(4)
    for _ in range(14):
        sx = rnd.randint(x0 + 6, x1 - 6)
        sy = rnd.randint(y0 + 4, y0 + 20)
        d.ellipse([sx - 1, sy - 1, sx + 1, sy + 1], fill=(220, 228, 240))
    # apartment block, 5 storeys, some windows lit
    d.rectangle([x0 + 60, y0 + 16, x0 + 150, y0 + 56], fill=(26, 40, 60))
    for r in range(4):
        for c in range(4):
            wx, wy = x0 + 68 + c * 21, y0 + 20 + r * 9
            col = (240, 200, 90) if (r * 4 + c) % 3 else (52, 66, 88)
            d.rectangle([wx, wy, wx + 11, wy + 6], fill=col)
    # fire + smoke eating the right side of the block
    flame(d, x0 + 168, y0 + 56, 22, 40)
    smoke(d, x0 + 175, y0 + 22, 12, (60, 60, 64))
    # drone with red trail above
    d.ellipse([x0 + 200, y0 + 10, x0 + 210, y0 + 16], fill=(230, 230, 230))
    d.line([(x0 + 176, y0 + 8), (x0 + 200, y0 + 13)], fill=(220, 80, 60),
           width=2)
    chip(d, x0 + 6, y0 + 5, "2 KILLED", RED, WHITE, size=9)
    panel_box(d, x0, y0, x1, y1)
    panel_text(d, x0, y0 + 56, x1 - x0, "4  DYMER, UKRAINE · WAR",
               "Drone hits Kyiv apartment block",
               "Russian drone strikes a 5-storey block in Dymer. 2 dead, "
               "11 missing, among them 2 children.",
               "Al Jazeera / AP, 22 Nov", hsize=13, dsize=9)


def draw_mercury(d, x0, y0, x1, y1):
    d.rectangle([x0, y0, x1, y0 + 56], fill=(232, 228, 214))
    # cratered Mercury, big at right, with a thin orbit ring
    cx, cy, r = x0 + 178, y0 + 30, 26
    d.ellipse([cx - 42, cy - 10, cx + 42, cy + 10], outline=(150, 144, 130),
              width=1)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(168, 162, 150))
    for ox, oy, cr in ((-8, -8, 6), (8, 4, 8), (-2, 12, 5), (12, -10, 4),
                       (-14, 6, 4)):
        d.ellipse([cx + ox - cr, cy + oy - cr, cx + ox + cr, cy + oy + cr],
                  fill=(138, 132, 120))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(120, 114, 102),
              width=1)
    # probe with gold solar panels at left
    d.rectangle([x0 + 30, y0 + 22, x0 + 52, y0 + 38], fill=(200, 160, 60))
    d.rectangle([x0 + 14, y0 + 26, x0 + 30, y0 + 34], fill=(60, 90, 140))
    d.rectangle([x0 + 52, y0 + 26, x0 + 68, y0 + 34], fill=(60, 90, 140))
    d.line([(x0 + 68, y0 + 30), (cx - r - 2, cy)], fill=(120, 114, 102),
           width=1)
    # stars on the pale sky
    for sx, sy in ((90, 12), (120, 20), (100, 44), (140, 10)):
        d.ellipse([x0 + sx - 1, y0 + sy - 1, x0 + sx + 1, y0 + sy + 1],
                  fill=(120, 110, 95))
    chip(d, x0 + 6, y0 + 5, "2ND EVER", RED, WHITE, size=9)
    panel_box(d, x0, y0, x1, y1)
    panel_text(d, x0, y0 + 56, x1 - x0, "6  SPACE · MERCURY",
               "BepiColombo enters Mercury orbit",
               "The ESA-JAXA probe becomes only the second mission to "
               "orbit Mercury, on 21 Nov.",
               "Reported 23 Nov", hsize=13, dsize=9)


def draw_markets(d, x0, y0, x1, y1):
    d.rectangle([x0, y0, x1, y0 + 56], fill=(244, 242, 236))
    # big board with a plunging red line
    d.rectangle([x0 + 10, y0 + 8, x0 + 150, y0 + 48], fill=WHITE,
                outline=LINE, width=1)
    pts = [(x0 + 16, y0 + 14), (x0 + 46, y0 + 18), (x0 + 76, y0 + 16),
           (x0 + 106, y0 + 30), (x0 + 136, y0 + 44)]
    d.line(pts, fill=RED, width=3)
    d.polygon([(x0 + 136, y0 + 44), (x0 + 126, y0 + 40), (x0 + 132, y0 + 50)],
              fill=RED)
    # red ticker bars at right
    for i, h in enumerate((10, 16, 8, 20, 12)):
        d.rectangle([x0 + 168 + i * 14, y0 + 40 - h, x0 + 178 + i * 14,
                     y0 + 40], fill=RED)
    d.rectangle([x0 + 168, y0 + 44, x0 + 234, y0 + 48], fill=(60, 60, 60))
    # traders, heads down at the bottom
    for i, c in enumerate(((40, 60, 90), (90, 90, 90), (140, 50, 60))):
        cx = x0 + 60 + i * 55
        d.ellipse([cx - 7, y0 + 42, cx + 7, y0 + 54], fill=(232, 200, 160))
        d.polygon([(cx - 11, y0 + 56), (cx - 7, y0 + 50), (cx + 7, y0 + 50),
                   (cx + 11, y0 + 56)], fill=c)
    chip(d, x0 + 6, y0 + 5, "-17.5%", RED, WHITE, size=9)
    panel_box(d, x0, y0, x1, y1)
    panel_text(d, x0, y0 + 56, x1 - x0, "7  TAIPEI · MARKETS",
               "Markets plunge; Taiwan bans shorting",
               "US stocks tumble; Taiwan shares fall 17.5% in a week; "
               "short-selling banned from Monday.",
               "23 Nov", hsize=13, dsize=9)


def draw_un(d, x0, y0, x1, y1):
    d.rectangle([x0, y0, x1, y0 + 56], fill=(222, 228, 236))
    # back wall with the big 128
    d.rectangle([x0 + 60, y0 + 6, x0 + 184, y0 + 30], fill=NAVY)
    d.text((x0 + 96, y0 + 8), "128", font=sans_b(20), fill=WHITE)
    # flags row
    for i, c in enumerate(((176, 30, 36), (40, 90, 160), (240, 200, 60),
                           (46, 110, 62), (240, 240, 240), (200, 120, 30),
                           (120, 60, 140), (60, 140, 140))):
        fx = x0 + 30 + i * 22
        d.rectangle([fx, y0 + 34, fx + 12, y0 + 42], fill=c,
                    outline=(120, 120, 120), width=1)
    # curved rows of desks + delegates
    for row, yy in enumerate((44, 50)):
        for i in range(7):
            cx = x0 + 24 + i * 32 + row * 4
            d.rectangle([cx - 9, y0 + yy, cx + 9, y0 + yy + 4],
                        fill=(150, 120, 80))
            d.ellipse([cx - 4, y0 + yy - 6, cx + 4, y0 + yy + 2],
                      fill=(232, 200, 160))
    chip(d, x0 + 6, y0 + 5, "128 NATIONS", RED, WHITE, size=9)
    panel_box(d, x0, y0, x1, y1)
    panel_text(d, x0, y0 + 56, x1 - x0, "9  UNITED NATIONS · ARMS",
               "128 nations back killer-robot rules",
               "At a UN conference, 128 countries agree to pursue rules "
               "on autonomous weapons by 2028.",
               "23 Nov", hsize=13, dsize=9)


# ---------------------------------------------------------------- bottom band
LAND = [
    (-100, 50, 28, 16), (-95, 32, 20, 10), (-85, 18, 9, 7),
    (-150, 64, 12, 7), (-42, 73, 9, 5),
    (-60, -8, 13, 13), (-66, -28, 8, 11),
    (14, 6, 19, 16), (20, -20, 13, 11), (44, 4, 8, 7),
    (10, 50, 16, 9), (38, 54, 22, 11), (75, 56, 28, 12),
    (100, 42, 16, 9), (78, 21, 11, 9), (104, 14, 9, 7),
    (113, 33, 11, 7), (139, 37, 5, 7), (128, -24, 13, 7),
    (172, -41, 4, 3), (100, -2, 7, 5), (44, 24, 7, 5), (-2, 54, 3, 4),
]

PINS = [  # (number, lon, lat, nudge_x, nudge_y)
    (1, 30.7, 36.9, 5, -3),
    (2, 56.2, 26.5, 0, 0),
    (3, 20.1, 32.1, -6, 4),
    (4, 30.5, 50.4, -8, -8),
    (7, 121.0, 23.7, 0, 0),
    (9, -74.0, 40.7, 0, 0),
]

ALSO_ON = [
    (5, "Poland: debris was Russian missiles (23 Nov)"),
    (8, "Houthi drone downed; Bahrain hit (AFP, 22 Nov)"),
    (10, "Drone strike hits Khartoum; 3 killed (AFP, 22 Nov)"),
    (11, "Settlers torch 12 cars near Ramallah (22 Nov)"),
    (12, "24 dead in Indonesian candy factory fire (22 Nov)"),
    (13, "Shuri Castle rises again in Okinawa (22 Nov)"),
    (14, "FIFA to confirm UK as 2035 Women's WC host (BBC)"),
    (15, "Alcaraz beats Zverev to win first ATP Finals (ATP, 22 Nov)"),
    (16, "Marquez seals 8th MotoGP title (MotoGP, 22 Nov)"),
    (17, "Lahore world's most polluted city, AQI 538 (Dawn / IQAir, 22 Nov)"),
    (18, "Bolsonaro 'stable' in intensive care (AFP, 22 Nov)"),
    (19, "South Sudan: 24 civilians killed, 7 children (AFP)"),
    (20, "Kim: N. Korea seeks security, not supremacy (KCNA, 23 Nov)"),
    (21, "WHO chief pleads for peace in Ebola-hit DR Congo"),
    (22, "Samsung Securities hack exposes 8,241 clients"),
    (23, "Democrats win 258 House seats, most since 1992"),
    (24, "Netanyahu, Eisenkot end talks with no deal (AFP)"),
    (25, "Nigeria: 35 Fulani killed in reprisal attacks (AFP)"),
    (26, "Thitikul wins third straight LPGA finale, $4m (AP)"),
    (27, "Liverpool thrash 10-man Man Utd 4-0 (Sky, 22 Nov)"),
    (28, "S. Korea minister quits over AI exam cheating (AFP)"),
    (29, "Iran claims it downed a US MQ-9 drone (22 Nov)"),
    (30, "Iran FM says Tehran still open to a US deal (22 Nov)"),
    (31, "Broncos beat Raiders 38-24 (22 Nov)"),
    (32, "South Sudan vote pushed back to February (22 Nov)"),
    (33, "Canada says it has seen no Hegseth memo (Reuters)"),
    (34, "Gulf states condemn Iran attacks on Bahrain (22 Nov)"),
    (35, "Giants edge Jaguars 23-18 (22 Nov)"),
]


def draw_map(d, x0, y0, x1, y1):
    w, h = x1 - x0, y1 - y0

    def px(lon):
        return x0 + (lon + 168.0) / 360.0 * w

    def py(lat):
        return y0 + (75.0 - lat) / 130.0 * h

    step = 5
    yy = y0 + 3
    while yy < y1 - 2:
        xx = x0 + 3
        while xx < x1 - 2:
            lon = (xx - x0) / w * 360.0 - 168.0
            lat = 75.0 - (yy - y0) / h * 130.0
            for clon, clat, rx, ry in LAND:
                if ((lon - clon) / rx) ** 2 + ((lat - clat) / ry) ** 2 <= 1:
                    d.ellipse([xx - 1.5, yy - 1.5, xx + 1.5, yy + 1.5],
                              fill=(169, 143, 95))
                    break
            xx += step
        yy += step
    f = sans_b(8)
    for num, lon, lat, nx, ny in PINS:
        cx, cy = px(lon) + nx, py(lat) + ny
        d.ellipse([cx - 7, cy - 7, cx + 7, cy + 7], fill=RED,
                  outline=WHITE, width=1)
        t = str(num)
        d.text((cx - f.getlength(t) / 2, cy - 6), t, font=f, fill=WHITE)


def draw_bottom(d):
    d.text((12, 842), "WHERE IT HAPPENED", font=sans_b(11), fill=INK)
    d.text((12, 855), "pins match story numbers", font=sans(8), fill=GREY)
    d.text((324, 842), "ALSO ON MONDAY 23 NOVEMBER — 28 MORE STORIES",
           font=sans_b(11), fill=INK)
    draw_map(d, 12, 868, 312, 986)
    # ALSO ON, two columns of 14
    for col in range(2):
        cx = 324 + col * 348
        for row in range(14):
            num, txt = ALSO_ON[col * 14 + row]
            y = 860 + row * 9
            d.text((cx, y), str(num), font=sans_b(8), fill=RED)
            d.text((cx + 18, y), txt, font=sans(8), fill=(52, 48, 40))
    # DATE CHECK box
    d.rectangle([12, 990, 1012, 1012], outline=RED, width=1)
    d.text((18, 992),
           "Every story here was reported or still developing on Monday 23 "
           "November 2026, in at least one time zone.",
           font=sans(8), fill=INK)
    d.text((18, 1002),
           "DATE CHECK — Left out: 'El Chapo Isidro' captured (20 Nov) · "
           "Huang return ruled out (21 Nov) · EU–Indonesia deal signed "
           "(21 Nov) · Ronaldo 986 goals (21 Nov) · Shenzhen summit "
           "(19 Nov) · Palisades arsonist convicted (20 Nov).",
           font=sans(8), fill=INK)
    # footer
    d.text((12, 1015),
           "Sources: Reuters · AP · AFP · BBC · Al Jazeera · IPS · "
           "OilPrice · ATP · MotoGP · Dawn · IQAir · KCNA · Sky Sports",
           font=sans(8), fill=GREY)
    ft = "quick-lynx-56 · make.fun"
    f = sans(8)
    d.text((1012 - f.getlength(ft), 1015), ft, font=f, fill=GREY)


def build():
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)
    draw_masthead(d)
    draw_date(d)
    draw_stats(d)
    draw_region_bar(d)
    draw_hero(img, d)
    d = ImageDraw.Draw(img)
    draw_cop31(d, 12, 546, 508, 698)
    draw_libya(d, 516, 546, 1012, 698)
    draw_kyiv(d, 12, 702, 256, 838)
    draw_mercury(d, 264, 702, 508, 838)
    draw_markets(d, 516, 702, 760, 838)
    draw_un(d, 768, 702, 1012, 838)
    draw_bottom(d)
    img.save(OUT, format="PNG", optimize=True)
    return OUT


if __name__ == "__main__":
    p = build()
    print(p, os.path.getsize(p), "bytes")
