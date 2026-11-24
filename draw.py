#!/usr/bin/env python3
"""Draw entry.png: a one-page newspaper front page summing up 23 Nov 2026.

Monday 23 November 2026. 35 stories across 7 regions (EUROPE 8,
AMERICAS 7, ASIA 6, MIDDLE EAST 5, WORLD 3, AFRICA 3, OCEANIA 3),
3 hero + 10 secondary original flat illustrations, a THE DAY IN UTC
timeline strip, a numbers strip of six separate cells where every
number tells a complete mini-story, verification tags on every
illustrated story, a pinned dotted world map whose legend carries the
region counts, a 22-story numbered list, a DATE CHECK box with dated
exclusions plus a "Not yet" tail, and a sources footer. Counts
reconcile: 3 + 10 + 22 = 35; region counts sum to 35; 13 fields.

Every story was verified as having happened, or first been reported,
on Monday 23 November 2026, from Reuters, AP, AFP, BBC, Al Jazeera,
The Hindu, ANI, IANS, ESPNcricinfo, CNN and allAfrica. Disputed
figures are shown as claims, never as fact. Near-misses are named in
the DATE CHECK box, not shown as news. Drawn with Pillow only; no
photos, no copied art.
"""
from PIL import Image, ImageDraw, ImageFont
import math
import os

W = H = 1024
PAPER = (248, 245, 238)
INK = (20, 20, 20)
MUTED = (90, 86, 78)
RED = (166, 27, 27)
NAVY = (18, 34, 64)
RULE = (180, 174, 162)
CARD = (255, 255, 255)
MAPDOT = (158, 168, 180)
GREEN = (46, 134, 74)

SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def F(path, size):
    return ImageFont.truetype(path, size)


def wrap_text(d, text, fnt, width):
    """Greedy word wrap; returns list of lines that fit width."""
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if d.textlength(trial, font=fnt) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def put_text(d, xy, text, fnt, width, fill, leading=2, limit=None):
    """Draw wrapped text; returns y after last line. Warns on overflow."""
    x, y = xy
    lines = wrap_text(d, text, fnt, width)
    if limit is not None and len(lines) > limit:
        print(f"OVERFLOW: {text[:48]!r} -> {len(lines)} lines (max {limit})")
        lines = lines[:limit]
    for line in lines:
        d.text((x, y), line, font=fnt, fill=fill)
        y += fnt.size + leading
    return y


