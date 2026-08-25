# Rockall Score for Upper GI Bleeding

> **Post-endoscopy Mortality and Rebleeding Risk Assessment**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB.svg)

---

## Overview

The Rockall Score is a validated scoring system for assessing mortality and rebleeding risk after acute upper gastrointestinal hemorrhage. It combines clinical (pre-endoscopy) and endoscopic (post-endoscopy) components.

**Score range: 0-11** (Clinical: 0-7, Endoscopic: 0-4)

---

## Scoring Components

### Clinical (Pre-endoscopy)

| Component | Points |
|-----------|--------|
| **Age** | <60: **0**, 60-79: **1**, ≥80: **2** |
| **Shock** | HR>100 & SBP≥100: **1**, SBP<100: **2** |
| **Comorbidity** | None: **0**, CHF/IHD: **2**, Renal/Liver failure/Malignancy: **3** |

### Endoscopic (Post-endoscopy)

| Component | Points |
|-----------|--------|
| **Diagnosis** | Mallory-Weiss/None: **0**, Peptic ulcer/ESD: **1**, Cancer: **2** |
| **Major stigmata** | None/Dark spot: **0**, Blood/Visible vessel/Active bleeding: **2** |

## Mortality Risk by Total Score

| Score | Mortality | Risk Category |
|-------|-----------|---------------|
| 0 | 0.2% | Low |
| 1 | 0.4% | Low |
| 2 | 2.2% | Low |
| 3 | 3.3% | Moderate |
| 4 | 5.3% | Moderate |
| 5-6 | 8% | High |
| 7-8 | 14% | High |
| ≥9 | 27% | Very High |

---

## Quick Start

```bash
# Single patient (clinical only)
python rockall_score.py single --age 70 --sbp 85 --comorbidity cardiac

# Full post-endoscopy score
python rockall_score.py single --age 70 --sbp 85 --comorbidity cardiac --diagnosis peptic_ulcer --stigmata active_bleeding

# Batch processing
python rockall_score.py batch -i patients.csv -o results.csv
```

## Python API

```python
from rockall_score import calculate_rockall

result = calculate_rockall(
    age=70, shock_hr=110, shock_sbp=85,
    comorbidity="cardiac",
    endoscopic_diagnosis="peptic_ulcer",
    major_stigmata="active_bleeding",
)

print(f"Clinical Score: {result['clinical_score']}")
print(f"Endoscopic Score: {result['endoscopic_score']}")
print(f"Total Score: {result['total_score']}")
print(f"Mortality: {result['mortality_percent']}%")
print(f"Rebleeding: {result['rebleeding_percent']}%")
```

## Tests

```bash
python -m pytest test_rockall_score.py -v
```

## References

- Rockall TA, et al. Risk assessment after acute upper gastrointestinal haemorrhage. *Gut* 1996;38:316-21.
- Rockall TA, et al. Validation of a scoring system for assessment of prognosis after acute upper gastrointestinal haemorrhage. *Gut* 1996;38:322-7.

## License

MIT License. See [LICENSE](LICENSE).
