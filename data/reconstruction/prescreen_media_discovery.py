from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[2]
RECON = ROOT / "data" / "reconstruction"
DISC = RECON / "discovery"
INFILE = DISC / "media_discovery_urls.csv"
AUDIT = DISC / "media_discovery_prescreen.csv"
DIRECT = RECON / "expanded_media_candidates_discovery_direct.csv"
SUMMARY = DISC / "media_discovery_prescreen_summary.json"

CENTRAL = re.compile(r"(?:marikana|lonmin|farlam|nkaneng|wonderkop|bapo(?:-ba-mogale)?)", re.I)
DATE_DM = re.compile(r"/(?:article|opinionista)/(20\d{2})-(\d{2})-(\d{2})-")
DATE_SUFFIX = re.compile(r"-(20\d{2})-(\d{2})-(\d{2})(?:-|/?$)")


def read_rows(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def canon(url: str) -> str:
    p = urlsplit((url or "").strip())
    host = p.netloc.lower().removeprefix("www.")
    path = re.sub(r"/+", "/", p.path).rstrip("/")
    return urlunsplit(("https", host, path, "", ""))


def known_urls() -> set[str]:
    urls: set[str] = set()
    for path in [RECON / "retrieval_manifest.csv", RECON / "institutional_replacement_candidates.csv"]:
        if not path.exists():
            continue
        for r in read_rows(path):
            u = r.get("url") or ""
            if u:
                urls.add(canon(u))
    for path in RECON.glob("expanded_*_candidates*.csv"):
        if path.name == DIRECT.name:
            continue
        for r in read_rows(path):
            u = r.get("url") or ""
            if u:
                urls.add(canon(u))
    return urls


def year_from_url(url: str) -> str:
    m = DATE_DM.search(url) or DATE_SUFFIX.search(url)
    return m.group(1) if m else ""


def slug_title(url: str) -> str:
    slug = urlsplit(url).path.rstrip("/").split("/")[-1]
    slug = re.sub(r"^20\d{2}-\d{2}-\d{2}-", "", slug)
    slug = re.sub(r"-20\d{2}-\d{2}-\d{2}(?:-\d+)?$", "", slug)
    return re.sub(r"[-_]+", " ", slug).strip().title()


known = known_urls()
audit = []
direct = []
counts = Counter()
pub_counts = Counter()
seen_new = set()

for idx, row in enumerate(read_rows(INFILE), 1):
    publisher = row.get("publisher", "")
    url = row.get("url", "")
    cu = canon(url)
    year = year_from_url(url)
    path_text = urlsplit(url).path.lower()
    if cu in known:
        status = "already_screened"
    elif cu in seen_new:
        status = "duplicate_discovery_url"
    elif year and not (2010 <= int(year) <= 2023):
        status = "exclude_outside_period"
    elif not year:
        status = "review_year_unresolved"
    elif CENTRAL.search(path_text):
        status = "direct_case_title_pending_acquisition"
    else:
        status = "secondary_keyword_only_review"
    seen_new.add(cu)
    counts[status] += 1
    pub_counts[(publisher, status)] += 1
    audit.append({"publisher": publisher, "url": url, "canonical_url": cu, "year": year, "prescreen_status": status})
    if status == "direct_case_title_pending_acquisition":
        cid = f"DISC-MEDIA-{len(direct)+1:04d}"
        direct.append({
            "candidate_id": cid,
            "source_family": "media",
            "title": slug_title(url),
            "year": year,
            "publisher": publisher,
            "url": url,
            "screening_status": "eligible_pending_acquisition",
            "decision_reason": "Discovered from documented publisher archive/sitemap; publication is within 2010-2023 and URL title is explicitly Marikana/Lonmin/Farlam/Bapo/Nkaneng/Wonderkop-centred. Final inclusion remains subject to acquisition, text quality, duplicate and substantive QC.",
            "search_id": "SEARCH-MEDIA-ARCHIVE-PRESCREEN",
            "source_universe": "strict_documented",
        })

AUDIT.parent.mkdir(parents=True, exist_ok=True)
with AUDIT.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=audit[0].keys()); w.writeheader(); w.writerows(audit)
with DIRECT.open("w", encoding="utf-8", newline="") as f:
    fields = ["candidate_id","source_family","title","year","publisher","url","screening_status","decision_reason","search_id","source_universe"]
    w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(direct)
summary = {
    "discovered_urls": len(audit),
    "status_counts": dict(counts),
    "direct_case_new_candidates": len(direct),
    "publisher_status_counts": {f"{p}::{s}": n for (p,s),n in sorted(pub_counts.items())},
    "note": "Automated pre-screen only; secondary-keyword URLs are preserved for reviewer screening and are not silently excluded."
}
SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
