# Synthetic lab guide

Run the default experiment:

```bash
python scripts/run_synthetic_recommender_lab.py
```

Run a smaller smoke experiment:

```bash
python scripts/run_synthetic_recommender_lab.py --users 40 --items 70 --top-k 8 --seed 7 --output-dir outputs_ci
```

## Outputs

The script writes synthetic users, items, interactions, recommendations with explanations, algorithm comparison metrics, provider exposure fairness audits, subgroup audits, filter-bubble reports, user trust audits, a Markdown report, figures, and a hash-chained audit log.

## Suggested experiments

- Increase `--items` to study catalog coverage.
- Change `--top-k` to inspect exposure concentration at different list lengths.
- Compare `popularity` with `fairness_rerank` for provider exposure gap.
- Compare `content_based` with `diversity_rerank` for filter-bubble risk.
