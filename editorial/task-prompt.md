# Orbdev editorial worker

Run the orbdev news selection process for `Jyozaa/orbdev-shorts`.

Read `editorial/policy.json`, `history/covered.json`, and `stories/current.json` if it exists before selecting anything.

Search the public web for important AI and developer-technology announcements within the configured lookback window. Prioritize the official sources listed in the policy. Secondary reporting may be used to discover a story or add context, but every selected story must have at least one primary source.

Apply every hard rule in the policy. Score each viable candidate out of 10 using the configured scoring weights. Do not queue anything below the minimum score. Do not exceed the daily cap in Europe/London time. Treat matching announcements, product names, URLs, or substantially identical developments as duplicates.

If nothing qualifies, make no repository changes.

If a story qualifies:

1. Verify the factual claims against the primary source.
2. Write a concise script within the configured word and duration targets.
3. Structure it as a useful explanation: what changed, why it matters, and a material caveat when one exists.
4. Choose only supported scene types: `hook`, `explain`, `comparison`, `impact`, `caveat`, `outro`.
5. Create a stable lowercase kebab-case `storyKey` that identifies the underlying announcement independently of wording.
6. Build `stories/current.json` using the schema below.
7. Update `history/covered.json` with the same story key and source URLs after the current story has been written successfully.

Use this shape for `stories/current.json`:

```json
{
  "slug": "short-kebab-slug",
  "title": "Internal story title",
  "narration": "70 to 105 words",
  "plannedDurationSeconds": 34,
  "scenes": [
    {
      "type": "hook",
      "start": 0,
      "end": 5,
      "kicker": "QUICK UPDATE",
      "title": "Short headline"
    }
  ],
  "editorial": {
    "storyKey": "stable-story-key",
    "selectedAt": "ISO-8601 timestamp",
    "score": 8.4,
    "topics": ["models"],
    "companies": ["Example"],
    "sources": [
      {
        "title": "Primary source title",
        "publisher": "Example",
        "url": "https://example.com/source",
        "publishedAt": "ISO-8601 timestamp when available",
        "primary": true
      }
    ]
  },
  "publish": {
    "youtubeTitle": "Short, factual title",
    "description": "Two concise sentences followed by source links.",
    "tags": ["AI", "technology"],
    "category": "SCIENCE_TECHNOLOGY",
    "madeForKids": false
  }
}
```

Scene times must be contiguous, start at zero, and end at `plannedDurationSeconds`. Keep on-screen text compact enough for a vertical phone display. Do not use unsupported claims in hooks.

For `history/covered.json`, append:

```json
{
  "storyKey": "stable-story-key",
  "slug": "short-kebab-slug",
  "headline": "Internal story title",
  "selectedAt": "ISO-8601 timestamp",
  "score": 8.4,
  "sourceUrls": ["https://example.com/source"]
}
```

After successfully queuing a story, report only its headline, score, and primary source. If no story qualifies, produce no user notification.
