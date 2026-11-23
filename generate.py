#!/usr/bin/env python3
"""news-image-20261123 — Cairo renderer (eksperimen vs R5 PIL).
Deterministik, tanpa network. Render: python3 generate_cairo.py
Output: entry.png 1024x1024.
"""
import math
import random
import cairo

W, H = 1024, 1024


def C(r, g, b):
    return (r / 255.0, g / 255.0, b / 255.0)


def CA(r, g, b, a):
    return (r / 255.0, g / 255.0, b / 255.0, a)


CREAM = C(247, 241, 222)
PAPER = C(252, 248, 236)
INK = C(17, 17, 17)
GREY = C(90, 84, 70)
NAVY = C(14, 42, 78)
NAVY_D = C(10, 25, 48)
RED = C(176, 30, 36)
RED_D = C(140, 22, 28)
LINE = C(201, 191, 165)
WHITE = C(255, 255, 255)
SKY_PALE = C(216, 228, 238)
DEK = C(52, 48, 40)


def rect(ctx, x, y, w, h, color, lw=0):
    ctx.save()
    ctx.set_source_rgb(*color)
    ctx.rectangle(x, y, w, h)
    ctx.fill()
    ctx.restore()


def rounded_rect_path(ctx, x, y, w, h, r):
    ctx.new_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()


def chip(ctx, x, y, text, size, bg, fg, bold=True):
    """Kotak rounded + teks; kembalikan lebar chip."""
    ctx.save()
    ctx.select_font_face("DejaVu Sans",
                         cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_BOLD if bold
                         else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)
    tw = ctx.text_extents(text)[2]
    pad, h = 6, size + 10
    rounded_rect_path(ctx, x, y, tw + pad * 2, h, 4)
    ctx.set_source_rgb(*bg)
    ctx.fill()
    ctx.set_source_rgb(*fg)
    ctx.move_to(x + pad, y + 5 + ctx.font_extents()[0])
    ctx.show_text(text)
    ctx.restore()
    return tw + pad * 2


def set_font(ctx, family, size, bold=False, italic=False):
    ctx.select_font_face(
        family,
        cairo.FONT_SLANT_ITALIC if italic else cairo.FONT_SLANT_NORMAL,
        cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)


def text_w(ctx, s, family, size, bold=False, italic=False):
    set_font(ctx, family, size, bold, italic)
    return ctx.text_extents(s)[2]


def draw_text(ctx, x, y_top, s, family, size, color,
              bold=False, italic=False, align="left"):
    """y_top = koordinat atas (gaya PIL); konversi ke baseline."""
    ctx.save()
    set_font(ctx, family, size, bold, italic)
    ascent = ctx.font_extents()[0]
    w = ctx.text_extents(s)[2]
    if align == "center":
        x = x - w / 2.0
    elif align == "right":
        x = x - w
    ctx.set_source_rgb(*color)
    ctx.move_to(x, y_top + ascent)
    ctx.show_text(s)
    ctx.restore()


def wrap_lines(ctx, s, family, size, max_w, bold=False, italic=False):
    set_font(ctx, family, size, bold, italic)
    lines, cur = [], ""
    for word in s.split(" "):
        trial = word if not cur else cur + " " + word
        if ctx.text_extents(trial)[2] <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(ctx, x, y_top, s, family, size, color, max_w,
                 lh, bold=False, italic=False):
    lines = wrap_lines(ctx, s, family, size, max_w, bold, italic)
    for i, ln in enumerate(lines):
        draw_text(ctx, x, y_top + i * lh, ln, family, size, color,
                  bold, italic)
    return len(lines)


def vgrad(ctx, x0, y0, x1, y1, stops):
    g = cairo.LinearGradient(x0, y0, x1, y1)
    for off, col in stops:
        g.add_color_stop_rgb(off, *col)
    ctx.set_source(g)
    return g


def rgrad(ctx, cx, cy, r0, r1, stops):
    g = cairo.RadialGradient(cx, cy, r0, cx, cy, r1)
    for off, col in stops:
        g.add_color_stop_rgba(off, *col)
    ctx.set_source(g)
    return g


def flame(ctx, cx, base_y, w, h, tilt=0.0):
    """Satu lidah api teardrop bezier, 3 lapis. base_y = dasar api."""
    tip_x = cx + tilt * h * 0.35
    tip_y = base_y - h
    layers = [
        (1.00, C(214, 72, 28)),
        (0.72, C(238, 140, 40)),
        (0.45, C(248, 205, 80)),
    ]
    for scale, col in layers:
        ww, hh = w * scale, h * scale
        bx = cx + (1 - scale) * w * 0.08
        ctx.save()
        ctx.set_source_rgb(*col)
        ctx.new_path()
        ctx.move_to(bx - ww / 2, base_y)
        # sisi kiri melengkung naik ke ujung, dengan 1 lobe
        ctx.curve_to(bx - ww * 0.62, base_y - hh * 0.35,
                     bx - ww * 0.55, base_y - hh * 0.62,
                     bx - ww * 0.18, base_y - hh * 0.86)
        ctx.curve_to(bx - ww * 0.06, base_y - hh * 0.95,
                     tip_x - (bx - tip_x) * (1 - scale) * 0.4,
                     tip_y + hh * 0.10, tip_x, tip_y)
        # sisi kanan turun dengan lobe kedua
        ctx.curve_to(tip_x + ww * 0.10, tip_y + hh * 0.28,
                     bx + ww * 0.42, base_y - hh * 0.60,
                     bx + ww * 0.50, base_y - hh * 0.30)
        ctx.curve_to(bx + ww * 0.55, base_y - hh * 0.12,
                     bx + ww * 0.45, base_y - hh * 0.02,
                     bx + ww / 2, base_y)
        ctx.close_path()
        ctx.fill()
        ctx.restore()


