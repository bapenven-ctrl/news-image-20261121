#!/usr/bin/env python3
"""
news-image-20261121 — "The World in One Day", Saturday 21 November 2026.

Original flat-vector broadsheet renderer (Python + Pillow), written for this
entry. Deterministic: no randomness, no clock, no network. Running it twice
writes byte-identical entry.png files.

Layout system (style reference only — all code and artwork are original):
masthead -> big-numbers strip -> region chips -> 3 hero panels + pin map ->
10 illustrated cards -> 3-column briefs -> DATE CHECK band -> footer.
"""
import math
import os
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------- constants
W, H = 1024, 1024          # final size
S = 2                      # supersample factor (render at 2048, downscale)
M = 26                     # page margin (design units)
CW = W - 2 * M             # content width = 972

CREAM = (247, 241, 227)
PAPER = (252, 249, 240)
INK = (26, 24, 20)
MUTE = (96, 88, 74)
RED = (164, 32, 40)        # deep red accent
DRED = (122, 24, 30)
NAVY = (16, 38, 62)
NAVY2 = (23, 54, 86)
SAND = (216, 186, 130)     # map land
LINE = (178, 168, 148)

FD = "/usr/share/fonts/truetype/noto/"


def F(name, size):
    """Font at design size (scaled by supersample factor)."""
    return ImageFont.truetype(FD + name, int(size * S))


SER_B = "NotoSerif-Bold.ttf"
SER = "NotoSerif-Regular.ttf"
SER_I = "NotoSerif-Italic.ttf"
SAN_B = "NotoSans-Bold.ttf"
SAN = "NotoSans-Regular.ttf"
SAN_I = "NotoSans-Italic.ttf"

# ---------------------------------------------------------------- story data
# Every figure below was checked against dated primary reporting on
# 21 Nov 2026 (see stories.md). STORY-LOCKED 22 Nov 2026, 00:55 UTC:
# 11 Tahap-1 items proved to be 19-20 Nov news and were dropped/replaced.

BIG_NUMBERS = [
    ("Day 13", "of a COP summit that missed its close \u2014 still no deal"),
    ("3", "ballistic missiles destroyed over Riyadh"),
    ("6.7", "magnitude of the earthquake in Junin, Peru"),
    ("146", "people safe after a jet's emergency landing in Davao"),
    ("$55,130", "bitcoin's low on Saturday \u2014 lowest since Sep 2024"),
    ("136", "K L Rahul's runs in Wellington"),
]

REGIONS = [("EUROPE", 9), ("AMERICAS", 6), ("ASIA-PACIFIC", 9),
           ("MIDEAST", 6), ("OCEANIA", 2), ("WORLD", 2)]
REGION_COLORS = [(43, 90, 160), (178, 44, 44), (198, 110, 44), (122, 36, 110),
                 (44, 130, 150), (70, 70, 70)]

# hero: (num, kicker, headline lines, summary lines, source, ill key, lon, lat)
HEROES = [
    (1, "01 \u00b7 ANTALYA, T\u00dcRKIYE \u00b7 CLIMATE",
     ["Climate summit ends Saturday", "with no deal in sight"],
     ["COP31 missed its Friday close and stayed deadlocked",
      "into Saturday night; the promised third text never came."],
     "(Health Policy Watch, AP)", "cop", 30.7, 36.9),
    (2, "02 \u00b7 RIYADH, SAUDI ARABIA \u00b7 WAR",
     ["Three Houthi missiles shot", "down over Riyadh"],
     ["The Saudi-led coalition destroyed three ballistic",
      "missiles targeting Riyadh; a drone was downed later."],
     "(Reuters, AFP)", "riyadh", 46.7, 24.6),
    (3, "03 \u00b7 MERCURY ORBIT \u00b7 SPACE",
     ["BepiColombo slips into orbit", "around Mercury"],
     ["After an eight-year journey, ESA's probe fired for",
      "37 minutes and entered orbit \u2014 only the second ever."],
     "(ESA, Nature)", "bepi", 8.65, 49.87),
]

# card: (num, kicker, headline lines, summary lines, source, ill key, lon, lat)
CARDS = [
    (4, "04 \u00b7 JUN\u00cdN \u00b7 EARTHQUAKE",
     ["Magnitude 6.7 earthquake", "shakes central Peru"],
     ["The deep quake at 00:09 UTC was felt",
      "in Lima; no deaths or damage."],
     "(USGS, Gesti\u00f3n)", "peru", -75.5, -11.5),
    (5, "05 \u00b7 DAVAO \u00b7 AVIATION",
     ["Jet lands safely after", "engine fire alert"],
     ["Air Niugini diverts after midnight;", "all 146 aboard are safe."],
     "(AP)", "plane", 125.4, 7.8),
    (6, "06 \u00b7 PERTH \u00b7 CRICKET",
     ["Australia win Ashes opener", "inside two days"],
     ["Head's 123 off 83 balls seals an eight-",
      "wicket win; Starc takes 10 for 113."],
     "(ANI)", "ashes", 115.86, -31.95),
    (7, "07 \u00b7 GULF OF FINLAND \u00b7 WAR",
     ["Russian cargo ship hit by", "drones in the Baltic"],
     ["Sparta II catches fire and drifts into",
      "Finnish waters; all 16 crew evacuated."],
     "(Reuters)", "sparta", 24.94, 60.17),
    (8, "08 \u00b7 WELLINGTON \u00b7 CRICKET",
     ["Rahul hits 136 as India", "take the lead"],
     ["136 off 290 balls; India 486 for 4,",
      "replying to 368, lead by 118."],
     "(ESPNcricinfo)", "rahul", 173.8, -40.6),
    (9, "09 \u00b7 LAS VEGAS \u00b7 FORMULA 1",
     ["Antonelli fastest \u2014 but", "Verstappen takes pole"],
     ["Antonelli 1:33.893, then a five-place",
      "grid penalty; Verstappen inherits pole."],
     "(Formula1.com)", "f1", -115.1, 36.2),
    (10, "10 \u00b7 WORLD \u00b7 MARKETS",
     ["Bitcoin falls below", "$58,000 on Saturday"],
     ["Low $55,130, closes $57,884 \u2014 the",
      "lowest since September 2024."],
     "(CoinGecko)", "bitcoin", -74.0, 40.7),
    (11, "11 \u00b7 UKRAINE \u00b7 WAR",
     ["Russia launches 3 missiles", "and 148 drones overnight"],
     ["Ukraine's air force says 117 drones",
      "were downed by 08:00 Kyiv time."],
     "(Ukrainian Air Force)", "drones", 30.5, 50.4),
    (12, "12 \u00b7 STRAIT OF HORMUZ \u00b7 WAR",
     ["Iran says it shot down", "a US drone"],
     ["IRGC claims its 58th MQ-9 downing",
      "over Hormuz. No US confirmation."],
     "(IRIB claim)", "hormuz", 56.3, 27.4),
    (13, "13 \u00b7 GAZA CITY \u00b7 WAR",
     ["Israeli strike kills three", "in a vehicle in Gaza City"],
     ["Three killed in Tel al-Hawa; Gaza counts",
      "1,671 dead since the October ceasefire."],
     "(Reuters)", "gaza", 35.0, 31.8),
]

