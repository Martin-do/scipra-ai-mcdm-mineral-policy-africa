"""Build a reviewer-focused queue from secondary archive media evidence.

This helper does not decide membership. It groups the 1,062 evidence rows into
review priorities so high-value hidden body-text case matches can be examined
before low-information/no-anchor material. Final decision fields stay blank.
"""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECON = ROOT / "data" / "reconstruction"
EVIDENCE = RECON / "secondary_media_targeted_evidence.csv"
OUT = RECON / "secondary_media_substantive_review_queue.csv"
SUMMARY = RECON / "secondary_media_substantive_review_queue_summary.json"

PRIORITY = {
    "strong_early_2012_event_context": 0,
    "strong_case_context_supported": 1,
    "strong_lonmin_context_supported": 2,
    "possible_lonmin_substantive_context": 3,
    "case_term_low_context_review": 4,
    "sibanye_context_without_case_anchor_review": 5,
    "lonmin_low_context_review": 6,
    "ambiguous_secondary_review": 7,
    "acquisition_or_text_exception": 8,
    "strong_routine_no_case_anchor": 9,
    "no_case_anchor": 10,
}


def read_rows(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


rows = read_rows(EVIDENCE)
if len(rows) != 1062:
    raise RuntimeError(f"Expected 1062 secondary evidence rows, found {len(rows)}")

out_rows = []
class_counts = Counter()
priority_counts = Counter()
publisher_counts = Counter()
for r in rows:
    klass = r.get("evidence_class", "")
    rank = PRIORITY.get(klass, 99)
    class_counts[klass] += 1
    priority_counts[str(rank)] += 1
    publisher_counts[r.get("publisher", "")] += 1
    out_rows.append({
        "candidate_id": r.get("candidate_id", ""),
        "review_priority": rank,
        "evidence_class": klass,
        "title": r.get("title", ""),
        "year": r.get("year", ""),
        "publication_date_from_url": r.get("publication_date_from_url", ""),
        "publisher": r.get("publisher", ""),
        "url": r.get("url", ""),
        "targeted_fetch_status": r.get("targeted_fetch_status", ""),
        "retrieved_text_words": r.get("retrieved_text_words", ""),
        "retrieved_text_sha256": r.get("retrieved_text_sha256", ""),
        "retrieved_lonmin_mentions": r.get("retrieved_lonmin_mentions", ""),
        "retrieved_sibanye_mentions": r.get("retrieved_sibanye_mentions", ""),
        "case_terms": r.get("case_terms", ""),
        "case_mentions_total": r.get("case_mentions_total", ""),
        "event_terms": r.get("event_terms", ""),
        "event_distinct_terms": r.get("event_distinct_terms", ""),
        "social_terms": r.get("social_terms", ""),
        "social_distinct_terms": r.get("social_distinct_terms", ""),
        "corporate_terms": r.get("corporate_terms", ""),
        "corporate_distinct_terms": r.get("corporate_distinct_terms", ""),
        "evidence_note": r.get("evidence_note", ""),
        "review_decision": "",
        "review_reason_code": "",
        "review_note": "",
    })

out_rows.sort(key=lambda r: (int(r["review_priority"]), r["year"], r["candidate_id"]))
with OUT.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
    writer.writeheader()
    writer.writerows(out_rows)

summary = {
    "records_in_review_queue": len(out_rows),
    "evidence_class_counts": dict(class_counts),
    "review_priority_counts": dict(priority_counts),
    "publisher_counts": dict(publisher_counts),
    "priority_order": PRIORITY,
    "final_decisions_made": 0,
    "note": (
        "Reviewer queue only. Priority is for review efficiency, not corpus eligibility. "
        "No row is included or excluded by this builder."
    ),
}
SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
