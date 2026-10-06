# Story queue

The editorial worker writes one validated story JSON per independently qualifying topic into this directory.

A single 12-hour discovery scan may add zero, one, or many files.

Naming convention:

```
stories/queue/<yyyy-mm-dd>-<slug>.json
```

Each file uses the same schema as `stories/current.json`.

On push, `.github/workflows/render-queue.yml` renders only the queue JSON files added or changed by that push. Multiple files render in parallel.

When repository variable `ORBDEV_AUTO_PUBLISH` is set to `true` and the YouTube OAuth secrets are configured, each successful render is uploaded immediately after rendering. There are no fixed posting time blocks.


The scheduled ChatGPT editorial automation writes accepted story files here through the connected GitHub repository. Those queue-file pushes trigger `.github/workflows/render-queue.yml`, which renders only the queue files changed by that push.

Do not mark a story covered when it is queued. Successful render receipts update `history/covered.json` later so failed renders remain retryable.


## Production YouTube metadata

Every newly queued production story should follow `editorial/youtube-metadata.md` and set `publish.metadataVersion: 1`.

New stories must include an optimized YouTube title, concise description, 4-15 metadata tags, 3-5 visible hashtags, public privacy, `madeForKids: false`, and compact metadata-review scores. `scripts/validate_story.py` enforces this contract for metadataVersion 1 stories.

The uploader appends any missing primary-source URLs and the visible hashtag line to the final YouTube description. Metricool is used only for performance feedback; it does not delay or perform the upload.

## Video-identity and media-diversity gate

Repeat topics are allowed. A second Short may use the same announcement, paper,
repository, or primary URL when its narration/angle/visual plan is genuinely
different. The queue only suppresses an identical narration + storyboard plan,
and the YouTube boundary checks the rendered MP4 SHA-256 when a prior upload hash
is available.

The renderer uses each distinct source image at most once (old `allowReuse`
flags are ignored). Videos with repeated source imagery or weak text-heavy
fallback plans are rejected before publishing. When useful source media is
scarce, the deterministic diagram planner should explain the mechanism rather
than recycle an image or fill the screen with narration text.

## Repeat-topic publishing policy (Phase 1)

The same announcement, research paper or open-source repository may inspire more
than one Orbdev Short. Each video should add a genuinely different insight,
angle, or visual explanation. Use a fresh slug for every creative take. The
queue suppresses identical narration + storyboard payloads, not matching source
URLs or event keywords. After rendering, the YouTube uploader uses the actual
MP4 SHA-256 to reject byte-for-byte reuploads already recorded in published
history. Legacy uploads without stored hashes cannot be byte-verified
retroactively. No external AI model or AI API key is involved.
