from recfair.explanations import add_explanations, explanation_audit
from recfair.fairness import provider_exposure_fairness, subgroup_recommendation_audit
from recfair.metrics import algorithm_comparison, filter_bubble_report, user_trust_audit
from recfair.recommenders import build_all_recommendations
from recfair.synthetic import SyntheticRecommenderConfig, generate_synthetic_recommender_data


def test_metrics_have_expected_columns():
    data = generate_synthetic_recommender_data(SyntheticRecommenderConfig(users=24, items=60, interactions_per_user=7, seed=8))
    recs = build_all_recommendations(data["users"], data["items"], data["interactions"], top_k=5)
    explanations = add_explanations(recs)
    comparison = algorithm_comparison(recs, data["items"])
    fairness = provider_exposure_fairness(recs, data["items"])
    bubbles = filter_bubble_report(recs)
    trust = user_trust_audit(recs, explanations)
    exp = explanation_audit(explanations)
    subgroup = subgroup_recommendation_audit(recs)
    assert {"method", "mean_relevance_proxy", "provider_exposure_gap"}.issubset(comparison.columns)
    assert {"provider_group", "exposure_share", "absolute_exposure_gap"}.issubset(fairness.columns)
    assert {"filter_bubble_score", "filter_bubble_risk"}.issubset(bubbles.columns)
    assert {"trust_proxy_score", "trust_risk_flag"}.issubset(trust.columns)
    assert {"explanation_coverage", "mean_explanation_quality_proxy"}.issubset(exp.columns)
    assert {"user_group", "subgroup_relevance_gap"}.issubset(subgroup.columns)
