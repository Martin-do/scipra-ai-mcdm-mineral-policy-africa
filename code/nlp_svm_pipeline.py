"""NLP–SVM utilities for SCIPRA stakeholder stance classification.

The public functions in this module use an sklearn Pipeline so TF-IDF fitting
occurs inside each cross-validation fold. This prevents held-out documents from
influencing vocabulary selection or IDF statistics.

The small example in ``__main__`` is demonstrative only and must not be treated
as a reproduction of the manuscript's reported 87-document results.
"""

from __future__ import annotations

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


RANDOM_STATE = 42


def build_pipeline(*, min_df: int = 2) -> Pipeline:
    """Construct the leakage-safe TF-IDF + RBF-SVM classifier."""
    return Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    max_features=500,
                    ngram_range=(1, 2),
                    min_df=min_df,
                    max_df=0.90,
                    sublinear_tf=True,
                    norm="l2",
                ),
            ),
            (
                "svm",
                SVC(
                    kernel="rbf",
                    C=1.0,
                    gamma="scale",
                    class_weight="balanced",
                    probability=True,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )


def cross_validate_svm(corpus: list[str], labels: np.ndarray):
    """Run stratified CV with preprocessing fitted within each training fold."""
    y = np.asarray(labels, dtype=int)
    counts = np.bincount(y)
    nonzero = counts[counts > 0]
    if len(nonzero) < 2:
        raise ValueError("Both stance classes are required for classification.")

    min_class_size = int(nonzero.min())
    n_splits = min(5, min_class_size)
    if n_splits < 2:
        raise ValueError("At least two observations per class are required for CV.")

    # min_df=2 is the manuscript configuration for the full corpus. Very small
    # demonstrative corpora use min_df=1 so the toy example remains runnable.
    min_df = 2 if len(corpus) >= 20 else 1
    model = build_pipeline(min_df=min_df)
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)
    metrics = cross_validate(
        model,
        np.asarray(corpus, dtype=object),
        y,
        cv=cv,
        scoring=["accuracy", "precision", "recall", "f1", "roc_auc"],
        error_score="raise",
    )
    model.fit(np.asarray(corpus, dtype=object), y)
    return model, metrics


def vader_urgency_adjustment(text: str, raw_urgency: float, ceiling: float = 0.10) -> float:
    """Apply the manuscript's bounded VADER urgency adjustment."""
    analyzer = SentimentIntensityAnalyzer()
    compound = analyzer.polarity_scores(text)["compound"]
    return float(np.clip(raw_urgency + ceiling * compound, 0.0, 1.0))


if __name__ == "__main__":
    corpus = [
        "community rights consent and participation",
        "strike crisis protest and urgent displacement",
        "regulatory compliance and transparency improved",
        "investment capital and authority mandate",
        "environmental impact and accountability",
        "community consent and legal recognition improved",
    ]
    labels = np.array([1, 0, 1, 1, 0, 1])

    _, metrics = cross_validate_svm(corpus, labels)
    print("DEMONSTRATION ONLY — not manuscript reproduction")
    print("CV metrics:", {k: v.tolist() for k, v in metrics.items()})