# ---------- small flat-drawing primitives ----------
def sky(d, box, top, mid, bot):
    x0, y0, x1, y1 = box
    for i, c in enumerate((top, mid, bot)):
        d.rectangle([x0, y0 + (y1 - y0) * i // 3,
                     x1, y0 + (y1 - y0) * (i + 1) // 3], fill=c)


def disc(d, cx, cy, r, color):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)


def puff(d, x, y, s, color):
    d.ellipse([x, y, x + s, y + s * 0.55], fill=color)
    d.ellipse([x + s * 0.5, y - s * 0.25, x + s * 1.5, y + s * 0.4], fill=color)
    d.ellipse([x + s, y, x + s * 2, y + s * 0.55], fill=color)


def block(d, x, y, w, h, color, lit=(255, 214, 90)):
    d.rectangle([x, y, x + w, y + h], fill=color)
    for wy in range(y + 7, y + h - 7, 13):
        for wx in range(x + 5, x + w - 7, 13):
            d.rectangle([wx, wy, wx + 5, wy + 6], fill=lit)


def spark(d, cx, cy, r, color):
    d.polygon([(cx, cy - r), (cx + r * 0.28, cy - r * 0.28), (cx + r, cy),
               (cx + r * 0.28, cy + r * 0.28), (cx, cy + r),
               (cx - r * 0.28, cy + r * 0.28), (cx - r, cy),
               (cx - r * 0.28, cy - r * 0.28)], fill=color)


def fire(d, x, y, s):
    """Flame with base at (x, y), height s."""
    d.polygon([(x - s * 0.4, y), (x, y - s), (x + s * 0.4, y)], fill=(255, 140, 40))
    d.polygon([(x - s * 0.2, y), (x, y - s * 0.55), (x + s * 0.2, y)],
              fill=(255, 220, 120))


def figure(d, x, y, s, skin=(232, 190, 160), shirt=(30, 90, 160)):
    """Small standing person: head, torso, legs."""
    d.ellipse([x - s * 0.28, y, x + s * 0.28, y + s * 0.55], fill=skin)
    d.rectangle([x - s * 0.3, y + s * 0.55, x + s * 0.3, y + s * 1.15], fill=shirt)
    d.rectangle([x - s * 0.22, y + s * 1.15, x - s * 0.02, y + s * 1.7],
                fill=(30, 30, 34))
    d.rectangle([x + s * 0.02, y + s * 1.15, x + s * 0.22, y + s * 1.7],
                fill=(30, 30, 34))


def banner(d, box, text):
    """Red key-number banner across the bottom of a hero picture."""
    x0, y0, x1, y1 = box
    d.rectangle([x0, y1 - 18, x1, y1], fill=RED)
    f = F(SANS_B, 13)
    d.text((x0 + (x1 - x0 - d.textlength(text, font=f)) / 2, y1 - 16),
           text, font=f, fill=(255, 255, 255))


# ---------- hero pictures (310 x 124) ----------
def pic_dymer(d, box):
    """Hero 1: night in Dymer — a block with its middle stairwell gone,
    rubble, a rescue ladder, a searchlight beam, a survivor carried out."""
    x0, y0, x1, y1 = box
    sky(d, box, (14, 22, 46), (24, 36, 68), (36, 52, 92))
    spark(d, x0 + 22, y0 + 10, 4, (255, 255, 255))
    spark(d, x0 + 290, y0 + 14, 3, (255, 255, 255))
    # five-storey block, middle stairwell collapsed
    for bx, bw in [(x0 + 10, 58), (x0 + 150, 58)]:
        block(d, bx, y1 - 66, bw, 66, (10, 16, 32), lit=(255, 190, 90))
    # jagged rubble where the stairwell was
    d.polygon([(x0 + 72, y1 - 18), (x0 + 84, y1 - 58), (x0 + 98, y1 - 64),
               (x0 + 114, y1 - 46), (x0 + 128, y1 - 40), (x0 + 146, y1 - 18)],
              fill=(64, 62, 58))
    fire(d, x0 + 106, y1 - 58, 20)
    puff(d, x0 + 92, y0 + 4, 16, (118, 126, 146))
    # searchlight beam from the right
    d.polygon([(x1 - 8, y1 - 18), (x0 + 210, y0 + 8), (x0 + 222, y0 + 8),
               (x1 - 2, y1 - 18)], fill=(255, 236, 160))
    # rescue ladder leaning on the left block
    d.line([x0 + 76, y1 - 18, x0 + 96, y1 - 66], fill=(220, 200, 90), width=3)
    for k in range(1, 5):
        t = k / 5
        lx = x0 + 76 + 20 * t
        ly = y1 - 18 - 48 * t
        d.line([lx - 4, ly, lx + 4, ly], fill=(220, 200, 90), width=2)
    figure(d, x0 + 92, y1 - 70, 14, shirt=(200, 60, 40))
    # stretcher team at the foot of the rubble
    figure(d, x0 + 170, y1 - 46, 13, shirt=(220, 180, 60))
    figure(d, x0 + 196, y1 - 46, 13, shirt=(60, 140, 90))
    d.rectangle([x0 + 178, y1 - 30, x0 + 196, y1 - 26], fill=(200, 200, 196))
    d.rectangle([x0, y1 - 18, x1, y1], fill=(12, 18, 34))
    banner(d, box, "15 DEAD IN KYIV REGION")


def pic_merkury(d, box):
    """Hero 2: night at Benghazi — a corvette listing and burning,
    three sea drones closing in, a helicopter in the smoke."""
    x0, y0, x1, y1 = box
    sky(d, box, (12, 18, 40), (20, 30, 58), (30, 44, 78))
    spark(d, x0 + 24, y0 + 10, 4, (255, 255, 255))
    spark(d, x0 + 288, y0 + 12, 3, (255, 255, 255))
    disc(d, x0 + 262, y0 + 16, 10, (240, 230, 200))
    # sea
    d.rectangle([x0, y1 - 34, x1, y1], fill=(24, 58, 92))
    for wx in range(x0 + 8, x1 - 8, 26):
        d.line([wx, y1 - 26, wx + 12, y1 - 26], fill=(90, 140, 180), width=1)
    # listing corvette, bow down, smoke and fire amidships
    hx, hy = x0 + 92, y1 - 52
    d.polygon([(hx, hy + 22), (hx + 118, hy + 22), (hx + 128, hy + 8),
               (hx + 6, hy + 8)], fill=(28, 28, 32))
    d.rectangle([hx + 30, hy - 6, hx + 52, hy + 8], fill=(52, 52, 56))
    d.rectangle([hx + 60, hy - 2, hx + 96, hy + 8], fill=(40, 40, 44))
    d.line([hx + 40, hy - 6, hx + 40, hy - 20], fill=(120, 120, 124), width=2)
    fire(d, hx + 74, hy - 2, 26)
    puff(d, hx + 58, y0 + 2, 18, (110, 110, 116))
    puff(d, hx + 96, y0 + 12, 12, (130, 130, 134))
    # helicopter silhouette above the smoke
    cx, cy = x0 + 168, y0 + 22
    d.ellipse([cx - 10, cy - 4, cx + 10, cy + 4], fill=(20, 20, 22))
    d.line([cx - 22, cy - 4, cx + 22, cy - 4], fill=(20, 20, 22), width=2)
    d.line([cx + 10, cy, cx + 20, cy + 6], fill=(20, 20, 22), width=2)
    # three sea drones closing in, wakes behind them
    for dx in (x0 + 30, x0 + 62, x0 + 236):
        d.polygon([(dx, y1 - 26), (dx + 18, y1 - 26), (dx + 22, y1 - 20),
                   (dx + 4, y1 - 20)], fill=(200, 200, 204))
        d.line([dx - 12, y1 - 22, dx, y1 - 22], fill=(220, 235, 242), width=2)
    d.rectangle([x0, y1 - 18, x1, y1], fill=(16, 32, 56))
    banner(d, box, "7 SEA DRONES SANK HER")


def pic_nvidia(d, box):
    """Hero 3: the market roars back — four rising bars with values."""
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=(244, 240, 228))
    d.rectangle([x0, y1 - 18, x1, y1], fill=(232, 224, 204))
    rows = [("NVIDIA", "+31.5%", 80, (46, 134, 74)),
            ("NASDAQ", "+6.5%", 48, (36, 84, 160)),
            ("S&P 500", "+4.7%", 40, (36, 84, 160)),
            ("DOW", "+3.0%", 34, (36, 84, 160))]
    for i, (name, val, h, col) in enumerate(rows):
        bx = x0 + 18 + i * 74
        d.rectangle([bx, y1 - 24 - h, bx + 46, y1 - 24], fill=col)
        f1, f2 = F(SANS_B, 11), F(SANS_B, 12)
        d.text((bx + (46 - d.textlength(name, font=f1)) / 2, y1 - 24 - h - 15),
               name, font=f1, fill=INK)
        d.text((bx + (46 - d.textlength(val, font=f2)) / 2, y1 - 24 - h + 4),
               val, font=f2, fill=(255, 255, 255))
    banner(d, box, "NVIDIA +31.5% · BEST DAY SINCE 2003")
