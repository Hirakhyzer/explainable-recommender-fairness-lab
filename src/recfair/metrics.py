"""Relevance, diversity, exposure, filter-bubble, and trust-proxy metrics."""

from __future__ import annotations

import math
import numpy as np
import pandas as pd


def algorithm_comparison(recommendations: pd.DataFrame, items: pd.DataFrame) -> pd.DataFrame:
    """Return compact algorithm-level comparison metrics."""
    rows = []
    for method, group in recommendations.groupby("method"):
        user_div = filter_bubble_report(group)
        exposure = exposure_distribution(group)
        rows.append({
            "method": method,
            "recommendation_count": int(len(group)),
            "mean_relevance_proxy": float(group["base_score"].mean()) if len(group) else 0.0,
            "mean_quality_score": float(group["quality_score"].mean()) if len(group) else 0.0,
            "mean_popularity_percentile": float(group["popularity_percentile"].mean()) if len(group) else 0.0,
            "top_decile_exposure_share": float((group["popularity_percentile"] >= 0.90).mean()) if len(group) else 0.0,
            "catalog_coverage": float(group["item_id"].nunique() / max(items["item_id"].nunique(), 1)),
            "mean_category_entropy": float(user_div["category_entropy"].mean()) if len(user_div) else 0.0,
            "mean_provider_entropy": float(user_div["provider_entropy"].mean()) if len(user_div) else 0.0,
            "filter_bubble_risk_rate": float(user_div["filter_bubble_risk"].mean()) if len(user_div) else 0.0,
            "provider_exposure_gap": float(exposure["exposure_share"].max() - exposure["exposure_share"].min()) if len(exposure) else 0.0,
        })
    return pd.DataFrame(rows).sort_values("method").reset_index(drop=True)


def exposure_distribution(recommendations: pd.DataFrame) -> pd.DataFrame:
    """Compute provider exposure share by algorithm."""
    if recommendations.empty:
        return pd.DataFrame(columns=["method", "provider_group", "exposures", "exposure_share"])
    rows = []
    for method, group in recommendations.groupby("method"):
        total = max(len(group), 1)
        counts = group["provider_group"].value_counts().to_dict()
        for provider in sorted(group["provider_group"].unique()):
            exposures = int(counts.get(provider, 0))
            rows.append({"method": method, "provider_group": provider, "exposures": exposures, "exposure_share": exposures / total})
    return pd.DataFrame(rows)


def filter_bubble_report(recommendations: pd.DataFrame) -> pd.DataFrame:
    """Estimate per-user filter-bubble risk from category/provider concentration."""
    rows = []
    for (method, user_id), group in recommendations.groupby(["method", "user_id"]):
        category_entropy = _normalized_entropy(group["category"].tolist())
        provider_entropy = _normalized_entropy(group["provider_group"].tolist())
        top_category_share = float(group["category"].value_counts(normalize=True).iloc[0]) if len(group) else 0.0
        top_provider_share = float(group["provider_group"].value_counts(normalize=True).iloc[0]) if len(group) else 0.0
        bubble_score = float(np.clip(0.45 * (1 - category_entropy) + 0.25 * (1 - provider_entropy) + 0.30 * max(top_category_share, top_provider_share), 0, 1))
        rows.append({
            "method": method,
            "user_id": user_id,
            "user_group": group["user_group"].iloc[0],
            "category_entropy": round(category_entropy, 4),
            "provider_entropy": round(provider_entropy, 4),
            "dominant_category_share": round(top_category_share, 4),
            "dominant_provider_share": round(top_provider_share, 4),
            "filter_bubble_score": round(bubble_score, 4),
            "filter_bubble_risk": int(bubble_score >= 0.68),
        })
    return pd.DataFrame(rows)


def user_trust_audit(recommendations: pd.DataFrame, explanations: pd.DataFrame) -> pd.DataFrame:
    """Compute user-level trust proxy from relevance, diversity, explanation quality, and sensitive topic risk."""
    bubbles = filter_bubble_report(recommendations)
    exp = explanations.groupby(["method", "user_id"], as_index=False).agg(
        explanation_quality_proxy=("explanation_quality_proxy", "mean"),
        explanation_coverage=("has_explanation", "mean"),
    )
    rec = recommendations.groupby(["method", "user_id"], as_index=False).agg(
        relevance_proxy=("base_score", "mean"),
        sensitive_topic_share=("sensitive_topic_flag", "mean"),
    )
    out = rec.merge(bubbles, on=["method", "user_id"], how="left").merge(exp, on=["method", "user_id"], how="left")
    out["explanation_quality_proxy"] = out["explanation_quality_proxy"].fillna(0.0)
    out["explanation_coverage"] = out["explanation_coverage"].fillna(0.0)
    out["trust_proxy_score"] = np.clip(
        0.34 * out["relevance_proxy"]
        + 0.24 * out["explanation_quality_proxy"]
        + 0.18 * out["category_entropy"].fillna(0.0)
        + 0.14 * out["provider_entropy"].fillna(0.0)
        + 0.10 * (1 - out["sensitive_topic_share"].fillna(0.0)),
        0,
        1,
    )
    out["trust_risk_flag"] = (out["trust_proxy_score"] < 0.45).astype(int)
    return out.sort_values(["trust_proxy_score", "filter_bubble_score"]).reset_index(drop=True)


def _normalized_entropy(values: list[str]) -> float:
    if not values:
        return 0.0
    counts = pd.Series(values).value_counts(normalize=True)
    entropy = float(-(counts * np.log2(counts)).sum())
    max_entropy = math.log2(len(counts)) if len(counts) > 1 else 1.0
    return float(np.clip(entropy / max_entropy, 0, 1))


def summary_metrics(comparison: pd.DataFrame, fairness: pd.DataFrame, bubbles: pd.DataFrame, trust: pd.DataFrame) -> dict[str, float | int | str]:
    """Compact run summary for JSON and audit logs."""
    return {
        "method_count": int(comparison["method"].nunique()) if len(comparison) else 0,
        "best_mean_relevance_method": str(comparison.sort_values("mean_relevance_proxy", ascending=False)["method"].iloc[0]) if len(comparison) else "none",
        "lowest_exposure_gap_method": str(comparison.sort_values("provider_exposure_gap")["method"].iloc[0]) if len(comparison) else "none",
        "mean_filter_bubble_risk_rate": float(bubbles["filter_bubble_risk"].mean()) if len(bubbles) else 0.0,
        "mean_trust_proxy_score": float(trust["trust_proxy_score"].mean()) if len(trust) else 0.0,
        "largest_provider_exposure_gap": float(fairness["provider_exposure_gap"].max()) if len(fairness) else 0.0,
        "data_origin": "synthetic fictional recommender records",
        "decision_boundary": "research review support only; not automatic creator or user ranking",
    }
