"""Build a conservative cross-phase duplicate audit for SCIPRA reconstruction.

Compares the earlier 300-record screened reconstruction manifest with the 661
archive-media records retained after substantive screening and republication
review. The audit never treats a repeated text hash as sufficient on its own.
Automatic cross-phase collapse requires corroborating source identity:

* the same canonical URL; or
* the same valid text SHA-256 AND the same normalized title.

Same-title/year/publisher matches with differing URLs/hashes are review
candidates only. Same hashes across unrelated metadata are extraction-collision
signals only. Known archive text-quality exceptions never become analysis-ready
merely because they carry a syntactically valid hash.

This script does not freeze the corpus and does not use stance/model outputs.
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
PRIOR = RECON / "review_handoff" / "screened_qc_preliminary_unique_text_manifest.csv"
ARCHIVE = RECON / "archive_media_post_titlepair_manifest.csv"
QUALITY = RECON / "archive_media_quality_review_decisions.csv"

MATCHES = RECON / "cross_phase_match_audit.csv"
SAFE = RECON / "cross_phase_safe_duplicate_decisions.csv"
TITLE_REVIEW = RECON / "cross_phase_same_title_review.csv"
HASH_COLLISIONS = RECON / "cross_phase_hash_collision_review.csv"
COMBINED = RECON / "cross_phase_preliminary_combined_manifest.csv"
SUMMARY = RECON / "cross_phase_dedup_summary.json"

SHA_RX = re.compile(r"^[0-9a-f]{64}$")


def read_rows(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def norm_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def canon_url(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    try:
        p = urlsplit(value)
    except Exception:
        return value.lower().rstrip("/")
    host = p.netloc.lower().removeprefix("www.")
    path = re.sub(r"/+", "/", p.path).rstrip("/")
    scheme = "https" if host else p.scheme.lower()
    return urlunsplit((scheme, host, path, "", ""))


def valid_sha(value: str) -> str:
    value = (value or "").strip().lower()
    return value if SHA_RX.fullmatch(value) else ""


prior = read_rows(PRIOR)
archive = read_rows(ARCHIVE)
quality_rows = read_rows(QUALITY)
if len(prior) != 300:
    raise RuntimeError(f"Expected 300 prior screened rows, found {len(prior)}")
if len(archive) != 661:
    raise RuntimeError(f"Expected 661 post-republication archive rows, found {len(archive)}")

quality_by_id = {r["record_id"]: r for r in quality_rows}
known_quality_ids = set(quality_by_id)
if len(known_quality_ids) != 11:
    raise RuntimeError(f"Expected 11 raw archive quality-review rows, found {len(known_quality_ids)}")

# Normalize prior records.
prior_norm = []
for r in prior:
    urls = {canon_url(r.get("source_url")), canon_url(r.get("final_url"))} - {""}
    prior_norm.append({
        "record_id": r.get("candidate_id", ""),
        "phase": "prior_screened_300",
        "title": r.get("title", ""),
        "normalised_title": norm_title(r.get("title", "")),
        "year": r.get("year", ""),
        "publisher": r.get("publisher", ""),
        "source_url": r.get("source_url", ""),
        "final_url": r.get("final_url", ""),
        "canonical_urls": urls,
        "text_sha256": valid_sha(r.get("text_sha256", "")),
        "text_words": r.get("text_words", ""),
        "analysis_ready": True,
        "metadata_source": r.get("metadata_source", ""),
    })

archive_norm = []
for r in archive:
    rid = r.get("record_id", "")
    ready = str(r.get("analysis_ready_pre_cross_phase", "")).lower() == "true"
    archive_norm.append({
        "record_id": rid,
        "phase": "archive_media_post_republication",
        "title": r.get("title", ""),
        "normalised_title": norm_title(r.get("title", "")),
        "year": r.get("year", ""),
        "publisher": r.get("publisher", ""),
        "source_url": r.get("url", ""),
        "final_url": r.get("url", ""),
        "canonical_urls": {canon_url(r.get("url", ""))} - {""},
        "text_sha256": valid_sha(r.get("retrieved_text_sha256", "")),
        "text_words": r.get("retrieved_text_words", ""),
        "analysis_ready": ready,
        "archive_queue": r.get("archive_queue", ""),
        "decision_status": r.get("decision_status", ""),
        "decision_provenance": r.get("decision_provenance", ""),
        "final_text_quality_status": r.get("final_text_quality_status", ""),
    })

# Guard known quality status arithmetic. One of the 11 raw exceptions was itself
# collapsed as a later republication, leaving 10 among the retained 661.
retained_quality_ids = {r["record_id"] for r in archive_norm if not r["analysis_ready"]}
if len(retained_quality_ids) != 10:
    raise RuntimeError(f"Expected 10 retained archive quality exceptions, found {len(retained_quality_ids)}")

prior_by_url = defaultdict(list)
prior_by_hash = defaultdict(list)
prior_by_title_year_pub = defaultdict(list)
for p in prior_norm:
    for u in p["canonical_urls"]:
        prior_by_url[u].append(p)
    if p["text_sha256"]:
        prior_by_hash[p["text_sha256"]].append(p)
    prior_by_title_year_pub[(p["normalised_title"], p["year"], p["publisher"].strip().lower())].append(p)

match_rows = []
safe_candidates = defaultdict(list)
title_review_rows = []
hash_collision_rows = []

for a in archive_norm:
    seen_pairs = set()
    # URL identity is strong source identity even if archive extraction is bad.
    url_matches = []
    for u in a["canonical_urls"]:
        url_matches.extend(prior_by_url.get(u, []))
    for p in url_matches:
        pair = (p["record_id"], a["record_id"])
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        same_hash = bool(a["text_sha256"] and a["text_sha256"] == p["text_sha256"])
        same_title = a["normalised_title"] == p["normalised_title"]
        match_rows.append({
            "prior_record_id": p["record_id"], "archive_record_id": a["record_id"],
            "match_type": "same_canonical_url", "same_title": str(same_title).lower(),
            "same_valid_text_sha256": str(same_hash).lower(), "prior_title": p["title"],
            "archive_title": a["title"], "prior_publisher": p["publisher"], "archive_publisher": a["publisher"],
            "prior_year": p["year"], "archive_year": a["year"], "prior_url": p["final_url"] or p["source_url"],
            "archive_url": a["source_url"], "prior_text_sha256": p["text_sha256"],
            "archive_text_sha256": a["text_sha256"], "archive_analysis_ready_before_cross_phase": str(a["analysis_ready"]).lower(),
            "disposition": "safe_cross_phase_duplicate_candidate",
        })
        safe_candidates[a["record_id"]].append((p, "same_canonical_url"))

    # Hash identity is safe only when title identity corroborates it. Otherwise
    # preserve as a collision signal. Also do not use a known archive quality
    # exception's suspect hash for automatic collapse.
    if a["text_sha256"] and a["record_id"] not in retained_quality_ids:
        for p in prior_by_hash.get(a["text_sha256"], []):
            pair = (p["record_id"], a["record_id"])
            same_title = a["normalised_title"] == p["normalised_title"]
            same_url = bool(a["canonical_urls"] & p["canonical_urls"])
            if same_title or same_url:
                if pair not in seen_pairs:
                    seen_pairs.add(pair)
                    match_rows.append({
                        "prior_record_id": p["record_id"], "archive_record_id": a["record_id"],
                        "match_type": "same_sha256_with_metadata_corroboration", "same_title": str(same_title).lower(),
                        "same_valid_text_sha256": "true", "prior_title": p["title"], "archive_title": a["title"],
                        "prior_publisher": p["publisher"], "archive_publisher": a["publisher"],
                        "prior_year": p["year"], "archive_year": a["year"], "prior_url": p["final_url"] or p["source_url"],
                        "archive_url": a["source_url"], "prior_text_sha256": p["text_sha256"],
                        "archive_text_sha256": a["text_sha256"], "archive_analysis_ready_before_cross_phase": "true",
                        "disposition": "safe_cross_phase_duplicate_candidate",
                    })
                safe_candidates[a["record_id"]].append((p, "same_sha256_with_metadata_corroboration"))
            else:
                hash_collision_rows.append({
                    "prior_record_id": p["record_id"], "archive_record_id": a["record_id"],
                    "shared_text_sha256": a["text_sha256"], "prior_title": p["title"], "archive_title": a["title"],
                    "prior_url": p["final_url"] or p["source_url"], "archive_url": a["source_url"],
                    "review_status": "do_not_auto_collapse_hash_metadata_conflict",
                })

    # Exact title/year/publisher is a review signal when not already safe.
    key = (a["normalised_title"], a["year"], a["publisher"].strip().lower())
    for p in prior_by_title_year_pub.get(key, []):
        if p["record_id"] in {x[0]["record_id"] for x in [safe_candidates.get(a["record_id"], [])] if x}:
            continue
        same_url = bool(a["canonical_urls"] & p["canonical_urls"])
        same_hash = bool(a["text_sha256"] and a["text_sha256"] == p["text_sha256"])
        if same_url or (same_hash and a["record_id"] not in retained_quality_ids):
            continue
        title_review_rows.append({
            "prior_record_id": p["record_id"], "archive_record_id": a["record_id"],
            "normalised_title": a["normalised_title"], "year": a["year"], "publisher": a["publisher"],
            "prior_url": p["final_url"] or p["source_url"], "archive_url": a["source_url"],
            "prior_text_sha256": p["text_sha256"], "archive_text_sha256": a["text_sha256"],
            "archive_analysis_ready_before_cross_phase": str(a["analysis_ready"]).lower(),
            "review_status": "same_title_year_publisher_requires_explicit_review",
        })

# Create deterministic safe decisions, always retaining the already-screened
# prior record and mapping the archive record as redundant cross-phase identity.
safe_rows = []
redundant_archive_ids = set()
for aid, candidates in sorted(safe_candidates.items()):
    unique = {}
    for p, reason in candidates:
        unique[p["record_id"]] = (p, reason)
    chosen_id = sorted(unique)[0]
    chosen, chosen_reason = unique[chosen_id]
    redundant_archive_ids.add(aid)
    reasons = sorted({reason for _, reason in unique.values()})
    safe_rows.append({
        "retained_prior_record_id": chosen["record_id"],
        "redundant_archive_record_id": aid,
        "duplicate_evidence": ";".join(reasons),
        "number_of_prior_candidates": len(unique),
        "final_duplicate_decision": "collapse_cross_phase_duplicate_keep_prior_screened_record",
        "decision_reason": "same_source_identity_corroborated_by_canonical_url_or_hash_plus_title",
    })

# Emit unified preliminary combined manifest. This is still pre-near-duplicate.
combined = []
for p in prior_norm:
    combined.append({
        "canonical_record_id": p["record_id"], "source_phase": p["phase"], "title": p["title"],
        "year": p["year"], "publisher": p["publisher"], "url": p["final_url"] or p["source_url"],
        "text_sha256": p["text_sha256"], "text_words": p["text_words"], "analysis_ready": "true",
        "cross_phase_status": "retained_prior_screened_record", "duplicate_representative_record_id": p["record_id"],
    })
for a in archive_norm:
    if a["record_id"] in redundant_archive_ids:
        continue
    combined.append({
        "canonical_record_id": a["record_id"], "source_phase": a["phase"], "title": a["title"],
        "year": a["year"], "publisher": a["publisher"], "url": a["source_url"],
        "text_sha256": a["text_sha256"], "text_words": a["text_words"],
        "analysis_ready": str(a["analysis_ready"]).lower(), "cross_phase_status": "retained_archive_record_after_safe_cross_phase_audit",
        "duplicate_representative_record_id": a["record_id"],
    })

# Write outputs.
def write_csv(path: Path, rows: list[dict], fields: list[str]):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)

match_fields = [
    "prior_record_id","archive_record_id","match_type","same_title","same_valid_text_sha256","prior_title","archive_title",
    "prior_publisher","archive_publisher","prior_year","archive_year","prior_url","archive_url","prior_text_sha256",
    "archive_text_sha256","archive_analysis_ready_before_cross_phase","disposition"
]
write_csv(MATCHES, match_rows, match_fields)
write_csv(SAFE, safe_rows, ["retained_prior_record_id","redundant_archive_record_id","duplicate_evidence","number_of_prior_candidates","final_duplicate_decision","decision_reason"])
write_csv(TITLE_REVIEW, title_review_rows, ["prior_record_id","archive_record_id","normalised_title","year","publisher","prior_url","archive_url","prior_text_sha256","archive_text_sha256","archive_analysis_ready_before_cross_phase","review_status"])
write_csv(HASH_COLLISIONS, hash_collision_rows, ["prior_record_id","archive_record_id","shared_text_sha256","prior_title","archive_title","prior_url","archive_url","review_status"])
write_csv(COMBINED, combined, ["canonical_record_id","source_phase","title","year","publisher","url","text_sha256","text_words","analysis_ready","cross_phase_status","duplicate_representative_record_id"])

analysis_ready_count = sum(r["analysis_ready"] == "true" for r in combined)
summary = {
    "scope": "cross_phase_dedup_prior_screened_300_plus_post_republication_archive_661",
    "prior_screened_records": len(prior_norm),
    "archive_records_post_republication": len(archive_norm),
    "combined_pool_before_cross_phase_dedup": len(prior_norm) + len(archive_norm),
    "safe_cross_phase_duplicate_archive_records": len(redundant_archive_ids),
    "safe_cross_phase_duplicate_decision_rows": len(safe_rows),
    "same_title_year_publisher_review_pairs": len(title_review_rows),
    "hash_metadata_conflict_pairs": len(hash_collision_rows),
    "records_retained_after_safe_cross_phase_dedup": len(combined),
    "analysis_ready_records_after_safe_cross_phase_dedup": analysis_ready_count,
    "retained_non_analysis_ready_records": len(combined) - analysis_ready_count,
    "near_duplicate_review_complete": False,
    "corpus_frozen": False,
    "dedup_rule": (
        "Automatic cross-phase collapse requires the same canonical URL, or the same valid text SHA-256 corroborated by the same normalized title. "
        "Hash-only matches across conflicting metadata are never auto-collapsed. Same-title/year/publisher matches with differing URL/hash remain explicit review candidates."
    ),
    "important_note": (
        "This is the safe exact/metadata cross-phase pass only. Remaining same-title candidates and broader near-duplicate review must be resolved before the canonical corpus manifest can be frozen."
    ),
}
SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
