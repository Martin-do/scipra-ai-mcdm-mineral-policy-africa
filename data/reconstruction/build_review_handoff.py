from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECON = ROOT / "data" / "reconstruction"
ACQ = ROOT / "acquisition_output"
OUT = RECON / "review_handoff"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def copy(src: Path, dest_name: str | None = None):
    if src.exists():
        shutil.copy2(src, OUT / (dest_name or src.name))


def filter_csv(src: Path, dest: Path, predicate):
    with src.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    chosen = [r for r in rows if predicate(r)]
    if not rows:
        return 0
    with dest.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(chosen)
    return len(chosen)


OUT.mkdir(parents=True, exist_ok=True)

# Core screened acquisition/QC snapshot (the auto-discovered direct queue is
# deliberately excluded by the calling workflow).
copy(ACQ / "acquisition_status.csv", "screened_acquisition_status.csv")
copy(ACQ / "summary.json", "screened_acquisition_summary.json")
qcout = ACQ / "qc"
for name in [
    "summary.json",
    "preliminary_unique_text_manifest.csv",
    "acquisition_exceptions.csv",
    "exact_duplicate_clusters.csv",
    "same_title_year_review.csv",
    "same_url_review.csv",
    "near_duplicate_review.csv",
    "manual_exclusions.csv",
]:
    copy(qcout / name, f"screened_qc_{name}")

# Protocol/provenance materials.
for name in [
    "RECONSTRUCTION_PROTOCOL.md",
    "SOURCE_FAMILY_RULES.md",
    "source_family_status.csv",
    "retrieval_search_log.csv",
    "manual_qc_decisions.csv",
    "candidate_corpus_87.csv",
    "retrieval_manifest.csv",
    "institutional_replacement_candidates.csv",
    "source_overrides.csv",
]:
    copy(RECON / name)

# Archive discovery queues: these are NOT part of the screened corpus snapshot.
copy(RECON / "expanded_media_candidates_discovery_direct.csv", "archive_direct_case_review_queue.csv")
prescreen = RECON / "discovery" / "media_discovery_prescreen.csv"
secondary_n = filter_csv(
    prescreen,
    OUT / "archive_secondary_keyword_review_queue.csv",
    lambda r: r.get("prescreen_status") == "secondary_keyword_only_review",
)
unresolved_n = filter_csv(
    prescreen,
    OUT / "archive_year_unresolved_review_queue.csv",
    lambda r: r.get("prescreen_status") == "review_year_unresolved",
)
for name in [
    "media_discovery_summary.json",
    "media_discovery_prescreen_summary.json",
    "media_discovery_endpoint_audit.csv",
]:
    copy(RECON / "discovery" / name)

acq = read_json(ACQ / "summary.json")
qc = read_json(qcout / "summary.json")
disc = read_json(RECON / "discovery" / "media_discovery_prescreen_summary.json")

handoff = {
    "snapshot_type": "screened_reconstruction_review_snapshot",
    "corpus_frozen": False,
    "historical_manuscript_benchmark_n": 87,
    "screened_candidates_processed": acq.get("processed_candidates"),
    "screened_status_counts": acq.get("status_counts"),
    "screened_unique_extracted_texts_after_exact_dedup_before_manual_exclusions": qc.get("unique_extracted_texts_after_exact_dedup_before_manual_exclusions"),
    "screened_preliminary_corpus_after_exact_dedup_and_prospective_exclusions": qc.get("preliminary_corpus_records_after_exact_dedup_and_prospective_exclusions"),
    "screened_acquisition_exceptions": qc.get("acquisition_exception_records"),
    "exact_duplicate_clusters": qc.get("exact_duplicate_clusters"),
    "exact_duplicate_redundant_records": qc.get("exact_duplicate_redundant_records"),
    "same_title_year_review_clusters": qc.get("same_title_year_clusters_requiring_review"),
    "same_url_review_clusters": qc.get("same_url_clusters_requiring_review"),
    "near_duplicate_pairs_ge_0_95": qc.get("near_duplicate_pairs_flagged_at_similarity_ge_0_95"),
    "archive_discovered_urls": disc.get("discovered_urls"),
    "archive_direct_case_new_review_queue": disc.get("direct_case_new_candidates"),
    "archive_secondary_keyword_review_queue": secondary_n,
    "archive_year_unresolved_review_queue": unresolved_n,
    "important_note": "The preliminary screened corpus is not the final corpus. Archive discovery revealed additional candidates that must be substantively screened before corpus freeze. No stance labels or model results were used to determine membership.",
}
(OUT / "HANDOFF_SUMMARY.json").write_text(json.dumps(handoff, indent=2), encoding="utf-8")

