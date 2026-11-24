#!/usr/bin/env python3
"""news-image-20261123 — ronde 4 (R4) renderer Cairo.

Revisi visual dalam template Cairo: plume asap kontinu, ledakan ranjau
lembut, panel secondary dipadatkan, hero lebih kaya. Isi + layout +
semua teks SAMA PERSIS dengan Cairo (35 cerita, Senin 23 Nov 2026).
Deterministik, tanpa network. Render hanya di glad-dew.
Output: entry.png 1024x1024.
"""
import math
import random
import cairo

PAGE_W, PAGE_H = 1024, 1024
HERO_X0, HERO_Y0 = 12, 192
HERO_X1, HERO_Y1 = 1012, 542
SEA_Y = 452


def rgb(r, g, b):
    return (r / 255.0, g / 255.0, b / 255.0)


def rgba(r, g, b, a):
    return (r / 255.0, g / 255.0, b / 255.0, a)


# ---- palet (sama seperti Cairo) ----
CREAM = rgb(247, 241, 222)
PAPER = rgb(252, 248, 236)
INK = rgb(17, 17, 17)
GREY = rgb(90, 84, 70)
NAVY = rgb(14, 42, 78)
NAVY_D = rgb(10, 25, 48)
RED = rgb(176, 30, 36)
LINE = rgb(201, 191, 165)
WHITE = rgb(255, 255, 255)
BODY = rgb(52, 48, 40)
GOLD = rgb(240, 200, 90)


def fill_rect(ctx, x, y, w, h, col):
    ctx.save()
    ctx.set_source_rgb(*col)
    ctx.rectangle(x, y, w, h)
    ctx.fill()
    ctx.restore()


def stroke_rect(ctx, x, y, w, h, col, lw=1.0):
    ctx.save()
    ctx.set_source_rgb(*col)
    ctx.set_line_width(lw)
    ctx.rectangle(x + 0.5, y + 0.5, w, h)
    ctx.stroke()
    ctx.restore()


def disc(ctx, x, y, r, col):
    ctx.save()
    ctx.set_source_rgb(*col)
    ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.fill()
    ctx.restore()


def soft_disc(ctx, x, y, r, col, alpha):
    """Lingkaran dengan tepi memudar (radial alpha) — bukan elips datar."""
    g = cairo.RadialGradient(x, y, 0, x, y, r)
    g.add_color_stop_rgba(0, col[0], col[1], col[2], alpha)
    g.add_color_stop_rgba(0.7, col[0], col[1], col[2], alpha * 0.55)
    g.add_color_stop_rgba(1, col[0], col[1], col[2], 0)
    ctx.save()
    ctx.set_source(g)
    ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.fill()
    ctx.restore()


def round_path(ctx, x, y, w, h, r):
    ctx.new_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()


def pick_font(ctx, fam, size, bold=False, italic=False):
    ctx.select_font_face(
        fam,
        cairo.FONT_SLANT_ITALIC if italic else cairo.FONT_SLANT_NORMAL,
        cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)


def measure(ctx, s, fam, size, bold=False, italic=False):
    pick_font(ctx, fam, size, bold, italic)
    return ctx.text_extents(s)[2]


def put_text(ctx, x, y_top, s, fam, size, col, bold=False,
             italic=False, align="left"):
    """y_top = koordinat atas (gaya PIL); dikonversi ke baseline Cairo."""
    ctx.save()
    pick_font(ctx, fam, size, bold, italic)
    ascent = ctx.font_extents()[0]
    w = ctx.text_extents(s)[2]
    if align == "center":
        x = x - w / 2.0
    elif align == "right":
        x = x - w
    ctx.set_source_rgb(*col)
    ctx.move_to(x, y_top + ascent)
    ctx.show_text(s)
    ctx.restore()


def wrap_to(ctx, s, fam, size, max_w, bold=False, italic=False):
    pick_font(ctx, fam, size, bold, italic)
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


def put_wrapped(ctx, x, y_top, s, fam, size, col, max_w, lh,
                bold=False, italic=False):
    lines = wrap_to(ctx, s, fam, size, max_w, bold, italic)
    for i, ln in enumerate(lines):
        put_text(ctx, x, y_top + i * lh, ln, fam, size, col, bold, italic)
    return len(lines)

def tag(ctx, x, y, s, size, bg, fg):
    """Chip rounded + teks; kembalikan lebar total chip."""
    ctx.save()
    pick_font(ctx, "DejaVu Sans", size, bold=True)
    tw = ctx.text_extents(s)[2]
    pad, h = 6, size + 10
    round_path(ctx, x, y, tw + pad * 2, h, 4)
    ctx.set_source_rgb(*bg)
    ctx.fill()
    ctx.set_source_rgb(*fg)
    ctx.move_to(x + pad, y + 5 + ctx.font_extents()[0])
    ctx.show_text(s)
    ctx.restore()
    return tw + pad * 2


def lin_grad(ctx, x0, y0, x1, y1, stops):
    g = cairo.LinearGradient(x0, y0, x1, y1)
    for off, col in stops:
        g.add_color_stop_rgb(off, *col)
    ctx.set_source(g)
    return g


def rad_grad(ctx, cx, cy, r0, r1, stops):
    g = cairo.RadialGradient(cx, cy, r0, cx, cy, r1)
    for off, col in stops:
        g.add_color_stop_rgba(off, *col)
    ctx.set_source(g)
    return g


def lerp_col(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


# ---- api + bara + asap (lab api) ----

def flame_tongue(ctx, cx, base_y, w, h, tilt=0.0):
    """Satu lidah api teardrop bezier, 3 lapis (luar merah, oranye, inti)."""
    tip_x = cx + tilt * h * 0.35
    tip_y = base_y - h
    for scale, col in ((1.00, rgb(214, 72, 28)),
                       (0.72, rgb(238, 140, 40)),
                       (0.45, rgb(248, 205, 80))):
        ww, hh = w * scale, h * scale
        bx = cx + (1 - scale) * w * 0.08
        ctx.save()
        ctx.set_source_rgb(*col)
        ctx.new_path()
        ctx.move_to(bx - ww / 2, base_y)
        ctx.curve_to(bx - ww * 0.62, base_y - hh * 0.35,
                     bx - ww * 0.55, base_y - hh * 0.62,
                     bx - ww * 0.18, base_y - hh * 0.86)
        ctx.curve_to(bx - ww * 0.06, base_y - hh * 0.95,
                     tip_x - (bx - tip_x) * (1 - scale) * 0.4,
                     tip_y + hh * 0.10, tip_x, tip_y)
        ctx.curve_to(tip_x + ww * 0.10, tip_y + hh * 0.28,
                     bx + ww * 0.42, base_y - hh * 0.60,
                     bx + ww * 0.50, base_y - hh * 0.30)
        ctx.curve_to(bx + ww * 0.55, base_y - hh * 0.12,
                     bx + ww * 0.45, base_y - hh * 0.02,
                     bx + ww / 2, base_y)
        ctx.close_path()
        ctx.fill()
        ctx.restore()


def embers(ctx, cx, base_y, seed, count=26):
    """Bara/percikan naik dari api: titik oranye-kuning memudar ke atas."""
    rng = random.Random(seed)
    for _ in range(count):
        t = rng.random()
        ex = cx + rng.uniform(-70, 70) * (0.4 + 0.6 * t)
        ey = base_y - t * rng.uniform(90, 150)
        r = rng.uniform(0.8, 2.2) * (1 - 0.5 * t)
        col = rgb(248, 205, 80) if rng.random() < 0.5 else rgb(240, 120, 40)
        ctx.save()
        ctx.set_source_rgba(col[0], col[1], col[2], 0.9 * (1 - 0.7 * t))
        ctx.arc(ex, ey, r, 0, 2 * math.pi)
        ctx.fill()
        ctx.restore()


def _spine_points(spine, step=4.0):
    """Interpolasi rapat di sepanjang spine supaya cakram tumpang tindih
    padat (jarak ~4px, radius 12-20px) — tidak ada sambungan yang kelihatan."""
    pts = []
    for (x0, y0), (x1, y1) in zip(spine, spine[1:]):
        seg = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(seg / step))
        for i in range(n):
            t = i / n
            pts.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
    pts.append(spine[-1])
    return pts


