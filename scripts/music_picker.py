"""
Picks a random background music track and builds the credit line that must
appear in the YouTube description (Kevin MacLeod tracks are free under
Creative Commons BY 4.0, which only requires attribution).
"""
import glob
import os
import random

from config import MUSIC_DIR


def _title_from_filename(path):
    name = os.path.splitext(os.path.basename(path))[0]
    return name.replace("-", " ").title()


def pick_music():
    """Return (music_path, credit_text). If no music exists, return (None, "")."""
    tracks = sorted(glob.glob(os.path.join(MUSIC_DIR, "*.mp3")))
    if not tracks:
        return None, ""

    track = random.choice(tracks)
    title = _title_from_filename(track)
    credit = (
        f'Music: "{title}" by Kevin MacLeod (incompetech.com)\n'
        f"Licensed under Creative Commons: By Attribution 4.0 License\n"
        f"http://creativecommons.org/licenses/by/4.0/"
    )
    return track, credit


if __name__ == "__main__":
    print(pick_music())
