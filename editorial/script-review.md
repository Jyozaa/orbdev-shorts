# Orbdev script review gate

This file defines the mandatory editorial passes that happen after a topic qualifies and before any visual planning or queue commit.

The purpose is to separate writing from editing. A first draft is never assumed to be publishable.

## Pass 1 — Writer

Write one narration draft from the verified research.

Requirements:
- 80-105 words unless policy.json changes the target.
- Build around one central technical idea or contradiction.
- Make the first sentence concrete enough that a viewer immediately understands why the development is interesting.
- Explain what changed, how the important mechanism works, why it matters in practice, and the material limitation/caveat.
- Prefer implication over feature enumeration.
- Humor should emerge from the technical situation rather than being appended to a dry paragraph.
- Do not choose visuals, memes, SFX, beat boundaries, or on-screen copy yet.

The writer may use verified research notes, but should not simply compress a press release, model card, benchmark table, changelog, or creator transcript.

## Pass 2 — Critic

Now act as a skeptical script editor. Evaluate the narration alone, with no credit for future visuals, memes, captions, music, or editing.

Score each dimension from 0-10:

1. Hook
   - Is the first sentence specific and interesting?
   - Does it expose the real technical tension instead of generic hype?

2. Spoken naturalness
   - Does this sound like a person explaining something aloud?
   - Are sentence lengths varied?
   - Are there stiff written phrases, synthetic transitions, or awkward clauses?

3. Explanation clarity
   - Can a technically curious viewer understand what changed and how it works?
   - Are important terms explained through consequence rather than jargon stacking?

4. Information selection
   - Does every retained fact serve the central idea?
   - Are there unnecessary specs, numbers, product bullets, or side facts?

5. Humor / editorial voice
   - Is the dry/playful observation earned by the facts?
   - Does humor feel integrated rather than bolted on?
   - Avoid copying any creator's wording, catchphrases, or persona.

6. Caveat / practical implication
   - Does the script clearly state the important limitation, tradeoff, access constraint, price, hardware requirement, or uncertainty when material?
   - Does the viewer understand why the headline matters in practice?

7. Payoff
   - Does the ending resolve or sharpen the opening premise?
   - Is it concise enough to feel like an ending rather than another fact?

8. Factual discipline
   - Are claims attributed correctly?
   - Are comparisons and benchmark statements appropriately qualified?
   - Is the language no stronger than the verified evidence?

## Passing threshold

A draft passes only when:
- average score is at least 8.0/10;
- no dimension is below 7.0/10;
- factual discipline is at least 8.0/10.

Do not inflate scores to avoid rewriting.

If the draft fails, identify the 2-4 most important weaknesses and perform Pass 3. Do not merely patch individual words if the structure is weak.

## Pass 3 — Rewriter

Rewrite the narration from scratch or substantially restructure it using the critic's findings.

Rules:
- Preserve verified facts, not the draft's phrasing.
- Remove low-value details before adding new words.
- Strengthen the central angle rather than adding more jokes.
- Replace generic transitions with direct cause/effect or contrast.
- Keep the script natural for the Orbdev deadpan narrator.
- Do not copy creator wording even when Creator Radar inspired the angle.

Run the critic rubric again after the rewrite.

The worker may perform up to three writer/editor iterations. If the script still cannot pass honestly after three attempts, reject the topic for this batch rather than queue weak copy.

## Pass 4 — Factual re-check

After the script passes the quality rubric, compare every material claim in the final narration against the primary source(s) again.

Specifically re-check:
- numbers and units;
- model/product/version names;
- benchmark attribution;
- release/access/licensing claims;
- price or hardware requirements;
- comparisons;
- caveats and limitations;
- any joke or analogy that implies a factual claim.

If a correction changes the meaning or rhythm of the script, run the critic once more on the corrected narration.

## Pass 5 — Production structure

Only after the narration passes both script quality and factual re-check:

1. Split the final narration exactly into semantic beats.
2. Assign editorial roles.
3. Plan source visuals, explanatory treatments, metrics, memes and SFX.
4. Validate the complete story JSON.
5. Queue the story.

Visual quality must never be used to justify a script that failed the narration-only review.

## Audit metadata

For newly queued stories, add a compact `editorial.scriptReview` object when practical:

```json
{
  "iterations": 2,
  "average": 8.5,
  "scores": {
    "hook": 9,
    "spokenNaturalness": 8,
    "explanationClarity": 9,
    "informationSelection": 8,
    "humorVoice": 8,
    "caveatPracticalImplication": 9,
    "payoff": 8,
    "factualDiscipline": 9
  }
}
```

Do not store chain-of-thought, private reasoning, or long critique text in the repository. Store only the compact scores and iteration count.
