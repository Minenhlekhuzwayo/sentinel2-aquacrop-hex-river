# Single-notebook cleanup record

- Source: latest uploaded executed notebook `01_sentinel2_aquacrop_pipeline_FINAL (3).ipynb`, via the previously cleaned complete pipeline.
- Only one notebook remains: `notebooks/Sentinel2_AquaCropOSPy_TableGrapes_HexRiver_Pipeline.ipynb`.
- Sections 1–12 contain the full code, labelled in order. Section 13 shows completed outputs and runs the software checks, all in the same notebook.
- Markdown explanations use simple short sentences. Code comments mark every stage and clarify numerical safeguards, simulation comparisons, evaluation and scenario limits.
- AST comparison confirmed that the scientific calculation statements did not change.
- The full crop model was not rerun during this formatting cleanup. Original saved model results were preserved.
- The project uses `src/pipeline_utils.py` for reusable functions and the bundled data files, not another notebook.