def smoke_plume(ctx, spine, r_base, r_top, dark, light, alpha=0.5):
    """Kolom asap tebal: cakram radial-alpha rapat di sepanjang spine
    (jarak 5px) — badan kolom ~2x lipat r4 (r_base 36, alpha 0.8)
    supaya terbaca sebagai kolom di 300px, bukan jejak tipis.
    Ujung atas tetap ramping (r_top 14) dan berhenti y~240 supaya
    tidak menutupi headline; teks digambar belakangan sehingga
    selalu di atas asap. Inti tiap cakram genap dipertegas supaya
    tengah kolom lebih pekat daripada tepinya."""
    pts = _spine_points(spine, step=5.0)
    total = max(1, len(pts) - 1)
    for i, (px, py) in enumerate(pts):
        t = i / total
        swell = 1 + 0.5 * math.sin(math.pi * t)
        rad = (r_base + (r_top - r_base) * t) * swell
        wob = 5.0 * math.sin(i * 0.9)
        col = lerp_col(dark, light, t)
        soft_disc(ctx, px + wob, py, rad, col, alpha * 0.26)
        if i % 2 == 0:
            k = i // 2
            core_r = max(3.0, rad * 0.55)
            core_col = lerp_col(dark, light, min(1.0, t + 0.25))
            soft_disc(ctx, px + 3.0 * math.sin(2 * k * 0.9), py,
                      core_r, core_col, alpha * 0.14)


def sea_texture(ctx, seed=23):
    """Tekstur ombak: whitecaps (busur putih pendek), pantulan oranye,
    puing mengambang (papan + tong) di dekat lambung."""
    rng = random.Random(seed)
    # whitecaps: busur-busur putih tipis tersebar di laut
    for _ in range(34):
        wx = rng.uniform(30, 990)
        wy = rng.uniform(458, 536)
        wl = rng.uniform(8, 26)
        ctx.save()
        ctx.set_source_rgba(1, 1, 1, rng.uniform(0.18, 0.42))
        ctx.set_line_width(rng.uniform(1.0, 1.8))
        ctx.new_path()
        ctx.arc(wx, wy, wl, math.pi * 1.08, math.pi * 1.92)
        ctx.stroke()
        ctx.restore()
    # pantulan oranye di bawah api (streak horizontal translusen)
    for ry, rw, col, a in ((492, 190, rgb(232, 140, 50), 0.45),
                           (500, 230, rgb(214, 122, 52), 0.40),
                           (506, 160, rgb(232, 140, 50), 0.45),
                           (512, 120, rgb(214, 122, 52), 0.35),
                           (520, 200, rgb(232, 140, 50), 0.25)):
        ctx.save()
        ctx.set_source_rgba(col[0], col[1], col[2], a)
        ctx.rectangle(425, ry, rw, 3)
        ctx.fill()
        ctx.restore()
    # puing: 2 papan miring + 1 tong mengambang
    for px, py, ang in ((300, 512, 0.25), (700, 524, -0.3), (880, 508, 0.1)):
        ctx.save()
        ctx.translate(px, py)
        ctx.rotate(ang)
        ctx.set_source_rgb(*rgb(96, 74, 52))
        ctx.rectangle(-14, -2.5, 28, 5)
        ctx.fill()
        ctx.restore()
    ctx.save()
    ctx.translate(760, 518)
    ctx.rotate(0.4)
    ctx.set_source_rgb(*rgb(70, 60, 50))
    ctx.rectangle(-7, -5, 14, 10)
    ctx.fill()
    ctx.set_source_rgb(*rgb(120, 90, 60))
    ctx.rectangle(-7, -5, 14, 3)
    ctx.fill()
    ctx.restore()

# ---- kepala halaman ----

def draw_masthead(ctx):
    fill_rect(ctx, 0, 0, PAGE_W, 30, NAVY_D)
    put_text(ctx, 12, 6, "THE WORLD IN ONE DAY", "DejaVu Sans", 16,
             WHITE, bold=True)
    put_text(ctx, 1012, 9,
             "35 STORIES  \u2022  6 REGIONS  \u2022  EVERY ONE DATED MONDAY 23 NOVEMBER 2026",
             "DejaVu Sans", 11, rgb(214, 222, 235), bold=True, align="right")


def draw_date_block(ctx):
    put_text(ctx, 512, 36, "Monday 23 November 2026", "DejaVu Serif", 56,
             INK, bold=True, align="center")
    put_text(ctx, 512, 102,
             "COP31 collapses with no deal  \u00b7  Mines hit tankers in Hormuz  \u00b7  Russian warship struck in Libya",
             "DejaVu Serif", 16, RED, italic=True, align="center")


STAT_CELLS = [
    ("$120BN", "adaptation cash cut at COP31"),
    ("6", "tankers Iran claims hit by mines"),
    ("10", "injured in Libya warship strike"),
    ("2", "killed in Dymer apartment strike"),
    ("17.5%", "Taiwan stocks' fall in one week"),
    ("128", "nations backing killer-robot rules"),
]


def draw_stat_strip(ctx):
    for i, (num, cap) in enumerate(STAT_CELLS):
        x = 12 + i * 167
        fill_rect(ctx, x, 122, 163, 46, PAPER)
        stroke_rect(ctx, x, 122, 163, 46, LINE)
        put_text(ctx, x + 8, 124, num, "DejaVu Sans", 19, RED, bold=True)
        put_wrapped(ctx, x + 8, 146, cap, "DejaVu Sans", 8, GREY,
                    163 - 16, 10)


