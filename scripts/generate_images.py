"""
Generates cartoon images for each scene.

- If REPLICATE_API_TOKEN is set, it uses Flux (high quality, ~$0.003/image).
- Otherwise it falls back to Pollinations.ai (free), so the channel never breaks.
"""
import os
import time
import urllib.parse

import requests

from config import WIDTH, HEIGHT

# Cheapest good Flux model on Replicate; great for bright cartoon art.
FLUX_MODEL = "black-forest-labs/flux-schnell"


def _pollinations(prompt, out_path, seed, retries):
    encoded = urllib.parse.quote(prompt)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width={WIDTH}&height={HEIGHT}&seed={seed}&nologo=true&model=flux"
    )
    last_err = None
    for attempt in range(retries):
        try:
            resp = requests.get(url, timeout=120)
            if resp.status_code == 200 and \
                    resp.headers.get("Content-Type", "").startswith("image"):
                with open(out_path, "wb") as f:
                    f.write(resp.content)
                return out_path
            last_err = f"status={resp.status_code}"
        except Exception as e:  # noqa: BLE001
            last_err = str(e)
        time.sleep(8 * (attempt + 1))
    raise RuntimeError(f"Pollinations failed after {retries} tries: {last_err}")


def _replicate(prompt, out_path, seed):
    import replicate  # imported here so it's only needed when a token exists

    output = replicate.run(
        FLUX_MODEL,
        input={
            "prompt": prompt,
            "aspect_ratio": "16:9",
            "output_format": "png",
            "num_outputs": 1,
            "seed": seed,
            "go_fast": True,
        },
    )
    item = output[0]
    if hasattr(item, "read"):          # newer replicate returns file objects
        data = item.read()
    else:                               # older versions return URLs
        data = requests.get(str(item), timeout=120).content
    with open(out_path, "wb") as f:
        f.write(data)
    return out_path


def generate_image(prompt, out_path, seed=0, retries=4):
    """Create one cartoon image. Uses Flux if available, else Pollinations."""
    if os.environ.get("REPLICATE_API_TOKEN"):
        try:
            return _replicate(prompt, out_path, seed)
        except Exception as e:  # noqa: BLE001
            print(f"  Flux failed ({e}); falling back to Pollinations...")
    return _pollinations(prompt, out_path, seed, retries)


if __name__ == "__main__":
    generate_image(
        "a happy yellow sun, soft cute 2D cartoon illustration for toddlers, "
        "bright cheerful colors, simple rounded shapes, storybook style, no text",
        "test.png",
        seed=42,
    )
    print("Wrote test.png")
