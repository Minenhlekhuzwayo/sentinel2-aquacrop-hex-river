# Before claiming final study results

1. Use Python **3.11 or 3.12**, install `requirements.txt` successfully, and record `aquacrop.__version__` and `refet.__version__`.
2. Run `python -m pytest -q tests` (six unit tests), then open `notebooks/Sentinel2_AquaCropOSPy_TableGrapes_HexRiver_Pipeline.ipynb` in the repository.
3. Select the authoritative satellite extraction: the included 219-date archive is the documented default. To investigate the historical 223-date version, perform an authenticated GEE re-extraction **separately**, examine any differences, and only then decide which extraction to use consistently across all sections.
4. Audit `config/parameter_provenance.csv` against the full Er-Raki paper (particularly **Kcb=1.10**, Tupp, crop-stage and stress parameters). Once locked, do **not** mix earlier water metrics with rerun parameters.
5. Run notebook Sections 0–11 from a clean kernel. Section 8 must verify seven pairs of full budbreak-to-30-April output ranges and flag model runtime problems instead of suppressing them.
6. Confirm that the technical harvest-date workaround and `Name="Default"` custom crop handling produce correct outputs under AquaCrop-OSPy 3.1.0.
7. Review Section 9 metrics on both **smoothed** (development/timing) and **direct acquisition** (sensitivity) dates, with normalized vs raw scale clearly distinguished.
8. Review Section 10 water totals and check whether scenario parameters cause plausible but *not field-validated* irrigation/ET differences.
9. Report missing field phenology, mixed vine/inter-row pixel signal, long 2017/18 cloud gaps, in-sample peak constraint, uncalibrated soil and controlled irrigation scenario as limitations.
10. Confirm successful Section 11 message and presence of `data/processed/run_manifest.json`. The cached preflight manifest (`offline_preflight_manifest.json`) is **not** evidence of a final AquaCrop run.
11. Before publishing a public GitHub repository, check whether the exact Dagbreek vineyard boundary is approved for publication and whether the source data can be redistributed.
