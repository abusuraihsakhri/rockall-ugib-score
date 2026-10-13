#!/usr/bin/env python3
"""
Tests for Rockall Score for Upper GI Bleeding.
"""
import json
import sys
import os
import csv
import pytest

sys.path.insert(0, os.path.dirname(__file__))

from rockall_score import (
    calculate_rockall,
    calculate_rockall_from_dict,
    process_batch,
    main,
    MORTALITY_RATES,
    REBLEEDING_RATES,
)


# =============================================================================
# Age Scoring Tests
# =============================================================================

class TestAgeScoring:
    def test_age_below_60(self):
        result = calculate_rockall(age=45)
        assert result["clinical_components"]["age"] == 0

    def test_age_60(self):
        result = calculate_rockall(age=60)
        assert result["clinical_components"]["age"] == 1

    def test_age_79(self):
        result = calculate_rockall(age=79)
        assert result["clinical_components"]["age"] == 1

    def test_age_80(self):
        result = calculate_rockall(age=80)
        assert result["clinical_components"]["age"] == 2

    def test_age_90(self):
        result = calculate_rockall(age=90)
        assert result["clinical_components"]["age"] == 2


# =============================================================================
# Shock Scoring Tests
# =============================================================================

class TestShockScoring:
    def test_no_shock(self):
        result = calculate_rockall(shock_hr=72, shock_sbp=130)
        assert result["clinical_components"]["shock"] == 0

    def test_tachycardia_only(self):
        result = calculate_rockall(shock_hr=110, shock_sbp=120)
        assert result["clinical_components"]["shock"] == 1

    def test_hypotension(self):
        result = calculate_rockall(shock_hr=120, shock_sbp=90)
        assert result["clinical_components"]["shock"] == 2

    def test_hypotension_overrides_tachycardia(self):
        """SBP < 100 scores 2 even if HR <= 100."""
        result = calculate_rockall(shock_hr=80, shock_sbp=85)
        assert result["clinical_components"]["shock"] == 2


# =============================================================================
# Comorbidity Scoring Tests
# =============================================================================

class TestComorbidityScoring:
    def test_no_comorbidity(self):
        result = calculate_rockall(comorbidity="none")
        assert result["clinical_components"]["comorbidity"] == 0

    def test_cardiac_comorbidity(self):
        result = calculate_rockall(comorbidity="cardiac")
        assert result["clinical_components"]["comorbidity"] == 2

    def test_cardiac_chf(self):
        result = calculate_rockall(comorbidity="chf")
        assert result["clinical_components"]["comorbidity"] == 2

    def test_major_comorbidity(self):
        result = calculate_rockall(comorbidity="major")
        assert result["clinical_components"]["comorbidity"] == 3

    def test_liver_failure(self):
        result = calculate_rockall(comorbidity="liver_failure")
        assert result["clinical_components"]["comorbidity"] == 3

    def test_renal_failure(self):
        result = calculate_rockall(comorbidity="renal_failure")
        assert result["clinical_components"]["comorbidity"] == 3


# =============================================================================
# Endoscopic Diagnosis Tests
# =============================================================================

class TestEndoscopicDiagnosis:
    def test_no_diagnosis(self):
        result = calculate_rockall(endoscopic_diagnosis="none")
        assert result["endoscopic_components"]["diagnosis"] == 0

    def test_peptic_ulcer(self):
        result = calculate_rockall(endoscopic_diagnosis="peptic_ulcer")
        assert result["endoscopic_components"]["diagnosis"] == 1

    def test_cancer(self):
        result = calculate_rockall(endoscopic_diagnosis="cancer")
        assert result["endoscopic_components"]["diagnosis"] == 2


# =============================================================================
# Major Stigmata Tests
# =============================================================================

class TestMajorStigmata:
    def test_no_stigmata(self):
        result = calculate_rockall(major_stigmata="none")
        assert result["endoscopic_components"]["major_stigmata"] == 0

    def test_dark_spot(self):
        result = calculate_rockall(major_stigmata="dark_spot")
        assert result["endoscopic_components"]["major_stigmata"] == 0

    def test_active_bleeding(self):
        result = calculate_rockall(major_stigmata="active_bleeding")
        assert result["endoscopic_components"]["major_stigmata"] == 2

    def test_visible_vessel(self):
        result = calculate_rockall(major_stigmata="visible_vessel")
        assert result["endoscopic_components"]["major_stigmata"] == 2

    def test_blood_in_ugit(self):
        result = calculate_rockall(major_stigmata="blood")
        assert result["endoscopic_components"]["major_stigmata"] == 2


# =============================================================================
# Mortality Risk Tests
# =============================================================================

class TestMortalityRisk:
    def test_clinical_mortality_is_separate_from_complete(self):
        result = calculate_rockall(age=65, shock_hr=70, shock_sbp=130)
        assert result["clinical_score"] == 1
        assert result["clinical_mortality_percent"] == 2.4
        assert result["mortality_percent"] is None
        assert result["total_score"] is None

    def test_clinical_mortality_score_four(self):
        result = calculate_rockall(age=85, shock_sbp=85)
        assert result["clinical_score"] == 4
        assert result["clinical_mortality_percent"] == 24.6

    def test_complete_mortality_and_rebleeding(self):
        result = calculate_rockall(
            age=40, shock_hr=70, shock_sbp=120, comorbidity="none",
            endoscopic_diagnosis="none", major_stigmata="none",
        )
        assert result["total_score"] == 0
        assert result["mortality_percent"] == 0.0
        assert result["rebleeding_percent"] == 4.9

    def test_scores_eight_to_eleven_use_grouped_cohort(self):
        result = calculate_rockall(
            age=85, shock_sbp=80, comorbidity="major",
            endoscopic_diagnosis="cancer", major_stigmata="active_bleeding",
        )
        assert result["total_score"] == 11
        assert result["mortality_percent"] == 41.1
        assert result["rebleeding_percent"] == 41.8


