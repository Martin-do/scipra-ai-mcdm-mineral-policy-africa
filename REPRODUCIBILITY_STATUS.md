# SCIPRA Reproducibility Status

This document records the current state of the public reproducibility package relative to the manuscript **“Bridging the Investment-Regulatory-Stakeholder Divide: An AI-Enhanced MCDM Framework for Mineral Resource Policy Convergence in Africa.”**

## Current status

The repository is sufficient to inspect and reproduce parts of the SCIPRA mathematical framework, including downstream PCI/RPCI calculations from published scenario-domain inputs. It is **not yet sufficient for independent end-to-end empirical reproduction of the manuscript's 87-document NLP-SVM results**.

## Verified blockers

1. **Corpus-size mismatch**
   - Manuscript-reported corpus: 87 documents.
   - Current `data/processed/corpus_manifest.csv`: 13 documents.
   - Current `data/processed/svm_labels.csv`: 13 documents.
   - The remaining manuscript corpus records, labels, and full provenance are not present in the current package.

2. **Empirical table inputs are not reconstructed upstream**
   - `code/generate_tables.py` begins from the published scenario domain scores `(I, R, S)`.
   - This reproduces the PCI/RPCI arithmetic but not the empirical derivation of those domain scores.

3. **Stakeholder salience/SIC provenance requires reconciliation**
   - `data/processed/plu_scores.csv` contains both reported `SIC` and `SIC_computed` values.
   - Several rows differ materially, so the authoritative calibration pathway must be established before values are regenerated.

4. **P/L/U specification requires one authoritative definition**
   - The supplementary mathematical specification uses an indicator-style expression for salience term membership.
   - The current implementation counts term occurrences.
   - The manuscript text describes keyword-frequency patterns.
   - This should be reconciled explicitly rather than silently changing code or equations.

5. **Annotation reproducibility is incomplete**
   - The manuscript reports an annotation protocol and agreement statistics.
   - The package does not currently include per-annotator labels for all 87 records, so those agreement statistics cannot yet be independently regenerated.

## Repairs completed on `reproducibility-rework`

- Removed the machine-specific Windows manifest path from `code/execute_full_analysis.py`.
- Replaced fuzzy/manual document mapping with deterministic filename-based joining.
- Added strict corpus validation and fail-fast behaviour when the expected 87-document corpus is absent.
- Prevented the script from printing `N=87` when fewer documents are actually loaded.
- Added an explicit `--allow-partial` diagnostic mode that labels incomplete runs as non-manuscript results.
- Moved TF-IDF into an sklearn `Pipeline` so vocabulary and IDF fitting occur within each cross-validation training fold.
- Clarified that `code/generate_tables.py` reproduces downstream arithmetic from published scenario inputs rather than reconstructing those inputs from raw evidence.

## Required before claiming full empirical reproducibility

The following artefacts or equivalent derivation pathways are still required:

- Full 87-document corpus manifest.
- Stable source identifiers/URLs and access dates for all 87 documents.
- Full stance labels and stakeholder-group assignments.
- Original per-annotator labels and adjudication records if annotation-agreement claims are retained.
- One authoritative P/L/U scoring definition, implemented consistently in manuscript, SI, and code.
- Reconciled SIC values with a documented derivation or calibration source.
- End-to-end derivation of the scenario/domain scores used in PCI analysis.
- Regenerated SVM metrics using leakage-safe cross-validation.
- A clean-environment reproduction test demonstrating that reported outputs can be regenerated from the archived inputs.

## Scientific integrity rule for this rework

Missing empirical evidence will not be recreated by inference merely to match reported manuscript values. Where historical source data or original labels cannot be recovered, the manuscript and repository should state the limitation explicitly and narrow the corresponding reproducibility claim.
