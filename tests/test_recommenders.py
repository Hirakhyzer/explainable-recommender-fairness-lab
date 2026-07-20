from recfair.recommenders import METHODS, build_all_recommendations, build_recommendations
from recfair.synthetic import SyntheticRecommenderConfig, generate_synthetic_recommender_data


def _sample():
    return generate_synthetic_recommender_data(SyntheticRecommenderConfig(users=24, items=60, interactions_per_user=7, seed=5))


def test_all_methods_generate_recommendations():
    data = _sample()
    recs = build_all_recommendations(data["users"], data["items"], data["interactions"], top_k=6)
    assert not recs.empty
    assert set(recs["method"].unique()) == set(METHODS)
    assert recs.groupby(["method", "user_id"]).size().max() <= 6


def test_recommendations_exclude_seen_items():
    data = _sample()
    recs = build_recommendations(data["users"], data["items"], data["interactions"], method="content_based", top_k=6)
    seen = data["interactions"].groupby("user_id")["item_id"].apply(set).to_dict()
    for row in recs.itertuples(index=False):
        assert row.item_id not in seen[row.user_id]
