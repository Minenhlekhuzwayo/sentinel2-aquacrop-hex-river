"""Rebuild the *satellite/GDD only* intermediates offline using archived project files.

Does not run reference ET or AquaCrop; do not mislabel its products as final model results.
Run from repository root: python tests/offline_preflight.py
"""
from pathlib import Path
import hashlib
import json
import sys
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.pipeline_utils import (
    clean_satellite_features, canopy_proxy_and_smoothing, phenology_from_curves,
    event_gdd_table, daily_gdd, SEASONS,
)
raw=ROOT/'data/raw/sentinel2_dagbreek_features_archived_219.csv'
weatherfile=ROOT/'data/raw/weatherDatasetNASAPower.csv'
assert raw.exists() and weatherfile.exists()
df=clean_satellite_features(pd.read_csv(raw))
satellite, curves, gaps, settings=canopy_proxy_and_smoothing(df)
events=phenology_from_curves(curves,satellite)
w=pd.read_csv(weatherfile,skiprows=16,na_values=[-999,-999.0])
assert len(w)==5479
w['Date']=pd.to_datetime(w.YEAR.astype(int).astype(str)+'-01-01')+pd.to_timedelta(w.DOY-1,unit='D')
w=w.rename(columns={'T2M_MIN':'MinTemp','T2M_MAX':'MaxTemp'})
assert w[['MinTemp','MaxTemp','Date']].notna().all().all()
gdd,daily=event_gdd_table(events,w)
assert len(df)==219 and len(gdd)==7 and len(events)==7
assert list(df.groupby('Season').size()) == [16,31,34,34,33,37,34]
assert np.isfinite(daily['GDD']).all()
processed=ROOT/'data/processed'
tables=ROOT/'outputs/tables'
for f,table in [('sentinel2_features_clean.csv',df),('sentinel2_features_with_cc_proxy.csv',satellite),
 ('sentinel2_canopy_smoothed.csv',curves),('phenology.csv',events),('phenology_gdd.csv',gdd),('daily_gdd.csv',daily)]:
 table.to_csv(processed/f,index=False)
gaps.to_csv(tables/'observation_gap_qa.csv',index=False)
pd.DataFrame([settings]).to_csv(tables/'canopy_proxy_parameters.csv',index=False)
styles={'Budbreak_Date':'green','Full_Budbreak_Date':'dodgerblue','Maximum_CC_Date':'darkorange',
        'Senescence_Onset_Date':'red','End_of_Season_Date':'purple'}
for season in SEASONS:
 raw_rows=satellite[satellite.Season==season]
 smooth=curves[curves.Season==season]
 row=events[events.Season==season].iloc[0]
 fig,ax=plt.subplots(figsize=(9,4.4))
 ax.scatter(raw_rows.Date,raw_rows.Sentinel_CC_Proxy,s=22,label='Actual Sentinel acquisition')
 ax.plot(smooth.Date,smooth.Sentinel_CC_Smoothed,lw=2,label='Reconstructed + smoothed proxy')
 ax.set(title=f'Dagbreek canopy proxy: {season}',xlabel='Date',ylabel='NDVI-derived proxy (0–1)',ylim=(0,1.05))
 ax.legend(fontsize=8);ax.grid(alpha=.2);fig.autofmt_xdate();fig.tight_layout()
 fig.savefig(ROOT/'outputs/figures/canopy'/f'raw_vs_smoothed_{season.replace("/","-")}.png',dpi=160)
 plt.close(fig)
 fig,ax=plt.subplots(figsize=(9.5,4.6))
 ax.scatter(raw_rows.Date,raw_rows.Sentinel_CC_Proxy,s=18,label='Actual Sentinel acquisition',alpha=.7)
 ax.plot(smooth.Date,smooth.Sentinel_CC_Smoothed,lw=2,label='Smoothed proxy')
 for ev,color in styles.items():
  if pd.notna(row[ev]):ax.axvline(row[ev],ls='--',color=color,label=ev.replace('_Date','').replace('_',' '))
 ax.set(title=f'Satellite phenological proxies: {season}',xlabel='Date',ylabel='NDVI-derived proxy (0–1)',ylim=(0,1.05))
 ax.legend(fontsize=7,ncol=2);ax.grid(alpha=.2);fig.autofmt_xdate();fig.tight_layout()
 fig.savefig(ROOT/'outputs/figures/phenology'/f'phenology_{season.replace("/","-")}.png',dpi=160)
 plt.close(fig)
fig,ax=plt.subplots(figsize=(10,5))
ax.plot(gdd.Season,gdd.Maximum_CC_GDD,'o-',label='Peak canopy proxy')
ax.plot(gdd.Season,gdd.Senescence_Onset_GDD,'o-',label='Senescence proxy')
ax.tick_params(axis='x',rotation=30)
ax.set(title='GDD of satellite phenological proxies — archived 219 observations',ylabel='GDD since satellite budbreak')
ax.legend();ax.grid(alpha=.2);fig.tight_layout()
fig.savefig(ROOT/'outputs/figures/phenology'/'phenology_gdd_by_season.png',dpi=160)
plt.close(fig)
manifest={'status':'satellite_GDD_preflight_only__NOT_AQUACROP_VALIDATED',
 'n_archived_dates':len(df),'growing_seasons':SEASONS,'counts':df.groupby('Season').size().to_dict(),
 'archive_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),
 'n_weather_rows':len(w),'ndvi_scaling':settings,
 'warning':'No Earth Engine re-extraction, RefET ETo or AquaCrop simulation performed.'}
(processed/'offline_preflight_manifest.json').write_text(json.dumps(manifest,indent=2))
print('OFFLINE PREFLIGHT PASSED: Archived Sentinel -> canopy smoothing -> phenology -> GDD')
print('Preliminary phenology (from archived 219-date source only):')
print(events[['Season','Budbreak_Date','Full_Budbreak_Date','Maximum_CC_Date','Senescence_Onset_Date','Early_Growth_Left_Censored_Flag']].to_string(index=False))
print('Satellite QA:',gaps[['Season','Maximum_Gap_Days']].to_string(index=False))
