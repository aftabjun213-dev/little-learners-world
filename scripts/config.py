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
# A pool of warm, friendly, kid-appropriate narrator voices. The robot picks a
# different one for each episode so the channel doesn't sound repetitive.
VOICES = [
    "en-US-AvaNeural",       # natural, warm woman (very expressive)
    "en-US-EmmaNeural",      # gentle, friendly woman
    "en-US-JennyNeural",     # warm, friendly woman
    "en-US-AriaNeural",      # bright, cheerful woman
    "en-US-AndrewNeural",    # warm, friendly man
    "en-US-BrianNeural",     # relaxed, friendly man
    "en-GB-SoniaNeural",     # calm British woman
    "en-AU-NatashaNeural",   # cheerful Australian woman
]
# Fallback single voice (used if the pool is somehow empty).
VOICE = os.environ.get("VOICE", "en-US-JennyNeural")

# Slightly slower speech is easier for little kids to follow.
VOICE_RATE = os.environ.get("VOICE_RATE", "-8%")

# ----- Video look -----
WIDTH = 1280
HEIGHT = 720
FPS = 25
CROSSFADE = 0.6          # seconds of crossfade between scenes
SCENE_COUNT = 16         # how many scenes (images) per video (~5-6 min total)
SECONDS_PER_SCENE = 20   # rough target narration length per scene

# ----- Background music -----
MUSIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "music")
MUSIC_VOLUME = 0.23      # how loud the music is under the voice (0.0 - 1.0)

# ----- Publishing -----
# Your local timezone, used to schedule the 8am publish time.
# Examples: "America/New_York", "America/Los_Angeles",
#           "Europe/London", "Asia/Seoul", "Asia/Kolkata"
TIMEZONE = os.environ.get("TIMEZONE") or "America/Los_Angeles"
PUBLISH_HOUR = int(os.environ.get("PUBLISH_HOUR") or "8")   # 8 = 8am

# Where temporary files are written
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
