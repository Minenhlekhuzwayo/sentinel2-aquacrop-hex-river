# Publication and upload checklist

Use a **private GitHub repository** at first. The package includes an exact vineyard-block polygon in `data/study_area/dagbreek_vineyard_block.geojson` and extracted satellite and climate datasets. Confirm permission to share this material before changing visibility to public.

Before the first **commit** (even to a private remote):
- [ ] Review `data/study_area/` and `data/raw/` for any data you are not authorised to distribute.
- [ ] Review the Jupyter notebook for tokens, email addresses, private paths, and accidental secrets.
- [ ] Confirm that the notebook in `notebooks/` is the corrected, working version used in Colab.
- [ ] Confirm `README.md`, `requirements.txt` and `.gitignore` are present at the repository root.
- [ ] Confirm `.pytest_cache`, `__pycache__`, downloaded ZIPs and the large `.mp4` demo video are excluded.
- [ ] Inspect **GitHub Desktop → Changes** to see exactly what is being committed.
- [ ] Run `python -m pytest -q tests/test_pipeline_utils.py` if the local environment has dependencies installed.

Before ever making the repository **public**:
- [ ] Get supervisor/owner agreement to reveal the precise vineyard location/boundary.
- [ ] Confirm satellite-derived exports, NASA POWER records and third-party data may be redistributed.
- [ ] Confirm all images, figures and bibliographic details have appropriate attribution.
- [ ] Decide whether an explicit code licence is appropriate; none has been selected yet.
- [ ] Inspect past commits too: `.gitignore` does not remove previously committed confidential material.

Scientific claims to keep in documentation:
- The seven-season run manifest records 14 simulations, but some early verification notes were written **before** the completed archive.
- The error reduction is **in-sample satellite–model agreement**, not independent field validation.
- The water table contains **simulated** amounts under assumed conditions, not measured irrigation savings.
- `Kcb=1.10` is a documented parameter assumption with unverified primary-source provenance.
