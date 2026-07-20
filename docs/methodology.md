# Methodology

This lab compares transparent recommender baselines and rerankers on synthetic data.

## Synthetic data

The generator creates fictional users, items, providers, creators, item categories, tags, quality scores, popularity seeds, and historical interactions. Large providers receive a small synthetic popularity advantage so exposure concentration can be measured.

## Algorithms

1. **Popularity baseline** ranks by interaction-derived popularity and item quality.
2. **Content-based baseline** uses user interaction history, category/tag matches, item quality, and popularity.
3. **Collaborative-style similarity baseline** uses similar-user liked-item overlap.
4. **Diversity reranker** reorders content-based candidates to increase category and provider variety.
5. **Fairness reranker** reorders content-based candidates to reduce provider exposure imbalance.

## Evaluation

The local pipeline computes:

- relevance proxy
- popularity bias
- top-decile exposure share
- catalog coverage
- provider exposure gap
- category and provider entropy
- filter-bubble score
- explanation quality proxy
- trust proxy score

These metrics are diagnostic. They do not determine real-world platform policy.
