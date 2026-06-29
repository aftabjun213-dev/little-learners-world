"""
Generates a seamless, tileable sparkle overlay used to add gentle floating
'magic' particles on top of the video (a free way to make it feel animated).

The image is WIDTH wide and HEIGHT*2 tall, with the bottom half identical to
the top half, so it can be scrolled upward forever with no visible seam.
"""
import random

from PIL import Image, ImageDraw, ImageFilter


def make_sparkle_overlay(width, height, out_path, count=70, seed=7):
    random.seed(seed)
    tile = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(tile)

    for _ in range(count):
        x = random.randint(0, width)
        y = random.randint(0, height)
        r = random.randint(2, 7)
        alpha = random.randint(40, 170)
        draw.ellipse([x - r, y - r, x + r, y + r],
                     fill=(255, 255, 255, alpha))

    tile = tile.filter(ImageFilter.GaussianBlur(1.6))

    full = Image.new("RGBA", (width, height * 2), (0, 0, 0, 0))
    full.paste(tile, (0, 0))
    full.paste(tile, (0, height))   # identical bottom half => seamless loop
    full.save(out_path)
    return out_path


if __name__ == "__main__":
    make_sparkle_overlay(1280, 720, "sparkles.png")
    print("Wrote sparkles.png")
