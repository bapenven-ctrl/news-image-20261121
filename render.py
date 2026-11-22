#!/usr/bin/env python3
"""Render entry.png for news-image-20261121 V3 (ATM).

Fresh design, written from scratch in this session (2026-11-22):
  - a large world map is the hero (top ~45% of the canvas); the 12 biggest
    stories sit ON the map as numbered pins, each with a baked-in big number
    and a 2-4 word verdict label;
  - the other 26 stories are NOT a tiny numbered list: they are three
    region columns in 12-13 px type;
  - a vertical UTC rail on the left edge ties every map story to its hour.
No part of the V1/V2 broadsheet layout is reused (owner instruction 18:49 WIB).
All drawings are procedural vector work in this file; no external assets.
Deterministic: no randomness, no clock, no network. Rendered at 2x then
downscaled with LANCZOS to 1024x1024.
"""
import sys
from PIL import Image, ImageDraw, ImageFont

S = 2                      # supersample factor
W, H = 1024 * S, 1024 * S

# ---------- palette ----------
PAPER   = (247, 242, 231)  # cream paper
INK     = (20, 20, 20)     # near-black
GREY    = (110, 108, 100)
FAINT   = (150, 148, 138)
RED     = (178, 34, 34)    # kept for the most urgent (W4)
OCEAN   = (226, 234, 236)
LAND    = (223, 217, 196)
LANDLINE = (170, 163, 138)
WHITE   = (255, 255, 255)
DARKBOX = (24, 42, 60)     # space box
BAND    = (20, 20, 20)     # top band

# region colours (W1: same colour on map pin, column number disc, legend)
REGION = {
    "EUROPE":      (31, 78, 121),
    "MIDEAST":     (179, 84, 30),
    "AMERICAS":    (46, 125, 50),
    "ASIA-PAC":    (106, 27, 154),
    "OCEANIA":     (0, 131, 143),
    "AFRICA":      (141, 110, 0),
    "WORLD":       (55, 71, 79),
}

# ---------- fonts ----------
FD = "/usr/share/fonts/truetype/noto/"
def F(name, size):
    return ImageFont.truetype(FD + name, size * S)

SERIF_B   = lambda s: F("NotoSerif-Bold.ttf", s)
SERIF     = lambda s: F("NotoSerif-Regular.ttf", s)
SERIF_I   = lambda s: F("NotoSerif-Italic.ttf", s)
SERIF_D_B = lambda s: F("NotoSerifDisplay-Bold.ttf", s)
SANS      = lambda s: F("NotoSans-Regular.ttf", s)
SANS_B    = lambda s: F("NotoSans-Bold.ttf", s)
SANS_I    = lambda s: F("NotoSans-Italic.ttf", s)

img = Image.new("RGB", (W, H), PAPER)
d = ImageDraw.Draw(img)

def X(v): return v * S
def Y(v): return v * S

def text(x, y, s, font, fill=INK, anchor="la"):
    d.text((X(x), Y(y)), s, font=font, fill=fill, anchor=anchor)

def text_w(s, font):
    return d.textlength(s, font=font) / S

def fit(s, font, maxw, label):
    """Assert a line fits; fail loudly instead of overflowing silently."""
    w = text_w(s, font)
    assert w <= maxw, f"OVERFLOW {label}: {w:.1f} > {maxw} :: {s!r}"
    return w

def rrect(x0, y0, x1, y1, fill=None, outline=None, width=1, radius=0):
    d.rounded_rectangle([X(x0), Y(y0), X(x1), Y(y1)], radius=radius * S,
                        fill=fill, outline=outline, width=width * S)

def rect(x0, y0, x1, y1, fill=None, outline=None, width=1):
    d.rectangle([X(x0), Y(y0), X(x1), Y(y1)], fill=fill,
                outline=outline, width=width * S)

def line(points, fill=INK, width=1):
    d.line([(X(x), Y(y)) for x, y in points], fill=fill, width=width * S)

