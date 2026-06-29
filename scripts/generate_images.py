"""
Generates cartoon images from text prompts using Pollinations.ai
(free, no API key needed).
"""
import time
import urllib.parse

import requests

from config import WIDTH, HEIGHT


def generate_image(prompt, out_path, seed=0, retries=4):
    """Download one cartoon image for the given prompt."""
    encoded = urllib.parse.quote(prompt)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width={WIDTH}&height={HEIGHT}&seed={seed}&nologo=true&model=flux"
    )

    last_err = None
    for attempt in range(retries):
        try:
            resp = requests.get(url, timeout=120)
            content_type = resp.headers.get("Content-Type", "")
            if resp.status_code == 200 and content_type.startswith("image"):
                with open(out_path, "wb") as f:
                    f.write(resp.content)
                return out_path
            last_err = f"status={resp.status_code} type={content_type}"
        except Exception as e:  # noqa: BLE001
            last_err = str(e)
        # Wait and retry (Pollinations can be busy)
        time.sleep(8 * (attempt + 1))

    raise RuntimeError(f"Could not generate image after {retries} tries: {last_err}")


if __name__ == "__main__":
    generate_image(
        "a happy yellow sun, soft cute 2D cartoon illustration for toddlers, "
        "bright cheerful colors, simple rounded shapes, storybook style, no text",
        "test.png",
        seed=42,
    )
    print("Wrote test.png")