# brief: (num, city, text) — single line each, source in parentheses
BRIEFS = [
    (14, "KYIV", "Kryvyi Rih strike kills 2, injures 60 (attack Fri; toll Sat, AP)"),
    (15, "ANTALYA", "EU warns COP31 against a \u201cfossil summit\u201d (Al Jazeera)"),
    (16, "ANTALYA", "Panama threatens to block the climate text (Al Jazeera)"),
    (17, "ANTALYA", "Indonesia's PLN signs six clean-power deals (Antara)"),
    (18, "SANAA", "Houthis threaten Jeddah and Red Sea ports (Al Jazeera)"),
    (19, "TAIPEI", "Mayor urges: don't block NT$20,000 cash payout (Asia Daily)"),
    (20, "PYONGYANG", "Kim tours factories after no Trump meeting (AFP)"),
    (21, "NEW DELHI", "Pakistan minister gets Taj Mahal, not dargah (Fact)"),
    (22, "KANSAS", "No. 10 BYU beats Kansas 31\u201329 in triple overtime (Reuters)"),
    (23, "SEJONG", "Freight train derails; no one hurt (Korea Herald)"),
    (24, "BANGKOK", "Arsenic 30\u00d7 safe limit; water cut to 20,000 homes (CRT)"),
    (25, "NEW DELHI", "Pakistani minister joins SCO forum in India (Centreline)"),
    (26, "NAYPYIDAW", "Rights groups urge sanctions after ruling (AP)"),
    (27, "TEHRAN", "Iran: uranium stays; \u201cfair solution\u201d possible (Iran paper)"),
    (28, "BRUSSELS", "EU\u2013Indonesia sign trade deal after 10 years (EC)"),
    (29, "GENEVA", "UN \u201ckiller robots\u201d talks end with no rules, to 2028 (AP)"),
    (30, "PARIS", "Cost-of-living protests: 82,500 march in France (Al Jazeera)"),
    (31, "MANAMA", "Iran attack sets Bahrain industrial site ablaze (Al Jazeera)"),
    (32, "BRUSSELS", "UK\u2013EU sign three post-Brexit deals (One Turn)"),
    (33, "WASHINGTON", "Indian jailed 19+ years over Pannun murder plot (AJ)"),
    (34, "PORT-AU-PRINCE", "Police kill at least 34 gang members in raid (AJ)"),
]

DATE_CHECK = [
    "Iraq retakes Jurf al-Sakhar \u00b7 Bayelsa funeral boat capsizes \u00b7 Texas execution (63 min) \u00b7 Palisades arson verdict \u00b7 Vance on Iran strikes \u00b7 SpaceX funding threat \u00b7",
    "Trump's data-centre tax \u00b7 China\u2013Japan Taiwan row \u00b7 ANC's 31% in Johannesburg \u00b7 Virginia's first measles death \u00b7 Wall Street's slide into correction \u00b7 Russian missile in Poland \u00b7",
    "Danish attach\u00e9 plot \u00b7 EU's \u20ac7.9bn for Ukraine \u00b7 India's H5N1 vaccine \u00b7 Bayer's $7.25bn Roundup deal \u00b7 Akvan's landfall. Older: Shenzhen summit, Anthropic IPO, GTA VI (19 Nov) \u00b7 Voyager 1 (18 Nov) \u00b7 COP31 deal (Sunday).",
]

TOTAL_STORIES = len(HEROES) + len(CARDS) + len(BRIEFS)  # 34

