"""Build a deterministic pre-freeze deduplication audit for eligible archive media.

Inputs are the two completed substantive-decision ledgers. Only records with a
final `include` decision enter this audit. Exact SHA-256 text duplicates are
collapsed deterministically; same-URL and same-normalised-title/year clusters are
review flags only and are never automatically collapsed unless hashes are equal.

This script does not freeze the corpus and does not use stance labels or model
outputs.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[2]
RECON = ROOT / "data" / "reconstruction"
TITLE_LEDGER = RECON / "media_substantive_decision_ledger.csv"
SECONDARY_LEDGER = RECON / "secondary_media_substantive_decision_ledger.csv"
PRE = RECON / "archive_media_included_pre_dedup_manifest.csv"
EXACT = RECON / "archive_media_exact_duplicate_clusters.csv"
TITLE_REVIEW = RECON / "archive_media_same_title_year_review.csv"
URL_REVIEW = RECON / "archive_media_same_url_review.csv"
DEDUP = RECON / "archive_media_exact_dedup_preliminary_manifest.csv"
SUMMARY = RECON / "archive_media_dedup_summary.json"


def read_rows(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def canon_url(url: str) -> str:
    p = urlsplit((url or "").strip())
    host = p.netloc.lower().removeprefix("www.")
    path = re.sub(r"/+", "/", p.path).rstrip("/")
    return urlunsplit(("https", host, path, "", ""))


def norm_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (title or "").lower()).strip()


def sort_key(r):
    # Deterministic representative rule: earliest known publication date, then
    # lexical URL and record ID. This chooses a canonical row without implying
    # that later exact copies are invalid sources.
    date = r.get("publication_date_from_url") or f"{r.get('year','9999')}-99-99"
    return (date, r.get("canonical_url", ""), r.get("record_id", ""))


title_rows = read_rows(TITLE_LEDGER)
secondary_rows = read_rows(SECONDARY_LEDGER)
if len(title_rows) != 690 or len(secondary_rows) != 1062:
    raise RuntimeError(f"Unexpected ledger sizes: title={len(title_rows)}, secondary={len(secondary_rows)}")

included = []
for source, rows in (("title_trigger", title_rows), ("secondary_keyword", secondary_rows)):
    for r in rows:
        if r.get("final_decision") != "include":
            continue
        sha = (r.get("retrieved_text_sha256") or "").strip().lower()
        if not re.fullmatch(r"[0-9a-f]{64}", sha):
            raise RuntimeError(f"Included record lacks valid text SHA-256: {r.get('candidate_id')}: {sha!r}")
        included.append({
            "record_id": r.get("candidate_id", ""),
            "archive_queue": source,
            "title": r.get("title", ""),
            "normalised_title": norm_title(r.get("title", "")),
            "year": r.get("year", ""),
            "publication_date_from_url": r.get("publication_date_from_url", ""),
            "publisher": r.get("publisher", ""),
            "url": r.get("url", ""),
            "canonical_url": canon_url(r.get("url", "")),
            "retrieved_text_words": r.get("retrieved_text_words", ""),
            "retrieved_text_sha256": sha,
            "reason_code": r.get("reason_code", ""),
            "decision_status": r.get("decision_status", ""),
            "decision_provenance": r.get("decision_provenance", ""),
        })

expected_title = sum(r.get("final_decision") == "include" for r in title_rows)
expected_secondary = sum(r.get("final_decision") == "include" for r in secondary_rows)
if (expected_title, expected_secondary, len(included)) != (547, 131, 678):
    raise RuntimeError(
        f"Expected 547 + 131 = 678 included media rows; got {expected_title} + {expected_secondary} = {len(included)}"
    )
if len({r["record_id"] for r in included}) != len(included):
    raise RuntimeError("Duplicate record IDs found across eligible archive media")

included.sort(key=sort_key)
fields = list(included[0].keys())
with PRE.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(included)


def groups_by(keyfn):
    d = defaultdict(list)
    for r in included:
        key = keyfn(r)
        if key:
            d[key].append(r)
    return {k: sorted(v, key=sort_key) for k, v in d.items() if len(v) > 1}

exact_groups = groups_by(lambda r: r["retrieved_text_sha256"])
url_groups = groups_by(lambda r: r["canonical_url"])
title_year_groups = groups_by(lambda r: (r["normalised_title"], r["year"]))

exact_rows = []
redundant_ids = set()
for n, (sha, members) in enumerate(sorted(exact_groups.items()), 1):
    keeper = members[0]["record_id"]
    for pos, r in enumerate(members, 1):
        is_keeper = r["record_id"] == keeper
        if not is_keeper:
            redundant_ids.add(r["record_id"])
        exact_rows.append({
            "cluster_id": f"MEDIA-EXACT-{n:04d}",
            "text_sha256": sha,
            "cluster_size": len(members),
            "member_order": pos,
            "record_id": r["record_id"],
            "canonical_representative": str(is_keeper).lower(),
            "representative_record_id": keeper,
            "archive_queue": r["archive_queue"],
            "publisher": r["publisher"],
            "publication_date_from_url": r["publication_date_from_url"],
            "title": r["title"],
            "url": r["url"],
        })

exact_fields = [
    "cluster_id", "text_sha256", "cluster_size", "member_order", "record_id",
    "canonical_representative", "representative_record_id", "archive_queue", "publisher",
    "publication_date_from_url", "title", "url"
]
with EXACT.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=exact_fields); w.writeheader(); w.writerows(exact_rows)


def write_review(path: Path, groups: dict, prefix: str, key_label: str):
    out = []
    for n, (key, members) in enumerate(sorted(groups.items(), key=lambda kv: str(kv[0])), 1):
        exact_same = len({m["retrieved_text_sha256"] for m in members}) == 1
        for r in members:
            out.append({
                "cluster_id": f"{prefix}-{n:04d}",
                key_label: " | ".join(key) if isinstance(key, tuple) else str(key),
                "cluster_size": len(members),
                "all_text_sha256_equal": str(exact_same).lower(),
                "record_id": r["record_id"],
                "archive_queue": r["archive_queue"],
                "publisher": r["publisher"],
                "publication_date_from_url": r["publication_date_from_url"],
                "retrieved_text_sha256": r["retrieved_text_sha256"],
                "title": r["title"],
                "url": r["url"],
            })
    review_fields = [
        "cluster_id", key_label, "cluster_size", "all_text_sha256_equal", "record_id", "archive_queue",
        "publisher", "publication_date_from_url", "retrieved_text_sha256", "title", "url"
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=review_fields); w.writeheader(); w.writerows(out)
    return out

url_rows = write_review(URL_REVIEW, url_groups, "MEDIA-URL", "canonical_url")
title_rows_out = write_review(TITLE_REVIEW, title_year_groups, "MEDIA-TITLEYEAR", "normalised_title_year")

dedup = []
for r in included:
    if r["record_id"] in redundant_ids:
        continue
    x = dict(r)
    x["exact_dedup_status"] = "retained_unique_or_representative"
    dedup.append(x)
with DEDUP.open("w", encoding="utf-8", newline="") as f:
    out_fields = fields + ["exact_dedup_status"]
    w = csv.DictWriter(f, fieldnames=out_fields); w.writeheader(); w.writerows(dedup)

summary = {
    "scope": "eligible_archive_media_after_substantive_screening_before_corpus_freeze",
    "title_trigger_inclusions": expected_title,
    "secondary_keyword_inclusions": expected_secondary,
    "included_media_records_pre_dedup": len(included),
    "records_with_valid_text_sha256": len(included),
    "exact_duplicate_clusters": len(exact_groups),
    "exact_duplicate_cluster_members": len(exact_rows),
    "exact_duplicate_redundant_records": len(redundant_ids),
    "records_after_exact_sha256_dedup": len(dedup),
    "same_canonical_url_clusters_for_review": len(url_groups),
    "same_normalised_title_year_clusters_for_review": len(title_year_groups),
    "same_url_rows": len(url_rows),
    "same_title_year_rows": len(title_rows_out),
    "corpus_frozen": False,
    "dedup_rule": (
        "Only identical acquired-text SHA-256 values are automatically collapsed. The canonical representative is the earliest "
        "known publication date, then lexical canonical URL and record ID. Same URL or same normalised title/year is review-only "
        "unless text hashes are identical."
    ),
    "important_note": (
        "This audit covers the newly screened archive-media inclusion pool only. Cross-source/cross-phase deduplication against "
        "the previously screened institutional/media reconstruction corpus still remains before the canonical corpus manifest can be frozen."
    ),
}
SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
