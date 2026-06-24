from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets"
ICONSET_DIR = ASSET_DIR / "查图.iconset"
FONT_PATHS = [
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/Supplemental/Songti.ttc",
]


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for font_path in FONT_PATHS:
        try:
            return ImageFont.truetype(font_path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def make_base_icon(size: int) -> Image.Image:
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    radius = int(size * 0.21)

    for y in range(size):
        t = y / max(size - 1, 1)
        r = round(24 + (52 - 24) * t)
        g = round(103 + (164 - 103) * t)
        b = round(160 + (210 - 160) * t)
        draw.line([(0, y), (size, y)], fill=(r, g, b, 255))

    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=255)
    image.putalpha(mask)

    overlay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.ellipse(
        (int(size * 0.06), int(size * 0.04), int(size * 0.94), int(size * 0.86)),
        fill=(255, 255, 255, 26),
    )
    image.alpha_composite(overlay)

    font = load_font(int(size * 0.34))
    text = "查图"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (size - text_w) / 2 - bbox[0]
    y = (size - text_h) / 2 - bbox[1] - size * 0.015

    shadow_offset = max(2, size // 80)
    draw.text((x, y + shadow_offset), text, font=font, fill=(0, 32, 60, 95))
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))

    return image


def main() -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    ICONSET_DIR.mkdir(parents=True, exist_ok=True)
    base = make_base_icon(1024)
    base.save(ASSET_DIR / "查图-icon-source.png")

    sizes = [
        (16, "icon_16x16.png"),
        (32, "icon_16x16@2x.png"),
        (32, "icon_32x32.png"),
        (64, "icon_32x32@2x.png"),
        (128, "icon_128x128.png"),
        (256, "icon_128x128@2x.png"),
        (256, "icon_256x256.png"),
        (512, "icon_256x256@2x.png"),
        (512, "icon_512x512.png"),
        (1024, "icon_512x512@2x.png"),
    ]

    for target_size, filename in sizes:
        resized = base.resize((target_size, target_size), Image.Resampling.LANCZOS)
        resized.save(ICONSET_DIR / filename)


if __name__ == "__main__":
    main()
