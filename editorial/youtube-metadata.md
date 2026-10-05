# Orbdev YouTube metadata contract

This file defines the production metadata and performance-feedback rules for every newly queued Orbdev Short.

## Ownership

The scheduled GPT editorial worker owns metadata generation.

Metadata is created only after:
1. the story has passed research and factual verification;
2. the narration has passed the script-review gate;
3. the final narration has passed the factual re-check.

Do not optimize metadata before the story angle is stable.

## Required publish object

Every newly queued production story must set:

```json
{
  "publish": {
    "metadataVersion": 1,
    "youtubeTitle": "...",
    "description": "...",
    "tags": ["..."],
    "hashtags": ["#...", "#...", "#..."],
    "category": "SCIENCE_TECHNOLOGY",
    "madeForKids": false,
    "privacyStatus": "public",
    "metadataReview": {
      "score": 8.5,
      "hookAccuracy": 9,
      "searchClarity": 8,
      "descriptionQuality": 9,
      "hashtagRelevance": 8
    }
  }
}
```

The uploader automatically appends missing primary-source URLs and the visible hashtag line to the final YouTube description.

## Title rules

The title must be:
- 20-100 characters;
- factually accurate and supported by the final script/sources;
- understandable without seeing the thumbnail or description;
- built around the actual development, consequence, contradiction, or verified catalyst;
- specific enough to distinguish this story from generic AI/tech news.

Prefer:
- a concrete surprising fact;
- a clear consequence;
- a strong comparison when the comparison is verified;
- the most recognizable entity when it materially helps comprehension/search.

Avoid:
- keyword stuffing;
- all-caps clickbait;
- fake urgency;
- unsupported superlatives;
- generic phrases such as "This Changes Everything";
- repeating the same title construction across consecutive uploads;
- putting hashtags in the title.

The title may be punchy, but must not promise something stronger than the video proves.

## Description rules

Write a concise 1-3 sentence description that:
- states what happened;
- adds the most useful context not obvious from the title;
- remains accurate if viewed out of context;
- does not repeat the full narration;
- does not contain filler calls-to-action by default.

Do not manually paste the Sources block if the uploader can append it from `editorial.sources`.

Target the human reader first. Search keywords should appear naturally rather than as a keyword list.

## YouTube metadata tags

Use 4-15 focused metadata tags.

Include, when relevant:
- canonical company/project/person/product name;
- technology/model/tool name;
- broader category such as AI, cybersecurity, mathematics, cloud computing, semiconductors, or consulting;
- one or two specific concept tags such as mixture of experts, zero day, ransomware, theorem proof, GPU, earnings.

Avoid irrelevant trending terms and near-duplicate singular/plural spam.

## Visible hashtags

Use 3-5 visible hashtags.

Rules:
- each begins with `#`;
- no spaces;
- prefer broad discoverability plus one story-specific term;
- every hashtag must genuinely describe the video;
- do not use `#Shorts` automatically unless performance evidence later shows a real benefit;
- do not repeat a hashtag merely because it was used on previous videos.

Typical mix:
- one broad category, e.g. `#AI`, `#Cybersecurity`, `#Technology`;
- one domain/entity tag, e.g. `#NVIDIA`, `#OpenSource`, `#Mathematics`;
- one specific topic tag, e.g. `#Ransomware`, `#LLM`, `#ZeroDay`.

## Metadata critic

Score the final metadata from 0-10 on:

1. Hook accuracy
   - Does the title accurately express the strongest verified angle?
   - Is there any clickbait gap between title and video?

2. Search clarity
   - Can a viewer/search engine identify the entity/topic immediately?
   - Are the title and tags specific rather than generic?

3. Description quality
   - Is the description concise, useful, and non-repetitive?
   - Does it add context without becoming a keyword dump?

4. Hashtag relevance
   - Are all 3-5 hashtags genuinely relevant?
   - Is the set broad enough for discovery without being spammy?

The metadata passes only when:
- overall score >= 8.0;
- every dimension >= 7.0.

Rewrite metadata until it passes. Do not change the script merely to rescue metadata.

## Metricool performance feedback

Metricool is a feedback layer, not the publisher and not a scheduling gate.

Connected Orbdev Metricool brand:
- brand ID: `7214999`
- timezone: `Europe/London`
- network: YouTube

At the beginning of each scheduled editorial run, when the connector is available, inspect recent YouTube performance for approximately the last 30 days.

Useful per-video fields include:
- title;
- publication date/time;
- views;
- average view duration;
- watch minutes;
- likes;
- comments;
- shares.

Useful channel-level fields include:
- video views;
- subscribers;
- subscribers gained/lost.

### Minimum sample rule

If fewer than 5 Orbdev videos have usable per-video performance data, treat Metricool as informational only and make no performance-driven editorial changes.

At 5-9 usable videos:
- allow only weak qualitative observations;
- never change hard thresholds or discovery coverage.

At 10+ usable videos:
- use repeated patterns as a soft signal for title wording, hook style, topic prioritization, and preferred duration range.

Never infer a trend from one viral or failed video.

## Allowed performance adaptations

Metricool may softly influence:
- which otherwise-qualified topics are prioritized;
- whether concrete-number vs entity-first vs consequence-first titles have recently worked better;
- whether very short or longer scripts appear to retain viewers better;
- which topic families appear to earn stronger engagement;
- whether a recurring title pattern is underperforming.

Metricool must not:
- override factual/editorial thresholds;
- cause a weak story to be published;
- suppress an entire discovery lane from a small sample;
- copy a previous successful title verbatim;
- delay publication to a "best time" slot.

Orbdev publishes as soon as the post-discovery editorial/render pipeline finishes. Performance feedback changes future content decisions, not upload timing.

## Audit

For newly queued stories, store only the compact `publish.metadataReview` score object.

Do not store hidden reasoning, long critique text, or raw Metricool analytics inside story JSON.
