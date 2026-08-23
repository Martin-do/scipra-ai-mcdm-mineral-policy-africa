"""Apply explicit reviewed decisions for batch 02 of the 154 low-signal records.

Unlike batch 01, this file uses an explicit candidate-ID allowlist after row-level
review of title, date and targeted acquired-text evidence. It deliberately leaves
merger/job/community records unresolved where ownership-transition relevance may
be substantive, and leaves extraction-stub cases unresolved rather than deciding
from title alone.
"""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECON = ROOT / "data" / "reconstruction"
LEDGER = RECON / "media_substantive_decision_ledger.csv"
SUMMARY = RECON / "media_substantive_decision_summary.json"

# Clear longitudinal Lonmin labour-relations / wage / strike cases under the
# locked scope, including the 2014 platinum strike where Lonmin is substantive.
INCLUDE_IDS = {
    "DISC-MEDIA-0366",  # AMCU/Lonmin strike-averting talks
    "DISC-MEDIA-0367",  # AMCU/Lonmin recognition talks/arbitration
    "DISC-MEDIA-0370",  # R12,500 wage demand during 2014 strike
    "DISC-MEDIA-0371",  # AMCU threatens strike at Lonmin
    "DISC-MEDIA-0373",  # AMCU strike notice incl. Lonmin
    "DISC-MEDIA-0409",  # Illegal strike at Lonmin
    "DISC-MEDIA-0418",  # Lonmin restart challenge to 2014 platinum strike
    "DISC-MEDIA-0420",  # Lonmin/AMCU union-recognition dispute
    "DISC-MEDIA-0440",  # Lonmin work stoppage across shafts
    "DISC-MEDIA-0495",  # AMCU arbitration at Lonmin
    "DISC-MEDIA-0512",  # Living conditions + workers/community context
    "DISC-MEDIA-0515",  # 2014 AMCU strike impact at Lonmin
    "DISC-MEDIA-0518",  # Lonmin/AMCU Labour Court dispute during 2014 strike
    "DISC-MEDIA-0530",  # AMCU union negotiations referred to CCMA
    "DISC-MEDIA-0540",  # Lonmin strike + police/death/unrest context
    "DISC-MEDIA-0591",  # NUM/AMCU majority dynamics at Lonmin
    "DISC-MEDIA-0687",  # Wildcat strike at Lonmin
}

# Clear non-case corporate/financial/transaction records after evidence review.
EXCLUDE_CORPORATE_IDS = {
    "DISC-MEDIA-0261",  # investors/Sibanye deal mechanics
    "DISC-MEDIA-0377",  # bank recommendation on Sibanye offer
    "DISC-MEDIA-0379",  # deal economics/rand
    "DISC-MEDIA-0380",  # chair appointment
    "DISC-MEDIA-0430",  # chair succession
    "DISC-MEDIA-0439",  # Pandora JV buyout
    "DISC-MEDIA-0461",  # investors/Sibanye deal mechanics
    "DISC-MEDIA-0479",  # generic company profile
    "DISC-MEDIA-0529",  # liquidity/corporate challenges
    "DISC-MEDIA-0534",  # CFO exit
    "DISC-MEDIA-0535",  # CFO exit republication
    "DISC-MEDIA-0537",  # quarterly results/liquidity
    "DISC-MEDIA-0547",  # executive dual role
    "DISC-MEDIA-0552",  # Lonmin Canada acquisition
    "DISC-MEDIA-0581",  # half-year loss/spending target
    "DISC-MEDIA-0586",  # COO appointment
    "DISC-MEDIA-0597",  # shareholder voting rights
    "DISC-MEDIA-0603",  # lender/loan agreements
    "DISC-MEDIA-0614",  # pure buyout regulatory approval mechanics
    "DISC-MEDIA-0632",  # contractor contract at Lonmin
    "DISC-MEDIA-0641",  # offer-price/deal mechanics
    "DISC-MEDIA-0642",  # rival-bid/offer mechanics
    "DISC-MEDIA-0643",  # merger longstop-date mechanics
    "DISC-MEDIA-0671",  # shareholder support for deal
    "DISC-MEDIA-0673",  # PGM/green-tech market outlook
    "DISC-MEDIA-0682",  # Northern Ireland exploration portfolio
    "DISC-MEDIA-0685",  # possible purchase of mining assets
}

