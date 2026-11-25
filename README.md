# grant-audit-ready

Evidence-linked Single Audit readiness checker for community grantees, built for the Meta Muse Ember hackathon.
The model only extracts values with exact quotes. Code does the rules, arithmetic and quote verification.
Findings without a verified quote are dropped. Every run reports its cost.

Status: local prototype, synthetic data only. Not deployed. See SCOPE.md, RULES.md, RESEARCH.md.
Run tests: `python3 -m pytest -q` · Build demo: `python3 build_demo.py`
Secrets: the API key is read from the environment (`META_MODEL_API_KEY`); never commit it.

## Eval (zero-spend extractor, not Ember)
`python3 eval_run.py` injects synthetic errors and scores recall by category. Dev seeds tune; held-out seeds are scored once.
Current gaps (honest): date 4/10, threshold-flip 0/10 (the stand-in extractor does not read "not required"), prior-finding rule needs a pack that contains the phrase. Numbers from the real model come after the first live run.
