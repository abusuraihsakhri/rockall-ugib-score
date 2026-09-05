# Rockall Ugib Score

> **Domain:** Clinical Decision Support & Biomedical Computing

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)

</div>

---

## Overview

Rockall Score for Upper Gastrointestinal Bleeding (UGIB). Calculates pre-endoscopy (clinical) and post-endoscopy (total) Rockall scores for mortality and rebleeding risk assessment.

Score range: 0-11 (clinical 0-7, endoscopic 0-4).

**References:**
- Rockall TA, et al. Risk assessment after acute upper gastrointestinal haemorrhage. Gut 1996;38:316-21.
- Rockall TA, et al. Gut 1996;38:322-7 (validation cohort).

**Author:** Dr. Abu Suraih Sakhri
**License:** MIT

---

## Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/rockall-ugib-score.git
cd rockall-ugib-score

# Install core dependencies
pip install -e .

# Or install with web API support
pip install -e ".[web]"

# Or install with all development dependencies
pip install -e ".[dev]"
```

---

## Usage

### Command Line Interface

**Single patient calculation:**
```bash
python cli.py single --age 70 --sbp 85 --comorbidity cardiac
```

**Batch processing from CSV:**
```bash
python cli.py batch -i patients.csv -o results.csv
```

**Audit system:**
```bash
python cli.py audit --task-id TASK-001
python cli.py chat "Explain the scoring system"
python cli.py verify-audit
```

### Python API

```python
from rockall_score import calculate_rockall, calculate_rockall_from_dict

# Direct calculation
result = calculate_rockall(
    age=70,
    shock_hr=110,
    shock_sbp=85,
    comorbidity="cardiac",
    endoscopic_diagnosis="peptic_ulcer",
    major_stigmata="blood"
)
print(result["total_score"])      # 7
print(result["risk_category"])    # "Very High"
print(result["mortality_percent"]) # 14.0

# From dictionary (e.g., from CSV/JSON)
result = calculate_rockall_from_dict({
    "age": "70",
    "sbp": "85",
    "comorbidity": "cardiac"
})
```

### Web API (Optional)

```bash
# Start the FastAPI server
uvicorn agents.api:app --reload

# Endpoints:
# GET  /health          - Health check
# GET  /metrics         - Prometheus metrics
# POST /api/audit       - Process task through audit system
# POST /api/chat        - Query supervisory chat
# GET  /api/audit/logs  - Retrieve audit trail
```

---

## Scoring System

### Clinical Score (Pre-endoscopy, 0-7)

| Component | Criteria | Points |
|-----------|----------|--------|
| Age | < 60 | 0 |
| | 60-79 | 1 |
| | >= 80 | 2 |
| Shock | HR < 100, SBP >= 100 | 0 |
| | HR > 100 | 1 |
| | SBP < 100 | 2 |
| Comorbidity | None | 0 |
| | Cardiac (CHF/IHD) | 2 |
| | Major (renal/liver failure, malignancy) | 3 |

### Endoscopic Score (0-4)

| Component | Criteria | Points |
|-----------|----------|--------|
| Diagnosis | None/Mallory-Weiss | 0 |
| | Peptic ulcer/ESD | 1 |
| | Cancer | 2 |
| Stigmata | None/Dark spot | 0 |
| | Blood/Visible vessel/Active bleeding | 2 |

### Risk Categories

| Total Score | Category | Recommendation |
|-------------|----------|----------------|
| 0-2 | Low | Consider early discharge |
| 3-4 | Moderate | Inpatient monitoring |
| 5-6 | High | ICU monitoring, endoscopic intervention |
| 7-11 | Very High | ICU care, consider surgery |

---

## Testing

```bash
# Run all tests
pytest -v

# Run with coverage
pytest -v --cov=.

# Run specific test file
pytest test_rockall_score.py -v
```

---

## Security Features

- **Zero-PHI Outbound Interceptor:** AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers
- **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs
- **Input Validation:** Range checking on clinical parameters, path traversal protection on file operations

Set `AUDIT_SECRET_KEY` environment variable for production deployments to ensure audit trail persistence across restarts.

---

## Docker Deployment

```bash
# Build and run with Docker Compose
AUDIT_SECRET_KEY=your-secret-key docker-compose up --build

# Or with Docker directly
docker build -t rockall-ugib-score .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secret-key rockall-ugib-score
```

---

## Project Structure

```
rockall-ugib-score/
├── rockall_score.py      # Core scoring logic + CLI
├── cli.py                # CLI entry point
├── enrichment.py         # Enrichment engines
├── simulator.py          # High-throughput simulation
├── agents/               # Enterprise agent framework
│   ├── base.py           # Security, PHI guard, audit trail
│   ├── models.py         # Pydantic data models
│   ├── supervisor.py     # Multi-agent orchestrator
│   ├── workers.py        # Specialized domain workers
│   ├── api.py            # FastAPI REST endpoints
│   └── ...
├── tests/                # Test suite
├── web/                  # Frontend dashboard
├── pyproject.toml        # Project metadata & dependencies
└── Dockerfile            # Container configuration
```
