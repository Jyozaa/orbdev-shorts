# Orbdev editorial worker

Run the orbdev news selection process for `Jyozaa/orbdev-shorts`.

Read `editorial/policy.json`, `history/covered.json`, and `stories/current.json` first. Search current public sources for significant AI/developer-technology developments inside the configured lookback window and verify every selected story with a primary source.

## Narration

Write spoken editorial copy, not a press-release summary. Use a concrete hook, explain what changed technically, show why it matters, then give the catch/limitation and a concise implication or punchline. Keep it conversational, precise and dry/playful. Aim for 75-105 words.

Write narration first, then split it exactly into 12-22 semantic beats. Beat text must reproduce narration word-for-word. Do not manually time beats.

## Visual-director rule

For every beat, ask: **what relationship should the viewer understand without the narration?**

Prefer visual explanations over labelled boxes. Use `explain` for relationships:

```json
{"type":"explain","mode":"pixel-upscale","labels":["LOW RES","UPSCALED"]}
{"type":"explain","mode":"network-shrink","fromLayers":[5,4,4,3],"toLayers":[3,3,2],"labels":["LARGE NETWORK","SMALLER NETWORK"]}
{"type":"explain","mode":"capacity","load":98,"labels":["GPU"]}
{"type":"explain","mode":"stability","labels":["SHIMMER","STABLE"]}
{"type":"explain","mode":"pipeline","stages":["IMAGE","QSSR","PS5","4K"]}
{"type":"explain","mode":"fanout","center":"MODEL","nodes":["CODE","WEB","FILES","TOOLS"]}
```

These animations build the explanation over time and use most of the frame. In a technical 25-40s Short, include at least two genuine `explain` beats when the story supports them.

Generic `flow`, `diagram`, and `network` are fallbacks, not defaults. Do not turn nouns into rounded boxes just because it is easy.

## Source imagery

Use official imagery only when it is semantically relevant to that exact beat. Every source visual MUST include a query describing the image you actually want:

```json
{"type":"source","sourceIndex":0,"query":"Marvel Wolverine gameplay","mustMatch":["wolverine"],"fit":"cover"}
{"type":"source","sourceIndex":0,"query":"PSSR image quality comparison","mustMatch":["pssr"],"fit":"contain","annotations":[
  {"label":"fine detail","x":72,"y":36}
]}
```

The source pipeline ranks article images using asset-local alt text, nearby page context, URL text, and the query. For named games/products/features, add `mustMatch` with the identifying term(s). Every required term must exist in the asset's own metadata or URL. Source assets are not reused across unrelated beats unless `allowReuse:true` is explicitly justified. If no candidate passes, reject the image and let an explanatory visual win. Never request generic queries such as "article image" or "PS5 news".

Use real imagery for recognizable products, demos, UI, games, hardware and research figures. A good explanatory animation is better than an irrelevant source image.

## Composition and motion

- Use most of the usable frame; avoid tiny diagrams floating in black space.
- Animation must explain construction/transformation, not merely fade a finished diagram in.
- Mix camera-scale/pan motion with object motion.
- Logos can participate inside explanations rather than requiring a separate logo scene.
- Charts/timelines/comparisons remain useful where they actually fit.
- Avoid the same treatment family consecutively when alternatives exist.
- Keep generic flow/diagram treatments below ~25%.

## Memes

Target 3-4 meme/reaction moments when natural.

Automatic reaction cues are for genuine reaction language such as:
- "the headline sounds wild"
- "this is wild"
- "kind of insane"
- "this gets weird"
- "sounds great"

Do NOT automatically meme structural transitions such as "here's the catch". Those should normally use editorial SFX (for example scratch) unless the script explicitly describes a reaction.

Silent image/video memes are overlays only: no border, no card, narration continues. A full-screen cutaway requires a short video meme with useful audio. Short audio reactions must finish naturally.

The renderer groups semantic beats into ~1.8-3.35s visual windows, choosing the strongest and most varied visual rather than blindly preferring source images.

After queueing a story, report only headline, score and primary source. If nothing qualifies, make no repository changes.
