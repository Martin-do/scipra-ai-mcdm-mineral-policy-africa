"""Build the blinded independent-validation sample for revised SCIPRA A_sj.

Revision-validation layer only. This script does not modify the frozen corpus,
historical audit, or prior criterion-relevance outputs.

Sampling is pre-specified and locked before human coding. The automated
primary relevance label is used only to obtain diagnostic coverage and is
never written to the blinded coder file.
"""
from __future__ import annotations

import csv
import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REV = ROOT / "data" / "revision_analysis"
PF = ROOT / "data" / "post_freeze_analysis"
OUT = ROOT / "data" / "revision_validation"

AUDIT = REV / "criterion_relevance_document_audit.csv"
STAKE = PF / "reconstructed_stakeholder_attribution_final.csv"

SEED = 20260826
TARGET_PER_STAKEHOLDER = 12
STAKEHOLDERS = ["government", "investor", "community", "labour", "NGO"]
CRITERIA = [
    "NPV",
    "IRR",
    "Geological Feasibility",
    "Market Stability",
    "Local Employment",
    "Community Infrastructure",
]
PRIMARY_FIELD = "relevant_s2_f2"

DEFINITIONS = {
    "NPV": (
        "Substantive discussion of project/investment valuation through present-value logic, "
        "discounted future cash flows, capital-investment value, or an equivalent project-value "
        "concept. Generic money/cost/revenue references do not qualify unless tied to investment valuation."
    ),
    "IRR": (
        "Substantive discussion of an investment return rate, rate-of-return/profitability criterion, "
        "return on investment, or an equivalent return-performance concept. Generic profit/revenue "
        "language without an investment-return concept does not automatically qualify."
    ),
    "Geological Feasibility": (
        "Substantive discussion of the mineral deposit or mine's geological/technical resource basis, "
        "including orebody characteristics, reserves/resources, ore grade, mine life, resource base, "
        "or geological/mining feasibility."
    ),
    "Market Stability": (
        "Substantive discussion of commodity/platinum market conditions affecting project viability, "
        "including prices, demand, supply, volatility, stability, or commodity-market conditions."
    ),
    "Local Employment": (
        "Substantive discussion of employment opportunities, employment creation/retention/loss, local "
        "hiring, workforce numbers, retrenchment/layoffs, or availability of jobs for local/affected people. "
        "Workers, labour disputes, unions, strikes, wages, or mineworkers alone do not qualify unless the "
        "document substantively concerns employment quantity, availability, creation, retention, loss, or local hiring."
    ),
    "Community Infrastructure": (
        "Substantive discussion of physical or social infrastructure/services for affected communities, "
        "including housing/accommodation, schools, clinics/healthcare facilities, roads, water, sanitation, "
        "electricity, community facilities/development infrastructure, or infrastructure commitments under an SLP."
    ),
}