REGION_SEGS = [
    ("EUROPE", 6, NAVY), ("MIDDLE EAST", 7, RED),
    ("AMERICAS", 6, rgb(46, 110, 62)), ("ASIA", 7, rgb(196, 110, 20)),
    ("AFRICA", 6, rgb(140, 95, 45)), ("GLOBAL", 3, rgb(88, 70, 140)),
]


def draw_region_bar(ctx):
    """Bar rekonsiliasi 6/7/6/6/7/3 = 35 — angka WAJIB tampil."""
    x = 12.0
    for name, n, col in REGION_SEGS:
        w = 1000.0 * n / 35.0
        fill_rect(ctx, x, 170, w, 18, col)
        put_text(ctx, x + w / 2, 174, "%s %d" % (name, n), "DejaVu Sans", 10,
                 WHITE, bold=True, align="center")
        x += w


# ---- hero: langit, laut, bulan, camar ----

def hero_sky_sea(ctx):
    # langit: gradien 4 stop, laut: 2 stop (sedikit lebih terang dari
    # Cairo supaya fraksi gelap halaman turun dari tepi atas 20,4%
    # dan memberi ruang untuk panel malam Merkurius)
    lin_grad(ctx, 0, HERO_Y0, 0, SEA_Y, [
        (0.0, rgb(10, 27, 51)), (0.28, rgb(44, 72, 108)),
        (0.68, rgb(110, 145, 180)), (1.0, rgb(214, 122, 52))])
    ctx.rectangle(HERO_X0, HERO_Y0, HERO_X1 - HERO_X0, SEA_Y - HERO_Y0)
    ctx.fill()
    lin_grad(ctx, 0, SEA_Y, 0, HERO_Y1, [
        (0.0, rgb(64, 102, 130)), (1.0, rgb(52, 92, 120))])
    ctx.rectangle(HERO_X0, SEA_Y, HERO_X1 - HERO_X0, HERO_Y1 - SEA_Y)
    ctx.fill()
    rng = random.Random(11)
    for _ in range(70):
        disc(ctx, rng.uniform(20, 1004), rng.uniform(200, 342),
             rng.uniform(1.0, 2.0), rgb(220, 228, 240))
    # camar: 5 siluet "v" kecil di langit
    ctx.save()
    ctx.set_source_rgb(*rgb(30, 40, 55))
    ctx.set_line_width(1.6)
    for gx, gy, gs in ((300, 230, 7), (340, 248, 5), (640, 224, 6),
                       (700, 252, 5), (240, 268, 4)):
        ctx.new_path()
        ctx.move_to(gx - gs, gy)
        ctx.curve_to(gx - gs * 0.4, gy - gs * 0.8, gx - gs * 0.1,
                     gy - gs * 0.5, gx, gy)
        ctx.curve_to(gx + gs * 0.1, gy - gs * 0.5, gx + gs * 0.4,
                     gy - gs * 0.8, gx + gs, gy)
        ctx.stroke()
    ctx.restore()
    # bulan: halo radial + cakram + 2 kawah
    rad_grad(ctx, 880, 256, 0, 90, [
        (0.0, rgba(212, 204, 170, 0.55)), (0.5, rgba(212, 204, 170, 0.18)),
        (1.0, rgba(212, 204, 170, 0.0))])
    ctx.arc(880, 256, 90, 0, 2 * math.pi)
    ctx.fill()
    rad_grad(ctx, 880, 256, 0, 28, [
        (0.0, rgba(248, 242, 218, 1.0)), (1.0, rgba(226, 219, 190, 1.0))])
    ctx.arc(880, 256, 28, 0, 2 * math.pi)
    ctx.fill()
    for kx, ky, kr in ((872, 248, 5), (890, 264, 4)):
        disc(ctx, kx, ky, kr, rgb(210, 202, 172))
    # tanker jauh di horizon kanan
    fill_rect(ctx, 838, 436, 150, 16, rgb(24, 40, 60))
    fill_rect(ctx, 846, 424, 12, 12, rgb(24, 40, 60))


def hero_tanker(ctx):
    # lambung utama bezier, haluan meruncing ke kiri
    ctx.save()
    ctx.set_source_rgb(*rgb(16, 22, 30))
    ctx.new_path()
    ctx.move_to(170, SEA_Y)
    ctx.line_to(826, SEA_Y)
    ctx.line_to(826, 478)
    ctx.curve_to(700, 488, 400, 488, 300, 486)
    ctx.curve_to(230, 484, 185, 472, 170, SEA_Y)
    ctx.close_path()
    ctx.fill()
    ctx.restore()
    fill_rect(ctx, 170, 470, 656, 8, rgb(120, 40, 30))  # strip garis air
    fill_rect(ctx, 700, 392, 62, 60, rgb(24, 32, 44))   # anjungan
    for r in range(3):
        for c in range(3):
            fill_rect(ctx, 710 + c * 18, 404 + r * 16, 10, 8, GOLD)
    fill_rect(ctx, 668, 408, 20, 44, rgb(24, 32, 44))   # cerobong
    fill_rect(ctx, 668, 396, 20, 12, rgb(150, 50, 35))  # atap merah
    for i in range(5):                                  # 5 palka kargo
        fill_rect(ctx, 200 + i * 88, 438, 60, 14, rgb(34, 44, 56))
    # karat + garis dek tipis di lambung
    ctx.save()
    ctx.set_source_rgba(140, 80, 40, 0.55)
    ctx.set_line_width(1)
    for px, py in ((260, 480), (420, 482), (580, 480)):
        ctx.move_to(px, py)
        ctx.line_to(px + 18, py + 2)
        ctx.stroke()
    ctx.restore()

def hero_fire_plume(ctx):
    # glow radial oranye di belakang api (tidak sampai teks)
    rad_grad(ctx, 520, 400, 0, 130, [
        (0.0, rgba(240, 140, 50, 0.20)), (0.5, rgba(240, 140, 50, 0.08)),
        (1.0, rgba(240, 140, 50, 0.0))])
    ctx.arc(520, 400, 130, 0, 2 * math.pi)
    ctx.fill()
    # dasar api lebih padat: 3 lidah besar + 3 lidah kecil di antaranya
    flame_tongue(ctx, 470, SEA_Y, 38, 88, tilt=-0.12)
    flame_tongue(ctx, 540, SEA_Y, 46, 108, tilt=0.05)
    flame_tongue(ctx, 600, SEA_Y, 32, 70, tilt=0.15)
    flame_tongue(ctx, 505, SEA_Y, 22, 48, tilt=-0.05)
    flame_tongue(ctx, 572, SEA_Y, 18, 40, tilt=0.10)
    flame_tongue(ctx, 432, SEA_Y, 16, 36, tilt=-0.18)
    embers(ctx, 520, 400, seed=31, count=30)
    # asap: kolom TEBAL per lidah api — pangkal di ujung lidah,
    # spine melengkung kait (hanyut kiri di bawah, naik tegak di
    # atas), puncak berhenti di y~240 (di bawah headline, ujung
    # ramping supaya teks tetap bersih)
    smoke_plume(ctx, [(538, 350), (520, 330), (500, 310), (482, 292),
                      (470, 272), (462, 254), (458, 240)],
                 36, 14, rgb(64, 64, 68), rgb(120, 120, 126), alpha=0.8)
    smoke_plume(ctx, [(596, 386), (580, 366), (562, 346), (546, 326),
                      (534, 310)],
                 24, 12, rgb(64, 64, 68), rgb(120, 120, 126), alpha=0.8)