# ---------------------------------------------------------------- world map
# Hand-drawn simplified continent outlines in (lon, lat). Original stylised
# polygons, coarse on purpose — pins are verified to land inside them.
LAND = [
    # North America
    [(-168, 66), (-140, 70), (-125, 72), (-110, 68), (-95, 69), (-85, 66),
     (-80, 62), (-76, 58), (-70, 55), (-65, 50), (-70, 45), (-74, 40),
     (-76, 35), (-80, 32), (-80, 26), (-84, 22), (-90, 20), (-97, 16),
     (-105, 12), (-97, 8), (-92, 8), (-86, 12), (-83, 9), (-79, 9),
     (-83, 15), (-90, 14), (-95, 16), (-105, 20), (-110, 23), (-114, 29),
     (-120, 34), (-124, 40), (-124, 46), (-130, 54), (-140, 60), (-155, 60),
     (-165, 60)],
    # South America
    [(-79, 9), (-75, 11), (-70, 12), (-62, 10), (-55, 6), (-50, 0),
     (-44, -3), (-35, -8), (-38, -15), (-40, -22), (-48, -27), (-52, -33),
     (-57, -38), (-62, -41), (-65, -45), (-67, -50), (-68, -54), (-71, -54),
     (-73, -50), (-73, -44), (-73, -37), (-71, -30), (-70, -20), (-75, -15),
     (-79, -8), (-80, -4), (-80, 1), (-77, 4)],
    # Africa
    [(-6, 35), (0, 36), (10, 37), (11, 34), (20, 32), (30, 31), (32, 31),
     (35, 28), (38, 22), (40, 15), (43, 12), (48, 11), (51, 10), (50, 5),
     (42, -2), (40, -10), (38, -18), (35, -24), (32, -29), (25, -34),
     (19, -35), (17, -30), (15, -22), (13, -15), (12, -10), (9, -5),
     (9, 0), (6, 4), (-3, 5), (-8, 5), (-13, 8), (-17, 12), (-17, 15),
     (-16, 20), (-15, 25), (-13, 28), (-9, 31)],
    # Eurasia (single landmass, simplified coasts)
    [(-9, 37), (-9, 43), (-2, 44), (-9, 46), (-2, 49), (0, 51), (5, 53),
     (8, 57), (5, 59), (5, 61), (10, 64), (18, 69), (25, 71), (31, 70),
     (45, 68), (60, 69), (75, 70), (90, 72), (105, 72), (120, 73),
     (135, 72), (150, 70), (160, 69), (170, 67), (178, 65), (178, 62),
     (162, 60), (158, 55), (150, 50), (142, 45), (140, 38), (129, 35),
     (122, 31), (120, 25), (110, 20), (108, 15), (106, 9), (104, 2),
     (100, 6), (98, 10), (97, 16), (92, 16), (91, 22), (88, 21), (86, 20),
     (80, 13), (77, 8), (72, 18), (66, 25), (61, 25), (57, 27), (52, 26),
     (50, 29), (48, 30), (50, 24), (55, 24), (59, 22), (55, 17), (48, 14),
     (43, 12), (40, 15), (38, 21), (35, 28), (34, 31), (36, 36), (30, 36),
     (27, 37), (23, 36), (19, 40), (16, 38), (16, 40), (12, 44), (19, 42),
     (23, 40), (26, 38), (23, 36), (19, 40), (15, 40), (12, 44), (7, 44),
     (3, 43), (-2, 37)],
    # Britain
    [(-5, 50), (-3, 53), (-5, 55), (-3, 57), (-2, 58), (-1, 56), (0, 53),
     (1, 51)],
    # Japan
    [(130, 31), (133, 34), (137, 35), (140, 36), (141, 40), (141, 43),
     (143, 43), (145, 44), (143, 45), (140, 42), (139, 38), (135, 34),
     (131, 32)],
    # Indonesia / Papua (stylised archipelago mass)
    [(95, 5), (100, 0), (105, -5), (110, -7), (115, -8), (120, -9),
     (125, -10), (131, -3), (136, -2), (141, -3), (146, -6), (150, -9),
     (147, -9), (141, -8), (136, -4), (131, -4), (125, -8), (119, -8),
     (113, -7), (106, -6), (100, -2), (95, 3)],
    # Philippines
    [(120, 18), (122, 16), (121, 14), (120, 12), (122, 10), (124, 8),
     (126, 7), (126, 9), (124, 11), (122, 13), (121, 16), (120, 18)],
    # Australia
    [(113, -22), (114, -28), (115, -34), (118, -35), (124, -33), (130, -32),
     (132, -32), (135, -35), (137, -35), (140, -38), (145, -38), (147, -38),
     (150, -37), (153, -31), (153, -27), (151, -24), (146, -19), (142, -15),
     (142, -11), (140, -17), (136, -15), (135, -12), (132, -11), (129, -14),
     (126, -14), (122, -17), (118, -20)],
    # New Zealand
    [(166, -45.5), (169, -43), (171, -41.8), (173, -40.5), (175, -38.5),
     (176.5, -37.5), (175, -39), (174.5, -40.5), (173, -42), (171, -43.8),
     (168, -46.5)],
]


def project(lon, lat, box):
    """Equirectangular projection into box (x, y, w, h), lon -170..185, lat -58..78."""
    x, y, w, h = box
    px = x + (lon + 170) / 355.0 * w
    py = y + (78 - lat) / 136.0 * h
    return px, py


def point_in_land(lon, lat):
    """Ray-casting point-in-polygon against LAND (in lon/lat space)."""
    inside = False
    for poly in LAND:
        n = len(poly)
        j = n - 1
        for i in range(n):
            xi, yi = poly[i]
            xj, yj = poly[j]
            if ((yi > lat) != (yj > lat)) and \
               (lon < (xj - xi) * (lat - yi) / (yj - yi) + xi):
                inside = not inside
            j = i
    return inside

# ---------------------------------------------------------------- drawing helpers
def X(v):
    return v * S


def rect(d, box, **kw):
    d.rectangle([X(box[0]), X(box[1]), X(box[2]), X(box[3])], **kw)


def ell(d, box, **kw):
    d.ellipse([X(box[0]), X(box[1]), X(box[2]), X(box[3])], **kw)


