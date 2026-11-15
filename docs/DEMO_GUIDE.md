# Demo guide — one complete notebook

Open `notebooks/Sentinel2_AquaCropOSPy_TableGrapes_HexRiver_Pipeline.ipynb`. It contains both the complete implementation and the saved-results review.

| What to show | Notebook section | Simple narration |
|---|---|---|
| Research question | Title | The project uses satellite and weather data to improve simulated seasonal canopy agreement. |
| Weather data | 2 | Prepare daily climate inputs for AquaCrop. |
| Satellite observations | 3–4 | Check images, compute NDVI and smooth the vegetation curve. |
| Growth timing | 5–6 | Extract dates and convert to growing degree days. |
| Model setup | 7–8 | Keep the same conditions and change selected crop timing parameters. |
| Paired simulations | 9 | Run two models for each of seven seasons. |
| Compare canopy | 10 and 13.2 | Lower error means closer agreement with the satellite curve. |
| Water results | 11 and 13.3 | Discuss simulated water changes, not measured savings. |
| Testing and provenance | 12 and 13.1/13.3 | Show the run manifest and six software tests. |

For a reliable recording, run Section 13 only, which uses already-saved results. To repeat the full experiment, install `requirements.txt` and run the notebook from the top.
