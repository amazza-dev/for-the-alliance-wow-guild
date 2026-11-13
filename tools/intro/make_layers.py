"""Cut the guild banner into the layers used by the animated intro, plus the web-sized banners.

Usage:
    python3 tools/intro/make_layers.py            # writes into public/

Requires Pillow and numpy. Coordinates below are in a 1024 x 1024 space over the square banner.
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_SQUARE = os.path.join(ROOT, "assets-src", "banner-square-source.jpg")
SRC_WIDE = os.path.join(ROOT, "assets-src", "banner-wide-source.jpg")
OUT = os.path.join(ROOT, "public")

S = 1200
k = S / 1024
src = Image.open(SRC_SQUARE).convert("RGB").resize((S, S), Image.LANCZOS)


def P(pts):
    return [(x * k, y * k) for x, y in pts]


def mask(polys=(), feather=6):
    m = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(m)
    for p in polys:
        d.polygon(P(p), fill=255)
    return m.filter(ImageFilter.GaussianBlur(feather))


def save_layer(name, m, image=None):
    im = (image or src).copy()
    im.putalpha(m)
    bb = m.point(lambda v: 255 if v > 2 else 0).getbbox()
    im.crop(bb).save(os.path.join(OUT, f"{name}.webp"), quality=82, method=6)
    l, t, r, b = [round(v / S * 100, 3) for v in bb]
    print(f"{name:12s} left {l}%  top {t}%  width {round(r - l, 3)}%  height {round(b - t, 3)}%")


# The lion's mane outline (everything inside moves with the lion)
MANE = [(460, 193), (553, 193), (675, 226), (715, 263), (758, 365), (773, 455), (753, 572), (715, 682),
        (670, 740), (512, 745), (354, 740), (319, 682), (284, 572), (262, 455), (275, 365), (319, 263), (371, 226)]

layers = {
    "corners": mask([[(0, 0), (250, 0), (250, 58), (62, 58), (62, 235), (0, 235)],
                     [(1024, 0), (774, 0), (774, 58), (962, 58), (962, 235), (1024, 235)],
                     [(0, 1024), (250, 1024), (250, 962), (62, 962), (62, 800), (0, 800)],
                     [(1024, 1024), (774, 1024), (774, 962), (962, 962), (962, 800), (1024, 800)]]),
    "w_for": mask([[(62, 62), (268, 62), (268, 200), (62, 200)]], 3),
    "w_the": mask([[(268, 62), (476, 62), (476, 200), (268, 200)]], 3),
    "w_alliance": mask([[(476, 62), (965, 62), (965, 200), (476, 200)]], 3),
    "ribbon": mask([[(30, 705), (200, 700), (380, 722), (512, 728), (645, 722), (830, 700), (995, 705), (995, 890),
                     (650, 882), (650, 1000), (380, 1000), (380, 882), (30, 890)]], 4),
    "weap_l": mask([[(0, 230), (205, 230), (205, 560), (310, 705), (0, 705)]], 5),
    "weap_r": mask([[(820, 205), (1024, 205), (1024, 705), (735, 705), (820, 560)]], 5),
}
for name, m in layers.items():
    save_layer(name, m)

# Lion: cropped to the mane outline plus padding (the page clips it with the same polygon)
lion_m = mask([MANE], 7)
pad = 14
xs, ys = [x for x, _ in MANE], [y for _, y in MANE]
box = tuple(int(v * k) for v in (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad))
lion = src.copy()
lion.putalpha(lion_m)
lion.crop(box).save(os.path.join(OUT, "lion.webp"), quality=84, method=6)
print("lion         cropped to mane box", box)

# Shield frame with the mane removed
shield = mask([[(430, 12), (600, 12), (590, 60), (440, 60)],
               [(205, 200), (820, 200), (905, 200), (905, 300), (820, 300), (820, 560), (735, 660), (512, 690),
                (289, 660), (205, 560), (205, 300), (120, 300), (120, 200)]], 4)
grow = mask([MANE], 3).filter(ImageFilter.MaxFilter(9))
save_layer("shield", ImageChops.subtract(shield, grow))

# Painted stand-in shield interior, shown until the lion rises over it
region = ImageChops.multiply(mask([MANE], 3).filter(ImageFilter.MaxFilter(15)),
                             mask([[(205, 200), (820, 200), (820, 560), (512, 735), (205, 560)]], 2))
y = np.linspace(0, 1, S)[:, None]
top, bot = np.array([52, 90, 178]), np.array([24, 48, 112])
arr = np.zeros((S, S, 3))
for c in range(3):
    arr[:, :, c] = top[c] * (1 - y) + bot[c] * y
n = np.random.default_rng(3).normal(0, 1, (S // 6, S // 6))
tex = np.array(Image.fromarray(((n - n.min()) / (n.max() - n.min()) * 255).astype("uint8")).resize((S, S), Image.BICUBIC)) / 255 - .5
fill = Image.fromarray(np.clip(arr * (1 + .18 * tex[:, :, None]), 0, 255).astype("uint8"), "RGB")
d = ImageDraw.Draw(fill)


def band(pts, w_silver, w_gold, off):
    d.line(P(pts), fill=(176, 184, 198), width=int(w_silver * k), joint="curve")
    d.line(P(pts), fill=(138, 146, 162), width=int(w_silver * k * .35), joint="curve")
    d.line(P([(x, yy + off) for x, yy in pts]), fill=(226, 174, 58), width=int(w_gold * k), joint="curve")


band([(230, 221), (795, 221)], 42, 7, 24)
band([(258, 585), (512, 722), (766, 585)], 36, 7, -22)
for x in range(300, 760, 70):
    d.ellipse(P([(x - 5, 216), (x + 5, 226)]), fill=(214, 170, 80))
save_layer("shield_fill", region, fill.filter(ImageFilter.GaussianBlur(.8)))

# Finished banner for the end of the intro, and the site banners
src.save(os.path.join(OUT, "full.jpg"), quality=84, optimize=True, progressive=True)
wide = Image.open(SRC_WIDE).convert("RGB")
wide.resize((1920, int(1920 * wide.size[1] / wide.size[0])), Image.LANCZOS).save(
    os.path.join(OUT, "banner-wide.jpg"), quality=82, optimize=True, progressive=True)
sq = Image.open(SRC_SQUARE).convert("RGB")
sq.resize((900, 900), Image.LANCZOS).save(os.path.join(OUT, "banner-square.jpg"), quality=82, optimize=True, progressive=True)
sq.crop((560, 330, 1370, 1260)).resize((160, 184), Image.LANCZOS).save(os.path.join(OUT, "crest.jpg"), quality=85)
print("done")
