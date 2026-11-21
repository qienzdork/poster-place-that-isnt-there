#!/usr/bin/env python3
"""AURELLE - The Floating Isles.

A vintage sunset travel poster for an invented archipelago drifting above
a sea of clouds. Pure Pillow, stdlib only, no network, seeded deterministic.
Writes /output/entry.png (1024x1024 PNG).
"""

import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W = 1024
H = 1024
OUT = "/output/entry.png"
SEED = 20261121

# ---- palette -------------------------------------------------------------
SKY_STOPS = [
    (0.00, (36, 26, 78)),     # deep dusk plum
    (0.32, (107, 47, 99)),    # magenta dusk
    (0.58, (198, 90, 74)),    # coral horizon
    (0.80, (240, 138, 60)),   # sunset orange
    (1.00, (247, 185, 92)),   # low gold
]
SUN_CORE = (255, 217, 122)
SUN_RIM = (244, 164, 66)
ROCK_DARK = (74, 52, 92)
ROCK_MID = (108, 74, 112)
ROCK_LITE = (150, 104, 122)
PINE = (38, 74, 66)
PINE_LITE = (58, 102, 82)
LIGHTHOUSE = (246, 236, 214)
LIGHTHOUSE_RED = (196, 74, 60)
AIRSHIP = (224, 120, 86)
AIRSHIP_DARK = (178, 84, 62)
CLOUD_CREAM = (247, 232, 208)
CLOUD_PINK = (244, 205, 180)
CLOUD_LILAC = (214, 178, 205)
BAND = (22, 35, 63)
CREAM = (246, 231, 200)
GOLD = (232, 182, 76)

FONT_SERIF_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
FONT_SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def sky_color(t):
    for i in range(len(SKY_STOPS) - 1):
        t0, c0 = SKY_STOPS[i]
        t1, c1 = SKY_STOPS[i + 1]
        if t0 <= t <= t1:
            return lerp(c0, c1, (t - t0) / (t1 - t0))
    return SKY_STOPS[-1][1]


def draw_sky(img):
    d = ImageDraw.Draw(img)
    horizon = 790
    for y in range(horizon):
        d.line([(0, y), (W, y)], fill=sky_color(y / horizon))
    return d


def draw_stars(d, rng):
    for _ in range(90):
        x = rng.randint(0, W)
        y = rng.randint(0, 300)
        r = rng.choice([1, 1, 1, 2])
        a = rng.randint(90, 220)
        d.ellipse([x - r, y - r, x + r, y + r],
                  fill=(255, 240, 210), outline=None)
    # faint 4-point sparkles
    for _ in range(8):
        x = rng.randint(40, W - 40)
        y = rng.randint(20, 240)
        s = rng.randint(5, 9)
        d.line([(x - s, y), (x + s, y)], fill=(255, 244, 220), width=1)
        d.line([(x, y - s), (x, y + s)], fill=(255, 244, 220), width=1)


def draw_sun(img):
    """Low golden sun sitting in the gap between the two islands."""
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    cx, cy, r = 600, 448, 66
    for i in range(46, 0, -1):
        rr = r + i * 4
        alpha = int(150 * (1 - i / 46) ** 2)
        gd.ellipse([cx - rr, cy - rr, cx + rr, cy + rr],
                   fill=(255, 190, 90, alpha))
    glow = glow.filter(ImageFilter.GaussianBlur(6))
    img.alpha_composite(glow)
    d = ImageDraw.Draw(img)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=SUN_CORE)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=SUN_RIM, width=3)
    # subtle horizontal haze bands across the sun
    for dy, alpha in ((-18, 60), (4, 45), (26, 55)):
        d.line([(cx - r + 6, cy + dy), (cx + r - 6, cy + dy)],
               fill=(244, 164, 66), width=5)


def draw_distant_islets(d):
    """One hazy far islet floating in the sun gap, below the sun."""
    d.polygon([(572, 656), (606, 626), (640, 642), (662, 656)],
              fill=(158, 96, 130))
    d.polygon([(572, 656), (662, 656), (662, 664), (572, 664)],
              fill=(148, 88, 122))
    # tiny pine on the far islet
    d.polygon([(606, 620), (601, 630), (611, 630)], fill=(120, 76, 110))


