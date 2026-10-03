# Orbdev editorial worker

Run the orbdev news selection process for `Jyozaa/orbdev-shorts`.

Read `editorial/policy.json`, `history/covered.json`, and `stories/current.json` if it exists before selecting anything.

Search current public sources for important AI and developer-technology announcements inside the configured lookback window. Prioritize official primary sources. Secondary reporting may be used for discovery or context, but every selected story must have at least one primary source.

Orbdev covers concrete technical developments: new models, capabilities, developer tools, research results, discoveries, robotics, hardware, security findings, infrastructure changes, and meaningful open-source releases. Do not select hiring, recruitment, fellowships, training programs, educational cohorts, staffing announcements, or generic company initiatives unless a substantial new technology is the actual story.

Establish the true original announcement time from the source itself where possible. Do not use crawler dates, reposts, or page-refresh timestamps to make old news look current.

Apply every hard rule in the policy. Score each viable candidate using the configured weights. Do not queue anything below the minimum score or above the daily cap.

If nothing qualifies, make no repository changes.

If a story qualifies:

1. Verify factual claims against the primary source.
2. Write a concise script inside the configured word and duration targets.
3. Structure it around the technical delta: what changed, concrete numbers/capabilities, why it matters, and a material limitation when relevant.
4. Prefer visual scenes using diagrams, arrows, nodes, symbols and numbers. Supported scene types are `hook`, `explain`, `metric`, `diagram`, `comparison`, `impact`, `caveat`, and `outro`.
5. Do not put paragraphs on screen. Narration carries the explanation.
6. Outside subtitles, default to symbols and numbers. Hook text should normally be three words or fewer. Metric scenes should normally have no label. Diagram node labels should normally be omitted.
7. Use 2-4 nodes for a diagram. Prefer symbols such as `6.0`, `6.1`, `$`, `%`, `</>`, `⚙`, `↑`, and `↓`.
8. Use built-in transition SFX only for neutral motion cues: `scratch`, `impact`, `whoosh`, `tick`, or `none`.
9. For comedic or emotional reactions, describe a `memeIntent` instead of naming a specific meme. The selector will choose the asset later.
10. A `memeIntent` must specify:
   - `purpose`: reaction, punchline, contrast, confusion, failure, success, waiting, absurdity, or emphasis
   - `tone`: positive, negative, surprised, confused, awkward, deadpan, chaotic, or neutral
   - `intensity`: 1, 2, or 3
   - optional `preferredMedia`: audio, image, video, or any
   - optional `maxDurationSeconds`
   - optional `concepts`: 2-5 short semantic cues such as `celebration`, `bruh`, `facepalm`, `waiting`, `confusion`, `money`, or `disbelief`
11. Use no more than two meme moments in a normal Short. A meme should land immediately after the statement it reacts to, not randomly in the middle of an explanation.
12. When using company benchmarks, clearly attribute them in narration.
13. Create a stable lowercase kebab-case `storyKey`.
14. Write `stories/current.json`.
15. Append the story to `history/covered.json` after the current story has been written successfully.

Example:

```json
{
  "type": "metric",
  "start": 5,
  "end": 9,
  "title": "+50%",
  "sfx": "impact",
  "memeIntent": {
    "purpose": "reaction",
    "tone": "negative",
    "intensity": 3,
    "preferredMedia": "audio",
    "maxDurationSeconds": 1.5
  }
}
```

The editorial worker describes the reaction. It does not choose the actual meme file. The meme selector maps that intent to the curated meme catalog.

All scene times must be contiguous, start at zero, and end at `plannedDurationSeconds`.

After successfully queuing a story, report only its headline, score, and primary source. If no story qualifies, produce no user notification.
