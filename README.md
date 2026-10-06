# orbdev-shorts

Automated discovery, editorial planning and cloud rendering for Orbdev vertical tech-news Shorts.

## Pipeline

Orbdev separates discovery from verification and rendering:

```
12-hour discovery scan
  -> Major News
  -> Market / Business
  -> Hot / Emerging
  -> Creator Radar
  -> cross-lane clustering + heat scoring
  -> editorial inbox
  -> scheduled ChatGPT research + primary-source verification
  -> one story JSON per qualifying topic
  -> parallel Remotion renders
  -> optional immediate YouTube upload
```

There are no fixed posting time blocks and no fixed daily story cap. A scan may produce zero, one or many Shorts. Lane diversity is a soft discovery goal, never a quota.

## Discovery lanes

**Major News** searches significant AI, developer, robotics, hardware and infrastructure announcements, plus mathematical/scientific findings and confirmed cybersecurity incidents such as breaches, ransomware, zero-days, supply-chain attacks and data/credential leaks.

**Market / Business** tracks material business developments involving AI companies, Big Tech and major consulting firms: earnings/guidance, AI/cloud/chip/data-centre spending, M&A, IPO/financing/valuation events, major contracts and consequential strategic changes. Generic stock-price chatter is excluded unless there is a concrete verified catalyst.

**Hot / Emerging** actively hunts fast-rising GitHub repositories, GitHub Trending, open-source developer tools, runtimes/CLIs/databases/compilers, coding agents, Hacker News momentum and trending Hugging Face models. Momentum age can matter more than repository creation age, and low-signal new repos must clear standalone evidence gates unless another lane independently confirms the topic.

**Creator Radar** monitors the configured channels in `editorial/discovery.json`. Long roundup videos are split into chapter/transcript topics when possible. Creator commentary is used for discovery, context and heat only; factual claims still require primary-source verification.

The current Creator Radar includes Fireship, AI Search, Two Minute Papers, AI Explained, Matt Wolfe, ThePrimeTime, Matthew Berman and All About AI. Creator uploads are processed once per discovery state, and high-recall roundup channels receive larger per-video topic budgets so a single roundup can generate multiple independent candidates.

The scheduled scan is defined in `.github/workflows/discovery-scan.yml`. It writes its latest editorial candidate set to `editorial/inbox/latest.json` and uploads a full scan report as a workflow artifact.

## Multiple stories per scan

Scheduled editorial batches should write one accepted story per file:

```
stories/queue/2026-10-04-example-story.json
stories/queue/2026-10-04-another-story.json
```

A single commit containing several queue files triggers `.github/workflows/render-queue.yml`, which renders the changed stories independently in parallel.

`stories/current.json` remains the single-story/manual inspection path used by `.github/workflows/render-short.yml`.

## Narration

Kokoro-82M is the primary narrator, using the Michael voice in one continuous full-script synthesis pass.

Visual/editorial beats do not create separate TTS recordings. `editorialRole` still guides visual rhythm, meme intent and callbacks, while spoken pacing comes from natural punctuation and the continuous performance.

Trailing audio is not trimmed from Kokoro segments, preserving final consonants and sentence decay. The target is roughly 172 effective WPM, with natural articulation taking priority over exact speed.

## Rendering locally

Requirements:
- Node.js 22+
- Python 3.12+
- ffmpeg
- espeak-ng for the emergency narration fallback

```bash
npm install
python3 -m pip install -r requirements.txt
python3 scripts/validate_story.py stories/test.json
python3 scripts/generate_narration.py stories/test.json
python3 scripts/prepare_render_props.py stories/test.json
npx remotion render src/index.ts OrbdevShort out/orbdev-test.mp4 \
  --props=build/render-props.json \
  --codec=h264 \
  --pixel-format=yuv420p
```

## Optional YouTube auto-publishing

Auto-publishing is disabled unless repository variable:

```
ORBDEV_AUTO_PUBLISH=true
```

is configured.

The repository must also provide these GitHub Actions secrets:

```
YOUTUBE_CLIENT_ID
YOUTUBE_CLIENT_SECRET
YOUTUBE_REFRESH_TOKEN
```

When enabled, each successful queued render is uploaded immediately using the story's `publish` metadata. No fixed publication clock is used.

New production stories use `publish.metadataVersion: 1` and must pass the YouTube metadata contract in `editorial/youtube-metadata.md`: optimized title, concise description, focused metadata tags, 3-5 visible hashtags, public privacy, and metadata-review scores. The uploader automatically appends missing primary-source URLs and the visible hashtag line to the final description.

Metricool remains outside the upload path. The scheduled GPT editorial worker may read recent YouTube performance from the connected Metricool brand as a soft feedback signal, with a minimum sample threshold; Metricool never delays immediate publishing.

## Editorial policy

- `editorial/policy.json` contains the hard editorial and rendering rules.
- `editorial/discovery.json` configures discovery lanes, Creator Radar and heat signals.
- `editorial/discovery-worker.md` defines verification and deduplication behavior.
- `editorial/task-prompt.md` defines story writing, explanation, humor, visual planning and queue behavior.


## Scheduled editorial handoff

GitHub Actions owns deterministic discovery, rendering and optional YouTube publishing. The repository does **not** require an OpenAI API key for autonomous editorial work.

The scheduled ChatGPT automation reads `editorial/inbox/latest.json` after the twice-daily discovery scans, performs live-web research and primary-source verification, applies the editorial quality/heat thresholds, and writes one validated `stories/queue/*.json` file per accepted topic through the connected GitHub repository.

Queue-file pushes trigger `.github/workflows/render-queue.yml`. Successful render receipts—not editorial acceptance—add stories to `history/covered.json`, so failed renders remain retryable.

This keeps the four discovery lanes, Creator Radar, heat scoring, narration, rendering and publishing logic inside the repo while using the existing ChatGPT scheduled automation as the sole editorial reasoning layer.


## Narration profiles

Production narration uses `editorial/narration-profiles.json`. The default `orbdev-deadpan` profile uses Michael with continuous Kokoro synthesis and targets roughly 172 WPM.

The complete narration is passed to Kokoro as one performance. Visual beats and editorial roles never force speech cuts. Native-speed retargeting and final `atempo` correction are deliberately conservative so word endings and prosody remain natural.

Every render writes `build/narration-report.json` with synthesis mode, native speed, raw/final WPM and applied tempo. The manual `Narration audition` workflow can render voice variants without changing production defaults.

## Production quality and backfill safeguards (October 2026)

- `scripts/capture_sources.py` fingerprints source images and rejects near duplicates.
- `scripts/prepare_render_props.py` never reuses source imagery, even if an old story has `allowReuse: true`; it selects distinct story-specific compositions and rotates diagram layout variants against recent successful renders.
- `scripts/check_visual_quality.py` blocks renders with repeated images, excessive generic fallbacks or repeated diagram layouts.
- `scripts/filter_queue.py` suppresses identical storyboards, **not** stories about the same event. Another original angle on the same development is allowed, even with the same primary source URL.
- `scripts/publish_youtube.py` checks SHA-256 of the actual rendered MP4 against previous confirmed uploads. A new story may reuse the topic; the *exact same video bytes* cannot be uploaded again when a previous checksum exists. Successful uploads persist the video and story-plan hashes.
- Successful render/publish receipts update `history/covered.json` and `history/visual-history.json` *after fetching the newest branch state*, with serialized history writes and retries.
- `editorial/inbox/backfill-progress.json` lets the twice-daily editorial automation work through the historical September 25–October 6 lead set over several runs without forgetting reviewed or rejected candidates.
- The editorial worker still verifies primary sources and writes a reviewed script before queuing. Discovery qualification by itself is **not** publication approval. New video counts depend on verified stories and the independent YouTube upload limit.

The quality CI check runs Python syntax/regression tests and TypeScript typechecking without rendering or uploading.