def smoke_puff(ctx, x, y, r, color, alpha):
    """Gumpal asap tepi lembut: beberapa lingkaran radial-alpha."""
    for dx, dy, rr, a in ((0, 0, r, alpha), (-r * 0.45, r * 0.2, r * 0.7, alpha * 0.8),
                          (r * 0.45, -r * 0.15, r * 0.65, alpha * 0.8),
                          (0, -r * 0.4, r * 0.6, alpha * 0.7)):
        g = cairo.RadialGradient(x + dx, y + dy, 0, x + dx, y + dy, rr)
        g.add_color_stop_rgba(0, color[0], color[1], color[2], a)
        g.add_color_stop_rgba(1, color[0], color[1], color[2], 0)
        ctx.save()
        ctx.set_source(g)
        ctx.arc(x + dx, y + dy, rr, 0, 2 * math.pi)
        ctx.fill()
        ctx.restore()


def smoke_column(ctx, points, base_color, top_color, alpha=0.55):
    """points: [(x,y,r), ...] pangkal->puncak; warna makin terang."""
    n = len(points)
    for i, (x, y, r) in enumerate(points):
        t = i / max(1, n - 1)
        col = tuple(bc + (tc - bc) * t
                    for bc, tc in zip(base_color, top_color))
        smoke_puff(ctx, x, y, r, col, alpha * (1 - 0.25 * t))


def masthead(ctx):
    rect(ctx, 0, 0, W, 30, NAVY_D)
    draw_text(ctx, 12, 6, "THE WORLD IN ONE DAY", "DejaVu Sans", 16,
              WHITE, bold=True)
    draw_text(ctx, 1012, 9,
              "35 STORIES  \u2022  6 REGIONS  \u2022  EVERY ONE DATED MONDAY 23 NOVEMBER 2026",
              "DejaVu Sans", 11, C(214, 222, 235), bold=True, align="right")


def date_block(ctx):
    draw_text(ctx, 512, 36, "Monday 23 November 2026", "DejaVu Serif", 56,
              INK, bold=True, align="center")
    draw_text(ctx, 512, 102,
              "COP31 collapses with no deal  \u00b7  Mines hit tankers in Hormuz  \u00b7  Russian warship struck in Libya",
              "DejaVu Serif", 16, RED, italic=True, align="center")


STATS = [
    ("$120BN", "adaptation cash cut at COP31"),
    ("6", "tankers Iran claims hit by mines"),
    ("10", "injured in Libya warship strike"),
    ("2", "killed in Dymer apartment strike"),
    ("17.5%", "Taiwan stocks' fall in one week"),
    ("128", "nations backing killer-robot rules"),
]


def stat_strip(ctx):
    for i, (num, cap) in enumerate(STATS):
        x = 12 + i * 167
        rect(ctx, x, 122, 163, 46, PAPER)
        ctx.save()
        ctx.set_source_rgb(*LINE)
        ctx.set_line_width(1)
        ctx.rectangle(x + 0.5, 122.5, 163, 46)
        ctx.stroke()
        ctx.restore()
        draw_text(ctx, x + 8, 124, num, "DejaVu Sans", 19, RED, bold=True)
        draw_wrapped(ctx, x + 8, 146, cap, "DejaVu Sans", 8, GREY,
                     163 - 16, 10)


REGIONS = [
    ("EUROPE", 6, NAVY), ("MIDDLE EAST", 7, RED),
    ("AMERICAS", 6, C(46, 110, 62)), ("ASIA", 7, C(196, 110, 20)),
    ("AFRICA", 6, C(140, 95, 45)), ("GLOBAL", 3, C(88, 70, 140)),
]


def region_bar(ctx):
    x = 12.0
    for name, n, col in REGIONS:
        w = 1000.0 * n / 35.0
        rect(ctx, x, 170, w, 18, col)
        draw_text(ctx, x + w / 2, 174, "%s %d" % (name, n), "DejaVu Sans", 10,
                  WHITE, bold=True, align="center")
        x += w


