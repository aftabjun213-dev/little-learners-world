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

# ---------------------------------------------------------------------------
# STORY STRUCTURE LIBRARY - the engine rotates these so no two consecutive
# episodes feel the same. Each entry is (name, instructions for the writer).
# ---------------------------------------------------------------------------
STRUCTURES = [
    ("Mystery Hunt",
     "Open on a strange sound, footprint, or clue. The characters (and the child!) "
     "become detectives. Keep asking 'what could it be?' and eliminate fun wrong "
     "guesses scene by scene. Reveal the answer only near the end, then celebrate."),
    ("Big Journey",
     "A character must travel somewhere exciting to reach a goal. Pass through 3 "
     "distinct fun locations; each location teaches one piece of the lesson. Build "
     "anticipation before each new place: 'What's OVER that hill?'"),
    ("Uh-Oh, Fix It!",
     "Something small and funny goes wrong early on. The characters try 2-3 silly "
     "ideas that comically fail, then the day's lesson is exactly what fixes it. "
     "Kids love shouting the right answer before the characters get it."),
    ("Follow-Along Day",
     "We shadow the character through their day. Every scene invites the child to "
     "COPY an action: stomp, clap, count, roar, stretch. Highest participation "
     "structure - the child should be moving the whole time."),
    ("Silly Backwards Day",
     "Everything happens the WRONG way (a fish in a tree! socks on ears!). The "
     "child gets to be the expert who shouts the correction. End with everything "
     "put right and the lesson locked in."),
    ("Treasure Countdown",
     "There are N hidden things to find (colors, numbers, shapes, animals). Find "
     "them one by one with a count-along and a mini-celebration for each. Finish "
     "with a big final tally and a happy dance."),
]


def _build_prompt(topic_title, concept, scene_count, structure):
    struct_name, struct_rules = structure
    return f"""You are the beloved host and storyteller of a hit children's cartoon channel,
writing one episode for kids ages 3 to 7.

Episode title idea: "{topic_title}"
Teaching goal: {concept}

TODAY'S STORY STRUCTURE (follow it - this is what keeps episodes feeling fresh):
"{struct_name}": {struct_rules}

RETENTION RULES - little kids stop watching in seconds if you lose them. Non-negotiable:
1. THE HOOK (scene 1): Start MID-ACTION at the most exciting moment - a sound, a surprise,
   a question - within the FIRST TWO SENTENCES. Never start with "Hello" or introductions.
   First brainstorm 3 candidate opening lines in the "hook_options" field, then use the
   strongest one as the actual opening of scene 1.
2. RE-HOOKS: EVERY scene (except the last) must END on a mini-cliffhanger or direct
   question that makes the child need the next scene: "But wait... what's that behind
   the tree?!" / "Uh oh... do YOU know what happens next?"
3. PARTICIPATION: at least half the scenes ask the child to DO something out loud or
   with their body: shout the answer, count along, roar, clap, point, stomp.
4. REPETITION WITH RHYTHM: give the episode one short, catchy repeated phrase (like a
   mini-chant the child can join) tied to the lesson, used 3-4 times.

VOICE & TONE: Write exactly the way a warm, playful human storyteller SPEAKS:
- Talk directly to the child ("Can you see it? Point to it! Yesss!")
- Contractions, natural rhythm, short punchy sentences mixed with longer ones.
- Real feeling: gentle surprise ("Oh my!"), joy ("Hooray!"), wonder ("Woooow!").
- Sound words everywhere: "splish-splash!", "boing!", "wheee!"
- Characters get personality and little bits of dialogue.
- Ellipses (...) for suspense pauses, "!" for excitement.
- Warm, encouraging. No scary content. No violence. Nothing sad for long.

Return ONLY valid JSON (no markdown, no extra text) in exactly this shape:

{{
  "hook_options": ["3 candidate opening lines - most exciting first"],
  "title_options": ["3 to 5 YouTube title options, BEST FIRST, each max 75 chars with one emoji. Formula: fun hook + clear learning outcome parents search for (e.g. 'What Sound Does a Cow Make? \\ud83d\\udc04 Farm Animals for Kids'). Vary the formulas across options."],
  "description": "A warm 2-3 sentence YouTube description for parents mentioning the learning outcome and age range 3-7, ending with a gentle call to subscribe to {CHANNEL_NAME}.",
  "tags": ["10 to 15 short lowercase keyword tags relevant to kids learning and this topic"],
  "thumbnail_prompt": "A prompt for ONE eye-catching thumbnail image: extreme close-up of the episode's main character with a big expressive emotion (surprise/joy), ONE bright high-contrast background color, very simple composition. Include: 'soft cute 2D cartoon illustration for toddlers, bright cheerful colors, simple rounded shapes, storybook style, no text'.",
  "thumbnail_text": "2 to 4 punchy words for the thumbnail (e.g. 'MOO?!' or 'FIND THE RED!')",
  "scenes": [
    {{
      "chapter_title": "2-4 word fun chapter name for this scene",
      "mood": "one of: excited, curious, gentle, silly, calm",
      "narration": "The exact spoken words for this scene (about {SECONDS_PER_SCENE} seconds read aloud). Follow ALL retention rules.",
      "image_prompt": "A detailed description of a single bright, cute cartoon illustration for this scene. Keep the SAME characters looking consistent across scenes. Always include the style words: 'soft cute 2D cartoon illustration for toddlers, bright cheerful colors, simple rounded shapes, storybook style, no text'."
    }}
  ]
}}

Make exactly {scene_count} scenes that flow as ONE continuous story following the
"{struct_name}" structure, with a happy, satisfying ending that repeats the catchy
lesson phrase one last time. Each narration is about {SECONDS_PER_SCENE} seconds
read aloud. Vary the mood across scenes - excitement peaks, curious build-ups,
one gentle beat, and a calm proud ending.
"""


