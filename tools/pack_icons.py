"""Add the aniworld-cli icons to the bundled ModernZ icon font.

``aniworld_cli/mpv/fonts/modernz-icons.ttf`` is a copy of ModernZ's icon font
with three glyphs added, for the three extra on-screen buttons the bundled
config uses. They are ligature names, not text:

* ``fluent_anime4k``     -- "enhance" sparkle: one four-point star plus two
                            smaller ones
* ``fluent_anime4k_off`` -- the same sparkle with a slash through it, shown while
                            the shader chain is off
* ``fluent_shortcuts``   -- a keyboard: rounded body, two key rows, spacebar

(``fluent_subtitles`` for the language button already exists upstream, so the
script does not touch it.)

Why the vendored TTF is patched instead of drawing with ASS tags: ModernZ
renders a button's content with the single icon font (``control_3`` style,
``\\fn modernz-icons``), so a ligature name used as the button label *is* an
icon -- no script change, no second font, and the diff in the config stays
data-only. The cost is that ``modernz-icons.ttf`` is no longer pristine, which
``aniworld_cli/mpv/THIRD-PARTY.md`` documents.

Geometry, measured from the bundled glyphs rather than guessed: the em is 1024
units, the design grid is 24 units, so 1 design unit = 42.667 font units; icon
glyphs are 1024 wide (one em) and the grid's top-left corner sits at font
(0, 1024) -- e.g. ``fluent_info`` spans design 2..22 horizontally, exactly
85..939 in font units. Outline icons use a 2-unit stroke.

The script is idempotent: a glyph, its codepoint and its ligatures are one unit,
keyed by the ligature text (this font's ``post`` table is version 3.0 and carries
no glyph names, so names are not usable as identity). Re-run it after replacing
the font with a newer upstream build:

    python3 tools/pack_icons.py

Requires ``fontTools`` (``pip install fontTools``).
"""

from __future__ import annotations

import unicodedata
from pathlib import Path

import math

from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import Glyph

ROOT = Path(__file__).resolve().parents[1]
FONT = ROOT / "aniworld_cli" / "mpv" / "fonts" / "modernz-icons.ttf"

UPEM = 1024
GRID = 24.0
UNIT = UPEM / GRID          # 42.667 font units per design unit
STROKE = 2.0                # design units, matches the bundled icons
ADVANCE = 1024              # every icon is one em wide

#: New glyphs, in the order their codepoints are assigned (U+F091 onwards: the
#: font already uses U+F000..U+F090 densely).
START_CP = 0xF091

# ---------------------------------------------------------------------------
# geometry helpers -- design coordinates, 24x24 grid, y pointing DOWN
# ---------------------------------------------------------------------------


def rr_ops(x: float, y: float, w: float, h: float, r: float) -> list[tuple]:
    """A rounded rectangle as (M|L|C|Z, points...) ops, clockwise on screen.

    Clockwise in a y-down grid is: top edge left->right, down the right edge,
    bottom edge right->left, up the left edge -- which is also the direction
    TrueType wants for an *outer* contour.
    """
    k = r * 0.5523  # cubic approximation of a quarter circle
    x0, y0, x1, y1 = x, y, x + w, y + h
    return [
        ("M", (x0 + r, y0)),
        ("L", (x1 - r, y0)),
        ("C", (x1 - r + k, y0), (x1, y0 + r - k), (x1, y0 + r)),
        ("L", (x1, y1 - r)),
        ("C", (x1, y1 - r + k), (x1 - r + k, y1), (x1 - r, y1)),
        ("L", (x0 + r, y1)),
        ("C", (x0 + r - k, y1), (x0, y1 - r + k), (x0, y1 - r)),
        ("L", (x0, y0 + r)),
        ("C", (x0, y0 + r - k), (x0 + r - k, y0), (x0 + r, y0)),
        ("Z",),
    ]


