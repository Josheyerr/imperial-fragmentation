"""Build the Workshop icon (preview.jpg) and the launcher thumbnail from the clean source art.

The art sits fully inside a continuous gold frame, so nothing is hidden under the border,
and the title is sized to fit inside the frame with room to spare.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "art" / "preview_source.jpg"
PREVIEW = ROOT / "preview.jpg"
THUMBNAIL = Path(
    r"C:\Users\kmkjk\OneDrive\Documents\Paradox Interactive\Crusader Kings III\mod\imperial_fragmentation\thumbnail.png"
)
FONT = r"C:\Windows\Fonts\BOOKOSB.TTF"

SIZE = 1024
GOLD = (214, 176, 98)
GOLD_LIGHT = (246, 220, 150)
GOLD_DARK = (128, 90, 40)
BACK = (14, 9, 6)

OUTER = 14        # outer frame line inset
ART = 44          # art inset; the inner frame line hugs this edge


def gradient_text(draw_size, text, font, top, bottom):
    """Text filled with a vertical gold gradient, returned as an RGBA layer."""
    mask = Image.new("L", draw_size, 0)
    ImageDraw.Draw(mask).text((0, 0), text, font=font, fill=255)
    grad = Image.new("RGBA", draw_size)
    gd = ImageDraw.Draw(grad)
    h = draw_size[1]
    for y in range(h):
        t = y / max(h - 1, 1)
        gd.line([(0, y), (draw_size[0], y)], fill=tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)) + (255,))
    grad.putalpha(mask)
    return grad


def fit_font(text, max_width, start):
    size = start
    while size > 10:
        font = ImageFont.truetype(FONT, size)
        left, _, right, _ = font.getbbox(text)
        if right - left <= max_width:
            return font
        size -= 2
    return ImageFont.truetype(FONT, size)


def place_title(canvas, text, font, centre_y):
    left, top, right, bottom = font.getbbox(text)
    w, h = right - left, bottom - top
    pad = 24
    layer_size = (w + pad * 2, h + pad * 2)
    origin = (SIZE // 2 - layer_size[0] // 2, int(centre_y - layer_size[1] / 2))

    # soft shadow
    shadow = Image.new("L", layer_size, 0)
    ImageDraw.Draw(shadow).text((pad - left + 4, pad - top + 6), text, font=font, fill=230)
    shadow = shadow.filter(ImageFilter.GaussianBlur(7))
    canvas.paste((0, 0, 0), origin, shadow)

    # dark outline
    outline = Image.new("L", layer_size, 0)
    ImageDraw.Draw(outline).text((pad - left, pad - top), text, font=font, fill=255, stroke_width=3, stroke_fill=255)
    canvas.paste((34, 18, 8), origin, outline)

    # gold fill: a vertical gradient over the glyph area, masked by the letters
    mask = Image.new("L", layer_size, 0)
    ImageDraw.Draw(mask).text((pad - left, pad - top), text, font=font, fill=255)
    grad = Image.new("RGB", layer_size)
    gd = ImageDraw.Draw(grad)
    for y in range(layer_size[1]):
        t = min(max((y - pad) / max(h, 1), 0), 1)
        gd.line([(0, y), (layer_size[0], y)], fill=tuple(int(GOLD_LIGHT[i] + (GOLD[i] * 0.8 - GOLD_LIGHT[i]) * t) for i in range(3)))
    canvas.paste(grad, origin, mask)


def build():
    art = Image.open(SOURCE).convert("RGB")
    inner = SIZE - ART * 2
    art = art.resize((inner, inner), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))

    # darken the lower third so the title reads over the castle
    shade = Image.new("L", (inner, inner), 0)
    sd = ImageDraw.Draw(shade)
    start = int(inner * 0.58)
    for y in range(start, inner):
        t = (y - start) / (inner - start)
        sd.line([(0, y), (inner, y)], fill=int(190 * t ** 1.3))
    art.paste((0, 0, 0), (0, 0), shade)

    canvas = Image.new("RGB", (SIZE, SIZE), BACK)
    canvas.paste(art, (ART, ART))
    d = ImageDraw.Draw(canvas)

    # continuous double frame
    d.rectangle([OUTER, OUTER, SIZE - 1 - OUTER, SIZE - 1 - OUTER], outline=GOLD, width=7)
    d.rectangle([OUTER + 2, OUTER + 2, SIZE - 1 - OUTER - 2, SIZE - 1 - OUTER - 2], outline=GOLD_LIGHT, width=2)
    d.rectangle([ART - 5, ART - 5, SIZE - 1 - ART + 5, SIZE - 1 - ART + 5], outline=GOLD_DARK, width=2)
    d.rectangle([ART - 3, ART - 3, SIZE - 1 - ART + 3, SIZE - 1 - ART + 3], outline=GOLD, width=3)

    # corner diamonds where the two frame lines meet
    for cx in (OUTER + 15, SIZE - 1 - OUTER - 15):
        for cy in (OUTER + 15, SIZE - 1 - OUTER - 15):
            r = 13
            d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=GOLD, outline=GOLD_DARK)
            d.polygon([(cx, cy - 5), (cx + 5, cy), (cx, cy + 5), (cx - 5, cy)], fill=GOLD_LIGHT)

    # title, kept well inside the frame
    max_w = inner - 220
    big = fit_font("FRAGMENTATION", max_w, 110)
    small = ImageFont.truetype(FONT, int(big.size * 0.95))
    place_title(canvas, "IMPERIAL", small, 790)
    place_title(canvas, "FRAGMENTATION", big, 905)

    # divider between the two lines
    d = ImageDraw.Draw(canvas)
    y = 848
    d.line([(SIZE // 2 - 230, y), (SIZE // 2 - 16, y)], fill=GOLD, width=3)
    d.line([(SIZE // 2 + 16, y), (SIZE // 2 + 230, y)], fill=GOLD, width=3)
    d.polygon([(SIZE // 2, y - 9), (SIZE // 2 + 9, y), (SIZE // 2, y + 9), (SIZE // 2 - 9, y)], fill=GOLD_LIGHT, outline=GOLD_DARK)

    canvas.save(PREVIEW, quality=92, optimize=True)
    canvas.resize((256, 256), Image.LANCZOS).save(THUMBNAIL, optimize=True)
    print("wrote", PREVIEW, "and", THUMBNAIL)


if __name__ == "__main__":
    build()
