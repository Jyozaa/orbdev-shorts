# Orbdev editorial worker

Run the orbdev news selection process for `Jyozaa/orbdev-shorts`.

Read `editorial/policy.json`, `history/covered.json`, and `stories/current.json` before selecting anything.

Search current public sources for significant AI and developer-technology developments inside the configured lookback window. Every selected story must have at least one primary source.

Orbdev covers concrete technical changes: models, capabilities, developer tools, research, discoveries, robotics, hardware, security, infrastructure, graphics technology, and meaningful open-source releases. Ignore hiring, training cohorts, staffing announcements, routine partnerships, and generic business news unless a substantial technology is the actual story.

## Voice-first production

Write narration first. Then split the exact narration into short sequential `beats`. Beat text must reproduce narration exactly, word-for-word and in order. Do not invent timestamps. The renderer derives beat timing from narration word boundaries.

Aim for 12-22 beats in a normal Short. Most beats should contain roughly 3-9 spoken words and visually change every ~1.2-2.0 seconds.

Narration should be concise, dry, conversational, technically accurate, roughly 70-105 words, free of filler intros, and explicit when benchmarks are company-reported.

## Visual vocabulary

Prefer animated graphical explanation over words on a black canvas.

Supported visuals:

```json
{"type":"source","sourceIndex":0}
{"type":"logo","slug":"playstation","label":"PlayStation"}
{"type":"flow","nodes":[
  {"kind":"logo","slug":"playstation","label":"PS5"},
  {"kind":"symbol","value":"AI"},
  {"kind":"symbol","value":"↑"}
]}
{"type":"metric","value":"95%"}
{"type":"diagram","symbols":["GPU","AI","$$$"]}
{"type":"comparison","left":"6.0","right":"6.1"}
{"type":"symbol","symbol":"</>"}
{"type":"text","text":"NOT #1"}
```

Rules:
- Logos, flows, diagrams, comparisons and source imagery are preferred over text-only scenes.
- Use a real brand logo when the beat is about a recognizable company/platform/product family and a Simple Icons slug is available.
- `logo`, `flow`, `diagram`, and `comparison` are animated automatically. Do not design static slides.
- `flow` is preferred for explaining a process or relationship. It supports logo, symbol and short-text nodes.
- Diagram arrays contain nodes only; connectors are drawn and animated automatically.
- `text` is a fallback and must be at most three words.
- Keep text-only beats below roughly 30% of the Short.
- At least ~45% of beats should be rich visuals: source, logo, flow, diagram, or comparison.
- Use at least one source visual when available.
- For a 25-40 second Short, target 3-4 meme/reaction moments when the story provides natural opportunities; never force an irrelevant meme.

## Meme presentation

A meme intent may set `presentation` to `overlay`, `cutaway`, or `auto`.

`overlay`:
- narration continues
- subtitles remain
- best for quick sounds or small reactions

`cutaway`:
- full-screen takeover
- narration pauses
- subtitles disappear
- meme plays to a natural end when it is a short video
- narration resumes afterward
- the selector rejects overly long video memes instead of chopping them mid-reaction

For cutaway videos, `maxDurationSeconds` is not a hard trim point. Short clips up to the cutaway budget are preserved to their natural end. Use `maxDurationSeconds` mainly for images or overlays.

Example:

```json
{
  "purpose":"success",
  "tone":"positive",
  "intensity":2,
  "preferredMedia":"video",
  "presentation":"cutaway",
  "concepts":["celebration","upgrade","win"]
}
```

The local meme selector chooses the actual file.

Do not manually provide start/end times. The timeline compiler inserts cutaway pauses into narration and keeps captions/visual beats synchronized automatically.

After successfully queuing a story, report only its headline, score, and primary source. If nothing qualifies, make no repository changes and produce no notification.
