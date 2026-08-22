"""Protocol-driven acquisition with collision-safe candidate identities.

The historical 87-record seed uses stable IDs. Expansion screening files were
created in several passes and some reuse local IDs such as EXP-MEDIA-001 for
different documents. This wrapper preserves every screened candidate by
qualifying colliding expansion IDs with the source-file stem. It does not
silently discard either record; duplicate-content resolution is deferred to the
pre-model corpus-QC stage using URLs and extracted-text hashes.
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

import acquire_corpus as base

RECON = Path(__file__).resolve().parent
OVERRIDES = RECON / "source_overrides.csv"

# Force the verified public Farlam mirror instead of the malformed repository PDF.
base.LOCAL_FALLBACKS.pop("INST-001", None)


def eligible(row: dict[str, str]) -> bool:
    decision = (row.get("decision") or "").strip().lower()
    if decision in {"include", "included", "include_candidate", "eligible"}:
        return True
    status = (row.get("screening_status") or row.get("status") or "").strip().lower()
    return status.startswith("eligible") or status in {
        "verified_candidate",
        "verified",
        "include",
        "included",
        "verified_archive",
        "verified_historical_citation",
    }


def expansion_records() -> list[tuple[Path, dict[str, str], str]]:
    records: list[tuple[Path, dict[str, str], str]] = []
    for path in base.expanded_candidate_files():
        for row in base.read_csv(path):
            if not eligible(row):
                continue
            raw_id = (row.get("candidate_id") or row.get("recovery_id") or "").strip()
            if raw_id:
                records.append((path, row, raw_id))
    return records


_EXPANSIONS = expansion_records()
_RAW_ID_COUNTS = Counter(raw_id for _, _, raw_id in _EXPANSIONS)


def acquisition_id(path: Path, raw_id: str) -> str:
    """Return stable unique ID; qualify only IDs reused across screening files."""
    if _RAW_ID_COUNTS[raw_id] > 1:
        return f"{path.stem}__{raw_id}"
    return raw_id


def candidate_ids_v3() -> tuple[list[str], int]:
    seed_rows = base.read_csv(RECON / "candidate_corpus_87.csv")
    seed_ids = [(r.get("candidate_doc_id") or "").strip() for r in seed_rows]
    seed_ids = [cid for cid in seed_ids if cid]
    if len(seed_ids) != 87:
        raise RuntimeError(
            "Historical seed file candidate_corpus_87.csv should contain 87 IDs; "
            f"found {len(seed_ids)}"
        )

    ids = list(seed_ids)
    ids.extend(acquisition_id(path, raw_id) for path, _, raw_id in _EXPANSIONS)

    if len(set(ids)) != len(ids):
        dupes = [cid for cid, n in Counter(ids).items() if n > 1]
        raise RuntimeError(f"Duplicate acquisition IDs remain after qualification: {dupes}")
    return ids, len(seed_ids)


def build_lookup_v3() -> dict[str, dict[str, str]]:
    lookup: dict[str, dict[str, str]] = {}

    # Historical/retrieval seed metadata.
    for row in base.read_csv(RECON / "retrieval_manifest.csv"):
        cid = (row.get("recovery_id") or "").strip()
        if cid:
            lookup[cid] = {
                "candidate_id": cid,
                "raw_candidate_id": cid,
                "title": row.get("title", ""),
                "year": row.get("year", ""),
                "publisher": row.get("publisher", ""),
                "url": row.get("url", ""),
                "source": "retrieval_manifest",
            }

    for row in base.read_csv(RECON / "institutional_replacement_candidates.csv"):
        cid = (row.get("candidate_id") or "").strip()
        if cid:
            lookup[cid] = {
                "candidate_id": cid,
                "raw_candidate_id": cid,
                "title": row.get("document_title", ""),
                "year": row.get("year", ""),
                "publisher": row.get("party_or_source", ""),
                "url": row.get("url", ""),
                "source": "institutional_replacement_candidates",
            }

    # Every prospectively screened expansion record, collision-safe.
    for path, row, raw_id in _EXPANSIONS:
        cid = acquisition_id(path, raw_id)
        lookup[cid] = {
            "candidate_id": cid,
            "raw_candidate_id": raw_id,
            "title": row.get("title", ""),
            "year": row.get("year", ""),
            "publisher": row.get("publisher", ""),
            "url": row.get("url", ""),
            "source": path.name,
        }

    # Transparent URL/source overrides. For collided expansion IDs, title is used
    # to identify the intended record so an override cannot leak to another file.
    if OVERRIDES.exists():
        with OVERRIDES.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                raw_id = (row.get("candidate_id") or "").strip()
                title = (row.get("title") or "").strip()
                targets = []
                if raw_id in lookup:
                    targets.append(raw_id)
                targets.extend(
                    key for key, meta in lookup.items()
                    if key != raw_id
                    and meta.get("raw_candidate_id") == raw_id
                    and (not title or meta.get("title") == title)
                )
                # Apply only when the target is unambiguous by ID/title.
                if len(targets) == 1:
                    key = targets[0]
                    lookup[key].update({
                        "title": row.get("title", lookup[key].get("title", "")),
                        "year": row.get("year", lookup[key].get("year", "")),
                        "publisher": row.get("publisher", lookup[key].get("publisher", "")),
                        "url": row.get("url", lookup[key].get("url", "")),
                        "source": "source_overrides",
                    })

    return lookup


def bounded_fetch(session, url: str, attempts: int = 2):
    """Bound failure latency while preserving failed URLs for later recovery."""
    last = ""
    for attempt in range(1, attempts + 1):
        try:
            response = session.get(url, timeout=30, allow_redirects=True)
            if response.status_code == 200:
                return response, ""
            last = f"HTTP {response.status_code}"
            if response.status_code in {401, 403, 404, 410}:
                return response, last
        except Exception as exc:
            last = f"{type(exc).__name__}: {exc}"
        base.time.sleep(attempt * 2)
    return None, last


base.row_is_eligible = eligible
base.candidate_ids = candidate_ids_v3
base.build_lookup = build_lookup_v3
base.fetch = bounded_fetch

if __name__ == "__main__":
    raise SystemExit(base.main())
