"""Regression tests for clinical completeness, validation, and audit integrity."""
import csv
import math
from pathlib import Path

import pytest

from rockall_score import calculate_rockall, calculate_rockall_from_dict, process_batch
from agents.base import AuditTrail


def test_tachycardia_threshold_is_inclusive():
    result = calculate_rockall(age=50, shock_hr=100, shock_sbp=100)
    assert result["clinical_components"]["shock"] == 1


def test_hypotension_is_independent_of_missing_pulse():
    result = calculate_rockall(age=50, shock_sbp=90)
    assert result["clinical_complete"] is True
    assert result["clinical_components"]["shock"] == 2
    assert result["clinical_mortality_percent"] == 5.6


def test_pulse_without_bp_cannot_identify_shock_severity():
    result = calculate_rockall(age=65, shock_hr=110)
    assert "shock" not in result["clinical_components"]
    assert not result["clinical_complete"]
    assert result["clinical_mortality_percent"] is None


def test_high_bp_without_pulse_is_not_assumed_normal():
    result = calculate_rockall(age=50, shock_sbp=120)
    assert "shock" not in result["clinical_components"]
    assert result["total_score"] is None


def test_explicit_endoscopy_required_for_full_score():
    result = calculate_rockall(age=50, shock_hr=75, shock_sbp=130)
    assert result["clinical_complete"]
    assert not result["endoscopic_complete"]
    assert result["total_score"] is None
    assert result["mortality_percent"] is None


def test_other_major_comorbidity_is_two_points():
    result = calculate_rockall(comorbidity="other_major")
    assert result["clinical_components"]["comorbidity"] == 2


def test_no_lesion_with_bleeding_stigmata_is_invalid():
    with pytest.raises(ValueError, match="inconsistent"):
        calculate_rockall(endoscopic_diagnosis="none", major_stigmata="blood")


@pytest.mark.parametrize("kwargs", [
    {"shock_hr": math.nan},
    {"shock_hr": math.inf},
    {"shock_sbp": float("-inf")},
    {"shock_sbp": 0},
    {"shock_hr": 0},
    {"age": True},
    {"age": 59.8},
    {"comorbidity": "mystery"},
    {"endoscopic_diagnosis": "unreported lesion"},
    {"major_stigmata": "unsure"},
])
def test_invalid_values_fail_closed(kwargs):
    with pytest.raises(ValueError):
        calculate_rockall(**kwargs)


def test_invalid_csv_numeric_field_is_not_silently_zero():
    with pytest.raises(ValueError, match="Invalid numeric"):
        calculate_rockall_from_dict({"age": "seventy"})


def test_fractional_age_from_dict_rejected():
    with pytest.raises(ValueError, match="whole"):
        calculate_rockall_from_dict({"age": "60.5"})


def test_batch_uses_absolute_paths_and_reports_invalid_row(tmp_path):
    source = tmp_path / "data.csv"
    target = tmp_path / "results.csv"
    source.write_text("age,hr,sbp,diagnosis,stigmata\n64,90,120,other,none\n", encoding="utf-8")
    assert process_batch(str(source), str(target)) == 1
    with target.open(newline="", encoding="utf-8") as handle:
        row = next(csv.DictReader(handle))
    assert row["clinical_score"] == "1"
    assert row["total_score"] == "2"
    assert row["mortality_percent"] == "0.2"

    source.write_text("age,hr,sbp\n60.5,90,120\n", encoding="utf-8")
    with pytest.raises(ValueError, match="CSV line 2"):
        process_batch(str(source), str(target))


def test_batch_cannot_overwrite_input(tmp_path):
    source = tmp_path / "data.csv"
    source.write_text("age\n70\n", encoding="utf-8")
    with pytest.raises(ValueError, match="must differ"):
        process_batch(str(source), str(source))


def test_hmac_verifier_detects_data_or_signature_mutation():
    audit = AuditTrail(secret_key="test-secret-not-for-production")
    audit.log("tester", "operator", "TEST", {"ok": True})
    assert audit.verify_integrity()
    detached = audit.get_trail()
    detached[0]["actor"] = "not-original"
    assert audit.verify_integrity()
    audit.logs[0]["actor"] = "not-original"
    assert not audit.verify_integrity()


def test_hmac_verifier_detects_signature_mutation():
    audit = AuditTrail(secret_key="test-secret-not-for-production")
    audit.log("tester", "operator", "TEST", {"ok": True})
    audit.logs[0]["current_hash"] = "0" * 64
    assert not audit.verify_integrity()