def rock_mask(points):
    """Alpha mask of an island polygon, for clipping strata lines."""
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).polygon(points, fill=255)
    return m


def draw_strata(base, points, rng, base_color, line_color):
    """Rock strata lines clipped to the island's true edges."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    mask = rock_mask(points)
    min_y = min(p[1] for p in points)
    max_y = max(p[1] for p in points)
    y = min_y + 26
    while y < max_y - 8:
        pts = []
        x = min(p[0] for p in points) - 20
        x_max = max(p[0] for p in points) + 20
        while x < x_max:
            pts.append((x, y + rng.randint(-6, 6)))
            x += rng.randint(28, 60)
        ld.line(pts, fill=line_color + (150,), width=3, joint="curve")
        y += rng.randint(30, 46)
    layer.putalpha(Image.composite(layer.split()[3], Image.new("L", (W, H), 0), mask))
    base.alpha_composite(layer)


def draw_lighthouse(d, bx, by):
    """Cream lighthouse with red bands on the main island's crest."""
    # tower
    d.polygon([(bx - 16, by), (bx - 11, by - 118), (bx + 11, by - 118),
               (bx + 16, by)], fill=LIGHTHOUSE)
    d.polygon([(bx - 15, by - 34), (bx - 13, by - 58), (bx + 13, by - 58),
               (bx + 15, by - 34)], fill=LIGHTHOUSE_RED)
    d.polygon([(bx - 12, by - 82), (bx - 11, by - 100), (bx + 11, by - 100),
               (bx + 12, by - 82)], fill=LIGHTHOUSE_RED)
    # gallery + lamp room
    d.rectangle([bx - 15, by - 128, bx + 15, by - 118], fill=(52, 44, 74))
    d.rectangle([bx - 9, by - 146, bx + 9, by - 128], fill=(255, 214, 120))
    d.polygon([(bx - 13, by - 146), (bx, by - 158), (bx + 13, by - 146)],
              fill=LIGHTHOUSE_RED)
    d.line([(bx - 9, by - 137), (bx + 9, by - 137)], fill=(120, 80, 40), width=2)
    # light beam sweeping right toward the sun gap
    beam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(beam)
    bd.polygon([(bx + 8, by - 140), (bx + 8, by - 130),
                (bx + 240, by - 96), (bx + 240, by - 168)],
               fill=(255, 226, 150, 105))
    beam = beam.filter(ImageFilter.GaussianBlur(4))
    return beam


def draw_pine(d, bx, by, s, color=PINE):
    d.polygon([(bx, by - s), (bx - s * 0.55, by), (bx + s * 0.55, by)],
              fill=color)
    d.polygon([(bx, by - s * 1.7), (bx - s * 0.42, by - s * 0.55),
               (bx + s * 0.42, by - s * 0.55)], fill=color)
    d.rectangle([bx - 2, by, bx + 2, by + 7], fill=(60, 44, 40))


def draw_main_island(img, d, rng):
    """Lighthouse island, left of the sun gap."""
    pts = [(48, 800), (58, 640), (96, 540), (150, 478), (222, 428),
           (300, 402), (372, 420), (448, 452), (512, 500), (548, 560),
           (536, 700), (520, 800)]
    d.polygon(pts, fill=ROCK_MID)
    # lit top edge
    d.line(pts[2:9], fill=ROCK_LITE, width=4, joint="curve")
    # shadowed underside
    d.polygon([(48, 800), (520, 800), (536, 700), (548, 560),
               (520, 640), (300, 700), (120, 660)], fill=ROCK_DARK)
    draw_strata(img, pts, rng, ROCK_MID, (60, 40, 76))
    # grassy crest
    d.polygon([(222, 428), (300, 402), (372, 420), (352, 436),
               (300, 424), (248, 440)], fill=(72, 110, 78))
    d.polygon([(150, 478), (222, 428), (248, 440), (176, 488)],
              fill=(66, 102, 74))
    beam = draw_lighthouse(d, 300, 408)
    img.alpha_composite(beam)
    # a few pines on the crest
    for bx, by, s in ((238, 432, 26), (356, 426, 30), (398, 446, 22)):
        draw_pine(d, bx, by, s)
    return pts


