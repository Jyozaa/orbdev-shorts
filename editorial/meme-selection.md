# Meme selection

Orbdev uses the meme folders stored directly inside this repository:

- `Meme Pack/Meme Sound Effects/`
- `Meme Pack/Meme Videos/`
- `Memes templates -HD-/`
- `Memes templates -HD- 2/`

Green-screen assets are currently excluded until chroma-key compositing is implemented.

The editorial step does not choose a meme by filename. It describes the reaction intent for a scene, and the local selector matches that intent against a catalog generated from the meme folders during the render.

## Selection fields

Each catalog item contains:

- `id`
- `path`
- `mediaType`: audio, image, or video
- `tags`
- `tones`
- `purposes`
- `intensity`
- `brandSafe`
- `rightsStatus`

## Matching

For each scene with `memeIntent`, candidates are scored using:

- purpose match: 35%
- tone match: 25%
- semantic tag overlap: 20%
- requested media type: 10%
- intensity fit: 5%
- concept/name affinity: small bonus

The selector uses a confidence threshold. If no meme scores well enough, the Short renders without a meme for that moment.

The selected source file is read directly from this repository, normalized into `public/memes/`, then inserted into the Remotion render. There is no cross-repository API lookup or asset download.

## Example

```json
{
  "memeIntent": {
    "purpose": "reaction",
    "tone": "negative",
    "intensity": 2,
    "preferredMedia": "audio",
    "maxDurationSeconds": 1.0,
    "concepts": ["bruh", "disbelief", "bad news"]
  }
}
```

The editor describes the meaning of the reaction. The selector decides which local meme asset best expresses it.

Normal Shorts should use no more than two meme moments so the memes remain punchlines rather than becoming the whole video.
