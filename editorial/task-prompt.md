# Orbdev editorial worker

## Continuous editorial throughput and historical backfill

The 25 September–6 October 2026 discovery backfill is saved at
`editorial/inbox/backfill-2026-09-25-to-2026-10-06.json`. It contains *candidates*,
not preverified stories. Read `editorial/inbox/backfill-progress.json` on every
editorial run. Research up to 12 unprocessed, high-signal historical candidates per
run, in addition to urgent fresh topics. Prioritise substantial technical news and
independent primary-source verification. Work across all four discovery lanes when
there are credible leads, without imposing a one-video-per-lane limit or arbitrary
daily posting cap. One creator roundup may produce multiple independently verified
Shorts. Write a complete story for **every** candidate that passes verification and
script critique; do not stop after the first successful story.

For every examined backfill candidate, persist its `clusterId` with outcome
`queued`, `already-covered`, `rejected` (include a short reason), or
`needs-research`. A prior Short on the same development does not imply
`already-covered` when a demonstrably different, independently useful angle
exists. Do not repeatedly reprocess the same failed lead. Store that
state in `editorial/inbox/backfill-progress.json` in the same commit as story queue
files when possible. The next scheduled run resumes where the previous one stopped.
Never queue generic templated narration simply to meet a target count.

Before queueing, check both `history/covered.json` and the entire
`stories/queue/` directory for **exactly repeated videos**, not repeated
headlines or primary URLs. **A topic may have more than one Short** when a
substantively new editorial angle, narration, and/or visual treatment produces
a different output. A previously published or manually deleted video is not
permission to reupload the identical video. Use a fresh unique slug for each
distinct take. Do not reupload the exact same narration + visual plan under
another filename; the uploader also compares final MP4 SHA-256 hashes.
Historical `alreadyCovered` in discovery is advisory context only, not a ban.

### Visual novelty requirement

Plan at least three genuinely different visual treatments. Each relevant source
image may appear at most once; do **not** set `allowReuse: true` in new stories.
Capture distinct product UI, code, demos, screenshots and charts from multiple
credible sources when possible, rather than recycling the same hero image.
Never introduce invented charts or misleading diagrams. Make explanatory
visuals specific to the mechanism in that story; alternate topic-specific
illustration, source media, numerical evidence and reaction cutaways.
Avoid the same pipeline/fanout/network motif in consecutive videos.
A render with too many fallback typography-only scenes may be rejected by
`scripts/check_visual_quality.py` and must be redesigned, not force-published.


Run the orbdev news selection process for `Jyozaa/orbdev-shorts`.

Read `editorial/policy.json`, `editorial/script-review.md`, `editorial/youtube-metadata.md`, `editorial/discovery.json`, `editorial/inbox/latest.json`, `editorial/discovery-worker.md`, `history/covered.json`, and `stories/current.json` first. The scheduled discovery scan searches Major News, Market / Business, Hot / Emerging and Creator Radar every 12 hours. Treat its inbox as a high-recall candidate set, not verified truth. Re-search and verify every selected topic with a primary source before writing.

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

After the final narration is locked, generate and review YouTube metadata using `editorial/youtube-metadata.md`. Every newly queued production story must include `publish.metadataVersion: 1`, an optimized `youtubeTitle`, concise `description`, 4-15 metadata `tags`, 3-5 visible `hashtags`, `privacyStatus: "public"`, `madeForKids: false`, and a compact `publish.metadataReview` object. Metadata must score at least 8.0 overall with no review dimension below 7.0 before the story may be queued.

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

Orbdev is now **diagram-first for explanation, source-first for evidence**.

1. When showing *what actually happened*, use a relevant official/source image, UI, demo, product, person, hardware view, chart or research figure.
2. When explaining *how or why it works*, default to a clean `drawn-diagram`. The narration explains; the diagram visualizes.
3. Use source media plus small highlights/branding when the source itself contains the mechanism worth pointing at.
4. Use metrics/charts when the number is the story.
5. Use kinetic typography only as brief punctuation for a hook, reaction or punchline. It must not carry paragraphs of explanation.
6. Standalone logos are rare and only for an actual brand reveal.

For a typical technical 25-40 second Short, aim roughly for **35-50% drawn-diagram windows**, **20-40% source/media windows when credible media exists**, **10-20% meme/reaction moments layered over or cutting away from those visuals**, and **no more than about 15% typography-led windows**. These ranges are editorial targets, not quotas: never invent a diagram or use irrelevant media to hit a number.

