"""
Central settings for Little Learners World.
You can change these by editing the values below, or by setting them
as environment variables / GitHub Action variables.
"""
import os

# ----- Channel branding -----
CHANNEL_NAME = "Little Learners World"

# ----- Claude (script writing) -----
# Haiku is the cheapest capable model -> keeps your cost very low.
CLAUDE_MODEL = "claude-haiku-4-5-20251001"

# ----- Voice (edge-tts, free) -----
# A pool of the most NATURAL-sounding voices (the newer "Multilingual" models
# are far less robotic than the older ones). The robot picks a different one
# each episode so the channel doesn't sound repetitive.
VOICES = [
    "en-US-AvaMultilingualNeural",      # warm, expressive woman (very natural)
    "en-US-EmmaMultilingualNeural",     # gentle, friendly woman
    "en-US-AndrewMultilingualNeural",   # warm, conversational man
    "en-US-BrianMultilingualNeural",    # relaxed, friendly man
]
# Fallback single voice (used if the pool is somehow empty).
VOICE = os.environ.get("VOICE", "en-US-AvaMultilingualNeural")

# A natural, gentle pace. (Too slow makes neural voices sound robotic.)
VOICE_RATE = os.environ.get("VOICE_RATE", "-4%")

# ----- Video look -----
WIDTH = 1920           # Full HD width (1080p)
HEIGHT = 1080          # Full HD height
FPS = 25
CROSSFADE = 0.6          # seconds of crossfade between scenes
SCENE_COUNT = 16         # how many scenes (images) per video (~5-6 min total)
SECONDS_PER_SCENE = 20   # rough target narration length per scene

# ----- Background music -----
MUSIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "music")
MUSIC_VOLUME = 0.23      # how loud the music is under the voice (0.0 - 1.0)

# ----- Subtitles -----
SUBTITLES = True         # burn cute captions onto the video
FONTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "fonts")
SUBTITLE_FONT = "Baloo 2"

# ----- Shorts (vertical 9:16, under 60s) -----
SHORT_WIDTH = 1080
SHORT_HEIGHT = 1920
SHORT_SCENE_COUNT = 4          # ~4 quick scenes
SHORT_SECONDS_PER_SCENE = 11   # ~44s total, safely under the 60s Shorts limit
# One publish time per short => this list also sets HOW MANY shorts per day.
# Spread across peak kid-viewing windows (local time): late morning,
# after-nap afternoon, and early evening.
SHORT_PUBLISH_HOURS = [11, 15, 19]

# ----- Publishing -----
# Your local timezone, used to schedule the 8am publish time.
# Examples: "America/New_York", "America/Los_Angeles",
#           "Europe/London", "Asia/Seoul", "Asia/Kolkata"
TIMEZONE = os.environ.get("TIMEZONE") or "America/Los_Angeles"
PUBLISH_HOUR = int(os.environ.get("PUBLISH_HOUR") or "8")   # 8 = 8am

# Where temporary files are written
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
