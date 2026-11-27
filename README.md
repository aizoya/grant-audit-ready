# grant-audit-ready

Evidence-linked Single Audit readiness checker for community grantees, built for the Meta Muse Ember hackathon.
The model only extracts values with exact quotes. Code does the rules, arithmetic and quote verification.
Findings without a verified quote are dropped. Every run reports its cost.

Status: synthetic data only; preview deployments on Vercel, no production deployment. See SCOPE.md, RULES.md, RESEARCH.md.
Run tests: `python3 -m pytest -q` · Build demo: `python3 build_demo.py`
Secrets: the API key is read from the environment (`META_MODEL_API_KEY`); never commit it.

## Eval (zero-spend extractor, not Ember)
`python3 eval_run.py` injects synthetic errors and scores recall by category. Dev seeds tune; held-out seeds are scored once.
Current gaps (honest): date 4/10, threshold-flip 0/10 (the stand-in extractor does not read "not required"), prior-finding rule needs a pack that contains the phrase. Numbers from the real model come after the first live run.

## Measured results (live Ember, temperature 0, effort minimal; synthetic packs only)
| Check | Template A (dev, seeds 0-4) | Template B (different wording, 5 programs, seeds 100-104) |
|---|---|---|
| arithmetic | 5/5 | 5/5 |
| award ID | 5/5 | 3/5 (measured when the ALN list had only 3 programs; the app now uses the official SAM.gov list, Nov 21, 2026, `data/aln.SOURCE.txt`; not yet re-measured) |
| dates | 5/5 | 5/5 |
| threshold | 5/5 | 5/5 |
| prior finding omitted | not exercised | 5/5 |
| false positives on clean packs | 0/10 runs | 0/10 runs |

Cost: about $0.0004 per report. Caveats: template B was used to find two logic bugs (unknown-ALN treated as mismatch; prior-finding matching on free-text reference), which were then fixed, so B is no longer fully held out. These are generated documents, not real audits.


## Scanned documents (added Nov 25)
A PDF with no text layer is sent to Muse Ember as a native PDF input (page images). It is read twice with different instructions.
Read 1 becomes the page text the pipeline quotes from. A finding is kept only if its quote matches read 1 and every number in the quote
also appears on the same page in read 2; otherwise it is dropped and counted ("dropped because the second read disagreed").
This is weaker than checking a real text layer, and the report says so. Limits: 12 pages per scanned document on the public demo.
Live probe on synthetic scanned PDFs (image-only, slight skew and noise): 3 documents, 9 model calls, about $0.0024, same 3 findings as the text version, 0 dropped.
Fixtures: `python3 scripts/make_scanned_fixture.py OUTDIR`; samples in `public/samples/`.

## Batch run (token-gated)
`/api/batch` runs generated synthetic packages (errors injected into template B, plus clean packs) with live Ember and reports total cost,
cost per package, packages per minute, recall by check and false alarms. It stays disabled unless `BATCH_TOKEN` is set on the server.
`LIVE_DISABLED=1` switches off all live model calls.


## Combined audit reports and scan quality
- Upload one combined audit report and the app finds the awards schedule, financial statements and findings by their headings (`ember_ledger/split.py`). Text PDFs only; scanned combined PDFs must be uploaded as three parts.
- The federal program list loads from `data/aln.csv` (columns `number,title`) when present. The built-in list has three demo programs.
- `scripts/make_noise_levels.py` builds scanned test pages at three quality levels; results are in `public/scanned-quality.json`.

## Real filings, first look (Nov 26, 2026; splitting only, no model run)
Three public Single Audit PDFs (Cameron Community Action Agency, Western South Dakota Community Action, Community Support Programs; downloaded by the owner from state sites, kept off the repo) were run through the free page splitter.
- Western South Dakota: found the awards schedule (2 pages), statements and findings correctly.
- Cameron: the awards table prints its title at the bottom of the page and the "Notes" page was mistaken for the schedule. Fixed by recognising the table header and treating Notes as a separate section.
- Community Support Programs: the awards schedule is a rotated table with an unreadable text layer. Combined mode now says so instead of guessing, and points to scanned mode or separate uploads.
- Not yet done: the model has not read these filings. The public demo also caps uploads (reports of 7 to 15 MB are too large for it).
