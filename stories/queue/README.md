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
