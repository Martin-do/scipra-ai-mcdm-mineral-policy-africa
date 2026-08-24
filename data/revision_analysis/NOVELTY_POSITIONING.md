# SCIPRA Revision — Novelty Positioning

## Status

This is a targeted positioning note, **not a systematic literature review** and not evidence for an absolute `first-ever` claim.

The revised SCIPRA contribution should be framed narrowly because several neighboring ideas already exist independently.

## What is not novel by itself

### Stakeholder-specific MCDA weights

Stakeholder-specific or multi-actor criterion weighting is established in MCDA/MAMCA practice. For example:

- Putro, Pradono & Setiawan (2021), *Development of Multi-Actor Multi-Criteria Analysis Based on the Weight of Stakeholder Involvement in the Assessment of Natural–Cultural Tourism Area Transportation Policies*, **Algorithms 14(7), 217**, DOI: `10.3390/a14070217`.
- Weber & Köppel (2022), *Can MCDA Serve Ex-Post to Indicate ‘Winners and Losers’ in Sustainability Dilemmas? A Case Study of Marine Spatial Planning in Germany*, **Energies 15(20), 7654**, DOI: `10.3390/en15207654`. The study derives stakeholder values/criterion relevance from submitted planning statements and performs stakeholder-specific MCDA/sensitivity analysis.

Therefore revised SCIPRA should not claim novelty simply for allowing different stakeholders to affect criterion weights.

### Text analytics combined with MCDM

Text-driven MCDM is also established. For example:

- Pérez Rave, Jaramillo Álvarez & Correa Morales (2022), *Multi-criteria decision-making leveraged by text analytics and interviews with strategists*, **Journal of Marketing Analytics 10(1), 30–49**, DOI: `10.1057/s41270-021-00125-8`. The framework uses text analytics to discover, validate and prioritize decision patterns/criteria.
- Text-mining/MCDM studies also derive criteria or objective weights from topic frequencies/proportions and other textual signals.

Therefore revised SCIPRA should not claim novelty simply for combining NLP/text mining with MCDM.

### Sentiment analysis combined with MCDM

Prior decision frameworks combine aspect-level sentiment/text mining with MCDM ranking methods. Therefore the use of an NLP-derived positive/negative signal in a decision framework is not sufficient as a novelty claim.

### Stakeholder salience theory

Power–Legitimacy–Urgency stakeholder salience is an established theoretical construct. Dynamic or context-sensitive stakeholder salience mapping also predates SCIPRA. The revision must therefore not claim novelty for SIC/PLU alone.

## Candidate gap identified by the present reconstruction

The historical SCIPRA code attempted to propagate stakeholder salience into criterion weights using one scalar multiplier:

`W_a = W_0 * (1 + delta*SIC)`

followed by vector normalization. The reconstruction proves that the common multiplier cancels, leaving relative criterion weights unchanged.

The proposed revision introduces the missing criterion-specific object explicitly:

- structural stakeholder salience: `SIC_s`
- observed stakeholder contention: `C_s = 1 - P_s(pro-integration)`
- stakeholder-by-criterion discourse relevance: `A_sj`
- salience-weighted pressure: `E_s = SIC_s*C_s`
- criterion-specific pressure: `G_j = sum_s(E_s*A_sj)/sum_s(E_s)`
- normalized criterion update: `W*_j = W0_j(1+delta*G_j)/sum_k W0_k(1+delta*G_k)`

## Defensible candidate contribution

A cautious contribution statement is:

> The revised framework couples structural stakeholder salience, empirically observed stakeholder contention, and criterion-specific issue relevance from a frozen governance corpus to produce transparent, non-degenerate criterion-weight updates in mineral-policy MCDA.

The targeted literature search conducted during reconstruction identified prior work on each neighboring component—stakeholder-specific MCDA, text-derived criterion weighting, sentiment-assisted MCDM, and dynamic stakeholder salience—but did not identify an obvious implementation of this exact three-factor propagation architecture in mineral-policy convergence.

This supports a **candidate methodological gap**, not an absolute priority claim.

## Language recommended for a manuscript

Prefer:

> "Building on stakeholder-salience, text-analytics and multi-actor MCDA literatures, this study introduces a criterion-specific propagation mechanism that jointly incorporates stakeholder salience, observed contention and documentary issue relevance."

Or, after a fuller systematic search:

> "To our knowledge, prior mineral-policy MCDA frameworks have not operationalized stakeholder salience, observed discourse contention and criterion-specific documentary relevance within a single normalized dynamic-weighting rule."

Avoid:

- "the first stakeholder-aware MCDM framework"
- "the first NLP-MCDM framework"
- "the first dynamic stakeholder weighting model"
- "the first use of text mining to derive MCDA weights"

Those broader claims are not supportable.

## Separate empirical contribution

The stance result is independent of the corrected-model novelty. The static robustness audit shows that, on the independently reconstructed frozen corpus, the historical pro-integration-dominant conclusion does not reproduce under either computational reading, the final adjudicated ledger, or 35 alternative adjudication settings. This can be presented as an empirical reproducibility/robustness contribution even if the corrected SWDC formulation is ultimately treated as future methodological development.

## Remaining literature task before submission

Before using `to our knowledge` language in a manuscript, conduct a structured search across at least Scopus/Web of Science/Google Scholar using combinations of:

- stakeholder salience + MCDA/MCDM/AHP
- stakeholder-specific/dynamic weights + mining/mineral policy
- issue salience/contention + MCDA
- sentiment/text mining + dynamic criterion weights
- multi-actor MCDA + unstructured text
- stakeholder claims + criterion relevance/weighting

Record search strings, dates, databases, inclusion criteria and nearest methodological comparators.