def read_csv(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_bool(value: str) -> bool:
    return str(value).strip().lower() == "true"


def build_candidates(audit_rows):
    by_record = defaultdict(dict)
    group_by_record = {}
    for r in audit_rows:
        rid = r["record_id"]
        criterion = r["criterion"]
        if criterion not in CRITERIA:
            continue
        group_by_record[rid] = r["stakeholder_group"]
        by_record[rid][criterion] = r

    candidates = []
    for rid, rows in by_record.items():
        if set(rows) != set(CRITERIA):
            continue
        group = group_by_record[rid]
        if group not in STAKEHOLDERS:
            continue
        vector = tuple(parse_bool(rows[c][PRIMARY_FIELD]) for c in CRITERIA)
        candidates.append({"record_id": rid, "stakeholder_group": group, "rows": rows, "vector": vector})
    return candidates


def select_group(group_candidates, target, rng):
    """Greedy deterministic diversity selection over six binary relevance outcomes."""
    pool = list(group_candidates)
    rng.shuffle(pool)  # deterministic tie order
    rank = {c["record_id"]: i for i, c in enumerate(pool)}
    selected = []
    outcome_counts = Counter()
    profile_counts = Counter()

    while pool and len(selected) < target:
        best = None
        best_score = None
        for cand in pool:
            score = 0.0
            for criterion, label in zip(CRITERIA, cand["vector"]):
                # Strongly prefer underrepresented criterion x outcome cells.
                score += 1.0 / (1.0 + outcome_counts[(criterion, label)])
            # Prefer relevance profiles not yet represented.
            score += 0.75 / (1.0 + profile_counts[cand["vector"]])
            # Deterministic tie-breaking from seeded shuffle.
            tie = -rank[cand["record_id"]]
            key = (score, tie)
            if best_score is None or key > best_score:
                best_score = key
                best = cand
        selected.append(best)
        pool.remove(best)
        profile_counts[best["vector"]] += 1
        for criterion, label in zip(CRITERIA, best["vector"]):
            outcome_counts[(criterion, label)] += 1
    return selected


def main():
    audit_rows = read_csv(AUDIT)
    stake_rows = read_csv(STAKE)
    candidates = build_candidates(audit_rows)

    metadata = {r["record_id"]: r for r in stake_rows}
    by_group = defaultdict(list)
    for c in candidates:
        by_group[c["stakeholder_group"]].append(c)

    rng = random.Random(SEED)
    selected = []
    group_shortfalls = {}
    for group in STAKEHOLDERS:
        available = len(by_group[group])
        target = min(TARGET_PER_STAKEHOLDER, available)
        group_shortfalls[group] = max(0, TARGET_PER_STAKEHOLDER - available)
        selected.extend(select_group(by_group[group], target, rng))

    # Stable output order after selection.
    selected.sort(key=lambda c: (STAKEHOLDERS.index(c["stakeholder_group"]), c["record_id"]))

    blinded_rows = []
    key_rows = []
    selected_summary = Counter()

    for doc_index, cand in enumerate(selected, start=1):
        rid = cand["record_id"]
        meta = metadata.get(rid, {})
        sample_document_id = f"VAL-DOC-{doc_index:03d}"
        for criterion_index, criterion in enumerate(CRITERIA, start=1):
            ar = cand["rows"][criterion]
            auto_label = parse_bool(ar[PRIMARY_FIELD])
            decision_id = f"{sample_document_id}-C{criterion_index}"
            common = {
                "decision_id": decision_id,
                "sample_document_id": sample_document_id,
                "record_id": rid,
                "title": meta.get("title", ""),
                "year": meta.get("year", ""),
                "publisher": meta.get("publisher", ""),
                "url": meta.get("url", ""),
                "criterion": criterion,
                "criterion_definition": DEFINITIONS[criterion],
            }
            blinded_rows.append({
                **common,
                "manual_label": "",
                "confidence_1_to_3": "",
                "rationale": "",
            })
            key_rows.append({
                **common,
                "stakeholder_group": cand["stakeholder_group"],
                "automated_primary_relevant": str(auto_label).lower(),
                "matched_sentences": ar["matched_sentences"],
                "distinct_phrase_families": ar["distinct_phrase_families"],
                "sentence_units": ar["sentence_units"],
            })
            selected_summary[(cand["stakeholder_group"], criterion, auto_label)] += 1

    blinded_path = OUT / "criterion_relevance_validation_sample_blinded.csv"
    key_path = OUT / "criterion_relevance_validation_key.csv"
    summary_path = OUT / "criterion_relevance_validation_sample_summary.json"

    blinded_fields = [
        "decision_id", "sample_document_id", "record_id", "title", "year", "publisher", "url",
        "criterion", "criterion_definition", "manual_label", "confidence_1_to_3", "rationale",
    ]
    key_fields = [
        "decision_id", "sample_document_id", "record_id", "title", "year", "publisher", "url",
        "criterion", "criterion_definition", "stakeholder_group", "automated_primary_relevant",
        "matched_sentences", "distinct_phrase_families", "sentence_units",
    ]
    write_csv(blinded_path, blinded_rows, blinded_fields)
    write_csv(key_path, key_rows, key_fields)

    coverage = []
    for group in STAKEHOLDERS:
        for criterion in CRITERIA:
            coverage.append({
                "stakeholder_group": group,
                "criterion": criterion,
                "auto_relevant": selected_summary[(group, criterion, True)],
                "auto_not_relevant": selected_summary[(group, criterion, False)],
            })

    summary = {
        "stage": "independent_criterion_relevance_validation_sampling",
        "seed": SEED,
        "target_documents_per_stakeholder": TARGET_PER_STAKEHOLDER,
        "selected_documents": len(selected),
        "blinded_document_criterion_decisions": len(blinded_rows),
        "group_shortfalls": group_shortfalls,
        "primary_automated_rule": "relevant_s2_f2",
        "sampling_note": (
            "Automated labels are used only for deterministic coverage/diversity sampling and are omitted from the blinded coder file."
        ),
        "blinded_sample_sha256": sha256(blinded_path),
        "locked_key_sha256": sha256(key_path),
        "coverage": coverage,
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
