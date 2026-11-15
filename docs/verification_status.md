> **Historical preflight note (6 November 2026):** This document records checks made before the later completed-run archive was supplied. For the seven-season completed-run record, see `data/processed/run_manifest.json` and `docs/execution_evidence.md`. Passing software tests is not independent agronomic validation.

# Verification status — 6 November 2026

## Verified locally

- Original NASA POWER daily source is present (5,479 rows, 2010-01-01–2024-12-31); units and -999 missing-value marker are recorded in the header.
- Archived original Sentinel feature source is present (219 dates over seven Sep–Apr growing seasons). It has been processed using the new `src.pipeline_utils` code.
- Seven growing-season canopy proxy curves, date-gap summaries, phenology proxy tables and GDD summaries were generated **from this historical 219-date archive**.
- Six automated unit tests of the pure-data code passed; notebook code cells pass Python syntax compilation.
- The interpolator now retains all original dates even if an acquisition does not coincide with the 5-day grid. The historic archived features happen to align with the grid, but the new code handles other cases.
- Corrected canopy-proxy phenology DOES NOT precisely reproduce all previous figures. For instance, the new 2017/18 early-green-up proxy is 2017-09-08, while an earlier exploratory stage reported 2017-09-23. Because the first two actual satellite acquisitions are 40 days apart, this stage is especially uncertain. Do not mix the old metrics with recalculated phenology.
- The archived 2017/18 series contains a 50-day observation gap; a 2017/18 budbreak estimate inside a sparse interval is particularly uncertain. The first observation in certain seasons already has appreciable canopy proxy, making early-season onset left-censored.

## Not verified in this runtime

- ReferenceET output, because `refet` is not installed here and external installation was blocked.
- Full Earth Engine extraction, because an authenticated account/project is not available here. The 219-versus-223 historical extraction discrepancy **has not been independently adjudicated**.
- AquaCrop-OSPy crop-object construction and seven-season execution, because `aquacrop` is not installed here and downloading it was blocked. The final notebook is ready to execute in a compatible connected Colab environment, but there is **no newly verified model performance table**.
- `Kcb=1.10` is now explicitly in the project working parameter set. This changes prior implicit-default scenarios; the value's provenance still needs checking against the primary paper and water results require rerunning.
- The model simulation date/runtime assertions, fallow custom-crop workaround and exact output schema must be checked with AquaCrop-OSPy 3.1.0.

## Research inference status

The earlier reported seven-season canopy/water comparisons remain **historical preliminary outputs**, not newly reproduced estimates. They are not shipped as current final results. A successful, complete run through notebook Section 11 is required before using new numerical outputs in the final dissertation.

## 2026-11-06 preflight refinements

- Phenology QA now includes `*_Bracketing_Observation_Gap_Days` rather than only the distance to the nearest acquisition. The 2017/18 inferred budbreak is within a **40-day gap**; it must not be described as a precisely observed budbreak date.
- The 2018/19 early-season green-up is **left-censored**: the first valid acquisition (2018-10-03) already exceeds the 0.10 canopy-proxy threshold.
- The six unit tests and the archived-input preflight (`tests/offline_preflight.py`) pass, but do not exercise the AquaCrop engine or RefET calculation.
