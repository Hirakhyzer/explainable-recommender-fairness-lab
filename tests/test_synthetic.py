from recfair.synthetic import SyntheticRecommenderConfig, generate_synthetic_recommender_data


def test_synthetic_shapes_and_keys():
    data = generate_synthetic_recommender_data(SyntheticRecommenderConfig(users=24, items=50, interactions_per_user=6, seed=3))
    assert set(data) == {"users", "items", "interactions"}
    assert len(data["users"]) == 24
    assert len(data["items"]) == 50
    assert data["interactions"]["user_id"].nunique() == 24
    assert data["items"]["provider_group"].nunique() >= 3


def test_invalid_config_rejected():
    try:
        SyntheticRecommenderConfig(users=5, items=20, interactions_per_user=2)
    except ValueError:
        assert True
    else:
        raise AssertionError("invalid config should fail")
