# orbdev-shorts

Automated discovery, editorial planning and cloud rendering for Orbdev vertical tech-news Shorts.

## Pipeline

Orbdev separates discovery from verification and rendering:

```
12-hour discovery scan
  -> Major News
  -> Hot / Emerging
  -> Creator Radar
  -> cross-lane clustering + heat scoring
  -> editorial inbox
  -> primary-source verification
  -> one story JSON per qualifying topic
  -> parallel Remotion renders
  -> optional immediate YouTube upload
```

There are no fixed posting time blocks and no fixed daily story cap. A scan may produce zero, one or many Shorts. Lane diversity is a soft discovery goal, never a quota.

## Discovery lanes

**Major News** searches significant AI, developer, robotics, research, hardware and infrastructure announcements.

**Hot / Emerging** actively hunts fast-rising GitHub repositories, open-source developer tools, coding agents, Hacker News momentum and trending Hugging Face models. Momentum age can matter more than repository creation age.

**Creator Radar** monitors the configured channels in `editorial/discovery.json`. Long roundup videos are split into chapter/transcript topics when possible. Creator commentary is used for discovery, context and heat only; factual claims still require primary-source verification.

The current Creator Radar includes Fireship, AI Search, Two Minute Papers, AI Explained, Matt Wolfe, ThePrimeTime, Matthew Berman and All About AI.

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

Kokoro-82M is the primary narrator. Narration is synthesized by semantic beat rather than as one flat paragraph.

The renderer uses subtle `editorialRole` prosody:
- facts/setup stay brisk;
- explanations stay clear and even;
- analogies/jokes relax slightly;
- reactions/punchlines receive small setup pauses and slightly slower deadpan delivery;
- callbacks receive a brief setup pause;
- transitions are faster.

Post-tempo acceleration is deliberately light. The target remains roughly 180-195 effective WPM, but writing density and silence removal do more of the work than brute-force audio speedup.

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

## Editorial policy

- `editorial/policy.json` contains the hard editorial and rendering rules.
- `editorial/discovery.json` configures discovery lanes, Creator Radar and heat signals.
- `editorial/discovery-worker.md` defines verification and deduplication behavior.
- `editorial/task-prompt.md` defines story writing, explanation, humor, visual planning and queue behavior.