def reverse_ops(ops: list[tuple]) -> list[tuple]:
    """Reverse a closed path so it cuts a hole under non-zero winding."""
    # Expand to (kind, ctrl_points..., end_point) with an explicit start point.
    segs: list[tuple] = []
    start = None
    cur = None
    for op in ops:
        kind = op[0]
        if kind == "M":
            start = cur = op[1]
        elif kind == "L":
            segs.append((kind, cur, op[1]))
            cur = op[1]
        elif kind == "C":
            segs.append((kind, cur, op[1], op[2], op[3]))
            cur = op[3]
        elif kind == "Z":
            segs.append(("L", cur, start))
            cur = start

    out: list[tuple] = [("M", segs[-1][-1])]
    for seg in reversed(segs):
        if seg[0] == "L":
            out.append(("L", seg[1]))
        else:
            _, _, c1, c2, end = seg
            out.append(("C", c2, c1, seg[1]))
    out.append(("Z",))
    return out


def star_ops(cx: float, cy: float, r: float, waist: float = 0.30) -> list[tuple]:
    """A four-point "sparkle" star with concave sides, as cubic ops."""
    w = r * waist
    return [
        ("M", (cx, cy - r)),
        ("C", (cx + w, cy - w), (cx + w, cy - w), (cx + r, cy)),
        ("C", (cx + w, cy + w), (cx + w, cy + w), (cx, cy + r)),
        ("C", (cx - w, cy + w), (cx - w, cy + w), (cx - r, cy)),
        ("C", (cx - w, cy - w), (cx - w, cy - w), (cx, cy - r)),
        ("Z",),
    ]


def rr_ring(x, y, w, h, r) -> list[list[tuple]]:
    """A stroked rounded rectangle: outer contour + reversed inner one."""
    half = STROKE / 2
    outer = rr_ops(x, y, w, h, r)
    inner = rr_ops(x + half, y + half, w - STROKE, h - STROKE, max(r - half, 0.4))
    return [outer, reverse_ops(inner)]


# ---------------------------------------------------------------------------
# the two designs
# ---------------------------------------------------------------------------


def shorts_icon() -> list[list[tuple]]:
    """Classic keyboard: body, two rows of five keys, a spacebar."""
    contours = rr_ring(2.5, 7.0, 19.0, 11.0, 2.6)
    for row_y in (10.1, 12.5):
        for col_x in (6.4, 8.9, 11.4, 13.9, 16.4):
            contours.append(rr_ops(col_x - 0.7, row_y - 0.7, 1.4, 1.4, 0.42))
    contours.append(rr_ops(8.6, 14.5, 6.8, 1.7, 0.85))
    return contours


def anime4k_icon() -> list[list[tuple]]:
    """The "enhance" sparkle: one big four-point star and two small ones."""
    return [
        star_ops(10.4, 11.2, 6.4),
        star_ops(18.2, 6.9, 2.7, waist=0.34),
        star_ops(19.4, 15.8, 2.0, waist=0.34),
    ]


def bar_ops(cx: float, cy: float, length: float, thickness: float,
            angle: float) -> list[tuple]:
    """A bar as a closed polygon; ``angle`` in degrees, y down.

    The points are reversed on purpose: the contour has to wind the same way as
    ``star_ops``, or the non-zero fill rule turns the overlap into a *hole*
    instead of a union -- which is exactly what a slash through a sparkle must
    not be (it punched a diagonal slot through the star the first time).
    """
    a = math.radians(angle)
    dx, dy = math.cos(a), math.sin(a)
    nx, ny = -dy, dx
    hl, ht = length / 2, thickness / 2
    points = [
        (cx + dx * hl + nx * ht, cy + dy * hl + ny * ht),
        (cx + dx * hl - nx * ht, cy + dy * hl - ny * ht),
        (cx - dx * hl - nx * ht, cy - dy * hl - ny * ht),
        (cx - dx * hl + nx * ht, cy - dy * hl + ny * ht),
    ][::-1]
    return [("M", points[0])] + [("L", p) for p in points[1:]] + [("Z",)]