# Later isolated operational fatalities/accidents at other shafts/projects are
# not the 2012 Marikana killings/justice case and are excluded under the scope.
EXCLUDE_OTHER_EVENT_IDS = {
    "DISC-MEDIA-0362",  # 2018 mine accident
    "DISC-MEDIA-0483",  # E1 shaft tramming fatality
    "DISC-MEDIA-0484",  # Hossy shaft fatality
    "DISC-MEDIA-0485",  # Pandora E3 fatality
    "DISC-MEDIA-0486",  # Rowland shaft fatality
    "DISC-MEDIA-0511",  # Saffy production fatality
    "DISC-MEDIA-0580",  # Pandora fall-of-ground accident
    "DISC-MEDIA-0622",  # K3 shaft fatality
}


def read_rows(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


rows = read_rows(LEDGER)
by_id = {r["candidate_id"]: r for r in rows}
requested = INCLUDE_IDS | EXCLUDE_CORPORATE_IDS | EXCLUDE_OTHER_EVENT_IDS
missing = sorted(requested - set(by_id))
if missing:
    raise RuntimeError(f"Batch 02 candidate IDs missing from ledger: {missing}")

for cid in sorted(INCLUDE_IDS):
    r = by_id[cid]
    if r.get("decision_status") == "pending_substantive_review":
        r["decision_status"] = "final_batch_02"
        r["final_decision"] = "include"
        r["reason_code"] = "include_case_central"
        r["decision_note"] = (
            "Included after explicit row-level review under the locked longitudinal scope: the record substantively concerns "
            "Lonmin labour relations, AMCU/NUM dynamics, wages, strike/work-stoppage activity, 2014 platinum-strike effects, "
            "or living/community conditions rather than routine corporate reporting."
        )
        r["decision_provenance"] = "review_batch_02_explicit_id_review_2026-08-23"

for cid in sorted(EXCLUDE_CORPORATE_IDS):
    r = by_id[cid]
    if r.get("decision_status") == "pending_substantive_review":
        r["decision_status"] = "final_batch_02"
        r["final_decision"] = "exclude"
        r["reason_code"] = "exclude_general_corporate_financial"
        r["decision_note"] = (
            "Excluded after explicit row-level review: the substantive focus is routine corporate finance, management, securities, "
            "transaction/deal mechanics, production/market outlook, contracting or non-South-African asset activity rather than the "
            "Marikana/Lonmin policy case."
        )
        r["decision_provenance"] = "review_batch_02_explicit_id_review_2026-08-23"

for cid in sorted(EXCLUDE_OTHER_EVENT_IDS):
    r = by_id[cid]
    if r.get("decision_status") == "pending_substantive_review":
        r["decision_status"] = "final_batch_02"
        r["final_decision"] = "exclude"
        r["reason_code"] = "exclude_other_mine_or_event"
        r["decision_note"] = (
            "Excluded after explicit row-level review: this is a later isolated operational mine/shaft accident or fatality, not the "
            "August 2012 Marikana killings, their justice/accountability process, or another declared longitudinal case theme."
        )
        r["decision_provenance"] = "review_batch_02_explicit_id_review_2026-08-23"

with LEDGER.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

status_counts = Counter(r["decision_status"] for r in rows)
reason_counts = Counter(r["reason_code"] for r in rows)
final_rows = [r for r in rows if r["decision_status"].startswith("final_")]
summary = {
    "ledger_scope": "154_lonmin_only_low_case_signal_records",
    "records_in_ledger": len(rows),
    "final_decisions_made": len(final_rows),
    "final_inclusions": sum(r["final_decision"] == "include" for r in final_rows),
    "final_exclusions": sum(r["final_decision"] == "exclude" for r in final_rows),
    "pending_substantive_review": sum(r["decision_status"] == "pending_substantive_review" for r in rows),
    "decision_status_counts": dict(status_counts),
    "reason_code_counts": dict(reason_counts),
    "batch_02_explicit_review_counts": {
        "include_case_central": len(INCLUDE_IDS),
        "exclude_general_corporate_financial": len(EXCLUDE_CORPORATE_IDS),
        "exclude_other_mine_or_event": len(EXCLUDE_OTHER_EVENT_IDS),
    },
    "important_note": (
        "Batch 02 uses explicit reviewed candidate-ID lists. Ambiguous ownership-transition, merger/job/community, and extraction-stub "
        "records remain pending. No stance label, historical class target or model result was used."
    )
}
SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