# ---------- secondary pictures (185 x 58) ----------
def pic_eu(d, box):
    """4: Brussels — a ring of stars, a bank, a ship crossed out."""
    x0, y0, x1, y1 = box
    sky(d, box, (24, 40, 84), (36, 58, 110), (52, 78, 138))
    cx, cy = x0 + 42, y0 + 26
    for k in range(12):
        a = k * 3.14159 * 2 / 12 - 3.14159 / 2
        sx, sy = cx + 26 * math.cos(a), cy + 20 * math.sin(a)
        spark(d, sx, sy, 3, (255, 214, 90))
    # bank with columns
    bx = x0 + 82
    d.polygon([(bx, y1 - 44), (bx + 26, y1 - 54), (bx + 52, y1 - 44)], fill=(232, 228, 220))
    d.rectangle([bx, y1 - 44, bx + 52, y1 - 16], fill=(232, 228, 220))
    for k in range(4):
        d.rectangle([bx + 6 + k * 12, y1 - 40, bx + 11 + k * 12, y1 - 20],
                    fill=(160, 156, 148))
    # shadow-fleet ship with a red cross
    sx, sy = x0 + 146, y1 - 30
    d.polygon([(sx, sy + 8), (sx + 32, sy + 8), (sx + 36, sy), (sx, sy)],
              fill=(24, 24, 28))
    d.rectangle([sx + 8, sy - 8, sx + 20, sy], fill=(200, 60, 50))
    d.line([sx - 2, sy - 12, sx + 38, sy + 12], fill=RED, width=2)
    d.line([sx - 2, sy + 12, sx + 38, sy - 12], fill=RED, width=2)
    d.rectangle([x0, y1 - 8, x1, y1], fill=(16, 28, 56))


def pic_fifa(d, box):
    """5: Zurich — a pitch, a trophy, a ball, 2031 and 2035 boards."""
    x0, y0, x1, y1 = box
    sky(d, box, (150, 200, 140), (170, 212, 150), (190, 224, 164))
    d.rectangle([x0, y1 - 16, x1, y1], fill=(60, 128, 64))
    d.ellipse([x0 + 60, y1 - 52, x0 + 126, y1 - 14], outline=(255, 255, 255), width=1)
    d.line([x0 + 93, y1 - 52, x0 + 93, y1 - 14], fill=(255, 255, 255), width=1)
    # trophy
    tx, ty = x0 + 122, y0 + 8
    d.polygon([(tx, ty), (tx + 20, ty), (tx + 16, ty + 18), (tx + 4, ty + 18)],
              fill=(255, 214, 90))
    d.rectangle([tx + 7, ty + 18, tx + 13, ty + 26], fill=(255, 214, 90))
    d.rectangle([tx + 2, ty + 26, tx + 18, ty + 30], fill=(255, 214, 90))
    d.ellipse([tx - 4, ty + 2, tx + 2, ty + 10], outline=(255, 214, 90), width=2)
    d.ellipse([tx + 18, ty + 2, tx + 24, ty + 10], outline=(255, 214, 90), width=2)
    # ball
    disc(d, x0 + 162, y1 - 26, 7, (255, 255, 255))
    d.polygon([(x0 + 162, y1 - 30), (x0 + 166, y1 - 26), (x0 + 162, y1 - 22),
               (x0 + 158, y1 - 26)], fill=(30, 30, 30))
    # year boards
    for i, (yr, col) in enumerate([("2031", (36, 84, 160)), ("2035", (178, 44, 44))]):
        bx = x0 + 8 + i * 52
        d.rectangle([bx, y0 + 6, bx + 46, y0 + 22], fill=col)
        f = F(SANS_B, 11)
        d.text((bx + (46 - d.textlength(yr, font=f)) / 2, y0 + 8), yr,
               font=f, fill=(255, 255, 255))
    d.rectangle([x0, y1 - 8, x1, y1], fill=(40, 96, 48))


def pic_sparta(d, box):
    """6: the Sparta II reaches St Petersburg — a cargo ship under tow
    past onion domes, smoke gone, harbour calm."""
    x0, y0, x1, y1 = box
    sky(d, box, (214, 226, 232), (190, 208, 220), (168, 192, 208))
    disc(d, x0 + 20, y0 + 10, 8, (255, 214, 90))
    # onion domes on the shore
    for dx, col in [(x0 + 140, (40, 120, 90)), (x0 + 162, (200, 60, 50)),
                    (x0 + 182, (36, 84, 160))]:
        d.rectangle([dx, y1 - 30, dx + 10, y1 - 8], fill=(120, 110, 96))
        d.pieslice([dx - 2, y1 - 44, dx + 12, y1 - 26], start=180, end=360, fill=col)
        d.rectangle([dx + 4, y1 - 50, dx + 6, y1 - 44], fill=col)
    d.rectangle([x0, y1 - 18, x1, y1], fill=(36, 76, 118))
    # cargo ship, upright again, light smoke
    hx, hy = x0 + 56, y1 - 32
    d.polygon([(hx, hy + 12), (hx + 92, hy + 12), (hx + 100, hy + 2), (hx, hy + 2)],
              fill=(24, 24, 28))
    for i, c in enumerate([(200, 60, 50), (40, 120, 90), (220, 160, 40)]):
        d.rectangle([hx + 10 + i * 22, hy - 8, hx + 28 + i * 22, hy + 2], fill=c)
    puff(d, hx + 40, y0 + 2, 10, (200, 200, 204))
    # tug ahead with a tow line
    tx, ty = x0 + 12, y1 - 28
    d.polygon([(tx, ty + 10), (tx + 30, ty + 10), (tx + 34, ty + 2), (tx, ty + 2)],
              fill=(180, 60, 40))
    d.rectangle([tx + 8, ty - 8, tx + 20, ty + 2], fill=(240, 240, 238))
    d.line([tx + 34, ty + 4, hx, hy + 4], fill=(60, 60, 60), width=1)


