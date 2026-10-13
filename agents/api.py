"""
FastAPI REST API Server for Rockall Ugib Score.
"""
import os
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from pydantic import BaseModel
from .base import AuditLogger, PHIGuard, SecurityException
from rockall_score import calculate_rockall
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Rockall Ugib Score API",
    description="Local Rockall scoring endpoint with optional legacy audit utilities",
    version="1.1.0",
)




class ScoreRequest(BaseModel):
    age: Optional[int] = None
    shock_hr: Optional[float] = None
    shock_sbp: Optional[float] = None
    comorbidity: str = "none"
    endoscopic_diagnosis: Optional[str] = None
    major_stigmata: Optional[str] = None


@app.get("/", include_in_schema=False)
def frontend():
    return FileResponse(Path(__file__).resolve().parent.parent / "index.html")


@app.post("/api/score")
def api_score(payload: ScoreRequest):
    try:
        return calculate_rockall(**payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "rockall-ugib-score", "domain": "Clinical & Biomedical AI", "standard": "CAP / CLSI / ISO Standards", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    try:
        dossier = supervisor.process_task(payload)
        return dossier.to_dict()
    except SecurityException as exc:
        raise HTTPException(status_code=422, detail="Sensitive identifier rejected") from exc


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs():
    if os.getenv("ENABLE_AUDIT_LOGS") != "1":
        raise HTTPException(status_code=403, detail="Audit logs are disabled by default")
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