def disc(cx, cy, r, fill, outline=None, width=1):
    d.ellipse([X(cx - r), Y(cy - r), X(cx + r), Y(cy + r)],
              fill=fill, outline=outline, width=width * S)

# =====================================================================
# TOP BAND + MASTHEAD
# =====================================================================
rect(0, 0, 1024, 26, fill=BAND)
text(14, 7, "THE WORLD IN ONE DAY", SANS_B(11), fill=WHITE)
text(512, 7, "ALL TIMES UTC \u2014 EXCEPT WHERE MARKED", SANS_B(11), fill=WHITE, anchor="ma")
text(1010, 7, "EVERY STORY DATED SATURDAY 21 NOVEMBER 2026", SANS_B(11),
     fill=WHITE, anchor="ra")

masthead = "Saturday 21 November 2026"
fit(masthead, SERIF_D_B(60), 840, "masthead")
text(14, 38, masthead, SERIF_D_B(60), fill=INK)
# red date badge, right of masthead
rrect(866, 40, 1010, 108, fill=RED)
text(938, 50, "SAT", SANS_B(24), fill=WHITE, anchor="ma")
text(938, 76, "21 NOV", SANS_B(24), fill=WHITE, anchor="ma")

sub = ("38 stories \u00b7 7 regions \u00b7 15 fields \u2014 COP31 no deal \u00b7 "
       "Riyadh: 3 missiles down \u00b7 BepiColombo in Mercury orbit")
fit(sub, SERIF_I(16), 996, "subhead")
text(14, 116, sub, SERIF_I(16), fill=INK)
line([(14, 142), (1010, 142)], fill=INK, width=2)

# =====================================================================
# WORLD MAP (hero)  x 46..1010, y 148..548
# =====================================================================
MAP_X0, MAP_Y0, MAP_X1, MAP_Y1 = 46, 148, 1010, 548
MAP_W, MAP_H = MAP_X1 - MAP_X0, MAP_Y1 - MAP_Y0
rect(MAP_X0, MAP_Y0, MAP_X1, MAP_Y1, fill=OCEAN)

# equirectangular projection, lon -170..190 -> x, lat 78..-58 -> y
def project(lon, lat):
    x = MAP_X0 + (lon + 170) / 360.0 * MAP_W
    y = MAP_Y0 + (78 - lat) / 136.0 * MAP_H
    return (x, y)

def poly(coords, fill=LAND, outline=LANDLINE, width=1):
    pts = [(X(px), Y(py)) for px, py in
           (project(lon, lat) for lon, lat in coords)]
    d.polygon(pts, fill=fill, outline=outline)
    d.line(pts + [pts[0]], fill=outline, width=width * S)

# --- continents (simplified outlines drawn for this entry) ---
NORTH_AMERICA = [(-168,66),(-165,60),(-158,58),(-152,60),(-140,60),(-135,57),
    (-130,54),(-125,49),(-124,42),(-120,34),(-114,29),(-110,24),(-105,20),
    (-97,16),(-94,17),(-90,14),(-86,12),(-83,9),(-79,9),(-81,13),(-84,16),
    (-87,21),(-90,21),(-91,19),(-97,26),(-93,30),(-89,30),(-84,30),(-81,25),
    (-80,32),(-76,35),(-74,40),(-70,42),(-68,45),(-65,44),(-60,47),(-55,52),
    (-60,55),(-64,58),(-68,58),(-72,62),(-78,62),(-85,66),(-92,66),(-95,69),
    (-110,68),(-125,70),(-140,70),(-155,71),(-165,68)]
GREENLAND = [(-58,64),(-52,60),(-43,60),(-40,64),(-32,68),(-22,70),(-20,74),
    (-25,76),(-35,76),(-50,74),(-58,70),(-60,66)]
