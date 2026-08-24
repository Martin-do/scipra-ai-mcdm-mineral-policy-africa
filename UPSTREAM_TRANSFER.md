# Canonical upstream transfer

## Canonical repository

The final non-manuscript SCIPRA reproducibility workflow belongs in:

`igeoo/scipra-ai-mcdm-mineral-policy-africa`

The `Martin-do` fork is an isolated development workspace only.

## Frozen source branch for upstream transfer

`Martin-do/scipra-ai-mcdm-mineral-policy-africa:canonical-upstream-transfer`

This branch is cumulative: it contains the dataset reconstruction, frozen corpus audit, post-freeze annotation/model reconstruction, mathematical reproducibility audit, stance-robustness analysis, corrected SWDC revision analysis, reviewer materials and integrity metadata.

## Upstream base

`igeoo/scipra-ai-mcdm-mineral-policy-africa:main`

The upstream `main` branch was verified during reconstruction to remain at historical commit:

`89369ea8d9679aa79ed42eea0019bc0b9d722fb0`

## Manuscript exclusion boundary

The computational/reproducibility repository must remain separate from the unpublished manuscript and submission package until the manuscript has been updated and the authors have approved its submission/archive status.

The canonical transfer therefore removes the historical tracked publication-document artifacts:

- `SCIPRA_04052026.docx`
- `appendices/SCIPRA_Supplementary_Material.docx`
- `appendices/SCIPRA_SI_References.docx`

The repository `.gitignore` also excludes `SCIPRA_*.docx` and `appendices/*.docx` to reduce the risk of reintroducing unpublished submission materials accidentally.

Any methodology facts previously recovered from those historical documents that are necessary for reproducibility are retained only through transparent text extracts, protocols, audit outputs, scripts and provenance records already committed to the workflow. The unpublished binary manuscript/submission documents themselves are not part of the canonical computational package.

The current upstream `igeoo/main` still contains the historical publication documents until the canonical cross-fork PR is merged. Merging the canonical transfer will remove them from the current repository tree; Git history is not rewritten.

## Required upstream action

Open a pull request from the frozen source branch above into `igeoo/main`, review it, and merge it.

The ChatGPT GitHub integration currently has read-only permission on the `igeoo` repository, so it cannot push, create, or merge that upstream pull request directly. No additional computational work is required before the transfer.

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

Do **not** include the unpublished/revised manuscript, submission manuscript, supplementary manuscript documents or submission-specific Word/PDF artifacts unless the authors later make an explicit archival decision after revision/approval.

## Scientific boundary

The upstream package must preserve the distinction between:
1. historical SCIPRA claims;
2. independently reconstructed replication results; and
3. proposed corrected SCIPRA revision results.

No revision output should be described as if it were recovered from the historical implementation.