Do not put the narration on screen. Large text is not a substitute for a visual explanation. Diagram annotations should normally be **one or two words**, with three words as a hard maximum. Capture several distinct source assets rather than repeating one hero image.

## Source imagery and safe framing

Every source visual needs a semantic `query`; named products/games/features need `mustMatch`.

```json
{"type":"source","sourceIndex":0,"query":"Marvel Wolverine gameplay PS5","mustMatch":["wolverine"]}
{"type":"source","sourceIndex":0,"query":"QSSR sharper detail comparison PS5","mustMatch":["qssr"]}
```

Do not force destructive 9:16 crops. The renderer uses asset dimensions and preserves the full meaningful image over a blurred/darkened background. Text, faces, logos and UI near the edge must remain visible.

Reject weak source matches instead of showing the wrong image.

## Explanatory animation

Use the new `drawn-diagram` grammar for normal technical explanation. The semantic families are `branch/orbit/flow/growth/stack/comparison/timeline/wave/shield/funnel/mesh`; choose the family from meaning, not visual novelty alone.

```json
{"type":"drawn-diagram","kind":"branch","labels":["ROUTER","EXPERTS","OUTPUT"]}
{"type":"drawn-diagram","kind":"shield","labels":["SANDBOX"]}
{"type":"drawn-diagram","kind":"orbit","labels":["AGENT","TOOLS","MEMORY","FILES"]}
{"type":"drawn-diagram","kind":"growth","labels":["BEFORE","AFTER"]}
```

Do not manually add `continuityKey`, `continuityIn` or `continuityOut`; render preparation assigns continuity when adjacent semantic diagrams should morph. Prefer these diagrams over legacy `explain`, `flow`, `diagram`, `network`, and text-card treatments in newly authored stories.

Different `drawn-diagram` families may be consecutive **when they are one evolving explanation**. The renderer persists anchor particles and morphs topology across the scene boundary. Choose a changing family because the idea changes, not merely to animate something. Do not chain the same family repeatedly and do not connect unrelated ideas just to create motion.

## Editing rhythm

Main visual holds are usually about 1.5-3.1 seconds, but timing follows meaning rather than a metronome. A useful source image can breathe; a punchline may receive several very quick overlay events.

The first five seconds deserve disproportionate visual effort: relevant real media immediately, a clear hook, motion, and ideally one amusing turn.

Avoid large unused black areas. Prefer layered compositions and foreground/background depth.

## Memes and reactions

**Context is more important than meme density.** A meme should feel like the exact reaction to the words being spoken, not merely a generic surprised/deadpan image that happens to fit the tone.

For a normal Orbdev Short, set `editorial.memeMode` to `"normal"` or omit it. Plan roughly **3-6 genuine meme opportunities when the narration naturally supports them**, but never invent a reaction beat or use a weak meme just to hit a count. It is acceptable for the finished edit to contain fewer memes when the approved local catalog has no contextually correct asset.

Every explicit `memeIntent.concepts` must describe the **specific meaning of that narration line**. Prefer concrete concepts such as `["price","cost"]`, `["rejection","not smaller"]`, `["confusion","contradiction"]`, `["large number","surprise"]`, `["smart","efficient"]`, `["failure","hallucination"]`, or `["waiting","slow"]`. Do not use only generic concepts such as `["reaction","deadpan","emphasis"]`; those do not tell the selector what the meme should mean.

Use `editorial.memeMode: "restrained"` only when meme-heavy treatment would be inappropriate, such as deaths, severe physical harm, disasters, war victims, abuse, or similarly sensitive human suffering. Restrained mode may use 0-2 tasteful reaction moments. A cybersecurity breach, product failure, corporate mistake, benchmark surprise, technical limitation, or business story is **not automatically restrained**; reactions can target the system, attacker, company decision, or technical absurdity without mocking affected people.

Memes are punctuation, not wallpaper. Attach them to `joke`, `analogy`, `reaction`, `punchline`, and `callback` beats, or to a factual beat whose wording creates a genuine reaction opportunity. Prefer visible image/video reactions over audio-only cues when the contextual match is strong. The deterministic selector is allowed to skip a requested meme if no approved asset matches the narration context.

