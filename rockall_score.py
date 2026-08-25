#!/usr/bin/env python3
"""
Rockall Score for Upper Gastrointestinal Bleeding (UGIB)
Calculates pre-endoscopy (clinical) and post-endoscopy (total) Rockall scores
for mortality and rebleeding risk assessment.

Score range: 0-11 (clinical 0-7, endoscopic 0-4).

References:
  - Rockall TA, et al. Risk assessment after acute upper gastrointestinal
    haemorrhage. Gut 1996;38:316-21.
  - Rockall TA, et al. Gut 1996;38:322-7 (validation cohort).

Author: Dr. Abu Suraih Sakhri
License: MIT
"""

import argparse
import csv
import json
import sys
from typing import Dict, Any, Optional


# Mortality rates by total Rockall score (Rockall et al. 1996)
MORTALITY_RATES = {
    0: 0.2, 1: 0.4, 2: 2.2, 3: 3.3, 4: 5.3,
    5: 8.0, 6: 8.0, 7: 14.0, 8: 14.0, 9: 27.0,
    10: 27.0, 11: 27.0,
}

# Rebleeding rates by total Rockall score
REBLEEDING_RATES = {
    0: 2.0, 1: 3.0, 2: 5.0, 3: 8.0, 4: 12.0,
    5: 18.0, 6: 22.0, 7: 30.0, 8: 35.0, 9: 40.0,
    10: 45.0, 11: 50.0,
}


def calculate_rockall(
    age: Optional[int] = None,
    shock_hr: Optional[float] = None,
    shock_sbp: Optional[float] = None,
    comorbidity: str = "none",
    endoscopic_diagnosis: str = "none",
    major_stigmata: str = "none",
) -> Dict[str, Any]:
    """
    Calculate Rockall Score for upper GI bleeding.

    Parameters:
        age: Patient age in years
        shock_hr: Heart rate in bpm (for shock assessment)
        shock_sbp: Systolic blood pressure in mmHg (for shock assessment)
        comorbidity: 'none', 'cardiac' (CHF/IHD), or 'major' (renal/liver failure, malignancy)
        endoscopic_diagnosis: 'none'/'mallory-weiss', 'peptic_ulcer'/'esd', or 'cancer'
        major_stigmata: 'none'/'dark_spot', or 'blood'/'visible_vessel'/'active_bleeding'

    Returns:
        Dict with clinical_score, endoscopic_score, total_score, mortality/rebleeding risk.
    """
    clinical_score = 0
    clinical_components = {}

    # --- Age ---
    if age is not None:
        if age >= 80:
            clinical_components["age"] = 2
        elif age >= 60:
            clinical_components["age"] = 1
        else:
            clinical_components["age"] = 0
        clinical_score += clinical_components["age"]

    # --- Shock ---
    if shock_hr is not None or shock_sbp is not None:
        hr = shock_hr if shock_hr is not None else 0
        sbp = shock_sbp if shock_sbp is not None else 200
        if sbp < 100:
            clinical_components["shock"] = 2
        elif hr > 100:
            clinical_components["shock"] = 1
        else:
            clinical_components["shock"] = 0
        clinical_score += clinical_components["shock"]

    # --- Comorbidity ---
    comorb_lower = comorbidity.lower().strip()
    if comorb_lower in ("major", "renal", "liver", "malignancy", "renal_failure",
                         "liver_failure", "disseminated_malignancy",
                         "renal_liver_malignancy"):
        clinical_components["comorbidity"] = 3
    elif comorb_lower in ("cardiac", "chf", "ihd", "cardiac_failure",
                           "ischemic_heart_disease", "heart_failure"):
        clinical_components["comorbidity"] = 2
    else:
        clinical_components["comorbidity"] = 0
    clinical_score += clinical_components["comorbidity"]

    # --- Endoscopic components ---
    endo_score = 0
    endo_components = {}

    # Diagnosis
    diag_lower = endoscopic_diagnosis.lower().strip()
    if diag_lower in ("cancer", "malignant", "gastric_cancer", "esophageal_cancer"):
        endo_components["diagnosis"] = 2
    elif diag_lower in ("peptic_ulcer", "esd", "erosive_disease", "duodenal_ulcer",
                         "gastric_ulcer", "peptic", "ulcer"):
        endo_components["diagnosis"] = 1
    else:
        endo_components["diagnosis"] = 0
    endo_score += endo_components["diagnosis"]

    # Major stigmata of recent hemorrhage
    stig_lower = major_stigmata.lower().strip()
    if stig_lower in ("blood", "visible_vessel", "active_bleeding",
                       "active", "vessel", "blood_in_ugit", "adherent_clot"):
        endo_components["major_stigmata"] = 2
    else:
        endo_components["major_stigmata"] = 0
    endo_score += endo_components["major_stigmata"]

    total = clinical_score + endo_score

    # Mortality and rebleeding risk
    mortality_pct = MORTALITY_RATES.get(min(total, 11), 27.0)
    rebleeding_pct = REBLEEDING_RATES.get(min(total, 11), 50.0)

    # Risk category
    if total <= 2:
        risk = "Low"
        recommendation = "Low risk of rebleeding and mortality. Consider early discharge with outpatient follow-up."
    elif total <= 4:
        risk = "Moderate"
        recommendation = "Moderate risk. Inpatient monitoring recommended. Endoscopic therapy as indicated."
    elif total <= 6:
        risk = "High"
        recommendation = "High risk. ICU monitoring, aggressive resuscitation, endoscopic intervention required."
    else:
        risk = "Very High"
        recommendation = "Very high mortality risk. ICU care, consider interventional radiology or surgical consult."

    return {
        "tool": "rockall-score",
        "clinical_score": clinical_score,
        "clinical_components": clinical_components,
        "endoscopic_score": endo_score,
        "endoscopic_components": endo_components,
        "total_score": total,
        "max_possible_score": 11,
        "mortality_percent": mortality_pct,
        "rebleeding_percent": rebleeding_pct,
        "risk_category": risk,
        "recommendation": recommendation,
    }


