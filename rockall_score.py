#!/usr/bin/env python3
"""Rockall score for upper gastrointestinal bleeding.

Pre-endoscopy score 0-7; complete score 0-11. Historical outcome frequencies
are observations from the original Rockall cohort, not individualized risks.
See README.md for source and clinical limitations.
"""
import argparse
import csv
import json
import math
import os
from pathlib import Path
from typing import Any, Dict, Optional

# Original-cohort OBSERVED frequencies by complete Rockall score, in percent.
# All complete scores 8-11 share the reported >=8 cohort (not extrapolations).
MORTALITY_RATES = {0: 0.0, 1: 0.0, 2: 0.2, 3: 2.9, 4: 5.3, 5: 10.8,
                   6: 17.3, 7: 27.0, 8: 41.1, 9: 41.1, 10: 41.1, 11: 41.1}
REBLEEDING_RATES = {0: 4.9, 1: 3.4, 2: 5.3, 3: 11.2, 4: 14.1, 5: 24.1,
                    6: 32.9, 7: 43.8, 8: 41.8, 9: 41.8, 10: 41.8, 11: 41.8}
CLINICAL_MORTALITY_RATES = {0: 0.2, 1: 2.4, 2: 5.6, 3: 11.0, 4: 24.6,
                            5: 39.6, 6: 48.9, 7: 50.0}

COMORBIDITIES = {
    "none": 0,
    "cardiac": 2, "chf": 2, "ihd": 2, "cardiac_failure": 2,
    "ischemic_heart_disease": 2, "heart_failure": 2,
    "other_major": 2, "other_major_comorbidity": 2,
    "major": 3, "renal": 3, "liver": 3, "renal_failure": 3,
    "liver_failure": 3, "disseminated_malignancy": 3,
    "renal_liver_malignancy": 3,
}
DIAGNOSES = {
    "none": 0, "mallory-weiss": 0, "mallory_weiss": 0,
    "other": 1, "peptic_ulcer": 1, "esd": 1, "erosive_disease": 1,
    "duodenal_ulcer": 1, "gastric_ulcer": 1, "peptic": 1, "ulcer": 1,
    "cancer": 2, "malignant": 2, "gastric_cancer": 2,
    "esophageal_cancer": 2,
}
STIGMATA = {
    "none": 0, "dark_spot": 0,
    "blood": 2, "visible_vessel": 2, "active_bleeding": 2,
    "active": 2, "vessel": 2, "blood_in_ugit": 2, "adherent_clot": 2,
}


def _category(value: str, mapping: dict, label: str) -> int:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be text")
    key = value.strip().lower()
    if key not in mapping:
        raise ValueError(f"Unknown {label}: {value!r}; expected one of {', '.join(sorted(mapping))}")
    return mapping[key]


def _number(value: Optional[float], name: str, maximum: float) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number")
    number = float(value)
    if not math.isfinite(number) or number <= 0 or number > maximum:
        raise ValueError(f"{name} must be greater than 0 and at most {maximum}, got {value}")
    return number


def calculate_rockall(
    age: Optional[int] = None,
    shock_hr: Optional[float] = None,
    shock_sbp: Optional[float] = None,
    comorbidity: str = "none",
    endoscopic_diagnosis: Optional[str] = None,
    major_stigmata: Optional[str] = None,
) -> Dict[str, Any]:
    """Calculate available score components without inventing missing data.

    A complete Rockall score is returned only when all five components are
    known. Clinical score is numeric but marked incomplete unless age, shock
    and comorbidity are known. SBP <100 establishes the shock component
    independently of HR; otherwise BOTH BP and pulse are needed.
    """
    if age is not None and (isinstance(age, bool) or not isinstance(age, int)
                            or age < 0 or age > 150):
        raise ValueError(f"Age must be between 0 and 150 whole years, got {age}")
    hr = _number(shock_hr, "Heart rate", 300)
    sbp = _number(shock_sbp, "Systolic BP", 300)
    clinical = {}
    if age is not None:
        clinical["age"] = 2 if age >= 80 else (1 if age >= 60 else 0)
    if sbp is not None and sbp < 100:
        clinical["shock"] = 2
    elif sbp is not None and hr is not None:
        clinical["shock"] = 1 if hr >= 100 else 0
    clinical["comorbidity"] = _category(comorbidity, COMORBIDITIES, "comorbidity")
    clinical_score = sum(clinical.values())
    clinical_complete = "age" in clinical and "shock" in clinical

    endoscopic = {}
    if endoscopic_diagnosis is not None:
        endoscopic["diagnosis"] = _category(endoscopic_diagnosis, DIAGNOSES, "diagnosis")
    if major_stigmata is not None:
        endoscopic["major_stigmata"] = _category(major_stigmata, STIGMATA, "stigmata")
    endoscopic_complete = len(endoscopic) == 2
    if endoscopic_complete and endoscopic_diagnosis.strip().lower() == "none" and endoscopic["major_stigmata"]:
        raise ValueError("No lesion with major bleeding stigmata is inconsistent; choose 'other' diagnosis")

    endoscopic_score = sum(endoscopic.values())
    score_complete = clinical_complete and endoscopic_complete
    total = clinical_score + endoscopic_score if score_complete else None

    # A clinical subtotal and a full Rockall score are DIFFERENT scales.
    return {
        "tool": "rockall-score",
        "clinical_score": clinical_score,
        "clinical_complete": clinical_complete,
        "clinical_components": clinical,
        "endoscopic_score": endoscopic_score,
        "endoscopic_complete": endoscopic_complete,
        "endoscopic_components": endoscopic,
        "partial_score": clinical_score + endoscopic_score,
        "total_score": total,
        "score_complete": score_complete,
        "max_possible_score": 11,
        "clinical_mortality_percent": (
            CLINICAL_MORTALITY_RATES[clinical_score] if clinical_complete else None
        ),
        "mortality_percent": MORTALITY_RATES[total] if score_complete else None,
        "rebleeding_percent": REBLEEDING_RATES[total] if score_complete else None,
        "risk_category": "Historical low-score group" if score_complete and total <= 2 else (
            "Higher score" if score_complete else None
        ),
        "recommendation": (
            "Historical cohort frequencies are not individualized predictions. "
            "Do not use Rockall alone to decide admission, discharge or treatment; "
            "use clinical assessment and current UGIB guidelines."
        ),
    }


