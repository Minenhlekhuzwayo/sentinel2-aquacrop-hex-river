# Execution evidence and verification boundaries

## Completed source package

The supplied `Dagbreek_Research_Results (2).zip` contains `data/processed/run_manifest.json` with the status `full_aquacrop_seven_season_run_completed_and_checked`, seven recorded seasons and 219 archived satellite dates. It also contains all paired comparison tables and generated figures. The separately supplied `01_sentinel2_aquacrop_pipeline_FINAL (3).ipynb` has execution counts and saved outputs for the completed computational workflow. The data archive's notebook, by contrast, is the earlier clean unexecuted notebook.

## Checks carried out during readability cleanup

- The cleaned full notebook was generated from the **latest executed source** (3), excluding only the Colab ZIP setup and optional Colab download/export commands.
- An AST-based check verified the scientific calculation code was **identical** after splitting large cells into annotated steps.
- The six local pure-data unit tests passed.
- Section 13 of the single notebook reads the archived outputs; it is not a new simulation.

## Not independently checked here

The `aquacrop` and `refet` packages are unavailable in this local environment, so the seven paired AquaCrop simulations and weather ET calculations were **not rerun during cleanup**. Data and outputs are the researcher's archived execution results. The 219 vs 223 earlier extraction discrepancy and the source of `Kcb=1.10` remain unresolved in the provided research material.
