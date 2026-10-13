# Rockall UGIB Score

Standalone Rockall risk-score calculator for upper gastrointestinal bleeding, with separate clinical/pre-endoscopy (0–7) and complete/post-endoscopy (0–11) calculations. The browser app works offline, with no Python runtime or backend required. An optional Python CLI and FastAPI service are also included.

## Browser application

Open [index.html](index.html) locally in a modern browser, or use the GitHub Pages deployment once its production build is confirmed. Identical static application entries are maintained at [docs/index.html](docs/index.html) and [web/index.html](web/index.html) for static hosting.

Enter age, heart rate, systolic blood pressure and the most severe comorbidity. Enable endoscopic findings only after endoscopy, then enter diagnosis and stigmata. The result provides point contributions, available scores, and observed historical cohort frequencies.

The page performs calculations locally, without transmitting or storing inputs. Do not enter names or patient identifiers.

## Rockall scoring

| Component | 0 points | 1 point | 2 points | 3 points |
| --- | --- | --- | --- | --- |
| Age | <60 | 60–79 | ≥80 | — |
| Shock | SBP ≥100 and HR <100 | SBP ≥100 and HR ≥100 | SBP <100 | — |
| Comorbidity | None | — | Cardiac failure, IHD, other major comorbidity | Renal failure, liver failure, disseminated malignancy |
| Endoscopic diagnosis | Mallory–Weiss tear or no lesion/no stigmata | Other diagnoses | Upper GI malignancy | — |
| Recent bleeding stigmata | None / dark spot | — | Blood, adherent clot, visible or spurting vessel | — |

HR is in beats/min and SBP in mmHg. The clinical subtotal combines age, shock and comorbidity (max 7). The complete score adds endoscopic diagnosis and bleeding stigmata (max 11). Missing clinical measurements do not default to normal: the CLI/API report completeness flags, a partial subtotal and null for outcomes requiring unavailable information. SBP below 100 suffices for shock 2 even if pulse is unavailable.

The Python `major` option denotes the 3-point category (renal failure, liver failure or disseminated malignancy). `other_major` specifically denotes the 2-point category.

### Historical outcomes (percent)

| Score | Clinical-score mortality | Complete-score mortality | Complete-score rebleeding |
| --- | ---: | ---: | ---: |
| 0 | 0.2 | 0 | 4.9 |
| 1 | 2.4 | 0 | 3.4 |
| 2 | 5.6 | 0.2 | 5.3 |
| 3 | 11.0 | 2.9 | 11.2 |
| 4 | 24.6 | 5.3 | 14.1 |
| 5 | 39.6 | 10.8 | 24.1 |
| 6 | 48.9 | 17.3 | 32.9 |
| 7 | 50.0 | 27.0 | 43.8 |
| ≥8 | Not applicable | 41.1 | 41.8 |

The source combines complete scores 8–11 into one ≥8 category. These are **observed historical cohort frequencies**, not calibrated probabilities for an individual patient.

**Clinical limitation:** Rockall alone must not determine admission, discharge, ICU disposition or therapy. ACG and ESGE UGIB guidelines recommend Glasgow–Blatchford scoring for initial low-risk assessment with clinical judgment. Rockall is less reliable for predicting rebleeding than mortality.

## Python and CLI

Python 3.10+ is required.

```bash
python -m pip install -e ".[dev]"
python cli.py single --age 70 --hr 110 --sbp 85 --comorbidity cardiac
python cli.py single --age 70 --hr 110 --sbp 85 --comorbidity cardiac --diagnosis peptic_ulcer --stigmata blood
python cli.py batch -i sample.csv -o results.csv
python -m pytest -q
```

CSV supports `age`, `hr`/`heart_rate`, `sbp`, `comorbidity`, `diagnosis` and `stigmata`. Invalid inputs fail explicitly and identify CSV row numbers. Batch processing accepts absolute file paths but does not overwrite its source. Keep identifiable patient data only on appropriately protected systems.

## Optional API

```bash
python -m pip install -e ".[web]"
uvicorn agents.api:app --host 127.0.0.1 --port 8000
```

The served homepage displays the same browser-only calculator. `POST /api/score` accepts age, shock_hr, shock_sbp, comorbidity, endoscopic_diagnosis and major_stigmata as JSON. `GET /health` and `GET /metrics` provide service information.

Legacy audit/chat endpoints are retained but are **not** Rockall clinical assessment systems. `GET /api/audit/logs` is disabled unless `ENABLE_AUDIT_LOGS=1` is set. The HMAC ledger is in-memory, not persistent. Its regex-based PHI guard does not guarantee de-identification or HIPAA compliance. Do not expose the API publicly without additional authentication, access controls, and operational safeguards.

For local Docker deployment:

```bash
export AUDIT_SECRET_KEY="set-a-long-random-secret"
docker compose up --build
```

The Compose configuration requires a secret and binds port 8000 to the local host by default.

## Tests and deployment

```bash
python -m pytest -q
node --test web/test-app.cjs
```

GitHub Actions runs Python 3.10–3.12 tests, browser logic tests using Node.js, and a Python dependency audit. The Pages job publishes the static root application after checks pass on `master`. The browser implementation uses standard HTML, CSS and JavaScript; Pyodide is unnecessary. Modern evergreen browsers are targeted.

## References

- Rockall TA, Logan RFA, Devlin HB, Northfield TC. Risk assessment after acute upper gastrointestinal haemorrhage. *Gut*. 1996;38:316–321. [DOI: 10.1136/gut.38.3.316](https://doi.org/10.1136/gut.38.3.316).
- [Original-cohort outcome tables](https://ovesco.com/complete-rockall-score/).
- Laine L et al. [ACG Clinical Guideline: Upper Gastrointestinal and Ulcer Bleeding](https://pubmed.ncbi.nlm.nih.gov/33929377/). 2021.
- [ESGE Guideline Update 2021](https://www.esge.com/endoscopic-diagnosis-and-management-of-nonvariceal-upper-gastrointestinal-hemorrhage-esge-update-2021).

## License

MIT — see [LICENSE](LICENSE).
