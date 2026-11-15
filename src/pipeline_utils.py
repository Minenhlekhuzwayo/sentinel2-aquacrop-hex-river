"""Pure-data preprocessing and QA helpers for the Dagbreek research pipeline.

All event dates refer to an empirical block-mean NDVI-derived canopy proxy,
NOT independently observed vine phenology or physical canopy fraction.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy.signal import savgol_filter
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

SEASONS = [f"{year}/{year+1}" for year in range(2017, 2024)]
FEATURES = ("NDVI", "EVI2", "NDMI", "NDRE", "B4", "B5", "B8", "B11")
EVENTS = {
    "Full_Budbreak": "Full_Budbreak_Date",
    "Maximum_CC": "Maximum_CC_Date",
    "Senescence_Onset": "Senescence_Onset_Date",
    "End_of_Season": "End_of_Season_Date",
}


def daily_gdd(tmin, tmax, tbase: float = 10.0, tupper: float = 35.0):
    """AquaCrop GDD method 1: clip MEAN(Tmin,Tmax), then subtract base."""
    if tupper <= tbase:
        raise ValueError("tupper must exceed tbase")
    mean = (np.asarray(tmin, dtype=float) + np.asarray(tmax, dtype=float)) / 2.0
    out = np.maximum(np.minimum(mean, tupper) - tbase, 0.0)
    return float(out) if out.ndim == 0 else out


def clean_satellite_features(raw: pd.DataFrame) -> pd.DataFrame:
    """One block-mean record/date, seven Sep-Apr seasons, no fabricated observations."""
    df = raw.copy()
    if "NDWI" in df and "NDMI" not in df:
        df = df.rename(columns={"NDWI": "NDMI"})
    missing = {"Date", *FEATURES} - set(df.columns)
    if missing:
        raise ValueError(f"Missing satellite input columns: {sorted(missing)}")
    df["Date"] = pd.to_datetime(df["Date"], errors="raise").dt.normalize()
    for name in FEATURES:
        df[name] = pd.to_numeric(df[name], errors="coerce")
    df = df.sort_values("Date").groupby("Date", as_index=False)[list(FEATURES)].mean()
    years = np.where(df["Date"].dt.month <= 4, df["Date"].dt.year - 1, df["Date"].dt.year)
    df["Season"] = pd.Series(years, index=df.index).astype(str) + "/" + pd.Series(years + 1, index=df.index).astype(str)
    df = df[df["Date"].dt.month.isin([9, 10, 11, 12, 1, 2, 3, 4])]
    df = df[df["Season"].isin(SEASONS)].dropna(subset=list(FEATURES))
    df = df[["Date", "Season", *FEATURES]].sort_values(["Season", "Date"]).reset_index(drop=True)
    if df.empty:
        raise ValueError("No cloud-screened satellite records remain")
    return df


def check_seasons(df: pd.DataFrame):
    got = sorted(df["Season"].unique())
    if got != SEASONS:
        raise AssertionError(f"Expected the seven growing seasons {SEASONS}; got {got}")
    if df["Date"].isna().any():
        raise AssertionError("Missing date(s) in selected seasons")


def canopy_proxy_and_smoothing(
    satellite: pd.DataFrame,
    interval_days: int = 5,
    window: int = 7,
    polyorder: int = 2,
):
    """Global 5th/95th percentile NDVI scaling + interpolation preserving off-grid observations."""
    check_seasons(satellite)
    if window % 2 != 1 or window <= polyorder:
        raise ValueError("Savitzky-Golay window must be odd and exceed polyorder")
    df = satellite.copy()
    lo = float(df["NDVI"].quantile(.05))
    hi = float(df["NDVI"].quantile(.95))
    if not np.isfinite([lo, hi]).all() or hi <= lo:
        raise ValueError("NDVI endmembers are invalid")
    df["CC_unclipped"] = (df["NDVI"] - lo) / (hi - lo)
    df["Sentinel_CC_Proxy"] = df["CC_unclipped"].clip(0, 1)
    curves, qa = [], []
    for season, part in df.groupby("Season", sort=True):
        obs = part.set_index("Date")["Sentinel_CC_Proxy"].sort_index()
        if obs.index.has_duplicates:
            raise AssertionError("Duplicate dates remain after cleaning")
        gaps = obs.index.to_series().diff().dt.days.dropna()
        regular = pd.date_range(obs.index.min(), obs.index.max(), freq=f"{interval_days}D")
        # Reindex to the UNION first: simply reindexing to the 5-day grid drops
        # observations on off-grid dates and silently changes the evidence.
        union = obs.reindex(obs.index.union(regular)).sort_index()
        reconstructed = union.interpolate(method="time", limit_area="inside").reindex(regular)
        if reconstructed.isna().any() or len(reconstructed) < window:
            raise ValueError(f"{season}: insufficient support to smooth ({len(reconstructed)} dates)")
        smooth = savgol_filter(reconstructed.to_numpy(dtype=float), window_length=window, polyorder=polyorder)
        curve = pd.DataFrame({
            "Date": regular,
            "Season": season,
            "Sentinel_CC_Interpolated": reconstructed.to_numpy(dtype=float),
            "Sentinel_CC_Smoothed": np.clip(smooth, 0, 1),
            "Direct_Observation_On_Grid": regular.isin(obs.index),
        })
        curves.append(curve)
        qa.append({
            "Season": season,
            "Number_of_Raw_Observations": len(obs),
            "First_Observation": obs.index.min(),
            "Last_Observation": obs.index.max(),
            "Median_Gap_Days": float(gaps.median()) if len(gaps) else np.nan,
            "Maximum_Gap_Days": int(gaps.max()) if len(gaps) else np.nan,
            "Gaps_Above_15_Days": int((gaps > 15).sum()),
            "Regular_Grid_Points": len(regular),
            "Direct_Observations_On_Grid": int(regular.isin(obs.index).sum()),
        })
    settings = {
        "Low_percentile": 5,
        "High_percentile": 95,
        "NDVI_low_endmember": lo,
        "NDVI_high_endmember": hi,
        "Grid_interval_days": interval_days,
        "SG_window_points": window,
        "SG_nominal_window_days": interval_days * window,
        "SG_polyorder": polyorder,
    }
    return df, pd.concat(curves, ignore_index=True), pd.DataFrame(qa), settings


def detect_budbreak(values, threshold=.05, window_points=5, positive_fraction=.75, minimum_increase=.05):
    """First early-green-up candidate with sustained positive 5-day-grid development."""
    cc = np.asarray(values, dtype=float)
    for i in range(len(cc) - window_points + 1):
        future = cc[i:i+window_points]
        if (
            np.isfinite(future).all()
            and cc[i] >= threshold
            and np.mean(np.diff(future) > 0) >= positive_fraction
            and future[-1] - future[0] >= minimum_increase
        ):
            return i
    return None


def detect_phenology(curve: pd.DataFrame) -> dict:
    """Replicate current operational thresholds, with deterministic missing-data handling."""
    df = curve.sort_values("Date").reset_index(drop=True)
    cc = df["Sentinel_CC_Smoothed"].to_numpy(dtype=float)
    if len(cc) == 0 or not np.isfinite(cc).any():
        raise ValueError("Cannot derive phenology without finite smoothed canopy proxy")
    max_i = int(np.nanargmax(cc))  # first attainment of seasonal maximum
    max_cc = float(cc[max_i])
    bud_i = detect_budbreak(cc)
    full_i = None
    if bud_i is not None:
        for i in range(bud_i, len(cc) - 2):
            if np.all(cc[i:i + 3] >= .10):
                full_i = i
                break
    sen_date = pd.NaT
    threshold = .9 * max_cc
    post = df.iloc[max_i:].set_index("Date")
    change = post["Sentinel_CC_Smoothed"].rolling("30D").mean().diff()
    for i in range(1, len(post)):
        future = change.iloc[i:min(i + 4, len(change))]
        if (
            post["Sentinel_CC_Smoothed"].iloc[i] <= threshold
            and pd.notna(change.iloc[i]) and change.iloc[i] < 0
            and len(future) >= 1 and (future < 0).mean() >= .75
        ):
            sen_date = post.index[i]
            break
    eos_date = pd.NaT
    if pd.notna(sen_date):
        starts = df.index[df["Date"] == sen_date]
        if len(starts):
            for i in range(int(starts[0]), len(cc) - 2):
                if np.all(cc[i:i+3] <= .50) and cc[i] >= cc[i+1] >= cc[i+2]:
                    eos_date = df.loc[i, "Date"]
                    break
    date_or_nat = lambda i: df.loc[i, "Date"] if i is not None else pd.NaT
    return {
        "Budbreak_Date": date_or_nat(bud_i),
        "Full_Budbreak_Date": date_or_nat(full_i),
        "Maximum_CC_Date": df.loc[max_i, "Date"],
        "Senescence_Onset_Date": sen_date,
        "End_of_Season_Date": eos_date,
        "Maximum_CC_Proxy": max_cc,
        "Budbreak_Threshold": .05,
        "Full_Budbreak_Threshold": .10,
        "Senescence_Threshold": threshold,
        "End_of_Season_Threshold": .50,
        "Budbreak_To_FullBudbreak_Days": (
            (date_or_nat(full_i) - date_or_nat(bud_i)).days
            if full_i is not None and bud_i is not None else np.nan
        ),
        "Full_Budbreak_Equals_Budbreak": bool(bud_i == full_i) if bud_i is not None and full_i is not None else False,
    }


def phenology_from_curves(curves: pd.DataFrame, raw: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for season, curve in curves.groupby("Season", sort=True):
        events = detect_phenology(curve)
        raw_dates = raw.loc[raw["Season"] == season, "Date"]
        for name in ["Budbreak", "Full_Budbreak", "Maximum_CC", "Senescence_Onset", "End_of_Season"]:
            d = events.get(name + "_Date")
            events[name + "_Distance_to_Closest_Raw_Observation_Days"] = (
                int((raw_dates - d).abs().dt.days.min()) if pd.notna(d) else np.nan
            )
            if pd.notna(d):
                left = raw_dates[raw_dates <= d]
                right = raw_dates[raw_dates >= d]
                # The nearest acquisition alone conceals uncertainty when an
                # event is near one end of a long cloud-related gap.
                events[name + "_Bracketing_Observation_Gap_Days"] = (
                    int((right.min() - left.max()).days)
                    if len(left) and len(right) else np.nan
                )
            else:
                events[name + "_Bracketing_Observation_Gap_Days"] = np.nan
        first = raw.loc[raw["Season"] == season].sort_values("Date").iloc[0]
        events["First_Raw_Observation_Already_Above_FullBudbreak"] = bool(first["Sentinel_CC_Proxy"] >= 0.10)
        events["Budbreak_At_First_Raw_Observation"] = bool(
            pd.notna(events["Budbreak_Date"]) and events["Budbreak_Date"] == first["Date"]
        )
        events["Early_Growth_Left_Censored_Flag"] = bool(
            events["First_Raw_Observation_Already_Above_FullBudbreak"]
            and events["Budbreak_At_First_Raw_Observation"]
        )
        rows.append({"Season": season, **events})
    result = pd.DataFrame(rows)
    check_seasons(result.assign(Date=pd.Timestamp("2017-01-01")))
    return result


def event_gdd_table(phenology: pd.DataFrame, daily_weather: pd.DataFrame):
    """Daily GDD includes budbreak date; budbreak is declared 0 as a reference.

    The same-date full-budbreak value can therefore be >0. This accounting
    convention is preserved from the research notebook and must be described.
    """
    require = {"Date", "MinTemp", "MaxTemp"}
    if require - set(daily_weather):
        raise ValueError("Weather lacks Date, MinTemp or MaxTemp")
    df = daily_weather[["Date", "MinTemp", "MaxTemp"]].copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date")
    df["MeanTemp"] = (df["MinTemp"] + df["MaxTemp"]) / 2
    df["GDD"] = daily_gdd(df["MinTemp"], df["MaxTemp"])
    rows, daily_rows = [], []
    for _, row in phenology.iterrows():
        bud = pd.to_datetime(row["Budbreak_Date"])
        season = row["Season"]
        if pd.isna(bud):
            raise ValueError(f"{season}: budbreak not detected; cannot run AquaCrop")
        end = pd.Timestamp(int(season.split("/")[1]), 4, 30)
        current = df[(df.Date >= bud) & (df.Date <= end)].copy()
        if current.empty:
            raise ValueError(f"{season}: missing weather over the crop season")
        if len(current) != (end - bud).days + 1:
            raise ValueError(f"{season}: incomplete daily weather after budbreak")
        current["Accumulated_GDD"] = current.GDD.cumsum()
        current["Season"] = season
        daily_rows.append(current)
        entry = {"Season": season, "Budbreak_Date": bud, "Budbreak_GDD": 0.0}
        for ev, col in EVENTS.items():
            date = pd.to_datetime(row[col])
            entry[ev + "_Date"] = date
            if pd.isna(date):
                entry[ev + "_GDD"] = np.nan
            elif date < bud or date > end:
                raise ValueError(f"{season}: {ev} event date outside simulated season")
            else:
                entry[ev + "_GDD"] = float(current.loc[current.Date == date, "Accumulated_GDD"].iloc[0])
        rows.append(entry)
    return pd.DataFrame(rows), pd.concat(daily_rows, ignore_index=True)


def aquacrop_max_canopy_gdd(crop) -> float:
    term = (0.25 * crop.CCx**2 / crop.CC0) / (crop.CCx - .98 * crop.CCx)
    if term <= 0 or crop.CGC <= 0:
        raise ValueError("Invalid crop canopy-growth parameters")
    return float(crop.Emergence + math.log(term) / crop.CGC)


def derive_cgc(cc0: float, ccx: float, emergence: float, satellite_peak: float) -> float:
    if satellite_peak <= emergence:
        raise ValueError("Satellite peak GDD must exceed the numerical emergence time")
    term = (0.25 * ccx**2 / cc0) / (ccx - .98 * ccx)
    result = math.log(term) / (satellite_peak - emergence)
    if result <= 0 or not np.isfinite(result):
        raise ValueError("Non-positive or non-finite CGC")
    return float(result)


def metrics(observed, simulated) -> dict:
    obs, sim = np.asarray(observed, dtype=float), np.asarray(simulated, dtype=float)
    if obs.shape != sim.shape or len(obs) < 3 or not np.isfinite(obs).all() or not np.isfinite(sim).all():
        raise ValueError("Model–satellite metrics require >=3 paired finite observations")
    return {
        "N": int(len(obs)),
        "RMSE": float(np.sqrt(mean_squared_error(obs, sim))),
        "MAE": float(mean_absolute_error(obs, sim)),
        "R2": float(r2_score(obs, sim)) if np.var(obs) > 1e-12 else np.nan,
    }


def normalized_metrics(observed, baseline, informed):
    arrays = [np.asarray(x, dtype=float) for x in (observed, baseline, informed)]
    if any(not np.isfinite(x).all() or x.max() <= 0 for x in arrays):
        raise ValueError("Cannot normalize a constant-zero or invalid canopy curve")
    return tuple(x / x.max() for x in arrays)


def safe_pct_change(new: float, reference: float):
    return 100 * (new - reference) / reference if abs(reference) > 1e-10 else np.nan
