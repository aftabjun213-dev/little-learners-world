"""
The daily robot. Runs once per day:
  1. Pick the next topic from topics.json
  2. Write the story with Claude Haiku
  3. Make voiceover (edge-tts) + images (Pollinations) for each scene
  4. Build the video with Ken Burns + crossfades (FFmpeg)
  5. Upload to YouTube, Made for Kids, scheduled to publish at 8am
  6. Save progress so tomorrow uses the next topic
"""
import datetime as dt
import json
import os
import random
import sys
from zoneinfo import ZoneInfo

# Allow "python scripts/main.py" to find sibling modules
sys.path.insert(0, os.path.dirname(__file__))

from config import OUTPUT_DIR, TIMEZONE, PUBLISH_HOUR, CHANNEL_NAME, VOICES, VOICE
from generate_script import generate_script
from generate_audio import generate_audio
from generate_images import generate_image
from make_video import build_video
from music_picker import pick_music
from effects import make_sparkle_overlay
from upload_youtube import upload_video
from config import WIDTH, HEIGHT

ROOT = os.path.dirname(os.path.dirname(__file__))
TOPICS_FILE = os.path.join(ROOT, "topics.json")
STATE_FILE = os.path.join(ROOT, "state.json")


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def next_publish_time():
    """Return today's (or tomorrow's) PUBLISH_HOUR in the user's timezone, as UTC ISO."""
    tz = ZoneInfo(TIMEZONE)
    now = dt.datetime.now(tz)
    target = now.replace(hour=PUBLISH_HOUR, minute=0, second=0, microsecond=0)
    if target <= now + dt.timedelta(minutes=10):
        target += dt.timedelta(days=1)
    return target.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    topics = load_json(TOPICS_FILE, [])
    state = load_json(STATE_FILE, {"index": 0})
    idx = state.get("index", 0) % len(topics)
    topic = topics[idx]

    print(f"=== {CHANNEL_NAME} ===")
    print(f"Episode #{idx + 1}: {topic['title']}")

    # 1. Story + SEO from Claude
    print("Writing the story with Claude Haiku...")
    script = generate_script(topic["title"], topic["concept"])
    scenes = script["scenes"]

    # Pick one narrator voice for this whole episode (varies each episode).
    voice = random.choice(VOICES) if VOICES else VOICE
    print(f"Narrator voice: {voice}")

    # 2/3. Per-scene audio + image
    media = []
    base_seed = random.randint(1, 1_000_000)
    for i, scene in enumerate(scenes):
        print(f"Scene {i + 1}/{len(scenes)}: voice + image...")
        audio_path = os.path.join(OUTPUT_DIR, f"scene_{i}.mp3")
        image_path = os.path.join(OUTPUT_DIR, f"scene_{i}.png")
        generate_audio(scene["narration"], audio_path, voice=voice)
        generate_image(scene["image_prompt"], image_path, seed=base_seed + i)
        media.append({"image": image_path, "audio": audio_path})

    # 4. Build the video (with soft music + floating sparkles)
    print("Building the video with FFmpeg (this takes a few minutes)...")
    music_path, music_credit = pick_music()
    if music_path:
        print(f"Background music: {os.path.basename(music_path)}")
    sparkle_path = os.path.join(OUTPUT_DIR, "sparkles.png")
    make_sparkle_overlay(WIDTH, HEIGHT, sparkle_path)
    video_path = os.path.join(OUTPUT_DIR, "final.mp4")
    build_video(media, video_path, music_path=music_path,
                sparkle_path=sparkle_path)

    # 5. Upload to YouTube
    publish_at = next_publish_time()
    print(f"Uploading to YouTube (will publish at {publish_at})...")
    title = script["video_title"]
    description = (
        f"{script['description']}\n\n"
        f"Welcome to {CHANNEL_NAME} - fun, gentle learning for little kids!\n"
        f"#kids #learning #cartoon #preschool"
    )
    if music_credit:
        description += f"\n\n---\n{music_credit}"
    thumbnail = media[0]["image"]  # use the first scene image as thumbnail
    upload_video(
        video_path, title, description, script["tags"], publish_at,
        thumbnail_path=thumbnail,
    )

    # 6. Save progress
    state["index"] = (idx + 1) % len(topics)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    print("Done! Tomorrow will use the next topic.")


if __name__ == "__main__":
    main()
