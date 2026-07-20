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

# Per-scene delivery: the script engine tags each scene with a mood and the
# voice speeds up / slows down + shifts pitch to match. (rate, pitch)
MOOD_STYLES = {
    "excited": ("+6%", "+15Hz"),
    "curious": ("-2%", "+6Hz"),
    "gentle":  ("-8%", "-4Hz"),
    "silly":   ("+5%", "+18Hz"),
    "calm":    ("-12%", "-8Hz"),
}

# ----- ElevenLabs (premium voice - optional) -----
# Activates automatically when the ELEVENLABS_API_KEY secret is set.
# "eleven_flash_v2_5" = excellent quality at HALF the credit cost (0.5 credit/
# char) so your monthly credits cover roughly 2x more videos. For maximum
# richness on a bigger plan, set ELEVEN_MODEL to "eleven_multilingual_v2".
ELEVEN_MODEL = os.environ.get("ELEVEN_MODEL") or "eleven_flash_v2_5"
# Per-scene mood -> (stability, style, speed). Lower stability + higher style
# = more emotion/energy. Speed < 1.0 slows delivery - little kids need a
# gentler pace to follow along (1.0 was too fast).
ELEVEN_MOODS = {
    "excited": (0.30, 0.65, 0.93),
    "curious": (0.40, 0.45, 0.90),
    "gentle":  (0.55, 0.30, 0.86),
    "silly":   (0.28, 0.75, 0.93),
    "calm":    (0.62, 0.20, 0.84),
}
ELEVEN_DEFAULT_MOOD = (0.45, 0.40, 0.90)

# ----- Video look -----
WIDTH = 1920           # Full HD width (1080p)
HEIGHT = 1080          # Full HD height
FPS = 25
CROSSFADE = 0.6          # seconds of crossfade between scenes
# Retention data (Jul 2026) showed kids watched only 24-48s of 5-min videos.
# Target length: 3-6 minutes (ElevenLabs reads a touch slower than the target,
# so 12 scenes x ~18s lands around 4-5 minutes).
SCENE_COUNT = 12         # how many story scenes per video
SECONDS_PER_SCENE = 18   # rough target narration length per scene

# Rapid picture changes: each scene shows several pictures with quick cuts
# instead of one still frame. ~every 6 seconds a new picture appears.
IMAGE_SECONDS = 6        # target seconds each picture stays on screen
IMAGES_PER_SCENE_MIN = 2
# Max 3 pictures/scene keeps image cost ~$4/month (raising to 4 adds ~$1/mo)
IMAGES_PER_SCENE_MAX = 3

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
# Timezone the publish time is anchored to. We anchor to US EASTERN because the
# audience is US English-speaking kids and Eastern has the biggest population.
# Examples: "America/New_York", "America/Los_Angeles", "Europe/London", "Asia/Kolkata"
TIMEZONE = os.environ.get("TIMEZONE") or "America/New_York"
# 15 = 3 PM. Research shows 2-4 PM (after school) is the best window for young
# kids on weekdays, and a good midday slot on weekends.
PUBLISH_HOUR = int(os.environ.get("PUBLISH_HOUR") or "15")

# Where temporary files are written
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
