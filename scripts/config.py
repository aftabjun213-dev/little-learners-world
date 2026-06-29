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
# Warm, friendly voices good for kids. Change if you like:
#   en-US-AnaNeural      -> cheerful child voice
#   en-US-JennyNeural    -> warm, friendly woman
#   en-GB-SoniaNeural    -> calm British woman
VOICE = os.environ.get("VOICE", "en-US-JennyNeural")

# Slightly slower speech is easier for little kids to follow.
VOICE_RATE = os.environ.get("VOICE_RATE", "-8%")

# ----- Video look -----
WIDTH = 1280
HEIGHT = 720
FPS = 25
CROSSFADE = 0.6          # seconds of crossfade between scenes
SCENE_COUNT = 6          # how many scenes (images) per video

# ----- Publishing -----
# Your local timezone, used to schedule the 8am publish time.
# Examples: "America/New_York", "America/Los_Angeles",
#           "Europe/London", "Asia/Seoul", "Asia/Kolkata"
TIMEZONE = os.environ.get("TIMEZONE") or "America/Los_Angeles"
PUBLISH_HOUR = int(os.environ.get("PUBLISH_HOUR") or "8")   # 8 = 8am

# Where temporary files are written
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
