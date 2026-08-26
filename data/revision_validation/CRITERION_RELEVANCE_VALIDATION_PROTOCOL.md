# SCIPRA Revision — Independent Criterion-Relevance Validation Protocol

## Status and boundary

This protocol belongs to a new **post-audit validation layer**. It does not alter the frozen historical audit, the frozen reconstructed corpus, or the Outcome C provenance determination.

The purpose is to test the construct validity of the documentary stakeholder-by-criterion relevance proxy `A_sj` used in the revised SCIPRA method. The automated criterion-relevance decisions are treated as a classifier to be checked against independent human judgement; they are not treated as ground truth.

The validation protocol is **pre-specified and locked before human coding begins**. There is no claim of external preregistration.

## Core question

Does the automated document-level relevance rule identify whether a document substantively addresses each named decision criterion with enough agreement and diagnostic performance to justify using `A_sj` as an empirical discourse-relevance proxy?

This validation does **not** ask whether the resulting criterion weights are normatively correct.

## Population

The validation population is the same frozen revision population used for the criterion-relevance matrix:

- documents with a finalized reconstructed stance label;
- documents with a resolved final stakeholder attribution; and
- documents whose source text was freshly recovered for the criterion-relevance analysis.

The existing primary automated decision is the pre-specified 2-sentence / 2-distinct-family rule in `criterion_relevance_document_audit.csv` (`relevant_s2_f2`).

## Sampling design

Sampling occurs at the **document level**, not by hand-picking individual document–criterion pairs.

1. Set deterministic random seed to `20260826`.
2. Within each of the five resolved stakeholder groups, select 12 documents (target total `n = 60`).
3. Selection uses a deterministic greedy diversity algorithm over the six-dimensional automated primary relevance vector. The objective is to improve positive/negative coverage for each criterion while also representing different automated relevance profiles.
4. Every sampled document is independently judged for **all six criteria**, yielding a target of 360 document–criterion judgements per coder.
5. If a stakeholder group has fewer than 12 eligible documents, use all eligible documents and report the shortfall. Do not replace the missing cases by tuning toward any desired criterion result.
6. Sampling is fixed before any human labels are entered. The generated sample manifest and its SHA-256 are retained.

The sampling algorithm may use the automated relevance labels only for **stratification/coverage**, never as information shown to the coders.

## Blinding

Coders receive:

- sample ID;
- record ID;
- title;
- year;
- publisher/source;
- source URL;
- criterion name;
- conceptual criterion definition; and
- blank judgement fields.

Coders do **not** receive:

- the automated relevance label;
- matched-sentence counts;
- phrase-family counts;
- the regex/lexicon list;
- stakeholder group used in the revised aggregation;
- `A_sj` values;
- revised criterion weights; or
- the historical Table 2 values.

The automated key is stored separately and is opened only after both first-pass coder files are locked.

## Human coding scale

Each document–criterion pair is coded independently as:

- `Relevant` — the document substantively addresses the criterion as defined below;
- `Not relevant` — the criterion is absent, incidental, or merely mentioned without substantive treatment; or
- `Uncertain` — available text is insufficient or the case cannot be resolved confidently from the definition.

Coders also record a short rationale and confidence (`1 = low`, `2 = moderate`, `3 = high`).

No coder may inspect the automated key before completing and locking the first pass.

## Conceptual criterion definitions

### NPV

Substantive discussion of project/investment valuation through present-value logic, discounted future cash flows, capital-investment value, or an equivalent project-value concept. Generic references to money, costs, revenue, or company finances do not qualify unless tied to project/investment valuation.

### IRR

Substantive discussion of an investment return rate, rate-of-return/profitability criterion, return on investment, or an equivalent return-performance concept. Generic profit/revenue language without a return-rate or investment-return concept does not automatically qualify.

### Geological Feasibility

Substantive discussion of the mineral deposit or mine's geological/technical resource basis, including orebody characteristics, reserves/resources, ore grade, mine life, resource base, or geological/mining feasibility.

### Market Stability

Substantive discussion of commodity/platinum market conditions affecting project viability, such as prices, demand, supply, market volatility, market stability, or commodity-market conditions.

### Local Employment