def _pick(params: Dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in params and params[key] is not None and str(params[key]).strip() != "":
            return params[key]
    return None


def _float_or_none(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        value = float(value)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError(f"Invalid numeric value: {value!r}") from exc
    if not math.isfinite(value):
        raise ValueError("Numeric inputs must be finite")
    return value


def _int_or_none(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    parsed = _float_or_none(value)
    if not parsed.is_integer():
        raise ValueError(f"Age must be a whole number: {value!r}")
    return int(parsed)


def calculate_rockall_from_dict(params: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate using CLI/CSV key aliases; invalid values are never silently ignored."""
    return calculate_rockall(
        age=_int_or_none(_pick(params, "age")),
        shock_hr=_float_or_none(_pick(params, "heart_rate", "hr", "shock_hr")),
        shock_sbp=_float_or_none(_pick(params, "sbp", "shock_sbp")),
        comorbidity=_pick(params, "comorbidity") or "none",
        endoscopic_diagnosis=_pick(params, "diagnosis", "endoscopic_diagnosis"),
        major_stigmata=_pick(params, "stigmata", "major_stigmata"),
    )


def _validate_file_path(filepath: str, must_exist: bool = False) -> str:
    """Accept ordinary absolute CLI paths; reject relative parent traversal."""
    path = Path(filepath).expanduser()
    if not path.is_absolute() and ".." in path.parts:
        raise ValueError(f"Invalid file path (path traversal): {filepath}")
    if must_exist and not path.is_file():
        raise FileNotFoundError(f"Input file not found: {filepath}")
    return str(path)


def process_batch(input_csv: str, output_csv: str) -> int:
    """Read UTF-8 CSV and write scored CSV; fail before writing on invalid rows."""
    input_csv = _validate_file_path(input_csv, must_exist=True)
    output_csv = _validate_file_path(output_csv)
    if os.path.realpath(input_csv) == os.path.realpath(output_csv):
        raise ValueError("Input and output paths must differ")
    with open(input_csv, mode="r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        if not fieldnames:
            raise ValueError("Input CSV must have a header row")
        rows = list(reader)

    out_fields = list(dict.fromkeys(fieldnames + [
        "clinical_score", "clinical_complete", "endoscopic_score",
        "endoscopic_complete", "total_score", "score_complete",
        "clinical_mortality_percent", "mortality_percent",
        "rebleeding_percent", "risk_category", "recommendation",
    ]))
    out_rows = []
    for line, row in enumerate(rows, start=2):
        try:
            score = calculate_rockall_from_dict(row)
        except ValueError as exc:
            raise ValueError(f"CSV line {line}: {exc}") from exc
        out_rows.append({**row, **{k: score[k] for k in out_fields if k in score}})
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
                          choices=["none", "cardiac", "other_major", "major", "renal_failure", "liver_failure", "disseminated_malignancy"],
                          help="Comorbidity category")
    p_single.add_argument("--diagnosis", default=None,
                          choices=["none", "mallory_weiss", "other", "peptic_ulcer", "cancer"],
                          help="Endoscopic diagnosis")
    p_single.add_argument("--stigmata", default=None,
                          choices=["none", "dark_spot", "blood", "visible_vessel", "active_bleeding"],
                          help="Major stigmata of recent hemorrhage")

    # Batch processing
    p_batch = subparsers.add_parser("batch", help="Batch process CSV file")
    p_batch.add_argument("-i", "--input", required=True, help="Input CSV file")
    p_batch.add_argument("-o", "--output", default="results.csv", help="Output CSV file")

    # Audit trail verification
    p_audit = subparsers.add_parser("audit", help="Process a task through the audit system")
    p_audit.add_argument("--task-id", required=True, help="Task identifier for audit processing")

    # Chat/Query interface
    p_chat = subparsers.add_parser("chat", help="Query the supervisory chat system")
    p_chat.add_argument("query", nargs="+", help="Query string for the chat system")

    # Verify audit integrity
    p_verify = subparsers.add_parser("verify-audit", help="Verify HMAC audit trail integrity")

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

    elif args.command == "audit":
        from agents.supervisor import SystemSupervisor
        from agents.models import SystemTaskPayload
        supervisor = SystemSupervisor(model_provider="mock")
        payload = SystemTaskPayload(
            task_id=args.task_id,
            target_identifier="CLI-AUDIT",
            primary_metric=0.0,
        )
        dossier = supervisor.process_task(payload)
        print(json.dumps(dossier.to_dict(), indent=2, default=str))

    elif args.command == "chat":
        from agents.supervisor import SystemSupervisor
        supervisor = SystemSupervisor(model_provider="mock")
        query = " ".join(args.query)
        response = supervisor.query_supervisory_chat(query)
        print(json.dumps({"query": query, "response": response}, indent=2))

    elif args.command == "verify-audit":
        from agents.base import AuditLogger
        is_valid = AuditLogger.verify_integrity()
        trail_len = len(AuditLogger.get_trail())
        print(json.dumps({"integrity_valid": is_valid, "trail_length": trail_len}, indent=2))

    return 0



if __name__ == "__main__":
    main()
