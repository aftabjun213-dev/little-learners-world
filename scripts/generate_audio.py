"""
Turns narration text into warm voiceover audio using edge-tts (free, no API key).
"""
import asyncio

import edge_tts

from config import VOICE, VOICE_RATE


async def _synth(text, out_path, voice, rate):
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate)
    await communicate.save(out_path)


def generate_audio(text, out_path, voice=VOICE, rate=VOICE_RATE):
    """Create an mp3 voiceover file at out_path."""
    asyncio.run(_synth(text, out_path, voice, rate))
    return out_path


if __name__ == "__main__":
    generate_audio("Hello little learners! Today we are going on an adventure.",
                   "test.mp3")
    print("Wrote test.mp3")
