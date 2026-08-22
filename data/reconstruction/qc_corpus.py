from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from sklearn.feature_extraction.text import HashingVectorizer

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "acquisition_output"
QC = OUT / "qc"
STATUS = OUT / "acquisition_status.csv"
TEXT_DIR = OUT / "text"

NEAR_DUPLICATE_THRESHOLD = 0.95


def read_status() -> list[dict[str, str]]:
    with STATUS.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def canonical_priority(candidate_id: str) -> tuple[int, str]:
    # Prefer a historical seed identifier when identical text occurs in a later
    # expansion record. This is identity selection only; it does not restore the
    # historical N=87 design or privilege historical labels/results.
    if re.match(r"^(OFFICIAL|INST|MEDIA|CORP)-", candidate_id):
        return (0, candidate_id)
    if candidate_id.startswith("WEB-"):
        return (1, candidate_id)
    if candidate_id.startswith("EXP-"):
        return (2, candidate_id)
    if candidate_id.startswith("expanded_"):
        return (3, candidate_id)
    return (4, candidate_id)


def main() -> int:
    rows = read_status()
    extracted = [r for r in rows if r.get("status") == "acquired_extracted"]
    exceptions = [r for r in rows if r.get("status") != "acquired_extracted"]

    by_hash: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in extracted:
        text_hash = (row.get("text_sha256") or "").strip()
        if text_hash:
            by_hash[text_hash].append(row)

    duplicate_rows: list[dict[str, object]] = []
    noncanonical_ids: set[str] = set()
    duplicate_cluster_count = 0

    for text_hash, group in sorted(by_hash.items()):
        if len(group) < 2:
            continue
        duplicate_cluster_count += 1
        canonical = min((r["candidate_id"] for r in group), key=canonical_priority)
        for row in group:
            is_canonical = row["candidate_id"] == canonical
            if not is_canonical:
                noncanonical_ids.add(row["candidate_id"])
            duplicate_rows.append({
                "text_sha256": text_hash,
                "cluster_size": len(group),
                "canonical_id": canonical,
                "candidate_id": row["candidate_id"],
                "is_canonical": str(is_canonical).lower(),
                "title": row.get("title", ""),
                "year": row.get("year", ""),
                "publisher": row.get("publisher", ""),
                "source_url": row.get("source_url", ""),
                "metadata_source": row.get("metadata_source", ""),
            })

    unique_rows = [r for r in extracted if r["candidate_id"] not in noncanonical_ids]

    # Near-duplicate review is intentionally conservative. Exact-hash duplicates
    # are already collapsed above. HashingVectorizer is used only to surface
    # high-similarity pairs for manual review; it never excludes a document by
    # itself.
    texts: list[str] = []
    text_rows: list[dict[str, str]] = []
    for row in unique_rows:
        path = TEXT_DIR / f"{row['candidate_id']}.txt"
        if not path.exists():
            continue
        texts.append(path.read_text(encoding="utf-8", errors="replace"))
        text_rows.append(row)

    near_rows: list[dict[str, object]] = []
    if texts:
        vectorizer = HashingVectorizer(
            n_features=2**17,
            alternate_sign=False,
            norm="l2",
            stop_words="english",
            ngram_range=(1, 2),
        )
        matrix = vectorizer.transform(texts)
        similarities = matrix @ matrix.T
        coo = similarities.tocoo()
        seen: set[tuple[int, int]] = set()
        for i, j, score in zip(coo.row, coo.col, coo.data):
            if i >= j or score < NEAR_DUPLICATE_THRESHOLD:
                continue
            pair = (int(i), int(j))
            if pair in seen:
                continue
            seen.add(pair)
            a = text_rows[i]
            b = text_rows[j]
            if (a.get("text_sha256") or "") == (b.get("text_sha256") or ""):
                continue
            near_rows.append({
                "similarity": f"{float(score):.6f}",
                "candidate_id_a": a["candidate_id"],
                "candidate_id_b": b["candidate_id"],
                "title_a": a.get("title", ""),
                "title_b": b.get("title", ""),
                "year_a": a.get("year", ""),
                "year_b": b.get("year", ""),
                "publisher_a": a.get("publisher", ""),
                "publisher_b": b.get("publisher", ""),
                "url_a": a.get("source_url", ""),
                "url_b": b.get("source_url", ""),
                "decision": "manual_review",
            })

    exception_fields = [
        "candidate_id", "status", "title", "year", "publisher", "metadata_source",
        "source_url", "final_url", "http_status", "content_type", "retrieval_method",
        "raw_bytes", "extraction_method", "pages", "text_chars", "text_words", "error",
    ]
    exception_rows = [{key: row.get(key, "") for key in exception_fields} for row in exceptions]

    manifest_fields = [
        "candidate_id", "title", "year", "publisher", "metadata_source", "source_url",
        "final_url", "raw_sha256", "text_sha256", "text_words",
    ]
    manifest_rows = [{key: row.get(key, "") for key in manifest_fields} for row in unique_rows]

    write_csv(
        QC / "exact_duplicate_clusters.csv",
        ["text_sha256", "cluster_size", "canonical_id", "candidate_id", "is_canonical",
         "title", "year", "publisher", "source_url", "metadata_source"],
        duplicate_rows,
    )
    write_csv(
        QC / "near_duplicate_review.csv",
        ["similarity", "candidate_id_a", "candidate_id_b", "title_a", "title_b", "year_a",
         "year_b", "publisher_a", "publisher_b", "url_a", "url_b", "decision"],
        sorted(near_rows, key=lambda r: float(r["similarity"]), reverse=True),
    )
    write_csv(QC / "acquisition_exceptions.csv", exception_fields, exception_rows)
    write_csv(QC / "preliminary_unique_text_manifest.csv", manifest_fields, manifest_rows)

    status_counts = Counter(row.get("status", "") for row in rows)
    summary = {
        "candidate_records_processed": len(rows),
        "acquired_extracted_records": len(extracted),
        "acquisition_exception_records": len(exceptions),
        "exact_duplicate_clusters": duplicate_cluster_count,
        "exact_duplicate_redundant_records": len(noncanonical_ids),
        "preliminary_unique_extracted_texts_after_exact_dedup": len(unique_rows),
        "near_duplicate_pairs_flagged_at_similarity_ge_0_95": len(near_rows),
        "status_counts": dict(status_counts),
        "near_duplicate_threshold": NEAR_DUPLICATE_THRESHOLD,
        "corpus_frozen": False,
        "note": (
            "Preliminary QC only. Corpus freeze requires resolution of acquisition exceptions, "
            "manual review of near duplicates, substantive relevance/text-quality screening, "
            "and documented source-family saturation."
        ),
    }
    (QC / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
