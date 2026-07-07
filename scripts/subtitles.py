"""
Builds a cute .ass subtitle file, timed to match each scene's narration.

Each scene's text is split into short phrases and spread across that scene's
time on screen, so kids see one easy line at a time (big, rounded, colorful).
"""
import re

from config import WIDTH, HEIGHT, CROSSFADE, SUBTITLE_FONT


def _fmt(t):
    """Seconds -> ASS time  H:MM:SS.cs"""
    if t < 0:
        t = 0
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    cs = int(round((t - int(t)) * 100))
    if cs == 100:
        cs = 99
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _split_sentences(text):
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def _header():
    # Colors are &HAABBGGRR. White fill, thick dark-purple outline, soft shadow.
    return f"""[Script Info]
ScriptType: v4.00+
PlayResX: {WIDTH}
PlayResY: {HEIGHT}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cute,{SUBTITLE_FONT},80,&H00FFFFFF,&H000000FF,&H00762C4A,&H64000000,-1,0,0,0,100,100,0,0,1,6,3,2,120,120,120,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def build_ass(scenes, durations, out_path):
    """
    scenes: list of dicts with a 'narration' key.
    durations: matching list of each scene's audio length (seconds).
    Writes an .ass file to out_path.
    """
    lines = [_header()]

    start = 0.0
    for i, scene in enumerate(scenes):
        scene_start = start
        scene_len = durations[i]
        # Leave a little gap at the transition so text doesn't linger across cuts.
        usable = max(scene_len - CROSSFADE, 0.5)

        sentences = _split_sentences(scene.get("narration", "")) or [""]
        total_chars = sum(len(s) for s in sentences) or 1

        t = scene_start
        for sent in sentences:
            share = (len(sent) / total_chars) * usable
            s0 = t
            s1 = t + share
            text = sent.replace("\n", " ").strip()
            if text:
                lines.append(
                    f"Dialogue: 0,{_fmt(s0)},{_fmt(s1)},Cute,,0,0,0,,{text}"
                )
            t = s1

        # Next scene begins after this one, minus the crossfade overlap.
        start = scene_start + scene_len - CROSSFADE

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return out_path