Substantive discussion of **employment opportunities, employment creation/retention/loss, local hiring, workforce numbers, retrenchment/layoffs, or the availability of jobs for local/affected people**. Generic references to workers, labour disputes, unions, strikes, wages, or mineworkers do **not** qualify by themselves unless the passage substantively concerns employment quantity, availability, creation, retention, loss, or local hiring. This exclusion is deliberate because the earlier semantic-sensitivity audit showed that broad labour-conflict terminology can inflate this criterion.

### Community Infrastructure

Substantive discussion of physical or social infrastructure/services for affected communities, including housing/accommodation, schools, clinics/healthcare facilities, roads, water, sanitation, electricity, community facilities/development infrastructure, or infrastructure commitments under a Social and Labour Plan.

## Independent coding and adjudication

Two coders independently complete the same blinded sample.

After both first-pass files are locked:

1. calculate raw inter-coder agreement before any adjudication;
2. disclose disagreements only after first-pass lock;
3. adjudicate disagreements using the same conceptual definitions, without viewing the automated label where practicable;
4. retain both original coder labels and the adjudicated reference label;
5. only then compare the automated primary rule with the adjudicated manual reference.

`Uncertain` is retained as a first-class outcome in the raw coder record. Primary binary diagnostic analysis excludes unresolved `Uncertain` cases unless they are resolved during adjudication. The number and distribution of uncertain cases must be reported.

## Validation metrics

Report at minimum:

### Inter-coder reliability

- exact percent agreement;
- Cohen's kappa for resolved binary Relevant / Not relevant judgements;
- criterion-specific percent agreement and kappa where estimable.

### Automated-rule diagnostic performance against adjudicated manual reference

- sensitivity/recall;
- specificity;
- positive predictive value (precision);
- negative predictive value;
- balanced accuracy;
- F1 score;
- confusion matrix;
- criterion-specific diagnostic metrics;
- exploratory stakeholder-group breakdowns, clearly labelled as exploratory because cell sizes are smaller.

## Interpretation targets

The following are **interpretive targets, not post-hoc pass/fail rules**:

- Cohen's kappa around or above `0.60` would support substantial inter-coder reliability;
- balanced accuracy around or above `0.75` would provide useful evidence that the automated proxy distinguishes relevant from non-relevant documents;
- criterion-level results must be inspected even if the pooled metric is strong;
- Local Employment receives explicit scrutiny because the prior semantic-sensitivity audit already identified construct fragility.

A strong pooled score cannot conceal a poorly performing individual criterion.

## Decision logic after validation

### If performance is broadly adequate

Retain `A_sj` as a **documentary discourse-relevance proxy**, not a normative preference matrix. Report manual-validation results alongside semantic-sensitivity analysis.

### If one or more criteria perform poorly

Do not tune terms until the desired revised weight appears. Instead:

1. document the failure;
2. revise the conceptual ontology/operational definition transparently;
3. version the revised mapping as a new post-audit method;
4. evaluate it on a **new locked validation sample or held-out validation subset**;
5. retain the original automated result as part of the audit trail.

### If performance is generally inadequate

Do not use automated `A_sj` values for substantive policy-weight claims. The criterion-specific propagation equation may remain as a mathematically valid methodological proposal, but the Marikana empirical weighting demonstration must be presented as exploratory or removed from the central evidence.

## Contention term

The primary validation concerns `A_sj`. In the revised manuscript, the core propagation should use structural salience and criterion relevance:

`G_j = sum_s(SIC_s * A_sj) / sum_s(SIC_s)`

`W*_j = W0_j(1 + delta * G_j) / sum_k[W0_k(1 + delta * G_k)]`

The contention modifier may be reported as an **optional dynamic extension**:

`E_s = SIC_s * C_s`

because the existing Marikana component ablation shows that contention adds only a very small incremental weight effect in this case. This is an empirical demotion, not a claim that contention is mathematically invalid in all settings.

## Historical-score firewall

Historical A/B/C I/R/S scenario values are not used to validate the revised criterion-specific method. They may appear only in an explicitly labelled historical reproducibility/audit table, preferably in supplementary material.

## Files produced by the validation workflow

The companion sample-builder creates:

- `criterion_relevance_validation_sample_blinded.csv`
- `criterion_relevance_validation_key.csv`
- `criterion_relevance_validation_sample_summary.json`

After two coder files are completed, the companion analysis script creates:

- `criterion_relevance_validation_agreement.csv`
- `criterion_relevance_validation_diagnostics.csv`
- `criterion_relevance_validation_summary.json`

All generated files should be hashed and retained with the final revision archive.