Silent meme images/videos are unboxed overlays: no card, border, or frame. Short video cutaways with useful audio may briefly interrupt narration when the gag warrants it. Spread strong meme moments across the Short instead of clustering them, but do not force placements in the first five seconds or ending when the narration does not support one.

Do not automatically meme structural phrases like "here's the catch" or ordinary factual transitions. Before adding `memeIntent`, ask: **what exact reaction should a viewer have to this sentence?** If that answer is vague, omit the meme intent.

## Narration rendering

Kokoro-82M is primary. Write punctuation for natural breathing and emphasis. The target is energetic but human; do not compensate for weak writing by unnaturally speeding up the voice or pitch shifting it.

Process every independently qualifying topic from the scan, not only the single highest-scoring topic. One creator roundup may therefore produce several separate Shorts. Do not force representation from an empty/weak lane. For each accepted topic, create a separate story JSON and report headline, lane(s), final score and primary source. If nothing qualifies, make no story changes.


## Authored-chaos checklist

Before committing a story, audit the first 5 seconds and every humor beat:

- Do not rely on a fixed cut-every-two-seconds rhythm. Keep the base visual readable, then create energy with quick meme/reaction overlays, highlights, zooms and sound punctuation.
- Prefer a real screenshot/demo/photo when grounding a factual claim; prefer a drawn diagram when explaining a mechanism. Logos should usually be a small layer, not the whole frame.
- Audit text density: if a visual needs more than a few large words to make sense, redesign it as a diagram, source highlight or metric.
- For each `joke`, `analogy`, `reaction`, `punchline` or `callback`, ask what the visual punchline is. If a meme is appropriate, give it an explicit `memeIntent`.
- In a normal 35-40 second story, plan 4-6 explicit meme/reaction moments, with at least three explicitly preferring image/video media. Use restrained mode only for genuinely sensitive human-suffering topics.
- Make callbacks intentional: reuse a phrase, premise, visual concept or reaction category near the ending instead of treating every beat as unrelated.
- Do not crop screenshots or source art for vertical framing. The foreground is always contained inside the subtitle-safe region; visual energy comes from blurred background fill, motion, layered labels and overlays.
- Keep technical trust intact: jokes can be aggressive, but facts, quotes, benchmark attribution and limitations must remain accurate.


## Pacing target

Aim for a compressed broadcast cadence rather than a conventional explainer cadence. Narration should generally land around 165-180 effective WPM when the wording remains intelligible. Natural articulation, complete consonants, and better sentence rhythm matter more than maximum speed. Write shorter clauses and remove filler instead of relying on TTS acceleration.

Visual pacing follows editorial meaning:
- factual/source visuals usually hold around 1.1-2.5 seconds;
- jokes, reactions, analogies, punchlines and callbacks should normally get their own visual beat;
- the first five seconds should change major visual ideas roughly every 0.9-1.6 seconds when readable;
- use sub-second meme/reaction overlays for extra energy rather than making every source image unreadably brief;
- long source visuals may remain on screen if overlays, zooms, highlights or reaction events create internal motion.


## Metricool performance feedback

At the start of each scheduled editorial pass, when the connected Metricool account is available, inspect recent Orbdev YouTube performance according to `editorial/youtube-metadata.md`.

Use Metricool only as a soft feedback signal. If fewer than 5 videos have usable per-video analytics, do not make performance-driven editorial changes. At 5-9 videos, use only weak qualitative observations. At 10+ videos, repeated patterns may softly influence title style, hook style, topic priority, and preferred duration.

Metricool must never lower factual/editorial thresholds, suppress a discovery lane based on a small sample, or delay publication. Uploads still happen as soon as the post-discovery editorial and render pipeline finishes.

## Discovery batch behavior

The scan is not a posting calendar. There are no fixed upload slots.

Every 12 hours:
1. inspect all four discovery lanes;
2. cluster duplicates across lanes;
3. use creator/community convergence as a heat signal;
4. independently verify candidate facts;
5. publish/render every topic that still clears the editorial threshold.

Aim to find at least one worthwhile topic from each lane, but this is a soft discovery goal only. A lane with no strong topic contributes zero stories.

Major News must also cover high-signal mathematics and cybersecurity developments, not only AI/product releases. Explicitly consider new theorem/proof results, conjecture resolutions, theoretical-CS/algorithmic breakthroughs, cryptography results, confirmed breaches, data/credential leaks, ransomware, zero-days, supply-chain attacks and major cyber incidents. For cyber stories, separate confirmed facts from attacker claims and speculative attribution.

