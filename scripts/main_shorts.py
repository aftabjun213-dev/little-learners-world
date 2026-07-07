"""
Makes and uploads TWO YouTube Shorts per run, scheduled to publish at two
different times of day. Vertical (9:16), ~45 seconds, Made for Kids.

Reuses the same building blocks as the long video (Claude story, edge-tts voice,
Flux images, FFmpeg motion+music+sparkles+subtitles) but in a short vertical form.
"""
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))

from config import (OUTPUT_DIR, TIMEZONE, CHANNEL_NAME, VOICES, VOICE,
                    SHORT_WIDTH, SHORT_HEIGHT, SHORT_SCENE_COUNT,
                    SHORT_SECONDS_PER_SCENE, SHORT_PUBLISH_HOURS)
from generate_script import generate_short_script
from generate_audio import generate_audio
from generate_images import generate_image
from make_video import build_video
from music_picker import pick_music
from effects import make_sparkle_overlay
from schedule_util import next_publish_iso
from upload_youtube import upload_video

ROOT = os.path.dirname(os.path.dirname(__file__))
TOPICS_FILE = os.path.join(ROOT, "shorts_topics.json")
STATE_FILE = os.path.join(ROOT, "shorts_state.json")


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def make_one_short(topic, slot, publish_hour):
    """Build and upload a single short. `slot` keeps filenames unique."""
    print(f"\n--- Short: {topic['title']} (publishes ~{publish_hour}:00) ---")
    script = generate_short_script(
        topic["title"], topic["concept"],
        SHORT_SCENE_COUNT, SHORT_SECONDS_PER_SCENE,
    )
    scenes = script["scenes"]

    voice = random.choice(VOICES) if VOICES else VOICE
    print(f"Voice: {voice}")

    media = []
    base_seed = random.randint(1, 1_000_000)
    for i, scene in enumerate(scenes):
        audio_path = os.path.join(OUTPUT_DIR, f"s{slot}_scene_{i}.mp3")
        image_path = os.path.join(OUTPUT_DIR, f"s{slot}_scene_{i}.png")
        generate_audio(scene["narration"], audio_path, voice=voice)
        generate_image(scene["image_prompt"], image_path, seed=base_seed + i,
                       width=SHORT_WIDTH, height=SHORT_HEIGHT, aspect_ratio="9:16")
        media.append({"image": image_path, "audio": audio_path,
                      "narration": scene["narration"]})

    music_path, music_credit = pick_music()
    sparkle_path = os.path.join(OUTPUT_DIR, f"s{slot}_sparkles.png")
    make_sparkle_overlay(SHORT_WIDTH, SHORT_HEIGHT, sparkle_path)

    video_path = os.path.join(OUTPUT_DIR, f"short_{slot}.mp4")
    build_video(media, video_path, music_path=music_path,
                sparkle_path=sparkle_path, width=SHORT_WIDTH, height=SHORT_HEIGHT)

    publish_at = next_publish_iso(publish_hour, TIMEZONE)
    title = f"{script['video_title']} #Shorts"
    description = (
        f"{script['description']}\n\n"
        f"{CHANNEL_NAME} - fun, quick learning for little kids!\n"
        f"#Shorts #shorts #kids #learning #preschool #toddler"
    )
    if music_credit:
        description += f"\n\n---\n{music_credit}"

    upload_video(video_path, title, description, script["tags"], publish_at,
                 thumbnail_path=None)
    print(f"Uploaded short, will publish at {publish_at}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    topics = load_json(TOPICS_FILE, [])
    state = load_json(STATE_FILE, {"index": 0})
    idx = state.get("index", 0)

    num_shorts = len(SHORT_PUBLISH_HOURS)  # one short per publish time
    print(f"=== {CHANNEL_NAME} Shorts ({num_shorts} today) ===")
    for slot in range(num_shorts):
        topic = topics[(idx + slot) % len(topics)]
        hour = SHORT_PUBLISH_HOURS[slot]
        make_one_short(topic, slot, hour)

    state["index"] = (idx + num_shorts) % len(topics)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    print(f"\nDone! {num_shorts} shorts uploaded.")


if __name__ == "__main__":
    main()