def pic_nepal(d, box):
    """7: the Himalayas — snow peaks, a crimson pennant flag, aid boxes."""
    x0, y0, x1, y1 = box
    sky(d, box, (150, 196, 220), (178, 212, 232), (206, 226, 240))
    disc(d, x0 + 22, y0 + 10, 8, (255, 214, 90))
    # snow peaks
    d.polygon([(x0 + 8, y1 - 8), (x0 + 52, y1 - 46), (x0 + 96, y1 - 8)],
              fill=(120, 140, 160))
    d.polygon([(x0 + 52, y1 - 46), (x0 + 62, y1 - 34), (x0 + 42, y1 - 34)],
              fill=(255, 255, 255))
    d.polygon([(x0 + 70, y1 - 8), (x0 + 118, y1 - 52), (x0 + 166, y1 - 8)],
              fill=(96, 118, 140))
    d.polygon([(x0 + 118, y1 - 52), (x0 + 130, y1 - 38), (x0 + 106, y1 - 38)],
              fill=(255, 255, 255))
    # Nepal pennant flag on a pole
    fx, fy = x0 + 156, y0 + 8
    d.line([fx, fy, fx, y1 - 8], fill=(60, 60, 60), width=2)
    d.polygon([(fx + 1, fy), (fx + 24, fy + 7), (fx + 1, fy + 14)], fill=(178, 44, 44))
    d.polygon([(fx + 1, fy + 13), (fx + 18, fy + 19), (fx + 1, fy + 24)],
              fill=(178, 44, 44))
    # aid boxes
    for i, (bx, by) in enumerate([(x0 + 10, y1 - 26), (x0 + 26, y1 - 26),
                                  (x0 + 18, y1 - 40)]):
        d.rectangle([bx, by, bx + 14, by + 12], fill=(190, 150, 90))
        d.line([bx, by + 6, bx + 14, by + 6], fill=(140, 106, 60), width=1)
    d.rectangle([x0, y1 - 8, x1, y1], fill=(90, 110, 130))


def pic_ahmadi(d, box):
    """8: a dark stage — a microphone in a spotlight cone, a red slash
    across a music note: a voice punished for singing."""
    x0, y0, x1, y1 = box
    sky(d, box, (16, 16, 26), (28, 26, 44), (44, 38, 62))
    # spotlight cone
    d.polygon([(x0 + 78, y0), (x0 + 108, y0), (x0 + 138, y1 - 8),
               (x0 + 48, y1 - 8)], fill=(255, 236, 160))
    # stage floor and curtain edge
    d.rectangle([x0, y1 - 12, x1, y1], fill=(60, 20, 24))
    d.rectangle([x0, y0, x0 + 14, y1], fill=(120, 24, 30))
    d.rectangle([x1 - 14, y0, x1, y1], fill=(120, 24, 30))
    # microphone on a stand
    mx, my = x0 + 93, y0 + 16
    d.ellipse([mx - 8, my, mx + 8, my + 14], fill=(220, 220, 224))
    d.line([mx - 8, my + 4, mx + 8, my + 4], fill=(120, 120, 124), width=1)
    d.line([mx - 8, my + 9, mx + 8, my + 9], fill=(120, 120, 124), width=1)
    d.line([mx, my + 14, mx, y1 - 12], fill=(120, 120, 124), width=2)
    d.line([mx - 8, y1 - 12, mx + 8, y1 - 12], fill=(120, 120, 124), width=2)
    # a music note, crossed out in red
    nx, ny = x0 + 150, y0 + 14
    d.ellipse([nx, ny + 8, nx + 8, ny + 14], fill=(255, 255, 255))
    d.line([nx + 7, ny + 8, nx + 7, ny - 4], fill=(255, 255, 255), width=2)
    d.line([nx - 4, ny - 6, nx + 16, ny + 16], fill=RED, width=3)
    d.text((x0 + 20, y1 - 24), "74", font=F(SANS_B, 13), fill=(255, 255, 255))


def pic_china(d, box):
    """9: Beijing — a red flag, a courthouse, a gavel."""
    x0, y0, x1, y1 = box
    sky(d, box, (178, 44, 44), (190, 60, 56), (204, 84, 76))
    # flag with five stars
    fx, fy = x0 + 12, y0 + 6
    d.rectangle([fx, fy, fx + 52, fy + 30], fill=(178, 44, 44),
                outline=(255, 214, 90), width=1)
    spark(d, fx + 12, fy + 9, 5, (255, 214, 90))
    for sx, sy in [(fx + 26, fy + 6), (fx + 32, fy + 12), (fx + 30, fy + 20),
                   (fx + 22, fy + 22)]:
        spark(d, sx, sy, 2, (255, 214, 90))
    # courthouse
    bx = x0 + 84
    d.polygon([(bx, y1 - 40), (bx + 30, y1 - 52), (bx + 60, y1 - 40)],
              fill=(240, 236, 228))
    d.rectangle([bx, y1 - 40, bx + 60, y1 - 12], fill=(240, 236, 228))
    for k in range(4):
        d.rectangle([bx + 7 + k * 14, y1 - 36, bx + 12 + k * 14, y1 - 16],
                    fill=(160, 156, 148))
    # gavel
    gx, gy = x0 + 156, y1 - 30
    d.rectangle([gx, gy - 6, gx + 22, gy + 2], fill=(120, 86, 60))
    d.line([gx + 11, gy + 2, gx + 11, gy + 14], fill=(120, 86, 60), width=3)
    d.rectangle([gx + 2, gy + 14, gx + 20, gy + 18], fill=(90, 66, 44))
    d.rectangle([x0, y1 - 8, x1, y1], fill=(120, 30, 30))


def pic_cikande(d, box):
    """10: Cikande — a three-storey candy plant, flames from the
    windows, smoke, a ladder and a rescuer at the gate."""
    x0, y0, x1, y1 = box
    sky(d, box, (240, 190, 150), (232, 176, 138), (222, 160, 124))
    # three-storey plant
    fx, fy = x0 + 12, y1 - 44
    d.rectangle([fx, fy, fx + 116, y1 - 8], fill=(150, 110, 80))
    d.rectangle([fx, fy - 6, fx + 116, fy], fill=(120, 86, 60))
    for row in range(3):
        for wx in range(fx + 8, fx + 108, 20):
            d.rectangle([wx, fy + 6 + row * 12, wx + 10, fy + 14 + row * 12],
                        fill=(255, 214, 90))
    fire(d, fx + 30, fy, 22)
    fire(d, fx + 84, fy, 18)
    puff(d, fx + 18, y0 + 2, 18, (110, 110, 116))
    puff(d, fx + 66, y0 + 10, 14, (130, 130, 134))
    # ladder and rescuer at the gate
    d.line([x1 - 36, y1 - 8, x1 - 18, y1 - 46], fill=(220, 200, 90), width=3)
    figure(d, x1 - 16, y1 - 48, 13, shirt=(200, 60, 40))
    d.rectangle([x0, y1 - 8, x1, y1], fill=(110, 88, 66))


