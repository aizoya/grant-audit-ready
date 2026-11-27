# Submission pack: Grant Audit Ready (Meta Muse Ember Hackathon)

Deadline: Dec 2, 2026, 9:00 PM ET (6:00 PM PT). Nothing is submitted. Final submission needs Franklyn's approval.

## Project description (draft, about 150 words)
Grant Audit Ready is a readiness checker for organizations that spend federal grant money and face a Single Audit. A grantee uploads three documents: the schedule of federal awards, the financial statements and last year's findings. Muse Ember reads them and returns values with exact quotes. It does no arithmetic. Plain code adds the lines, checks award numbers against the official SAM.gov list, tests the audit threshold, dates and unanswered prior findings, and verifies every quote against the page. A finding with no verified quote is dropped and counted. Scanned documents are read twice and a finding survives only if both reads agree. Every report shows what it cost. In a synthetic test of 120 generated packages the run cost about six cents: all arithmetic, date, threshold and prior-finding errors caught, 10 of 18 wrong award numbers, no false alarms on 30 clean packages. It is a readiness aid, not an audit opinion, and it has not been proven on real filings.

## Use of Meta AI tooling (for the 25% criterion)
- Muse Ember through the Meta Model API with strict JSON-schema output, temperature 0, and native PDF input for scanned pages.
- Used for extraction with quotes only. Arithmetic, rules and quote verification are code, so the model cannot invent a finding.
- Two independent reads of scanned pages, with agreement required.
- Cost ledger with a hard stop, per-request cap and kill switch; recorded batch run through the same API.

## Checklist
| Item | Status | Owner |
|---|---|---|
| Public repo (aizoya/grant-audit-ready) | public; latest work on `claude/scanned-mode`, default branch is `claude/foundation` | Franklyn decides which branch is submitted |
| Live link | https://grantaudit.aizoya.com (serves `claude/scanned-mode`) | done |
| 3-minute demo video | silent captioned cut done; voice generated; waiting for the mp3 to reach the workspace, then finish and pre-flight | Claude (needs file move) |
| Project description | draft above | Franklyn approves |
| Usage screenshot (Meta Model API Usage page, Nov 23 - Dec 2, Muse Ember filter, total tokens and spend) | not taken | Franklyn (login) |
| Prompt/token trace with amount spent | export from the Meta Usage page; our own per-run costs are in `public/batch-run.json`, `public/demo-runs.json` and the README | Franklyn exports, Claude summarizes |
| Muse Code trajectory export | only if Muse Code was used; it was not | n/a |
| Meta credits | confirm claimed by Nov 30, 12:00 PM ET and the key works through Dec 7; spend so far about $0.2 against our $9 stop | Franklyn |
| New-work check | first commit Nov 24, 2026 (after the Nov 23 window opened) | done |
| No secrets in repo, no real filings in repo or video | verified by search before each push | done |
| Final submission form | link not yet known | Franklyn |