def line(d, pts, **kw):
    d.line([(X(x), X(y)) for x, y in pts], **kw)


def poly(d, pts, **kw):
    d.polygon([(X(x), X(y)) for x, y in pts], **kw)


def txt(d, xy, s, font, fill=INK, anchor="la"):
    d.text((X(xy[0]), X(xy[1])), s, font=F(font[0], font[1]), fill=fill,
           anchor=anchor)


def tw(s, font):
    """Text width in design units."""
    f = F(font[0], font[1])
    return f.getlength(s) / S


def chip(d, x, y, s, bg=INK, fg=(255, 255, 255), size=8.5):
    w = tw(s, (SAN_B, size)) + 10
    rect(d, (x, y, x + w, y + 13), fill=bg)
    txt(d, (x + 5, y + 2.2), s, (SAN_B, size), fill=fg)
    return w


# ---------------------------------------------------------------- illustrations
# All artwork is original flat vector drawing. Hero box = 236x100, card = 189x40.
def ill_cop(d, b):
    x, y, w, h = b[0], b[1], b[2] - b[0], b[3] - b[1]
    rect(d, b, fill=(193, 222, 205))
    cx, cy, r = x + 62, y + 48, 34
    ell(d, (cx - r, cy - r, cx + r, cy + r), fill=(64, 120, 190))
    poly(d, [(cx - 20, cy - 22), (cx - 4, cy - 28), (cx - 2, cy - 14),
             (cx - 14, cy - 8), (cx - 22, cy - 14)], fill=(74, 160, 90))
    poly(d, [(cx + 6, cy + 2), (cx + 22, cy - 2), (cx + 26, cy + 12),
             (cx + 12, cy + 18), (cx + 4, cy + 10)], fill=(74, 160, 90))
    poly(d, [(cx - 8, cy + 16), (cx + 2, cy + 12), (cx + 4, cy + 24),
             (cx - 4, cy + 28)], fill=(74, 160, 90))
    tx = x + 122
    rect(d, (tx, y + 16, tx + 10, y + 74), fill=(240, 240, 235),
         outline=INK, width=S)
    rect(d, (tx + 2, y + 34, tx + 8, y + 74), fill=RED)
    ell(d, (tx - 3, y + 70, tx + 13, y + 86), fill=RED)
    kx, ky, kr = x + 178, y + 50, 26
    ell(d, (kx - kr, ky - kr, kx + kr, ky + kr), fill=(250, 248, 240),
        outline=INK, width=S)
    line(d, [(kx, ky), (kx, ky - 17)], fill=INK, width=S)
    line(d, [(kx, ky), (kx + 12, ky + 6)], fill=INK, width=S)
    chip(d, x + 8, y + h - 17, "NO DEAL \u00b7 DAY 13")


def ill_riyadh(d, b):
    x, y, w, h = b[0], b[1], b[2] - b[0], b[3] - b[1]
    rect(d, b, fill=NAVY)
    for sx, sy in [(30, 18), (80, 10), (150, 22), (200, 12), (110, 28)]:
        ell(d, (x + sx, y + sy, x + sx + 3, y + sy + 3), fill=(230, 230, 210))
    base = y + h - 16
    for bx, bw, bh in [(6, 26, 26), (38, 18, 38), (62, 30, 20), (98, 16, 30),
                       (120, 34, 24), (160, 20, 34), (186, 28, 22),
                       (218, 14, 28)]:
        rect(d, (x + bx, base - bh, x + bx + bw, base), fill=(8, 20, 36))
    rect(d, (x, base, x + w, y + h), fill=(8, 20, 36))
    for i, (ax, ay) in enumerate([(36, 30), (108, 20), (182, 34)]):
        pts = []
        for t in range(21):
            tt = t / 20.0
            px = x + 8 + tt * (ax - 8)
            # smooth arc from the ground up to the burst point
            py = (y + h - 20) + tt * (ay - (y + h - 20)) \
                - math.sin(tt * math.pi) * 26
            pts.append((px, py))
        line(d, pts, fill=(240, 200, 90), width=S)
        for dx, dy in [(0, -7), (5, -5), (7, 0), (5, 5), (0, 7), (-5, 5),
                       (-7, 0), (-5, -5)]:
            line(d, [(x + ax, y + ay), (x + ax + dx, y + ay + dy)],
                 fill=(255, 170, 60), width=S)
        ell(d, (x + ax - 3, y + ay - 3, x + ax + 3, y + ay + 3),
            fill=(255, 220, 130))
    chip(d, x + 8, y + h - 17, "3 DOWN OVER RIYADH")


def ill_bepi(d, b):
    x, y, w, h = b[0], b[1], b[2] - b[0], b[3] - b[1]
    rect(d, b, fill=(10, 16, 30))
    for sx, sy in [(14, 12), (52, 8), (120, 10), (180, 16), (214, 8),
                   (90, 20), (160, 26)]:
        ell(d, (x + sx, y + sy, x + sx + 2, y + sy + 2), fill=(220, 220, 200))
    cx, cy, r = x + 62, y + 52, 24
    ell(d, (cx - r, cy - r, cx + r, cy + r), fill=(206, 128, 64))
    ell(d, (cx - 12, cy - 8, cx - 4, cy), fill=(178, 104, 52))
    ell(d, (cx + 4, cy + 6, cx + 12, cy + 14), fill=(178, 104, 52))
    ell(d, (cx + 8, cy - 14, cx + 14, cy - 8), fill=(178, 104, 52))
    # orbit ellipse + probe with solar panels
    d.ellipse([X(x + 18), X(y + 12), X(x + 218), X(y + 92)],
              outline=(235, 235, 225), width=S)
    px, py = x + 182, y + 26
    rect(d, (px - 5, py - 3, px + 5, py + 3), fill=(240, 240, 235),
         outline=INK, width=S)
    rect(d, (px - 17, py - 2, px - 6, py + 2), fill=(52, 90, 160))
    rect(d, (px + 6, py - 2, px + 17, py + 2), fill=(52, 90, 160))
    chip(d, x + 8, y + h - 17, "2ND EVER \u00b7 37-MIN BURN")