def pic_binance(d, box):
    """11: Washington — a gold coin, a shield, a gavel: the state moves
    to claw back the stolen crypto."""
    x0, y0, x1, y1 = box
    sky(d, box, (24, 40, 84), (36, 58, 110), (52, 78, 138))
    spark(d, x0 + 20, y0 + 8, 3, (255, 255, 255))
    # gold coin with B
    cx, cy = x0 + 46, y0 + 28
    disc(d, cx, cy, 18, (255, 200, 60))
    d.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], outline=(180, 130, 20), width=2)
    d.text((cx - 6, cy - 9), "B", font=F(SANS_B, 18), fill=(140, 96, 10))
    # shield
    sx, sy = x0 + 108, y0 + 10
    d.polygon([(sx, sy), (sx + 34, sy), (sx + 34, sy + 20), (sx + 17, sy + 34),
               (sx, sy + 20)], fill=(220, 220, 224))
    d.line([sx + 10, sy + 17, sx + 15, sy + 23, sx + 25, sy + 9], fill=GREEN, width=2)
    # gavel
    gx, gy = x0 + 152, y1 - 30
    d.rectangle([gx, gy - 6, gx + 22, gy + 2], fill=(200, 170, 120))
    d.line([gx + 11, gy + 2, gx + 11, gy + 14], fill=(200, 170, 120), width=3)
    d.rectangle([gx + 2, gy + 14, gx + 20, gy + 18], fill=(160, 130, 90))
    d.text((x0 + 84, y1 - 22), "$1bn", font=F(SANS_B, 13), fill=(255, 255, 255))
    d.rectangle([x0, y1 - 8, x1, y1], fill=(16, 28, 56))


def pic_gaza(d, box):
    """12: Jabalia — a water well, a blue UN flag, smoke over the camp."""
    x0, y0, x1, y1 = box
    sky(d, box, (232, 196, 150), (224, 182, 138), (212, 166, 124))
    disc(d, x0 + 20, y0 + 10, 8, (255, 214, 90))
    # low camp houses
    for bx, bw, bh in [(x0 + 8, 34, 22), (x0 + 46, 30, 28), (x0 + 138, 36, 20)]:
        d.rectangle([bx, y1 - bh, bx + bw, y1 - 8], fill=(196, 178, 148))
        d.rectangle([bx + 4, y1 - bh - 5, bx + bw - 4, y1 - bh],
                    fill=(160, 140, 110))
    # water well with a wheel
    wx, wy = x0 + 96, y1 - 34
    d.rectangle([wx - 14, wy, wx + 14, y1 - 8], fill=(150, 130, 104))
    d.rectangle([wx - 18, wy - 4, wx + 18, wy], fill=(120, 100, 78))
    d.line([wx - 16, wy - 14, wx + 16, wy - 14], fill=(90, 70, 52), width=2)
    d.line([wx - 12, wy - 14, wx - 12, wy - 4], fill=(90, 70, 52), width=2)
    d.line([wx + 12, wy - 14, wx + 12, wy - 4], fill=(90, 70, 52), width=2)
    disc(d, wx, wy - 14, 5, (120, 100, 78))
    # smoke and a burst where the strike fell
    puff(d, wx - 6, y0 + 2, 14, (110, 110, 116))
    spark(d, wx + 22, y0 + 20, 8, (255, 140, 40))
    # UN flag on a pole
    fx, fy = x1 - 26, y0 + 8
    d.line([fx, fy, fx, y1 - 8], fill=(60, 60, 60), width=2)
    d.rectangle([fx + 1, fy, fx + 22, fy + 13], fill=(90, 150, 220))
    d.ellipse([fx + 7, fy + 3, fx + 16, fy + 10], fill=(255, 255, 255))
    d.rectangle([x0, y1 - 8, x1, y1], fill=(120, 104, 84))


def pic_cricket(d, box):
    """13: the Basin Reserve — a pitch, stumps, a blocker and a 239/5
    board: five hours of defence to save the Test."""
    x0, y0, x1, y1 = box
    sky(d, box, (150, 200, 140), (170, 212, 150), (190, 224, 164))
    disc(d, x0 + 18, y0 + 10, 8, (255, 214, 90))
    d.rectangle([x0, y1 - 16, x1, y1], fill=(60, 128, 64))
    d.rectangle([x0 + 58, y1 - 44, x0 + 128, y1 - 16], fill=(214, 186, 140))
    # stumps at the striker's end
    for k in range(3):
        d.line([x0 + 66 + k * 3, y1 - 40, x0 + 66 + k * 3, y1 - 30],
               fill=(240, 220, 160), width=2)
    # batsman playing a dead bat
    figure(d, x0 + 96, y1 - 52, 14, shirt=(20, 20, 20))
    d.line([x0 + 104, y1 - 38, x0 + 112, y1 - 20], fill=(150, 110, 70), width=4)
    # ball rolling away, fielder watching
    disc(d, x0 + 140, y1 - 22, 3, (178, 34, 34))
    figure(d, x0 + 160, y1 - 50, 13, shirt=(255, 255, 255))
    # scoreboard
    d.rectangle([x1 - 54, y0 + 8, x1 - 8, y0 + 26], fill=(20, 20, 20))
    d.text((x1 - 50, y0 + 10), "239/5", font=F(SANS_B, 11), fill=(255, 255, 255))
    puff(d, x0 + 120, y0 + 4, 12, (240, 240, 238))


