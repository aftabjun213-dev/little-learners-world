"""
Uses Claude Haiku to write a fun, gentle educational story for kids 3-7.
Returns everything we need in ONE API call (keeps cost minimal):
  - video_title  (SEO friendly)
  - description  (SEO friendly)
  - tags         (list of keywords)
  - scenes       (list of {narration, image_prompt})
"""
import json
import os
import re

from anthropic import Anthropic

from config import CLAUDE_MODEL, SCENE_COUNT, SECONDS_PER_SCENE, CHANNEL_NAME


def _build_prompt(topic_title, concept, scene_count):
    return f"""You are writing an animated educational cartoon episode for children ages 3 to 7.
The finished video should be about 5 to 6 minutes long.

Episode title idea: "{topic_title}"
Teaching goal: {concept}

Write a warm, gentle, joyful story that teaches this concept. Use simple words,
short sentences, friendly repetition, fun sound words (like "splash!" and "wheee!"),
and a cozy storybook tone. Introduce one or two cute characters and give the story a
clear beginning, middle, and happy ending. Gently repeat the key lesson so little kids
remember it. No scary content. No violence.

Return ONLY valid JSON (no markdown, no extra text) in exactly this shape:

{{
  "video_title": "A catchy, friendly YouTube title (max 80 chars) including a relevant emoji",
  "description": "A warm 2-3 sentence YouTube description for parents, ending with a gentle call to subscribe to {CHANNEL_NAME}.",
  "tags": ["10 to 15 short lowercase keyword tags relevant to kids learning and this topic"],
  "scenes": [
    {{
      "narration": "4 to 6 simple sentences a narrator reads for this scene (about {SECONDS_PER_SCENE} seconds when read aloud).",
      "image_prompt": "A detailed description of a single bright, cute cartoon illustration for this scene. Keep the SAME characters looking consistent across scenes. Always include the style words: 'soft cute 2D cartoon illustration for toddlers, bright cheerful colors, simple rounded shapes, storybook style, no text'."
    }}
  ]
}}

Make exactly {scene_count} scenes that flow as one continuous story.
Each narration should take about {SECONDS_PER_SCENE} seconds to read aloud, so the whole
episode reaches roughly 5 to 6 minutes total.
"""


def _extract_json(text):
    """Claude usually returns clean JSON, but strip code fences just in case."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    # Grab the outermost {...}
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start:end + 1]
    return json.loads(text)


def generate_script(topic_title, concept, scene_count=SCENE_COUNT):
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"].strip())
    prompt = _build_prompt(topic_title, concept, scene_count)

    resp = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = resp.content[0].text
    data = _extract_json(raw)

    # Basic safety defaults
    data.setdefault("tags", [])
    data["tags"] = list(data["tags"]) + [
        "kids learning", "educational cartoon for kids", "toddler videos",
        "preschool", "learning for kids", CHANNEL_NAME.lower(),
    ]
    return data


if __name__ == "__main__":
    # Quick manual test
    out = generate_script("The Rainbow That Lost Its Colors",
                          "Learning the colors of the rainbow")
    print(json.dumps(out, indent=2))
