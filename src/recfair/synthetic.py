"""Deterministic synthetic recommender data.

All users, items, providers, creators, and interactions are fictional. The data is
for testing fairness, exposure, filter-bubble, explanation, and trust metrics
without private platform logs.
"""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd

CATEGORIES = ["science", "technology", "arts", "health", "education", "finance", "sports", "travel"]
PROVIDER_GROUPS = ["independent", "small_studio", "large_studio", "public_interest"]
USER_GROUPS = ["new_user", "regular_user", "power_user", "accessibility_focused"]


@dataclass(frozen=True)
class SyntheticRecommenderConfig:
    users: int = 100
    items: int = 160
    interactions_per_user: int = 18
    seed: int = 42

    def __post_init__(self) -> None:
        if self.users < 20:
            raise ValueError("Use at least 20 users for subgroup fairness analysis.")
        if self.items < 40:
            raise ValueError("Use at least 40 items for exposure and diversity analysis.")
        if self.interactions_per_user < 5:
            raise ValueError("Use at least 5 interactions per user.")


def generate_synthetic_recommender_data(config: SyntheticRecommenderConfig | None = None) -> dict[str, pd.DataFrame]:
    """Generate fictional users, items, and interactions."""
    cfg = config or SyntheticRecommenderConfig()
    rng = np.random.default_rng(cfg.seed)
    users = _users(cfg, rng)
    items = _items(cfg, rng)
    interactions = _interactions(users, items, cfg, rng)
    return {"users": users, "items": items, "interactions": interactions}


def _users(cfg: SyntheticRecommenderConfig, rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for idx in range(cfg.users):
        primary = CATEGORIES[idx % len(CATEGORIES)]
        secondary = CATEGORIES[(idx * 3 + 2) % len(CATEGORIES)]
        group = USER_GROUPS[idx % len(USER_GROUPS)]
        diversity_preference = float(np.clip(rng.normal(0.45 + 0.12 * (idx % 3), 0.18), 0.05, 0.95))
        rows.append({
            "user_id": f"U-{idx+1:04d}",
            "user_group": group,
            "primary_interest": primary,
            "secondary_interest": secondary,
            "diversity_preference": round(diversity_preference, 3),
            "trust_sensitivity": round(float(np.clip(rng.normal(0.55, 0.18), 0.10, 0.98)), 3),
            "session_depth": int(rng.integers(3, 14)),
        })
    return pd.DataFrame(rows)


def _items(cfg: SyntheticRecommenderConfig, rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for idx in range(cfg.items):
        category = CATEGORIES[(idx * 5 + idx // 3) % len(CATEGORIES)]
        provider = PROVIDER_GROUPS[idx % len(PROVIDER_GROUPS)]
        # Large studios receive a synthetic popularity advantage to make bias measurable.
        provider_boost = {"large_studio": 0.22, "small_studio": 0.08, "public_interest": 0.02, "independent": -0.03}[provider]
        quality = float(np.clip(rng.normal(0.62, 0.16), 0.08, 0.98))
        popularity = float(np.clip(0.45 * quality + provider_boost + rng.beta(2, 5), 0.02, 1.0))
        tag_a = category
        tag_b = CATEGORIES[(idx + 3) % len(CATEGORIES)]
        rows.append({
            "item_id": f"I-{idx+1:04d}",
            "creator_id": f"C-{(idx % max(12, cfg.items // 8))+1:03d}",
            "provider_group": provider,
            "category": category,
            "tags": f"{tag_a}|{tag_b}",
            "quality_score": round(quality, 3),
            "popularity_seed": round(popularity, 3),
            "sensitive_topic_flag": int(category in {"health", "finance"} and rng.random() < 0.18),
        })
    items = pd.DataFrame(rows)
    items["popularity_percentile"] = items["popularity_seed"].rank(pct=True)
    return items


def _interactions(users: pd.DataFrame, items: pd.DataFrame, cfg: SyntheticRecommenderConfig, rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    item_lookup = items.set_index("item_id")
    for user in users.itertuples(index=False):
        scores = []
        for item in items.itertuples(index=False):
            interest_match = 1.0 if item.category == user.primary_interest else 0.55 if item.category == user.secondary_interest else 0.18
            score = 0.52 * interest_match + 0.26 * item.quality_score + 0.22 * item.popularity_seed + rng.normal(0, 0.05)
            scores.append(max(0.001, score))
        probs = np.array(scores) / np.sum(scores)
        chosen = rng.choice(items["item_id"].to_numpy(), size=min(cfg.interactions_per_user, len(items)), replace=False, p=probs)
        for step, item_id in enumerate(chosen):
            item = item_lookup.loc[item_id]
            interest_match = item.category in {user.primary_interest, user.secondary_interest}
            rating = float(np.clip(2.2 + 1.3 * interest_match + item.quality_score + rng.normal(0, 0.55), 1.0, 5.0))
            rows.append({
                "user_id": user.user_id,
                "item_id": item_id,
                "rating": round(rating, 2),
                "liked": int(rating >= 3.7),
                "watch_fraction": round(float(np.clip(rating / 5 + rng.normal(0, 0.12), 0.05, 1.0)), 3),
                "interaction_order": step + 1,
            })
    return pd.DataFrame(rows)
