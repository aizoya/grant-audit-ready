# 3-minute judging demo script (synthetic data only)

Source of truth for the spoken lines: `docs/DEMO_NARRATION.json` (trimmed Nov 27: about 211 words, 138 s planned, so the voiced cut lands near 2:30 with room for page loads). The table below is the scene plan. Both samples on screen are recorded runs and are labelled that way. The export must pass `python3 scripts/demo/check_video.py FILE.mp4` (audio present, under 3:00, 1080p) before it is called ready.

Target 2:50. Record the screen at 1080p, one take per scene, voice from the same ElevenLabs voice or live narration. Never show real filings or keys. Every number below comes from the recorded run on the Proof tab or from what the live app shows on screen at that moment.

| Time | Screen | Say |
|---|---|---|
| 0:00-0:15 | Front page hero (verified finding), teaser paused | Organizations subject to a Single Audit have to get their package right. Grant Audit Ready checks it before the auditor does, and it never shows a finding it cannot quote. |
| 0:15-0:45 | App page: pick the arithmetic sample (a recorded real Muse Ember run on a synthetic package) | The model reads the awards schedule, the statements and last year's findings. It returns values with exact quotes. It does no arithmetic. |
| 0:45-1:20 | Result: "Awards schedule does not add up", click the quote, source text highlights | Plain code adds the lines: $1,277,400 against a stated total of $1,240,000. The finding carries the quote and the page. If the quote is not found on the page, the finding is dropped and counted. |
| 1:20-1:50 | Cost meter on the result, then run the clean package (no findings) | Each run shows what it cost, here a fraction of a cent. The clean package gives no findings on this test package. |
| 1:50-2:20 | Upload section (scanned mode explained; no scanned result is faked on screen) | Scanned pages are read twice. A finding survives only if both reads agree. Otherwise it is dropped and we say so. We label this mode lower assurance. |
| 2:20-2:45 | Proof tab: ledger lines (earlier synthetic test: 120 packages, about six cents, recall table incl. award numbers 10/18 on the official list), Honest limits | An earlier synthetic test: 120 generated packages, about six cents on Muse Ember. It is not proof on real filings. We show what we miss, and what we have not tested: real filings at scale, and handwriting. |
| 2:45-2:55 | Wordmark, URL, "Built on Meta Muse Ember" | Grant Audit Ready, by AIZOYA. Try it at grantaudit.aizoya.com. |

Before recording
- Confirm the Usage page shows the spend (Muse Ember filter) and stays under our $9 hard stop.
- If real-filing results exist, add one line to the 2:20-2:45 scene with the real numbers and organization names, and no more than that.
- Do not claim a win, a customer, or judge feedback.

Recording: `python3 scripts/demo/record_demo.py OUTDIR [durations.json]` makes the captioned screen capture from `docs/DEMO_NARRATION.json`. The voice is added after the ElevenLabs monthly reset (about Nov 29, 6 pm PT); the character allowance was used up on Nov 26.

Final render (Nov 27): narration generated as 7 clips (one per segment, ElevenLabs voice "Benjamin", 83 s of speech). `record_demo.py` now logs each scene's real start in `timeline.json`; `python3 scripts/demo/mux.py CAPDIR CLIPDIR OUT.mp4` places each clip at its scene start plus 0.6 s, so page-load delays cannot drift the voice off the captions. The on-screen badge states the work was built during the hackathon (a rule requirement).
