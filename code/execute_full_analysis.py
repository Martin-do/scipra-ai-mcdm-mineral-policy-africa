"""End-to-end SCIPRA NLP-SVM and PCI/RPCI analysis.

This script is intentionally strict about corpus provenance. The manuscript
reports an 87-document Marikana corpus. By default, execution stops if the
repository does not contain 87 matched corpus records rather than printing
results under an incorrect N=87 label.

Use --allow-partial only for diagnostic/exploratory runs on an incomplete
corpus. Results from partial runs must not be reported as manuscript
replications.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC

from pci_computation import DomainScores, pci, pci_nonlinear, rpci


EXPECTED_CORPUS_SIZE = 87
RANDOM_STATE = 42
REPO_ROOT = Path(__file__).resolve().parents[1]
MASTER_PATH = REPO_ROOT / "data" / "processed" / "corpus_master.csv"
MANIFEST_PATH = REPO_ROOT / "data" / "processed" / "corpus_manifest.csv"


SIC = {
    "government": 0.703,
    "investor": 0.770,
    "community": 0.749,
    "labour": 0.807,
    "NGO": 0.686,
}


def load_corpus() -> pd.DataFrame:
    """Load and join processed corpus text to its documented manifest."""
    if not MASTER_PATH.exists():
        raise FileNotFoundError(f"Missing processed corpus: {MASTER_PATH}")
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Missing corpus manifest: {MANIFEST_PATH}")

    master_df = pd.read_csv(MASTER_PATH)
    manifest_df = pd.read_csv(MANIFEST_PATH)

    required_master = {"filename", "text"}
    required_manifest = {"doc_id", "filename", "stakeholder_group", "stance_label"}
    missing_master = required_master.difference(master_df.columns)
    missing_manifest = required_manifest.difference(manifest_df.columns)
    if missing_master:
        raise ValueError(f"corpus_master.csv missing columns: {sorted(missing_master)}")
    if missing_manifest:
        raise ValueError(f"corpus_manifest.csv missing columns: {sorted(missing_manifest)}")

    if master_df["filename"].duplicated().any():
        duplicates = master_df.loc[master_df["filename"].duplicated(), "filename"].tolist()
        raise ValueError(f"Duplicate filenames in corpus_master.csv: {duplicates}")
    if manifest_df["filename"].duplicated().any():
        duplicates = manifest_df.loc[manifest_df["filename"].duplicated(), "filename"].tolist()
        raise ValueError(f"Duplicate filenames in corpus_manifest.csv: {duplicates}")

    df = manifest_df.merge(
        master_df[["filename", "text"]],
        on="filename",
        how="inner",
        validate="one_to_one",
    )
    df = df.dropna(subset=["text", "stance_label", "stakeholder_group"]).copy()
    df["stance_label"] = df["stance_label"].astype(int)

    print(f"Processed corpus rows: {len(master_df)}")
    print(f"Manifest rows:         {len(manifest_df)}")
    print(f"Matched usable rows:   {len(df)}")

    unmatched_manifest = sorted(set(manifest_df["filename"]) - set(master_df["filename"]))
    unmatched_master = sorted(set(master_df["filename"]) - set(manifest_df["filename"]))
    if unmatched_manifest:
        print(f"WARNING: {len(unmatched_manifest)} manifest records have no processed text.")
    if unmatched_master:
        print(f"WARNING: {len(unmatched_master)} processed files have no manifest record.")

    return df


def build_model() -> Pipeline:
    """Build a leakage-safe TF-IDF + RBF-SVM pipeline.

    TF-IDF is inside the sklearn Pipeline so vocabulary and IDF statistics are
    learned independently within each training fold during cross-validation.
    """
    return Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    max_features=500,
                    ngram_range=(1, 2),
                    min_df=2,
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
                    probability=True,
                    class_weight="balanced",
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )


def run_analysis(*, allow_partial: bool = False) -> None:
    df = load_corpus()
    n_docs = len(df)

    if n_docs != EXPECTED_CORPUS_SIZE and not allow_partial:
        raise RuntimeError(
            f"Manuscript replication requires {EXPECTED_CORPUS_SIZE} matched documents, "
            f"but this repository currently provides {n_docs}. "
            "Execution stopped to avoid reporting an incomplete corpus as N=87. "
            "Use --allow-partial only for diagnostics."
        )

    y = df["stance_label"].to_numpy(dtype=int)
    class_counts = np.bincount(y)
    nonzero_counts = class_counts[class_counts > 0]
    if len(nonzero_counts) < 2:
        raise RuntimeError("Both stance classes are required for stratified cross-validation.")

    min_class = int(nonzero_counts.min())
    n_splits = min(5, min_class)
    if n_splits < 2:
        raise RuntimeError("At least two observations per class are required for CV.")

    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)
    model = build_model()

    # Out-of-fold probabilities. Because TF-IDF is inside the Pipeline, each
    # fold learns its vocabulary/IDF values from training documents only.
    prob_matrix = cross_val_predict(
        model,
        df["text"].astype(str).to_numpy(),
        y,
        cv=cv,
        method="predict_proba",
    )
    df["prob_pro"] = prob_matrix[:, 1]

    # Fit once on all available data only after out-of-fold predictions exist.
    model.fit(df["text"].astype(str).to_numpy(), y)

    group_stats = df.groupby("stakeholder_group")["prob_pro"].mean().to_dict()

    # Manuscript/SI mapping: investor acceptance -> I_score; government
    # acceptance -> R_score; SIC-weighted mean across all five groups -> S_score.
    missing_groups = [g for g in SIC if g not in group_stats]
    if missing_groups:
        raise RuntimeError(
            "Cannot compute manuscript domain mapping because these stakeholder "
            f"groups have no matched documents: {missing_groups}"
        )

    val_i = group_stats["investor"]
    val_r = group_stats["government"]
    val_s = sum(SIC[g] * group_stats[g] for g in SIC) / sum(SIC.values())

    final_scores = DomainScores(
        investment=val_i,
        regulatory=val_r,
        stakeholder=val_s,
    )

    res_pci = pci(final_scores)
    res_nl = pci_nonlinear(final_scores)
    res_rpci = rpci(final_scores)

    run_label = "FULL MANUSCRIPT CORPUS" if n_docs == EXPECTED_CORPUS_SIZE else "PARTIAL DIAGNOSTIC CORPUS"
    print("\n" + "=" * 62)
    print(f"SCIPRA {run_label} RESULTS (N={n_docs})")
    print("=" * 62)
    if n_docs != EXPECTED_CORPUS_SIZE:
        print("WARNING: These values are NOT manuscript replication results.")
    print(f"Cross-validation folds: {n_splits}")
    print("Domain Scores:")
    print(f"  Investment (I) : {val_i:.4f}")
    print(f"  Regulatory (R) : {val_r:.4f}")
    print(f"  Stakeholder(S) : {val_s:.4f}")
    print("-" * 62)
    print("Index Results:")
    print(f"  Linear PCI     : {res_pci:.4f}")
    print(f"  Non-Linear PCI : {res_nl:.4f}")
    print(f"  Normalized RPCI: {res_rpci:.4f}")
    print("=" * 62)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="Run on an incomplete corpus for diagnostics only.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_analysis(allow_partial=args.allow_partial)