PICS = {1: pic_dymer, 2: pic_merkury, 3: pic_nvidia, 4: pic_eu, 5: pic_fifa,
        6: pic_sparta, 7: pic_nepal, 8: pic_ahmadi, 9: pic_china,
        10: pic_cikande, 11: pic_binance, 12: pic_gaza, 13: pic_cricket}

# ---------- story data ----------
# (num, region, topic, source, tag, headline, summary)
HEROES = [
    (1, "EUROPE", "UKRAINE", "AL JAZEERA", "CONFIRMED",
     "Dymer toll hits 11 as Kyiv region buries 15",
     "11 in Dymer, 3 in Vyshneve, 1 in Bila Tserkva; a woman, 79, pulled alive."),
    (2, "AFRICA", "LIBYA", "AP", "OFFICIAL",
     "Zelenskyy: Ukraine sank corvette in Libya",
     "Merkury sunk at Benghazi; a Ka-27 helicopter destroyed; cargo ship Angara hit."),
    (3, "AMERICAS", "MARKETS", "REUTERS", "CONFIRMED",
     "Huang back at Nvidia; Wall Street roars",
     "Board reinstates Huang after Trump's push; Wall St's best day since April 2025."),
]
SECONDARY = [
    (4, "EUROPE", "EU", "AP", "OFFICIAL",
     "EU proposes 22nd Russia sanctions",
     "60 banks off SWIFT; 70 ships listed; flag ban at EU sport."),
    (5, "WORLD", "SPORT", "REUTERS", "OFFICIAL",
     "FIFA: US hosts 2031, UK hosts 2035",
     "48 teams, 104 matches; first Women's World Cup in the UK."),
    (6, "EUROPE", "BALTIC", "REUTERS", "CONFIRMED",
     "Sparta II docks in St Petersburg",
     "Towed in after the drone hit; all 16 crew safe."),
    (7, "ASIA", "NEPAL", "REUTERS", "OFFICIAL",
     "India unveils $1.62bn Nepal package",
     "NPR 24,000 crore for flood rebuild; talks in New Delhi."),
    (8, "MIDDLE EAST", "IRAN", "REUTERS", "REPORTED",
     "Iran flogs singer Ahmadi 74 times",
     "Five lashed in Qom over a hijab-less concert; 2-year bans."),
    (9, "ASIA", "CHINA", "AP", "OFFICIAL",
     "China sentences official to death",
     "Official 'leaked state secrets to a foreign country'."),
    (10, "ASIA", "INDONESIA", "REUTERS", "CONFIRMED",
     "Cikande toll hits 24, 30 still missing",
     "24 body bags out; DNA ID may take weeks; 300 were on shift."),
    (11, "AMERICAS", "USA", "REUTERS", "OFFICIAL",
     "US moves to recover $1bn Binance crypto",
     "North Korean hackers blamed; civil claim filed on Monday."),
    (12, "MIDDLE EAST", "GAZA", "REUTERS", "REPORTED",
     "Israeli strike kills UNRWA worker",
     "Adel al-Helo hit at a Jabalia well; 3 killed Monday."),
    (13, "OCEANIA", "CRICKET", "AP", "CONFIRMED",
     "NZ bat out 120 overs to draw Test",
     "Mitchell 49*, Phillips 26*; India's 720/9 not enough."),
]
LISTED = [
    "Germany, Denmark schools hit by bomb threats",
    "Hungary PM Magyar to visit Ukraine 'soon'",
    "Belgium PM sets 31 Dec budget deadline",
    "NATO sends AWACS to Poland after missile talks",
    "Moscow: Estonia acts near 'open war'",
    "Trump halts Iowa explosives detonation",
    "Court opens path to erase Trump hush-money conviction",
    "Rep. Gomez quits after ethics report",
    "49ers rout Vikings 35–10 in Mexico City",
    "Amtrak derails in Louisiana after hitting truck",
    "Manipur: 9 arrested, 81 still in hospital",
    "Delhi: knife attack injures 9 police; man shot",
    "Jaishankar phones Lavrov on Monday",
    "Iran vows to counter US blockade of Hormuz",
    "Saudi sway loomed over failed COP31 deal",
    "Gaza City: vehicle strike kills 2 more",
    "COP31: can climate diplomacy build on the collapse?",
    "US blacklists Megaspeed in Nvidia chip scandal",
    "Kenya, DR Congo restore ambassador ties",
    "Zimbabwe preacher Uebert Angel arrested",
    "Australia to treat AI as foreign-policy challenge",
    "COP31 flop: Pacific nations voice despair",
]
REGIONS = [("EUROPE", 8, (36, 84, 160)), ("AMERICAS", 7, (14, 128, 128)),
           ("ASIA", 6, (122, 62, 158)), ("MIDDLE EAST", 5, (178, 44, 44)),
           ("WORLD", 3, (96, 96, 100)), ("AFRICA", 3, (46, 134, 74)),
           ("OCEANIA", 3, (214, 122, 26))]
FIELDS = ["WAR", "CLIMATE", "MARKETS", "SPORT", "DIPLOMACY", "COURTS",
          "DISASTER", "POLITICS", "CRIME", "CULTURE", "TRANSPORT",
          "SECURITY", "TECH"]
# numbers strip: six cells, two rows of three; each a complete mini-story
NUMBERS = [("15", "killed in Kyiv-region strikes, 11 in Dymer"),
           ("+31.5%", "Nvidia shares jump as Huang returns"),
           ("7", "sea drones sank the Russian corvette"),
           ("60", "Russian banks cut from SWIFT by the EU"),
           ("24", "confirmed dead in the Cikande factory fire"),
           ("120", "overs New Zealand batted to save the Test")]
# timeline strip: seven timed events across the day (UTC)
TIMELINE = [("05:30", "Kyiv toll hits 15"),
            ("14:00", "Nvidia reinstates Huang"),
            ("14:32", "Amtrak derails in Louisiana"),
            ("15:42", "Gaza strikes kill 3"),
            ("16:24", "FIFA: US 2031, UK 2035"),
            ("17:47", "EU proposes 22nd sanctions"),
            ("21:58", "Sparta II reaches port")]