readme = f"""# SCIPRA reconstructed corpus — external review handoff

## Status

This is a **pre-model, pre-label, non-frozen reconstruction snapshot**. It must not be described as the final SCIPRA corpus or as the exact historical 87-document corpus.

The manuscript historically reported **N=87**. During reproducibility reconstruction, that number was demoted from a target to a historical benchmark. Corpus membership is now determined prospectively by the documented retrieval and source-family rules.

## Screened/acquired snapshot

- Candidates processed in this screened-only snapshot: **{acq.get('processed_candidates')}**
- Acquisition status: **{json.dumps(acq.get('status_counts', {}), sort_keys=True)}**
- Unique extracted texts after exact SHA-256 deduplication, before manual exclusions: **{qc.get('unique_extracted_texts_after_exact_dedup_before_manual_exclusions')}**
- Preliminary screened corpus after exact deduplication and prospective exclusions: **{qc.get('preliminary_corpus_records_after_exact_dedup_and_prospective_exclusions')}**
- Acquisition exceptions: **{qc.get('acquisition_exception_records')}**
- Exact duplicate clusters / redundant records: **{qc.get('exact_duplicate_clusters')} / {qc.get('exact_duplicate_redundant_records')}**
- Same-title/year clusters still flagged: **{qc.get('same_title_year_clusters_requiring_review')}**
- Same-URL clusters still flagged: **{qc.get('same_url_clusters_requiring_review')}**
- Near-duplicate pairs at similarity >= 0.95: **{qc.get('near_duplicate_pairs_flagged_at_similarity_ge_0_95')}**

The main row-level dataset for review is `screened_qc_preliminary_unique_text_manifest.csv`. It contains source URLs, metadata, acquisition details and text hashes; it does **not** redistribute full copyrighted news text.

## Archive-discovery queue — not yet corpus members

A reproducible archive/sitemap discovery pass produced **{disc.get('discovered_urls')}** URLs from the documented media publishers that the crawler could enumerate.

- Direct case-title new candidates: **{disc.get('direct_case_new_candidates')}** (`archive_direct_case_review_queue.csv`)
- Secondary-keyword review queue: **{secondary_n}** (`archive_secondary_keyword_review_queue.csv`)
- Year-unresolved review queue: **{unresolved_n}** (`archive_year_unresolved_review_queue.csv`)

These records are deliberately kept separate from the screened corpus. A title-level match is not enough for final inclusion; they require substantive eligibility, acquisition/text-quality and duplicate review.

Mining Weekly's historical sitemap coverage was incomplete, so its manually recovered records remain valid and the crawler's zero historical Mining Weekly count must **not** be interpreted as absence of Mining Weekly material.

## Major reproducibility findings

1. The original supplementary description of **13 EITI South Africa documents is not recoverable as described**; South Africa is not an EITI implementing country. The reconstructed corpus therefore must be disclosed as a reconstructed replication corpus, not represented as the exact original 87 documents.
2. `Policy Gap 10` is about Kumba Iron Ore/Sishen and was prospectively excluded as outside the declared Marikana/Lonmin scope. `Policy Gap 7` is the directly Lonmin-focused Bench Marks follow-up and is represented in the reconstruction pool.
3. Repeated retrieval showed that stopping at 87 would artificially truncate the recoverable source universe. Final N must be an outcome of the retrieval protocol.
4. No historical class target (including the manuscript's reported 71/16 distribution), SVM metric, stance label or downstream model result was used to select documents.

## Source-family status

See `source_family_status.csv` for the formal closure table. At this snapshot:

- Marikana Commission / Justice: retrieval saturated under the fixed genre rules.
- Government / Parliament / regulator: retrieval saturated under the fixed case-centrality rules.
- NGO/civil society: source discovery saturated; newly resolved SERI/CER documents are included in this screened acquisition snapshot and remain subject to acquisition/QC outcomes.
- Corporate Lonmin/Sibanye-Stillwater: source discovery saturated; final release URLs are resolved, while protected report-host files remain transparent acquisition exceptions where applicable.
- Media: archive discovery completed for enumerable Daily Maverick/Engineering News endpoints; substantive screening of the newly discovered queues remains outstanding. Mining Weekly requires the preserved manual search pathway because its historical sitemap is incomplete.

## What has NOT been done

- Corpus is **not frozen**.
- No stance labels have been assigned for the reconstructed corpus.
- No class distribution has been accepted or targeted.
- No TF-IDF/SVM model has been rerun on this reconstruction.
- No manuscript metrics have been used as acceptance criteria.

## Recommended reviewer questions

1. Are the predeclared source-family rules sufficiently precise and defensible?
2. Should Commission Heads of Argument and expert analytical papers be retained in the same NLP corpus as media/corporate documents, or analysed as a stratified source family?
3. Are broader governance reports such as CER documents sufficiently Marikana/Lonmin-centred for the strict corpus?
4. Is the exact/near-duplicate strategy adequate for Creamer Media mirrors and republications?
5. Should the 690 direct-case archive candidates all undergo full-text substantive screening, or should a narrower prospective title/document-type rule be specified before that screening?
6. Should source-family proportions be reported/stratified rather than attempting to reproduce the historical 58/11/etc. quotas?
7. Is the term **reconstructed replication corpus** appropriate given that the claimed EITI block cannot be recovered as originally described?

## Key files

- `screened_qc_preliminary_unique_text_manifest.csv` — current preliminary unique screened corpus manifest.
- `screened_acquisition_status.csv` — every screened candidate's acquisition/extraction result, hashes and source URL.
- `screened_qc_acquisition_exceptions.csv` — acquisition/text exceptions.
- `screened_qc_exact_duplicate_clusters.csv` — exact duplicate provenance.
- `screened_qc_near_duplicate_review.csv` — high-similarity cases requiring review.
- `archive_direct_case_review_queue.csv` — newly discovered direct Marikana/Lonmin/etc. URL candidates, not yet corpus members.
- `archive_secondary_keyword_review_queue.csv` — ambiguous archive matches preserved for review.
- `RECONSTRUCTION_PROTOCOL.md`, `SOURCE_FAMILY_RULES.md`, `retrieval_search_log.csv`, `source_family_status.csv` — methodology and retrieval audit trail.

## Reproducibility boundary

This handoff contains manifests, URLs, hashes, acquisition/QC records and protocol material. Full copyrighted news article text is not redistributed in this review folder. The repository acquisition workflow records how source material was retrieved/extracted so an authorised reviewer can reproduce the acquisition from the original public URLs.
"""
(OUT / "README.md").write_text(readme, encoding="utf-8")

checklist = """# External reviewer checklist

Please review before any corpus freeze or model rerun:

- [ ] Historical N=87 is treated only as a benchmark, not a stopping rule.
- [ ] EITI South Africa provenance problem and reconstruction disclosure are acceptable.
- [ ] Date window and Marikana/Lonmin case-centrality rules are appropriate.
- [ ] Source-family genre rules are appropriate.
- [ ] Commission submissions/expert papers are comparable enough to retain, or should be stratified.
- [ ] Government/NGO/corporate source-family closure decisions are defensible.
- [ ] Archive direct-case review queue should be substantively screened under the current rules.
- [ ] Secondary-keyword archive queue handling is sufficiently conservative.
- [ ] Mining Weekly incomplete sitemap limitation is documented adequately.
- [ ] Exact duplicate and near-duplicate rules are adequate.
- [ ] Prospective manual exclusions are justified without reference to model results.
- [ ] Final corpus must be frozen and hashed before stance annotation/model fitting.
- [ ] Observed class distribution must be reported after annotation, not engineered to historical 71/16.
"""
(OUT / "REVIEWER_CHECKLIST.md").write_text(checklist, encoding="utf-8")

print(json.dumps(handoff, indent=2))
