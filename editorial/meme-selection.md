# Meme selection

Orbdev uses approved meme assets stored directly in this repository.

The editorial layer describes the meaning of a reaction. The selector chooses the local asset. Memes should feel like a coworker dropping the perfect reaction image into the conversation, not like decorative stickers.

## Target density

For an entertainment-heavy 35-40 second Short:
- 3-6 meme/reaction opportunities are a useful range when they are genuinely relevant;
- fewer is better than inserting an unrelated reaction;
- use audio-only reactions more sparingly;
- do not repeat the same asset in one Short.

Visible memes are normally borderless overlays and may be intentionally brief. Full-screen cutaways require a short video with useful audio and must play to a natural end.

## Matching

Candidates now pass a narration-context gate before normal ranking. The selector infers semantic context from the spoken line (for example money/pricing, rejection, confusion, success/failure, waiting, large-number surprise, intelligence/efficiency, security/danger, or comparison) and from semantic metadata attached to each local meme asset. Purpose and tone only break ties after relevance is established.

If the narration has a clear context, a candidate that does not match that context is rejected even if its tone is correct. If no approved meme is relevant enough, the selector skips the meme rather than filling the slot. When `preferredMedia` is `any`, image/video is still slightly favored after contextual matching.

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
