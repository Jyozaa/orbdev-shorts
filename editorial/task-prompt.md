# Orbdev editorial worker

Run the orbdev news selection process for `Jyozaa/orbdev-shorts`.

Read `editorial/policy.json`, `editorial/script-review.md`, `editorial/discovery.json`, `editorial/inbox/latest.json`, `editorial/discovery-worker.md`, `history/covered.json`, and `stories/current.json` first. The scheduled discovery scan searches Major News, Hot / Emerging and Creator Radar every 12 hours. Treat its inbox as a high-recall candidate set, not verified truth. Re-search and verify every selected topic with a primary source before writing.

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

## Mandatory multi-pass script workflow

For every qualifying topic, follow `editorial/script-review.md` before visual planning.

The required sequence is:

**verified research -> writer draft -> critic score -> rewrite when needed -> critic re-score -> factual re-check -> beat/visual planning -> queue**

The first draft is never automatically considered final.

During the writer and critic passes, ignore visuals, memes, captions, SFX and editing. Judge whether the narration alone would hold attention and explain the story clearly.

A script may proceed only when it meets the thresholds in `editorial/script-review.md`: average >= 8.0/10, no category below 7.0, and factual discipline >= 8.0. If it fails, rewrite it and score it again. After three unsuccessful iterations, reject that topic for the current batch instead of queueing weak narration.

After a script passes, re-check every material claim against primary sources. If factual corrections materially change the narration, re-run the critic once more.

For newly queued stories, include the compact `editorial.scriptReview` scores and iteration count when practical. Never store chain-of-thought or long private critique text in the repository.

## Spoken-copy quality gate

The script must sound natural before any memes, visuals or TTS are added. Treat this as a hard editorial pass, not a style preference.

Prefer one central idea per Short. Every sentence should either explain that idea, sharpen its practical implication, introduce the important caveat, or pay off the premise. Do not turn a model card, changelog or press release into a spoken feature list.

Avoid generic AI-news phrasing and synthetic transitions such as:
- "X just dropped";
- "the trick is";
- "here's the catch";
- "so yes";
- "game changer";
- "this changes everything";
- "in other words" when a more direct sentence works.

Do not use those phrases merely because they create an easy hook. A hook should expose the surprising technical contrast itself.

Write for speech:
- contractions are preferred when natural;
- vary sentence length aggressively;
- allow a 2-5 word sentence when it creates contrast or deadpan timing;
- use concrete nouns and verbs instead of abstract product language;
- explain the practical consequence of a number instead of stacking specifications;
- keep at most 2-3 headline numbers unless additional numbers are essential to the story;
- prefer one memorable analogy or dry observation over several separate jokes.

Humor should usually emerge from the explanation. A caveat can be the joke. A comparison can be the punchline. Avoid appending a joke sentence after a dry paragraph merely to make the script feel entertaining.

Before queueing, read the narration aloud mentally and reject it if it sounds like written copy being recited. Rewrite any sentence that feels like a press release, list of capabilities, or generic AI summary.

A strong default structure is:
**surprising technical contrast -> what it is -> how it works -> practical benefit -> caveat -> concise payoff**.

This is a structure, not a template. Do not repeat identical hooks or punchline patterns across stories.

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

Process every independently qualifying topic from the scan, not only the single highest-scoring topic. One creator roundup may therefore produce several separate Shorts. Do not force representation from an empty/weak lane. For each accepted topic, create a separate story JSON and report headline, lane(s), final score and primary source. If nothing qualifies, make no story changes.


## Authored-chaos checklist

Before committing a story, audit the first 5 seconds and every humor beat:

- Do not rely on a fixed cut-every-two-seconds rhythm. Keep the base visual readable, then create energy with quick meme/reaction overlays, highlights, zooms and sound punctuation.
- Prefer a real screenshot/demo/photo as the visual substrate; logos should usually be a small layer, not the whole frame.
- For each `joke`, `analogy`, `reaction`, `punchline` or `callback`, ask what the visual punchline is. If a meme is appropriate, give it an explicit `memeIntent`.
- In a normal 35-40 second entertainment-heavy story, plan at least three clearly visible meme/image/video reactions when the catalog can support them.
- Make callbacks intentional: reuse a phrase, premise, visual concept or reaction category near the ending instead of treating every beat as unrelated.
- Do not crop screenshots or source art for vertical framing. The foreground is always contained inside the subtitle-safe region; visual energy comes from blurred background fill, motion, layered labels and overlays.
- Keep technical trust intact: jokes can be aggressive, but facts, quotes, benchmark attribution and limitations must remain accurate.


## Pacing target

Aim for a compressed broadcast cadence rather than a conventional explainer cadence. Narration should generally land around 175-190 effective WPM when the wording remains intelligible. Prefer better sentence rhythm over maximum speed. Write shorter clauses and remove filler instead of relying only on TTS acceleration.

