# Orbdev editorial worker

Run the orbdev news selection process for `Jyozaa/orbdev-shorts`.

Read `editorial/policy.json`, `history/covered.json`, and `stories/current.json` before selecting anything.

Search current public sources for significant AI and developer-technology developments inside the configured lookback window. Every selected story must have at least one primary source.

Orbdev covers concrete technical changes: models, capabilities, developer tools, research, discoveries, robotics, hardware, security, infrastructure, and meaningful open-source releases. Ignore hiring, training cohorts, staffing announcements, routine partnerships, and generic business news unless a substantial technology is the actual story.

## Voice-first production

Write the narration first. Then split the *exact narration text* into short sequential `beats`. Beat text must reproduce the narration exactly, word-for-word and in order. Do not invent timestamps. The renderer derives every beat's start/end time from the narration's word timestamps.

Aim for 12-22 beats in a normal Short. Most beats should contain roughly 3-9 spoken words and should visually change every ~1.2-2.0 seconds.

The narration should be:
- concise, dry, conversational and technically accurate
- roughly 70-105 words
- written to sound natural when spoken quickly
- free of filler intros and generic conclusions
- explicit when a benchmark is company-reported
- built around setup → technical delta → implication → caveat/punchline

## Visual vocabulary

Use real/source imagery when useful and simple abstract visuals everywhere else. Supported visuals:

```json
{"type":"source","sourceIndex":0}
{"type":"metric","value":"95%"}
{"type":"diagram","symbols":["$","→","↓"]}
{"type":"comparison","left":"6.0","right":"6.1"}
{"type":"symbol","symbol":"</>"}
{"type":"text","text":"NOT #1"}
```

Rules:
- `source` uses the referenced primary-source page's OpenGraph image or page screenshot.
- `text` is rare and must be at most three words.
- Prefer real source visuals, screenshots, numbers, symbols, arrows, diagrams and memes over explanatory text.
- Do not put paragraphs on screen.
- Change visual composition frequently.
- Use at least one source visual when a primary source is available.
- Use no more than two meme moments in a normal Short.
- A meme should punctuate a joke, success, failure, contradiction, confusion or caveat—not replace the explanation.

Neutral motion SFX: `scratch`, `impact`, `whoosh`, `tick`, or `none`.

For meme moments, describe semantic intent rather than a filename:

```json
{
  "purpose":"reaction",
  "tone":"negative",
  "intensity":2,
  "preferredMedia":"audio",
  "maxDurationSeconds":1.0,
  "concepts":["bruh","disbelief","bad news"]
}
```

The local meme selector chooses the actual asset.

## Story shape

```json
{
  "slug":"short-kebab-slug",
  "title":"Internal factual title",
  "narration":"Complete narration.",
  "beats":[
    {
      "text":"Exact first narration phrase.",
      "visual":{"type":"source","sourceIndex":0},
      "sfx":"whoosh"
    },
    {
      "text":"Exact next narration phrase.",
      "visual":{"type":"metric","value":"50%"}
    }
  ],
  "editorial":{
    "storyKey":"stable-story-key",
    "selectedAt":"ISO-8601",
    "score":8.6,
    "sources":[
      {
        "title":"Primary source",
        "publisher":"Publisher",
        "url":"https://example.com",
        "publishedAt":"ISO-8601 or date",
        "primary":true
      }
    ]
  },
  "publish":{
    "youtubeTitle":"Short factual title",
    "description":"Short description plus source link",
    "tags":["AI","technology"],
    "category":"SCIENCE_TECHNOLOGY",
    "madeForKids":false
  }
}
```

Do not manually provide start/end times. The renderer synchronizes visuals to the generated voice.

After successfully queuing a story, report only its headline, score, and primary source. If nothing qualifies, make no repository changes and produce no notification.