# =============================================================================
# Risk Category Tests
# =============================================================================

class TestRiskCategory:
    def test_no_full_risk_label_without_endoscopy(self):
        result = calculate_rockall(age=40, shock_sbp=130, shock_hr=70)
        assert result["risk_category"] is None

    def test_higher_complete_score_is_labelled(self):
        result = calculate_rockall(
            age=85, shock_sbp=80, comorbidity="major",
            endoscopic_diagnosis="cancer", major_stigmata="active_bleeding",
        )
        assert result["risk_category"] == "Higher score"


# =============================================================================
# Max Score Test
# =============================================================================

class TestMaxScore:
    def test_max_score_11(self):
        result = calculate_rockall(
            age=85, shock_hr=120, shock_sbp=80,
            comorbidity="major",
            endoscopic_diagnosis="cancer",
            major_stigmata="active_bleeding",
        )
        assert result["total_score"] == 11
        assert result["clinical_score"] == 7
        assert result["endoscopic_score"] == 4


# =============================================================================
# Batch Processing Tests
# =============================================================================

class TestBatch:
    def test_batch_processing(self, tmp_path):
        csv_in = tmp_path / "in.csv"
        csv_out = tmp_path / "out.csv"
        csv_in.write_text(
            "patient_id,age,hr,sbp,comorbidity,diagnosis,stigmata\n"
            "P001,40,72,130,none,none,none\n"
            "P002,85,120,80,major,cancer,active_bleeding\n",
            encoding="utf-8",
        )
        count = process_batch(str(csv_in), str(csv_out))
        assert count == 2
        assert csv_out.exists()
        content = csv_out.read_text(encoding="utf-8")
        assert "total_score" in content
        assert "mortality_percent" in content


# =============================================================================
# CLI Tests
# =============================================================================

class TestCLI:
    def test_cli_single(self):
        ret = main(["single", "--age", "70", "--sbp", "85",
                     "--comorbidity", "cardiac"])
        assert ret == 0

    def test_cli_single_minimal(self):
        ret = main(["single"])
        assert ret == 0

    def test_cli_batch(self, tmp_path):
        csv_in = tmp_path / "in.csv"
        csv_out = tmp_path / "out.csv"
        csv_in.write_text("age,sbp\n70,85\n", encoding="utf-8")
        ret = main(["batch", "-i", str(csv_in), "-o", str(csv_out)])
        assert ret == 0
        assert csv_out.exists()


# =============================================================================
# From Dict Tests
# =============================================================================

class TestFromDict:
    def test_from_dict_basic(self):
        params = {"age": "70", "sbp": "85", "comorbidity": "cardiac"}
        result = calculate_rockall_from_dict(params)
        assert result["partial_score"] > 0
        assert result["total_score"] is None

    def test_from_dict_empty(self):
        result = calculate_rockall_from_dict({})
        assert result["partial_score"] == 0
        assert result["total_score"] is None


# =============================================================================
# Input Validation Tests
# =============================================================================

class TestInputValidation:
    def test_negative_age_raises(self):
        with pytest.raises(ValueError, match="Age must be between"):
            calculate_rockall(age=-5)

    def test_unrealistic_age_raises(self):
        with pytest.raises(ValueError, match="Age must be between"):
            calculate_rockall(age=200)

    def test_negative_hr_raises(self):
        with pytest.raises(ValueError, match="Heart rate must be greater than"):
            calculate_rockall(shock_hr=-10)

    def test_unrealistic_hr_raises(self):
        with pytest.raises(ValueError, match="Heart rate must be greater than"):
            calculate_rockall(shock_hr=400)

    def test_negative_sbp_raises(self):
        with pytest.raises(ValueError, match="Systolic BP must be greater than"):
            calculate_rockall(shock_sbp=-50)

    def test_unrealistic_sbp_raises(self):
        with pytest.raises(ValueError, match="Systolic BP must be greater than"):
            calculate_rockall(shock_sbp=350)

    def test_valid_boundary_values(self):
        # Minimal valid values (no shock since sbp >= 100)
        result = calculate_rockall(age=0, shock_hr=1, shock_sbp=100)
        assert result["partial_score"] == 0

        # Maximum valid values
        result = calculate_rockall(age=150, shock_hr=300, shock_sbp=300)
        assert result["partial_score"] > 0


# =============================================================================
# Path Traversal Protection Tests
# =============================================================================

class TestPathTraversalProtection:
    def test_path_traversal_blocked_input(self, tmp_path):
        with pytest.raises(ValueError, match="path traversal"):
            process_batch("../etc/passwd", "output.csv")

    def test_path_traversal_blocked_output(self, tmp_path):
        csv_in = tmp_path / "in.csv"
        csv_in.write_text("age,sbp\n70,85\n", encoding="utf-8")
        with pytest.raises(ValueError, match="path traversal"):
            process_batch(str(csv_in), "../etc/output.csv")

    def test_missing_input_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            process_batch(str(tmp_path / "nonexistent.csv"), str(tmp_path / "out.csv"))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
