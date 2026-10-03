# orbdev-shorts

Cloud-rendered vertical video pipeline for orbdev.

## What it does

- Reads a structured story JSON file.
- Generates narration and word timings.
- Renders a 1080x1920 short with captions and simple motion graphics.
- Runs entirely in GitHub Actions.
- Uploads the finished MP4 as a workflow artifact.

## Story format

Story files live in `stories/`.

```json
{
  "slug": "example",
  "title": "Example title",
  "narration": "Narration text...",
  "plannedDurationSeconds": 30,
  "scenes": [
    {
      "type": "hook",
      "start": 0,
      "end": 5,
      "kicker": "QUICK UPDATE",
      "title": "Main headline"
    }
  ]
}
```

Scene types currently supported:

- `hook`
- `explain`
- `comparison`
- `impact`
- `caveat`
- `outro`

## Render locally

Requirements:

- Node.js 22+
- Python 3.11+
- ffmpeg
- espeak-ng for the fallback voice

```bash
npm install
python3 -m pip install -r requirements.txt
npm run render:test
```

The finished file is written to `out/orbdev-test.mp4`.

## GitHub Actions

The `Render short` workflow renders `stories/test.json` on relevant pushes and can also be run manually from the Actions tab.

The output is stored as the `orbdev-short` artifact.
