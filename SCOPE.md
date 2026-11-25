# SCOPE.md — DRAFT v1 (2026-11-24). Pending Franklyn's approval of niche + data download.

Working name: (none yet). Runtime module: `ember_ledger` (reusable across AIZOYA products).

## Problem (global-first framing)
Organizations that spend public/donor grant money must prove it was spent and reported correctly. Community grantees and the CPAs who serve them find errors late, in audit, when fixes are costly. US first (federal grants $848B in 2025, per OMB via Yale SOM paper); the same pattern exists for donor-funded programs worldwide (assumption - not yet sourced).

## One user, one workflow
User: a finance lead at a nonprofit or local government (or their CPA) preparing for a Single Audit.
Workflow: upload draft SEFA + financial statements + prior-year audit report (PDFs) -> get an evidence-linked readiness report (each finding quotes the source page; code verifies the quote) + a cost line (cents per report).

## Definition of done (acceptance tests)
1. Quote integrity: 100% of findings shown to the user carry >=1 verified quote (unverified findings are dropped and counted).
2. Deterministic checks (threshold, due date, SEFA arithmetic) have unit tests (done: 22 passing) and run without any model call.
3. Detection eval on synthetic injected errors in REAL public audit PDFs, per category (arithmetic mismatch, wrong award number/ALN, threshold misapplied, date errors, prior-finding omitted). Report recall and false-positive counts honestly, per category, on a HELD-OUT split never used for prompt tuning. If a held-out doc fails: report, do not patch.
4. Clean-document check: run on unmodified real reports; a human (and one independent reviewer) labels a sample of 20 flags as true/false/needs-review.
5. Cost: median and p95 cost per report from real usage fields; total spend under $9 hard stop; ablation table: (a) default max effort, no batching, vs (b) tuned (minimal/low effort, stable cached prefix, <=200K requests).
6. Clean end-to-end run on the final demo machine; 3-minute video; README with the cost report; working link (only after deployment approval).

## Non-goals
Audit opinions or legal advice; naming/accusing real organizations (real findings are never republished as accusations; only injected synthetic errors are scored); private data; payments; accounts; multi-tenant; auto-sending anything.

## Data plan (open data only)
- FAC single audit data: free, public domain (fac.gov/data). Use: realistic document structure + findings text distributions. Tribal-exempt items excluded (non-public by rule).
- 2 CFR 200 text (US government work) -> the cached rules prefix.
- NOT using Kensho FIND until its Terms of Usage are read and permit it.
- Shell cannot reach fac.gov (proxy policy). Route: Franklyn's home Mac, after approval, for limited samples only.

## Model plan
Runtime: Ember only (muse-ember-1.0, Responses API), deterministic code orchestrator (no larger planner model). Requests <=200K input; stable prefix first; effort set per step (minimal for extraction, low for cross-checks); structured output with strict JSON schema; ledger preflight on every call.

## Budget plan (list prices; ~$10 total, $9 hard stop)
- ~$0.50 live probe: confirm endpoint, usage fields, caching, effort behavior.
- ~$1.50 prompt development on ~10 dev docs.
- ~$4.00 held-out eval (50 docs x 2 configs for the ablation).
- ~$2.00 reserve + demo recording runs.
(Per-report cost unknown until probe; planning assumption only.)

## Timeline (to Dec 2, 9 PM ET = 6 PM PT; extra days only if rules confirm Dec 10)
Today-Nov 26: data sample, injection harness, schemas (no spend). Nov 26-28: probe + prompt dev. Nov 28-30: held-out eval + UI. Dec 1: video, README, clean run. Dec 2: Franklyn submits.

## Approvals needed (batch)
1. Niche + scope. 2. Download sample of public FAC files via home Mac. 3. Repo name (after I check existing aizoya repos). 4. Later: first live spend, deployment, submission.
