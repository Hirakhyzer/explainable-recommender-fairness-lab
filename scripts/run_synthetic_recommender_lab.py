"""Run the complete synthetic explainable recommender fairness lab.

The command uses only fictional users, items, providers, creators, and
interactions. It demonstrates popularity/content/collaborative baselines,
diversity and fairness reranking, explanation generation, filter-bubble analysis,
exposure fairness auditing, trust proxy scoring, reporting, figures, and a
hash-chained audit log.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from recfair.audit import append_record, verify_log
from recfair.config import ensure_output_dirs, set_seed
from recfair.explanations import add_explanations, explanation_audit
from recfair.fairness import fairness_summary, provider_exposure_fairness, subgroup_recommendation_audit
from recfair.metrics import algorithm_comparison, filter_bubble_report, summary_metrics, user_trust_audit
from recfair.recommenders import build_all_recommendations
from recfair.reporting import write_report
from recfair.synthetic import SyntheticRecommenderConfig, generate_synthetic_recommender_data
from recfair.visualization import plot_algorithm_relevance, plot_exposure_fairness, plot_filter_bubble_risk, plot_provider_exposure, plot_trust_proxy


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a synthetic explainable recommender fairness lab.")
    parser.add_argument("--users", type=int, default=100)
    parser.add_argument("--items", type=int, default=160)
    parser.add_argument("--interactions-per-user", type=int, default=18)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", default="outputs")
    args = parser.parse_args()

    set_seed(args.seed)
    outputs = ensure_output_dirs(args.output_dir)
    data = generate_synthetic_recommender_data(SyntheticRecommenderConfig(
        users=args.users,
        items=args.items,
        interactions_per_user=args.interactions_per_user,
        seed=args.seed,
    ))
    users = data["users"]
    items = data["items"]
    interactions = data["interactions"]

    recommendations = build_all_recommendations(users, items, interactions, top_k=args.top_k)
    explanations = add_explanations(recommendations)
    comparison = algorithm_comparison(recommendations, items)
    fairness = provider_exposure_fairness(recommendations, items)
    subgroup_audit = subgroup_recommendation_audit(recommendations)
    bubbles = filter_bubble_report(recommendations)
    exp_audit = explanation_audit(explanations)
    trust = user_trust_audit(recommendations, explanations)

    summary = summary_metrics(comparison, fairness, bubbles, trust)
    summary.update(fairness_summary(fairness, subgroup_audit))
    summary.update({
        "seed": args.seed,
        "user_count": int(len(users)),
        "item_count": int(len(items)),
        "interaction_count": int(len(interactions)),
        "recommendation_count": int(len(recommendations)),
        "top_k": int(args.top_k),
    })

    users.to_csv(outputs["results"] / "synthetic_users.csv", index=False)
    items.to_csv(outputs["results"] / "synthetic_items.csv", index=False)
    interactions.to_csv(outputs["results"] / "synthetic_interactions.csv", index=False)
    explanations.to_csv(outputs["results"] / "synthetic_recommendations.csv", index=False)
    comparison.to_csv(outputs["results"] / "synthetic_algorithm_comparison.csv", index=False)
    fairness.to_csv(outputs["results"] / "synthetic_exposure_fairness_audit.csv", index=False)
    subgroup_audit.to_csv(outputs["results"] / "synthetic_subgroup_recommendation_audit.csv", index=False)
    bubbles.to_csv(outputs["results"] / "synthetic_filter_bubble_report.csv", index=False)
    exp_audit.to_csv(outputs["results"] / "synthetic_explanation_audit.csv", index=False)
    trust.to_csv(outputs["results"] / "synthetic_user_trust_audit.csv", index=False)

    audit_path = outputs["audit"] / "recommender_fairness_audit_log.jsonl"
    append_record(audit_path, {**summary, "boundary": "synthetic recommender review support only"})
    summary["audit_log"] = verify_log(audit_path)
    (outputs["results"] / "synthetic_recommender_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    write_report(outputs["reports"] / "synthetic_recommender_fairness_report.md", summary, comparison, fairness, bubbles, exp_audit, trust)
    plot_algorithm_relevance(comparison, outputs["figures"] / "synthetic_algorithm_relevance.png")
    plot_exposure_fairness(fairness, outputs["figures"] / "synthetic_exposure_fairness.png")
    plot_filter_bubble_risk(bubbles, outputs["figures"] / "synthetic_filter_bubble_risk.png")
    plot_provider_exposure(fairness, outputs["figures"] / "synthetic_provider_exposure.png")
    plot_trust_proxy(trust, outputs["figures"] / "synthetic_trust_proxy.png")

    print(json.dumps(summary, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
