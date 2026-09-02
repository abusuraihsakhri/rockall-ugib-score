# Rockall Ugib Score

> **Domain:** Clinical Decision Support & Biomedical Computing  
> **Reference Guidelines & Standards:** `Standard Clinical Formulations & ISO/IEC Quality Frameworks`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

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

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`calculate_rockall()`**: Calculate Rockall Score for upper GI bleeding.

Parameters:
    age: Patient age in years
    shock_hr: Heart rate in bpm (for shock assessment)
    shock_sbp: Systolic blood pressure in mmHg (for shock assessment)
    comorbidity: 'none', 'cardiac' (CHF/IHD), or 'major' (renal/liver failure, malignancy)
    endoscopic_diagnosis: 'none'/'mallory-weiss', 'peptic_ulcer'/'esd', or 'cancer'
    major_stigmata: 'none'/'dark_spot', or 'blood'/'visible_vessel'/'active_bleeding'

Returns:
    Dict with clinical_score, endoscopic_score, total_score, mortality/rebleeding risk.
- **`calculate_rockall_from_dict()`**: Calculate Rockall score from a dictionary of parameters.
- **`process_batch()`**: Process a CSV file of patients and write Rockall scores.
- **`main()`** — calculates and validates main parameters.

---

## 📐 Mathematical Formulation & Logic

```text
  Calculates pre-endoscopy (clinical) and post-endoscopy (total) Rockall scores
  Calculate Rockall Score for upper GI bleeding.
  clinical_score = 0
  endo_score = 0
  risk = "Low"
```

---

## 💻 CLI Quickstart & Usage

### 1. Guided Interactive Mode
```bash
python cli.py
```

### 2. Direct Parameterized Evaluation
```bash
python cli.py --input data.csv
```

### Parameter Reference
- `--interactive`: Launch guided terminal interactive wizard.
- `--input <path>`: Evaluate input from JSON or CSV specification.
- `--json`: Output deterministic structured results in JSON format.

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `Patient_ID` | Parameter / observation metric | Required |
| `v1` | Parameter / observation metric | Required |
| `v2` | Parameter / observation metric | Required |
| `v3` | Parameter / observation metric | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t rockall-ugib-score .
docker run -p 8000:8000 rockall-ugib-score
```
