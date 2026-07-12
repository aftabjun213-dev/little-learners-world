"""
Turns narration text into warm voiceover audio using edge-tts (free, no API key).
Supports per-scene "mood" so delivery varies within one episode:
excited scenes are a touch faster/brighter, calm scenes slower/softer.
"""
import asyncio

import edge_tts

from config import VOICE, VOICE_RATE, MOOD_STYLES


async def _synth(text, out_path, voice, rate, pitch):
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate, pitch=pitch)
    await communicate.save(out_path)


def generate_audio(text, out_path, voice=VOICE, rate=None, mood=None):
    """Create an mp3 voiceover file at out_path.

    mood: optional key of MOOD_STYLES ("excited", "curious", "gentle",
    "silly", "calm") - sets rate+pitch for that scene. An explicit `rate`
    argument overrides the mood's rate.
    """
    mood_rate, pitch = MOOD_STYLES.get(mood, (VOICE_RATE, "+0Hz"))
    final_rate = rate if rate is not None else mood_rate
    asyncio.run(_synth(text, out_path, voice, final_rate, pitch))
    return out_path


if __name__ == "__main__":
    generate_audio("Wait... do you hear that? Something is coming!",
                   "test.mp3", mood="curious")
    print("Wrote test.mp3")
