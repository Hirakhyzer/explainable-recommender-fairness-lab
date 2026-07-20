"""Local plotting helpers for recommender fairness experiments."""

from __future__ import annotations

from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd


def _save(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def plot_algorithm_relevance(comparison: pd.DataFrame, path: str | Path) -> None:
    frame = comparison.sort_values("mean_relevance_proxy")
    plt.figure(figsize=(9, 4.8))
    plt.barh(frame["method"], frame["mean_relevance_proxy"])
    plt.xlabel("Mean relevance proxy")
    plt.title("Relevance proxy by recommender method")
    _save(path)


def plot_exposure_fairness(fairness: pd.DataFrame, path: str | Path) -> None:
    frame = fairness.groupby("method", as_index=False)["absolute_exposure_gap"].mean().sort_values("absolute_exposure_gap")
    plt.figure(figsize=(9, 4.8))
    plt.barh(frame["method"], frame["absolute_exposure_gap"])
    plt.xlabel("Mean absolute provider exposure gap")
    plt.title("Exposure fairness by method")
    _save(path)


def plot_filter_bubble_risk(bubbles: pd.DataFrame, path: str | Path) -> None:
    frame = bubbles.groupby("method", as_index=False)["filter_bubble_score"].mean().sort_values("filter_bubble_score")
    plt.figure(figsize=(9, 4.8))
    plt.barh(frame["method"], frame["filter_bubble_score"])
    plt.xlabel("Mean filter-bubble score")
    plt.title("Filter-bubble risk by method")
    _save(path)


def plot_provider_exposure(fairness: pd.DataFrame, path: str | Path) -> None:
    pivot = fairness.pivot(index="provider_group", columns="method", values="exposure_share").fillna(0)
    plt.figure(figsize=(10, 5))
    pivot.plot(kind="bar", ax=plt.gca())
    plt.ylabel("Exposure share")
    plt.title("Provider exposure share by method")
    plt.xticks(rotation=30, ha="right")
    _save(path)


def plot_trust_proxy(trust: pd.DataFrame, path: str | Path) -> None:
    frame = trust.groupby("method", as_index=False)["trust_proxy_score"].mean().sort_values("trust_proxy_score")
    plt.figure(figsize=(9, 4.8))
    plt.barh(frame["method"], frame["trust_proxy_score"])
    plt.xlabel("Mean trust proxy score")
    plt.title("Trust proxy by method")
    _save(path)
