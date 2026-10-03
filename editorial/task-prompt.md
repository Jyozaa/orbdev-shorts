# Orbdev editorial worker

Run the orbdev news selection process for `Jyozaa/orbdev-shorts`.

Read `editorial/policy.json`, `history/covered.json`, and `stories/current.json` before selecting anything.

Search current public sources for significant AI and developer-technology developments inside the configured lookback window. Every selected story must have at least one primary source.

Orbdev covers concrete technical changes: models, capabilities, developer tools, research, discoveries, robotics, hardware, security, infrastructure, and meaningful open-source releases. Ignore hiring, training cohorts, staffing announcements, routine partnerships, and generic business news unless a substantial technology is the actual story.

## Voice-first production

Write narration first. Then split the exact narration into short sequential `beats`. Beat text must reproduce narration exactly, word-for-word and in order. Do not invent timestamps. The renderer derives beat timing from narration word boundaries.

Aim for 12-22 beats in a normal Short. Most beats should contain roughly 3-9 spoken words and visually change every ~1.2-2.0 seconds.

Narration should be concise, dry, conversational, technically accurate, roughly 70-105 words, free of filler intros, and explicit when benchmarks are company-reported.

## Visual vocabulary

Supported visuals:

```json
{"type":"source","sourceIndex":0}
{"type":"metric","value":"95%"}
{"type":"diagram","symbols":["$","↓"]}
{"type":"comparison","left":"6.0","right":"6.1"}
{"type":"symbol","symbol":"</>"}
{"type":"text","text":"NOT #1"}
```

Rules:
- Prefer real/source imagery, metrics, symbols, diagrams, screenshots and memes over explanatory text.
- Keep diagram symbols short; the renderer fits them automatically inside responsive boxes.
- Diagram arrays contain nodes only. Do not put arrows such as `→` in the array; the renderer draws connectors automatically.
- `text` is rare and must be at most three words.
- Use at least one source visual when available.
- For a 25-40 second Short, target 3-4 meme/reaction moments when the story provides natural opportunities; never force an irrelevant meme.
- Mix quick audio/visual overlays with at least one stronger visual reaction when appropriate.
- Memes should punctuate setup, payoff, contradiction, absurdity, waiting, success, or failure.

Neutral motion SFX: `scratch`, `impact`, `whoosh`, `tick`, or `none`.

## Meme presentation

A meme intent may set `presentation` to `overlay`, `cutaway`, or `auto`.

`overlay`:
- narration continues
- subtitles remain
- best for quick sounds, small reaction images, short punch-ins

`cutaway`:
- full-screen takeover
- narration automatically pauses
- subtitles disappear
- meme audio/video plays
- narration resumes afterward
- best for standalone punchlines such as "2000 Years Later", reaction clips, facepalms, or a deliberate comedy beat

`auto`:
- selector chooses based on media type, purpose and intensity
- strong visual memes usually become cutaways; audio reactions usually remain overlays

Example cutaway:

```json
{
  "purpose":"waiting",
  "tone":"deadpan",
  "intensity":2,
  "preferredMedia":"video",
  "presentation":"cutaway",
  "maxDurationSeconds":1.7,
  "concepts":["waiting","later","long time"]
}
```

Example laughter/audio reaction:

```json
{
  "purpose":"punchline",
  "tone":"chaotic",
  "intensity":2,
  "preferredMedia":"audio",
  "presentation":"overlay",
  "maxDurationSeconds":0.8,
  "concepts":["laugh","laughter","comedy"]
}
```

The local meme selector chooses the actual file.

Do not manually provide start/end times. The timeline compiler inserts cutaway pauses into narration and keeps captions/visual beats synchronized automatically.

After successfully queuing a story, report only its headline, score, and primary source. If nothing qualifies, make no repository changes and produce no notification.
