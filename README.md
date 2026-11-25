# grant-audit-ready

Evidence-linked Single Audit readiness checker for community grantees, built for the Meta Muse Ember hackathon.
The model only extracts values with exact quotes. Code does the rules, arithmetic and quote verification.
Findings without a verified quote are dropped. Every run reports its cost.

Status: local prototype, synthetic data only. Not deployed. See SCOPE.md, RULES.md, RESEARCH.md.
Run tests: `python3 -m pytest -q` · Build demo: `python3 build_demo.py`
Secrets: the API key is read from the environment (`META_MODEL_API_KEY`); never commit it.
