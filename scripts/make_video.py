"""
Builds the final MP4 with FFmpeg:
  - each image gets a slow pan + zoom (Ken Burns effect)
  - scenes crossfade into each other
  - each scene's voiceover plays over its image, crossfading too
"""
import json
import subprocess

from config import WIDTH, HEIGHT, FPS, CROSSFADE


def get_duration(path):
    """Return the length (seconds) of an audio/video file using ffprobe."""
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "json", path,
    ])
    return float(json.loads(out)["format"]["duration"])


def _kenburns(idx, frames):
    """
    Ken Burns filter for one looped image input.

    IMPORTANT: the input is looped (-loop 1 -t duration), so it already arrives
    as `frames` separate frames. We therefore use d=1 (emit one output frame per
    input frame) and drive the slow zoom with `on` (the output frame counter).
    Using d=frames here would multiply frames and create a giant, hours-long video.
    """
    # Zoom from 1.0 up to ~1.20 across the whole scene, centered.
    zoom = f"min(1+0.0006*on,1.20)"
    x, y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    return (
        f"[{idx}:v]scale={WIDTH*2}:{HEIGHT*2},"
        f"zoompan=z='{zoom}':d=1:x='{x}':y='{y}':"
        f"s={WIDTH}x{HEIGHT}:fps={FPS},setsar=1,format=yuv420p[v{idx}]"
    )


def build_video(scenes, out_path):
    """
    scenes: list of dicts with keys 'image' and 'audio'.
    Produces out_path (mp4).
    """
    n = len(scenes)
    durations = [get_duration(s["audio"]) for s in scenes]

    cmd = ["ffmpeg", "-y"]
    # Image inputs first (0 .. n-1)
    for s, d in zip(scenes, durations):
        cmd += ["-loop", "1", "-framerate", str(FPS), "-t", f"{d:.3f}", "-i", s["image"]]
    # Audio inputs next (n .. 2n-1)
    for s in scenes:
        cmd += ["-i", s["audio"]]

    filters = []

    # 1) Ken Burns for each image
    for i, d in enumerate(durations):
        frames = max(int(round(d * FPS)), 1)
        filters.append(_kenburns(i, frames))

    # 2) Crossfade the video scenes together
    if n == 1:
        last_v = "v0"
    else:
        acc = durations[0]
        prev = "v0"
        for i in range(1, n):
            offset = acc - CROSSFADE
            out = f"vx{i}"
            filters.append(
                f"[{prev}][v{i}]xfade=transition=fade:"
                f"duration={CROSSFADE}:offset={offset:.3f}[{out}]"
            )
            acc += durations[i] - CROSSFADE
            prev = out
        last_v = prev

    # 3) Crossfade the audio tracks together
    if n == 1:
        last_a = f"{n}:a"
    else:
        prev = f"{n}:a"
        for i in range(1, n):
            out = f"ax{i}"
            filters.append(
                f"[{prev}][{n + i}:a]acrossfade=d={CROSSFADE}[{out}]"
            )
            prev = out
        last_a = prev

    filter_complex = ";".join(filters)

    cmd += [
        "-filter_complex", filter_complex,
        "-map", f"[{last_v}]",
        "-map", f"[{last_a}]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        out_path,
    ]

    subprocess.run(cmd, check=True)
    return out_path
