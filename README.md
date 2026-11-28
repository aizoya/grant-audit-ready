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
| award ID | 5/5 | 3/5 (measured with a 3-program reference list; superseded by the 120-package benchmark below) |
| dates | 5/5 | 5/5 |
| threshold | 5/5 | 5/5 |
| prior finding omitted | not exercised | 5/5 |
| false positives on clean packs | 0/10 runs | 0/10 runs |

Cost: about $0.0004 per report. Caveats: template B was used to find two logic bugs (unknown-ALN treated as mismatch; prior-finding matching on free-text reference), which were then fixed, so B is no longer fully held out. These are generated documents, not real audits.


## 120-package synthetic benchmark (Nov 26, 2026; official ALN list)
Separate from the five-sample table above. Recorded in `public/batch-run.json`; produced by the token-gated `/api/batch` (below), 3 runs of 40 generated packages (seeds 4000, 5000, 6000), live Muse Ember, synthetic documents only.
| Measure | Result |
|---|---|
| Packages / model calls / errors | 120 / 360 / 0 |
| Total cost / per package | $0.056152 / about $0.0005 |
| Arithmetic, date, threshold, omitted prior finding | 18/18 each |
| Award number | 10/18 |
| Clean packages flagged | 0 of 30 |
Reference list: official SAM.gov Assistance Listings (2,644 programs, file dated Nov 21, 2026). Not proof on real filings. A first run on the same day flagged all clean packages because `data/aln.csv` was not deployed; fixed in `fa058d6` and re-run.

**Re-run Nov 27, 2026 (after the ALN-title rule and splitter fixes, commit 24676c0):** same 120 packages and seeds, 360 calls, 0 errors, $0.056425 total. Results are unchanged: arithmetic, date, threshold and prior-finding 18/18 each, award number 10/18, 0 of 30 clean packages flagged. The fixes did not move recall on synthetic data; they matter on real schedules (see below). Award-number recall is the weak spot and is reported as measured.

## First live run on a real public report (Nov 26, 2026; results only)
One public Single Audit report (Western South Dakota Community Action, FY ended June 30, 2024) was split into its three parts and checked live with Muse Ember: cost $0.00162, 4 findings, 0 dropped, 17 checks passed. There is no ground truth for this report, so these are review flags, not confirmed errors:
- Awards total vs statement revenue ($5,303,201 vs $5,376,139): a legitimate flag by design (route to a person; timing and accrual differences are common).
- Two award-number findings (93.071, 93.048): false alarms. The schedule uses the common or act name, the official list uses a different title. The rule was too strict; it now flags only when the program name matches a different listing. Re-run on the fixed rule (cost $0.00154): those two flags are gone, 2 findings remain (the total difference and the mis-slotted prior finding), 19 checks passed.
- One prior-finding flag: the splitter left the report's corrective action plan (which answers the current-year finding) out of the findings slot, so the flag was a mis-slot, not a real gap. Fixed in the splitter afterwards (corrective action plan now stays with the findings); the model run after that fix has not been repeated.
The report itself stays out of the repo and the demo. This is one report, not a benchmark.

**Re-run Nov 27, 2026 after the splitter fix (same report, same three parts, results only):** cost $0.00162, 1 verified finding, 20 checks passed, 0 dropped for a missing quote. The remaining finding is the legitimate route-to-human: awards schedule total $5,303,201 vs financial-statement federal revenue $5,376,139 (differences can be timing or accrual items). The earlier false prior-finding flag is gone. One report, no ground truth: this shows the false alarms are fixed, not a recall measurement.

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
