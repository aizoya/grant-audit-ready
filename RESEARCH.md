# RESEARCH.md — prior-art map (2026-11-24, first pass; web search only, no GitHub/app-store sweep yet)

## Candidate 1: crisis / disaster report triage -> CROWDED
Devpost: Faraja (open-source, photo AI classification, PWA offline), SentraAI (voice -> ElevenLabs + DeepL), INKINGI Rescue (Rwanda, multilingual, scoring). GitHub: gemma3n-disaster-assistant (offline, CV + voice). Research: REACT AI (Japan EOCs), Kaicedra/UNICEF voice reporting in Mali.
Verdict: many builds of the same pattern. Not open.

## Candidate 2: plain-language benefits/letter explainer -> CROWDED (consumer side)
Apps: ExplainThis AI Letter Decoder, Explicame. Public sector: USDR + New Jersey UI translation assistants, Indiana DWD tool, Code for America, SUMM AI (EU).
Verdict: consumer explainers are everywhere. Open gap would be agency-side or verification, not another explainer.

## Candidate 3: long-document inconsistency audit -> CROWDED commercially, one open niche
Commercial: Ironclad (retrieve-then-verify, claims 3-4x lower cost than whole-contract reading), Harvey, Spellbook. Hackathon: OpticLoan, PaperHawk. Research: Kensho FIND benchmark (ACL 2026; best model gpt-5 recovered 64% of inserted inconsistencies; dataset on Hugging Face kensho/FIND with restrictive Terms of Usage - READ BEFORE USE).
Warning from evidence: long-context accuracy degrades (NoLiMa, cited by Ironclad), so "just stuff 1M tokens in" is a claim to TEST, not assume.

## Emerging gap: grantee-side single-audit / grant-report readiness
Context: federal grants $848B in 2025 (Yale SOM paper citing OMB). Grantees >= $1M federal spend need a Single Audit. HHS announced AI-driven enforcement of single-audit compliance (agency side). Public data source: Federal Audit Clearinghouse (public, machine-readable). Existing: Berkeley capstone complyraAI (research-staff focus), big-firm blog posts (BDO, Armanino). GAO loss estimate $233-521B/yr appears only in sponsored vendor content - treat as unverified.
Open question to test: does anyone sell a cheap, evidence-linked pre-audit checker for nonprofits / local governments / the CPAs who serve them? NOT yet verified - needs app-store, Product Hunt, GitHub sweep.

## Niche sweep results (2026-11-24, web search only; NOT yet done: app stores, Product Hunt, GitHub topic search by stars)
Grantee-side, found:
- Free checklists/templates (MangoApps single-audit readiness templates, Ramp checklist) - static, no document analysis.
- Advisory content on using generic AI prompts for audit prep (Armanino, BDO, Trullion) - guidance, not a product.
- Berkeley MIDS capstone "complyraAI" (research-staff compliance helper) - academic, scope differs.
Agency/oversight-side, found: HHS AI audit enforcement; HRSA "AI Audit Resolution Assistant" (HHS AI use-case inventory; HRSA used public FAC data to evaluate LLM accuracy); GAO internal "FAC Exploration Tool"; GAO-24-106173 documents FAC data quality problems.
Data side, found: FAC data is free and public domain; CSV downloads and a free API (key from Data.gov); 2016-present; 18F "FAC Distiller" (2019 prototype for findings text); community Apify scraper and an "mcp-fac" npm package. FAC publishes audit PDF + SF-SAC form per report.
Read: no found product does "upload your draft SEFA/financials/prior audit -> evidence-linked inconsistency + readiness report at cents per run" for community grantees. Absence in one pass of web search is NOT proof; still must sweep app stores/Product Hunt/GitHub and talk to 2-3 CPAs/nonprofit finance people.

## Meta Model API facts that shape the design (read from dev.meta.ai docs, 2026-11-24)
- Official price muse-ember-1.0: <=200K input tokens: $0.10 in / $0.50 out / $0.004 cached. >200K: $0.30 / $1.50 / $0.012, applied to the WHOLE request (cached tokens count toward the tier). => Keep every request <=200K; a 1M-token stuffing approach triples the price.
- Reasoning effort ranges minimal..max and DEFAULTS TO MAX => cost trap. Per-task effort is a budget lever. Reasoning-token billing not documented (assume billed as output until probed).
- Caching is implicit prefix caching; no minimum stated; no TTL stated; Responses API accepts prompt_cache_retention "24h" (a hint, not a guarantee). Pitfalls: volatile content early in the prompt breaks the prefix; per-user prompt_cache_key lowers hit rate; previous_response_id hides full-prefix accounting.
- Structured output uses constrained decoding (guaranteed schema conformance), works with tool calling; no recursive schemas; depth <=10.
- Rate limits: 3,000 RPM, 4M TPM per team. Docs do not describe credit/spend limits -> our own ledger must hard-stop.
- Ember accepts PDF/image/video/audio; docs say NOT recommended for knowledge-heavy questions => put the rules text in the cached prefix rather than relying on model memory.
- Cookbook shows only two recipes (Python->Rust port, photo organizing) => do not clone.

## Meta cookbook deep read (2026-11-24)
- use-cases page lists 14 recipes (chart analysis, slides, games, GitHub agent, computer use, multi-agent Kanban...). NONE for document audit, compliance, finance or public sector (page itself notes the gap). Agent-patterns page covers the basic loop, context management, search-and-replace edits and an alert-triage copilot; it does NOT cover cost control, budgets, effort levels, retries or escalation.
- photos recipe: unconstrained first run = 11,477 requests, 4.99M output tokens (4.40M reasoning). With 8 photos/request, 512px images and "minimal reasoning effort": 1,269 requests, 0.47M output tokens. => reasoning tokens ARE reported inside output tokens (resolves my open question); effort + batching cut output ~10x.
- python->rust recipe: planner Muse Wonder (56 calls) + Ember workers (1,466 calls, 157.6M input of which 154.0M cached, 0.99M output). My list-price arithmetic for the Ember share: 0.616 (cached) + 0.352 (uncached) + 0.493 (output) = ~$1.46. Meta gives no dollar figure. Cache hit rate ~98% when the prefix is stable.
- Verification discipline worth copying: held-out files never used for tuning; on a held-out failure, report it, do not patch (otherwise it becomes a dev set).
- Default concurrency in Muse Code is 7 subagents; 429s -> fewer workers/backoff.

## Uniqueness gate (draft, unproven)
"Evidence-linked, cost-metered audit-readiness checker for community grantees, built on cached rules + deterministic quote verification, priced in cents per report." Closest alternatives: Ironclad/Harvey (contracts, enterprise price), consumer explainers (no audit rules), agency-side AI (wrong buyer).
