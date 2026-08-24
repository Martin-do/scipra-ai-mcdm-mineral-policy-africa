# SCIPRA reconstructed corpus — external review handoff

## Status

This is a **pre-model, pre-label, non-frozen reconstruction snapshot**. It must not be described as the final SCIPRA corpus or as the exact historical 87-document corpus.

The manuscript historically reported **N=87**. During reproducibility reconstruction, that number was demoted from a target to a historical benchmark. Corpus membership is now determined prospectively by the documented retrieval and source-family rules.

## Screened/acquired snapshot

- Candidates processed in this screened-only snapshot: **366**
- Acquisition status: **{"acquired_extracted": 359, "acquired_low_text": 2, "acquired_no_text": 5}**
- Unique extracted texts after exact SHA-256 deduplication, before manual exclusions: **303**
- Preliminary screened corpus after exact deduplication and prospective exclusions: **301**
- Acquisition exceptions: **7**
- Exact duplicate clusters / redundant records: **54 / 56**
- Same-title/year clusters still flagged: **7**
- Same-URL clusters still flagged: **2**
- Near-duplicate pairs at similarity >= 0.95: **7**

The main row-level dataset for review is `screened_qc_preliminary_unique_text_manifest.csv`. It contains source URLs, metadata, acquisition details and text hashes; it does **not** redistribute full copyrighted news text.

## Archive-discovery queue — not yet corpus members

A reproducible archive/sitemap discovery pass produced **2076** URLs from the documented media publishers that the crawler could enumerate.

- Direct case-title new candidates: **690** (`archive_direct_case_review_queue.csv`)
- Secondary-keyword review queue: **1062** (`archive_secondary_keyword_review_queue.csv`)
- Year-unresolved review queue: **7** (`archive_year_unresolved_review_queue.csv`)

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
