"""Transparent recommendation algorithms and rerankers."""

from __future__ import annotations

import numpy as np
import pandas as pd

METHODS = ["popularity", "content_based", "collaborative_similarity", "diversity_rerank", "fairness_rerank"]


def build_recommendations(
    users: pd.DataFrame,
    items: pd.DataFrame,
    interactions: pd.DataFrame,
    method: str = "content_based",
    top_k: int = 10,
) -> pd.DataFrame:
    """Build top-k recommendations for one transparent method."""
    if method not in METHODS:
        raise ValueError(f"method must be one of {METHODS}")
    base_method = "content_based" if method in {"diversity_rerank", "fairness_rerank"} else method
    candidates = _score_candidates(users, items, interactions, base_method)
    if method == "diversity_rerank":
        return _rerank_diversity(candidates, top_k)
    if method == "fairness_rerank":
        return _rerank_provider_fairness(candidates, top_k)
    return _top_k(candidates, top_k, method)


def build_all_recommendations(users: pd.DataFrame, items: pd.DataFrame, interactions: pd.DataFrame, top_k: int = 10) -> pd.DataFrame:
    """Run all algorithms and return one recommendation table."""
    frames = [build_recommendations(users, items, interactions, method, top_k) for method in METHODS]
    return pd.concat(frames, ignore_index=True)


def _score_candidates(users: pd.DataFrame, items: pd.DataFrame, interactions: pd.DataFrame, method: str) -> pd.DataFrame:
    item_stats = _item_stats(items, interactions)
    seen = interactions.groupby("user_id")["item_id"].apply(set).to_dict()
    user_profiles = _user_profiles(users, items, interactions)
    similar_likes = _similar_user_likes(users, interactions)
    rows = []
    for user in users.itertuples(index=False):
        user_seen = seen.get(user.user_id, set())
        profile = user_profiles.get(user.user_id, {"categories": set(), "providers": set()})
        sim_like = similar_likes.get(user.user_id, {})
        for item in item_stats.itertuples(index=False):
            if item.item_id in user_seen:
                continue
            content_match = 1.0 if item.category in profile["categories"] else 0.45 if item.category in {user.primary_interest, user.secondary_interest} else 0.08
            provider_repeat = 1.0 if item.provider_group in profile["providers"] else 0.2
            collaborative_score = float(sim_like.get(item.item_id, 0.0))
            if method == "popularity":
                score = 0.78 * item.popularity_score + 0.22 * item.quality_score
            elif method == "collaborative_similarity":
                score = 0.52 * collaborative_score + 0.22 * content_match + 0.16 * item.quality_score + 0.10 * item.popularity_score
            else:
                score = 0.48 * content_match + 0.20 * item.quality_score + 0.17 * item.popularity_score + 0.10 * provider_repeat + 0.05 * user.diversity_preference
            rows.append({
                "user_id": user.user_id,
                "user_group": user.user_group,
                "item_id": item.item_id,
                "creator_id": item.creator_id,
                "provider_group": item.provider_group,
                "category": item.category,
                "tags": item.tags,
                "quality_score": float(item.quality_score),
                "popularity_score": float(item.popularity_score),
                "popularity_percentile": float(item.popularity_percentile),
                "sensitive_topic_flag": int(item.sensitive_topic_flag),
                "content_match_score": round(float(content_match), 4),
                "collaborative_score": round(float(collaborative_score), 4),
                "base_score": round(float(np.clip(score, 0, 1)), 4),
            })
    return pd.DataFrame(rows)


def _item_stats(items: pd.DataFrame, interactions: pd.DataFrame) -> pd.DataFrame:
    counts = interactions.groupby("item_id").agg(interaction_count=("user_id", "count"), mean_rating=("rating", "mean")).reset_index()
    out = items.merge(counts, on="item_id", how="left")
    out["interaction_count"] = out["interaction_count"].fillna(0)
    out["mean_rating"] = out["mean_rating"].fillna(out["quality_score"] * 5)
    max_count = max(float(out["interaction_count"].max()), 1.0)
    out["popularity_score"] = np.clip(0.65 * (out["interaction_count"] / max_count) + 0.35 * out["popularity_seed"], 0, 1)
    return out


def _user_profiles(users: pd.DataFrame, items: pd.DataFrame, interactions: pd.DataFrame) -> dict[str, dict[str, set[str]]]:
    enriched = interactions.merge(items[["item_id", "category", "provider_group"]], on="item_id", how="left")
    profiles = {}
    for user in users.itertuples(index=False):
        liked = enriched.loc[(enriched["user_id"] == user.user_id) & (enriched["liked"] == 1)]
        categories = set(liked["category"].dropna().astype(str).tolist()) or {user.primary_interest, user.secondary_interest}
        providers = set(liked["provider_group"].dropna().astype(str).tolist())
        profiles[user.user_id] = {"categories": categories, "providers": providers}
    return profiles


