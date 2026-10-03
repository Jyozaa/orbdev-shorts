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
4. Prefer visually useful scene types. Supported types are `hook`, `explain`, `metric`, `comparison`, `impact`, `caveat`, and `outro`.
5. Keep on-screen text short. Use `metric` scenes for one strong number rather than paragraphs.
6. When using company benchmarks, write the narration so the attribution is clear, for example "OpenAI says..." or "According to Google's benchmark...".
7. Create a stable lowercase kebab-case `storyKey`.
8. Write `stories/current.json`.
9. Append the story to `history/covered.json` after the current story has been written successfully.

A metric scene may include:

```json
{
  "type": "metric",
  "start": 5,
  "end": 10,
  "kicker": "API PRICE",
  "title": "50%",
  "body": "lower than the previous promotional price"
}
```

All scene times must be contiguous, start at zero, and end at `plannedDurationSeconds`.

After successfully queuing a story, report only its headline, score, and primary source. If no story qualifies, produce no user notification.
