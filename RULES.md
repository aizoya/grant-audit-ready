# Muse Ember Hackathon — RULES.md (dated 2026-11-24)

Status: Franklyn applied 2026-11-24; approval PENDING. No credits issued yet.

## Verified (official event page, https://cerebralvalley.ai/e/muse-ember-hackathon)
- Virtual, solo only, US residents 18+, max 1,000 selected, rolling review.
- $10 Meta Model API credits per selected participant; every project must run on Muse Ember via Meta Model API.
- Build window opens Nov 23, 9:00 AM ET. Submissions due Dec 2, 9:00 PM ET. Judging Dec 3-6. Winners Dec 7.
- Prize pool $5,000; categories "announced before kickoff" (not yet seen).
- Selected participants complete a short pre- and post-hackathon survey.
- Cookbook: https://dev.meta.ai/docs/cookbook/muse-ember (only shows planner+executor examples: Python->Rust port, photo sorting).

## Conflicts / unknowns (send to organizer only with Franklyn's OK)
1. Application close: page says Nov 25 12:00 PM ET; Franklyn's pasted copy said Nov 30. Franklyn also said contest runs to Dec 10 vs page Dec 2 submission. Plan to Dec 2 until Official Rules say otherwise.
2. Waiver page did not load; Official Rules not published/seen. IP, AI-use disclosure, credit-use rules UNKNOWN.
3. Judges, prize categories, submission format (video length? repo? live link?) UNKNOWN.
4. Is a non-Ember planner allowed at runtime? Page says "All in on Muse Ember" -> assume Ember-only at runtime.
5. RESOLVED 2026-11-24 from https://dev.meta.ai/docs/pricing-rate-limits: <=200K input $0.10/$0.50, cached $0.004; >200K whole request $0.30/$1.50, cached $0.012. (OpenRouter's $4/$20 is wrong for Ember.)
6. RESOLVED: implicit prefix caching exists on Meta's API (docs/prompt-caching); TTL and minimum size not stated. STILL UNKNOWN: whether the $10 credit hard-stops or can go negative (docs silent) - our ledger enforces $9 stop.

## Budget math (list price, third-party sources; confirm on Meta)
- $0.10/M input, $0.50/M output, ~$0.004/M cached input.
- $10 = ~100M input tokens or ~20M output tokens. One full 1M-context uncached call = ~$0.10.
