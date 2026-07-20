"""
Turns narration text into warm voiceover audio.

Two engines:
  - ElevenLabs (premium, most human) - used automatically when the
    ELEVENLABS_API_KEY environment variable is set AND the requested voice is
    an ElevenLabs voice name (heroes carry an "eleven_voice" for this).
  - edge-tts (free) - the default, and the automatic fallback if an ElevenLabs
    call ever fails (credits out, network, etc.) so the channel never breaks.

Per-scene "mood" varies the delivery in both engines.
"""
import asyncio
import os

import edge_tts
import requests

from config import (VOICE, VOICE_RATE, MOOD_STYLES,
                    ELEVEN_MODEL, ELEVEN_MOODS, ELEVEN_DEFAULT_MOOD)

_voice_id_cache = None


# ---------------- ElevenLabs (premium) ----------------
def _eleven_key():
    return os.environ.get("ELEVENLABS_API_KEY", "").strip()


def eleven_available():
    """True when an ElevenLabs API key is configured."""
    return bool(_eleven_key())


def _is_edge_voice(name):
    # All edge-tts voice ids end in "Neural"; ElevenLabs voices don't.
    return name.endswith("Neural")


def _eleven_voice_id(name):
    """Resolve an ElevenLabs voice NAME to its id (cached). Deterministic
    fallback keeps a hero on a stable voice even if the name isn't found."""
    global _voice_id_cache
    if _voice_id_cache is None:
        r = requests.get("https://api.elevenlabs.io/v1/voices",
                         headers={"xi-api-key": _eleven_key()}, timeout=30)
        r.raise_for_status()
        _voice_id_cache = {v["name"]: v["voice_id"]
                           for v in r.json().get("voices", [])}
    ids = _voice_id_cache
    if name in ids:
        return ids[name]
    if not ids:
        raise RuntimeError("No ElevenLabs voices on this account")
    keys = sorted(ids)                      # stable order
    pick = sum(map(ord, name)) % len(keys)  # deterministic per hero name
    return ids[keys[pick]]


def _eleven_synth(text, out_path, voice_name, mood):
    stability, style, speed = ELEVEN_MOODS.get(mood, ELEVEN_DEFAULT_MOOD)
    voice_id = _eleven_voice_id(voice_name)
    r = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        params={"output_format": "mp3_44100_128"},
        headers={"xi-api-key": _eleven_key()},
        json={
            "text": text,
            "model_id": ELEVEN_MODEL,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": 0.75,
                "style": style,
                "speed": speed,
                "use_speaker_boost": True,
            },
        },
        timeout=180,
    )
    r.raise_for_status()
    with open(out_path, "wb") as f:
        f.write(r.content)
    return out_path


# ---------------- edge-tts (free) ----------------
async def _edge_synth(text, out_path, voice, rate, pitch):
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate, pitch=pitch)
    await communicate.save(out_path)


def generate_audio(text, out_path, voice=VOICE, rate=None, mood=None):
    """Create an mp3 voiceover at out_path. Picks ElevenLabs or edge-tts based
    on whether a key is set and what kind of voice name was passed."""
    if eleven_available() and not _is_edge_voice(voice):
        try:
            return _eleven_synth(text, out_path, voice, mood)
        except Exception as e:  # noqa: BLE001
            print(f"  ElevenLabs failed ({e}); using free voice instead...")
            voice = VOICE  # fall back to a valid edge-tts voice

    mood_rate, pitch = MOOD_STYLES.get(mood, (VOICE_RATE, "+0Hz"))
    final_rate = rate if rate is not None else mood_rate
    asyncio.run(_edge_synth(text, out_path, voice, final_rate, pitch))
    return out_path


if __name__ == "__main__":
    generate_audio("Wait... do you hear that? Something is coming!",
                   "test.mp3", mood="curious")
    print("Wrote test.mp3")
