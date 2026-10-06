# Orbdev discovery and editorial handoff

The repository runs a discovery scan every 12 hours. Discovery is intentionally separated from factual verification and story writing.

## Discovery lanes

### Major News
Searches for significant technical and scientific announcements across frontier AI labs, developer platforms, robotics, hardware, infrastructure, mathematics, theoretical computer science, cryptography, cybersecurity and research.

This lane explicitly includes:
- new mathematical theorems, proofs, conjecture resolutions and important algorithmic/theoretical results
- cryptography results with clear technical significance
- confirmed data breaches, credential/data leaks, ransomware, zero-days, supply-chain compromises and major cyberattacks
- high-impact vulnerability disclosures and security incidents

For cyber incidents, separate confirmed facts from attacker claims, rumours and speculative attribution.

### Market / Business
Tracks material business and market developments involving AI companies, Big Tech and major consulting firms.

Examples include:
- earnings, revenue, guidance and AI/cloud demand
- AI/data-centre/chip capex and infrastructure spending
- acquisitions, mergers, IPOs, major financing or valuation events
- material contracts and strategic deals
- major restructuring with a real business/technology consequence
- consulting-firm AI revenue, demand, acquisitions and significant strategic shifts

This lane is not generic stock-market coverage. A share-price move by itself is insufficient. The editorial runner must identify and verify the concrete catalyst behind the move.

Target companies include major AI labs and technology firms such as OpenAI, Anthropic, Alphabet/Google, Microsoft, Meta, Nvidia, Amazon, Apple, Oracle, IBM, AMD, Intel, Broadcom, Salesforce, ServiceNow and Palantir, plus major consultancies including Accenture, Deloitte, PwC, EY, KPMG, McKinsey, BCG, Bain, Capgemini, Cognizant, Infosys and TCS.

### Hot / Emerging
Actively hunts for developer-interest signals that normal press search can miss:
- fast-growing GitHub repositories, including GitHub Trending even when the repository itself is older
- new open-source developer tools and coding agents
- Hacker News momentum
- trending Hugging Face models
- infrastructure, runtimes, libraries, MCP tooling and local-AI projects

For this lane, momentum age matters more than creation age. The scan combines newly-created repository searches with daily/weekly GitHub Trending signals, normalizing weekly stars into an approximate stars-per-day velocity, so an older project that suddenly explodes today can still be fresh. Low-star repositories do not qualify merely because they are new: standalone GitHub/Hugging Face/Hacker News candidates must clear evidence-quality gates unless independent lanes converge on the same topic.

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

When one development appears in multiple lanes, merge its evidence into one
research lead rather than duplicating the candidate. This does **not** prohibit
publishing distinct Shorts on the same topic with genuinely different scripts,
angles, or visual treatments. Block exact reuploads, not shared source URLs.

Cross-lane convergence is a heat signal, not proof. For example:

GitHub momentum + Hacker News + Fireship + Matt Wolfe

should raise editorial priority, but primary-source verification is still mandatory.

## Editorial handoff

The scheduled scan writes `editorial/inbox/latest.json`.

For each candidate marked `qualifiesForEditorial`:

1. Determine whether it is genuinely one coherent technical, scientific, cyber, or market/business story.
2. Find and read the strongest available primary source: official announcement, repository, paper, journal/preprint, security advisory, breach notice, regulatory filing, investor-relations release, model page or release notes.
3. Verify all material claims independently from creator commentary or secondary headlines.
4. Reject rumours, unconfirmed leaks, unsupported benchmark claims and misleading comparisons. Confirmed breach/data-leak incidents are valid when the evidence is solid.
5. Check `history/covered.json` and the current story for identical video plans.
   Prior topical coverage is an editorial novelty signal, not an automatic veto.
   A truly new angle, explanation, or visual story may warrant its own Short.
6. Re-score using the full editorial rubric, including significance, practical impact, novelty, source confidence, visual potential and current heat.
7. If it still clears the threshold, create one story JSON for that topic.
8. Multiple candidates from one scan may all become Shorts.

Never merge several unrelated creator-roundup topics into one generic news recap merely because they came from the same video.


## Scan-state rules

Creator videos are processed once per discovery state. A successful scan records the video ID in `history/discovery-state.json`; later 12-hour scans skip that same upload instead of repeatedly re-segmenting it. New videos are still scanned immediately on the next run.

Creator channels can set their own segment budget. High-recall roundup channels such as AI Search and Matt Wolfe are allowed more topic segments than single-topic channels, so one long roundup can legitimately yield several independent Short candidates.

## Scheduled ChatGPT editorial handoff

GitHub discovery stops after writing `editorial/inbox/latest.json` and `history/discovery-state.json`. It does not call an LLM API and does not dispatch a GitHub editorial workflow.

The scheduled ChatGPT automation is the editorial runner. It executes after the discovery scans, reads the repository files as authoritative instructions, and performs live-web research, primary-source verification, final scoring, multi-pass script review, narration/visual planning, and queue creation.

For Market / Business candidates, use filings, investor-relations releases, official company statements and high-quality financial reporting as appropriate. For private-company financing/valuation stories, distinguish completed transactions from negotiations or reported talks.

The quality gate remains unchanged:
- at least one backed primary source is mandatory;
- base editorial score must be at least 6.0/10 before heat is applied;
- heat/momentum can contribute at most +2, capped at 10 overall;
- the normal publication threshold remains 7.2;
- creator/community convergence is a heat signal, never factual proof.

The ChatGPT automation may queue zero, one, or many independently qualifying stories. A creator roundup may produce multiple separate queue files when several topics independently qualify.

The editorial commit must write accepted stories only to `stories/queue/`. It must **not** add them to `history/covered.json`. The render queue creates success receipts, and only the successful-render finalizer updates covered history. This keeps failed renders retryable.
