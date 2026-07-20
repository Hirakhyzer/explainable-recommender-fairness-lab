"""Provider and subgroup fairness audits for recommender outputs."""

from __future__ import annotations

import numpy as np
import pandas as pd


def provider_exposure_fairness(recommendations: pd.DataFrame, items: pd.DataFrame) -> pd.DataFrame:
    """Compare recommendation exposure share with catalog provider share."""
    catalog_share = items["provider_group"].value_counts(normalize=True).rename("catalog_share").reset_index().rename(columns={"index": "provider_group"})
    rows = []
    for method, group in recommendations.groupby("method"):
        exposure_share = group["provider_group"].value_counts(normalize=True).rename("exposure_share").reset_index().rename(columns={"index": "provider_group"})
        merged = catalog_share.merge(exposure_share, on="provider_group", how="left")
        merged["exposure_share"] = merged["exposure_share"].fillna(0.0)
        merged["method"] = method
        merged["exposure_gap_vs_catalog"] = merged["exposure_share"] - merged["catalog_share"]
        merged["absolute_exposure_gap"] = merged["exposure_gap_vs_catalog"].abs()
        gap = float(merged["exposure_share"].max() - merged["exposure_share"].min()) if len(merged) else 0.0
        merged["provider_exposure_gap"] = gap
        merged["underexposed_flag"] = (merged["exposure_gap_vs_catalog"] < -0.05).astype(int)
        rows.append(merged[["method", "provider_group", "catalog_share", "exposure_share", "exposure_gap_vs_catalog", "absolute_exposure_gap", "provider_exposure_gap", "underexposed_flag"]])
    return pd.concat(rows, ignore_index=True).sort_values(["method", "provider_group"]).reset_index(drop=True) if rows else pd.DataFrame()


def subgroup_recommendation_audit(recommendations: pd.DataFrame) -> pd.DataFrame:
    """Audit user-group access to diverse, explainable, and less concentrated recommendations."""
    if recommendations.empty:
        return pd.DataFrame(columns=["method", "user_group", "mean_relevance_proxy", "mean_popularity_percentile", "category_diversity", "provider_diversity", "sensitive_topic_share"])
    rows = []
    for (method, user_group), group in recommendations.groupby(["method", "user_group"]):
        rows.append({
            "method": method,
            "user_group": user_group,
            "mean_relevance_proxy": float(group["base_score"].mean()),
            "mean_popularity_percentile": float(group["popularity_percentile"].mean()),
            "category_diversity": int(group["category"].nunique()),
            "provider_diversity": int(group["provider_group"].nunique()),
            "sensitive_topic_share": float(group["sensitive_topic_flag"].mean()),
        })
    out = pd.DataFrame(rows)
    method_gap = out.groupby("method").agg(
        subgroup_relevance_gap=("mean_relevance_proxy", lambda s: float(s.max() - s.min())),
        subgroup_popularity_gap=("mean_popularity_percentile", lambda s: float(s.max() - s.min())),
    ).reset_index()
    return out.merge(method_gap, on="method", how="left").sort_values(["method", "user_group"]).reset_index(drop=True)


def fairness_summary(provider_fairness: pd.DataFrame, subgroup_audit: pd.DataFrame) -> dict[str, float | int | str]:
    """Compact fairness summary."""
    return {
        "mean_absolute_provider_exposure_gap": float(provider_fairness["absolute_exposure_gap"].mean()) if len(provider_fairness) else 0.0,
        "underexposed_provider_rows": int(provider_fairness["underexposed_flag"].sum()) if len(provider_fairness) else 0,
        "max_subgroup_relevance_gap": float(subgroup_audit["subgroup_relevance_gap"].max()) if len(subgroup_audit) else 0.0,
        "max_subgroup_popularity_gap": float(subgroup_audit["subgroup_popularity_gap"].max()) if len(subgroup_audit) else 0.0,
    }
