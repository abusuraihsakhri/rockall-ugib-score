"""HTTP-facing score helpers and safe optional utility defaults."""
import pytest
from fastapi import HTTPException

from agents.api import ScoreRequest, api_score, api_audit_logs, frontend


def test_score_endpoint_returns_incomplete_preendoscopy():
    value = api_score(ScoreRequest(age=65, shock_hr=90, shock_sbp=130, comorbidity="none"))
    assert value["clinical_score"] == 1
    assert value["clinical_complete"]
    assert not value["score_complete"]
    assert value["total_score"] is None


def test_score_endpoint_reports_complete_findings():
    value = api_score(ScoreRequest(
        age=85, shock_hr=120, shock_sbp=80, comorbidity="major",
        endoscopic_diagnosis="cancer", major_stigmata="blood",
    ))
    assert value["total_score"] == 11
    assert value["mortality_percent"] == 41.1


def test_score_endpoint_responds_with_validation_error():
    with pytest.raises(HTTPException) as exc:
        api_score(ScoreRequest(age=75, shock_hr=80, shock_sbp=125, comorbidity="unknown"))
    assert exc.value.status_code == 422


def test_sensitive_logs_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ENABLE_AUDIT_LOGS", raising=False)
    with pytest.raises(HTTPException) as exc:
        api_audit_logs()
    assert exc.value.status_code == 403


def test_frontend_points_to_bundled_html():
    response = frontend()
    assert response.path.endswith("index.html")