def _build_short_prompt(topic_title, concept, scene_count, seconds_per_scene):
    return f"""You are the host of a children's cartoon channel writing a super fun,
punchy YOUTUBE SHORT (vertical, about 40-50 seconds total) for kids ages 3 to 7.

Topic: "{topic_title}"
Teaching goal: {concept}

Rules for Shorts:
- HOOK them in the first 3 seconds with excitement ("Wanna learn a secret? Let's go!").
- Super energetic, warm, and playful — like a real host talking straight to the child.
- Natural spoken English with contractions, questions, and fun sound words.
- Teach just ONE tiny idea, repeated in a catchy way kids remember.
- End with a cheerful line inviting them to follow for more.

Return ONLY valid JSON (no markdown) in exactly this shape:

{{
  "video_title": "A punchy Shorts title (max 70 chars) with an emoji and the word Shorts vibe",
  "description": "1-2 fun sentences for the description.",
  "tags": ["10-15 short lowercase tags for kids learning shorts"],
  "scenes": [
    {{
      "narration": "The exact excited spoken words for this scene (about {seconds_per_scene} seconds).",
      "image_prompt": "One bright vertical cartoon illustration for this scene. Keep characters consistent. Always include: 'soft cute 2D cartoon illustration for toddlers, bright cheerful colors, simple rounded shapes, storybook style, vertical composition, no text'."
    }}
  ]
}}

Make exactly {scene_count} fast, punchy scenes that flow together.
"""


def generate_short_script(topic_title, concept, scene_count, seconds_per_scene):
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"].strip())
    prompt = _build_short_prompt(topic_title, concept, scene_count, seconds_per_scene)
    resp = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    data = _extract_json(resp.content[0].text)
    data.setdefault("tags", [])
    data["tags"] = list(data["tags"]) + [
        "shorts", "kids shorts", "learning for kids", "toddler", CHANNEL_NAME.lower(),
    ]
    return data


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


def generate_script(topic_title, concept, scene_count=SCENE_COUNT, structure=None):
    """structure: an entry from STRUCTURES; if None, one is chosen at random."""
    import random as _random
    if structure is None:
        structure = _random.choice(STRUCTURES)

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"].strip())
    prompt = _build_prompt(topic_title, concept, scene_count, structure)

    resp = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = resp.content[0].text
    data = _extract_json(raw)

    # Basic safety defaults so one missing field never crashes the nightly run
    data.setdefault("tags", [])
    data["tags"] = list(data["tags"]) + [
        "kids learning", "educational cartoon for kids", "toddler videos",
        "preschool", "learning for kids", CHANNEL_NAME.lower(),
    ]
    titles = data.get("title_options") or [data.get("video_title") or topic_title]
    data["video_title"] = titles[0]
    data["title_options"] = titles
    data["structure_used"] = structure[0]
    for scene in data.get("scenes", []):
        scene.setdefault("mood", "curious")
        scene.setdefault("chapter_title", "")
    return data


if __name__ == "__main__":
    # Quick manual test
    out = generate_script("The Rainbow That Lost Its Colors",
                          "Learning the colors of the rainbow")
    print(json.dumps(out, indent=2))
