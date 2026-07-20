"""Explainability utilities for recommender outputs."""

from __future__ import annotations

import numpy as np
import pandas as pd


def add_explanations(recommendations: pd.DataFrame) -> pd.DataFrame:
    """Attach transparent text explanations to recommendations."""
    if recommendations.empty:
        return pd.DataFrame(columns=list(recommendations.columns) + ["explanation", "reason_count", "has_explanation", "explanation_quality_proxy"])
    rows = []
    for row in recommendations.itertuples(index=False):
        reasons = []
        if float(row.content_match_score) >= 0.45:
            reasons.append("matches user interaction interests")
        if float(row.quality_score) >= 0.70:
            reasons.append("has high synthetic quality score")
        if float(row.popularity_percentile) >= 0.75:
            reasons.append("is broadly popular")
        if row.method in {"diversity_rerank", "fairness_rerank"}:
            reasons.append("included to improve diversity or exposure balance")
        if int(row.sensitive_topic_flag) == 1:
            reasons.append("sensitive-topic review recommended")
        if not reasons:
            reasons.append("selected by baseline ranking score")
        reason_count = len(reasons)
        quality = float(np.clip(0.20 + 0.18 * min(reason_count, 4) + 0.25 * float(row.content_match_score) + 0.15 * float(row.quality_score) - 0.10 * int(row.sensitive_topic_flag), 0, 1))
        data = row._asdict()
        data.update({
            "explanation": "; ".join(reasons) + ".",
            "reason_count": reason_count,
            "has_explanation": 1,
            "explanation_quality_proxy": round(quality, 4),
        })
        rows.append(data)
    return pd.DataFrame(rows)


def explanation_audit(explanations: pd.DataFrame) -> pd.DataFrame:
    """Summarize explanation availability and quality by algorithm."""
    if explanations.empty:
        return pd.DataFrame(columns=["method", "explanation_coverage", "mean_reason_count", "mean_explanation_quality_proxy", "sensitive_topic_review_share"])
    return explanations.groupby("method").agg(
        explanation_coverage=("has_explanation", "mean"),
        mean_reason_count=("reason_count", "mean"),
        mean_explanation_quality_proxy=("explanation_quality_proxy", "mean"),
        sensitive_topic_review_share=("sensitive_topic_flag", "mean"),
    ).reset_index().sort_values("method")