def draw_second_island(img, d, rng):
    """Pine-topped isle, right of the sun gap."""
    pts = [(664, 800), (676, 660), (700, 560), (752, 500), (830, 470),
           (912, 486), (962, 540), (984, 640), (972, 800)]
    d.polygon(pts, fill=ROCK_MID)
    d.line(pts[2:8], fill=ROCK_LITE, width=4, joint="curve")
    d.polygon([(664, 800), (972, 800), (984, 640), (940, 700),
               (800, 724), (700, 680)], fill=ROCK_DARK)
    draw_strata(img, pts, rng, ROCK_MID, (60, 40, 76))
    # pine forest along the ridge
    ridge = [(752, 500), (800, 482), (860, 472), (912, 486)]
    for i, (px, py) in enumerate(ridge):
        draw_pine(d, px, py, 30 + (i % 2) * 8,
                  PINE_LITE if i % 2 else PINE)
    for bx, by, s in ((780, 490, 22), (838, 476, 26), (884, 480, 20),
                      (928, 496, 24)):
        draw_pine(d, bx, by, s, PINE if (bx // 10) % 2 else PINE_LITE)
    return pts


def draw_waterfall(d, x_top, y_top, x_bot, y_bot, w_top=10, w_bot=22):
    """A waterfall spilling off an island edge into the cloud sea."""
    d.polygon([(x_top - w_top // 2, y_top), (x_top + w_top // 2, y_top),
               (x_bot + w_bot // 2, y_bot), (x_bot - w_bot // 2, y_bot)],
              fill=(206, 232, 238))
    d.line([(x_top, y_top), (x_bot, y_bot)], fill=(255, 255, 255), width=3)
    d.line([(x_top - w_top // 3, y_top), (x_bot - w_bot // 3, y_bot)],
           fill=(255, 255, 255), width=2)
    # mist puff where it meets the clouds
    for dx, r in ((-14, 12), (0, 16), (14, 11)):
        d.ellipse([x_bot + dx - r, y_bot - r // 2,
                   x_bot + dx + r, y_bot + r // 2],
                  fill=(240, 244, 244))


def draw_airship(d):
    """Coral airship drifting high over the right isle."""
    cx, cy = 800, 268
    # envelope
    d.ellipse([cx - 118, cy - 40, cx + 118, cy + 40], fill=AIRSHIP)
    d.ellipse([cx - 118, cy - 40, cx + 118, cy + 40], outline=AIRSHIP_DARK,
              width=3)
    d.arc([cx - 118, cy - 40, cx + 118, cy + 40], start=200, end=340,
          fill=(255, 190, 150), width=6)
    # tail fins
    d.polygon([(cx + 96, cy - 18), (cx + 138, cy - 52), (cx + 118, cy - 6)],
              fill=AIRSHIP_DARK)
    d.polygon([(cx + 96, cy + 18), (cx + 138, cy + 52), (cx + 118, cy + 6)],
              fill=AIRSHIP_DARK)
    # gondola + rigging
    d.line([(cx - 40, cy + 34), (cx - 30, cy + 62)], fill=(90, 60, 60),
           width=2)
    d.line([(cx + 40, cy + 34), (cx + 30, cy + 62)], fill=(90, 60, 60),
           width=2)
    d.rounded_rectangle([cx - 46, cy + 60, cx + 46, cy + 86], radius=8,
                        fill=(74, 52, 70))
    for wx in (-30, -10, 10, 30):
        d.rectangle([cx + wx - 5, cy + 68, cx + wx + 5, cy + 78],
                    fill=(255, 214, 120))
    # tiny pennant
    d.line([(cx - 118, cy - 40), (cx - 118, cy - 62)], fill=(90, 60, 60),
           width=2)
    d.polygon([(cx - 118, cy - 62), (cx - 96, cy - 56), (cx - 118, cy - 50)],
              fill=GOLD)


def draw_birds(d, rng):
    for _ in range(9):
        x = rng.randint(80, 940)
        y = rng.randint(180, 380)
        s = rng.randint(6, 11)
        d.arc([x - s, y - s // 2, x, y + s // 2], start=200, end=340,
              fill=(52, 40, 70), width=2)
        d.arc([x, y - s // 2, x + s, y + s // 2], start=200, end=340,
              fill=(52, 40, 70), width=2)


def draw_cloud_sea(img, d, rng):
    """Sea of clouds with a wavy puff top, filling the lower scene."""
    # base mass
    for y in range(724, 800):
        t = (y - 724) / 76
        d.line([(0, y), (W, y)], fill=lerp(CLOUD_CREAM, CLOUD_PINK, t))
    # wavy puff top: overlapping circles along the horizon of the sea
    x = -30
    while x < W + 40:
        r = rng.randint(34, 62)
        cy = 724 + rng.randint(-16, 10)
        col = rng.choice([CLOUD_CREAM, CLOUD_CREAM, CLOUD_PINK,
                          CLOUD_LILAC])
        d.ellipse([x - r, cy - r, x + r, cy + r], fill=col)
        x += int(r * rng.uniform(1.1, 1.5))
    # second, smaller puff row for texture
    x = -10
    while x < W + 40:
        r = rng.randint(18, 34)
        cy = 742 + rng.randint(-8, 12)
        col = rng.choice([CLOUD_CREAM, CLOUD_PINK, (250, 240, 222)])
        d.ellipse([x - r, cy - r, x + r, cy + r], fill=col)
        x += int(r * rng.uniform(1.2, 1.7))
    # soft shadows between puffs
    for _ in range(26):
        x = rng.randint(0, W)
        y = rng.randint(730, 790)
        rx = rng.randint(24, 60)
        ry = rng.randint(5, 10)
        d.ellipse([x - rx, y - ry, x + rx, y + ry],
                  fill=(226, 186, 196))
    # a couple of lone wisps drifting above the sea
    for wx, wy, s in ((150, 648, 40), (880, 660, 34), (520, 668, 28)):
        d.ellipse([wx - s, wy - s // 3, wx + s, wy + s // 3],
                  fill=(248, 236, 216))
        d.ellipse([wx - s // 2, wy - s // 2, wx + s // 2, wy],
                  fill=(250, 240, 224))


def draw_tracked(d, cx, y, text, font, fill, tracking):
    """Draw text centred on cx with letter tracking, return its width."""
    widths = [d.textlength(ch, font=font) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = cx - total / 2
    for ch, w in zip(text, widths):
        d.text((x, y), ch, font=font, fill=fill)
        x += w + tracking
    return total


def draw_title_band(d):
    """Bottom band: name, tagline, footer - classic travel-poster type."""
    d.rectangle([0, 800, W, H], fill=BAND)
    d.line([(48, 818), (W - 48, 818)], fill=GOLD, width=3)
    d.line([(48, 1004), (W - 48, 1004)], fill=GOLD, width=2)
    title_font = ImageFont.truetype(FONT_SERIF_BOLD, 102)
    draw_tracked(d, W // 2, 828, "AURELLE", title_font, CREAM, 16)
    tag_font = ImageFont.truetype(FONT_SANS, 22)
    draw_tracked(d, W // 2, 948, "WHERE THE ISLANDS DRIFT ABOVE THE CLOUDS",
                 tag_font, GOLD, 5)
    foot_font = ImageFont.truetype(FONT_SANS, 17)
    draw_tracked(d, W // 2, 978, "AIRSHIPS DAILY  ·  SUNSET SEASON  ·  19° ALL YEAR",
                 foot_font, (214, 205, 190), 3)


def build():
    rng = random.Random(SEED)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    d = draw_sky(img)
    draw_stars(d, rng)
    draw_sun(img)
    d = ImageDraw.Draw(img)
    draw_distant_islets(d)
    draw_airship(d)
    draw_birds(d, rng)
    draw_main_island(img, d, rng)
    draw_second_island(img, d, rng)
    # waterfalls spilling off the island edges into the clouds
    draw_waterfall(d, 120, 560, 96, 716)
    draw_waterfall(d, 528, 540, 552, 716)
    draw_waterfall(d, 700, 590, 684, 716)
    draw_waterfall(d, 952, 580, 972, 716)
    draw_cloud_sea(img, d, rng)
    draw_title_band(d)
    return img.convert("RGB")


def main():
    os.makedirs("/output", exist_ok=True)
    img = build()
    img.save(OUT, format="PNG", optimize=True)
    size = os.path.getsize(OUT)
    print(f"wrote {OUT}: {img.size[0]}x{img.size[1]}, {size} bytes")
    assert img.size == (1024, 1024), "wrong dimensions"
    assert size <= 1_048_576, "over 1 MiB"


if __name__ == "__main__":
    main()