# map pins: (num, x, y); red for 1-3, navy for 4-13
PINS = [(1, 212, 845), (2, 214, 881), (3, 96, 848), (4, 192, 840),
        (5, 178, 831), (6, 220, 830), (7, 262, 871), (8, 238, 862),
        (9, 282, 853), (10, 272, 895), (11, 106, 861), (12, 226, 871),
        (13, 306, 929)]
LAND = [  # ellipses (x0, y0, x1, y1) forming a coarse dotted world map
    (45, 826, 170, 880), (175, 824, 200, 837), (130, 883, 185, 940),
    (185, 837, 235, 862), (190, 865, 250, 929), (235, 830, 310, 880),
    (255, 880, 285, 897), (265, 912, 305, 935), (180, 840, 192, 851),
    (300, 844, 312, 862), (235, 862, 265, 894), (190, 855, 230, 869),
    (165, 840, 195, 858), (205, 865, 235, 887), (185, 826, 205, 844),
    (308, 928, 318, 940),
]


def kicker(d, x, y, num, region, topic, src, tag, width, size=10):
    """Left: 'N · REGION · TOPIC'; right: 'SOURCE · TAG'. Drops topic if tight."""
    f, sf = F(SANS_B, size), F(SANS, size - 1)
    right = f"{src} · {tag}"
    full = f"{num} · {region} · {topic}"
    if d.textlength(full, font=f) + d.textlength(right, font=sf) + 12 > width:
        full = f"{num} · {region}"
    d.text((x, y), full, font=f, fill=RED)
    d.text((x + width - d.textlength(right, font=sf), y), right, font=sf,
           fill=MUTED)


def kicker2(d, x, y, num, region, topic, src, tag, width):
    """Two-line kicker for the narrow secondary cards: line 1 is the
    number/region/topic, line 2 is the source and verification tag."""
    d.text((x, y), f"{num} · {region} · {topic}", font=F(SANS_B, 9), fill=RED)
    d.text((x, y + 11), f"{src} · {tag}", font=F(SANS, 8), fill=MUTED)


