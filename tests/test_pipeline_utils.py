"""Run: python -m pytest -q tests/"""
import numpy as np
import pandas as pd
import pytest
from src.pipeline_utils import (
    SEASONS, daily_gdd, clean_satellite_features, canopy_proxy_and_smoothing,
    detect_budbreak, derive_cgc, metrics, safe_pct_change,
)


def test_gdd_method1_mean_clipped_not_extreme_temp_clipped():
    assert np.allclose(daily_gdd([4, 20, 30], [14, 50, 46]), [0, 25, 25])
    assert daily_gdd(4, 14) == 0.0


def test_ndwi_renamed_and_seasons_retained():
    d = pd.DataFrame({"Date": [f"{y}-09-01" for y in range(2017, 2024)],
                      **{k: [.3]*7 for k in ["NDVI","EVI2","NDWI","NDRE","B4","B5","B8","B11"]}})
    cleaned = clean_satellite_features(d)
    assert list(cleaned.Season) == SEASONS
    assert "NDMI" in cleaned and "NDWI" not in cleaned


def test_off_grid_satellite_values_preserved():
    rows=[]
    for y in range(2017,2024):
        for day, ndvi in zip([1, 3, 9, 13, 17, 19, 25, 29, 34, 40], [.2,.25,.4,.5,.7,.8,.81,.7,.6,.4]):
            rows.append({"Date":pd.Timestamp(y,9,1)+pd.Timedelta(days=day-1),"Season":f"{y}/{y+1}","NDVI":ndvi})
    d=pd.DataFrame(rows)
    d["EVI2"] = d.NDVI
    for col in ("NDMI","NDRE","B4","B5","B8","B11"): d[col] = d.NDVI
    raw, series, qa, settings = canopy_proxy_and_smoothing(d)
    assert (qa["Number_of_Raw_Observations"]==10).all()
    assert np.isfinite(series["Sentinel_CC_Smoothed"]).all()
    assert settings["SG_window_points"] == 7
    assert (qa["Direct_Observations_On_Grid"] < qa["Number_of_Raw_Observations"]).all()


def test_budbreak_sustained():
    assert detect_budbreak([0,.05,.06,.08,.10,.13]) == 1
    assert detect_budbreak([0,.08,0,0,0,0]) is None


def test_cgc_matches_imposed_peak():
    cc0,ccx,emergence,target=.064,.65,10,650
    derived=derive_cgc(cc0,ccx,emergence,target)
    term=(.25*ccx**2/cc0)/(ccx-.98*ccx)
    assert abs(emergence+np.log(term)/derived-target)<1e-9
    with pytest.raises(ValueError): derive_cgc(cc0,ccx,100,90)


def test_comparison_metrics_and_zero_division():
    assert metrics([0, .5, 1], [0, .5, 1])["RMSE"] == 0
    assert np.isnan(safe_pct_change(2,0))