def anime4k_off_icon() -> list[list[tuple]]:
    """The same sparkle, slashed: the "shaders off" state.

    The slash is centred on the big star (10.4, 11.2) rather than on the 24-unit
    box, so it leaves the four arms symmetrical; the smallest star is dropped
    because the diagonal runs straight through the corner it sits in.
    """
    return [
        bar_ops(10.4, 11.2, 19.6, STROKE, 45),
        star_ops(10.4, 11.2, 6.4),
        star_ops(18.2, 6.9, 2.7, waist=0.34),
    ]


#: name -> (builder, description). One glyph serves both the plain and the
#: ``_filled`` ligature: these designs are already solid/keyed shapes, and a
#: heavier twin would just be the same drawing.
ICONS: dict[str, tuple] = {
    "anime4k": anime4k_icon,
    "shortcuts": shorts_icon,
    "anime4k_off": anime4k_off_icon,
}


# ---------------------------------------------------------------------------
# font plumbing
# ---------------------------------------------------------------------------


def glyph_from_contours(contours: list[list[tuple]]) -> Glyph:
    pen = TTGlyphPen(None)
    # Cubic paths have to become quadratics: TrueType has no cubic curves. The
    # tolerance is in font units -- 1 unit is 1/1024 em, well below a pixel.
    quad = Cu2QuPen(pen, max_err=1.0, reverse_direction=False)
    for ops in contours:
        cur = None
        for op in ops:
            kind = op[0]
            if kind == "M":
                cur = op[1]
                quad.moveTo(cur)
            elif kind == "L":
                cur = op[1]
                quad.lineTo(cur)
            elif kind == "C":
                c1, c2, end = op[1], op[2], op[3]
                quad.curveTo(c1, c2, end)
                cur = end
            elif kind == "Z":
                quad.closePath()
    return pen.glyph()


def to_font(contours: list[list[tuple]]) -> list[list[tuple]]:
    """Design coordinates (y down, 24 grid) -> font units (y up, 1024 em)."""
    out = []
    for ops in contours:
        conv = []
        for op in ops:
            if op[0] == "Z":
                conv.append(("Z",))
                continue
            pts = [((x * UNIT), (GRID - y) * UNIT) for x, y in op[1:]]
            conv.append((op[0], *pts))
        out.append(conv)
    return out


def ensure_placeholder(font: TTFont, ch: str) -> None:
    """Make sure ``ch`` is typeable: a blank, zero-advance glyph, as for the rest.

    The font only carries the ASCII characters its *own* ligature names need
    (``a b c d e f g h i k l m n o p r s t u v w x y z 0 1 3 5 _``) and every one
    of them is a blank zero-advance placeholder -- they exist purely as ligature
    input. ``fluent_anime4k`` needs ``4``, which upstream never needed, so add the
    same kind of placeholder rather than rename the icon around the gap. Only
    icon-font elements use this font, and their content is ligature names, so a
    blank ``4`` is not observable anywhere else.
    """
    cp = ord(ch)
    cmap = font.getBestCmap()
    if cp in cmap:
        return
    glyph_name = unicodedata.name(ch).split()[-1].lower()  # '4' -> 'four'
    if glyph_name in font.getGlyphOrder():
        raise SystemExit(f"glyph name {glyph_name!r} already taken")
    glyf = font["glyf"]
    glyph = Glyph()
    glyph.numberOfContours = 0
    glyph.xMin = glyph.yMin = glyph.xMax = glyph.yMax = 0
    glyf.glyphs[glyph_name] = glyph
    font.glyphOrder.append(glyph_name)
    font["hmtx"][glyph_name] = (0, 0)   # zero advance: invisible unless a ligature eats it
    font["maxp"].numGlyphs = len(font.glyphOrder)
    for table in font["cmap"].tables:
        if table.isUnicode():
            table.cmap[cp] = glyph_name
    print(f"added placeholder {ch!r} as {glyph_name}")