Market / Business covers material developments involving AI companies, Big Tech and major consulting firms. Look for earnings/guidance, revenue and demand shifts, AI/cloud/data-centre/chip capex, acquisitions/mergers, IPOs, significant financing/valuation events, major contracts, and consequential restructuring or strategy. A stock move alone is not a story: identify and verify the catalyst. Routine corporate PR should still be rejected.

Hot / Emerging topics should include niche technical developments, not only mainstream AI headlines. Explicitly consider fast-growing GitHub projects, open-source models, developer tools, coding agents, CLIs, runtimes, MCP tooling, local-AI projects, Hacker News momentum and Hugging Face momentum.

Creator Radar videos must be decomposed at topic level. A 30-minute roundup can generate multiple Shorts if several topics independently qualify. Never publish one generic recap merely because the topics came from the same creator upload.

When the same topic appears in Major News, Market / Business, Hot / Emerging and/or Creator Radar, merge it into one story candidate and record the convergence as heat.

## Domain-specific verification

For mathematical/scientific findings:
- verify the actual paper/preprint/journal or authoritative institutional source;
- distinguish a proved theorem/result from a conjecture, numerical experiment, preprint claim or informal announcement;
- do not oversell significance beyond what the result establishes;
- explain the result accurately enough that simplification does not change its meaning.

For cybersecurity incidents:
- distinguish confirmed compromise from suspected intrusion and attacker claims;
- verify affected systems/data, timeline, exploit/CVE details, and remediation when known;
- avoid speculative attribution;
- confirmed data/credential leaks are valid stories, while unconfirmed leak rumours are not.

For Market / Business:
- identify the concrete catalyst behind the headline;
- prefer filings, investor-relations releases and official company statements whenever a public primary source exists;
- when no public primary document exists, use the narrow policy exception: require either two independent high-quality financial sources or one top-tier source such as Reuters, Bloomberg, Financial Times or The Wall Street Journal with direct sourcing/attribution;
- distinguish completed M&A/financing from negotiations or reported talks, and say "reported", "in talks", "plans", or similar when confirmation is incomplete;
- do not turn ordinary stock-price movement into a story without a verified underlying event;
- explain why the business event matters to AI/tech/consulting rather than merely quoting percentages.

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

## Editorial roles and continuous narration

Keep assigning `fact`, `setup`, `explanation`, `analogy`, `joke`, `reaction`, `punchline`, `callback`, and `transition` when useful, but these roles no longer create separate TTS recordings.

Production narration is synthesized as one continuous Michael performance. Roles are metadata for visual rhythm, memes, callbacks, and story structure. Audible pacing should come from normal spoken punctuation and sentence construction.

Write punctuation for how a person would actually say the line. Do not add punctuation merely to manufacture TTS pauses, and do not compensate for weak writing by making every beat dramatic.


## YouTube metadata pass

After script approval and factual re-check, but before queueing, follow `editorial/youtube-metadata.md`.

Generate:
- one accurate, compelling 20-100 character YouTube title;
- a concise 1-3 sentence description;
- 4-15 focused metadata tags;
- 3-5 visible hashtags;
- public privacy and not-made-for-kids settings;
- compact metadata-review scores.

Do not put hashtags in the title. Do not keyword-stuff the description. The uploader automatically appends missing primary-source URLs and the hashtag line to the final description.

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


## Continuous-speech authoring

Visual beats and spoken delivery are intentionally decoupled. The production narrator receives the complete narration as one continuous Kokoro synthesis pass.

Do not design narration around TTS chunks. A sentence such as “A router sends each token through six specialists. The rest stays inactive.” should be written exactly as it should be spoken; the renderer will not split those clauses into independent voice recordings because their visual beats differ.

The production target is roughly 172 effective WPM, but complete consonants, natural sentence endings, and intelligibility take priority over hitting an exact number.

Use punctuation as a real speaker would:
- periods and questions for genuine sentence boundaries;
- commas for natural clauses;
- colons or dashes only when the spoken setup genuinely calls for them;
- avoid ellipses unless hesitation is actually intended.

Editorial roles remain useful for visuals and meme timing, but they must not be used as instructions to chop the narration audio.
