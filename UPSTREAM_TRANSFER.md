# Canonical upstream transfer

## Canonical repository

The final non-manuscript SCIPRA reproducibility workflow belongs in:

`igeoo/scipra-ai-mcdm-mineral-policy-africa`

The `Martin-do` fork is an isolated development workspace only.

## Source branch for upstream transfer

`Martin-do/scipra-ai-mcdm-mineral-policy-africa:robustness-swdc-revision`

This branch is cumulative: it contains the dataset reconstruction, frozen corpus audit, post-freeze annotation/model reconstruction, mathematical reproducibility audit, stance-robustness analysis, corrected SWDC revision analysis, reviewer materials and integrity metadata.

## Upstream base

`igeoo/scipra-ai-mcdm-mineral-policy-africa:main`

The upstream `main` branch was verified during reconstruction to remain at historical commit:

`89369ea8d9679aa79ed42eea0019bc0b9d722fb0`

## Required upstream action

Open a pull request from the source branch above into `igeoo/main`, review it, and merge it once the revision freeze files are present and verified.

The ChatGPT GitHub integration currently has read-only permission on the `igeoo` repository, so it cannot push or create that upstream pull request directly. No additional computational work should be required before the transfer once the revision freeze is complete.

## Repository scope

Include in the canonical repository:
- reconstruction protocols and manifests;
- frozen corpus metadata and hashes;
- post-freeze reconstructed annotation/model outputs;
- mathematical audits;
- reproducibility scripts and GitHub Actions workflows;
- robustness/sensitivity analyses;
- corrected SWDC revision code and evidence-derived criterion-relevance outputs;
- reviewer handoff/offline bundle workflows;
- integrity manifests and freeze summaries.

Do **not** treat the rewritten manuscript itself as a repository requirement. Manuscript drafting/revision remains outside this canonical computational transfer unless the authors separately decide to archive a manuscript version.

## Scientific boundary

The upstream package must preserve the distinction between:
1. historical SCIPRA claims;
2. independently reconstructed replication results; and
3. proposed corrected SCIPRA revision results.

No revision output should be described as if it were recovered from the historical implementation.