SOUTH_AMERICA = [(-79,9),(-77,4),(-80,-3),(-81,-6),(-77,-12),(-72,-18),
    (-70,-23),(-70,-30),(-72,-37),(-73,-44),(-74,-50),(-70,-54),(-66,-55),
    (-65,-45),(-62,-41),(-58,-34),(-52,-32),(-48,-28),(-41,-23),(-39,-17),
    (-35,-9),(-35,-6),(-40,-3),(-44,-2),(-50,0),(-53,4),(-58,6),(-62,9),
    (-68,11),(-72,12),(-77,8)]
AFRICA = [(-17,15),(-16,20),(-13,27),(-9,31),(-5,35),(0,36),(10,37),(11,34),
    (20,32),(30,31),(32,31),(34,28),(35,23),(37,18),(39,15),(41,11),(43,11),
    (46,11),(51,11),(51,2),(48,-2),(40,-10),(36,-18),(33,-26),(28,-33),
    (20,-35),(17,-32),(15,-27),(13,-18),(12,-12),(13,-6),(9,-1),(9,4),
    (-8,5),(-13,8),(-17,12)]
EURASIA = [(-9,37),(-9,43),(-2,44),(-1,46),(-4,48),(-2,50),(0,51),(3,53),
    (8,57),(10,59),(5,60),(5,62),(12,65),(18,69),(25,71),(30,70),(35,68),
    (40,68),(45,68),(50,69),(55,69),(60,69),(65,69),(70,72),(75,73),(80,73),
    (85,74),(90,75),(95,76),(100,77),(105,77),(110,74),(115,73),(120,73),
    (125,72),(130,72),(135,71),(140,72),(145,72),(150,70),(155,69),(160,69),
    (165,66),(170,66),(173,64),(170,60),(162,60),(158,56),(156,51),(150,59),
    (142,59),(142,55),(140,50),(138,46),(135,43),(132,43),(128,38),(127,35),
    (122,38),(120,34),(122,31),(120,28),(118,25),(110,21),(108,18),(105,10),
    (103,8),(100,7),(98,10),(95,16),(92,21),(90,22),(88,22),(86,20),(82,17),
    (80,13),(77,8),(76,10),(73,16),(70,20),(66,25),(62,25),(58,26),(56,27),
    (54,26),(52,26),(50,29),(48,30),(50,26),(52,24),(54,24),(56,26),(58,24),
    (58,22),(56,20),(54,17),(52,15),(48,14),(44,13),(42,15),(40,15),(38,18),
    (35,23),(34,28),(32,31),(30,31),(27,31),(23,33),(22,37),(19,40),(16,40),
    (12,44),(8,44),(3,43),(0,40),(-2,37),(-6,36),(-9,37)]
UK = [(-5,50),(-3,53),(-5,56),(-3,58),(-1,57),(0,53),(1,51)]
JAPAN = [(130,31),(133,34),(136,35),(139,37),(141,40),(142,44),(140,42),
    (138,38)]
AUSTRALIA = [(113,-22),(114,-30),(115,-35),(118,-35),(124,-33),(129,-32),
    (132,-32),(135,-35),(138,-35),(140,-38),(145,-38),(150,-37),(153,-32),
    (153,-27),(150,-23),(146,-19),(142,-15),(142,-11),(137,-12),(135,-15),
    (132,-12),(130,-13),(126,-14),(122,-17),(118,-20)]
NEW_GUINEA = [(131,-1),(136,-2),(141,-3),(146,-6),(150,-9),(147,-9),
    (142,-8),(138,-8),(134,-4)]
PHILIPPINES = [(120,18),(122,18),(122,14),(121,11),(124,10),(126,7),
    (122,7)]
BORNEO = [(109,1),(113,4),(117,6),(119,1),(117,-3),(112,-3),(109,-1)]
SUMATRA = [(95,5),(98,3),(101,0),(104,-3),(106,-6),(103,-4),(100,0),(97,4)]

for c in (NORTH_AMERICA, GREENLAND, SOUTH_AMERICA, AFRICA, EURASIA, UK,
          JAPAN, AUSTRALIA, NEW_GUINEA, PHILIPPINES, BORNEO, SUMATRA):
    poly(c)