def ill_peru(d, b):
    # card-sized seismograph (box 189x40): small-amplitude trace + chip
    x, y, w, h = b[0], b[1], b[2] - b[0], b[3] - b[1]
    rect(d, b, fill=(240, 228, 198))
    pts = []
    import math as _m
    for i in range(61):
        px = x + 6 + i * (w - 12) / 60.0
        amp = 1.5 + 9 * _m.exp(-((i - 28) / 8.0) ** 2)
        py = y + 18 + _m.sin(i * 1.9) * amp
        pts.append((px, py))
    line(d, pts, fill=RED, width=int(1.4 * S))
    chip(d, x + 6, y + h - 15, "M6.7 \u00b7 00:09 UTC", size=7.5)


def ill_ashes(d, b):
    x, y, w, h = b[0], b[1], b[2] - b[0], b[3] - b[1]
    rect(d, b, fill=(116, 172, 92))
    # the Ashes urn: small cream vase on a plinth
    ux = x + 34
    ell(d, (ux + 2, y + 6, ux + 18, y + 12), fill=(250, 248, 240))
    poly(d, [(ux + 2, y + 9), (ux + 18, y + 9), (ux + 14, y + 26),
             (ux + 6, y + 26)], fill=(250, 248, 240))
    rect(d, (ux, y + 26, ux + 20, y + 30), fill=(250, 248, 240))
    rect(d, (ux - 3, y + 30, ux + 23, y + 33), fill=(200, 170, 120))
    txt(d, (x + w - 46, y + 10), "123", (SER_B, 15), fill=(255, 255, 255))
    chip(d, x + 6, y + h - 15, "WON IN 2 DAYS", size=7.5)


def ill_sparta(d, b):
    x, y, w, h = b[0], b[1], b[2] - b[0], b[3] - b[1]
    rect(d, b, fill=(70, 110, 140))
    # smoke plume above the burning deck
    for sx, sy, sr in [(118, 8, 7), (128, 12, 9), (112, 14, 6)]:
        ell(d, (x + sx - sr, y + sy - sr, x + sx + sr, y + sy + sr),
            fill=(120, 120, 118))
    poly(d, [(x + 122, y + 16), (x + 128, y + 8), (x + 134, y + 16)],
         fill=(255, 150, 40))
    # hull + containers
    poly(d, [(x + 30, y + 26), (x + 160, y + 26), (x + 150, y + 36),
             (x + 40, y + 36)], fill=(40, 44, 52))
    rect(d, (x + 48, y + 18, x + 72, y + 26), fill=(178, 60, 50))
    rect(d, (x + 76, y + 18, x + 100, y + 26), fill=(52, 90, 160))
    rect(d, (x + 104, y + 20, x + 118, y + 26), fill=(200, 170, 90))
    chip(d, x + 6, y + h - 15, "16 CREW SAFE", size=7.5)


def ill_gaza(d, b):
    x, y, w, h = b[0], b[1], b[2] - b[0], b[3] - b[1]
    rect(d, b, fill=(214, 192, 168))
    for bx, bw, bh in [(10, 30, 18), (44, 24, 26), (72, 32, 16),
                       (108, 26, 24), (138, 30, 14)]:
        rect(d, (x + bx, y + h - bh, x + bx + bw, y + h), fill=(64, 60, 56))
    ell(d, (x + 48, y + 4, x + 60, y + 14), fill=(150, 148, 144))
    ell(d, (x + 56, y + 8, x + 70, y + 20), fill=(150, 148, 144))
    chip(d, x + 6, y + 5, "3 KILLED", size=7.5)


def ill_drones(d, b):
    x, y, w, h = b[0], b[1], b[2] - b[0], b[3] - b[1]
    rect(d, b, fill=NAVY)
    for dx, dy in [(40, 14), (95, 10), (148, 16)]:
        rect(d, (x + dx - 5, y + dy - 2, x + dx + 5, y + dy + 2),
             fill=(220, 220, 215))
        line(d, [(x + dx - 11, y + dy - 4), (x + dx + 11, y + dy - 4)],
             fill=(220, 220, 215), width=S)
        ell(d, (x + dx - 13, y + dy - 6, x + dx - 9, y + dy - 2),
            fill=(240, 200, 90))
        ell(d, (x + dx + 9, y + dy - 6, x + dx + 13, y + dy - 2),
            fill=(240, 200, 90))
    chip(d, x + 6, y + h - 15, "117 DOWN", size=7.5)


def ill_plane(d, b):
    x, y, w, h = b[0], b[1], b[2] - b[0], b[3] - b[1]
    rect(d, b, fill=(168, 204, 236))
    poly(d, [(x + 30, y + 24), (x + 120, y + 18), (x + 150, y + 22),
              (x + 122, y + 27), (x + 34, y + 29)], fill=(245, 245, 245))
    poly(d, [(x + 44, y + 23), (x + 58, y + 10), (x + 66, y + 10),
              (x + 60, y + 23)], fill=(210, 60, 55))
    poly(d, [(x + 88, y + 25), (x + 104, y + 33), (x + 94, y + 33),
              (x + 80, y + 26)], fill=(120, 130, 145))
    rect(d, (x, y + h - 7, x + w, y + h), fill=(70, 74, 80))
    for i in range(9):
        rect(d, (x + 10 + i * 21, y + h - 4.6, x + 20 + i * 21, y + h - 3.4),
             fill=(240, 240, 240))
    chip(d, x + 6, y + 5, "146 SAFE", size=7.5)


