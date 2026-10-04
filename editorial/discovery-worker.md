# Orbdev discovery and editorial handoff

The repository runs a discovery scan every 12 hours. Discovery is intentionally separated from factual verification and story writing.

## Discovery lanes

### Major News
Searches for significant technical announcements across frontier AI labs, developer platforms, robotics, hardware, research, infrastructure and graphics.

### Hot / Emerging
Actively hunts for developer-interest signals that normal press search can miss:
- fast-growing GitHub repositories, including GitHub Trending even when the repository itself is older
- new open-source developer tools and coding agents
- Hacker News momentum
- trending Hugging Face models
- infrastructure, runtimes, libraries, MCP tooling and local-AI projects

For this lane, momentum age matters more than creation age. The scan combines newly-created repository searches with daily/weekly GitHub Trending signals, so an older project that suddenly explodes today can still be fresh. Low-star repositories do not qualify merely because they are new: standalone GitHub/Hugging Face/Hacker News candidates must clear evidence-quality gates unless independent lanes converge on the same topic.

### Creator Radar
Scans the configured Creator Radar channels and decomposes long roundup videos into separate candidate topics when chapters or transcript transitions allow it.

Creators are discovery and interpretation signals, never factual authority. Their commentary can suggest:
- why a topic matters
- comparisons worth checking
- pricing/access questions
- caveats
- developer usefulness
- unusual research findings

Every factual claim must still be traced to a primary source before publication.

## Lane diversity is soft, never forced

The system should try to find at least one worthwhile topic from each lane on every scan, but it must never lower the quality threshold to satisfy a lane quota.

A scan may legitimately produce:
- zero stories
- one story
- many stories

There is no fixed daily publishing cap. Each independently qualifying topic may become its own Short.

## Creator roundup decomposition

One creator upload can produce many Orbdev candidates. Treat meaningful topics independently, then deduplicate them against the other discovery lanes.

Example:

creator roundup
-> topic A
-> topic B
-> topic C
-> topic D

Each topic receives its own score and verification pass. A weak topic is skipped even if another topic from the same video qualifies.

## Cross-lane convergence

If the same development appears in multiple lanes, merge the evidence rather than creating duplicate Shorts.

Cross-lane convergence is a heat signal, not proof. For example:

GitHub momentum + Hacker News + Fireship + Matt Wolfe

should raise editorial priority, but primary-source verification is still mandatory.

## Editorial handoff

The scheduled scan writes `editorial/inbox/latest.json`.

For each candidate marked `qualifiesForEditorial`:

1. Determine whether it is genuinely one technical story.
2. Find and read the primary source: official announcement, repository, paper, model page or release notes.
3. Verify all material claims independently from creator commentary.
4. Reject rumours, unsupported benchmark claims and misleading comparisons.
5. Check `history/covered.json` and the current story again.
6. Re-score using the full editorial rubric, including significance, practical impact, novelty, source confidence, visual potential and current heat.
7. If it still clears the threshold, create one story JSON for that topic.
8. Multiple candidates from one scan may all become Shorts.

Never merge several unrelated creator-roundup topics into one generic news recap merely because they came from the same video.


## Scan-state rules

Creator videos are processed once per discovery state. A successful scan records the video ID in `history/discovery-state.json`; later 12-hour scans skip that same upload instead of repeatedly re-segmenting it. New videos are still scanned immediately on the next run.

Creator channels can set their own segment budget. High-recall roundup channels such as AI Search and Matt Wolfe are allowed more topic segments than single-topic channels, so one long roundup can legitimately yield several independent Short candidates.