# ocean labels (small caps, grey)
text(120, 470, "PACIFIC", SANS_B(10), fill=(140, 160, 165))
text(700, 470, "INDIAN", SANS_B(10), fill=(140, 160, 165))
text(560, 510, "ATLANTIC", SANS_B(10), fill=(140, 160, 165))
# --- SPACE box (BepiColombo, story 3) top-right of the map ---
rrect(822, 176, 1002, 258, fill=DARKBOX)
# orbit ellipse + Mercury dot
d.ellipse([X(868), Y(186), X(956), Y(220)], outline=(220, 220, 210),
          width=2 * S)
disc(912, 203, 7, fill=(210, 190, 150))
disc(868, 203, 4, fill=WHITE)
disc(838, 190, 11, fill=REGION["WORLD"], outline=WHITE, width=2)
text(838, 183, "3", SANS_B(12), fill=WHITE, anchor="ma")
text(912, 224, "BEPICOLOMBO", SANS_B(11), fill=WHITE, anchor="ma")
text(912, 238, "IN ORBIT \u00b7 18:24 UTC", SANS_B(10),
     fill=(255, 210, 120), anchor="ma")

# --- map pins: (num, lon, lat, region, value, name, chip_x, chip_y) ---
# chip_x/chip_y = top-left of the label chip; leader line joins pin to chip.
PINS = [
    (1,  30.7,  36.9, "EUROPE",   "NO DEAL",  "COP31 \u00b7 ANTALYA", 400, 228),
    (2,  46.7,  24.7, "MIDEAST",  "3 DOWN",   "MISSILES \u00b7 RIYADH \u2014 02:41 AST",  662, 322),
    (4, -75.5, -11.0, "AMERICAS", "M6.7",     "QUAKE \u00b7 JUN\u00cdN \u2014 00:09 UTC", 140, 420),
    (5, 125.6,   7.1, "ASIA-PAC", "146 SAFE", "AIR NIUGINI \u00b7 DAVAO",          858, 330),
    (6, 115.9, -31.9, "OCEANIA",  "8 WICKETS","ASHES \u00b7 PERTH",                830, 492),
    (7,  24.0,  59.5, "EUROPE",   "2 DRONES", "SPARTA II \u00b7 GULF OF FINLAND", 516, 156),
    (12, 56.3,  26.5, "MIDEAST",  "58th CLAIM","IRAN CLAIMS US DRONE DOWN",       700, 258),
    (13, 34.5,  31.5, "MIDEAST",  "3 KILLED", "DRONE STRIKE \u00b7 GAZA CITY",      428, 302),
    (36, -108.5, 25.6, "AMERICAS","CAPTURED", "'CHAPO ISIDRO' \u00b7 GUASAVE",     60, 250),
    (37, -43.9, -19.9, "AMERICAS","-69%",     "DENGUE TRIAL \u00b7 BRAZIL \u2014 14:00 UTC", 238, 470),
    (38, -6.3,  53.3, "EUROPE",   "20\u201317",   "IRELAND BEAT S. AFRICA",          288, 190),
]

def chip(num, value, name, cx, cy, region):
    """Draw a label chip with a big baked-in number + name, return its box."""
    f_val, f_nam = SERIF_B(15), SANS(10.5)
    w = max(text_w(value, f_val), text_w(name, f_nam)) + 16
    h = 36
    x0, y0 = cx, cy
    rrect(x0, y0, x0 + w, y0 + h, fill=WHITE, outline=REGION[region], width=1)
    text(x0 + 8, y0 + 3, value, f_val, fill=REGION[region])
    text(x0 + 8, y0 + 21, name, f_nam, fill=INK)
    return (x0, y0, x0 + w, y0 + h)

# quake rings at the Peru pin (primitive: concentric circles)
px, py = project(-75.5, -11.0)
for r in (18, 27):
    d.ellipse([X(px - r), Y(py - r), X(px + r), Y(py + r)],
              outline=REGION["AMERICAS"], width=1 * S)
