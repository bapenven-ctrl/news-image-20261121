#!/usr/bin/env python3
"""news-image-20261121 V2 renderer — draws the broadsheet from scratch.

Deterministic: no randomness, no clock, no network. Supersamples 2x, then
downscales with LANCZOS. Run: python3 render.py  ->  writes entry.png here.
Layout (1024 canvas): top bar / masthead / standfirst / big-numbers strip /
region chips / 3 heroes in a row / 2x5 card grid / map + 2-column briefs /
DATE CHECK strip / footer. All 35 stories are Saturday 21 November 2026.
"""
import os
from PIL import Image, ImageDraw, ImageFont

SS = 2                      # supersample factor
W, H = 1024, 1024           # final size
CW, CH = W * SS, H * SS     # working canvas

# ---- palette (cream broadsheet, ink, dark red, navy) ----
CREAM   = (247, 243, 232)
PAPER   = (250, 246, 236)
INK     = (24, 22, 20)
RED     = (164, 32, 28)
DARKRED = (128, 22, 20)
NAVY    = (16, 32, 56)
NAVY2   = (24, 48, 80)
GOLD    = (198, 142, 38)
TEAL    = (16, 110, 105)
GREEN   = (46, 110, 62)
BROWN   = (120, 84, 52)
GREY    = (90, 86, 80)
LIGHT   = (232, 226, 210)
WHITE   = (255, 255, 255)
SKY     = (178, 205, 225)
SAND    = (222, 200, 158)

FONT_DIR = "/usr/share/fonts/truetype/noto"

def F(name, size):
    """Font at working-canvas scale (size is in 1024-canvas px)."""
    return ImageFont.truetype(os.path.join(FONT_DIR, name), int(round(size * SS)))

SERIF      = lambda s: F("NotoSerif-Regular.ttf", s)
SERIF_B    = lambda s: F("NotoSerif-Bold.ttf", s)
SERIF_I    = lambda s: F("NotoSerif-Italic.ttf", s)
SANS       = lambda s: F("NotoSans-Regular.ttf", s)
SANS_B     = lambda s: F("NotoSans-Bold.ttf", s)
SANS_I     = lambda s: F("NotoSans-Italic.ttf", s)

def S(v):
    return int(round(v * SS))

