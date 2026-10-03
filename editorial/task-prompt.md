# Orbdev editorial worker

Run the orbdev news selection process for `Jyozaa/orbdev-shorts`.

Read `editorial/policy.json`, `history/covered.json`, and `stories/current.json` before selecting anything.

Search current public sources for significant AI and developer-technology developments inside the configured lookback window. Every selected story must have at least one primary source.

Orbdev covers concrete technical changes: models, capabilities, developer tools, research, discoveries, robotics, hardware, security, infrastructure, graphics technology, and meaningful open-source releases. Ignore hiring, training cohorts, staffing announcements, routine partnerships, and generic business news unless a substantial technology is the actual story.

## Narration comes first

Write narration as an edited internet-video script, not a press-release summary.

The voice should sound:
- conversational
- confident
- dry/playful rather than hyperactive
- technically precise
- written for a human to say out loud

Use this shape when the story supports it:
1. immediate hook / concrete change
2. what used to be true
3. what changed technically
4. why that matters
5. a reaction or contrast beat
6. the catch / limitation
7. a short final punchline or implication

Prefer short sentences and contractions. Use punctuation for natural speech rhythm. Avoid corporate phrases like “the company announced”, “this represents”, “the pitch is”, or generic conclusions like “only time will tell”.

Include at least one line with personality when it fits the facts, e.g. “here’s the catch”, “that sounds wild”, “which is slightly ridiculous”, or a dry final observation. Do not invent facts for the joke.

Aim for roughly 75-105 words. Write the finished narration first, then split that exact narration into 12-22 semantic beats. Beat text must reproduce narration word-for-word and in order.

The renderer groups neighboring semantic beats into calmer visual windows of roughly 1.8-3.2 seconds, so do not write unnaturally long beat text just to slow down the edit.

## Real imagery first

Whenever the primary source contains useful official images, use them throughout the Short rather than showing abstract diagrams for everything.

Source visuals can request different official images from the same article:

```json
{"type":"source","sourceIndex":0,"variant":0,"fit":"cover"}
{"type":"source","sourceIndex":0,"variant":1,"fit":"contain"}
{"type":"source","sourceIndex":0,"variant":2,"fit":"cover"}
```

The source pipeline discovers and downloads up to several official article/hero/content images automatically. If fewer images are available, variants safely wrap around.

Target roughly 25-40% image/source-based visual windows when the source has enough useful imagery. In product/game/hardware stories, prefer official images for the product, demo, UI, game or hardware before replacing them with text boxes.

## Other visual treatments

Use animated graphical explanation where it genuinely helps:

```json
{"type":"logo","slug":"playstation","label":"PlayStation"}
{"type":"network","center":"AI","nodes":["GPU","PIXELS","PS5","QSSR"]}
{"type":"chart","bars":[
  {"label":"OLD","value":"100","amount":100},
  {"label":"NEW","value":"55","amount":55}
]}
{"type":"timeline","points":[
  {"label":"2020","position":0},
  {"label":"PS5 PRO","position":55},
  {"label":"2026","position":100}
]}
{"type":"comparison","left":"6.0","right":"6.1"}
{"type":"flow","nodes":[
  {"kind":"logo","slug":"playstation","label":"PS5"},
  {"kind":"symbol","value":"AI"},
  {"kind":"symbol","value":"↑"}
]}
```

Rules:
- Do not default to rows of labelled boxes.
- A diagram must explain a relationship that an image cannot show as clearly.
- Use at least four treatment families in a normal Short.
- Never use the exact same visual type three beats in a row.
- Keep generic flow/diagram beats below ~35%.
- Keep text-only beats below ~25%.
- At least ~55% of beats should be rich visuals.

## Meme opportunities

Target 3-4 meme/reaction moments when natural. Keep that frequency even when more official imagery is used.

Explicitly consider reaction memes for narration such as:
- “the headline sounds wild”
- “this is wild”
- “here’s the catch”
- “not so fast”
- “this gets weird”
- “sounds great”
- “kind of insane”

The selector also detects common reaction-cue phrases automatically.

### Meme presentation

**overlay**
- narration continues
- subtitles remain
- silent images/videos float directly over the main visual
- no card, no border, no framed box
- audio memes play over the main visual

**cutaway**
- only for a video meme that actually has useful audio
- takes over the full screen
- pauses narration
- hides subtitles
- plays to a natural end when short enough
- narration resumes afterward

Silent meme images/videos must never be standalone cutaways.

Short meme-audio reactions must finish naturally; do not intentionally trim a laugh/BRUH to fit a tiny semantic beat.

Do not manually provide start/end times. The timeline compiler handles narration, cutaways, subtitles, visuals and SFX.

After successfully queuing a story, report only its headline, score, and primary source. If nothing qualifies, make no repository changes and produce no notification.