def ill_bitcoin(d, b):
    x, y, w, h = b[0], b[1], b[2] - b[0], b[3] - b[1]
    rect(d, b, fill=(22, 22, 28))
    heights = [10, 14, 12, 19, 17, 24, 22, 29, 27, 33]
    for i, bh in enumerate(heights):
        bx = x + 12 + i * 13
        rect(d, (bx, y + h - 4 - bh, bx + 8, y + h - 4), fill=(198, 60, 52))
    txt(d, (x + w - 52, y + 6), "BTC", (SAN_B, 11), fill=(245, 180, 60))
    txt(d, (x + w - 62, y + 20), "LOW $55,130", (SAN_B, 9), fill=(230, 90, 80))


def ill_rahul(d, b):
    x, y, w, h = b[0], b[1], b[2] - b[0], b[3] - b[1]
    rect(d, b, fill=(116, 172, 92))
    for i in range(3):
        rect(d, (x + 30 + i * 6, y + 8, x + 33 + i * 6, y + 30),
             fill=(232, 214, 160))
    line(d, [(x + 74, y + 6), (x + 96, y + 30)], fill=(150, 100, 55),
         width=int(3 * S))
    ell(d, (x + 128, y + 12, x + 138, y + 22), fill=(200, 40, 40))
    txt(d, (x + w - 46, y + 10), "136", (SER_B, 15), fill=(255, 255, 255))


def ill_f1(d, b):
    x, y, w, h = b[0], b[1], b[2] - b[0], b[3] - b[1]
    rect(d, b, fill=(88, 94, 104))
    pts = [(x + 4 + i * 6, y + 30 - 12 * math.sin(i / 5.2)) for i in range(31)]
    line(d, pts, fill=(235, 235, 235), width=int(2 * S))
    cx, cy = x + 108, y + 16
    poly(d, [(cx - 26, cy + 6), (cx - 8, cy - 2), (cx + 10, cy - 2),
              (cx + 24, cy + 6)], fill=(20, 20, 24))
    rect(d, (cx - 30, cy + 6, cx + 28, cy + 9), fill=(20, 20, 24))
    ell(d, (cx - 18, cy + 7, cx - 8, cy + 15), fill=(10, 10, 12))
    ell(d, (cx + 12, cy + 7, cx + 22, cy + 15), fill=(10, 10, 12))
    txt(d, (x + w - 62, y + 6), "1:33.893", (SAN_B, 10), fill=(255, 255, 255))


def ill_hormuz(d, b):
    x, y, w, h = b[0], b[1], b[2] - b[0], b[3] - b[1]
    rect(d, b, fill=(66, 128, 168))
    for i in range(5):
        line(d, [(x + 8 + i * 8, y + 32 + (i % 2) * 3),
                  (x + 22 + i * 8, y + 32 + (i % 2) * 3)],
             fill=(200, 228, 244), width=S)
    poly(d, [(x + 56, y + 26), (x + 130, y + 26), (x + 120, y + 33),
              (x + 64, y + 33)], fill=(40, 44, 52))
    rect(d, (x + 84, y + 18, x + 104, y + 26), fill=(60, 64, 74))
    poly(d, [(x + 150, y + 8), (x + 164, y + 12), (x + 150, y + 16),
              (x + 154, y + 12)], fill=(30, 30, 36))
    chip(d, x + 6, y + 5, "IRAN'S CLAIM", size=7.5)


ILL = {"cop": ill_cop, "riyadh": ill_riyadh, "bepi": ill_bepi,
       "peru": ill_peru, "plane": ill_plane, "ashes": ill_ashes,
       "sparta": ill_sparta, "rahul": ill_rahul, "f1": ill_f1,
       "bitcoin": ill_bitcoin, "drones": ill_drones, "hormuz": ill_hormuz,
       "gaza": ill_gaza}