def hero(ctx):
    x0, y0, x1, y1 = 12, 192, 1012, 542
    # --- langit: gradien linear 4 stop ---
    vgrad(ctx, 0, y0, 0, 452, [
        (0.0, C(10, 27, 51)), (0.28, C(44, 72, 108)),
        (0.68, C(110, 145, 180)), (1.0, C(214, 122, 52))])
    ctx.rectangle(x0, y0, x1 - x0, 452 - y0)
    ctx.fill()
    # --- laut: gradien linear ---
    vgrad(ctx, 0, 452, 0, y1, [(0.0, C(60, 96, 126)), (1.0, C(46, 82, 110))])
    ctx.rectangle(x0, 452, x1 - x0, y1 - 452)
    ctx.fill()
    # --- bintang (seed 11) ---
    rng = random.Random(11)
    for _ in range(70):
        bx = rng.uniform(20, 1004)
        by = rng.uniform(200, 342)
        r = rng.uniform(1.0, 2.0)
        ctx.save()
        ctx.set_source_rgb(*C(220, 228, 240))
        ctx.arc(bx, by, r, 0, 2 * math.pi)
        ctx.fill()
        ctx.restore()
    # --- bulan: halo radial + cakram + kawah ---
    rgrad(ctx, 880, 256, 0, 90, [
        (0.0, CA(212, 204, 170, 0.55)), (0.5, CA(212, 204, 170, 0.18)),
        (1.0, CA(212, 204, 170, 0.0))])
    ctx.arc(880, 256, 90, 0, 2 * math.pi)
    ctx.fill()
    rgrad(ctx, 880, 256, 0, 28, [
        (0.0, CA(248, 242, 218, 1.0)), (1.0, CA(226, 219, 190, 1.0))])
    ctx.arc(880, 256, 28, 0, 2 * math.pi)
    ctx.fill()
    for kx, ky, kr in ((872, 248, 5), (890, 264, 4)):
        ctx.save()
        ctx.set_source_rgb(*C(210, 202, 172))
        ctx.arc(kx, ky, kr, 0, 2 * math.pi)
        ctx.fill()
        ctx.restore()
    # --- tanker jauh di horizon kanan ---
    rect(ctx, 838, 436, 150, 16, C(24, 40, 60))
    rect(ctx, 846, 424, 12, 12, C(24, 40, 60))
    # --- tanker utama: lambung bezier ---
    ctx.save()
    ctx.set_source_rgb(*C(16, 22, 30))
    ctx.new_path()
    ctx.move_to(170, 452)
    ctx.line_to(826, 452)
    ctx.line_to(826, 478)
    ctx.curve_to(700, 488, 400, 488, 300, 486)
    ctx.curve_to(230, 484, 185, 472, 170, 452)
    ctx.close_path()
    ctx.fill()
    ctx.restore()
    rect(ctx, 170, 470, 656, 8, C(120, 40, 30))  # strip garis air
    # anjungan + jendela menyala 3x3
    rect(ctx, 700, 392, 62, 60, C(24, 32, 44))
    for r in range(3):
        for c in range(3):
            rect(ctx, 710 + c * 18, 404 + r * 16, 10, 8, C(240, 200, 90))
    # cerobong + atap merah
    rect(ctx, 668, 408, 20, 44, C(24, 32, 44))
    rect(ctx, 668, 396, 20, 12, C(150, 50, 35))
    # 5 palka kargo
    for i in range(5):
        rect(ctx, 200 + i * 88, 438, 60, 14, C(34, 44, 56))
    # --- glow radial di belakang api (tidak sampai teks) ---
    rgrad(ctx, 520, 400, 0, 130, [
        (0.0, CA(240, 140, 50, 0.20)), (0.5, CA(240, 140, 50, 0.08)),
        (1.0, CA(240, 140, 50, 0.0))])
    ctx.arc(520, 400, 130, 0, 2 * math.pi)
    ctx.fill()
    # --- api: 3 lidah bezier berlapis ---
    flame(ctx, 470, 452, 38, 88, tilt=-0.12)
    flame(ctx, 540, 452, 46, 108, tilt=0.05)
    flame(ctx, 600, 452, 32, 70, tilt=0.15)
    # --- asap SESUDAH api, pangkal tepat di ujung lidah (tumpang tindih
    # ~6px, bukan di tengah badan api -> tersambung tanpa blob gelap di
    # badan api). Kolom padat, makin terang ke atas. ---
    smoke_column(ctx, [(535, 352, 14), (520, 330, 15), (502, 306, 16),
                       (482, 284, 15), (460, 262, 14), (440, 244, 12)],
                 C(46, 46, 50), C(96, 96, 100), alpha=0.45)
    smoke_column(ctx, [(598, 388, 12), (586, 368, 13), (570, 346, 13),
                       (554, 326, 12)],
                 C(46, 46, 50), C(96, 96, 100), alpha=0.45)


