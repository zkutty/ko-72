import math

# ── Landing wheel (440×440) ────────────────────────────────────────────────────
R_OUT = 200
R_IN  = 148
CTR   = 220
PAD   = 0.006

def arc_path(i: int) -> str:
    a0 = (i / 72) * 2 * math.pi - math.pi / 2
    a1 = ((i + 1) / 72) * 2 * math.pi - math.pi / 2
    sA0, sA1 = a0 + PAD, a1 - PAD
    p1 = (CTR + R_OUT * math.cos(sA0), CTR + R_OUT * math.sin(sA0))
    p2 = (CTR + R_OUT * math.cos(sA1), CTR + R_OUT * math.sin(sA1))
    p3 = (CTR + R_IN  * math.cos(sA1), CTR + R_IN  * math.sin(sA1))
    p4 = (CTR + R_IN  * math.cos(sA0), CTR + R_IN  * math.sin(sA0))
    return (
        f"M {p1[0]:.2f} {p1[1]:.2f} "
        f"A {R_OUT} {R_OUT} 0 0 1 {p2[0]:.2f} {p2[1]:.2f} "
        f"L {p3[0]:.2f} {p3[1]:.2f} "
        f"A {R_IN} {R_IN} 0 0 0 {p4[0]:.2f} {p4[1]:.2f} Z"
    )

# ── Archive-page ring (140×140) ────────────────────────────────────────────────
RING     = 140
RC       = RING / 2
R_OUT_SM = 58
R_IN_SM  = 48
PAD_SM   = 0.004

def ring_path(i: int) -> str:
    a0 = (i / 72) * 2 * math.pi - math.pi / 2
    a1 = ((i + 1) / 72) * 2 * math.pi - math.pi / 2
    sA0, sA1 = a0 + PAD_SM, a1 - PAD_SM
    p1 = (RC + R_OUT_SM * math.cos(sA0), RC + R_OUT_SM * math.sin(sA0))
    p2 = (RC + R_OUT_SM * math.cos(sA1), RC + R_OUT_SM * math.sin(sA1))
    p3 = (RC + R_IN_SM  * math.cos(sA1), RC + R_IN_SM  * math.sin(sA1))
    p4 = (RC + R_IN_SM  * math.cos(sA0), RC + R_IN_SM  * math.sin(sA0))
    return (
        f"M {p1[0]:.2f} {p1[1]:.2f} "
        f"A {R_OUT_SM} {R_OUT_SM} 0 0 1 {p2[0]:.2f} {p2[1]:.2f} "
        f"L {p3[0]:.2f} {p3[1]:.2f} "
        f"A {R_IN_SM} {R_IN_SM} 0 0 0 {p4[0]:.2f} {p4[1]:.2f} Z"
    )

# ── Cardinal labels (pre-computed x/y for the 440px wheel) ────────────────────
def cardinal_labels() -> list:
    """Return the four cardinal season labels with pre-computed SVG coordinates."""
    defs = [
        {'idx': 0,  'label': 'SPR', 'sub': 'Feb'},
        {'idx': 18, 'label': 'SUM', 'sub': 'May'},
        {'idx': 36, 'label': 'AUT', 'sub': 'Aug'},
        {'idx': 54, 'label': 'WIN', 'sub': 'Nov'},
    ]
    r = R_OUT + 30
    result = []
    for c in defs:
        angle = ((c['idx'] + 9) / 72) * 2 * math.pi - math.pi / 2
        result.append({
            **c,
            'x': round(CTR + r * math.cos(angle), 1),
            'y': round(CTR + r * math.sin(angle), 1),
        })
    return result

# ── Season augmentation ────────────────────────────────────────────────────────
def augment_seasons(seasons: list) -> list:
    """Add arc_d, ring_d, and url to every season dict."""
    return [
        {
            **s,
            'arc_d':  arc_path(i),
            'ring_d': ring_path(i),
            'url':    f"/archive/{s['id']:02d}-{s['slug']}.html",
        }
        for i, s in enumerate(seasons)
    ]
