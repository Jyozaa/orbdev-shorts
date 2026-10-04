# Meme selection

Orbdev uses approved meme assets stored directly in this repository.

The editorial layer describes the meaning of a reaction. The selector chooses the local asset. Memes should feel like a coworker dropping the perfect reaction image into the conversation, not like decorative stickers.

## Target density

For an entertainment-heavy 35-40 second Short:
- target 4-6 total meme/reaction moments when natural;
- aim for roughly 3-5 visible image/video reactions;
- use audio-only reactions more sparingly;
- do not repeat the same asset in one Short.

Visible memes are normally borderless overlays and may be intentionally brief. Full-screen cutaways require a short video with useful audio and must play to a natural end.

## Matching

Candidates are ranked by purpose, tone, semantic concepts, requested media, intensity, and tag/name affinity. When `preferredMedia` is `any`, the selector slightly favors image/video so the edit does not silently become audio-only.

The editorial roles `joke`, `reaction`, `analogy`, `punchline`, and `callback` can generate automatic meme opportunities when explicit `memeIntent` is absent.

## Example

```json
{
  "editorialRole": "punchline",
  "memeIntent": {
    "purpose": "punchline",
    "tone": "deadpan",
    "intensity": 2,
    "preferredMedia": "image",
    "presentation": "overlay",
    "concepts": ["nope", "disbelief", "reaction"]
  }
}
```
