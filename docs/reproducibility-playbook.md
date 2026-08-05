# Reproducibility Playbook

This playbook defines how to run and report experiments from the **Explainable Recommender Fairness Lab** so another researcher can inspect the workflow.

## 1. Minimum run record

Every experiment should record:

| Field | Example |
|---|---|
| Run name | `synthetic_recommender_seed_42_top10` |
| Dataset type | synthetic fictional users/items/providers |
| Number of users | `120` |
| Number of items | `180` |
| Top-k setting | `10` |
| Random seed | `42` |
| Algorithms | popularity, content-based, collaborative, diversity rerank, fairness rerank |
| Explanation rule | current explanation module and repository commit |
| Fairness groups | provider/creator groups in synthetic catalog |
| Metrics | relevance, diversity, catalog coverage, exposure gap, filter-bubble risk |
| Output directory | `outputs/` |
| Boundary statement | synthetic audit signals only, not real platform decisions |

## 2. Recommended command

```bash
python scripts/run_synthetic_recommender_lab.py --users 120 --items 180 --top-k 10 --seed 42
```

## 3. Evidence bundle

A complete run should include:

```text
outputs/results/synthetic_users.csv
outputs/results/synthetic_items.csv
outputs/results/synthetic_interactions.csv
outputs/results/synthetic_recommendations.csv
outputs/results/synthetic_algorithm_comparison.csv
outputs/results/synthetic_exposure_fairness_audit.csv
outputs/results/synthetic_filter_bubble_report.csv
outputs/results/synthetic_explanation_audit.csv
outputs/results/synthetic_user_trust_audit.csv
outputs/results/synthetic_recommender_summary.json
outputs/reports/synthetic_recommender_fairness_report.md
outputs/audit/recommender_fairness_audit_log.jsonl
outputs/figures/
```

## 4. Interpretation rules

- Report relevance and fairness metrics together.
- Never claim fairness improvement without reporting relevance trade-offs.
- Separate synthetic provider groups from any real demographic or creator group.
- Report filter-bubble and diversity metrics per user segment when possible.
- State that trust scores are proxies, not direct user psychology measurements.
- Preserve the governance boundary in every report.

## 5. Checklist before sharing results

- [ ] Seed and configuration recorded.
- [ ] Synthetic-data boundary stated clearly.
- [ ] Algorithms and reranking rules documented.
- [ ] Exposure fairness and relevance trade-off reported.
- [ ] Explanation coverage and limitations reported.
- [ ] Audit log preserved.
- [ ] No real-world ranking or platform decision claim is made.