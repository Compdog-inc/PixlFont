from fontTools.colorLib.builder import buildCOLR, buildCPAL
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
import argparse
import random
from pathlib import Path
from datetime import datetime, timezone
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.otTables import PaintFormat

from fontTools.ttLib.tables._g_l_y_f import Glyph

empty = Glyph()
empty.numberOfContours = 0

unitsPerEm = 1000
advanceWidth = 600
ascent = 800
descent = -200

# ASCII range
chars = [chr(i) for i in range(32, 127)]

DEFAULT_BANDS = {
    "regular": (10, 245),
    "light": (120, 240),
    "dark": (40, 170),
}


def glyph_name(c):
    return f"uni{ord(c):04X}"


# Base square glyph (same for all)
def make_square():
    pen = TTGlyphPen(None)
    pen.moveTo((100, 0))
    pen.lineTo((700, 0))
    pen.lineTo((700, 700))
    pen.lineTo((100, 700))
    pen.closePath()
    return pen.glyph()


def export_web_font(source_ttf, output_path, flavor):
    try:
        web_font = TTFont(str(source_ttf))
        web_font.flavor = flavor
        web_font.save(str(output_path))
        web_font.close()
        return output_path
    except Exception as exc:
        print(f"Warning: could not generate {output_path}: {exc}")
        return None


def parse_band(value, name):
    try:
        min_text, max_text = value.split(",", 1)
        band_min = int(min_text.strip())
        band_max = int(max_text.strip())
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid {name} band '{value}'. Use min,max (example: 40,180)."
        ) from exc

    if not (0 <= band_min <= 255 and 0 <= band_max <= 255):
        raise argparse.ArgumentTypeError(
            f"{name} band values must be in 0..255, got {band_min},{band_max}."
        )
    if band_min > band_max:
        raise argparse.ArgumentTypeError(
            f"{name} band min cannot be greater than max, got {band_min},{band_max}."
        )

    return (band_min, band_max)


def parse_cli_config():
    parser = argparse.ArgumentParser(
        description="Generate PixlFont variants with configurable grayscale bands."
    )
    parser.add_argument(
        "--regular-band",
        default=f"{DEFAULT_BANDS['regular'][0]},{DEFAULT_BANDS['regular'][1]}",
        help="Grayscale range for regular variant as min,max (default: 10,245).",
    )
    parser.add_argument(
        "--light-band",
        default=f"{DEFAULT_BANDS['light'][0]},{DEFAULT_BANDS['light'][1]}",
        help="Grayscale range for light variant as min,max (default: 120,240).",
    )
    parser.add_argument(
        "--dark-band",
        default=f"{DEFAULT_BANDS['dark'][0]},{DEFAULT_BANDS['dark'][1]}",
        help="Grayscale range for dark variant as min,max (default: 40,170).",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory where generated font files are written (default: output).",
    )

    args = parser.parse_args()
    bands = {
        "regular": parse_band(args.regular_band, "regular"),
        "light": parse_band(args.light_band, "light"),
        "dark": parse_band(args.dark_band, "dark"),
    }
    output_dir = Path(args.output_dir)
    return bands, output_dir


def generate_variant(base_name, family_name, gray_min, gray_max, output_dir):
    fb = FontBuilder(unitsPerEm, isTTF=True)
    char_to_glyph = {c: glyph_name(c) for c in chars}
    glyphOrder = [".notdef"] + [char_to_glyph[c] for c in chars]
    fb.setupGlyphOrder(glyphOrder)

    glyphs = {".notdef": make_square()}
    metrics = {".notdef": (advanceWidth, 0)}

    for c in chars:
        gname = char_to_glyph[c]
        glyphs[gname] = empty if c == " " else make_square()
        metrics[gname] = (advanceWidth, 0)

    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=ascent, descent=descent)
    fb.setupCharacterMap({ord(c): char_to_glyph[c] for c in chars})

    palette = []
    colorGlyphs = {}
    for c in chars:
        gname = char_to_glyph[c]
        gray = random.randint(gray_min, gray_max)
        rgba = (gray / 255, gray / 255, gray / 255, 1.0)
        palette.append(rgba)
        paletteIndex = len(palette) - 1
        colorGlyphs[gname] = {
            "Format": PaintFormat.PaintGlyph,
            "Glyph": gname,
            "Paint": {
                "Format": PaintFormat.PaintSolid,
                "PaletteIndex": paletteIndex,
                "Alpha": 1.0,
            },
        }

    colorGlyphs[".notdef"] = {
        "Format": PaintFormat.PaintGlyph,
        "Glyph": ".notdef",
        "Paint": {
            "Format": PaintFormat.PaintSolid,
            "PaletteIndex": 0,
            "Alpha": 1.0,
        },
    }

    fb.font["CPAL"] = buildCPAL([palette])
    fb.font["COLR"] = buildCOLR(colorGlyphs, version=1)

    full_name = f"{family_name} Regular"
    fb.setupNameTable(
        {
            "familyName": family_name,
            "styleName": "Regular",
            "uniqueFontIdentifier": full_name,
            "fullName": full_name,
            "psName": base_name,
        }
    )

    fb.setupMaxp()
    fb.setupHead()

    # Use current timestamp in Mac epoch seconds to avoid invalid/low head times.
    mac_epoch = datetime(1904, 1, 1, tzinfo=timezone.utc)
    now_mac_seconds = int((datetime.now(timezone.utc) - mac_epoch).total_seconds())
    head_table = fb.font["head"]
    setattr(head_table, "created", now_mac_seconds)
    setattr(head_table, "modified", now_mac_seconds)

    fb.setupOS2()
    os2_table = fb.font["OS/2"]
    setattr(os2_table, "fsType", 0)
    fb.setupPost()

    ttf_path = output_dir / f"{base_name}.ttf"
    fb.save(str(ttf_path))

    generated = [str(ttf_path)]
    woff2_path = export_web_font(ttf_path, output_dir / f"{base_name}.woff2", "woff2")
    if woff2_path:
        generated.append(str(woff2_path))
    woff_path = export_web_font(ttf_path, output_dir / f"{base_name}.woff", "woff")
    if woff_path:
        generated.append(str(woff_path))

    return generated


bands, output_dir = parse_cli_config()
output_dir.mkdir(parents=True, exist_ok=True)
variants = [
    ("PixlFont-Regular", "PixlFont", bands["regular"][0], bands["regular"][1]),
    (
        "PixlFont-Light-Regular",
        "PixlFont Light",
        bands["light"][0],
        bands["light"][1],
    ),
    ("PixlFont-Dark-Regular", "PixlFont Dark", bands["dark"][0], bands["dark"][1]),
]

all_generated_paths = []
for base_name, family_name, gray_min, gray_max in variants:
    all_generated_paths.extend(
        generate_variant(base_name, family_name, gray_min, gray_max, output_dir)
    )

print("Generated font files:")
for path in all_generated_paths:
    print(f"- {path}")
