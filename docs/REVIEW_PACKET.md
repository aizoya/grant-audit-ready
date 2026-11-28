# Review packet: Grant Audit Ready (Meta Muse Ember Hackathon)

Status: NOT submitted. Nothing here is a claimed win or judge feedback.
Build window ends Dec 2, 6:00 PM PT. Judging Dec 3-6.

## What we are asking reviewers
Grade this project like a judge would, then tell us what is missing. Be blunt. Model agreement is not proof, so check against the official rules and the live app, not against our claims.

Scoring weights (from the participant guide): Impact 30%, Use of Meta AI tooling 25%, Technical depth 20%, Demo 25%.

## Links
- Repo (public): https://github.com/aizoya/grant-audit-ready (branch `claude/scanned-mode`)
- Live: https://grantaudit.aizoya.com (if DNS has not propagated, use the Vercel preview from the repo's latest deployment)
- Judge page: first tab "For judges". Try the app tab runs the real model on synthetic samples.

## What it is
A grantee-side Single Audit readiness checker. The model (`muse-ember-1.0`) extracts values with exact quotes. Deterministic code does the rules, arithmetic and quote verification. A finding without a verified quote is dropped. Every run shows a cost meter. Scanned PDFs are read twice with different prompts and a finding is kept only if both reads agree.

## Facts we can prove (verify them)
- 69 automated tests pass.
- Recorded live batch: 120 synthetic packages, 360 calls, 0 errors, total $0.056152, $0.000468 per package, about 167 packages per minute (re-run Nov 26, 2026 with the official ALN list).
- Recall in that run: arithmetic 18/18, date 18/18, threshold 18/18, prior finding omitted 18/18, award number 18/18 on the Nov 27 re-run (10/18 on Nov 26; the rule fixes were tuned on these packages, and a 120-package holdout with new seeds was also 18/18), false alarms 0 of 30 clean packages, with the official SAM.gov list (2,644 programs, Nov 21, 2026). Found during this re-run: `data/aln.csv` was gitignored, so the deployed functions silently used the 3-program fallback and flagged 30/30 clean packages; fixed in fa058d6 (file now tracked and bundled), then re-run.
- False alarms: 0 flagged of 30 clean packages.
- Scanned-mode live probe: $0.0024, 11 seconds.
- No secrets in the repo. Public demo has cost caps, an hourly limit per IP, and a kill switch.

## Unknowns and weak spots (we know these)
- Model tests use synthetic documents only. Three real public Single Audits (Cameron Community Action Agency, Western South Dakota Community Action, Community Support Programs) were run through the free page splitter only: it handled one, we fixed two layout bugs it exposed, and one has an unreadable rotated table (see README). The model has not read a real filing yet; the public demo's upload cap is smaller than two of them.
- The 120-package result is an earlier synthetic test, not proof on real filings.
- Template B was used to fix bugs, so it is no longer fully held out.
- Market size and prices ($49 per package, firm plan) are not validated. Market numbers are left off the public page on purpose.
- Credits: $10 limit; going over disqualifies. Spend so far is tracked in the Meta Usage page.
- App Store and Google Play are "coming soon" only.
- Default branch is still `claude/foundation`; the submitted branch is not chosen yet.
- The 48-second teaser (AI voice, captions, no presenter) is on the front page; the 3-minute judging demo video is scripted (docs/DEMO_SCRIPT.md) but not recorded.

## Questions for reviewers
1. Score each criterion 1-10 and give one sentence why.
2. Is this a "dashboard as main feature", "image analyzer" or "basic RAG" project (the guide says avoid these)? Argue both sides.
3. Does the use of Muse Ember look deep enough for the 25% tooling score? What Ember feature are we not using that we should (structured output, native PDF input, caching, reasoning effort, Muse Code)?
4. What would a CPA or grants officer say is missing before paying for it?
5. Which claim on the page is weakest or could be read as overclaiming?
6. List anything in the submission checklist we may have missed (video, repo, description, token trace, Usage screenshot, trajectory JSON if Muse Code was used).
7. Top three fixes, ordered by score gained per hour, with 7 days left.

## Ready-to-paste prompt (P)
Copy everything between the lines into the reviewer's chat, with the repo link and the live link.

---
You are an independent hackathon judge and a skeptical grants-compliance expert. Review "Grant Audit Ready" for the Meta Muse Ember Hackathon (Cerebral Valley, virtual, solo, US-only). Judging weights: Impact 30%, Use of Meta AI tooling 25%, Technical depth 20%, Demo 25%. Projects to avoid: dashboard as the main feature, image analyzers, basic RAG.

Look at: the public repo https://github.com/aizoya/grant-audit-ready (branch claude/scanned-mode, read README.md and docs/REVIEW_PACKET.md) and the live site https://grantaudit.aizoya.com. Do not trust our claims; open the code and the app. Do not ask for secrets and do not paste any.

Return: (1) a 1-10 score for each of the four criteria with one sentence why; (2) the three weakest claims on the page; (3) what a CPA firm would object to; (4) the Ember features we under-use; (5) a missing-items checklist for the submission; (6) the top three fixes ranked by score gained per hour. Separate what you verified from what you assumed. If you could not open something, say so.
---

## How we will use the results
Franklyn sends the prompt himself (or approves each send). Replies are recorded as opinions, not proof. Anything a reviewer claims about the rules gets checked against the official guide before we act on it.