def wrap(text, font, max_w):
    """Greedy word wrap to max_w (working-canvas px). Returns list of lines."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if font.getlength(t) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def fit_lines(text, font, max_w, max_lines):
    """Wrap text; raise if it needs more than max_lines (fail loudly)."""
    lines = wrap(text, font, max_w)
    if len(lines) > max_lines:
        raise SystemExit(f"TEXT OVERFLOW: {text!r} needs {len(lines)} lines, max {max_lines}")
    return lines

def text_h(font):
    """Line height for a font (working-canvas px), from its own metrics."""
    a, d = font.getmetrics()
    return a + d

def draw_lines(d, lines, x, y, font, fill, leading=None):
    lh = leading if leading is not None else text_h(font)
    for ln in lines:
        d.text((x, y), ln, font=font, fill=fill)
        y += lh
    return y

def chip(d, box, fill, outline=None):
    d.rectangle(box, fill=fill, outline=outline, width=S(1))

def rule(d, x0, x1, y, fill=INK, w=1):
    d.line([(x0, y), (x1, y)], fill=fill, width=S(w))

# =====================================================================
# DATA — 35 stories, all Saturday 21 November 2026 (see sources in notes)
# =====================================================================
BIG = [  # (big number, caption) — 6 cells
    ("Day 13", "of a COP31 summit that missed its close — still no deal"),
    ("3", "ballistic missiles destroyed over Riyadh"),
    ("6.7", "magnitude of the earthquake in Junín, Peru"),
    ("146", "people safe after a jet's emergency landing in Davao"),
    ("$55,130", "bitcoin's low on Saturday — lowest since Sep 2024"),
    ("136", "K L Rahul's runs in Wellington"),
]
REGIONS = [("EUROPE", 8), ("AMERICAS", 6), ("ASIA-PACIFIC", 9),
           ("MIDEAST", 6), ("OCEANIA", 2), ("AFRICA", 1), ("WORLD", 3)]
REGION_COLORS = {"EUROPE": (30, 70, 130), "AMERICAS": (120, 60, 140),
                 "ASIA-PACIFIC": (180, 110, 20), "MIDEAST": (164, 32, 28),
                 "OCEANIA": (16, 110, 105), "AFRICA": (46, 110, 62),
                 "WORLD": (90, 86, 80)}

HEROES = [
    dict(n=1, place="ANTALYA, TÜRKIYE", field="CLIMATE",
         label="COP31: NO DEAL", art="cop31",
         head="Climate summit ends Saturday with no deal",
         summ="COP31 missed its Friday close and stayed deadlocked into Saturday night.",
         src="Health Policy Watch, AP"),
    dict(n=2, place="RIYADH, SAUDI ARABIA", field="WAR",
         label="3 DOWN OVER RIYADH", art="riyadh",
         head="Three Houthi missiles shot down over Riyadh",
         summ="The Saudi-led coalition destroyed three ballistic missiles targeting Riyadh.",
         src="Reuters, AFP"),
    dict(n=3, place="MERCURY ORBIT", field="SPACE",
         label="2ND EVER · 37-MIN BURN", art="bepi",
         head="BepiColombo slips into orbit around Mercury",
         summ="After an eight-year journey, ESA's probe entered orbit — only the second ever.",
         src="ESA, Nature"),
]

CARDS = [
    dict(n=4, place="JUNÍN, PERU", field="EARTHQUAKE", label="M6.7 · 00:09 UTC",
         art="peru", head="Magnitude 6.7 quake shakes central Peru",
         summ="Deep quake at 00:09 UTC, felt in Lima; no deaths or damage.",
         src="USGS"),
    dict(n=5, place="DAVAO, PHILIPPINES", field="AVIATION", label="146 SAFE",
         art="davao", head="Jet lands safely after engine fire alert",
         summ="Air Niugini diverts after midnight; all 146 safe.",
         src="AP"),
    dict(n=6, place="PERTH, AUSTRALIA", field="CRICKET", label="WON IN 2 DAYS",
         art="ashes", head="Australia win Ashes opener inside two days",
         summ="Head 123 off 83 seals the win; Starc 10 for 113.",
         src="ANI"),
    dict(n=7, place="GULF OF FINLAND", field="WAR", label="16 CREW SAFE",
         art="sparta", head="Russian cargo ship hit by drones in Baltic",
         summ="Sparta II ablaze, drifts into Finnish waters; 16 crew safe.",
         src="Reuters"),
    dict(n=8, place="WELLINGTON, NZ", field="CRICKET", label="136",
         art="rahul", head="Rahul hits 136 as India take the lead",
         summ="136 off 290 balls; India 486 for 4, replying to 368.",
         src="ESPNcricinfo"),
    dict(n=9, place="LAS VEGAS, USA", field="FORMULA 1", label="1:33.893",
         art="vegas", head="Antonelli fastest — Verstappen takes pole",
         summ="Antonelli 1:33.893, then a grid penalty. Verstappen on pole.",
         src="Formula1.com"),
    dict(n=10, place="WORLD", field="MARKETS", label="LOW $55,130",
         art="bitcoin", head="Bitcoin falls below $58,000 on Saturday",
         summ="Low $55,130, closes $57,884 — the lowest since Sep 2024.",
         src="CoinGecko"),
    dict(n=11, place="UKRAINE", field="WAR", label="117 DOWN",
         art="drones", head="3 missiles and 148 drones fired overnight",
         summ="Air force: 117 drones downed by 08:00 Kyiv time.",
         src="Ukrainian Air Force"),
    dict(n=12, place="STRAIT OF HORMUZ", field="WAR", label="IRAN'S CLAIM",
         art="hormuz", head="Iran says it shot down a US drone",
         summ="IRGC claims 58th MQ-9 downing. No US confirmation.",
         src="IRIB claim"),
    dict(n=13, place="GAZA CITY", field="WAR", label="3 KILLED",
         art="gaza", head="Israeli strike kills three in Gaza City",
         summ="Three killed in Tel al-Hawa; 1,671 dead since the ceasefire.",
         src="Reuters"),
]

# Briefs: one line each, "NN PLACE — text (source)". Kept short to fit a
# ~320px column at 13px; the renderer asserts every line fits.
BRIEFS = [
    (14, "KYIV", "Kryvyi Rih kills 2, injures 60 (AP)"),
    (15, "ANTALYA", "EU warns COP31 on 'fossil summit' (AJ)"),
    (16, "ANTALYA", "Panama may block climate text (AJ)"),
    (17, "ANTALYA", "PLN signs six clean-power deals (Antara)"),
    (18, "SANAA", "Houthis threaten Jeddah, Red Sea ports (AJ)"),
    (19, "TAIPEI", "Mayor: don't block NT$20,000 (Asia Daily)"),
    (20, "PYONGYANG", "Kim factory tour, no Trump meet (AFP)"),
    (21, "NEW DELHI", "Minister: Taj Mahal yes, dargah no (Fact)"),
    (22, "KANSAS", "BYU beats Kansas 31\u201329 in 3OT (Reuters)"),
    (23, "SEJONG", "Freight train derails; no one hurt (JoongAng)"),
    (24, "BANGKOK", "Arsenic 30\u00d7 limit; water cut for 20,000 (CRT)"),
    (25, "NEW DELHI", "Minister at SCO forum in Delhi (Centreline)"),
    (26, "NAYPYIDAW", "Rights groups urge sanctions (AP)"),
    (27, "TEHRAN", "Iran: uranium stays, deal possible (Iran paper)"),
    (28, "BRUSSELS", "EU\u2013Indonesia sign trade deal, 10 yrs on (EC)"),
    (29, "GENEVA", "UN 'killer robots' talks end, no rules (AP)"),
    (30, "PARIS", "Cost-of-living protests: 82,500 march (AJ)"),
    (31, "MANAMA", "Iran attack sets Bahrain site ablaze (AJ)"),
    (32, "BRUSSELS", "UK\u2013EU sign post-Brexit deals (One Turn)"),
    (33, "WASHINGTON", "Indian gets 19+ years, Pannun plot (AJ)"),
    (34, "PORT-AU-PRINCE", "Police kill 34 gang members (AJ)"),
    (35, "BAYELSA", "Boat toll up to 24 (capsized Fri; toll Sat, NEMA)"),
]

DATE_CHECK = ("DATE CHECK — First reported before Saturday — not shown as Saturday's news: "
    "Wall Street's correction · the Kyiv bridge barrage · the missile in Poland · the UK\u2013EU deal · Cyclone Akvan's landfall · "
    "the Denmark attach\u00e9 plot · the Roundup settlement · the Texas execution · the Palisades verdict · the Shenzhen summit · "
    "Anthropic's IPO · GTA VI · the ICJ ruling itself (19 Nov).")

# =====================================================================
# ILLUSTRATIONS — flat vector scenes, one per pictured panel.
# Each takes (d, box) with box=(x0,y0,x1,y1) in working-canvas px.
# =====================================================================
def _sky(d, box, top, bot):
    x0, y0, x1, y1 = box
    steps = 24
    for i in range(steps):
        t = i / (steps - 1)
        c = tuple(int(top[k] + (bot[k] - top[k]) * t) for k in range(3))
        d.rectangle([x0, y0 + (y1 - y0) * i / steps, x1, y0 + (y1 - y0) * (i + 1) / steps], fill=c)

def _building(d, x, ybase, w, h, fill, win):
    x, ybase, w, h = int(x), int(ybase), int(w), int(h)
    d.rectangle([x, ybase - h, x + w, ybase], fill=fill)
    for wy in range(ybase - h + S(4), ybase - S(2), S(9)):
        for wx in range(x + S(3), x + w - S(3), S(8)):
            d.rectangle([wx, wy, wx + S(3), wy + S(4)], fill=win)

def art_cop31(d, box):
    """Globe, thermometer, clock on pale green — summit stuck, no deal."""
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=(214, 232, 214))
    cx, cy, r = x0 + (x1 - x0) * 0.30, y0 + (y1 - y0) * 0.52, (y1 - y0) * 0.34
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(70, 140, 190), outline=NAVY, width=S(2))
    d.ellipse([cx - r * 0.55, cy - r * 0.7, cx + r * 0.1, cy - r * 0.1], fill=(90, 170, 90))
    d.ellipse([cx - r * 0.1, cy + r * 0.15, cx + r * 0.6, cy + r * 0.75], fill=(90, 170, 90))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 255, 255), width=S(1))
    # thermometer
    tx = x0 + (x1 - x0) * 0.62
    d.rectangle([tx, y0 + (y1 - y0) * 0.18, tx + S(7), y0 + (y1 - y0) * 0.72], fill=WHITE, outline=INK, width=S(1))
    d.rectangle([tx, y0 + (y1 - y0) * 0.45, tx + S(7), y0 + (y1 - y0) * 0.72], fill=RED)
    d.ellipse([tx - S(4), y0 + (y1 - y0) * 0.68, tx + S(11), y0 + (y1 - y0) * 0.86], fill=RED, outline=INK, width=S(1))
    # clock
    kx, ky, kr = x0 + (x1 - x0) * 0.85, y0 + (y1 - y0) * 0.42, (y1 - y0) * 0.26
    d.ellipse([kx - kr, ky - kr, kx + kr, ky + kr], fill=WHITE, outline=INK, width=S(2))
    d.line([kx, ky, kx, ky - kr * 0.7], fill=INK, width=S(2))
    d.line([kx, ky, kx + kr * 0.55, ky + kr * 0.3], fill=INK, width=S(2))
    d.rectangle([x0, y1 - S(4), x1, y1], fill=(120, 150, 110))

def art_riyadh(d, box):
    """Night skyline, three missile arcs, bursts."""
    x0, y0, x1, y1 = box
    _sky(d, box, (12, 20, 44), (28, 52, 92))
    for sx, sy in [(0.12, 0.2), (0.35, 0.12), (0.6, 0.22), (0.85, 0.1), (0.95, 0.3)]:
        d.ellipse([x0 + (x1 - x0) * sx - S(1), y0 + (y1 - y0) * sy - S(1),
                   x0 + (x1 - x0) * sx + S(1), y0 + (y1 - y0) * sy + S(1)], fill=WHITE)
    d.ellipse([x0 + (x1 - x0) * 0.78 - S(8), y0 + (y1 - y0) * 0.16 - S(8),
               x0 + (x1 - x0) * 0.78 + S(8), y0 + (y1 - y0) * 0.16 + S(8)], fill=(240, 230, 190))
    base = y1
    for bx, bw, bh in [(0.02, 0.10, 0.34), (0.14, 0.08, 0.5), (0.24, 0.12, 0.42),
                       (0.38, 0.09, 0.58), (0.49, 0.11, 0.38), (0.62, 0.08, 0.52),
                       (0.72, 0.12, 0.44), (0.86, 0.10, 0.6)]:
        _building(d, x0 + (x1 - x0) * bx, base, (x1 - x0) * bw, (y1 - y0) * bh, (10, 16, 34), (250, 200, 90))
    # missile arcs + bursts
    for ax, ay, bx2 in [(0.18, 0.75, 0.42), (0.45, 0.8, 0.68), (0.7, 0.72, 0.9)]:
        x_a, y_a = x0 + (x1 - x0) * ax, y0 + (y1 - y0) * ay
        x_b, y_b = x0 + (x1 - x0) * bx2, y0 + (y1 - y0) * 0.25
        mx, my = (x_a + x_b) / 2, min(y_a, y_b) - (y1 - y0) * 0.28
        pts = []
        for t in [i / 20 for i in range(21)]:
            px = (1 - t) ** 2 * x_a + 2 * (1 - t) * t * mx + t * t * x_b
            py = (1 - t) ** 2 * y_a + 2 * (1 - t) * t * my + t * t * y_b
            pts.append((px, py))
        d.line(pts, fill=(255, 210, 120), width=S(2))
        for dx, dy in [(0, 0), (S(5), 0), (-S(5), 0), (0, S(5)), (0, -S(5))]:
            d.line([x_b + dx - S(4), y_b + dy, x_b + dx + S(4), y_b + dy], fill=(255, 190, 60), width=S(2))
            d.line([x_b + dx, y_b + dy - S(4), x_b + dx, y_b + dy + S(4)], fill=(255, 190, 60), width=S(2))

def art_bepi(d, box):
    """Mercury, orbit ring, probe with panels."""
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=(14, 18, 38))
    for sx, sy in [(0.1, 0.15), (0.25, 0.3), (0.55, 0.1), (0.7, 0.28), (0.9, 0.12), (0.4, 0.55)]:
        d.ellipse([x0 + (x1 - x0) * sx - S(1), y0 + (y1 - y0) * sy - S(1),
                   x0 + (x1 - x0) * sx + S(1), y0 + (y1 - y0) * sy + S(1)], fill=WHITE)
    mx, my, mr = x0 + (x1 - x0) * 0.3, y0 + (y1 - y0) * 0.62, (y1 - y0) * 0.3
    d.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=(198, 132, 80), outline=(140, 85, 50), width=S(2))
    for cx, cy, cr in [(0.22, 0.55, 0.05), (0.38, 0.7, 0.04), (0.28, 0.72, 0.03)]:
        d.ellipse([mx + (cx - 0.3) * mr * 2 - S(3), my + (cy - 0.62) * mr * 2 - S(3),
                   mx + (cx - 0.3) * mr * 2 + S(3), my + (cy - 0.62) * mr * 2 + S(3)], fill=(150, 95, 55))
    # orbit ellipse + probe
    d.ellipse([x0 + (x1 - x0) * 0.08, y0 + (y1 - y0) * 0.12, x1 - S(6), y0 + (y1 - y0) * 0.92],
              outline=(255, 210, 120), width=S(2))
    px, py = x0 + (x1 - x0) * 0.82, y0 + (y1 - y0) * 0.24
    d.rectangle([px - S(14), py - S(3), px - S(4), py + S(3)], fill=(90, 140, 200), outline=WHITE, width=S(1))
    d.rectangle([px + S(4), py - S(3), px + S(14), py + S(3)], fill=(90, 140, 200), outline=WHITE, width=S(1))
    d.rectangle([px - S(5), py - S(5), px + S(5), py + S(5)], fill=(220, 220, 220), outline=INK, width=S(1))
    d.polygon([(px + S(5), py - S(4)), (px + S(11), py), (px + S(5), py + S(4))], fill=(255, 160, 60))

def art_peru(d, box):
    """Seismograph trace over mountains, small house."""
    x0, y0, x1, y1 = box
    _sky(d, box, (222, 200, 158), (240, 228, 200))
    d.polygon([(x0, y1), (x0 + (x1 - x0) * 0.25, y0 + (y1 - y0) * 0.35),
               (x0 + (x1 - x0) * 0.5, y1)], fill=(150, 120, 90))
    d.polygon([(x0 + (x1 - x0) * 0.4, y1), (x0 + (x1 - x0) * 0.7, y0 + (y1 - y0) * 0.25),
               (x1, y1)], fill=(120, 95, 70))
    d.polygon([(x0 + (x1 - x0) * 0.62, y0 + (y1 - y0) * 0.25),
               (x0 + (x1 - x0) * 0.68, y0 + (y1 - y0) * 0.18),
               (x0 + (x1 - x0) * 0.74, y0 + (y1 - y0) * 0.25)], fill=WHITE)
    # seismograph strip
    sy0, sy1 = y0 + (y1 - y0) * 0.55, y0 + (y1 - y0) * 0.85
    d.rectangle([x0 + S(4), sy0, x1 - S(4), sy1], fill=WHITE, outline=INK, width=S(1))
    mid = (sy0 + sy1) / 2
    pts, x = [], x0 + S(6)
    import math as _m
    while x < x1 - S(6):
        t = (x - x0) / (x1 - x0)
        amp = (y1 - y0) * 0.13 * _m.exp(-((t - 0.5) ** 2) / 0.02) + S(1)
        pts.append((x, mid + amp * _m.sin(t * 90)))
        x += S(3)
    d.line(pts, fill=RED, width=S(2))
    # house
    hx, hy = x0 + (x1 - x0) * 0.78, y1 - S(2)
    d.rectangle([hx, hy - S(12), hx + S(20), hy], fill=(200, 170, 130), outline=INK, width=S(1))
    d.polygon([(hx - S(3), hy - S(12)), (hx + S(10), hy - S(20)), (hx + S(23), hy - S(12))], fill=RED)

def art_davao(d, box):
    """Airliner on runway, slide, dawn sky."""
    x0, y0, x1, y1 = box
    _sky(d, box, (250, 200, 140), (250, 230, 200))
    d.ellipse([x0 + (x1 - x0) * 0.8, y0 + (y1 - y0) * 0.08,
               x0 + (x1 - x0) * 0.8 + S(16), y0 + (y1 - y0) * 0.08 + S(16)], fill=(255, 220, 130))
    d.rectangle([x0, y0 + (y1 - y0) * 0.78, x1, y1], fill=(90, 90, 95))
    d.line([x0, y0 + (y1 - y0) * 0.78, x1, y0 + (y1 - y0) * 0.78], fill=WHITE, width=S(1))
    for i in range(6):
        d.rectangle([x0 + (x1 - x0) * (0.05 + i * 0.16), y0 + (y1 - y0) * 0.88,
                     x0 + (x1 - x0) * (0.05 + i * 0.16) + S(10), y0 + (y1 - y0) * 0.88 + S(2)], fill=(255, 210, 60))
    # plane
    px, py = x0 + (x1 - x0) * 0.5, y0 + (y1 - y0) * 0.52
    d.ellipse([px - S(34), py - S(9), px + S(34), py + S(9)], fill=WHITE, outline=INK, width=S(1))
    d.polygon([(px + S(30), py - S(6)), (px + S(48), py - S(2)), (px + S(30), py + S(2))], fill=WHITE, outline=INK)
    d.polygon([(px - S(6), py - S(7)), (px + S(6), py - S(7)), (px + S(2), py - S(18))], fill=(30, 90, 160))
    d.rectangle([px - S(30), py + S(1), px + S(10), py + S(5)], fill=(30, 90, 160))
    for wx in range(-28, 8, 7):
        d.rectangle([px + S(wx), py - S(5), px + S(wx + 3), py - S(1)], fill=(60, 60, 70))
    # slide
    d.polygon([(px - S(20), py + S(8)), (px - S(34), y0 + (y1 - y0) * 0.78),
               (px - S(26), y0 + (y1 - y0) * 0.78)], fill=(250, 200, 60), outline=INK)

def art_ashes(d, box):
    """Cricket: bat, ball, stumps, green pitch."""
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=(120, 170, 90))
    d.rectangle([x0, y0 + (y1 - y0) * 0.55, x1, y1], fill=(90, 140, 70))
    d.rectangle([x0 + (x1 - x0) * 0.42, y0 + (y1 - y0) * 0.15,
                 x0 + (x1 - x0) * 0.58, y1], fill=(222, 200, 158))
    # stumps
    sx = x0 + (x1 - x0) * 0.5
    for dx in (-S(4), 0, S(4)):
        d.rectangle([sx + dx - S(1), y0 + (y1 - y0) * 0.2, sx + dx + S(1), y0 + (y1 - y0) * 0.38], fill=(240, 220, 160))
    d.rectangle([sx - S(6), y0 + (y1 - y0) * 0.18, sx + S(6), y0 + (y1 - y0) * 0.2], fill=(240, 220, 160))
    # bat
    bx, by = x0 + (x1 - x0) * 0.3, y0 + (y1 - y0) * 0.55
    d.polygon([(bx, by - S(22)), (bx + S(9), by - S(20)), (bx + S(7), by + S(4)), (bx - S(2), by + S(4))],
              fill=(210, 170, 110), outline=INK)
    d.rectangle([bx + S(1), by - S(30), bx + S(6), by - S(20)], fill=(120, 80, 40))
    # ball
    d.ellipse([x0 + (x1 - x0) * 0.72 - S(6), y0 + (y1 - y0) * 0.3 - S(6),
               x0 + (x1 - x0) * 0.72 + S(6), y0 + (y1 - y0) * 0.3 + S(6)], fill=RED, outline=WHITE, width=S(1))

def art_sparta(d, box):
    """Cargo ship on fire, two drones, grey sea."""
    x0, y0, x1, y1 = box
    _sky(d, box, (150, 160, 170), (200, 205, 210))
    d.rectangle([x0, y0 + (y1 - y0) * 0.62, x1, y1], fill=(60, 90, 120))
    for i in range(4):
        d.line([x0 + S(4), y0 + (y1 - y0) * (0.7 + i * 0.07), x1 - S(4), y0 + (y1 - y0) * (0.7 + i * 0.07)],
               fill=(140, 170, 200), width=S(1))
    # ship hull
    hx0, hx1 = x0 + (x1 - x0) * 0.12, x0 + (x1 - x0) * 0.88
    hy = y0 + (y1 - y0) * 0.62
    d.polygon([(hx0, hy - S(16)), (hx1, hy - S(16)), (hx1 - S(8), hy + S(4)), (hx0 + S(8), hy + S(4))],
              fill=(40, 50, 70))
    d.rectangle([hx0 + S(10), hy - S(30), hx0 + S(26), hy - S(16)], fill=(200, 200, 200), outline=INK, width=S(1))
    d.rectangle([hx0 + S(34), hy - S(26), hx0 + S(52), hy - S(16)], fill=(180, 60, 40), outline=INK, width=S(1))
    # fire + smoke
    for fx, fh, fc in [(0.42, 0.30, (255, 140, 40)), (0.52, 0.38, (255, 90, 30)), (0.62, 0.26, (255, 170, 60))]:
        d.polygon([(x0 + (x1 - x0) * fx - S(5), hy - S(16)),
                   (x0 + (x1 - x0) * fx, hy - S(16) - (y1 - y0) * fh),
                   (x0 + (x1 - x0) * fx + S(5), hy - S(16))], fill=fc)
    for sx, sy, sr in [(0.45, 0.18, 6), (0.55, 0.12, 8), (0.5, 0.06, 5)]:
        d.ellipse([x0 + (x1 - x0) * sx - S(sr), y0 + (y1 - y0) * sy - S(sr),
                   x0 + (x1 - x0) * sx + S(sr), y0 + (y1 - y0) * sy + S(sr)], fill=(120, 120, 125))
    # drones
    for dx, dy in [(0.2, 0.2), (0.8, 0.28)]:
        cx, cy = x0 + (x1 - x0) * dx, y0 + (y1 - y0) * dy
        d.ellipse([cx - S(4), cy - S(3), cx + S(4), cy + S(3)], fill=INK)
        d.line([cx - S(9), cy - S(4), cx + S(9), cy - S(4)], fill=INK, width=S(1))

def art_rahul(d, box):
    """Cricket century: bat raised, ball, scoreboard feel."""
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=(200, 225, 190))
    d.rectangle([x0, y0 + (y1 - y0) * 0.6, x1, y1], fill=(110, 160, 85))
    # crowd band
    for i in range(9):
        cx = x0 + (x1 - x0) * (0.06 + i * 0.11)
        d.ellipse([cx - S(5), y0 + (y1 - y0) * 0.42 - S(5), cx + S(5), y0 + (y1 - y0) * 0.42 + S(5)],
                  fill=[(200, 60, 50), (40, 80, 160), (230, 180, 60)][i % 3])
    # raised bat
    bx, by = x0 + (x1 - x0) * 0.5, y0 + (y1 - y0) * 0.5
    d.polygon([(bx - S(4), by - S(26)), (bx + S(6), by - S(24)), (bx + S(4), by + S(2)), (bx - S(6), by + S(2))],
              fill=(210, 170, 110), outline=INK)
    d.rectangle([bx - S(2), by + S(2), bx + S(3), by + S(12)], fill=(120, 80, 40))
    # ball + stumps
    d.ellipse([x0 + (x1 - x0) * 0.8 - S(5), y0 + (y1 - y0) * 0.72 - S(5),
               x0 + (x1 - x0) * 0.8 + S(5), y0 + (y1 - y0) * 0.72 + S(5)], fill=RED, outline=WHITE, width=S(1))
    sx = x0 + (x1 - x0) * 0.18
    for dx in (-S(4), 0, S(4)):
        d.rectangle([sx + dx - S(1), y0 + (y1 - y0) * 0.62, sx + dx + S(1), y0 + (y1 - y0) * 0.78], fill=(240, 220, 160))

def art_vegas(d, box):
    """Night street circuit, chequered flag, car."""
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=(20, 18, 40))
    for sx, sy in [(0.1, 0.15), (0.3, 0.08), (0.55, 0.18), (0.8, 0.1), (0.92, 0.25)]:
        d.ellipse([x0 + (x1 - x0) * sx - S(1), y0 + (y1 - y0) * sy - S(1),
                   x0 + (x1 - x0) * sx + S(1), y0 + (y1 - y0) * sy + S(1)], fill=WHITE)
    # track curve
    d.line([(x0, y0 + (y1 - y0) * 0.85), (x0 + (x1 - x0) * 0.4, y0 + (y1 - y0) * 0.55),
            (x0 + (x1 - x0) * 0.7, y0 + (y1 - y0) * 0.62), (x1, y0 + (y1 - y0) * 0.45)],
           fill=(70, 70, 85), width=S(10))
    d.line([(x0, y0 + (y1 - y0) * 0.85), (x0 + (x1 - x0) * 0.4, y0 + (y1 - y0) * 0.55),
            (x0 + (x1 - x0) * 0.7, y0 + (y1 - y0) * 0.62), (x1, y0 + (y1 - y0) * 0.45)],
           fill=(255, 220, 80), width=S(1))
    # chequered flag
    fx, fy = x0 + (x1 - x0) * 0.68, y0 + (y1 - y0) * 0.12
    for r in range(3):
        for c in range(4):
            col = WHITE if (r + c) % 2 == 0 else INK
            d.rectangle([fx + S(c * 5), fy + S(r * 5), fx + S(c * 5 + 5), fy + S(r * 5 + 5)], fill=col)
    d.line([fx, fy, fx, fy + S(30)], fill=INK, width=S(2))
    # car
    cx, cy = x0 + (x1 - x0) * 0.45, y0 + (y1 - y0) * 0.58
    d.polygon([(cx - S(20), cy), (cx - S(12), cy - S(7)), (cx + S(8), cy - S(7)),
               (cx + S(20), cy), (cx + S(20), cy + S(4)), (cx - S(20), cy + S(4))], fill=(200, 30, 40))
    d.ellipse([cx - S(14), cy + S(2), cx - S(6), cy + S(10)], fill=INK)
    d.ellipse([cx + S(8), cy + S(2), cx + S(16), cy + S(10)], fill=INK)

def art_bitcoin(d, box):
    """Falling chart, coin, red down arrow."""
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=(24, 28, 36))
    # grid
    for gy in [0.25, 0.5, 0.75]:
        d.line([x0 + S(4), y0 + (y1 - y0) * gy, x1 - S(4), y0 + (y1 - y0) * gy], fill=(60, 66, 76), width=S(1))
    pts = [(0.06, 0.3), (0.22, 0.38), (0.34, 0.32), (0.5, 0.55), (0.62, 0.5), (0.78, 0.72), (0.94, 0.82)]
    xy = [(x0 + (x1 - x0) * px, y0 + (y1 - y0) * py) for px, py in pts]
    d.line(xy, fill=(255, 80, 60), width=S(3))
    for px, py in xy:
        d.ellipse([px - S(2), py - S(2), px + S(2), py + S(2)], fill=(255, 200, 80))
    # coin
    cx, cy, cr = x0 + (x1 - x0) * 0.8, y0 + (y1 - y0) * 0.28, (y1 - y0) * 0.2
    d.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=(247, 147, 26), outline=(200, 110, 10), width=S(2))
    d.text((cx - S(5), cy - S(9)), "B", font=SANS_B(14), fill=WHITE)

def art_drones(d, box):
    """Night sky, drone swarm dots, intercept bursts."""
    x0, y0, x1, y1 = box
    _sky(d, box, (10, 16, 36), (30, 48, 84))
    d.ellipse([x0 + (x1 - x0) * 0.85, y0 + (y1 - y0) * 0.12,
               x0 + (x1 - x0) * 0.85 + S(14), y0 + (y1 - y0) * 0.12 + S(14)], fill=(240, 230, 190))
    # city silhouette
    base = y1
    for bx, bw, bh in [(0.0, 0.12, 0.3), (0.14, 0.1, 0.44), (0.26, 0.12, 0.36),
                       (0.4, 0.09, 0.5), (0.51, 0.13, 0.34), (0.66, 0.1, 0.46), (0.78, 0.12, 0.38), (0.9, 0.1, 0.3)]:
        _building(d, x0 + (x1 - x0) * bx, base, (x1 - x0) * bw, (y1 - y0) * bh, (8, 12, 28), (250, 200, 90))
    # drone dots + bursts
    for dx, dy in [(0.15, 0.3), (0.3, 0.2), (0.45, 0.35), (0.6, 0.22), (0.75, 0.32)]:
        cx, cy = x0 + (x1 - x0) * dx, y0 + (y1 - y0) * dy
        d.ellipse([cx - S(2), cy - S(2), cx + S(2), cy + S(2)], fill=(255, 220, 120))
    for bx, by in [(0.38, 0.28), (0.68, 0.18)]:
        cx, cy = x0 + (x1 - x0) * bx, y0 + (y1 - y0) * by
        for dx, dy in [(0, 0), (S(6), 0), (-S(6), 0), (0, S(6)), (0, -S(6))]:
            d.line([cx + dx - S(4), cy + dy, cx + dx + S(4), cy + dy], fill=(255, 190, 60), width=S(2))
            d.line([cx + dx, cy + dy - S(4), cx + dx, cy + dy + S(4)], fill=(255, 190, 60), width=S(2))

def art_hormuz(d, box):
    """Sea strait, ship, falling drone with smoke trail."""
    x0, y0, x1, y1 = box
    _sky(d, box, (190, 210, 225), (230, 235, 240))
    d.rectangle([x0, y0 + (y1 - y0) * 0.55, x1, y1], fill=(40, 90, 130))
    for i in range(3):
        d.line([x0 + S(4), y0 + (y1 - y0) * (0.64 + i * 0.1), x1 - S(4), y0 + (y1 - y0) * (0.64 + i * 0.1)],
               fill=(120, 170, 205), width=S(1))
    # distant shore
    d.polygon([(x0, y0 + (y1 - y0) * 0.55), (x0 + (x1 - x0) * 0.3, y0 + (y1 - y0) * 0.42),
               (x0 + (x1 - x0) * 0.55, y0 + (y1 - y0) * 0.55)], fill=(150, 130, 100))
    # ship
    sx0, sx1 = x0 + (x1 - x0) * 0.08, x0 + (x1 - x0) * 0.5
    sy = y0 + (y1 - y0) * 0.62
    d.polygon([(sx0, sy - S(12)), (sx1, sy - S(12)), (sx1 - S(6), sy + S(2)), (sx0 + S(6), sy + S(2))], fill=(60, 70, 80))
    d.rectangle([sx0 + S(12), sy - S(22), sx0 + S(24), sy - S(12)], fill=WHITE, outline=INK, width=S(1))
    # falling drone + smoke
    dx, dy = x0 + (x1 - x0) * 0.78, y0 + (y1 - y0) * 0.3
    pts = [(dx - S(30), dy - S(16)), (dx - S(20), dy - S(10)), (dx - S(10), dy - S(4)), (dx, dy)]
    d.line(pts, fill=(140, 140, 145), width=S(3))
    d.ellipse([dx - S(5), dy - S(3), dx + S(5), dy + S(3)], fill=INK)
    d.line([dx - S(10), dy - S(4), dx + S(10), dy - S(4)], fill=INK, width=S(1))
    # flame
    d.polygon([(dx - S(2), dy + S(3)), (dx + S(2), dy + S(3)), (dx, dy + S(12))], fill=(255, 140, 40))

def art_gaza(d, box):
    """Street, damaged building, smoke, aid van."""
    x0, y0, x1, y1 = box
    _sky(d, box, (225, 205, 175), (240, 228, 205))
    # buildings
    _building(d, x0 + (x1 - x0) * 0.05, y0 + (y1 - y0) * 0.85, (x1 - x0) * 0.22, (y1 - y0) * 0.55, (170, 150, 120), (70, 60, 50))
    _building(d, x0 + (x1 - x0) * 0.32, y0 + (y1 - y0) * 0.85, (x1 - x0) * 0.24, (y1 - y0) * 0.7, (140, 120, 95), (60, 50, 42))
    # broken top on second building
    d.polygon([(x0 + (x1 - x0) * 0.32, y0 + (y1 - y0) * 0.15),
               (x0 + (x1 - x0) * 0.4, y0 + (y1 - y0) * 0.08),
               (x0 + (x1 - x0) * 0.48, y0 + (y1 - y0) * 0.15)], fill=(90, 75, 60))
    # smoke
    for sx, sy, sr in [(0.42, 0.12, 7), (0.48, 0.06, 9), (0.55, 0.12, 6)]:
        d.ellipse([x0 + (x1 - x0) * sx - S(sr), y0 + (y1 - y0) * sy - S(sr),
                   x0 + (x1 - x0) * sx + S(sr), y0 + (y1 - y0) * sy + S(sr)], fill=(110, 105, 100))
    # street + van
    d.rectangle([x0, y0 + (y1 - y0) * 0.85, x1, y1], fill=(120, 110, 95))
    vx, vy = x0 + (x1 - x0) * 0.62, y0 + (y1 - y0) * 0.88
    d.rectangle([vx - S(18), vy - S(10), vx + S(18), vy], fill=WHITE, outline=INK, width=S(1))
    d.rectangle([vx + S(18), vy - S(7), vx + S(28), vy], fill=(200, 60, 40), outline=INK, width=S(1))
    d.ellipse([vx - S(12), vy - S(2), vx - S(4), vy + S(6)], fill=INK)
    d.ellipse([vx + S(8), vy - S(2), vx + S(16), vy + S(6)], fill=INK)

ART = {"cop31": art_cop31, "riyadh": art_riyadh, "bepi": art_bepi, "peru": art_peru,
       "davao": art_davao, "ashes": art_ashes, "sparta": art_sparta, "rahul": art_rahul,
       "vegas": art_vegas, "bitcoin": art_bitcoin, "drones": art_drones,
       "hormuz": art_hormuz, "gaza": art_gaza}

# =====================================================================
# WORLD MAP — stylised polygons (lon/lat), equirectangular projection.
# =====================================================================
NA = [(-168, 66), (-140, 70), (-125, 71), (-110, 68), (-95, 69), (-85, 66),
      (-80, 73), (-70, 62), (-65, 60), (-55, 52), (-60, 46), (-70, 42),
      (-75, 35), (-80, 32), (-81, 26), (-84, 30), (-90, 21), (-97, 16),
      (-94, 17), (-87, 13), (-83, 9), (-79, 9), (-85, 11), (-90, 14),
      (-95, 16), (-105, 20), (-110, 23), (-114, 28), (-120, 34), (-125, 40),
      (-124, 48), (-130, 55), (-140, 60), (-155, 58), (-165, 60)]
GREENLAND = [(-58, 64), (-45, 60), (-40, 65), (-30, 68), (-22, 70), (-25, 76),
             (-40, 78), (-55, 76), (-58, 70)]
SA = [(-79, 9), (-72, 12), (-62, 10), (-55, 6), (-50, 0), (-44, -3),
      (-35, -8), (-38, -15), (-40, -22), (-48, -28), (-52, -33), (-58, -38),
      (-62, -41), (-68, -52), (-70, -54), (-73, -50), (-73, -40), (-73, -30),
      (-70, -20), (-75, -15), (-80, -6), (-81, 0), (-80, 5)]
AFRICA = [(-17, 15), (-16, 20), (-10, 31), (-5, 35), (0, 36), (10, 37),
          (20, 32), (30, 31), (35, 28), (34, 27), (37, 22), (40, 15),
          (43, 11), (48, 10), (51, 12), (46, 5), (41, -2), (40, -10),
          (36, -18), (33, -26), (28, -33), (20, -35), (15, -27), (12, -18),
          (13, -10), (12, -5), (9, 4), (4, 6), (-8, 5), (-13, 8), (-17, 12)]
EURASIA = [(-10, 36), (-9, 43), (-2, 48), (-4, 49), (0, 50), (3, 52),
           (8, 55), (10, 58), (5, 60), (10, 62), (15, 68), (25, 71), (35, 68),
           (45, 68), (55, 69), (65, 69), (75, 72), (85, 74), (95, 76),
           (105, 77), (115, 76), (130, 72), (145, 72), (160, 70), (170, 67),
           (178, 65), (170, 60), (162, 56), (158, 52), (150, 59), (142, 55),
           (140, 50), (135, 44), (130, 42), (127, 40), (122, 38), (120, 32),
           (118, 25), (110, 21), (108, 18), (105, 10), (103, 8), (100, 8),
           (98, 12), (95, 16), (92, 21), (88, 22), (85, 20), (80, 15),
           (77, 8), (75, 12), (72, 20), (68, 22), (65, 25), (61, 25),
           (57, 26), (54, 27), (52, 28), (50, 30), (48, 30), (44, 29),
           (40, 28), (38, 24), (36, 21), (35, 18), (39, 21), (43, 13),
           (45, 12), (50, 16), (55, 17), (58, 20), (59, 22), (55, 25),
           (52, 26), (50, 29), (48, 30), (44, 29), (42, 29), (39, 31),
           (36, 36), (30, 36), (27, 37), (23, 36), (19, 40), (15, 38),
           (12, 42), (8, 39), (3, 38), (0, 36), (-2, 37), (-6, 36), (-9, 37)]
AUSTRALIA = [(114, -22), (114, -30), (115, -35), (120, -34), (129, -32),
             (132, -32), (136, -35), (140, -38), (145, -38), (150, -37),
             (153, -32), (153, -27), (150, -22), (146, -19), (142, -15),
             (142, -11), (137, -12), (135, -15), (132, -12), (130, -13),
             (126, -14), (122, -17), (118, -20)]
UK = [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53), (1, 51), (-3, 50)]
JAPAN = [(130, 31), (132, 33), (135, 34), (137, 35), (139, 37), (141, 39),
         (141, 42), (143, 43), (145, 44), (142, 42), (140, 39), (139, 36),
         (136, 34), (133, 34), (131, 32)]
NZ = [(167, -45), (170, -42), (173, -40), (175, -38), (178, -38), (176, -40),
      (173, -42), (169, -46)]
CONTINENTS = [NA, GREENLAND, SA, AFRICA, EURASIA, AUSTRALIA, UK, JAPAN, NZ]
# (story n, lon, lat, display offset dx, dy in 1024-px) — offsets de-clash pins
PINS = [(1, 30.7, 36.9, 0, -8), (2, 46.7, 24.7, 6, 4), (4, -76.0, -11.0, 0, 0),
        (5, 125.6, 7.1, 0, 0), (6, 115.9, -31.9, 0, 0), (7, 25.0, 60.2, -4, -6),
        (8, 174.8, -41.3, 0, 0), (9, -115.1, 36.2, 0, 0), (10, -74.0, 40.7, 0, 0),
        (11, 30.5, 50.4, -8, -4), (12, 56.5, 26.5, 8, -6), (13, 34.5, 31.5, 4, 8)]
PIN_NOTES = "Pins 1–2, 4–13 mark the pictured stories. 3 BepiColombo is in space — Mercury orbit. Pin 10 = world markets (New York)."

def draw_map(d, box):
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=NAVY)
    mx0, my0, mx1, my1 = x0 + S(2), y0 + S(2), x1 - S(2), y1 - S(2)
    def proj(lon, lat):
        return (mx0 + (lon + 180) / 360 * (mx1 - mx0),
                my0 + (90 - lat) / 180 * (my1 - my0))
    for poly in CONTINENTS:
        d.polygon([proj(lon, lat) for lon, lat in poly], fill=(222, 200, 158))
    # Indonesia dots
    for lon, lat in [(95, 5), (105, -5), (110, -7), (115, -8), (120, -9), (130, -3), (135, -4), (140, -6)]:
        px, py = proj(lon, lat)
        d.ellipse([px - S(2), py - S(2), px + S(2), py + S(2)], fill=(222, 200, 158))
    # pins
    fnum = SANS_B(8)
    for n, lon, lat, dx, dy in PINS:
        px, py = proj(lon, lat)
        ox, oy = px + S(dx), py + S(dy)
        if (dx, dy) != (0, 0):
            d.line([px, py, ox, oy], fill=WHITE, width=S(1))
        r = S(6.5)
        d.ellipse([ox - r, oy - r, ox + r, oy + r], fill=RED, outline=WHITE, width=S(1))
        tw = fnum.getlength(str(n))
        d.text((ox - tw / 2, oy - S(4.5)), str(n), font=fnum, fill=WHITE)

# =====================================================================
# LAYOUT + RENDER
# =====================================================================
MX = 14  # side margin, 1024-px

def render():
    img = Image.new("RGB", (CW, CH), CREAM)
    d = ImageDraw.Draw(img)
    X0, X1 = S(MX), S(W - MX)
    y = S(10)

    # ---- top bar ----
    d.text((X0, y), "THE WORLD IN ONE DAY", font=SANS_B(11), fill=RED)
    right = "35 STORIES · 7 REGIONS · EVERY ONE DATED SATURDAY 21 NOVEMBER 2026"
    d.text((X1 - SANS_B(10).getlength(right), y + S(1)), right, font=SANS_B(10), fill=INK)
    y += S(17)
    rule(d, X0, X1, y, w=2)
    y += S(5)

    # ---- masthead ----
    mast = "Saturday 21 November 2026"
    mf = SERIF_B(60)
    assert mf.getlength(mast) <= X1 - X0, "masthead too wide"
    d.text((X0, y), mast, font=mf, fill=INK)
    y += S(62)
    stand = "Climate summit ends with no deal  ·  Missiles shot down over Riyadh  ·  BepiColombo reaches Mercury"
    d.text((X0, y), stand, font=SERIF_I(15.5), fill=DARKRED)
    y += S(21)
    rule(d, X0, X1, y, w=1)
    y += S(5)

    # ---- big numbers strip (6 cells) ----
    bx, bw = X0, (X1 - X0) // 6
    top_y = y
    for i, (num, cap) in enumerate(BIG):
        cx = bx + i * bw
        if i:
            d.line([cx, top_y + S(2), cx, top_y + S(50)], fill=(200, 190, 170), width=S(1))
        d.text((cx + S(6), top_y), num, font=SERIF_B(26), fill=RED if i in (0, 1, 4) else INK)
        lines = fit_lines(cap, SANS(10.5), bw - S(12), 2)
        draw_lines(d, lines, cx + S(6), top_y + S(30), SANS(10.5), INK, leading=S(12))
    y = top_y + S(58)

    # ---- region chips ----
    cx = X0
    for name, count in REGIONS:
        label = f"{name} {count}"
        f = SANS_B(10)
        wch = f.getlength(label) + S(14)
        chip(d, (cx, y, cx + wch, y + S(16)), REGION_COLORS[name])
        d.text((cx + S(7), y + S(2)), label, font=f, fill=WHITE)
        cx += wch + S(6)
    d.text((X1 - SANS_I(10).getlength("ALL STORIES: SAT 21 NOV 2026, ANY TIME ZONE"), y + S(2)),
           "ALL STORIES: SAT 21 NOV 2026, ANY TIME ZONE", font=SANS_I(10), fill=INK)
    y += S(22)

    # ---- heroes: 3 columns, wide illustration band on top ----
    hw, gap = (X1 - X0 - S(20)) // 3, S(10)
    hy = y
    hero_h = S(212)
    for i, h in enumerate(HEROES):
        hx = X0 + i * (hw + gap)
        art_h = S(92)
        ART[h["art"]](d, (hx, hy, hx + hw, hy + art_h))
        # red label bar on the illustration
        lf = SANS_B(12)
        lw = lf.getlength(h["label"]) + S(14)
        d.rectangle([hx, hy, hx + lw, hy + S(20)], fill=RED)
        d.text((hx + S(7), hy + S(3)), h["label"], font=lf, fill=WHITE)
        # caption chip bottom-left inside art
        cf = SANS_B(10)
        cap = h["src"].upper()
        cw2 = cf.getlength(cap) + S(10)
        d.rectangle([hx, hy + art_h - S(17), hx + cw2, hy + art_h], fill=INK)
        d.text((hx + S(5), hy + art_h - S(14)), cap, font=cf, fill=WHITE)
        ty = hy + art_h + S(5)
        d.text((hx, ty), f"{h['n']:02d} · {h['place']} — {h['field']}", font=SANS_B(10.5), fill=RED)
        ty += S(14)
        lines = fit_lines(h["head"], SERIF_B(22.5), hw, 2)
        ty = draw_lines(d, lines, hx, ty, SERIF_B(22.5), INK, leading=S(26))
        ty += S(3)
        lines = fit_lines(h["summ"], SANS(14), hw, 2)
        ty = draw_lines(d, lines, hx, ty, SANS(14), INK, leading=S(17))
    y = hy + hero_h + S(6)

    # ---- cards: 2 rows x 5 ----
    cw, cgap = (X1 - X0 - S(32)) // 5, S(8)
    card_h = S(148)
    for row in range(2):
        for col in range(5):
            c = CARDS[row * 5 + col]
            cx = X0 + col * (cw + cgap)
            cy = y + row * (card_h + S(8))
            art_h = S(50)
            ART[c["art"]](d, (cx, cy, cx + cw, cy + art_h))
            lf = SANS_B(12)
            lw = lf.getlength(c["label"]) + S(10)
            d.rectangle([cx, cy, cx + lw, cy + S(19)], fill=RED)
            d.text((cx + S(5), cy + S(3)), c["label"], font=lf, fill=WHITE)
            ty = cy + art_h + S(4)
            d.text((cx, ty), f"{c['n']:02d} · {c['place']} — {c['field']}", font=SANS_B(9), fill=RED)
            ty += S(12)
            lines = fit_lines(c["head"], SERIF_B(16.5), cw, 2)
            ty = draw_lines(d, lines, cx, ty, SERIF_B(16.5), INK, leading=S(19))
            ty += S(2)
            lines = fit_lines(c["summ"], SANS(12.5), cw, 2)
            ty = draw_lines(d, lines, cx, ty, SANS(12.5), INK, leading=S(15))
            d.text((cx, cy + card_h - S(10)), f"({c['src']})", font=SANS_I(9), fill=GREY)
    y = y + 2 * card_h + S(8) + S(6)

    # ---- bottom: map left + briefs right ----
    map_w = S(280)
    briefs_x = X0 + map_w + S(12)
    briefs_w = X1 - briefs_x
    col_w = (briefs_w - S(12)) // 2
    by = y
    d.text((X0, by), "WHERE IT HAPPENED", font=SANS_B(12), fill=INK)
    d.text((briefs_x, by), "ALSO ON SATURDAY 21 NOVEMBER — 22 MORE STORIES",
           font=SANS_B(12), fill=INK)
    by += S(17)
    map_h = S(186)
    draw_map(d, (X0, by, X0 + map_w, by + map_h))
    d.text((X0, by + map_h + S(3)), PIN_NOTES, font=SANS_I(8.5), fill=GREY)
    # briefs, 2 columns x 11 rows, one line each
    bf_lead, bf_text = SANS_B(12), SANS(12)
    row_h = S(17)
    for i, (n, place, txt) in enumerate(BRIEFS):
        col = i // 11
        rowi = i % 11
        bx = briefs_x + col * (col_w + S(12))
        ry = by + rowi * row_h
        lead = f"{n} {place} — "
        total = bf_lead.getlength(lead) + bf_text.getlength(txt)
        if total > col_w:
            raise SystemExit(f"BRIEF OVERFLOW #{n}: {total / SS:.0f}px > {col_w / SS:.0f}px: {place} — {txt}")
        d.text((bx, ry), lead, font=bf_lead, fill=INK)
        d.text((bx + bf_lead.getlength(lead), ry), txt, font=bf_text, fill=INK)
    y = by + map_h + S(16)

    # ---- DATE CHECK strip ----
    dc = DATE_CHECK
    dcf = SANS(10.5)
    dc_lines = wrap(dc, dcf, X1 - X0 - S(16))
    dc_h = S(8) + len(dc_lines) * S(13) + S(8)
    d.rectangle([X0, y, X1, y + dc_h], outline=RED, width=S(2))
    yy = y + S(6)
    for ln in dc_lines:
        d.text((X0 + S(8), yy), ln, font=dcf, fill=INK)
        yy += S(13)
    y = y + dc_h + S(6)

    # ---- footer ----
    d.text((X0, y), "Every story here happened, or was first reported, on Saturday 21 November 2026 in at least one time zone. Claims are attributed.",
           font=SANS_I(9.5), fill=GREY)
    y += S(13)
    d.text((X0, y), "Sources named beside each story · Original vector drawings, not photographs",
           font=SANS_I(9.5), fill=GREY)
    y += S(4)
    if y > S(1014):
        raise SystemExit(f"LAYOUT OVERFLOW: content ends at {y / SS:.0f}px, limit 1014px")

    out = img.resize((W, H), Image.LANCZOS)
    out.save("entry.png", optimize=True)
    return out

def verify():
    """Internal checks: story count, numbering, region sums, pin coverage."""
    assert len(HEROES) + len(CARDS) + len(BRIEFS) == 35, "story count != 35"
    nums = [h["n"] for h in HEROES] + [c["n"] for c in CARDS] + [n for n, _, _ in BRIEFS]
    assert nums == list(range(1, 36)), f"numbering broken: {nums}"
    assert sum(c for _, c in REGIONS) == 35, "region counts != 35"
    assert len(ART) == 13, "art functions != 13"
    assert all(h["art"] in ART for h in HEROES) and all(c["art"] in ART for c in CARDS)
    print("VERIFY OK: 35 stories (3 hero + 10 cards + 22 briefs), numbering 1-35, regions sum 35, 13 illustrated panels")

if __name__ == "__main__":
    verify()
    render()
    print("rendered entry.png")