def main():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    M = 24
    X1 = W - M

    # ---- header ----
    d.rectangle([M, 14, 116, 136], fill=RED)
    d.text((30, 20), "NOV", font=F(SANS_B, 22), fill=(255, 255, 255))
    d.text((30, 44), "23", font=F(SERIF_B, 52), fill=(255, 255, 255))
    d.text((30, 104), "MON 2026", font=F(SANS_B, 13), fill=(255, 255, 255))
    d.text((132, 18), "THE DAY IN WORLD NEWS", font=F(SANS_B, 15), fill=RED)
    d.text((132, 38), "Monday 23 November 2026", font=F(SERIF_B, 44), fill=INK)
    d.text((132, 98),
           "Everything on this page happened, or was first reported, on Monday 23 November 2026.",
           font=F(SANS, 15), fill=MUTED)
    for i, line in enumerate(["35 STORIES", "7 REGIONS", "13 FIELDS"]):
        f = F(SANS_B, 19)
        d.text((X1 - d.textlength(line, font=f), 24 + i * 26), line, font=f, fill=INK)
    d.line([M, 142, X1, 142], fill=INK, width=2)

    # ---- timeline strip: seven timed events across the day ----
    ty = 147
    d.text((M, ty), "THE DAY IN UTC", font=F(SANS_B, 11), fill=RED)
    tw = (X1 - M) / 7
    for i, (t, lab) in enumerate(TIMELINE):
        cx = M + i * tw
        d.text((cx, ty + 13), t, font=F(SANS_B, 12), fill=RED)
        put_text(d, (cx, ty + 26), lab, F(SANS, 9), tw - 8, INK, leading=1,
                 limit=1)
    d.line([M, 182, X1, 182], fill=RULE, width=1)

    # ---- region strip ----
    y0, y1 = 186, 210
    total_w = X1 - M
    widths = [max(64, int(total_w * n / 35)) for _, n, _ in REGIONS]
    scale = total_w / sum(widths)
    widths = [int(w * scale) for w in widths]
    widths[-1] += total_w - sum(widths)
    x = M
    for (name, n, col), w in zip(REGIONS, widths):
        d.rectangle([x, y0, x + w - 1, y1], fill=col)
        label = f"{name} {n}"
        f = F(SANS_B, 13)
        if d.textlength(label, font=f) <= w - 8:
            d.text((x + (w - d.textlength(label, font=f)) / 2, y0 + 6),
                   label, font=f, fill=(255, 255, 255))
        else:
            f2 = F(SANS_B, 10)
            d.text((x + (w - d.textlength(name, font=f2)) / 2, y0 + 2),
                   name, font=f2, fill=(255, 255, 255))
            d.text((x + (w - d.textlength(str(n), font=f2)) / 2, y0 + 13),
                   str(n), font=f2, fill=(255, 255, 255))
        x += w

    # ---- numbers strip: six cells, two rows of three ----
    ny = 216
    for row in range(2):
        for col in range(3):
            num, lab = NUMBERS[row * 3 + col]
            cx = M + col * 325
            cy = ny + row * 23
            f1, f2 = F(SANS_B, 16), F(SANS, 11)
            d.text((cx, cy), num, font=f1, fill=RED)
            lx = cx + d.textlength(num + " ", font=f1)
            d.text((lx, cy + 3), lab, font=f2, fill=INK)
            end = lx + d.textlength(lab, font=f2)
            if end > X1:
                print(f"OVERFLOW: numbers cell {num!r} ends at {end}, edge {X1}")
    d.line([M, 266, X1, 266], fill=RULE, width=1)

    # ---- hero stories ----
    hy, hh = 272, 228
    hw, gap = 312, 20
    for i, (num, region, topic, src, tag, head, summ) in enumerate(HEROES):
        x = M + i * (hw + gap)
        d.rectangle([x, hy, x + hw, hy + hh], fill=CARD, outline=RULE, width=1)
        PICS[num](d, (x + 1, hy + 1, x + hw - 1, hy + 125))
        ky = hy + 132
        kicker(d, x + 10, ky, num, region, topic, src, tag, hw - 20, size=11)
        y2 = put_text(d, (x + 10, ky + 17), head, F(SERIF_B, 21),
                      hw - 20, INK, leading=1, limit=2)
        put_text(d, (x + 10, y2 + 3), summ, F(SANS, 12),
                 hw - 20, MUTED, leading=1, limit=2)

    # ---- secondary stories: 5 columns x 2 rows ----
    sy = 508
    cw, cgap = 187, 10
    ch = 140
    for i, (num, region, topic, src, tag, head, summ) in enumerate(SECONDARY):
        col, row = i % 5, i // 5
        x = M + col * (cw + cgap)
        yy = sy + row * (ch + 8)
        d.rectangle([x, yy, x + cw, yy + ch], fill=CARD, outline=RULE, width=1)
        PICS[num](d, (x + 1, yy + 1, x + cw - 1, yy + 57))
        kicker2(d, x + 8, yy + 61, num, region, topic, src, tag, cw - 16)
        y2 = put_text(d, (x + 8, yy + 86), head, F(SERIF_B, 14),
                      cw - 16, INK, leading=1, limit=2)
        put_text(d, (x + 8, y2 + 2), summ, F(SANS, 10),
                 cw - 16, MUTED, leading=1, limit=2)

    # ---- map + list ----
    my = 804
    d.line([M, my - 4, X1, my - 4], fill=INK, width=2)
    d.text((M, my), "WHERE IT HAPPENED", font=F(SANS_B, 14), fill=INK)
    d.text((330, my), "ALSO ON MONDAY 23 NOVEMBER — 22 MORE STORIES",
           font=F(SANS_B, 14), fill=INK)
    # dotted map
    mx0, my0, mx1, my1 = M, my + 20, 318, 940
    for gx in range(mx0, mx1, 6):
        for gy in range(my0, my1, 6):
            cx, cy = gx + 3, gy + 3
            if any((cx - (a + c) / 2) ** 2 / (((c - a) / 2) ** 2) +
                   (cy - (b + e) / 2) ** 2 / (((e - b) / 2) ** 2) <= 1
                   for a, b, c, e in LAND):
                d.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=MAPDOT)
    for num, px, py in PINS:
        col = RED if num <= 3 else NAVY
        d.ellipse([px - 7, py - 7, px + 7, py + 7], fill=col,
                  outline=(255, 255, 255), width=1)
        f = F(SANS_B, 9 if num < 10 else 8)
        t = str(num)
        d.text((px - d.textlength(t, font=f) / 2, py - 5), t, font=f,
               fill=(255, 255, 255))
    d.text((M, 944),
           "Europe 8 · Americas 7 · Asia 6 · Middle East 5 · World 3 · Africa 3 · Oceania 3",
           font=F(SANS, 9), fill=MUTED)
    # numbered list, two columns of 11
    lf = F(SANS, 11)
    for i, item in enumerate(LISTED):
        col = i // 11
        row = i % 11
        lx = 330 + col * 336
        ly = my + 22 + row * 10.5
        num = 14 + i
        d.text((lx, ly), f"{num}", font=F(SANS_B, 11), fill=RED)
        d.text((lx + 22, ly), item, font=lf, fill=INK)

    # ---- date check box ----
    by0 = 954
    d.rectangle([M, by0, X1, by0 + 48], outline=RED, width=2)
    d.text((M + 10, by0 + 3), "DATE CHECK", font=F(SANS_B, 12), fill=RED)
    d.text((M + 108, by0 + 3),
           "Left out on purpose — each was first reported before Monday:",
           font=F(SANS, 12), fill=INK)
    dc = F(SANS, 9)
    d.text((M + 10, by0 + 16),
           "COP31 collapse · Democrats' House win · Las Vegas GP · Cikande toll 3 dead · Hong Kong poll · Kaliningrad sirens · Iran–Bahrain radar claims (all 22 Nov)",
           font=dc, fill=MUTED)
    d.text((M + 10, by0 + 26),
           "India 720/9 · Lowy index · Israel talks end · Warrap attack (22 Nov) · Iran strikes Bahrain · 'El Chapo' · Peru quake · EU–Indonesia pact · Paris summit (21 Nov) · Kyiv bridges · Cyclone Akvan (20 Nov)",
           font=dc, fill=MUTED)
    d.text((M + 10, by0 + 36),
           "Not yet: CAS rules on Senegal AFCON appeal (Tue) · South Sudan election (Feb 2027) · COP32 (Nov 2027) · Trump hush-money ruling (later)",
           font=dc, fill=RED)
    # ---- footer ----
    d.text((M, 1006),
           "Tags: CONFIRMED — two or more outlets · OFFICIAL — on the record · REPORTED — one outlet",
           font=F(SANS, 8), fill=MUTED)
    d.text((M, 1015),
           "Sources: Reuters · AP · AFP · BBC · Al Jazeera · The Hindu",
           font=F(SANS, 8), fill=MUTED)
    attr = "Original drawings. Claims are attributed, not stated as fact."
    d.text((X1 - d.textlength(attr, font=F(SANS, 8)), 1015), attr,
           font=F(SANS, 8), fill=MUTED)

    total = len(HEROES) + len(SECONDARY) + len(LISTED)
    rsum = sum(n for _, n, _ in REGIONS)
    print(f"counts: heroes {len(HEROES)} + secondary {len(SECONDARY)} + listed {len(LISTED)} = {total}; regions sum {rsum}; fields {len(FIELDS)}")
    assert total == 35 and rsum == 35, "counts do not reconcile to 35"
    assert len(FIELDS) == 13, "field count wrong"

    img.save("entry.png", optimize=True)
    print("saved entry.png", img.size, "bytes:", os.path.getsize("entry.png"))


if __name__ == "__main__":
    main()
