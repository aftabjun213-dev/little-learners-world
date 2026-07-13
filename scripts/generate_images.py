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

# Fast, cheap Flux for the many scene pictures (~$0.003 each)...
FLUX_MODEL = "black-forest-labs/flux-schnell"
# ...and the top-quality Flux for the ONE thumbnail per video (~$0.025-0.03).
FLUX_PREMIUM_MODEL = "black-forest-labs/flux-dev"


def _pollinations(prompt, out_path, seed, retries, width, height):
    encoded = urllib.parse.quote(prompt)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width={width}&height={height}&seed={seed}&nologo=true&model=flux"
    )
    last_err = None
    for attempt in range(retries):
        try:
            resp = requests.get(url, timeout=90)
            if resp.status_code == 200 and \
                    resp.headers.get("Content-Type", "").startswith("image"):
                with open(out_path, "wb") as f:
                    f.write(resp.content)
                return out_path
            last_err = f"status={resp.status_code}"
        except Exception as e:  # noqa: BLE001
            last_err = str(e)
        time.sleep(4 * (attempt + 1))
    raise RuntimeError(f"Pollinations failed after {retries} tries: {last_err}")


def _replicate(prompt, out_path, seed, aspect_ratio, premium=False,
               go_fast=True):
    """Call Replicate's HTTP API directly in sync mode.

    'Prefer: wait' caps how long a single attempt can hang - during Replicate
    incidents (E9828) predictions otherwise sit for 1-5 minutes before dying,
    which used to burn the whole job's time budget.
    """
    model = FLUX_PREMIUM_MODEL if premium else FLUX_MODEL
    token = os.environ["REPLICATE_API_TOKEN"].strip()
    headers = {"Authorization": f"Bearer {token}"}
    inputs = {
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "output_format": "png",
        "num_outputs": 1,
        "seed": seed,
    }
    if not premium:
        # go_fast=False uses Replicate's alternate (bf16) pipeline - slower
        # but on different infrastructure, so it often works when the fast
        # lane is having an incident.
        inputs["go_fast"] = go_fast

    resp = requests.post(
        f"https://api.replicate.com/v1/models/{model}/predictions",
        headers={**headers, "Prefer": "wait=60"},
        json={"input": inputs},
        timeout=90,
    )
    if resp.status_code == 429:
        raise RuntimeError(f"429 throttled: {resp.text[:150]}")
    resp.raise_for_status()
    pred = resp.json()
    status = pred.get("status")

    # If it's still queued after the sync wait, poll briefly then give up
    # (a healthy flux image finishes in a couple of seconds).
    get_url = (pred.get("urls") or {}).get("get")
    waited = 0
    while status in ("starting", "processing") and get_url and waited < 24:
        time.sleep(4)
        waited += 4
        pred = requests.get(get_url, headers=headers, timeout=30).json()
        status = pred.get("status")

    if status != "succeeded":
        cancel_url = (pred.get("urls") or {}).get("cancel")
        if status in ("starting", "processing") and cancel_url:
            try:  # don't pay for a prediction we've given up on
                requests.post(cancel_url, headers=headers, timeout=15)
            except Exception:  # noqa: BLE001
                pass
        raise RuntimeError(pred.get("error") or f"status={status}")

    out = pred.get("output")
    url = out[0] if isinstance(out, list) else out
    data = requests.get(url, timeout=120).content
    with open(out_path, "wb") as f:
        f.write(data)
    return out_path


# Run-level Flux health tracking. If Flux fails completely for 2 pictures in a
# row (e.g. account throttled below $5 credit -> endless E9828/429), we stop
# trying it for the REST of the run instead of burning minutes on doomed
# retries for all ~36 pictures.
_flux_failed_streak = 0
_flux_disabled = False
_flux_spacing = 0.0   # extra pause between calls once rate limiting is seen


def generate_image(prompt, out_path, seed=0, retries=4,
                   width=None, height=None, aspect_ratio="16:9",
                   premium=False):
    """Create one cartoon image. Uses Flux if available, else Pollinations.

    width/height default to the main (landscape) video size; pass the vertical
    size and aspect_ratio='9:16' for Shorts. premium=True uses the top-quality
    Flux model (reserved for thumbnails - it costs ~10x more per image).
    """
    global _flux_failed_streak, _flux_disabled, _flux_spacing
    width = width or WIDTH
    height = height or HEIGHT
    if os.environ.get("REPLICATE_API_TOKEN") and not _flux_disabled:
        for attempt in range(3):
            try:
                if _flux_spacing:
                    time.sleep(_flux_spacing)
                # Retries switch to the alternate pipeline (go_fast=False),
                # which often dodges incidents on the fast lane.
                result = _replicate(prompt, out_path, seed, aspect_ratio,
                                    premium=premium, go_fast=(attempt == 0))
                _flux_failed_streak = 0
                return result
            except Exception as e:  # noqa: BLE001
                msg = str(e)
                if "429" in msg or "throttled" in msg.lower():
                    # Low-credit accounts get 6 requests/min: space out calls
                    _flux_spacing = 11.0
                    print(f"  Flux rate-limited (attempt {attempt + 1}/3); "
                          f"pacing to ~6 requests/min...")
                    time.sleep(12)
                else:
                    print(f"  Flux attempt {attempt + 1}/3 failed "
                          f"({msg[:110]})")
                    time.sleep(5 * (attempt + 1))
        _flux_failed_streak += 1
        if _flux_failed_streak >= 2:
            _flux_disabled = True
            print("  Flux keeps failing - using Pollinations for the rest "
                  "of this run (check Replicate credit is above $5).")
        else:
            print("  Flux unavailable; falling back to Pollinations...")
    return _pollinations(prompt, out_path, seed, retries, width, height)


if __name__ == "__main__":
    generate_image(
        "a happy yellow sun, soft cute 2D cartoon illustration for toddlers, "
        "bright cheerful colors, simple rounded shapes, storybook style, no text",
        "test.png",
        seed=42,
    )
    print("Wrote test.png")
