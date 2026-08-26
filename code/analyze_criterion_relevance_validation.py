"""Analyse independent human validation of revised SCIPRA criterion relevance.

Usage, first pass:
    python code/analyze_criterion_relevance_validation.py \
        --coder-a data/revision_validation/coder_a.csv \
        --coder-b data/revision_validation/coder_b.csv

After blinded adjudication:
    python code/analyze_criterion_relevance_validation.py \
        --coder-a data/revision_validation/coder_a.csv \
        --coder-b data/revision_validation/coder_b.csv \
        --adjudicated data/revision_validation/adjudicated.csv

The script never modifies the frozen audit/reconstruction layers.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "data" / "revision_validation"
DEFAULT_KEY = DEFAULT_OUT / "criterion_relevance_validation_key.csv"

BINARY = {"relevant": 1, "not relevant": 0}
ALLOWED = {"relevant", "not relevant", "uncertain"}


def read_csv(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows, fields=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = []
        for row in rows:
            for key in row:
                if key not in fields:
                    fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def norm_label(value: str) -> str:
    v = " ".join(str(value or "").strip().lower().replace("_", " ").split())
    aliases = {
        "yes": "relevant", "1": "relevant", "true": "relevant",
        "no": "not relevant", "0": "not relevant", "false": "not relevant",
        "not_relevant": "not relevant", "unsure": "uncertain", "?": "uncertain",
    }
    v = aliases.get(v, v)
    if v not in ALLOWED:
        raise ValueError(f"Invalid manual label: {value!r}")
    return v


def kappa_binary(pairs):
    """Cohen kappa for 0/1 pairs. Returns None when not estimable."""
    if not pairs:
        return None
    n = len(pairs)
    agree = sum(a == b for a, b in pairs) / n
    pa1 = sum(a == 1 for a, _ in pairs) / n
    pb1 = sum(b == 1 for _, b in pairs) / n
    pa0 = 1 - pa1
    pb0 = 1 - pb1
    expected = pa1 * pb1 + pa0 * pb0
    if math.isclose(1 - expected, 0.0):
        return None
    return (agree - expected) / (1 - expected)


def agreement_metrics(rows):
    total = len(rows)
    exact = sum(r["label_a"] == r["label_b"] for r in rows)
    binary_rows = [r for r in rows if r["label_a"] in BINARY and r["label_b"] in BINARY]
    pairs = [(BINARY[r["label_a"]], BINARY[r["label_b"]]) for r in binary_rows]
    return {
        "n_total": total,
        "exact_agreement": exact,
        "percent_agreement": exact / total if total else None,
        "n_binary_both": len(binary_rows),
        "cohen_kappa_binary": kappa_binary(pairs),
        "coder_a_uncertain": sum(r["label_a"] == "uncertain" for r in rows),
        "coder_b_uncertain": sum(r["label_b"] == "uncertain" for r in rows),
    }


def diagnostic_metrics(truth_pred_pairs):
    tp = sum(t == 1 and p == 1 for t, p in truth_pred_pairs)
    tn = sum(t == 0 and p == 0 for t, p in truth_pred_pairs)
    fp = sum(t == 0 and p == 1 for t, p in truth_pred_pairs)
    fn = sum(t == 1 and p == 0 for t, p in truth_pred_pairs)

    def div(a, b):
        return a / b if b else None

    sensitivity = div(tp, tp + fn)
    specificity = div(tn, tn + fp)
    precision = div(tp, tp + fp)
    npv = div(tn, tn + fn)
    accuracy = div(tp + tn, tp + tn + fp + fn)
    balanced = None if sensitivity is None or specificity is None else (sensitivity + specificity) / 2
    f1 = None if precision is None or sensitivity is None or (precision + sensitivity) == 0 else 2 * precision * sensitivity / (precision + sensitivity)
    return {
        "n": tp + tn + fp + fn,
        "tp": tp, "tn": tn, "fp": fp, "fn": fn,
        "accuracy": accuracy,
        "sensitivity_recall": sensitivity,
        "specificity": specificity,
        "precision_ppv": precision,
        "negative_predictive_value": npv,
        "balanced_accuracy": balanced,
        "f1": f1,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--coder-a", required=True, type=Path)
    parser.add_argument("--coder-b", required=True, type=Path)
    parser.add_argument("--adjudicated", type=Path, default=None)
    parser.add_argument("--key", type=Path, default=DEFAULT_KEY)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    a_rows = read_csv(args.coder_a)
    b_rows = read_csv(args.coder_b)
    a = {r["decision_id"]: r for r in a_rows}
    b = {r["decision_id"]: r for r in b_rows}
    if set(a) != set(b):
        raise RuntimeError("Coder files do not contain identical decision_id sets")

    merged = []
    for did in sorted(a):
        ra, rb = a[did], b[did]
        la, lb = norm_label(ra.get("manual_label", "")), norm_label(rb.get("manual_label", ""))
        merged.append({
            "decision_id": did,
            "sample_document_id": ra.get("sample_document_id", ""),
            "record_id": ra.get("record_id", ""),
            "criterion": ra.get("criterion", ""),
            "title": ra.get("title", ""),
            "url": ra.get("url", ""),
            "label_a": la,
            "confidence_a": ra.get("confidence_1_to_3", ""),
            "rationale_a": ra.get("rationale", ""),
            "label_b": lb,
            "confidence_b": rb.get("confidence_1_to_3", ""),
            "rationale_b": rb.get("rationale", ""),
        })

    overall = agreement_metrics(merged)
    by_criterion = []
    for criterion in sorted({r["criterion"] for r in merged}):
        subset = [r for r in merged if r["criterion"] == criterion]
        by_criterion.append({"scope": "criterion", "criterion": criterion, **agreement_metrics(subset)})

    agreement_rows = [{"scope": "overall", "criterion": "ALL", **overall}] + by_criterion
    write_csv(args.out_dir / "criterion_relevance_validation_agreement.csv", agreement_rows)

    disagreements = []
    for r in merged:
        if r["label_a"] != r["label_b"] or "uncertain" in (r["label_a"], r["label_b"]):
            disagreements.append({
                **r,
                "adjudicated_label": "",
                "adjudication_rationale": "",
            })
    write_csv(args.out_dir / "criterion_relevance_validation_disagreements_for_adjudication.csv", disagreements)

    summary = {
        "stage": "criterion_relevance_human_validation_first_pass",
        "overall_agreement": overall,
        "criterion_agreement": by_criterion,
        "disagreements_or_uncertain": len(disagreements),
        "automated_diagnostics_completed": False,
    }

    if args.adjudicated is not None:
        adjud_rows = read_csv(args.adjudicated)
        adjud = {r["decision_id"]: r for r in adjud_rows}
        key_rows = read_csv(args.key)
        key = {r["decision_id"]: r for r in key_rows}
        if set(adjud) != set(a):
            raise RuntimeError("Adjudicated file must contain all sampled decision_id values")
        if set(key) != set(a):
            raise RuntimeError("Validation key must contain all sampled decision_id values")

        eval_rows = []
        for did in sorted(a):
            manual = norm_label(adjud[did].get("adjudicated_label", ""))
            if manual == "uncertain":
                continue
            truth = BINARY[manual]
            auto = 1 if str(key[did]["automated_primary_relevant"]).lower() == "true" else 0
            eval_rows.append({
                "decision_id": did,
                "criterion": key[did]["criterion"],
                "stakeholder_group": key[did]["stakeholder_group"],
                "manual_reference": truth,
                "automated_prediction": auto,
            })

        diagnostics = []
        pairs = [(r["manual_reference"], r["automated_prediction"]) for r in eval_rows]
        diagnostics.append({"scope": "overall", "group": "ALL", "criterion": "ALL", **diagnostic_metrics(pairs)})

        for criterion in sorted({r["criterion"] for r in eval_rows}):
            sub = [r for r in eval_rows if r["criterion"] == criterion]
            diagnostics.append({
                "scope": "criterion", "group": "ALL", "criterion": criterion,
                **diagnostic_metrics([(r["manual_reference"], r["automated_prediction"]) for r in sub])
            })

        # Exploratory only: smaller cells.
        for group in sorted({r["stakeholder_group"] for r in eval_rows}):
            sub = [r for r in eval_rows if r["stakeholder_group"] == group]
            diagnostics.append({
                "scope": "stakeholder_exploratory", "group": group, "criterion": "ALL",
                **diagnostic_metrics([(r["manual_reference"], r["automated_prediction"]) for r in sub])
            })

        write_csv(args.out_dir / "criterion_relevance_validation_diagnostics.csv", diagnostics)
        summary.update({
            "automated_diagnostics_completed": True,
            "adjudicated_binary_cases": len(eval_rows),
            "automated_diagnostics": diagnostics,
            "interpretation_note": (
                "Pooled performance must not be used to conceal criterion-level failure. Local Employment requires explicit review."
            ),
        })

    (args.out_dir / "criterion_relevance_validation_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