Visual pacing follows editorial meaning:
- factual/source visuals usually hold around 1.1-2.5 seconds;
- jokes, reactions, analogies, punchlines and callbacks should normally get their own visual beat;
- the first five seconds should change major visual ideas roughly every 0.9-1.6 seconds when readable;
- use sub-second meme/reaction overlays for extra energy rather than making every source image unreadably brief;
- long source visuals may remain on screen if overlays, zooms, highlights or reaction events create internal motion.


## Discovery batch behavior

The scan is not a posting calendar. There are no fixed upload slots.

Every 12 hours:
1. inspect all three discovery lanes;
2. cluster duplicates across lanes;
3. use creator/community convergence as a heat signal;
4. independently verify candidate facts;
5. publish/render every topic that still clears the editorial threshold.

Aim to find at least one worthwhile topic from each lane, but this is a soft discovery goal only. A lane with no strong topic contributes zero stories.

Hot / Emerging topics should include niche technical developments, not only mainstream AI headlines. Explicitly consider fast-growing GitHub projects, open-source models, developer tools, coding agents, CLIs, runtimes, MCP tooling, local-AI projects, Hacker News momentum and Hugging Face momentum.

Creator Radar videos must be decomposed at topic level. A 30-minute roundup can generate multiple Shorts if several topics independently qualify. Never publish one generic recap merely because the topics came from the same creator upload.

When the same topic appears in Major News, Hot / Emerging and/or Creator Radar, merge it into one story candidate and record the convergence as heat.

## Explanation quality

Use Creator Radar to learn what questions are worth answering, not to copy wording. Strong scripts should normally make clear:
- what changed;
- what the thing actually is;
- why it matters in practice;
- how it compares with the obvious alternative;
- price/access/availability when material;
- the important caveat or limitation;
- the concise implication/payoff.

This combines high information density with enough explanation that a viewer can understand why the headline matters.

## Role-aware narration

The renderer now synthesizes semantic beats with subtle editorial-role prosody. Write roles intentionally:
- `fact` / `setup`: brisk;
- `explanation`: clear and even;
- `analogy` / `joke`: slightly more relaxed;
- `reaction` / `punchline`: allow a tiny setup pause and deadpan delivery;
- `callback`: brief setup pause;
- `transition`: fast connective delivery.

Do not compensate for a weak script by writing excessive punctuation or forcing every beat to sound dramatic.


## Queue contract for multiple Shorts

For each candidate that survives primary-source verification and final editorial scoring:

- write one file to `stories/queue/<yyyy-mm-dd>-<slug>.json`;
- use the same story schema and validation rules as `stories/current.json`;
- do **not** modify `history/covered.json` when queueing; successful render receipts update covered history later;
- never combine unrelated qualifying topics just to reduce the number of queue files.

A single scan may therefore add several queue JSON files. The queue render workflow will fan them out into independent render jobs.

Keep `stories/current.json` as the manual/single-story inspection target; scheduled editorial batches should use `stories/queue/`.

When auto-publishing is enabled, the story's `publish` block controls YouTube metadata. Use a factual title, source-linked description, appropriate tags, Science & Technology category unless another category is clearly better, and `madeForKids: false` for normal Orbdev content.


## Scheduled ChatGPT editorial contract

Discovery qualification is not publication approval. The scheduled ChatGPT automation is the only autonomous editorial runner. GitHub Actions performs discovery, rendering and optional publishing, but does not call an LLM API.

The scheduled GPT run must explicitly separate researcher, writer, critic/editor, rewriter and production-planner stages. Do not collapse them into a single "write a good script" pass. A story is not queue-ready until the narration-only critic gate and post-rewrite factual re-check both pass.

For each promising lead, use live web research and independently verify the underlying development. At least one primary source must be backed by discovery evidence or live research before accepting a story.

A candidate needs a base editorial score of at least 6.0 before heat is applied. The final score may receive up to +2 heat from current momentum/cross-lane convergence, capped at 10, but the normal minimum publication score still applies.

Queue accepted stories in one GitHub commit when practical. Do not add a story to covered history merely because it was queued. Covered history is updated from successful render receipts so failed jobs remain retryable.


## Speech-chunk authoring

Visual beats and spoken chunks are intentionally decoupled. Do not add punctuation merely to force every visual beat to sound separate.

The narrator groups compatible visual beats into roughly 8-16 word thought-groups. Factual/setup/explanation beats that form one spoken sentence should flow together. Jokes, reactions, punchlines and callbacks are allowed to break into their own speech chunk for deadpan timing.

The deadpan production target is about 182 effective WPM. The engine first adjusts Kokoro's native synthesis speed toward the selected profile target and only allows a very small final tempo correction. This is meant to preserve natural articulation rather than mechanically speeding a slower performance.

Use punctuation as a real speaker would:
- periods/questions for genuine sentence boundaries;
- commas for clauses;
- a colon or dash when a setup genuinely needs a payoff;
- avoid ellipses unless an audible hesitation is actually intended.