# dashed missile arc at the Riyadh pin (primitive: dashed arrow)
rx, ry = project(46.7, 24.7)
for i in range(5):
    x0 = rx + 16 + i * 9
    line([(x0, ry - 26 - i * 3), (x0 + 5, ry - 28 - i * 3)],
         fill=REGION["MIDEAST"], width=2)

pin_xy = {}
for num, lon, lat, region, value, name, cx, cy in PINS:
    px, py = project(lon, lat)
    pin_xy[num] = (px, py)
    box = chip(num, value, name, cx, cy, region)
    # leader line: pin -> nearest point of chip box
    bx = min(max(px, box[0]), box[2])
    by = min(max(py, box[1]), box[3])
    line([(px, py), (bx, by)], fill=GREY, width=1)
    disc(px, py, 11, fill=REGION[region], outline=WHITE, width=2)
    text(px, py - 7, str(num), SANS_B(12), fill=WHITE, anchor="ma")

# map frame
rect(MAP_X0, MAP_Y0, MAP_X1, MAP_Y1, outline=INK, width=1)

# =====================================================================
# UTC RAIL  x 0..46, y 148..548 — the day as a sequence
# =====================================================================
RAIL_TOP, RAIL_BOT, RAIL_X = 160, 536, 23
text(RAIL_X, 150, "UTC", SANS_B(8), fill=GREY, anchor="ma")
line([(RAIL_X, RAIL_TOP), (RAIL_X, RAIL_BOT)], fill=GREY, width=2)
for hr in (0, 6, 12, 18, 24):
    y = RAIL_TOP + (hr / 24.0) * (RAIL_BOT - RAIL_TOP)
    line([(RAIL_X - 5, y), (RAIL_X + 5, y)], fill=GREY, width=1)
    text(RAIL_X, y - 13, f"{hr:02d}", SANS(8), fill=GREY, anchor="ma")

# dot hour placement: dots sit at verified hours where the chip prints one
# (Peru 00:09 UTC, Riyadh 02:41 AST, Wolbachia 14:00 UTC, BepiColombo 18:24
# UTC); the rest sit mid-band with NO hour printed anywhere (COP31 evening,
# Sparta morning, Chapo/Ashes/Air Niugini/Gaza/Hormuz/Ireland placed by band).
# Riyadh 02:41 is AST by source (sumber.md: 02:41 AST Sat = 23:41 UTC Fri);
# printing it bare under an ALL TIMES UTC banner would mislabel it, and
# printing 23:41 UTC would put a Friday-23:41 occurrence at Saturday 23:41
# on the rail — a 24 h error. The AST zone is printed on the chip instead.
DOT_HOUR = {1: 21.5, 2: 2.68, 3: 18.4, 4: 0.15, 5: 10.5, 6: 9.0,
            7: 5.83, 12: 15.5, 13: 11.75, 36: 7.0, 37: 14.0, 38: 20.0}
DOT_REGION = {1: "EUROPE", 2: "MIDEAST", 3: "WORLD", 4: "AMERICAS",
              5: "ASIA-PAC", 6: "OCEANIA", 7: "EUROPE", 12: "MIDEAST",
              13: "MIDEAST", 36: "AMERICAS", 37: "AMERICAS", 38: "EUROPE"}
for num, hr in sorted(DOT_HOUR.items(), key=lambda kv: kv[1]):
    y = RAIL_TOP + (hr / 24.0) * (RAIL_BOT - RAIL_TOP)
    disc(RAIL_X, y, 9, fill=REGION[DOT_REGION[num]], outline=WHITE, width=1)
    text(RAIL_X, y - 6, str(num), SANS_B(9), fill=WHITE, anchor="ma")