# ---------------------------------------------------------------- verify
def wrap(s, font, maxw):
    words, lines, cur = s.split(), [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if tw(t, font) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def verify():
    problems = []
    if TOTAL_STORIES != 34:
        problems.append(f"story count {TOTAL_STORIES} != 34")
    if sum(n for _, n in REGIONS) != TOTAL_STORIES:
        problems.append("region counts do not sum to total stories")
    hero_tw = 612 - 248 - 8
    for (num, kick, head, summ, src, ill, lon, lat) in HEROES:
        for ln in head:
            if tw(ln, (SER_B, 19.5)) > hero_tw:
                problems.append(f"hero {num} headline too wide: {ln}")
        for ln in summ:
            if tw(ln, (SER, 10.5)) > hero_tw:
                problems.append(f"hero {num} summary too wide: {ln}")
        if tw(kick, (SAN_B, 9.5)) + tw(src, (SAN_I, 8.5)) + 12 > hero_tw:
            problems.append(f"hero {num} kicker+source too wide")
        if not point_in_land(lon, lat):
            problems.append(f"hero {num} pin off land at {lon},{lat}")
    card_tw = 189 - 14
    for (num, kick, head, summ, src, ill, lon, lat) in CARDS:
        for ln in head:
            if tw(ln, (SER_B, 12)) > card_tw:
                problems.append(f"card {num} headline too wide: {ln}")
        for ln in summ:
            if tw(ln, (SER, 9)) > card_tw:
                problems.append(f"card {num} summary too wide: {ln}")
        if tw(kick, (SAN_B, 8)) + tw(src, (SAN_I, 7.5)) + 8 > card_tw:
            problems.append(f"card {num} kicker+source too wide")
        if not point_in_land(lon, lat):
            problems.append(f"card {num} pin off land at {lon},{lat}")
    for (num, city, text) in BRIEFS:
        w = tw(str(num), (SER_B, 9.5)) + 5 + tw(city, (SAN_B, 9)) + 5 \
            + tw(text, (SER, 9.2))
        if w > 312:
            problems.append(f"brief {num} too wide ({w:.0f}px): {city}")
    for (big, cap) in BIG_NUMBERS:
        if len(wrap(cap, (SAN, 8.5), 150)) > 2:
            problems.append(f"big number caption wraps >2 lines: {big}")
        if tw(big, (SER_B, 25)) > 154:
            problems.append(f"big number too wide: {big}")
    for ln in DATE_CHECK:
        if tw(ln, (SER, 9.3)) > 940:
            problems.append(f"date check line too wide: {ln[:40]}...")
    nums = [h[0] for h in HEROES] + [c[0] for c in CARDS] + [b[0] for b in BRIEFS]
    if nums != list(range(1, 35)):
        problems.append(f"numbering broken: {nums}")
    return problems


# ---------------------------------------------------------------- render
def render():
    img = Image.new("RGB", (W * S, H * S), CREAM)
    d = ImageDraw.Draw(img)

    # strap
    txt(d, (M, 13), "THE WORLD IN ONE DAY", (SAN_B, 10.5), fill=RED)
    r = "SATURDAY'S NEWS \u00b7 ONE PAGE \u00b7 34 STORIES \u00b7 6 REGIONS"
    txt(d, (W - M - tw(r, (SAN_B, 9.5)), 13.5), r, (SAN_B, 9.5))
    line(d, [(M, 30), (W - M, 30)], fill=INK, width=int(1.6 * S))
    line(d, [(M, 33.5), (W - M, 33.5)], fill=INK, width=S)

    # masthead + standfirst
    mast = "Saturday 21 November 2026"
    txt(d, ((W - tw(mast, (SER_B, 60))) / 2, 40), mast, (SER_B, 60))
    sf = ("Climate summit ends with no deal \u00b7 Missiles shot down over "
          "Riyadh \u00b7 BepiColombo reaches Mercury")
    txt(d, ((W - tw(sf, (SER_I, 14.5))) / 2, 106), sf, (SER_I, 14.5),
        fill=DRED)

    # big numbers strip
    by, bh = 128, 62
    rect(d, (M, by, W - M, by + bh), fill=PAPER, outline=INK, width=S)
    cell = CW / 6.0
    for i, (big, cap) in enumerate(BIG_NUMBERS):
        cx = M + i * cell
        if i:
            line(d, [(cx, by + 6), (cx, by + bh - 6)], fill=LINE, width=S)
        txt(d, (cx + 9, by + 5), big, (SER_B, 25), fill=RED)
        for j, ln in enumerate(wrap(cap, (SAN, 8.5), 148)):
            txt(d, (cx + 9, by + 36 + j * 10.5), ln, (SAN, 8.5), fill=MUTE)

    # region chips
    cy = 198
    cx = M
    for (name, n), col in zip(REGIONS, REGION_COLORS):
        label = f"{name} {n}"
        wch = tw(label, (SAN_B, 9)) + 13
        rect(d, (cx, cy, cx + wch, cy + 15), fill=col)
        txt(d, (cx + 6.5, cy + 2.6), label, (SAN_B, 9),
            fill=(255, 255, 255))
        cx += wch + 5
    note = "ALL STORIES: SAT 21 NOV 2026, ANY TIME ZONE"
    txt(d, (W - M - tw(note, (SAN_B, 8.5)), cy + 3), note, (SAN_B, 8.5))

    # heroes (left) + map (right)
    top = 224
    for i, (num, kick, head, summ, src, ill, lon, lat) in enumerate(HEROES):
        hy = top + i * 108
        rect(d, (M, hy, M + 612, hy + 100), fill=PAPER, outline=LINE, width=S)
        ILL[ill](d, (M, hy, M + 236, hy + 100))
        tx = M + 248
        txt(d, (tx, hy + 7), kick, (SAN_B, 9.5), fill=RED)
        txt(d, (tx + 356 - tw(src, (SAN_I, 8.5)), hy + 7.5), src,
            (SAN_I, 8.5), fill=MUTE)
        for j, ln in enumerate(head):
            txt(d, (tx, hy + 22 + j * 22.5), ln, (SER_B, 19.5))
        for j, ln in enumerate(summ):
            txt(d, (tx, hy + 71 + j * 12.5), ln, (SER, 10.5), fill=(52, 48, 40))

    mx, my, mw, mh = 646, 224, 352, 316
    rect(d, (mx, my, mx + mw, my + mh), fill=NAVY)
    txt(d, (mx + 9, my + 7), "WHERE IT HAPPENED", (SAN_B, 10),
        fill=(255, 255, 255))
    pl = "Pins 1\u201313 (Lead & Feature)"
    txt(d, (mx + mw - 9 - tw(pl, (SAN, 8)), my + 8), pl, (SAN, 8),
        fill=(190, 205, 225))
    box = (mx + 8, my + 30, mw - 16, 218)
    for poly_ll in LAND:
        pts = [project(lon, lat, (box[0], box[1], box[2], box[3]))
               for lon, lat in poly_ll]
        poly(d, pts, fill=SAND)
    pins = [(h[0], h[6], h[7]) for h in HEROES] + \
           [(c[0], c[6], c[7]) for c in CARDS]
    pin_offset = {1: (-14, 5), 2: (9, 8), 3: (-8, -4), 7: (7, -13),
                  11: (-6, 7), 12: (12, -5), 13: (7, -3)}  # display nudges for crowded pins
    for num, lon, lat in pins:
        px, py = project(lon, lat, (box[0], box[1], box[2], box[3]))
        if num in pin_offset:
            px += pin_offset[num][0]
            py += pin_offset[num][1]
        ell(d, (px - 8.5, py - 8.5, px + 8.5, py + 8.5), fill=RED,
            outline=(255, 255, 255), width=S)
        txt(d, (px, py - 5.5), str(num), (SAN_B, 8.5),
            fill=(255, 255, 255), anchor="ma")
    ly = my + 262
    ell(d, (mx + 10, ly, mx + 20, ly + 10), fill=RED)
    txt(d, (mx + 25, ly), "1\u20133 Lead stories", (SAN, 8.5),
        fill=(235, 238, 244))
    ell(d, (mx + 118, ly, mx + 128, ly + 10), fill=RED)
    txt(d, (mx + 133, ly), "4\u201313 Feature stories", (SAN, 8.5),
        fill=(235, 238, 244))
    txt(d, (mx + 10, ly + 16), "Pin 10 = world markets (New York).",
        (SAN_I, 8.5), fill=(190, 205, 225))
    txt(d, (mx + 10, ly + 30),
        "Each number is the story with that number on this page.",
        (SAN_I, 8.5), fill=(190, 205, 225))

    # cards 2 rows x 5
    for idx, (num, kick, head, summ, src, ill, lon, lat) in enumerate(CARDS):
        r_i, c_i = divmod(idx, 5)
        cxx = M + c_i * 195
        cyy = 552 + r_i * 115
        rect(d, (cxx, cyy, cxx + 189, cyy + 109), fill=PAPER, outline=LINE,
             width=S)
        ILL[ill](d, (cxx, cyy, cxx + 189, cyy + 40))
        txt(d, (cxx + 7, cyy + 45), kick, (SAN_B, 8), fill=RED)
        txt(d, (cxx + 182 - tw(src, (SAN_I, 7.5)), cyy + 45.5), src,
            (SAN_I, 7.5), fill=MUTE)
        for j, ln in enumerate(head):
            txt(d, (cxx + 7, cyy + 57 + j * 14.5), ln, (SER_B, 12))
        for j, ln in enumerate(summ):
            txt(d, (cxx + 7, cyy + 88 + j * 10), ln, (SER, 9),
                fill=(52, 48, 40))

    # briefs
    txt(d, (M, 786), "ALSO ON SATURDAY 21 NOVEMBER \u2014 21 MORE STORIES",
        (SAN_B, 10.5))
    wb = "World Briefs (14\u201334)"
    txt(d, (W - M - tw(wb, (SAN_I, 9)), 787), wb, (SAN_I, 9), fill=MUTE)
    line(d, [(M, 802), (W - M, 802)], fill=LINE, width=S)
    cols = [BRIEFS[0:7], BRIEFS[7:14], BRIEFS[14:21]]
    for ci, col in enumerate(cols):
        bx = M + ci * 328
        for ri, (num, city, text) in enumerate(col):
            yy = 812 + ri * 16
            txt(d, (bx, yy), str(num), (SER_B, 9.5), fill=RED)
            x2 = bx + tw(str(num), (SER_B, 9.5)) + 5
            txt(d, (x2, yy + 0.5), city, (SAN_B, 9))
            x3 = x2 + tw(city, (SAN_B, 9)) + 5
            txt(d, (x3, yy + 0.5), text, (SER, 9.2), fill=(52, 48, 40))

    # date check
    dy, dh = 930, 58
    rect(d, (M, dy, W - M, dy + dh), fill=(250, 244, 228), outline=DRED,
         width=int(1.5 * S))
    cw_ = tw("DATE CHECK", (SAN_B, 9.5)) + 13
    rect(d, (M + 8, dy + 7, M + 8 + cw_, dy + 22), fill=RED)
    txt(d, (M + 14.5, dy + 9.6), "DATE CHECK", (SAN_B, 9.5),
        fill=(255, 255, 255))
    txt(d, (M + 16 + cw_, dy + 8.5),
        "First reported before Saturday \u2014 not shown as Saturday's news:",
        (SER_B, 10), fill=DRED)
    for j, ln in enumerate(DATE_CHECK):
        txt(d, (M + 10, dy + 25 + j * 11), ln, (SER, 9.3), fill=(52, 48, 40))

    # footer
    txt(d, (M, 997),
        "Every story here happened, or was first reported, on Saturday 21 "
        "November 2026 in at least one time zone. Claims are attributed.",
        (SER_I, 8.5), fill=MUTE)
    srcs = "Sources named beside each story \u00b7 Original vector drawings"
    txt(d, (W - M - tw(srcs, (SAN, 8.5)), 997), srcs, (SAN, 8.5), fill=MUTE)

    return img.resize((W, H), Image.LANCZOS)


def main():
    problems = verify()
    if problems:
        for p in problems:
            print("VERIFY FAIL:", p)
        raise SystemExit(1)
    print("VERIFY OK: 34 stories, counts consistent, all pins on land, "
          "no text overflow")
    img = render()
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, "entry.png")
    img.save(out, format="PNG", optimize=True)
    print("wrote", out, os.path.getsize(out), "bytes")
    if os.path.isdir("/output"):
        img.save("/output/entry.png", format="PNG", optimize=True)
        print("wrote /output/entry.png")


if __name__ == "__main__":
    main()