def hero_mine_blast(ctx):
    """Ledakan ranjau kiri hero, DIHALUSKAN: tanpa lingkaran putih,
    semburan berupa busur-busur lembut + busa (bukan piktogram)."""
    # pijar rendah di garis air + inti kuning kecil
    rad_grad(ctx, 150, SEA_Y, 0, 34, [
        (0.0, rgba(240, 140, 50, 0.55)), (0.6, rgba(240, 140, 50, 0.18)),
        (1.0, rgba(240, 140, 50, 0.0))])
    ctx.arc(150, SEA_Y, 34, 0, 2 * math.pi)
    ctx.fill()
    ctx.save()
    ctx.set_source_rgb(*rgb(248, 205, 80))
    ctx.new_path()
    ctx.move_to(140, SEA_Y)
    ctx.curve_to(144, 436, 147, 430, 150, 426)
    ctx.curve_to(153, 430, 156, 436, 160, SEA_Y)
    ctx.close_path()
    ctx.fill()
    ctx.restore()
    # semburan air: 3 busur putih lembut (bukan segitiga tajam)
    ctx.save()
    ctx.set_source_rgba(1, 1, 1, 0.8)
    ctx.set_line_width(2.0)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for sx, sh in ((132, 26), (150, 34), (168, 24)):
        ctx.new_path()
        ctx.move_to(sx - 5, SEA_Y)
        ctx.curve_to(sx - 2, SEA_Y - sh, sx + 2, SEA_Y - sh * 0.6,
                     sx + 5, SEA_Y - 4)
        ctx.stroke()
    # busa di permukaan: pita PIPIH menempel garis air (bukan kubah)
    # — elips diratakan (rx 30, ry ~5) + streak kedua lebih redup,
    # supaya tidak ada lagi kubah transparan di atas air; busur +
    # pijar tetap jadi isi ledakan
    ctx.save()
    ctx.translate(150, SEA_Y + 2)
    ctx.scale(1.0, 0.18)
    ctx.set_source_rgba(1, 1, 1, 0.5)
    ctx.arc(0, 0, 30, 0, 2 * math.pi)
    ctx.fill()
    ctx.restore()
    ctx.save()
    ctx.translate(150, SEA_Y + 5)
    ctx.scale(1.0, 0.15)
    ctx.set_source_rgba(1, 1, 1, 0.3)
    ctx.arc(0, 0, 40, 0, 2 * math.pi)
    ctx.fill()
    ctx.restore()
    ctx.set_source_rgba(1, 1, 1, 0.6)
    for dx, dy, dr in ((-30, -6, 2.2), (32, -9, 2.0), (-22, 4, 1.8),
                       (26, 3, 2.2), (-8, -18, 1.6), (10, -14, 1.6)):
        ctx.arc(150 + dx, SEA_Y + dy, dr, 0, 2 * math.pi)
        ctx.fill()
    ctx.restore()
    # ranjau laut mengambang dekat lambung (630,497)
    ctx.save()
    ctx.set_source_rgb(*rgb(16, 22, 30))
    ctx.arc(630, 497, 10, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_line_width(2)
    for k in range(8):
        a = k * math.pi / 4
        ctx.move_to(630 + math.cos(a) * 9, 497 + math.sin(a) * 9)
        ctx.line_to(630 + math.cos(a) * 15, 497 + math.sin(a) * 15)
    ctx.stroke()
    ctx.restore()


def hero_text(ctx):
    tag(ctx, 28, 206, "2  \u00b7  HORMUZ \u2014 MIDDLE EAST", 11, RED, WHITE)
    put_text(ctx, 28, 236, "Mines hit tankers in Hormuz", "DejaVu Serif",
             34, WHITE, bold=True)
    put_wrapped(ctx, 28, 278,
                "Iran claims two more tankers struck by sea mines, six in two days; "
                "UKMTO reports a vessel hit by an unknown projectile. "
                "Iran's claim is unverified.",
                "DejaVu Sans", 15, rgb(232, 236, 242), 620, 20)
    w1 = tag(ctx, 28, 506, "6 TANKERS", 12, RED, WHITE)
    tag(ctx, 28 + w1 + 8, 506, "BRENT $92.44", 12, WHITE, INK)
    put_text(ctx, 1000, 512, "AP via OilPrice, 23 Nov", "DejaVu Sans", 10,
             rgb(226, 232, 240), align="right")
    stroke_rect(ctx, 12, 192, 1000, 350, LINE)


def draw_hero(ctx):
    hero_sky_sea(ctx)
    hero_tanker(ctx)
    hero_fire_plume(ctx)
    hero_mine_blast(ctx)
    sea_texture(ctx)
    hero_text(ctx)


# ---- teks panel (layout ketat Cairo — metrik Cairo ~2-3% lebih lebar) ----

def panel_body(ctx, x, img_bottom, w, kicker, headline, dek, sumber,
               hsize=15, dsize=10):
    """kicker +11 -> headline (lh hsize+2) +2 -> dek (lh dsize+2) +2
    -> sumber. Mid muat 68px, secondary 84px."""
    y = img_bottom + 1
    put_text(ctx, x + 8, y, kicker, "DejaVu Sans", 9, RED, bold=True)
    y += 11
    n = put_wrapped(ctx, x + 8, y, headline, "DejaVu Serif", hsize, INK,
                    w - 16, hsize + 2, bold=True)
    y += n * (hsize + 2) + 2
    n = put_wrapped(ctx, x + 8, y, dek, "DejaVu Sans", dsize, BODY,
                    w - 16, dsize + 2)
    y += n * (dsize + 2) + 2
    put_text(ctx, x + 8, y, sumber, "DejaVu Sans", 8, GREY)


def panel_frame(ctx, x, y, w, h):
    stroke_rect(ctx, x, y, w, h, LINE)

# ---- panel tengah ----

def panel_cop31(ctx):
    x, y, w = 12, 546, 496
    fill_rect(ctx, x, y, w, 84, rgb(214, 226, 236))  # langit
    # bendera-bendera kecil berjajar di atas (kerumunan summit)
    fcols = [rgb(176, 40, 60), rgb(40, 90, 160), rgb(240, 200, 90),
             rgb(46, 110, 62), rgb(150, 90, 170), rgb(200, 90, 40)]
    for i, col in enumerate(fcols):
        fx = x + 150 + i * 44
        ctx.save()
        ctx.set_source_rgb(*rgb(90, 84, 70))
        ctx.set_line_width(1.5)
        ctx.move_to(fx, y + 6)
        ctx.line_to(fx, y + 22)
        ctx.stroke()
        ctx.set_source_rgb(*col)
        ctx.new_path()
        ctx.move_to(fx, y + 6)
        ctx.line_to(fx + 16, y + 10)
        ctx.line_to(fx, y + 14)
        ctx.close_path()
        ctx.fill()
        ctx.restore()
    # globe + benua
    ctx.save()
    ctx.set_source_rgb(*rgb(52, 110, 170))
    ctx.arc(x + 57, y + 49, 35, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_source_rgb(*rgb(90, 160, 90))
    for bx, by, br in ((45, 38, 9), (66, 52, 11), (50, 62, 7)):
        ctx.arc(x + bx, y + by, br, 0, 2 * math.pi)
        ctx.fill()
    ctx.set_source_rgb(*rgb(120, 175, 100))
    ctx.arc(x + 72, y + 34, 6, 0, 2 * math.pi)
    ctx.fill()
    ctx.restore()
    # baris belakang: 5 delegasi LENGKAP — kepala + bahu/badan (r4:
    # kepala saja sehingga tampak melayang); bahu trapesium turun
    # sampai tepi meja (y+62), warna jas diredupkan supaya baris
    # belakang terasa lebih jauh daripada baris depan
    back_suits = [rgb(137, 31, 47), rgb(153, 94, 31), rgb(117, 70, 133),
                  rgb(47, 101, 133), rgb(156, 70, 31)]
    for i, suit in enumerate(back_suits):
        dx = x + 186 + i * 52
        ctx.save()
        ctx.set_source_rgb(*suit)
        ctx.new_path()
        ctx.move_to(dx - 9, y + 62)
        ctx.line_to(dx + 9, y + 62)
        ctx.line_to(dx + 6, y + 38)
        ctx.line_to(dx - 6, y + 38)
        ctx.close_path()
        ctx.fill()
        ctx.restore()
        disc(ctx, dx, y + 32, 6, rgb(210, 180, 145))
    # meja summit + kertas-kertas di atasnya
    fill_rect(ctx, x + 130, y + 62, 290, 20, rgb(122, 84, 52))
    fill_rect(ctx, x + 130, y + 62, 290, 5, rgb(146, 104, 66))
    for i, px in enumerate((150, 230, 310, 380)):
        fill_rect(ctx, x + px, y + 57, 22, 5, WHITE)
    # 5 delegasi baris depan
    cols = [rgb(176, 40, 60), rgb(196, 120, 40), rgb(150, 90, 170),
            rgb(60, 130, 170), rgb(200, 90, 40)]
    for i, col in enumerate(cols):
        dx = x + 160 + i * 52
        disc(ctx, dx, y + 44, 9, rgb(232, 200, 160))
        ctx.save()
        ctx.set_source_rgb(*col)
        ctx.new_path()
        ctx.move_to(dx - 12, y + 62)
        ctx.line_to(dx + 12, y + 62)
        ctx.line_to(dx + 8, y + 52)
        ctx.line_to(dx - 8, y + 52)
        ctx.close_path()
        ctx.fill()
        ctx.restore()
    # termometer kanan (merkuri jatuh)
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
    tag(ctx, x + 8, y + 6, "COP31: NO DEAL", 10, RED, WHITE)
    cw = measure(ctx, "$120BN CUT", "DejaVu Sans", 10, bold=True) + 12
    tag(ctx, x + w - 8 - cw, y + 6, "$120BN CUT", 10, WHITE, INK)
    panel_body(ctx, x, y + 84, w, "1  ANTALYA, TURKEY \u00b7 CLIMATE",
               "COP31 collapses with no deal",
               "Two days of overtime end in failure: the draft never "
               "mentions fossil fuels and the $120bn adaptation target "
               "is dropped.",
               "IPS / Global Issues, 22 Nov")
    panel_frame(ctx, x, y, w, 152)


def panel_libya(ctx):
    x, y, w = 516, 546, 496
    fill_rect(ctx, x, y, w, 56, rgb(206, 216, 224))   # langit
    fill_rect(ctx, x, y + 56, w, 28, rgb(158, 180, 196))  # laut
    # garis ombak tipis di laut
    ctx.save()
    ctx.set_source_rgba(1, 1, 1, 0.35)
    ctx.set_line_width(1.2)
    for wy in (y + 64, y + 72, y + 79):
        ctx.new_path()
        ctx.move_to(x + 20, wy)
        ctx.curve_to(x + 150, wy - 3, x + 320, wy + 3, x + 470, wy)
        ctx.stroke()
    ctx.restore()
    # kapal korvet miring ~10 derajat, haluan ke kanan
    ctx.save()
    ctx.translate(x + 250, y + 40)
    ctx.rotate(-math.radians(10))
    ctx.set_source_rgb(*rgb(96, 104, 112))
    ctx.new_path()
    ctx.move_to(-190, -6)
    ctx.line_to(170, -6)
    ctx.curve_to(196, -4, 202, 2, 196, 8)
    ctx.curve_to(120, 20, -120, 20, -178, 10)
    ctx.curve_to(-192, 6, -194, -2, -190, -6)
    ctx.close_path()
    ctx.fill()
    ctx.set_source_rgb(*rgb(74, 80, 88))
    ctx.new_path()
    ctx.move_to(-178, 8)
    ctx.curve_to(-60, 18, 100, 18, 192, 6)
    ctx.line_to(196, 10)
    ctx.curve_to(100, 22, -60, 22, -182, 12)
    ctx.close_path()
    ctx.fill()
    ctx.set_source_rgb(*rgb(150, 60, 45))
    ctx.rectangle(-188, -2, 380, 4)
    ctx.fill()
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
    ctx.set_source_rgb(*rgb(60, 64, 70))
    ctx.rectangle(-196, -10, 8, 20)
    ctx.fill()
    ctx.set_line_width(1)
    ctx.move_to(-196, -10)
    ctx.line_to(-196, -18)
    ctx.stroke()
    ctx.set_source_rgb(*rgb(88, 96, 104))
    ctx.rectangle(-30, -34, 70, 28)
    ctx.fill()
    ctx.set_source_rgb(*rgb(60, 64, 70))
    ctx.rectangle(-30, -38, 70, 5)
    ctx.fill()
    for i in range(4):
        fill_rect(ctx, -22 + i * 16, -28, 9, 7, GOLD)
    fill_rect(ctx, 52, -30, 14, 24, rgb(96, 100, 106))
    fill_rect(ctx, 52, -34, 14, 5, rgb(30, 30, 32))
    ctx.set_source_rgb(*rgb(88, 96, 104))
    ctx.arc(140, -6, 12, math.pi, 2 * math.pi)
    ctx.fill()
    ctx.set_line_width(4)
    ctx.move_to(140, -14)
    ctx.line_to(168, -22)
    ctx.stroke()
    ctx.set_line_width(2)
    ctx.move_to(10, -38)
    ctx.line_to(10, -58)
    ctx.stroke()
    ctx.set_source_rgb(*RED)
    ctx.new_path()
    ctx.move_to(10, -58)
    ctx.line_to(26, -54)
    ctx.line_to(10, -50)
    ctx.close_path()
    ctx.fill()
    ctx.restore()
    # api di garis air buritan + haluan, asap tipis di atasnya
    flame_tongue(ctx, x + 70, y + 58, 22, 34, tilt=-0.1)
    flame_tongue(ctx, x + 440, y + 58, 16, 24, tilt=0.1)
    smoke_plume(ctx, [(x + 70, y + 28), (x + 63, y + 14), (x + 56, y + 4)],
                 8, 6, rgb(46, 46, 50), rgb(88, 88, 92), alpha=0.5)
    # drone + jejak kanan atas
    ctx.save()
    ctx.set_source_rgb(*rgb(40, 40, 40))
    ctx.arc(x + 430, y + 12, 3, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_source_rgba(200, 60, 40, 0.8)
    ctx.set_line_width(1.5)
    ctx.move_to(x + 430, y + 12)
    ctx.line_to(x + 470, y + 4)
    ctx.stroke()
    ctx.restore()
    # puing di air (lebih banyak dari Cairo)
    for px, py, pr in ((x + 150, y + 68, 3), (x + 300, y + 72, 2),
                       (x + 380, y + 66, 3), (x + 90, y + 74, 2),
                       (x + 250, y + 78, 2)):
        disc(ctx, px, py, pr, rgb(90, 90, 88))
    tag(ctx, x + 8, y + 6, "10 INJURED", 10, RED, WHITE)
    tag(ctx, x + 108, y + 6, "SHIP CAPSIZED", 10, WHITE, INK)
    panel_body(ctx, x, y + 84, w, "3  BENGHAZI, LIBYA \u00b7 WAR AT SEA",
               "Russian warship struck in Libya",
               "Suspected Ukrainian sea drones hit the corvette Merkury. "
               "The ship is badly damaged and capsizes; Kyiv and Moscow silent.",
               "AP / Reuters / BBC Verify, 22 Nov")
    panel_frame(ctx, x, y, w, 152)

# ---- panel secondary ----

def panel_kyiv(ctx):
    """Adegan kota malam: 2 blok apartemen + jalan + lampu + api."""
    x, y, w = 12, 702, 244
    fill_rect(ctx, x, y, w, 52, rgb(13, 30, 51))
    rng = random.Random(4)
    for _ in range(14):
        disc(ctx, x + rng.uniform(6, w - 6), y + rng.uniform(4, 50),
             rng.uniform(0.8, 1.6), rgb(220, 228, 240))
    # blok kiri (lebih rendah, gelap) + blok utama kanan
    fill_rect(ctx, x + 8, y + 26, 44, 26, rgb(20, 32, 50))
    lit_l = [(0, 0), (1, 1), (0, 2)]
    for r in range(3):
        for c in range(2):
            col = GOLD if (c, r) in lit_l else rgb(52, 64, 84)
            fill_rect(ctx, x + 14 + c * 18, y + 29 + r * 8, 10, 5, col)
    fill_rect(ctx, x + 60, y + 14, 90, 38, rgb(26, 40, 60))
    lit = [(0, 0), (2, 1), (1, 2), (3, 2), (0, 3), (2, 3)]
    for r in range(4):
        for c in range(4):
            col = GOLD if (c, r) in lit else rgb(60, 74, 96)
            fill_rect(ctx, x + 66 + c * 20, y + 18 + r * 9, 12, 6, col)
    # jalan di bawah blok + lampu jalan menyala di celah antar blok
    fill_rect(ctx, x, y + 50, w, 2, rgb(40, 48, 62))
    ctx.save()
    ctx.set_source_rgb(*rgb(90, 84, 70))
    ctx.set_line_width(1.5)
    ctx.move_to(x + 56, y + 50)
    ctx.line_to(x + 56, y + 38)
    ctx.stroke()
    ctx.set_source_rgb(*rgb(240, 200, 90))
    ctx.arc(x + 56, y + 37, 2.5, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_source_rgba(240, 200, 90, 0.35)
    ctx.arc(x + 56, y + 37, 6, 0, 2 * math.pi)
    ctx.fill()
    ctx.restore()
    # api memakan sisi kanan blok + asap plume kecil + bara
    flame_tongue(ctx, x + 152, y + 52, 20, 30, tilt=0.1)
    flame_tongue(ctx, x + 168, y + 52, 12, 18, tilt=0.15)
    smoke_plume(ctx, [(x + 152, y + 26), (x + 147, y + 12), (x + 142, y + 2)],
                 7, 5, rgb(46, 46, 50), rgb(88, 88, 92), alpha=0.5)
    for ex, ey, er in ((150, 14, 1.6), (158, 8, 1.3), (164, 18, 1.5),
                       (146, 20, 1.2), (170, 10, 1.4)):
        ctx.save()
        ctx.set_source_rgba(248, 180, 60, 0.85)
        ctx.arc(x + ex, y + ey, er, 0, 2 * math.pi)
        ctx.fill()
        ctx.restore()
    # drone + jejak merah kanan atas
    ctx.save()
    ctx.set_source_rgb(*rgb(220, 220, 220))
    ctx.arc(x + 210, y + 12, 3, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_source_rgba(200, 60, 40, 0.8)
    ctx.set_line_width(1.5)
    ctx.move_to(x + 210, y + 12)
    ctx.line_to(x + 232, y + 6)
    ctx.stroke()
    ctx.restore()
    tag(ctx, x + 8, y + 6, "2 KILLED", 9, RED, WHITE)
    panel_body(ctx, x, y + 52, w, "4  DYMER, UKRAINE \u00b7 WAR",
               "Drone hits Kyiv apartment block",
               "Russian drone strikes a 5-storey block in Dymer. 2 dead, "
               "11 missing, among them 2 children.",
               "Al Jazeera / AP, 22 Nov", hsize=12, dsize=9)
    panel_frame(ctx, x, y, w, 136)


def panel_mercury(ctx):
    """Adegan luar angkasa MALAM (panel gelap ke-2 di halaman):
    langit hitam berbintang + Merkurius berkawah + probe emas."""
    x, y, w = 264, 702, 244
    fill_rect(ctx, x, y, w, 52, rgb(12, 20, 38))
    rng = random.Random(9)
    for _ in range(26):
        disc(ctx, x + rng.uniform(4, w - 4), y + rng.uniform(4, 48),
             rng.uniform(0.7, 1.5), rgb(220, 228, 240))
    # cincin orbit elips tipis
    ctx.save()
    ctx.set_source_rgba(180, 175, 150, 0.7)
    ctx.set_line_width(1)
    ctx.translate(x + 178, y + 26)
    ctx.scale(1.6, 0.55)
    ctx.arc(0, 0, 34, 0, 2 * math.pi)
    ctx.stroke()
    ctx.restore()
    # planet berkawah + bayangan terminator (sabit gelap kanan)
    ctx.save()
    ctx.set_source_rgb(*rgb(168, 162, 150))
    ctx.arc(x + 178, y + 26, 26, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_source_rgb(*rgb(138, 132, 120))
    for kx, ky, kr in ((168, 18, 5), (188, 30, 6), (176, 38, 4),
                       (190, 14, 3), (166, 30, 3)):
        ctx.arc(x + kx, y + ky, kr, 0, 2 * math.pi)
        ctx.fill()
    ctx.set_source_rgba(20, 26, 40, 0.5)
    ctx.arc(x + 192, y + 26, 24, 0, 2 * math.pi)
    ctx.fill()
    ctx.restore()
    # probe kiri: badan emas + panel surya biru + garis ke planet
    ctx.save()
    ctx.set_source_rgb(*rgb(60, 90, 140))
    ctx.rectangle(x + 12, y + 22, 26, 12)
    ctx.fill()
    ctx.set_source_rgb(*rgb(200, 160, 60))
    ctx.rectangle(x + 40, y + 20, 18, 16)
    ctx.fill()
    ctx.set_source_rgba(220, 220, 220, 0.8)
    ctx.set_line_width(1)
    ctx.move_to(x + 58, y + 28)
    ctx.line_to(x + 152, y + 30)
    ctx.stroke()
    # antena kecil di probe
    ctx.move_to(x + 49, y + 20)
    ctx.line_to(x + 49, y + 12)
    ctx.stroke()
    ctx.set_source_rgb(*rgb(240, 200, 90))
    ctx.arc(x + 49, y + 11, 2, 0, 2 * math.pi)
    ctx.fill()
    ctx.restore()
    tag(ctx, x + 8, y + 6, "2ND EVER", 9, RED, WHITE)
    panel_body(ctx, x, y + 52, w, "6  SPACE \u00b7 MERCURY",
               "BepiColombo enters Mercury orbit",
               "The ESA-JAXA probe becomes only the second mission to "
               "orbit Mercury, on 21 Nov.",
               "Reported 23 Nov", hsize=12, dsize=9)
    panel_frame(ctx, x, y, w, 136)

def panel_bursa(ctx):
    """Adegan bursa yang hidup: papan besar + ticker tape + 4 trader
    di meja + layar candlestick — bukan garis di latar putih."""
    x, y, w = 516, 702, 244
    fill_rect(ctx, x, y, w, 52, rgb(238, 230, 208))  # lantai bursa hangat
    # papan besar kiri: garis merah jatuh + kepala panah + angka
    fill_rect(ctx, x + 8, y + 6, 118, 26, WHITE)
    stroke_rect(ctx, x + 8, y + 6, 118, 26, rgb(200, 190, 165))
    ctx.save()
    ctx.set_source_rgb(*RED)
    ctx.set_line_width(2.5)
    ctx.move_to(x + 14, y + 11)
    ctx.line_to(x + 48, y + 20)
    ctx.line_to(x + 80, y + 16)
    ctx.line_to(x + 116, y + 28)
    ctx.stroke()
    ctx.new_path()
    ctx.move_to(x + 116, y + 28)
    ctx.line_to(x + 106, y + 23)
    ctx.line_to(x + 107, y + 31)
    ctx.close_path()
    ctx.fill()
    ctx.restore()
    # layar candlestick kanan atas
    fill_rect(ctx, x + 132, y + 6, 104, 26, rgb(24, 32, 44))
    for i, (ch, cw_) in enumerate(((8, 6), (14, 8), (6, 5), (16, 9), (10, 6))):
        bx = x + 140 + i * 19
        col = RED if i % 2 == 0 else rgb(46, 160, 90)
        fill_rect(ctx, bx, y + 28 - ch, 8, ch, col)
        ctx.save()
        ctx.set_source_rgb(*col)
        ctx.set_line_width(1)
        ctx.move_to(bx + 4, y + 28 - ch - 3)
        ctx.line_to(bx + 4, y + 28 - ch + ch + 2)
        ctx.stroke()
        ctx.restore()
    # ticker tape: strip tipis batang merah/hijau di antara papan dan trader
    for i, bh in enumerate((3, 5, 3, 6, 4, 5, 2)):
        col = RED if i % 3 != 1 else rgb(46, 160, 90)
        fill_rect(ctx, x + 14 + i * 32, y + 37 - bh, 14, bh, col)
    # 4 trader di meja (kepala + bahu + dasi)
    tcols = [rgb(60, 60, 70), rgb(120, 40, 50), rgb(40, 70, 120),
             rgb(90, 70, 40)]
    for i, (tx, col) in enumerate(zip((36, 96, 156, 210), tcols)):
        disc(ctx, x + tx, y + 42, 5, rgb(232, 200, 160))
        ctx.save()
        ctx.set_source_rgb(*col)
        ctx.new_path()
        ctx.move_to(x + tx - 9, y + 52)
        ctx.line_to(x + tx + 9, y + 52)
        ctx.line_to(x + tx + 6, y + 46)
        ctx.line_to(x + tx - 6, y + 46)
        ctx.close_path()
        ctx.fill()
        ctx.restore()
    tag(ctx, x + 8, y + 6, "-17.5%", 9, RED, WHITE)
    panel_body(ctx, x, y + 52, w, "7  TAIPEI \u00b7 MARKETS",
               "Markets plunge; Taiwan bans shorting",
               "US stocks tumble; Taiwan shares fall 17.5% in a week; "
               "short-selling banned from Monday.",
               "23 Nov", hsize=12, dsize=9)
    panel_frame(ctx, x, y, w, 136)


def panel_pbb(ctx):
    x, y, w = 768, 702, 244
    fill_rect(ctx, x, y, w, 52, rgb(222, 228, 236))
    # dinding navy + angka 128
    fill_rect(ctx, x + 60, y + 6, 124, 24, NAVY)
    put_text(ctx, x + 122, y + 8, "128", "DejaVu Sans", 20, WHITE,
             bold=True, align="center")
    # deret 12 bendera kecil (lebih padat dari Cairo)
    fcols = [rgb(176, 40, 60), rgb(40, 90, 160), rgb(240, 200, 90),
             rgb(46, 110, 62), rgb(150, 90, 170), rgb(200, 90, 40),
             rgb(60, 130, 170), rgb(196, 120, 40), rgb(176, 40, 60),
             rgb(40, 90, 160), rgb(46, 110, 62), rgb(150, 90, 170)]
    for i, col in enumerate(fcols):
        fill_rect(ctx, x + 34 + i * 16, y + 34, 12, 8, col)
    # meja melengkung + 5 kepala delegasi + mikrofon
    ctx.save()
    ctx.set_source_rgb(*rgb(150, 120, 80))
    ctx.new_path()
    ctx.move_to(x + 20, y + 52)
    ctx.curve_to(x + 80, y + 42, x + 170, y + 42, x + 224, y + 52)
    ctx.line_to(x + 224, y + 52)
    ctx.line_to(x + 20, y + 52)
    ctx.close_path()
    ctx.fill()
    ctx.set_source_rgb(*rgb(232, 200, 160))
    for hx in (52, 92, 122, 152, 192):
        ctx.arc(x + hx, y + 42, 5, 0, 2 * math.pi)
        ctx.fill()
    # mikrofon di depan delegasi tengah
    ctx.set_source_rgb(*rgb(40, 40, 40))
    ctx.set_line_width(1.5)
    ctx.move_to(x + 122, y + 44)
    ctx.line_to(x + 122, y + 36)
    ctx.stroke()
    ctx.arc(x + 122, y + 34, 2.5, 0, 2 * math.pi)
    ctx.fill()
    ctx.restore()
    tag(ctx, x + 8, y + 6, "128 NATIONS", 9, RED, WHITE)
    panel_body(ctx, x, y + 52, w, "9  UNITED NATIONS \u00b7 ARMS",
               "128 nations back killer-robot rules",
               "At a UN conference, 128 countries agree to pursue rules "
               "on autonomous weapons by 2028.",
               "23 Nov", hsize=12, dsize=9)
    panel_frame(ctx, x, y, w, 136)

# ---- pita bawah: peta dotted + ALSO ON + DATE CHECK ----

LAND_ELLIPSES = [(-100, 50, 28, 16), (-95, 32, 20, 10), (-85, 18, 9, 7),
                 (-150, 64, 12, 7), (-42, 73, 9, 5), (-60, -8, 13, 13),
                 (-66, -28, 8, 11), (14, 6, 19, 16), (20, -20, 13, 11),
                 (44, 4, 8, 7), (10, 50, 16, 9), (38, 54, 22, 11),
                 (75, 56, 28, 12), (100, 42, 16, 9), (78, 21, 11, 9),
                 (104, 14, 9, 7), (113, 33, 11, 7), (139, 37, 5, 7),
                 (128, -24, 13, 7), (172, -41, 4, 3), (100, -2, 7, 5),
                 (44, 24, 7, 5), (-2, 54, 3, 4)]

MAP_PINS = [(1, 30.7, 36.9, 5, -3), (2, 56.2, 26.5, 0, 0),
            (3, 20.1, 32.1, -6, 4), (4, 30.5, 50.4, -8, -8),
            (7, 121.0, 23.7, 0, 0), (9, -74.0, 40.7, 0, 0)]

ALSO_ON_ITEMS = [
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


def lonlat_to_xy(lon, lat):
    return (12 + (lon + 168) / 360.0 * 300,
            868 + (75 - lat) / 130.0 * 118)


def _on_land(px, py):
    for lon, lat, rx, ry in LAND_ELLIPSES:
        cx, cy = lonlat_to_xy(lon, lat)
        sx = (300.0 / 360.0) * rx
        sy = (118.0 / 130.0) * ry
        if ((px - cx) / sx) ** 2 + ((py - cy) / sy) ** 2 <= 1:
            return True
    return False


def draw_bottom_band(ctx):
    put_text(ctx, 12, 842, "WHERE IT HAPPENED", "DejaVu Sans", 11, INK,
             bold=True)
    put_text(ctx, 12, 855, "pins match story numbers", "DejaVu Sans", 8,
             GREY)
    put_text(ctx, 324, 842, "ALSO ON MONDAY 23 NOVEMBER \u2014 28 MORE STORIES",
             "DejaVu Sans", 11, INK, bold=True)
    # peta dotted: grid 5px, titik hanya di daratan
    ctx.save()
    ctx.set_source_rgb(*rgb(169, 143, 95))
    gy = 868
    while gy <= 986:
        px = 12
        while px <= 312:
            if _on_land(px, gy):
                ctx.arc(px, gy, 1.5, 0, 2 * math.pi)
                ctx.fill()
            px += 5
        gy += 5
    ctx.restore()
    # 6 pin bernomor (pin 6 tidak ada: Merkurius mengorbit)
    for num, lon, lat, nx, ny in MAP_PINS:
        px, py = lonlat_to_xy(lon, lat)
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
        put_text(ctx, px, py - 5.5, str(num), "DejaVu Sans", 8, WHITE,
                 bold=True, align="center")
    # ALSO ON: 2 kolom x 14 baris
    for i, (num, txt) in enumerate(ALSO_ON_ITEMS):
        col = 0 if i < 14 else 1
        row = i % 14
        bx = 324 if col == 0 else 672
        by = 860 + row * 9
        put_text(ctx, bx, by, str(num), "DejaVu Sans", 8, RED, bold=True)
        put_text(ctx, bx + 18, by, txt, "DejaVu Sans", 8, BODY)


def draw_date_check_footer(ctx):
    ctx.save()
    ctx.set_source_rgb(*RED)
    ctx.set_line_width(1)
    ctx.rectangle(12.5, 990.5, 1000, 22)
    ctx.stroke()
    ctx.restore()
    put_text(ctx, 12, 992,
             "Every story here was reported or still developing on Monday "
             "23 November 2026, in at least one time zone.",
             "DejaVu Sans", 8, INK)
    put_text(ctx, 12, 1002,
             "DATE CHECK \u2014 Left out: 'El Chapo Isidro' captured (20 Nov) "
             "\u00b7 Huang return ruled out (21 Nov) \u00b7 EU\u2013Indonesia deal "
             "signed (21 Nov) \u00b7 Ronaldo 986 goals (21 Nov) \u00b7 Shenzhen "
             "summit (19 Nov) \u00b7 Palisades arsonist convicted (20 Nov).",
             "DejaVu Sans", 8, INK)
    put_text(ctx, 12, 1014,
             "Sources: Reuters \u00b7 AP \u00b7 AFP \u00b7 BBC \u00b7 Al Jazeera "
             "\u00b7 IPS \u00b7 OilPrice \u00b7 ATP \u00b7 MotoGP \u00b7 Dawn "
             "\u00b7 IQAir \u00b7 KCNA \u00b7 Sky Sports",
             "DejaVu Sans", 8, GREY)
    put_text(ctx, 1012, 1014, "quick-lynx-56 \u00b7 make.fun",
             "DejaVu Sans", 8, GREY, align="right")


def render_page():
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, PAGE_W, PAGE_H)
    ctx = cairo.Context(surf)
    ctx.set_source_rgb(*CREAM)
    ctx.paint()
    draw_masthead(ctx)
    draw_date_block(ctx)
    draw_stat_strip(ctx)
    draw_region_bar(ctx)
    draw_hero(ctx)
    panel_cop31(ctx)
    panel_libya(ctx)
    panel_kyiv(ctx)
    panel_mercury(ctx)
    panel_bursa(ctx)
    panel_pbb(ctx)
    draw_bottom_band(ctx)
    draw_date_check_footer(ctx)
    surf.write_to_png("entry.png")
    print("wrote entry.png")


if __name__ == "__main__":
    render_page()