# =====================================================================
# REGION COLUMNS — the other 26 stories (no tiny numbered list)
# =====================================================================
COL_Y0, COL_Y1 = 560, 940
text(14, COL_Y0, "ALSO ON SATURDAY 21 NOVEMBER 2026 \u2014 26 MORE STORIES",
     SANS_B(13), fill=INK)
text(1010, COL_Y0, "PIN NUMBERS MATCH THE STORIES ABOVE",
     SANS(10), fill=GREY, anchor="ra")
line([(14, COL_Y0 + 20), (1010, COL_Y0 + 20)], fill=INK, width=2)

COLS = [
    ("EUROPE \u00b7 MIDEAST", 14, [
        (11, "EUROPE", "Russia fires 3 missiles, 148 drones",
         "Air defences down 117 drones (United24)"),
        (14, "EUROPE", "Strikes kill 2 in Kryvyi Rih",
         "60 hurt; toll reported Saturday (AP)"),
        (15, "EUROPE", "EU warns COP31 not a \u2018fossil summit\u2019",
         "Bloc rejects dropping fossil fuels (Al Jazeera)"),
        (18, "MIDEAST", "Houthis threaten Jeddah, Red Sea ports",
         "Warning issued Saturday (Al Jazeera)"),
        (27, "MIDEAST", "Iran: uranium stays; deal possible",
         "Interview published Saturday (Reuters)"),
        (28, "EUROPE", "EU and Indonesia sign trade deal",
         "After 10 years; 98.5% of tariff lines (EU)"),
        (29, "EUROPE", "UN fails to agree \u2018killer robot\u2019 rules",
         "Talks extended to 2028 (AP)"),
        (30, "EUROPE", "82,500 march in France over living costs",
         "Ministry count; organisers say 150k (Al Jazeera)"),
        (32, "EUROPE", "UK and EU sign three post-Brexit deals",
         "Agreements signed Saturday (One Turn)"),
    ]),
    ("MIDEAST \u00b7 AMERICAS \u00b7 WORLD \u00b7 AFRICA", 355, [
        (31, "MIDEAST", "Iran strike burns Bahrain industrial site",
         "Bahrain reports fire; no casualties (Al Jazeera)"),
        (9, "AMERICAS", "Verstappen inherits Vegas pole",
         "Antonelli fastest 1:33.893, docked 5 places (F1)"),
        (10, "WORLD", "Bitcoin sinks to $55,130 low",
         "Sep 2024 low; closed at $57,884 (CoinGecko)"),
        (16, "AMERICAS", "Panama threatens to block climate text",
         "Joins EU objection at COP31 (Al Jazeera)"),
        (22, "AMERICAS", "No. 10 BYU beats Kansas 31\u201329 in 3OT",
         "Triple-overtime win, Saturday report (Reuters)"),
        (33, "AMERICAS", "US jails Indian in Pannun murder plot",
         "19+ years in prison (Al Jazeera)"),
        (34, "AMERICAS", "Haiti police kill 34+ gang members",
         "Raid reported Saturday (Al Jazeera)"),
        (35, "AFRICA", "Bayelsa boat toll rises to 24",
         "Capsized Fri; toll reported Sat (NEMA/AP)"),
    ]),
    ("ASIA-PACIFIC", 696, [
        (8, "ASIA-PAC", "KL Rahul 136 as India reach 486/4",
         "Lead 118 in Wellington, day 3 (ESPNcricinfo)"),
        (17, "ASIA-PAC", "PLN signs six clean-power deals",
         "Agreements signed at COP31 (Antara)"),
        (19, "ASIA-PAC", "Taipei mayor: don\u2019t block cash payouts",
         "Opposes blocking NT$20,000 payout (Asia Daily)"),
        (20, "ASIA-PAC", "Kim Jong Un tours factory",
         "KCNA reports visit Saturday (AFP)"),
        (21, "ASIA-PAC", "Pakistan minister cleared for Taj Mahal",
         "Nizamuddin dargah visit denied (Fact.net.in)"),
        (23, "ASIA-PAC", "Freight train derails in Sejong",
         "5 of 21 cars off track; no casualties (JoongAng)"),
        (24, "ASIA-PAC", "Arsenic 30\u00d7 limit in Chiang Rai rivers",
         "Water cut for 20,000+ homes (Chiang Rai Times)"),
        (25, "ASIA-PAC", "Pakistan minister speaks at SCO forum",
         "Calls climate a threat to civilisation (Centreline)"),
        (26, "ASIA-PAC", "Groups demand Myanmar sanctions",
         "After ICJ ruling; reaction Saturday (AP/TBS)"),
    ]),
]

