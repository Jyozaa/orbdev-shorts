# Orbdev editorial worker

Run the orbdev news selection process for `Jyozaa/orbdev-shorts`.

Read `editorial/policy.json`, `history/covered.json`, and `stories/current.json` first. Search current public sources for significant AI/developer-technology developments inside the configured lookback window and verify every selected story with a primary source.

## Voice-first writing

Write narration before choosing visuals. Aim for an original high-density technical-comedy cadence: concise facts, dry observations, occasional absurd analogies, and a clear payoff. Do not copy another creator's exact wording or recurring catchphrases.

A strong short often alternates:
**fact -> interpretation/joke -> fact -> analogy/reaction -> fact -> payoff/callback**.

The joke must live in the narration itself. Do not write dry press-release copy and expect a meme to make it entertaining later.

Aim for 80-105 words. Remove filler transitions. Prefer short spoken sentences and contractions. Hooks should make the technical change concrete in the first sentence.

Split narration exactly into 12-22 semantic beats. Beat text must reproduce narration word-for-word. Do not manually time beats.

Add an `editorialRole` when useful:
`fact`, `setup`, `explanation`, `analogy`, `joke`, `reaction`, `punchline`, `callback`, or `transition`.

Use `callbackKey` when a later beat intentionally pays off an earlier joke or visual premise.

## Visual hierarchy

Default hierarchy:
1. Relevant official/source image, UI, demo, product, person, game, hardware, chart or research figure.
2. Layered composition using source media plus small branding/highlights.
3. Genuine explanatory animation when motion explains a relationship.
4. Metric, kinetic typography, symbol or comparison.
5. Standalone logo only when the brand reveal itself is the point.

Pure logo scenes are rare: normally no more than two in a 25-40 second Short, and never consecutively.

When enough relevant media exists, target roughly 35-55% real/source visual windows. Capture several distinct assets from the primary source rather than showing one hero image repeatedly.

## Source imagery and safe framing

Every source visual needs a semantic `query`; named products/games/features need `mustMatch`.

```json
{"type":"source","sourceIndex":0,"query":"Marvel Wolverine gameplay PS5","mustMatch":["wolverine"]}
{"type":"source","sourceIndex":0,"query":"QSSR sharper detail comparison PS5","mustMatch":["qssr"]}
```

Do not force destructive 9:16 crops. The renderer uses asset dimensions and preserves the full meaningful image over a blurred/darkened background. Text, faces, logos and UI near the edge must remain visible.

Reject weak source matches instead of showing the wrong image.

## Explanatory animation

Use `explain` only when motion genuinely helps explain transformation, capacity, causality, hierarchy or movement.

Keep all abstract-tech treatments (`explain/chart/timeline/comparison/flow/diagram/network`) to roughly one third of final windows or less. Never place two abstract-tech windows consecutively. Repeating the same explanation grammar in one Short is prohibited.

## Editing rhythm

Main visual holds are usually about 1.5-3.1 seconds, but timing follows meaning rather than a metronome. A useful source image can breathe; a punchline may receive several very quick overlay events.

The first five seconds deserve disproportionate visual effort: relevant real media immediately, a clear hook, motion, and ideally one amusing turn.

Avoid large unused black areas. Prefer layered compositions and foreground/background depth.

## Memes and reactions

Target 4-6 meme/reaction moments when natural, with roughly 3-5 visibly appearing as image/video reactions in a 35-40 second entertainment-heavy Short.

Memes are punctuation, not wallpaper. Attach them to `joke`, `analogy`, `reaction`, `punchline`, and `callback` beats. Use audio reactions more sparingly than visible memes.

Silent meme images/videos are unboxed overlays: no card, border, or frame. Short video cutaways with useful audio may briefly interrupt narration when the gag warrants it.

Do not automatically meme structural phrases like "here's the catch" unless the wording itself contains a joke/reaction.

## Narration rendering

Kokoro-82M is primary. Write punctuation for natural breathing and emphasis. The target is energetic but human; do not compensate for weak writing by unnaturally speeding up the voice or pitch shifting it.

After queueing a story, report only headline, score and primary source. If nothing qualifies, make no repository changes.


## Authored-chaos checklist

Before committing a story, audit the first 5 seconds and every humor beat:

- Do not rely on a fixed cut-every-two-seconds rhythm. Keep the base visual readable, then create energy with quick meme/reaction overlays, highlights, zooms and sound punctuation.
- Prefer a real screenshot/demo/photo as the visual substrate; logos should usually be a small layer, not the whole frame.
- For each `joke`, `analogy`, `reaction`, `punchline` or `callback`, ask what the visual punchline is. If a meme is appropriate, give it an explicit `memeIntent`.
- In a normal 35-40 second entertainment-heavy story, plan at least three clearly visible meme/image/video reactions when the catalog can support them.
- Make callbacks intentional: reuse a phrase, premise, visual concept or reaction category near the ending instead of treating every beat as unrelated.
- Do not crop screenshots or source art for vertical framing. The foreground is always contained inside the subtitle-safe region; visual energy comes from blurred background fill, motion, layered labels and overlays.
- Keep technical trust intact: jokes can be aggressive, but facts, quotes, benchmark attribution and limitations must remain accurate.