def _similar_user_likes(users: pd.DataFrame, interactions: pd.DataFrame) -> dict[str, dict[str, float]]:
    liked = interactions.loc[interactions["liked"] == 1].groupby("user_id")["item_id"].apply(set).to_dict()
    all_users = users["user_id"].tolist()
    result: dict[str, dict[str, float]] = {}
    for user_id in all_users:
        own = liked.get(user_id, set())
        scores: dict[str, float] = {}
        for other_id in all_users:
            if other_id == user_id:
                continue
            other = liked.get(other_id, set())
            union = len(own | other)
            sim = len(own & other) / union if union else 0.0
            if sim <= 0:
                continue
            for item in other - own:
                scores[item] = scores.get(item, 0.0) + sim
        if scores:
            max_score = max(scores.values())
            result[user_id] = {item: value / max_score for item, value in scores.items()}
        else:
            result[user_id] = {}
    return result


def _top_k(candidates: pd.DataFrame, top_k: int, method: str) -> pd.DataFrame:
    if candidates.empty:
        return _empty_recommendations()
    out = candidates.sort_values(["user_id", "base_score"], ascending=[True, False]).groupby("user_id").head(top_k).copy()
    out["method"] = method
    out["rank"] = out.groupby("user_id")["base_score"].rank(method="first", ascending=False).astype(int)
    out["recommendation_score"] = out["base_score"]
    return out[_recommendation_columns()].sort_values(["method", "user_id", "rank"]).reset_index(drop=True)


def _rerank_diversity(candidates: pd.DataFrame, top_k: int) -> pd.DataFrame:
    rows = []
    for user_id, group in candidates.groupby("user_id"):
        selected = []
        remaining = group.sort_values("base_score", ascending=False).copy()
        while len(selected) < top_k and not remaining.empty:
            def score(row):
                used_cats = {s["category"] for s in selected}
                used_providers = {s["provider_group"] for s in selected}
                novelty = (0.13 if row.category not in used_cats else -0.03) + (0.10 if row.provider_group not in used_providers else -0.02)
                return float(row.base_score) + novelty
            remaining = remaining.assign(rerank_score=remaining.apply(score, axis=1))
            best = remaining.sort_values(["rerank_score", "base_score"], ascending=False).iloc[0].to_dict()
            selected.append(best)
            remaining = remaining.loc[remaining["item_id"] != best["item_id"]]
        rows.extend(selected)
    return _finalize_rerank(pd.DataFrame(rows), "diversity_rerank")


def _rerank_provider_fairness(candidates: pd.DataFrame, top_k: int) -> pd.DataFrame:
    target_share = 1.0 / max(candidates["provider_group"].nunique(), 1)
    global_counts = {provider: 0 for provider in candidates["provider_group"].unique()}
    rows = []
    for user_id, group in candidates.groupby("user_id"):
        selected = []
        remaining = group.sort_values("base_score", ascending=False).copy()
        while len(selected) < top_k and not remaining.empty:
            total = max(sum(global_counts.values()), 1)
            def score(row):
                current_share = global_counts.get(row.provider_group, 0) / total
                exposure_boost = max(0.0, target_share - current_share) * 0.30
                return float(row.base_score) + exposure_boost
            remaining = remaining.assign(rerank_score=remaining.apply(score, axis=1))
            best = remaining.sort_values(["rerank_score", "base_score"], ascending=False).iloc[0].to_dict()
            selected.append(best)
            global_counts[best["provider_group"]] = global_counts.get(best["provider_group"], 0) + 1
            remaining = remaining.loc[remaining["item_id"] != best["item_id"]]
        rows.extend(selected)
    return _finalize_rerank(pd.DataFrame(rows), "fairness_rerank")


def _finalize_rerank(frame: pd.DataFrame, method: str) -> pd.DataFrame:
    if frame.empty:
        return _empty_recommendations()
    frame = frame.copy()
    score_col = "rerank_score" if "rerank_score" in frame.columns else "base_score"
    frame["method"] = method
    frame["recommendation_score"] = frame[score_col].astype(float).clip(0, 1.2)
    frame = frame.sort_values(["user_id", "recommendation_score", "base_score"], ascending=[True, False, False])
    frame["rank"] = frame.groupby("user_id").cumcount() + 1
    return frame[_recommendation_columns()].sort_values(["method", "user_id", "rank"]).reset_index(drop=True)


def _recommendation_columns() -> list[str]:
    return [
        "method", "user_id", "user_group", "rank", "item_id", "creator_id", "provider_group", "category", "tags",
        "quality_score", "popularity_score", "popularity_percentile", "sensitive_topic_flag", "content_match_score",
        "collaborative_score", "base_score", "recommendation_score",
    ]


def _empty_recommendations() -> pd.DataFrame:
    return pd.DataFrame(columns=_recommendation_columns())