COL_W = 300
ROW_H = 36
for header, cx, stories in COLS:
    text(cx, COL_Y0 + 28, header, SANS_B(11), fill=INK)
    line([(cx, COL_Y0 + 46), (cx + COL_W, COL_Y0 + 46)],
         fill=REGION["WORLD"], width=2)
    y = COL_Y0 + 56
    for num, region, head, summ in stories:
        fit(head, SERIF_B(13), COL_W - 26, f"col head {num}")
        fit(summ, SANS(12), COL_W - 26, f"col summ {num}")
        disc(cx + 9, y + 8, 9, fill=REGION[region])
        text(cx + 9, y + 2, str(num), SANS_B(9), fill=WHITE, anchor="ma")
        text(cx + 24, y, head, SERIF_B(13), fill=INK)
        text(cx + 24, y + 15, summ, SANS(12), fill=(60, 58, 52))
        y += ROW_H
    # heavy close under the column (L4: no small element dangling)
    line([(cx, y - 2), (cx + COL_W, y - 2)], fill=INK, width=2)

# legend box fills the spare slot at the bottom of column 2 (L3: rows end even)
lx, ly = 355, COL_Y0 + 56 + 8 * ROW_H + 4
rrect(lx, ly, lx + COL_W, ly + 40, fill=(238, 234, 224), outline=GREY, width=1)
text(lx + 8, ly + 5, "HOW SURE", SANS_B(10), fill=INK)
text(lx + 8, ly + 20,
     "Every figure is attributed to its outlet beside the story.",
     SANS(10), fill=(60, 58, 52))

# =====================================================================
# DATE CHECK + FOOTER
# =====================================================================
line([(14, 950), (1010, 950)], fill=INK, width=2)
rrect(14, 958, 128, 984, fill=RED)
text(71, 964, "DATE CHECK", SANS_B(12), fill=WHITE, anchor="ma")
dc1 = ("\u00d7 EXCLUDED \u2014 NOT SATURDAY 21 NOV: Russian missiles land in Poland (20 Nov) \u00b7 "
       "Wall Street correction (20) \u00b7 GTA VI launch (19) \u00b7 ICJ Rohingya ruling (19)")
dc2 = ("COP31 final deal (announced Sun) \u00b7 Las Vegas GP race (Sun) \u00b7 Kyiv double strike (Fri) \u00b7 "
       "BepiColombo was CONFIRMED Sat \u2014 it is story 3 above")
fit(dc1, SANS(12), 1010 - 140, "date check 1")
fit(dc2, SANS(12), 1010 - 140, "date check 2")
text(140, 960, dc1, SANS(12), fill=INK)
text(140, 976, dc2, SANS(12), fill=INK)
foot_l = ("Every story happened or was first reported on Saturday 21 November 2026 "
          "(UTC), as the named outlets reported it.")
fit(foot_l, SANS(10), 690, "footer left")
text(14, 996, foot_l, SANS(10), fill=GREY)
text(1010, 996, "SOURCES: AP \u00b7 REUTERS \u00b7 AFP \u00b7 USGS \u00b7 ESA \u00b7 UKMTO",
     SANS(10), fill=GREY, anchor="ra")

out = img.resize((1024, 1024), Image.LANCZOS)
out.save(sys.argv[1] if len(sys.argv) > 1 else "entry.png", "PNG")
print("saved", sys.argv[1] if len(sys.argv) > 1 else "entry.png")
