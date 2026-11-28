# Submission packet: Grant Audit Ready (Muse Ember Hackathon)

Status: NOT submitted. Franklyn submits. Deadline: **Dec 2, 6:00 PM PT** (9:00 PM ET), per the participant guide and the submit page.
Fields below were read from the live submit form on Nov 27 (nothing was typed into it).

## Required fields and status
| Field | Status | Value / owner |
|---|---|---|
| Team Name | ready | Grant Audit Ready (solo: Franklyn Rosario) |
| Project Description (3,000 chars) | draft below | paste |
| Public GitHub Repository | ready | https://github.com/aizoya/grant-audit-ready/tree/claude/scanned-mode (see note on default branch) |
| 3 Minute Demo Video (YouTube-style URL) | render pending audio | Franklyn uploads the mp4 (unlisted is fine) and pastes the link |
| Usage screenshot (Nov 23 to Dec 2, filter Muse Ember, total tokens and spend) | Franklyn | dev.meta.ai Usage page |
| Muse Code trajectory JSON | only if Muse Code was used | not used for this build, as far as the repo shows |
| Team ID used for credit redemption | Franklyn | from dev.meta.ai |
| Describe your use of Meta products (3,000) | draft below | paste |
| Why are Meta's models important (3,000) | draft below | paste |
| Survey questions (likelihood, opinion, obstacles) | Franklyn | his own opinion |
| X post link | optional | skip or Franklyn posts |
| Prompt/token trace (rule "Proof of usage") | partial | `public/batch-run.json` (360 calls, $0.056152); per-call token rows now returned as `trace` by `/api/check` (commit 8c45677, not yet deployed) |

## Rule checks
- Repo public: yes. Default branch is still `claude/foundation` (Nov 25 README). Either submit the branch URL above or make `claude/scanned-mode` the default (Franklyn's call: it changes repo settings).
- Demo must show only what was built during the event: first commit Nov 24, 2026; video badge reads "Built during the Muse Ember Hackathon".
- Avoid-list: not a dashboard, not basic RAG, not an image analyzer. Core is extraction with quotes plus deterministic verification.
- Spend stays under $10: confirm on the Usage page screenshot.
- Never claim accuracy on real filings: the model has read one real public report once; every number in the video is from synthetic packages.

## Draft: Project Description
Grant Audit Ready checks a nonprofit's or local government's Single Audit package before the auditor does. Upload the awards schedule (SEFA), the financial statements and last year's findings, or one combined report, and get a readiness report where every finding quotes the page it came from.

Muse Ember only reads: it returns values with exact quotes through strict JSON schemas. Plain code does the arithmetic, applies the rules (SEFA totals, statements vs awards, Single Audit threshold, report dates, period match, award numbers against the official SAM.gov list of 2,644 programs, prior findings left unanswered) and verifies every quote against the source text. A finding whose quote is not on the page is dropped and counted. Scanned PDFs go to Ember as native PDF input and are read twice; a finding survives only if both reads agree, and the report labels that mode lower assurance.

Every run shows its cost. In a recorded synthetic benchmark, 120 generated packages took 360 Ember calls, $0.056 in total (about $0.0005 per package, about 167 packages per minute), caught 18/18 arithmetic, date, threshold and prior-finding errors, 18/18 wrong award numbers after rule fixes (10/18 before; a separate 120-package holdout was also 18/18), and raised no false alarms on 30 clean packages. These are synthetic documents, not proof on real filings; we say so in the app and the video.

Who it is for: finance leads and the CPAs who prepare Single Audit packages. Errors found in audit are expensive; found before, they are a fix.

## Draft: Describe your use of Meta products
Runtime is muse-ember-1.0 only, through the Meta Model API Responses endpoint, with a deterministic orchestrator (no larger planner model). We use: strict JSON-schema structured output (every value must carry its quote), native PDF input for scanned pages with a two-read agreement check, temperature 0 and minimal reasoning effort for extraction, and a stable system-prompt prefix with 24-hour prompt-cache retention. A cost ledger preflights every call against a hard stop and records real usage from the response, so each report prints its own cost.

## Draft: Why are Meta's models important
The product only works at Ember's unit cost. A screening pass a grantee runs ten times while fixing a package has to cost fractions of a cent, and a CPA firm screening hundreds of clients needs throughput, not a frontier model. Ember is cheap and fast enough to read every page, and reliable enough at quoting that code can verify each answer, which is what makes the "no quote, no finding" rule affordable.