def calculate_rockall_from_dict(params: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate Rockall score from a dictionary of parameters."""
    return calculate_rockall(
        age=_int_or_none(params.get("age")),
        shock_hr=_float_or_none(params.get("heart_rate") or params.get("hr") or params.get("shock_hr")),
        shock_sbp=_float_or_none(params.get("sbp") or params.get("shock_sbp")),
        comorbidity=str(params.get("comorbidity", "none")),
        endoscopic_diagnosis=str(params.get("diagnosis") or params.get("endoscopic_diagnosis", "none")),
        major_stigmata=str(params.get("stigmata") or params.get("major_stigmata", "none")),
    )


def process_batch(input_csv: str, output_csv: str) -> int:
    """Process a CSV file of patients and write Rockall scores."""
    with open(input_csv, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    out_fields = fieldnames + [
        "clinical_score", "endoscopic_score", "total_score",
        "mortality_percent", "rebleeding_percent", "risk_category", "recommendation",
    ]
    out_rows = []
    for r in rows:
        result = calculate_rockall_from_dict(r)
        row_dict = dict(r)
        row_dict["clinical_score"] = result["clinical_score"]
        row_dict["endoscopic_score"] = result["endoscopic_score"]
        row_dict["total_score"] = result["total_score"]
        row_dict["mortality_percent"] = result["mortality_percent"]
        row_dict["rebleeding_percent"] = result["rebleeding_percent"]
        row_dict["risk_category"] = result["risk_category"]
        row_dict["recommendation"] = result["recommendation"]
        out_rows.append(row_dict)

    with open(output_csv, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"Processed {len(out_rows)} records -> {output_csv}")
    return len(out_rows)


# =============================================================================
# CLI
# =============================================================================

def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="rockall-score",
        description="Rockall Score for Upper GI Bleeding - Mortality and rebleeding risk assessment",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Single calculation
    p_single = subparsers.add_parser("single", help="Calculate Rockall score for a single patient")
    p_single.add_argument("--age", type=int, help="Patient age in years")
    p_single.add_argument("--hr", type=float, help="Heart rate in bpm")
    p_single.add_argument("--sbp", type=float, help="Systolic blood pressure in mmHg")
    p_single.add_argument("--comorbidity", default="none",
                          choices=["none", "cardiac", "major"],
                          help="Comorbidity category")
    p_single.add_argument("--diagnosis", default="none",
                          choices=["none", "peptic_ulcer", "cancer"],
                          help="Endoscopic diagnosis")
    p_single.add_argument("--stigmata", default="none",
                          choices=["none", "dark_spot", "blood", "visible_vessel", "active_bleeding"],
                          help="Major stigmata of recent hemorrhage")

    # Batch processing
    p_batch = subparsers.add_parser("batch", help="Batch process CSV file")
    p_batch.add_argument("-i", "--input", required=True, help="Input CSV file")
    p_batch.add_argument("-o", "--output", default="results.csv", help="Output CSV file")

    args = parser.parse_args(argv)

    if args.command == "single":
        result = calculate_rockall(
            age=args.age, shock_hr=args.hr, shock_sbp=args.sbp,
            comorbidity=args.comorbidity,
            endoscopic_diagnosis=args.diagnosis,
            major_stigmata=args.stigmata,
        )
        print(json.dumps(result, indent=2))

    elif args.command == "batch":
        process_batch(args.input, args.output)

    return 0


# =============================================================================
# Helpers
# =============================================================================

def _float_or_none(val) -> Optional[float]:
    if val is None or val == "":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _int_or_none(val) -> Optional[int]:
    if val is None or val == "":
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


if __name__ == "__main__":
    main()
