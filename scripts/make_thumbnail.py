"""
Builds a dedicated, click-worthy thumbnail (instead of reusing scene 1):
  - ONE focal character close-up on a high-contrast background (Flux image)
  - 2-4 big punchy words in the cute Baloo 2 font with a thick outline
"""
import os

from PIL import Image, ImageDraw, ImageFont

from config import WIDTH, HEIGHT, FONTS_DIR

FONT_PATH = os.path.join(FONTS_DIR, "Baloo2.ttf")

# A small rotation of bright outline colors so thumbnails vary
OUTLINE_COLORS = [(75, 44, 118), (200, 60, 60), (30, 110, 190), (0, 130, 90)]


def add_thumbnail_text(image_path, text, out_path, episode_index=0):
    """Overlay big bold text onto the generated thumbnail image."""
    img = Image.open(image_path).convert("RGB")
    img = img.resize((WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)

    text = (text or "").strip().upper()
    if not text:
        img.save(out_path, quality=92)
        return out_path

    # Fit the text: start big, shrink until it fits within 90% of the width
    size = 230
    while size > 40:
        font = ImageFont.truetype(FONT_PATH, size)
        w = draw.textlength(text, font=font)
        if w <= WIDTH * 0.9:
            break
        size -= 8

    x = (WIDTH - w) / 2
    y = HEIGHT - size - 60          # near the bottom, clear of YouTube's timestamp
    outline = OUTLINE_COLORS[episode_index % len(OUTLINE_COLORS)]

    draw.text((x, y), text, font=font, fill=(255, 255, 255),
              stroke_width=max(6, size // 12), stroke_fill=outline)
    img.save(out_path, quality=92)
    return out_path


def make_thumbnail(generate_image_fn, thumb_prompt, thumb_text, out_dir,
                   seed=0, episode_index=0):
    """Generate the thumbnail image then stamp the text. Returns final path.

    generate_image_fn: the generate_image function (passed in to avoid a
    circular import).
    """
    raw = os.path.join(out_dir, "thumb_raw.png")
    final = os.path.join(out_dir, "thumbnail.png")
    # premium=True -> top-quality Flux model just for this one image per video
    generate_image_fn(thumb_prompt, raw, seed=seed, premium=True)
    return add_thumbnail_text(raw, thumb_text, final, episode_index)
