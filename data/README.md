# Data policy

This repository is synthetic-first. The default pipeline generates fictional users, items, creators, providers, categories, interactions, explanations, and recommendation outputs.

No private platform logs, real user profiles, real creator accounts, or sensitive attributes are required to run the lab.

For any real deployment, add privacy review, data minimization, consent/legal basis, retention controls, appeal mechanisms for providers, user controls, and independent fairness review before use.

Suggested real-data staging structure, intentionally ignored by Git:

```text
data/raw/
data/processed/
```

Do not commit private recommendation logs or identifiable user/provider information.
