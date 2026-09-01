"""Metrics, frozen validation threshold selection, and bootstrap intervals."""

from __future__ import annotations

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)


def optimal_balanced_accuracy_threshold(y_true: np.ndarray, probability: np.ndarray) -> float:
    candidates = np.unique(np.concatenate(([0.0], np.linspace(0.01, 0.99, 99), [1.0])))
    scores = np.array([
        balanced_accuracy_score(y_true, probability >= threshold) for threshold in candidates
    ])
    return float(candidates[int(np.argmax(scores))])


def binary_metrics(y_true: np.ndarray, probability: np.ndarray, threshold: float = 0.5) -> dict[str, float]:
    y = np.asarray(y_true, dtype=int)
    p = np.clip(np.asarray(probability, dtype=float), 1e-8, 1 - 1e-8)
    prediction = (p >= threshold).astype(int)
    return {
        "roc_auc": float(roc_auc_score(y, p)),
        "pr_auc": float(average_precision_score(y, p)),
        "balanced_accuracy": float(balanced_accuracy_score(y, prediction)),
        "f1": float(f1_score(y, prediction, zero_division=0)),
        "precision": float(precision_score(y, prediction, zero_division=0)),
        "recall": float(recall_score(y, prediction, zero_division=0)),
        "log_loss": float(log_loss(y, p, labels=[0, 1])),
        "brier_score": float(brier_score_loss(y, p)),
    }


def bootstrap_auc_intervals(
    y_true: np.ndarray,
    probability: np.ndarray,
    n_resamples: int = 500,
    seed: int = 42,
    confidence: float = 0.95,
) -> dict[str, float]:
    y = np.asarray(y_true, dtype=np.int8)
    p = np.asarray(probability, dtype=float)
    rng = np.random.default_rng(seed)
    positives = np.flatnonzero(y == 1)
    negatives = np.flatnonzero(y == 0)
    roc_values = np.empty(n_resamples, dtype=float)
    pr_values = np.empty(n_resamples, dtype=float)
    for index in range(n_resamples):
        sample = np.concatenate([
            rng.choice(positives, size=len(positives), replace=True),
            rng.choice(negatives, size=len(negatives), replace=True),
        ])
        sample_y = y[sample]
        sample_p = p[sample]
        roc_values[index] = roc_auc_score(sample_y, sample_p)
        pr_values[index] = average_precision_score(sample_y, sample_p)
    tail = (1.0 - confidence) / 2.0
    return {
        "roc_auc_ci_low": float(np.quantile(roc_values, tail)),
        "roc_auc_ci_high": float(np.quantile(roc_values, 1.0 - tail)),
        "pr_auc_ci_low": float(np.quantile(pr_values, tail)),
        "pr_auc_ci_high": float(np.quantile(pr_values, 1.0 - tail)),
        "bootstrap_resamples": int(n_resamples),
    }
