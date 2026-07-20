"""Markdown report writer for recommender fairness experiments."""

from __future__ import annotations

from pathlib import Path
import pandas as pd


def write_report(
    path: str | Path,
    summary: dict,
    comparison: pd.DataFrame,
    fairness: pd.DataFrame,
    bubbles: pd.DataFrame,
    explanation_audit: pd.DataFrame,
    trust: pd.DataFrame,
) -> None:
    """Write a compact advisor/research report."""
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    high_bubble = bubbles.sort_values("filter_bubble_score", ascending=False).head(10) if not bubbles.empty else bubbles
    low_trust = trust.sort_values("trust_proxy_score").head(10) if not trust.empty else trust
    content = f"""# Synthetic Recommender Fairness Report

## Boundary

This report uses synthetic fictional recommendation records. It is for research and review support only, not automatic real-world ranking, suppression, or creator/user decision-making.

## Summary

| Metric | Value |
| --- | ---: |
| Methods evaluated | {summary.get('method_count', 0)} |
| Best mean relevance method | {summary.get('best_mean_relevance_method', 'none')} |
| Lowest exposure gap method | {summary.get('lowest_exposure_gap_method', 'none')} |
| Mean filter-bubble risk rate | {summary.get('mean_filter_bubble_risk_rate', 0):.3f} |
| Mean trust proxy score | {summary.get('mean_trust_proxy_score', 0):.3f} |
| Largest provider exposure gap | {summary.get('largest_provider_exposure_gap', 0):.3f} |

## Algorithm comparison

{comparison.to_markdown(index=False) if not comparison.empty else 'No comparison rows generated.'}

## Provider exposure fairness

{fairness.to_markdown(index=False) if not fairness.empty else 'No fairness rows generated.'}

## Explanation audit

{explanation_audit.to_markdown(index=False) if not explanation_audit.empty else 'No explanation audit rows generated.'}

## Highest filter-bubble risk users

{high_bubble.to_markdown(index=False) if not high_bubble.empty else 'No filter-bubble rows generated.'}

## Lowest trust proxy users

{low_trust.to_markdown(index=False) if not low_trust.empty else 'No trust rows generated.'}

## Governance notes

- Treat relevance, fairness, filter-bubble, and trust values as diagnostic signals, not final policy decisions.
- Investigate under-exposed provider groups and high filter-bubble users with qualitative review.
- Do not infer sensitive traits or apply high-stakes decisions from this synthetic pipeline.
- Real deployments need privacy review, provider appeals, user controls, and continuous monitoring.
"""
    report_path.write_text(content, encoding="utf-8")
