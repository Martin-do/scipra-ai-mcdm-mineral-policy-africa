# SCIPRA Corpus Reconstruction Protocol

## Purpose

This branch reconstructs a traceable Marikana document corpus before any NLP/SVM code, labels, or reported model metrics are altered. The objective is to prevent outcome-driven corpus selection and to ensure that the computational pipeline is tailored to a frozen, auditable dataset.

## Original manuscript corpus claim

The supplementary material describes an 87-document corpus with the following source composition:

- 13 EITI documents
- 1 Farlam Commission report
- 2 Bench Marks Foundation reports
- 1 SERI document
- 1 Centre for Environmental Rights document
- 58 news/media documents
- 11 corporate engagement reports

Total: 87 documents.

## Provenance problem identified

South Africa is not an EITI implementing country. Therefore the claimed block of 13 South Africa EITI documents cannot presently be recovered as described. It must not be recreated synthetically or replaced without disclosure.

The reconstruction therefore preserves two distinct concepts:

1. **Recovered/original-category records**: documents matching a source category stated in the manuscript and independently verified.
2. **Replacement candidates**: transparent substitutes proposed only where an original category cannot be reconstructed. Replacement status must remain explicit in metadata and in any revised manuscript.

## Replacement rule for the invalid EITI block

A fixed, outcome-independent candidate set of 13 official Marikana Commission stakeholder/institutional submissions has been defined in `institutional_replacement_candidates.csv`.

Selection rule:

- document must be listed by the South African Department of Justice on the official Marikana Commission documents page;
- document must be a substantive Heads of Argument filing rather than an administrative Gazette notice;
- selection should span materially distinct stakeholder or institutional perspectives;
- selection occurs before stance annotation and before any NLP/SVM fitting;
- documents are not selected or removed based on whether they improve agreement with previously reported classifier metrics.

The 13 candidates comprise AMCU, Bapo ba Mogale, DMR/Shabangu, Evidence Leaders, Families, Injured and Arrested Persons, Lonmin, LRC, Mthethwa, NUM/Mrs Fundi, Ramaphosa, SAHRC, and SAPS.

## Media reconstruction rule

The recovery manifest contains 58 distinct media candidates from the publication universe identified in the manuscript: Mining Weekly, Engineering News, and Daily Maverick.

Inclusion criteria:

- publication date within the study period;
- direct substantive relevance to Marikana, Lonmin/Sibanye Marikana operations, the platinum strike, stakeholder conflict, community conditions, labour relations, regulatory response, ownership transition, or Marikana renewal;
- stable, article-specific URL;
- no duplicate mirror of the same story counted twice;
- selected before stance labels are assigned and without reference to model performance.

These are a **reconstructed candidate set** and are not represented as the exact unrecoverable original media sample unless documentary evidence later establishes identity.

## Corporate reconstruction rule

Corporate candidates are collected from official Lonmin/Sibanye-Stillwater reporting sources. Twelve candidates are currently logged. The final 11 must be selected using a source/content rule fixed before labeling, with preference for documents containing substantive Marikana stakeholder, social-and-labour-plan, renewal, housing, employment, or socioeconomic disclosures. Model performance must not influence selection.

## Annotation freeze

No stance labels, stakeholder-group assignments, TF-IDF features, P/L/U values, or SVM outputs should be generated until:

1. the corpus membership is frozen;
2. exact source metadata are recorded;
3. acquisition/text-extraction status is recorded;
4. duplicate documents are removed;
5. exact document hashes can be generated for redistributable/local copies or extracted text.

Annotation should then be performed independently of the previous reported class distribution and metrics.

## Reproducibility principle

If the reconstructed, auditable corpus produces different sample sizes, class proportions, salience scores, or classifier metrics from the original manuscript, the empirical claims must be revised to the regenerated results. The corpus or code must not be modified solely to recover predetermined numerical outputs.
