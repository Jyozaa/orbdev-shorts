# Orbdev editorial worker

Run the orbdev news selection process for `Jyozaa/orbdev-shorts`.

Read `editorial/policy.json`, `history/covered.json`, and `stories/current.json` if it exists before selecting anything.

Search the public web for important AI and developer-technology announcements within the configured lookback window. Prioritize official primary sources. Secondary reporting may be used for discovery or context, but every selected story must have at least one primary source.

Orbdev is a technology-news channel. Select concrete technical news: new models, capabilities, developer tools, research results, scientific discoveries, robotics, hardware, security findings, infrastructure changes, meaningful open-source releases, and similar developments. Do not select hiring, recruitment, fellowships, training programs, educational cohorts, staffing announcements, or generic company initiatives unless a substantial new technology is the actual story.

Establish the true original announcement time from the source itself where possible. Do not use crawler dates, reposts, or page-refresh timestamps to make an old story look current.

Apply every hard rule in the policy. Score each viable candidate out of 10 using the configured weights. Do not queue anything below the minimum score. Do not exceed the daily cap in Europe/London time. Treat matching announcements, product names, URLs, or substantially identical developments as duplicates.

If nothing qualifies, make no repository changes.

If a story qualifies:

1. Verify factual claims against the primary source.
2. Write a concise, fast script within the configured word and duration targets.
3. Structure it around the technical delta: what changed, one or two concrete numbers/capabilities, why it matters, and a real limitation where relevant.
4. Prefer visual scenes that communicate with diagrams, arrows, nodes, symbols and numbers. Supported scene types are `hook`, `explain`, `metric`, `diagram`, `comparison`, `impact`, `caveat`, and `outro`.
5. Do not put paragraphs on screen. Narration carries the explanation.
6. Hook text should normally be 6 words or fewer. Metric labels should normally be 4 words or fewer. Diagram node labels should normally be 3 words or fewer.
7. For a diagram scene, use 2-4 nodes. Each node may contain a symbol and a tiny label. The renderer draws arrows between nodes automatically.
8. Add an optional `sfx` to scenes. Choose only from `yay`, `rage`, `scratch`, `impact`, `whoosh`, `tick`, or `none`. Use reactions intentionally, not on every scene.
9. Examples: a meaningful price cut may use `yay`; a painful price increase may use `rage`; a catch/reversal may use `scratch`; a major benchmark number may use `impact`.
10. When using company benchmarks, make attribution clear in narration, e.g. "OpenAI says..." or "According to Google's benchmark...".
11. Create a stable lowercase kebab-case `storyKey`.
12. Write `stories/current.json`.
13. Append the story to `history/covered.json` after the current story has been written successfully.

Example diagram scene:

```json
{
  "type": "diagram",
  "start": 8,
  "end": 14,
  "title": "cost flow",
  "sfx": "whoosh",
  "nodes": [
    {"symbol": "PROMPT", "label": "input"},
    {"symbol": "→", "label": "cache"},
    {"symbol": "90%", "label": "discount"}
  ]
}
```

Example negative-news reaction:

```json
{
  "type": "metric",
  "start": 4,
  "end": 8,
  "title": "+50%",
  "body": "subscription price",
  "sfx": "rage"
}
```

All scene times must be contiguous, start at zero, and end at `plannedDurationSeconds`.

After successfully queuing a story, report only its headline, score, and primary source. If no story qualifies, produce no user notification.
