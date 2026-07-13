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
import math
import os
import random
import sys
from zoneinfo import ZoneInfo

# Allow "python scripts/main.py" to find sibling modules
sys.path.insert(0, os.path.dirname(__file__))

from config import (OUTPUT_DIR, TIMEZONE, PUBLISH_HOUR, CHANNEL_NAME,
                    VOICES, VOICE, WIDTH, HEIGHT, CROSSFADE, IMAGE_SECONDS,
                    IMAGES_PER_SCENE_MIN, IMAGES_PER_SCENE_MAX)
from generate_script import generate_script, STRUCTURES
from generate_audio import generate_audio, eleven_available
from generate_images import generate_image
from make_video import build_video, get_duration
from make_thumbnail import make_thumbnail
from music_picker import pick_music
from effects import make_sparkle_overlay
from upload_youtube import upload_video

ROOT = os.path.dirname(os.path.dirname(__file__))
TOPICS_FILE = os.path.join(ROOT, "topics.json")
STATE_FILE = os.path.join(ROOT, "state.json")
CHARACTERS_FILE = os.path.join(ROOT, "characters.json")


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
    characters = load_json(CHARACTERS_FILE, [])
    state = load_json(STATE_FILE, {"index": 0})
    idx = state.get("index", 0) % len(topics)
    topic = topics[idx]

    print(f"=== {CHANNEL_NAME} ===")
    print(f"Episode #{idx + 1}: {topic['title']}")

    # HERO ROTATION: one recurring hero stars for several days, then the next
    # rotates in. Each hero has their OWN consistent voice so kids recognise them.
    hero_index = state.get("hero_index", 0)
    hero_days_used = state.get("hero_days_used", 0)
    if characters:
        hero = characters[hero_index % len(characters)]
        # Premium ElevenLabs voice when the key is set, free edge-tts otherwise
        voice = (hero.get("eleven_voice") if eleven_available()
                 else hero["voice"])
        engine = "ElevenLabs" if eleven_available() else "edge-tts (free)"
        print(f"Hero: {hero['name']} (day {hero_days_used + 1} of "
              f"{hero['days']})  |  Voice: {voice} [{engine}]")
    else:  # no cast defined -> fall back to random narrator (old behaviour)
        hero = None
        voice = random.choice(VOICES) if VOICES else VOICE

    # STRUCTURE VARIETY: never repeat yesterday's structure.
    last_structure = state.get("last_structure")
    structure = random.choice(
        [s for s in STRUCTURES if s[0] != last_structure] or STRUCTURES)
    print(f"Story structure: {structure[0]}")

    # 1. Story + SEO from Claude (starring today's hero)
    print("Writing the story with Claude Haiku...")
    script = generate_script(topic["title"], topic["concept"],
                             structure=structure, hero=hero)
    scenes = script["scenes"]
    print(f"Title chosen: {script['video_title']}")

    # 2/3. Per-scene audio (mood-paced) + several quick-cut pictures
    media = []
    base_seed = random.randint(1, 1_000_000)
    for i, scene in enumerate(scenes):
        audio_path = os.path.join(OUTPUT_DIR, f"scene_{i}.mp3")
        generate_audio(scene["narration"], audio_path, voice=voice,
                       mood=scene.get("mood"))
        dur = get_duration(audio_path)
        # A new picture roughly every IMAGE_SECONDS so nothing feels static
        k = max(IMAGES_PER_SCENE_MIN,
                min(IMAGES_PER_SCENE_MAX, math.ceil(dur / IMAGE_SECONDS)))
        prompts = scene.get("image_prompts") or ["a bright cheerful cartoon"]
        print(f"Scene {i + 1}/{len(scenes)} [{scene.get('mood', 'curious')}]: "
              f"{dur:.0f}s narration, {k} pictures...")
        images = []
        for j in range(k):
            img_path = os.path.join(OUTPUT_DIR, f"scene_{i}_{j}.png")
            generate_image(prompts[j % len(prompts)], img_path,
                           seed=base_seed + i * 10 + j)
            images.append(img_path)
        media.append({
            "images": images,
            "audio": audio_path,
            "narration": scene["narration"],
        })

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

    # 4b. Dedicated thumbnail (falls back to scene 1 if anything goes wrong)
    thumbnail = media[0]["images"][0]
    try:
        if script.get("thumbnail_prompt"):
            print("Making the thumbnail...")
            thumbnail = make_thumbnail(
                generate_image, script["thumbnail_prompt"],
                script.get("thumbnail_text", ""), OUTPUT_DIR,
                seed=base_seed + 999, episode_index=idx,
            )
    except Exception as e:  # noqa: BLE001
        print(f"  (Thumbnail generation failed, using scene 1: {e})")

    # 5. Upload to YouTube (with chapters for discoverability)
    publish_at = next_publish_time()
    print(f"Uploading to YouTube (will publish at {publish_at})...")
    title = script["video_title"]

    # Chapter timestamps from real scene durations (YouTube needs 0:00 first)
    chapters = []
    t = 0.0
    for i, (m, scene) in enumerate(zip(media, scenes)):
        label = (scene.get("chapter_title") or f"Part {i + 1}").strip()
        chapters.append(f"{int(t // 60)}:{int(t % 60):02d} {label}")
        t += get_duration(m["audio"]) - CROSSFADE

    description = (
        f"{script['description']}\n\n"
        + "\n".join(chapters) + "\n\n"
        f"Welcome to {CHANNEL_NAME} - fun, gentle learning for kids ages 3-7!\n"
        f"New episodes every day. Perfect for preschool, toddlers and "
        f"kindergarten: colors, counting, shapes, animals, feelings and more.\n"
        f"#kids #learning #cartoon #preschool #toddler"
    )
    if music_credit:
        description += f"\n\n---\n{music_credit}"
    upload_video(
        video_path, title, description, script["tags"], publish_at,
        thumbnail_path=thumbnail,
    )

    # 6. Save progress + advance hero rotation
    if characters:
        hero_days_used += 1
        if hero_days_used >= hero["days"]:   # hero's run is over -> next hero
            hero_index = (hero_index + 1) % len(characters)
            hero_days_used = 0
        state["hero_index"] = hero_index
        state["hero_days_used"] = hero_days_used
    state["index"] = (idx + 1) % len(topics)
    state["last_structure"] = script.get("structure_used", structure[0])
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    nxt = "same hero" if characters and hero_days_used != 0 else "a new hero"
    print(f"Done! Tomorrow: next topic with {nxt}.")


if __name__ == "__main__":
    main()