def add_ligature(font: TTFont, text: str, glyph_name: str) -> None:
    """Register ``text`` as a ligature that resolves to ``glyph_name``."""
    cmap = font.getBestCmap()
    subtable = font["GSUB"].table.LookupList.Lookup[0].SubTable[0]
    first_glyph = cmap[ord(text[0])]
    components = [cmap[ord(ch)] for ch in text[1:]]

    from fontTools.ttLib.tables import otTables

    lig = otTables.Ligature()
    lig.Component = components
    lig.LigGlyph = glyph_name
    lig.CompCount = len(components) + 1

    existing = subtable.ligatures.setdefault(first_glyph, [])
    # Longest first: OpenType wants that inside a LigatureSet, so a shorter name
    # cannot shadow e.g. fluent_shortcuts_filled. Insert rather than sort, to
    # leave the order upstream chose for its own ligatures untouched.
    at = next(
        (i for i, other in enumerate(existing) if len(other.Component) < len(components)),
        len(existing),
    )
    existing.insert(at, lig)


def ligature_texts(font: TTFont) -> set[str]:
    """Every string the font's GSUB table already swaps for a single glyph.

    The check cannot use glyph *names*: this font's ``post`` table is version 3.0
    (no names at all), so FontTools invents ``glyphNNNNN`` ones on load and any
    name we assign is gone after a save. Codepoints and ligature texts are the
    only stable identity.
    """
    cmap = font.getBestCmap()
    cp_of = {name: cp for cp, name in cmap.items()}
    texts: set[str] = set()
    for lookup in font["GSUB"].table.LookupList.Lookup:
        for subtable in lookup.SubTable:
            for first, ligatures in (subtable.ligatures or {}).items():
                for lig in ligatures:
                    run = [first] + list(lig.Component)
                    if all(g in cp_of for g in run):
                        texts.add("".join(chr(cp_of[g]) for g in run))
    return texts


def main() -> int:
    font = TTFont(FONT)
    glyf, hmtx, cmap_tables = font["glyf"], font["hmtx"], font["cmap"]
    order = font.getGlyphOrder()
    existing = set(order)
    already = ligature_texts(font)

    added = 0
    for index, (name, builder) in enumerate(ICONS.items()):
        glyph_name = f"aniworld_{name}"
        wanted = [f"fluent_{name}{suffix}" for suffix in ("", "_filled")]
        if glyph_name in existing or any(text in already for text in wanted):
            # Re-running on an already patched font must not duplicate anything:
            # the glyph, its codepoint and its ligatures are one unit.
            print(f"{glyph_name}: already in the font, skipped")
            continue

        contours = to_font(builder())
        glyph = glyph_from_contours(contours)
        # Direction/left side bearing: TTGlyphPen records outlines, the metrics
        # need the bbox that FontTools recomputes on compile.
        glyph.recalcBounds(glyf)

        glyf.glyphs[glyph_name] = glyph
        font.glyphOrder.append(glyph_name)
        hmtx[glyph_name] = (ADVANCE, int(glyph.xMin))
        font["maxp"].numGlyphs = len(font.glyphOrder)

        cp = START_CP + index
        for table in cmap_tables.tables:
            if table.isUnicode():
                table.cmap[cp] = glyph_name

        for suffix in ("", "_filled"):
            text = f"fluent_{name}{suffix}"
            for ch in text:
                ensure_placeholder(font, ch)
            add_ligature(font, text, glyph_name)

        print(f"{glyph_name}: U+{cp:04X}  bbox=({glyph.xMin},{glyph.yMin})-({glyph.xMax},{glyph.yMax})")
        added += 1

    if not added:
        # Recompiling an unchanged font still rewrites the file; leave it alone so
        # a run on the shipped font is a no-op in git too.
        print("nothing to do: the font already carries every icon")
        return 0
    font.save(FONT)
    print(f"wrote {FONT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