def hero_text(ctx):
    # --- ledakan ranjau / semburan air kiri (~x150, y452) ---
    ctx.save()
    ctx.set_source_rgb(*C(240, 200, 90))
    ctx.new_path()
    ctx.move_to(138, 452); ctx.line_to(150, 424); ctx.line_to(162, 452)
    ctx.close_path(); ctx.fill()
    ctx.set_source_rgb(*C(248, 205, 80))
    ctx.new_path()
    ctx.move_to(144, 452); ctx.line_to(150, 436); ctx.line_to(156, 452)
    ctx.close_path(); ctx.fill()
    # dua semburan putih sempit
    ctx.set_source_rgb(*C(255, 255, 255))
    for sx in (128, 168):
        ctx.new_path()
        ctx.move_to(sx - 3, 452); ctx.line_to(sx, 414); ctx.line_to(sx + 3, 452)
        ctx.close_path(); ctx.fill()
    # cincin buih + tetesan
    ctx.set_source_rgba(1, 1, 1, 0.85)
    ctx.set_line_width(1.5)
    ctx.new_path()
    ctx.arc(150, 452, 22, 0, 2 * math.pi)
    ctx.stroke()
    for dx, dy in ((-34, -8), (36, -12), (-28, 6), (30, 4), (0, -22)):
        ctx.arc(150 + dx, 452 + dy, 1.8, 0, 2 * math.pi)
        ctx.fill()
    ctx.restore()
    # --- refleksi oranye di laut ---
    for ry, rw, col in ((492, 180, C(232, 140, 50)), (500, 220, C(214, 122, 52)),
                        (506, 150, C(232, 140, 50)), (512, 120, C(214, 122, 52))):
        ctx.save()
        ctx.set_source_rgba(col[0], col[1], col[2], 0.45)
        ctx.rectangle(430, ry, rw, 3)
        ctx.fill()
        ctx.restore()
    # --- ranjau laut (630,497) ---
    ctx.save()
    ctx.set_source_rgb(*C(16, 22, 30))
    ctx.arc(630, 497, 10, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_line_width(2)
    for k in range(8):
        a = k * math.pi / 4
        ctx.move_to(630 + math.cos(a) * 9, 497 + math.sin(a) * 9)
        ctx.line_to(630 + math.cos(a) * 15, 497 + math.sin(a) * 15)
    ctx.stroke()
    ctx.restore()
    # --- teks hero (setelah asap, tetap tajam) ---
    chip(ctx, 28, 206, "2  \u00b7  HORMUZ \u2014 MIDDLE EAST", 11, RED, WHITE)
    draw_text(ctx, 28, 236, "Mines hit tankers in Hormuz", "DejaVu Serif",
              34, WHITE, bold=True)
    draw_wrapped(ctx, 28, 278,
                 "Iran claims two more tankers struck by sea mines, six in two days; "
                 "UKMTO reports a vessel hit by an unknown projectile. "
                 "Iran's claim is unverified.",
                 "DejaVu Sans", 15, C(232, 236, 242), 620, 20)
    w1 = chip(ctx, 28, 506, "6 TANKERS", 12, RED, WHITE)
    chip(ctx, 28 + w1 + 8, 506, "BRENT $92.44", 12, WHITE, INK)
    draw_text(ctx, 1000, 512, "AP via OilPrice, 23 Nov", "DejaVu Sans", 10,
              C(226, 232, 240), align="right")
    # outline hero
    ctx.save()
    ctx.set_source_rgb(*LINE)
    ctx.set_line_width(1)
    ctx.rectangle(12.5, 192.5, 1000, 350)
    ctx.stroke()
    ctx.restore()


def panel_text(ctx, x, y_img_bottom, w, kicker, headline, dek, sumber,
               hsize=15, dsize=10):
    """Teks panel di bawah gambar; y_img_bottom = bawah area gambar.
    Layout ketat: kicker +11 -> headline (lh hsize+2) +2 -> dek
    (lh dsize+2) +2 -> sumber. Mid muat 68px, secondary 84px."""
    y = y_img_bottom + 1
    draw_text(ctx, x + 8, y, kicker, "DejaVu Sans", 9, RED, bold=True)
    y += 11
    n = draw_wrapped(ctx, x + 8, y, headline, "DejaVu Serif", hsize, INK,
                     w - 16, hsize + 2, bold=True)
    y += n * (hsize + 2) + 2
    n = draw_wrapped(ctx, x + 8, y, dek, "DejaVu Sans", dsize, DEK,
                     w - 16, dsize + 2)
    y += n * (dsize + 2) + 2
    draw_text(ctx, x + 8, y, sumber, "DejaVu Sans", 8, GREY)


def panel_outline(ctx, x, y, w, h):
    ctx.save()
    ctx.set_source_rgb(*LINE)
    ctx.set_line_width(1)
    ctx.rectangle(x + 0.5, y + 0.5, w, h)
    ctx.stroke()
    ctx.restore()


def mid_cop31(ctx):
    x, y, w = 12, 546, 496
    rect(ctx, x, y, w, 84, C(214, 226, 236))  # langit
    # globe
    ctx.save()
    ctx.set_source_rgb(*C(52, 110, 170))
    ctx.arc(x + 57, y + 49, 35, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_source_rgb(*C(90, 160, 90))
    for bx, by, br in ((45, 38, 9), (66, 52, 11), (50, 62, 7)):
        ctx.arc(x + bx, y + by, br, 0, 2 * math.pi)
        ctx.fill()
    ctx.set_source_rgb(*C(120, 175, 100))
    ctx.arc(x + 72, y + 34, 6, 0, 2 * math.pi)
    ctx.fill()
    ctx.restore()
    # meja summit
    rect(ctx, x + 130, y + 62, 290, 20, C(122, 84, 52))
    rect(ctx, x + 130, y + 62, 290, 5, C(146, 104, 66))
    # 5 delegasi
    cols = [C(176, 40, 60), C(196, 120, 40), C(150, 90, 170),
            C(60, 130, 170), C(200, 90, 40)]
    for i, col in enumerate(cols):
        dx = x + 160 + i * 52
        ctx.save()
        ctx.set_source_rgb(*C(232, 200, 160))
        ctx.arc(dx, y + 44, 9, 0, 2 * math.pi)
        ctx.fill()
        ctx.set_source_rgb(*col)
        ctx.new_path()
        ctx.move_to(dx - 12, y + 62)
        ctx.line_to(dx + 12, y + 62)
        ctx.line_to(dx + 8, y + 52)
        ctx.line_to(dx - 8, y + 52)
        ctx.close_path()
        ctx.fill()
        ctx.restore()
    # termometer kanan
    ctx.save()
    ctx.set_source_rgb(*WHITE)
    ctx.rectangle(x + 448, y + 14, 10, 52)
    ctx.fill()
    ctx.set_source_rgb(*RED)
    ctx.rectangle(x + 450, y + 44, 6, 22)
    ctx.fill()
    ctx.arc(x + 453, y + 68, 8, 0, 2 * math.pi)
    ctx.fill()
    ctx.restore()
    w1 = chip(ctx, x + 8, y + 6, "COP31: NO DEAL", 10, RED, WHITE)
    cw = text_w(ctx, "$120BN CUT", "DejaVu Sans", 10, bold=True) + 12
    chip(ctx, x + w - 8 - cw, y + 6, "$120BN CUT", 10, WHITE, INK)
    panel_text(ctx, x, y + 84, w, "1  ANTALYA, TURKEY \u00b7 CLIMATE",
               "COP31 collapses with no deal",
               "Two days of overtime end in failure: the draft never "
               "mentions fossil fuels and the $120bn adaptation target "
               "is dropped.",
               "IPS / Global Issues, 22 Nov")
    panel_outline(ctx, x, y, w, 152)


def mid_libya(ctx):
    x, y, w = 516, 546, 496
    rect(ctx, x, y, w, 56, C(206, 216, 224))   # langit
    rect(ctx, x, y + 56, w, 28, C(158, 180, 196))  # laut
    # --- kapal korvet miring ~10 derajat, haluan ke kanan ---
    ctx.save()
    ctx.translate(x + 250, y + 40)
    ctx.rotate(-math.radians(10))
    # lambung bezier halus
    ctx.set_source_rgb(*C(96, 104, 112))
    ctx.new_path()
    ctx.move_to(-190, -6)
    ctx.line_to(170, -6)
    ctx.curve_to(196, -4, 202, 2, 196, 8)
    ctx.curve_to(120, 20, -120, 20, -178, 10)
    ctx.curve_to(-192, 6, -194, -2, -190, -6)
    ctx.close_path()
    ctx.fill()
    # strake bawah lebih gelap + strip garis air merah
    ctx.set_source_rgb(*C(74, 80, 88))
    ctx.new_path()
    ctx.move_to(-178, 8)
    ctx.curve_to(-60, 18, 100, 18, 192, 6)
    ctx.line_to(196, 10)
    ctx.curve_to(100, 22, -60, 22, -182, 12)
    ctx.close_path()
    ctx.fill()
    ctx.set_source_rgb(*C(150, 60, 45))
    ctx.rectangle(-188, -2, 380, 4)
    ctx.fill()
    # tepi dek highlight + sambungan pelat + guratan karat
    ctx.set_source_rgba(1, 1, 1, 0.35)
    ctx.set_line_width(1.5)
    ctx.move_to(-190, -6)
    ctx.line_to(170, -6)
    ctx.stroke()
    ctx.set_source_rgba(60, 60, 60, 0.5)
    ctx.set_line_width(1)
    for px in (-120, -40, 40, 120):
        ctx.move_to(px, -6)
        ctx.line_to(px, 8)
        ctx.stroke()
    ctx.set_source_rgba(140, 80, 40, 0.6)
    for px, py in ((-90, 2), (20, 4), (90, 0)):
        ctx.move_to(px, py)
        ctx.line_to(px + 14, py + 3)
        ctx.stroke()
    # transom buritan + tiang rel
    ctx.set_source_rgb(*C(60, 64, 70))
    ctx.rectangle(-196, -10, 8, 20)
    ctx.fill()
    ctx.set_line_width(1)
    ctx.move_to(-196, -10)
    ctx.line_to(-196, -18)
    ctx.stroke()
    # anjungan + 4 jendela menyala + atap gelap
    ctx.set_source_rgb(*C(88, 96, 104))
    ctx.rectangle(-30, -34, 70, 28)
    ctx.fill()
    ctx.set_source_rgb(*C(60, 64, 70))
    ctx.rectangle(-30, -38, 70, 5)
    ctx.fill()
    for i in range(4):
        rect(ctx, -22 + i * 16, -28, 9, 7, C(240, 200, 90))
    # cerobong tutup hitam
    rect(ctx, 52, -30, 14, 24, C(96, 100, 106))
    rect(ctx, 52, -34, 14, 5, C(30, 30, 32))
    # kubah meriam depan + laras
    ctx.set_source_rgb(*C(88, 96, 104))
    ctx.arc(140, -6, 12, math.pi, 2 * math.pi)
    ctx.fill()
    ctx.set_line_width(4)
    ctx.move_to(140, -14)
    ctx.line_to(168, -22)
    ctx.stroke()
    # tiang + bendera merah kecil
    ctx.set_line_width(2)
    ctx.move_to(10, -38)
    ctx.line_to(10, -58)
    ctx.stroke()
    ctx.set_source_rgb(*RED)
    ctx.new_path()
    ctx.move_to(10, -58); ctx.line_to(26, -54); ctx.line_to(10, -50)
    ctx.close_path(); ctx.fill()
    ctx.restore()
    # api di garis air buritan + haluan (kecil), asap di atasnya
    flame(ctx, x + 70, y + 58, 22, 34, tilt=-0.1)
    flame(ctx, x + 440, y + 58, 16, 24, tilt=0.1)
    smoke_column(ctx, [(x + 70, y + 26, 8), (x + 62, y + 12, 9)],
                 C(46, 46, 50), C(88, 88, 92), alpha=0.5)
    # drone + jejak kanan atas
    ctx.save()
    ctx.set_source_rgb(*C(40, 40, 40))
    ctx.arc(x + 430, y + 12, 3, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_source_rgba(200, 60, 40, 0.8)
    ctx.set_line_width(1.5)
    ctx.move_to(x + 430, y + 12)
    ctx.line_to(x + 470, y + 4)
    ctx.stroke()
    ctx.restore()
    # puing di air
    for px, py, pr in ((x + 150, y + 68, 3), (x + 300, y + 72, 2),
                       (x + 380, y + 66, 3)):
        ctx.save()
        ctx.set_source_rgb(*C(90, 90, 88))
        ctx.arc(px, py, pr, 0, 2 * math.pi)
        ctx.fill()
        ctx.restore()
    chip(ctx, x + 8, y + 6, "10 INJURED", 10, RED, WHITE)
    chip(ctx, x + 108, y + 6, "SHIP CAPSIZED", 10, WHITE, INK)
    panel_text(ctx, x, y + 84, w, "3  BENGHAZI, LIBYA \u00b7 WAR AT SEA",
               "Russian warship struck in Libya",
               "Suspected Ukrainian sea drones hit the corvette Merkury. "
               "The ship is badly damaged and capsizes; Kyiv and Moscow silent.",
               "AP / Reuters / BBC Verify, 22 Nov")
    panel_outline(ctx, x, y, w, 152)


def sec_kyiv(ctx):
    x, y, w = 12, 702, 244
    rect(ctx, x, y, w, 52, C(13, 30, 51))
    rng = random.Random(4)
    for _ in range(14):
        ctx.save()
        ctx.set_source_rgb(*C(220, 228, 240))
        ctx.arc(x + rng.uniform(6, w - 6), y + rng.uniform(4, 50),
                rng.uniform(0.8, 1.6), 0, 2 * math.pi)
        ctx.fill()
        ctx.restore()
    # blok apartemen + jendela 4x4 (~1/3 menyala)
    rect(ctx, x + 60, y + 14, 90, 38, C(26, 40, 60))
    lit = [(0, 0), (2, 1), (1, 2), (3, 2), (0, 3), (2, 3)]
    for r in range(4):
        for c in range(4):
            col = C(240, 200, 90) if (c, r) in lit else C(60, 74, 96)
            rect(ctx, x + 66 + c * 20, y + 18 + r * 9, 12, 6, col)
    # api + asap di sisi kanan blok
    flame(ctx, x + 152, y + 52, 20, 30, tilt=0.1)
    smoke_column(ctx, [(x + 152, y + 24, 7), (x + 146, y + 10, 8)],
                 C(46, 46, 50), C(88, 88, 92), alpha=0.5)
    # drone + jejak merah kanan atas
    ctx.save()
    ctx.set_source_rgb(*C(220, 220, 220))
    ctx.arc(x + 210, y + 12, 3, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_source_rgba(200, 60, 40, 0.8)
    ctx.set_line_width(1.5)
    ctx.move_to(x + 210, y + 12)
    ctx.line_to(x + 232, y + 6)
    ctx.stroke()
    ctx.restore()
    chip(ctx, x + 8, y + 6, "2 KILLED", 9, RED, WHITE)
    panel_text(ctx, x, y + 52, w, "4  DYMER, UKRAINE \u00b7 WAR",
               "Drone hits Kyiv apartment block",
               "Russian drone strikes a 5-storey block in Dymer. 2 dead, "
               "11 missing, among them 2 children.",
               "Al Jazeera / AP, 22 Nov", hsize=12, dsize=9)
    panel_outline(ctx, x, y, w, 136)


def sec_mercury(ctx):
    x, y, w = 264, 702, 244
    rect(ctx, x, y, w, 52, C(232, 228, 214))
    # cincin orbit elips tipis
    ctx.save()
    ctx.set_source_rgba(120, 110, 90, 0.7)
    ctx.set_line_width(1)
    ctx.save()
    ctx.translate(x + 178, y + 26)
    ctx.scale(1.6, 0.55)
    ctx.arc(0, 0, 34, 0, 2 * math.pi)
    ctx.stroke()
    ctx.restore()
    # planet berkawah
    ctx.set_source_rgb(*C(168, 162, 150))
    ctx.arc(x + 178, y + 26, 26, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_source_rgb(*C(138, 132, 120))
    for kx, ky, kr in ((168, 18, 5), (188, 30, 6), (176, 38, 4),
                       (190, 14, 3), (166, 30, 3)):
        ctx.arc(x + kx, y + ky, kr, 0, 2 * math.pi)
        ctx.fill()
    ctx.restore()
    # probe kiri: badan emas + panel surya biru + garis
    ctx.save()
    ctx.set_source_rgb(*C(60, 90, 140))
    ctx.rectangle(x + 12, y + 22, 26, 12)
    ctx.fill()
    ctx.set_source_rgb(*C(200, 160, 60))
    ctx.rectangle(x + 40, y + 20, 18, 16)
    ctx.fill()
    ctx.set_source_rgba(60, 60, 60, 0.8)
    ctx.set_line_width(1)
    ctx.move_to(x + 58, y + 28)
    ctx.line_to(x + 152, y + 30)
    ctx.stroke()
    ctx.set_source_rgb(*C(120, 110, 90))
    for sx, sy in ((30, 8), (90, 44), (120, 10)):
        ctx.arc(x + sx, y + sy, 1.2, 0, 2 * math.pi)
        ctx.fill()
    ctx.restore()
    chip(ctx, x + 8, y + 6, "2ND EVER", 9, RED, WHITE)
    panel_text(ctx, x, y + 52, w, "6  SPACE \u00b7 MERCURY",
               "BepiColombo enters Mercury orbit",
               "The ESA-JAXA probe becomes only the second mission to "
               "orbit Mercury, on 21 Nov.",
               "Reported 23 Nov", hsize=12, dsize=9)
    panel_outline(ctx, x, y, w, 136)


def sec_bursa(ctx):
    x, y, w = 516, 702, 244
    rect(ctx, x, y, w, 52, C(244, 242, 236))
    # papan putih + garis merah jatuh + kepala panah
    rect(ctx, x + 10, y + 8, 140, 40, WHITE)
    ctx.save()
    ctx.set_source_rgb(*RED)
    ctx.set_line_width(3)
    ctx.move_to(x + 16, y + 14)
    ctx.line_to(x + 60, y + 26)
    ctx.line_to(x + 100, y + 22)
    ctx.line_to(x + 138, y + 42)
    ctx.stroke()
    ctx.new_path()
    ctx.move_to(x + 138, y + 42); ctx.line_to(x + 126, y + 36)
    ctx.line_to(x + 128, y + 46)
    ctx.close_path(); ctx.fill()
    ctx.restore()
    # 5 batang ticker merah kanan
    for i, bh in enumerate((10, 16, 8, 20, 12)):
        rect(ctx, x + 160 + i * 15, y + 44 - bh, 10, bh, RED)
    # 3 trader menunduk
    for i, tx in enumerate((40, 110, 180)):
        ctx.save()
        ctx.set_source_rgb(*C(232, 200, 160))
        ctx.arc(x + tx, y + 46, 5, 0, 2 * math.pi)
        ctx.fill()
        ctx.set_source_rgb(*C(60, 60, 70))
        ctx.new_path()
        ctx.move_to(x + tx - 9, y + 52)
        ctx.line_to(x + tx + 9, y + 52)
        ctx.line_to(x + tx + 6, y + 46)
        ctx.line_to(x + tx - 6, y + 46)
        ctx.close_path()
        ctx.fill()
        ctx.restore()
    chip(ctx, x + 8, y + 6, "-17.5%", 9, RED, WHITE)
    panel_text(ctx, x, y + 52, w, "7  TAIPEI \u00b7 MARKETS",
               "Markets plunge; Taiwan bans shorting",
               "US stocks tumble; Taiwan shares fall 17.5% in a week; "
               "short-selling banned from Monday.",
               "23 Nov", hsize=12, dsize=9)
    panel_outline(ctx, x, y, w, 136)


def sec_pbb(ctx):
    x, y, w = 768, 702, 244
    rect(ctx, x, y, w, 52, C(222, 228, 236))
    # dinding navy + angka 128
    rect(ctx, x + 60, y + 6, 124, 24, NAVY)
    draw_text(ctx, x + 122, y + 8, "128", "DejaVu Sans", 20, WHITE,
              bold=True, align="center")
    # deret 8 bendera kecil
    fcols = [C(176, 40, 60), C(40, 90, 160), C(240, 200, 90),
             C(46, 110, 62), C(150, 90, 170), C(200, 90, 40),
             C(60, 130, 170), C(196, 120, 40)]
    for i, col in enumerate(fcols):
        rect(ctx, x + 60 + i * 16, y + 34, 12, 8, col)
    # baris melengkung meja + kepala delegasi
    ctx.save()
    ctx.set_source_rgb(*C(150, 120, 80))
    ctx.new_path()
    ctx.move_to(x + 20, y + 52)
    ctx.curve_to(x + 80, y + 42, x + 170, y + 42, x + 224, y + 52)
    ctx.line_to(x + 224, y + 52)
    ctx.line_to(x + 20, y + 52)
    ctx.close_path()
    ctx.fill()
    ctx.set_source_rgb(*C(232, 200, 160))
    for hx in (70, 122, 174):
        ctx.arc(x + hx, y + 42, 5, 0, 2 * math.pi)
        ctx.fill()
    ctx.restore()
    chip(ctx, x + 8, y + 6, "128 NATIONS", 9, RED, WHITE)
    panel_text(ctx, x, y + 52, w, "9  UNITED NATIONS \u00b7 ARMS",
               "128 nations back killer-robot rules",
               "At a UN conference, 128 countries agree to pursue rules "
               "on autonomous weapons by 2028.",
               "23 Nov", hsize=12, dsize=9)
    panel_outline(ctx, x, y, w, 136)


LAND = [(-100, 50, 28, 16), (-95, 32, 20, 10), (-85, 18, 9, 7),
        (-150, 64, 12, 7), (-42, 73, 9, 5), (-60, -8, 13, 13),
        (-66, -28, 8, 11), (14, 6, 19, 16), (20, -20, 13, 11),
        (44, 4, 8, 7), (10, 50, 16, 9), (38, 54, 22, 11),
        (75, 56, 28, 12), (100, 42, 16, 9), (78, 21, 11, 9),
        (104, 14, 9, 7), (113, 33, 11, 7), (139, 37, 5, 7),
        (128, -24, 13, 7), (172, -41, 4, 3), (100, -2, 7, 5),
        (44, 24, 7, 5), (-2, 54, 3, 4)]

PINS = [(1, 30.7, 36.9, 5, -3), (2, 56.2, 26.5, 0, 0),
        (3, 20.1, 32.1, -6, 4), (4, 30.5, 50.4, -8, -8),
        (7, 121.0, 23.7, 0, 0), (9, -74.0, 40.7, 0, 0)]

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


def project(lon, lat):
    return (12 + (lon + 168) / 360.0 * 300,
            868 + (75 - lat) / 130.0 * 118)


def in_land(px, py):
    for lon, lat, rx, ry in LAND:
        cx, cy = project(lon, lat)
        sx = (300.0 / 360.0) * rx
        sy = (118.0 / 130.0) * ry
        if ((px - cx) / sx) ** 2 + ((py - cy) / sy) ** 2 <= 1:
            return True
    return False


def bottom_band(ctx):
    draw_text(ctx, 12, 842, "WHERE IT HAPPENED", "DejaVu Sans", 11, INK,
              bold=True)
    draw_text(ctx, 12, 855, "pins match story numbers", "DejaVu Sans", 8,
              GREY)
    draw_text(ctx, 324, 842, "ALSO ON MONDAY 23 NOVEMBER \u2014 28 MORE STORIES",
              "DejaVu Sans", 11, INK, bold=True)
    # peta dotted: grid 5px, titik hanya di daratan
    ctx.save()
    ctx.set_source_rgb(*C(169, 143, 95))
    gx, gy = 12, 868
    while gy <= 986:
        px = gx
        while px <= 312:
            if in_land(px, gy):
                ctx.arc(px, gy, 1.5, 0, 2 * math.pi)
                ctx.fill()
            px += 5
        gy += 5
    ctx.restore()
    # 6 pin bernomor
    for num, lon, lat, nx, ny in PINS:
        px, py = project(lon, lat)
        px += nx
        py += ny
        ctx.save()
        ctx.set_source_rgb(*RED)
        ctx.arc(px, py, 7, 0, 2 * math.pi)
        ctx.fill()
        ctx.set_source_rgb(*WHITE)
        ctx.set_line_width(1)
        ctx.arc(px, py, 7, 0, 2 * math.pi)
        ctx.stroke()
        ctx.restore()
        draw_text(ctx, px, py - 5.5, str(num), "DejaVu Sans", 8, WHITE,
                  bold=True, align="center")
    # ALSO ON: 2 kolom x 14 baris
    for i, (num, txt) in enumerate(ALSO_ON):
        col = 0 if i < 14 else 1
        row = i % 14
        bx = 324 if col == 0 else 672
        by = 860 + row * 9
        draw_text(ctx, bx, by, str(num), "DejaVu Sans", 8, RED, bold=True)
        draw_text(ctx, bx + 18, by, txt, "DejaVu Sans", 8, DEK)


def date_check_footer(ctx):
    ctx.save()
    ctx.set_source_rgb(*RED)
    ctx.set_line_width(1)
    ctx.rectangle(12.5, 990.5, 1000, 22)
    ctx.stroke()
    ctx.restore()
    draw_text(ctx, 12, 992,
              "Every story here was reported or still developing on Monday "
              "23 November 2026, in at least one time zone.",
              "DejaVu Sans", 8, INK)
    draw_text(ctx, 12, 1002,
              "DATE CHECK \u2014 Left out: 'El Chapo Isidro' captured (20 Nov) "
              "\u00b7 Huang return ruled out (21 Nov) \u00b7 EU\u2013Indonesia deal "
              "signed (21 Nov) \u00b7 Ronaldo 986 goals (21 Nov) \u00b7 Shenzhen "
              "summit (19 Nov) \u00b7 Palisades arsonist convicted (20 Nov).",
              "DejaVu Sans", 8, INK)
    draw_text(ctx, 12, 1014,
              "Sources: Reuters \u00b7 AP \u00b7 AFP \u00b7 BBC \u00b7 Al Jazeera "
              "\u00b7 IPS \u00b7 OilPrice \u00b7 ATP \u00b7 MotoGP \u00b7 Dawn "
              "\u00b7 IQAir \u00b7 KCNA \u00b7 Sky Sports",
              "DejaVu Sans", 8, GREY)
    draw_text(ctx, 1012, 1014, "quick-lynx-56 \u00b7 make.fun",
              "DejaVu Sans", 8, GREY, align="right")


def build():
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    ctx.set_source_rgb(*CREAM)
    ctx.paint()
    masthead(ctx)
    date_block(ctx)
    stat_strip(ctx)
    region_bar(ctx)
    hero(ctx)
    hero_text(ctx)
    mid_cop31(ctx)
    mid_libya(ctx)
    sec_kyiv(ctx)
    sec_mercury(ctx)
    sec_bursa(ctx)
    sec_pbb(ctx)
    bottom_band(ctx)
    date_check_footer(ctx)
    surf.write_to_png("entry.png")
    print("wrote entry.png")


if __name__ == "__main__":
    build()
