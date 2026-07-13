"""
Builds the final MP4 with FFmpeg:
  - each image gets dynamic motion (varied pan + zoom, "Ken Burns")
  - scenes transition with varied effects (fades, slides, wipes, circles)
  - gentle floating sparkles drift over everything (free "live" feel)
  - each scene's voiceover plays over its image, crossfading too
  - soft background music plays underneath, with fade in/out
"""
import json
import os
import subprocess

from config import WIDTH, HEIGHT, FPS, CROSSFADE, MUSIC_VOLUME, SUBTITLES, FONTS_DIR
from subtitles import build_ass

# A rotating set of gentle, kid-friendly scene transitions.
TRANSITIONS = [
    "fade", "smoothleft", "circleopen", "slideup", "dissolve",
    "smoothright", "wiperight", "circleclose", "fadeblack", "slidedown",
]

SPARKLE_SPEED = 30   # pixels/second the sparkle layer drifts upward


def get_duration(path):
    """Return the length (seconds) of an audio/video file using ffprobe."""
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "json", path,
    ])
    return float(json.loads(out)["format"]["duration"])


def _kenburns(idx, frames, width, height):
    """
    Dynamic motion for one looped image input. Varies direction per scene.

    The input is looped (-loop 1 -t duration), so it already arrives as `frames`
    frames. We use d=1 (one output per input frame) and drive motion with `on`
    (the output frame counter). Using d=frames would multiply frames and create
    a giant, hours-long video.
    """
    preset = idx % 4
    if preset == 0:          # slow zoom in, centered
        z = "min(1+0.0006*on,1.18)"
        x, y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    elif preset == 1:        # zoom in while panning left -> right
        z = "min(1+0.0005*on,1.16)"
        x, y = f"(iw-iw/zoom)*on/{frames}", "ih/2-(ih/zoom/2)"
    elif preset == 2:        # zoom in while panning top -> bottom
        z = "min(1+0.0005*on,1.16)"
        x, y = "iw/2-(iw/zoom/2)", f"(ih-ih/zoom)*on/{frames}"
    else:                    # gentle zoom out, centered
        z = "max(1.18-0.0006*on,1.0)"
        x, y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"

    # Supersample 1.5x for a crisp pan/zoom without the CPU cost of full 4K.
    ss_w, ss_h = int(width * 1.5), int(height * 1.5)
    return (
        f"[{idx}:v]scale={ss_w}:{ss_h},"
        f"zoompan=z='{z}':d=1:x='{x}':y='{y}':"
        f"s={width}x{height}:fps={FPS},setsar=1,format=yuv420p[v{idx}]"
    )


def build_video(scenes, out_path, music_path=None, sparkle_path=None,
                width=None, height=None):
    """
    scenes: list of dicts with keys 'image' and 'audio'.
    music_path: optional mp3 to play softly underneath.
    sparkle_path: optional PNG (width x height*2) of drifting particles.
    width/height default to the main landscape size (pass vertical for Shorts).
    Produces out_path (mp4).
    """
    width = width or WIDTH
    height = height or HEIGHT
    n = len(scenes)
    durations = [get_duration(s["audio"]) for s in scenes]
    # The intended final length (scenes overlap by CROSSFADE each transition).
    total = sum(durations) - (n - 1) * CROSSFADE

    cmd = ["ffmpeg", "-y"]
    # Image inputs first (0 .. n-1)
    for s, d in zip(scenes, durations):
        cmd += ["-loop", "1", "-framerate", str(FPS), "-t", f"{d:.3f}", "-i", s["image"]]
    # Audio inputs next (n .. 2n-1)
    for s in scenes:
        cmd += ["-i", s["audio"]]

    input_count = 2 * n
    # Optional background music input (looped forever; trimmed later)
    music_idx = None
    if music_path:
        music_idx = input_count
        cmd += ["-stream_loop", "-1", "-i", music_path]
        input_count += 1
    # Optional sparkle overlay (a still PNG, looped)
    sparkle_idx = None
    if sparkle_path:
        sparkle_idx = input_count
        cmd += ["-loop", "1", "-framerate", str(FPS), "-i", sparkle_path]
        input_count += 1

    filters = []

    # 1) Motion for each image
    for i, d in enumerate(durations):
        frames = max(int(round(d * FPS)), 1)
        filters.append(_kenburns(i, frames, width, height))

    # 2) Transition the video scenes together (varied effects)
    if n == 1:
        last_v = "v0"
    else:
        acc = durations[0]
        prev = "v0"
        for i in range(1, n):
            offset = acc - CROSSFADE
            out = f"vx{i}"
            trans = TRANSITIONS[i % len(TRANSITIONS)]
            filters.append(
                f"[{prev}][v{i}]xfade=transition={trans}:"
                f"duration={CROSSFADE}:offset={offset:.3f}[{out}]"
            )
            acc += durations[i] - CROSSFADE
            prev = out
        last_v = prev

    # 2b) Drift floating sparkles over the whole video
    if sparkle_idx is not None:
        filters.append(
            f"[{sparkle_idx}:v]scale={width}:{height*2},format=rgba[spr]"
        )
        filters.append(
            f"[{last_v}][spr]overlay=x=0:"
            f"y='-(mod(t*{SPARKLE_SPEED},{height}))':"
            f"format=yuv420:shortest=1[outv]"
        )
        last_v = "outv"

    # 2c) Burn cute subtitles (timed to each scene's narration)
    if SUBTITLES and any(s.get("narration") for s in scenes):
        ass_path = os.path.join(
            os.path.dirname(os.path.abspath(out_path)), "subs.ass"
        )
        build_ass(scenes, durations, ass_path, width, height)
        ass_f = ass_path.replace("\\", "/")
        fonts_f = FONTS_DIR.replace("\\", "/")
        filters.append(
            f"[{last_v}]subtitles=filename='{ass_f}':fontsdir='{fonts_f}'[vsub]"
        )
        last_v = "vsub"

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

    # 3b) Mix soft background music under the narration (fade in + fade out)
    final_a = last_a
    if music_idx is not None:
        fade_out_start = max(total - 3.0, 0.0)
        filters.append(
            f"[{music_idx}:a]volume={MUSIC_VOLUME},afade=t=in:st=0:d=2[bg]"
        )
        filters.append(
            f"[{last_a}][bg]amix=inputs=2:duration=first:normalize=0[amixed]"
        )
        filters.append(
            f"[amixed]afade=t=out:st={fade_out_start:.3f}:d=3[aout]"
        )
        final_a = "aout"

    filter_complex = ";".join(filters)

    cmd += [
        "-filter_complex", filter_complex,
        "-map", f"[{last_v}]",
        "-map", f"[{final_a}]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "superfast",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        # SAFETY: stop at the intended length no matter what the audio does.
        # Without this, a looped music track makes FFmpeg pad the video forever.
        "-t", f"{total:.3f}",
        "-shortest",
        out_path,
    ]

    subprocess.run(cmd, check=True)
    return out_path
