# Meme selection

Orbdev does not choose memes from the narration by exact filename matching.

The editorial step describes the *reaction intent* for a scene. A separate selector matches that intent against a curated catalog built from `Jyozaa/memes`.

## Selection fields

Each meme catalog item should contain:

- `id`
- `path`
- `mediaType`: audio, image, or video
- `tags`: semantic concepts such as disbelief, facepalm, success, failure, waiting, awkward, confusion
- `tones`: positive, negative, surprised, confused, awkward, deadpan, chaotic, neutral
- `purposes`: reaction, punchline, contrast, confusion, failure, success, waiting, absurdity, emphasis
- `intensity`: 1-3
- `durationSeconds`
- `brandSafe`
- `rightsStatus`: approved, review, blocked
- `cooldown`: how recently it was used

## Matching

For each scene with `memeIntent`, score catalog items using:

- purpose match: 35%
- tone match: 25%
- semantic tag overlap: 20%
- requested media type: 10%
- intensity fit: 5%
- freshness / repetition penalty: 5%

Reject an item before scoring when:

- it exceeds the requested duration
- `brandSafe` is false
- `rightsStatus` is not approved
- it was used too recently
- its media type does not fit the scene

The selector should prefer no meme when the best score is below a confidence threshold. This prevents forced or irrelevant jokes.

## Examples

"API price increased 50%" can produce:

```json
{
  "purpose": "reaction",
  "tone": "negative",
  "intensity": 3,
  "preferredMedia": "audio"
}
```

Potential catalog matches could include a brief "BRUH", wrong-answer buzzer, facepalm clip, or another approved frustration asset.

"A model is 5x faster" can produce:

```json
{
  "purpose": "success",
  "tone": "positive",
  "intensity": 2,
  "preferredMedia": "video"
}
```

Potential matches could include an approved celebration clip.

"This benchmark has one weird caveat" can produce:

```json
{
  "purpose": "confusion",
  "tone": "confused",
  "intensity": 2,
  "preferredMedia": "image"
}
```

Potential matches could include an approved confused reaction image.

The catalog should be curated once and then reused by every scheduled run. The scheduled editor never needs to inspect thousands of binary meme files.
