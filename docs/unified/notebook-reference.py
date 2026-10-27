# Installation helper (does nothing if dependencies are already present)
import importlib.util, subprocess, sys
PACKAGES = {'numpy':'numpy','pandas':'pandas','rasterio':'rasterio','pyproj':'pyproj',
            'scipy':'scipy','sklearn':'scikit-learn','matplotlib':'matplotlib'}
missing = [p for m,p in PACKAGES.items() if importlib.util.find_spec(m) is None]
if missing: subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', *missing])
print('Dependencies ready.')

from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import zipfile, json, warnings, math, re
import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import Window
from pyproj import Transformer
from scipy.stats import spearmanr, pearsonr
import matplotlib.pyplot as plt

DATA_DIR = Path('/mnt/data') if Path('/mnt/data/satellite_results_preview_fixed.zip').exists() else Path.cwd()
SAT_ZIP = DATA_DIR / 'satellite_results_preview_fixed.zip'
REPEAT_CSV = DATA_DIR / 'repeat_scan_manifest.csv'
SITE_CSV = DATA_DIR / 'site_inputs.csv'
GEORISK_REF_CSV = DATA_DIR / 'georisk_reference.csv'
TRUTH_CSV = DATA_DIR / 'ground_truth.csv'
OUT = DATA_DIR / 'ecosignal_unified_outputs'
RASTER_DIR = OUT / 'satellite_rasters'
OUT.mkdir(parents=True, exist_ok=True)

# Fixed provisional architecture: do not claim these weights were learned or validated.
BASE_WEIGHTS = {'satellite':0.25,'aqi':0.25,'lichen_coverage':0.20,
                'growth_form':0.10,'geomorphology':0.20}
# At least 3 independently supplied domains and >=65% of nominal weight must be present.
MIN_DOMAINS = 3
MIN_AVAILABLE_WEIGHT = 0.65
SAT_PATCH_RADIUS_PIXELS = 1  # 3 x 3 patch about each WGS84 site; 20m raster source
N_WEIGHT_TRIALS = 1000
RANDOM_SEED = 20261012

assert abs(sum(BASE_WEIGHTS.values())-1) < 1e-10
print('Inputs:', DATA_DIR)
print('Output:', OUT)
print('Satellite ZIP exists:', SAT_ZIP.exists(), '| repeat manifest exists:', REPEAT_CSV.exists())

if not SAT_ZIP.exists():
    raise FileNotFoundError(f'Missing {SAT_ZIP}; upload satellite_results_preview_fixed.zip or change DATA_DIR.')
with zipfile.ZipFile(SAT_ZIP) as z:
    names = set(z.namelist())
    assert 'manifest.json' in names, 'Satellite ZIP missing manifest.json'
    sat_meta = json.loads(z.read('manifest.json'))
    assert sat_meta.get('completed') is True, 'Satellite data were not marked complete'
    assert {'NDVI','NDMI','BSI','MNDWI'}.issubset(set(sat_meta['indices']))
    weeks = sorted({e['week'] for e in sat_meta['outputs'] if e['kind']=='weekly'})
    LATEST_WEEK = weeks[-1]
    weekly_entries = sorted([e for e in sat_meta['outputs'] if e['kind']=='weekly' and e['week']==LATEST_WEEK],key=lambda e:e['tile'])
    # Only safe, named GeoTIFF members; protect against archive traversal.
    for entry in weekly_entries:
        member = entry['file']
        assert member in names and re.fullmatch(r'weekly/\d{4}-\d{2}-\d{2}/r\d+_c\d+\.tif',member), member
        dest = RASTER_DIR / member
        if not dest.exists() or dest.stat().st_size != z.getinfo(member).file_size:
            dest.parent.mkdir(parents=True, exist_ok=True)
            with z.open(member) as source, open(dest,'wb') as target:
                import shutil
                shutil.copyfileobj(source,target)
        entry['local_file'] = str(dest)
print('Satellite source:', sat_meta['source'], '| week:',LATEST_WEEK,
      '| resolution:',sat_meta['resolution_m'],'m | tiles:',len(weekly_entries))
print('Acquisitions:',', '.join(sat_meta['acquisition_dates']))
print('Manifest cautions:', *sat_meta.get('limitations',[]), sep='\n- ')

SITE_COLUMNS = ['site_id','latitude','longitude','aqi','aqi_observed_at',
  'coverage_percent','coverage_confidence','growth_form','growth_form_confidence',
  'georisk_percentile','georisk_raw','georisk_confidence','substrate_type']
if not SITE_CSV.exists():
    pd.DataFrame(columns=SITE_COLUMNS).to_csv(OUT/'site_inputs_TEMPLATE.csv',index=False)
if not GEORISK_REF_CSV.exists():
    pd.DataFrame(columns=['georisk_raw']).to_csv(OUT/'georisk_reference_TEMPLATE.csv',index=False)
if not TRUTH_CSV.exists():
    pd.DataFrame(columns=['site_id','target_concern_0_100','observed_at',
      'target_definition','independent_source']).to_csv(OUT/'ground_truth_TEMPLATE.csv',index=False)

def read_csv_optional(path):
    return pd.read_csv(path) if path.exists() and path.stat().st_size else pd.DataFrame()

def numeric(s): return pd.to_numeric(s,errors='coerce')

def ensure_cols(df, cols):
    df=df.copy()
    for c in cols:
        if c not in df: df[c]=np.nan
    return df

repeat = read_csv_optional(REPEAT_CSV)
if len(repeat):
    key='monitoring_site_id' if 'monitoring_site_id' in repeat else 'site_id'
    assert key in repeat.columns
    repeat=repeat.copy()
    repeat['site_id']=repeat[key].astype('string').str.strip()
    repeat['capture_sequence']=numeric(repeat.get('capture_sequence',pd.Series(index=repeat.index,dtype=float)))
    # Only the last user-confirmed same-site observation; reject unconfirmed joins.
    confirmed=repeat.get('site_id_confirmed',pd.Series(True,index=repeat.index)).astype(str).str.lower().isin(['true','1','yes'])
    repeat_latest=(repeat.loc[confirmed].sort_values('capture_sequence').drop_duplicates('site_id',keep='last'))
    repeat_latest=ensure_cols(repeat_latest,['latitude','longitude','coverage_percent','coverage_confidence','growth_form','growth_form_confidence','aqi','substrate_type'])
    repeat_latest=repeat_latest[['site_id','latitude','longitude','coverage_percent','coverage_confidence',
                  'growth_form','growth_form_confidence','aqi','substrate_type']]
else:
    repeat_latest=pd.DataFrame(columns=['site_id'])

manual=read_csv_optional(SITE_CSV)
if len(manual):
    if 'site_id' not in manual: raise ValueError('site_inputs.csv must include site_id')
    manual=ensure_cols(manual,SITE_COLUMNS)
    manual['site_id']=manual['site_id'].astype('string').str.strip()
    assert manual['site_id'].notna().all() and manual['site_id'].is_unique, 'Duplicate/blank site_id in site_inputs.csv'
    # Manually provided nonblank values override repeat scans; no sequential overwrite.
    sites=manual.set_index('site_id').combine_first(repeat_latest.set_index('site_id')).reset_index()
else:
    sites=ensure_cols(repeat_latest.copy(),SITE_COLUMNS)
    sites=sites[SITE_COLUMNS] if len(sites) else pd.DataFrame(columns=SITE_COLUMNS)

sites=ensure_cols(sites,SITE_COLUMNS)
for c in ['latitude','longitude','aqi','coverage_percent','coverage_confidence','growth_form_confidence',
          'georisk_percentile','georisk_raw','georisk_confidence']:
    sites[c]=numeric(sites[c])
for c,lo,hi in [('latitude',-90,90),('longitude',-180,180),('aqi',0,500),
                ('coverage_percent',0,100),('coverage_confidence',0,1),
                ('growth_form_confidence',0,1),('georisk_percentile',0,100),('georisk_confidence',0,1)]:
    bad=sites[c].notna() & ~sites[c].between(lo,hi)
    if bad.any():
        print('WARNING: dropping out-of-range',c,'for',sites.loc[bad,'site_id'].tolist())
        sites.loc[bad,c]=np.nan
sites['site_id']=sites['site_id'].astype(str)
assert sites['site_id'].is_unique
print('Loaded',len(sites),'unique sites; georeferenced:',int((sites.latitude.notna() & sites.longitude.notna()).sum()))
print('Data availability:', {k:int(sites[k].notna().sum()) for k in ['aqi','coverage_percent','growth_form','georisk_percentile','georisk_raw']})
display(sites.head(10))

reference=read_csv_optional(GEORISK_REF_CSV)
if 'georisk_raw' in reference:
    ref_values=np.sort(numeric(reference['georisk_raw']).dropna().to_numpy(float))
else: ref_values=np.array([],dtype=float)
if len(ref_values)>=100:
    mask=sites['georisk_percentile'].isna() & sites['georisk_raw'].notna()
    sites.loc[mask,'georisk_percentile']=100.0*np.searchsorted(ref_values,sites.loc[mask,'georisk_raw'].to_numpy(float),side='right')/len(ref_values)
    print('GeoRisk CDF reference count:',len(ref_values),'(fixed source cohort required)')
elif sites['georisk_raw'].notna().any() and sites['georisk_percentile'].isna().any():
    print('WARNING: raw GeoRisk scores will not be ranked: need >=100 representative reference values.')
assert sites['georisk_percentile'].dropna().between(0,100).all()

INDEX_BANDS={'NDVI':'NDVI_clear_count','NDMI':'NDMI_clear_count',
             'BSI':'BSI_clear_count','MNDWI':'MNDWI_clear_count'}

def sample_site_raster(ds,lat,lon,radius=1):
    if not np.isfinite(lat) or not np.isfinite(lon): return None
    x,y=Transformer.from_crs('EPSG:4326',ds.crs,always_xy=True).transform(float(lon),float(lat))
    if not (ds.bounds.left<=x<ds.bounds.right and ds.bounds.bottom<y<=ds.bounds.top): return None
    r,c=ds.index(x,y)
    if not (0<=r<ds.height and 0<=c<ds.width): return None
    r0=max(0,r-radius); r1=min(ds.height,r+radius+1)
    c0=max(0,c-radius); c1=min(ds.width,c+radius+1)
    a=ds.read(window=Window(c0,r0,c1-c0,r1-r0)).astype(float)
    band={name:i for i,name in enumerate(ds.descriptions)}
    result={}; counts=[]; valid_total=0
    for idx,clear in INDEX_BANDS.items():
        if idx not in band or clear not in band:
            raise ValueError(f'GeoTIFF missing {idx} / {clear}; found {ds.descriptions}')
        vals=a[band[idx]]; nclear=a[band[clear]]
        valid=np.isfinite(vals) & np.isfinite(nclear) & (nclear>=1) & (vals>=-1) & (vals<=1)
        result[idx.lower()]=float(np.median(vals[valid])) if np.any(valid) else np.nan
        result[idx.lower()+'_clear_count']=float(np.median(nclear[valid])) if np.any(valid) else 0
        counts.append(result[idx.lower()+'_clear_count'])
        valid_total+=int(valid.sum())
    result['sat_valid_pixels']=valid_total
    result['sat_observation_fraction']=float(np.clip(np.mean(counts)/3.0,0,1))
    return result

def sample_satellite(sites,entries):
    out={str(s):{'site_id':str(s)} for s in sites['site_id']}
    to_sample=sites.dropna(subset=['latitude','longitude'])
    for entry in entries:
        with rasterio.open(entry['local_file']) as ds:
            for row in to_sample.itertuples(index=False):
                site_id=str(row.site_id)
                sample=sample_site_raster(ds,row.latitude,row.longitude,SAT_PATCH_RADIUS_PIXELS)
                if sample is None: continue
                old=out[site_id]
                # Rank overlapping tiles on actual count of clear and valid pixels.
                if sample['sat_valid_pixels']>old.get('sat_valid_pixels',-1):
                    out[site_id].update(sample)
                    out[site_id]['sat_tile']=entry['tile']
                    out[site_id]['sat_week']=entry['week']
    return pd.DataFrame(out.values())

samples=sample_satellite(sites,weekly_entries) if len(sites) else pd.DataFrame(columns=['site_id'])
sites=sites.merge(samples,on='site_id',how='left',validate='one_to_one')
for c in ['ndvi','ndmi','bsi','mndwi','sat_observation_fraction']:
    if c not in sites:sites[c]=np.nan
print('Sites with sampled NDVI:',int(sites['ndvi'].notna().sum()),'of',len(sites))
display(sites[['site_id','latitude','longitude','ndvi','ndmi','bsi','mndwi','sat_observation_fraction']].head(10))

def clip01(x): return np.clip(x,0,1)
def anchor_score(x,lower,upper,invert=False):
    y=100*clip01((np.asarray(x,dtype=float)-lower)/(upper-lower))
    return 100-y if invert else y

# Optional switch: disable growth-form weighting if evidence for its heuristic is insufficient.
INCLUDE_GROWTH_FORM = True
GROWTH_FORM_MAP={'fruticose':20., 'foliose':45., 'crustose':65.}
GROWTH_SYNONYMS={'fruticose':'fruticose','foliose':'foliose','crustose':'crustose',
 'fruticose lichen':'fruticose','foliose lichen':'foliose','crustose lichen':'crustose'}

def compute_components(df):
    df=df.copy()
    for c in ['ndvi','ndmi','bsi','aqi','coverage_percent','georisk_percentile',
              'sat_observation_fraction','coverage_confidence','growth_form_confidence','georisk_confidence']:
        if c not in df:df[c]=np.nan
        df[c]=numeric(df[c])
    for c in ['ndvi','ndmi','bsi']:
        df.loc[~df[c].between(-1,1),c]=np.nan
    df['satellite']=0.45*anchor_score(df.ndvi,0.2,0.8,True) + \
                    0.35*anchor_score(df.ndmi,-0.2,0.5,True) + \
                    0.20*anchor_score(df.bsi,-0.3,0.3,False)
    df.loc[df[['ndvi','ndmi','bsi']].isna().any(axis=1),'satellite']=np.nan
    df['aqi']=df.aqi.where(df.aqi.between(0,500))
    df['aqi_component']=100*clip01(df.aqi/300)
    df['lichen_coverage']=(100-df.coverage_percent.where(df.coverage_percent.between(0,100)))
    forms=df.get('growth_form',pd.Series(np.nan,index=df.index)).astype('string').str.strip().str.lower()
    df['growth_form_component']=forms.map(GROWTH_SYNONYMS).map(GROWTH_FORM_MAP).astype(float) if INCLUDE_GROWTH_FORM else np.nan
    df['geomorphology']=df.georisk_percentile.where(df.georisk_percentile.between(0,100))
    # Keep component names and source raw names distinct.
    df=df.rename(columns={'aqi_component':'aqi_score','growth_form_component':'growth_form_score'})
    df['satellite_quality']=df.sat_observation_fraction.clip(0,1)
    df['aqi_quality']=np.where(df.aqi.notna(),0.6,np.nan) # Unverified provenance => moderate placeholder, NOT calibrated confidence.
    df['lichen_coverage_quality']=df.coverage_confidence.clip(0,1)
    df['growth_form_quality']=df.growth_form_confidence.clip(0,1)
    df['geomorphology_quality']=df.georisk_confidence.clip(0,1)
    return df

SCORE_COL={'satellite':'satellite','aqi':'aqi_score','lichen_coverage':'lichen_coverage',
           'growth_form':'growth_form_score','geomorphology':'geomorphology'}
QUALITY_COL={c:('satellite_quality' if c=='satellite' else 'aqi_quality' if c=='aqi' else c+'_quality') for c in BASE_WEIGHTS}

def apply_weights(df,weights=BASE_WEIGHTS):
    df=df.copy()
    assert set(weights)==set(BASE_WEIGHTS) and all(v>=0 for v in weights.values())
    w=np.array([weights[k] for k in SCORE_COL],float)
    assert w.sum()>0
    w=w/w.sum()
    raw=np.column_stack([numeric(df[SCORE_COL[k]]).to_numpy(float) for k in SCORE_COL])
    valid=np.isfinite(raw)
    denom=valid@w
    num=np.nansum(np.where(valid,raw,0)*w,axis=1)
    partial=np.divide(num,denom,out=np.full(len(df),np.nan),where=denom>0)
    count=valid.sum(axis=1)
    eligible=(count>=MIN_DOMAINS) & (denom>=MIN_AVAILABLE_WEIGHT-1e-10)
    df['available_domain_count']=count
    df['nominal_weight_coverage']=denom
    df['partial_score_0_100']=partial
    df['unified_concern_0_100']=np.where(eligible,partial,np.nan)
    df['score_status']=np.where(eligible & (count==len(w)),'complete',np.where(eligible,'qualified_partial','insufficient_data'))
    df['missing_components']=[';'.join([c for j,c in enumerate(SCORE_COL) if not row[j]]) for row in valid]
    q=np.column_stack([numeric(df[QUALITY_COL[k]]).to_numpy(float) for k in SCORE_COL])
    # Unknown quality does not quietly become high confidence; only known and present quality enters mean.
    qvalid=valid & np.isfinite(q)
    qden=qvalid@w
    quality=np.divide(np.nansum(np.where(qvalid,q,0)*w,axis=1),qden,
        out=np.full(len(df),np.nan),where=qden>0)
    df['input_quality_index_0_1']=quality
    df['quality_weight_coverage']=qden
    df['source_quality_status']=np.where(qden>=denom-1e-10,'quality_reported_for_all_inputs','some_input_quality_unknown')
    return df

scored=apply_weights(compute_components(sites))
assert scored['unified_concern_0_100'].dropna().between(0,100).all()
print('Score status counts:',scored.score_status.value_counts().to_dict())
show=['site_id','satellite','aqi_score','lichen_coverage','growth_form_score','geomorphology',
      'unified_concern_0_100','partial_score_0_100','score_status','missing_components']
display(scored[show].head(15))

def test_scoring():
    fixture=pd.DataFrame([dict(site_id='UNIT-1',ndvi=.8,ndmi=.5,bsi=-.3,aqi=0,coverage_percent=100,
         growth_form='fruticose',georisk_percentile=0,coverage_confidence=.9,
         growth_form_confidence=.9,georisk_confidence=.9,sat_observation_fraction=.7),
        dict(site_id='UNIT-2',ndvi=.2,ndmi=-.2,bsi=.3,aqi=300,coverage_percent=0,
         growth_form='crustose',georisk_percentile=100),
        dict(site_id='UNIT-3',ndvi=np.nan,ndmi=np.nan,bsi=np.nan,aqi=np.nan,
             coverage_percent=20,growth_form=np.nan,georisk_percentile=np.nan)])
    out=apply_weights(compute_components(fixture))
    assert np.isclose(out.loc[0,'satellite'],0)
    assert np.isclose(out.loc[1,'satellite'],100)
    assert np.isclose(out.loc[0,'aqi_score'],0)
    assert np.isclose(out.loc[1,'aqi_score'],100)
    assert out.loc[0,'unified_concern_0_100'] < out.loc[1,'unified_concern_0_100']
    assert out.loc[2,'score_status']=='insufficient_data'
    assert pd.isna(out.loc[2,'unified_concern_0_100'])
    # Each domain increased in isolation must not reduce score for identical missingness.
    assert out.loc[0,'available_domain_count']==5
    q=apply_weights(compute_components(fixture.assign(coverage_percent=[90,0,20])))
    assert q.loc[0,'unified_concern_0_100']>=out.loc[0,'unified_concern_0_100']
    # Missing AQI may be qualified partial but never mislabeled complete.
    without=fixture.copy();without.loc[0,'aqi']=np.nan
    z=apply_weights(compute_components(without))
    assert z.loc[0,'score_status']!='complete'
    return 9
n_checks=test_scoring()
print('PASS:',n_checks,'deterministic assertions; synthetic fixtures excluded from real outputs.')

availability=pd.DataFrame([{'component':k,'count':int(scored[SCORE_COL[k]].notna().sum()),
                  'fraction':float(scored[SCORE_COL[k]].notna().mean()) if len(scored) else 0,
                  'weight':BASE_WEIGHTS[k]} for k in SCORE_COL])
display(availability)
repeatability=[]
if len(repeat) and {'monitoring_site_id','coverage_percent','capture_sequence'}.issubset(repeat.columns):
    for sid,g in repeat.groupby('monitoring_site_id'):
        g=g.sort_values('capture_sequence')
        if len(g)>=2:
            a,b=g.iloc[0],g.iloc[-1]
            v1=pd.to_numeric(a['coverage_percent'],errors='coerce')
            v2=pd.to_numeric(b['coverage_percent'],errors='coerce')
            if np.isfinite(v1) and np.isfinite(v2):
                repeatability.append({'site_id':sid,'older_coverage_percent':v1,
                    'newer_coverage_percent':v2,'change_percentage_points':v2-v1,
                    'date_status':'unknown unless captured_at is filled'})
repeatability=pd.DataFrame(repeatability)
if len(repeatability): display(repeatability)

fig,axes=plt.subplots(1,2,figsize=(12,4))
availability.plot(x='component',y='fraction',kind='bar',ylim=(0,1),legend=False,
                  ax=axes[0],title='Measured component availability')
axes[0].set_ylabel('Share of sites');axes[0].tick_params(axis='x',rotation=40)
scored['score_status'].value_counts().plot(kind='bar',ax=axes[1],title='Publication status')
axes[1].tick_params(axis='x',rotation=30)
plt.tight_layout();plt.savefig(OUT/'data_completeness.png',dpi=160);plt.show()

def ranking_metrics(reference,candidate):
    a=np.asarray(reference,float);b=np.asarray(candidate,float)
    valid=np.isfinite(a)&np.isfinite(b)
    a=a[valid];b=b[valid]
    if len(a)<3: return {'n':len(a),'spearman_rho':np.nan,'mean_abs_change':np.nan,
                        'max_abs_change':np.nan,'top_decile_jaccard':np.nan}
    rho=spearmanr(a,b).statistic if np.std(a)>0 and np.std(b)>0 else np.nan
    k=max(1,int(math.ceil(.1*len(a))))
    ia=set(np.argsort(-a,kind='mergesort')[:k]);ib=set(np.argsort(-b,kind='mergesort')[:k])
    return {'n':len(a),'spearman_rho':float(rho),'mean_abs_change':float(np.mean(np.abs(a-b))),
      'max_abs_change':float(np.max(np.abs(a-b))),
      'top_decile_jaccard':len(ia&ib)/len(ia|ib)}

complete=scored.loc[scored.available_domain_count==5].copy()
ablation=[]
if len(complete)>=5:
    base=apply_weights(complete)['unified_concern_0_100'].to_numpy(float)
    for excluded in BASE_WEIGHTS:
        w={k:(0. if k==excluded else v) for k,v in BASE_WEIGHTS.items()}
        alt=apply_weights(complete,w)['unified_concern_0_100'].to_numpy(float)
        ablation.append({'excluded':excluded,**ranking_metrics(base,alt)})
    ablation=pd.DataFrame(ablation)
    display(ablation)
else:
    ablation=pd.DataFrame(columns=['excluded','n','spearman_rho','mean_abs_change',
                                   'max_abs_change','top_decile_jaccard'])
    print(f'NOT EVALUABLE: {len(complete)} complete-case sites; need >=5 for ablations.')
ablation.to_csv(OUT/'unified_score_ablation.csv',index=False)

rng=np.random.default_rng(RANDOM_SEED)
keys=list(BASE_WEIGHTS)
base_w=np.array(list(BASE_WEIGHTS.values()))
sens=[]; sampled_weights=[]
if len(complete)>=5:
    baseline=apply_weights(complete)['unified_concern_0_100'].to_numpy(float)
    for i in range(N_WEIGHT_TRIALS):
        perturbed=base_w*rng.uniform(.75,1.25,len(base_w))
        perturbed=perturbed/perturbed.sum()
        scenario={k:float(v) for k,v in zip(keys,perturbed)}
        alt=apply_weights(complete,scenario)['unified_concern_0_100'].to_numpy(float)
        metrics=ranking_metrics(baseline,alt)
        sens.append({'trial':i,**metrics})
        sampled_weights.append({'trial':i,**scenario})
    sensitivity=pd.DataFrame(sens);weight_scenarios=pd.DataFrame(sampled_weights)
    display(sensitivity[['spearman_rho','mean_abs_change','max_abs_change','top_decile_jaccard']].describe())
    fig,ax=plt.subplots(figsize=(7,4))
    ax.hist(sensitivity['spearman_rho'].dropna(),bins=25)
    ax.set(title='Rank robustness under ±25% weight perturbations',xlabel='Spearman rho',ylabel='Trials')
    plt.tight_layout();plt.savefig(OUT/'sensitivity_rho.png',dpi=160);plt.show()
else:
    sensitivity=pd.DataFrame(columns=['trial','n','spearman_rho','mean_abs_change','max_abs_change','top_decile_jaccard'])
    weight_scenarios=pd.DataFrame(columns=['trial']+keys)
    print('NOT EVALUABLE: insufficient complete-case observations; no real sensitivity claims.')
sensitivity.to_csv(OUT/'unified_score_sensitivity.csv',index=False)
weight_scenarios.to_csv(OUT/'weight_scenarios.csv',index=False)

aggregation=[]
if len(complete)>=5:
    A=np.column_stack([complete[SCORE_COL[k]].to_numpy(float) for k in keys])
    arithmetic=A@base_w
    geometric=np.exp(np.log(1+A)@base_w)-1
    # Alternate AQI curve changes its mapping within 0..100 while retaining monotonicity.
    a_alt=A.copy();aqi_idx=keys.index('aqi')
    a_alt[:,aqi_idx]=100*np.sqrt(np.clip(a_alt[:,aqi_idx]/100,0,1))
    alternate_aqi=a_alt@base_w
    for name,arr in [('geometric_offset_1',geometric),('aqi_sqrt_transform',alternate_aqi)]:
        aggregation.append({'scenario':name,**ranking_metrics(arithmetic,arr)})
    aggregation=pd.DataFrame(aggregation);display(aggregation)
else:
    aggregation=pd.DataFrame(columns=['scenario','n','spearman_rho','mean_abs_change','max_abs_change','top_decile_jaccard'])
    print('NOT EVALUABLE: not enough complete cases to compare aggregation methods.')
aggregation.to_csv(OUT/'aggregation_robustness.csv',index=False)

truth=read_csv_optional(TRUTH_CSV)
independent_validation={'status':'not_run','reason':'No independent, appropriately defined ground_truth.csv supplied'}
spatial_blocks=pd.DataFrame(columns=['block_id','n','spearman_rho','mae'])
if len(truth):
    required={'site_id','target_concern_0_100','target_definition','independent_source'}
    if not required.issubset(truth.columns):
        independent_validation={'status':'not_run','reason':f'Ground truth missing required columns {sorted(required-set(truth.columns))}'}
    elif truth['site_id'].duplicated().any():
        independent_validation={'status':'not_run','reason':'Ground truth contains duplicate site_id; aggregate independent observations first'}
    else:
        truth=truth.copy();truth['site_id']=truth.site_id.astype(str)
        truth['target_concern_0_100']=numeric(truth.target_concern_0_100)
        truth=truth.loc[truth.target_concern_0_100.between(0,100)]
        joined=scored.merge(truth,on='site_id',how='inner',validate='one_to_one')
        joined=joined.dropna(subset=['unified_concern_0_100','target_concern_0_100','latitude','longitude'])
        joined=joined.loc[joined['target_definition'].notna() & joined['independent_source'].notna()].copy()
        if len(joined)>=20:
            joined['block_lat']=np.floor(joined.latitude/0.05).astype(int)
            joined['block_lon']=np.floor(joined.longitude/0.05).astype(int)
            joined['block_id']=joined.block_lat.astype(str)+'_'+joined.block_lon.astype(str)
            if joined.block_id.nunique()>=3:
                pred=joined.unified_concern_0_100.to_numpy(float)
                actual=joined.target_concern_0_100.to_numpy(float)
                rho=float(spearmanr(pred,actual).statistic) if np.std(actual)>0 and np.std(pred)>0 else np.nan
                independent_validation={'status':'descriptive_evaluation_complete',
                      'n':int(len(joined)),'spatial_blocks':int(joined.block_id.nunique()),
                      'spearman_rho':rho,'mae_same_construct_only':float(np.mean(abs(pred-actual))),
                      'target_definitions':joined.target_definition.dropna().unique().tolist(),
                      'sources':joined.independent_source.dropna().unique().tolist(),
                      'warning':'Independence, target validity, temporal alignment, and sampling bias require manual review.'}
                blocks=[]
                for bid,g in joined.groupby('block_id'):
                    if len(g)>=3:
                        a=g.unified_concern_0_100.to_numpy(float);b=g.target_concern_0_100.to_numpy(float)
                        rho_b=float(spearmanr(a,b).statistic) if np.std(a)>0 and np.std(b)>0 else np.nan
                    else:rho_b=np.nan
                    blocks.append({'block_id':bid,'n':len(g),'spearman_rho':rho_b,
                                   'mae':float(np.mean(abs(g.unified_concern_0_100-g.target_concern_0_100)))})
                spatial_blocks=pd.DataFrame(blocks)
            else: independent_validation={'status':'not_run','reason':'<3 distinct 0.05-degree geographic blocks'}
        else:independent_validation={'status':'not_run','reason':f'Only {len(joined)} matching, georeferenced score/independent-outcome pairs; require >=20'}
print('Independent validation:',independent_validation)
spatial_blocks.to_csv(OUT/'spatial_block_validation.csv',index=False)

scored.to_csv(OUT/'unified_site_scores.csv',index=False)
availability.to_csv(OUT/'component_availability.csv',index=False)
repeatability.to_csv(OUT/'repeat_scan_stability.csv',index=False)

LIMITATIONS=[
 'Unified score is a provisional multi-domain composite, not calibrated environmental risk or probability.',
 'Fixed component weights and anchors are hypotheses requiring external justification and local calibration.',
 'Growth-form ranking is a simplified exploratory ecological heuristic, not a universal pollution sensitivity ordering.',
 'Lichen coverage and growth-form outputs cannot be assumed independent; image models may share measurement errors.',
 'GeoRisk percentiles are relative uncalibrated susceptibility rankings, not erosion probabilities or predicted depths.',
 'Sentinel-2 vegetation/moisture/bare-soil proxies vary with land cover, water, agriculture, clouds, and season.',
 'AQI station/interpolated values may not represent individual lichen sites or satellite pixels.',
 'A low lichen coverage percentage is not independently proof of air contamination.',
 'Unobserved input quality is not imputed as high confidence.',
 'Remote-sensing, lichen, AQI and terrain observations can span different dates and spatial resolutions.',
 'Spatial autocorrelation and temporally repeated observations must not be mistaken for independent sample size.',
 'Ablation and weight sensitivity quantify robustness, not predictive accuracy or optimal weights.',
 'A true composite outcome must be defined and independently measured before external validity can be claimed.'
]
def safe_json(v):
    if isinstance(v,(np.integer,)):return int(v)
    if isinstance(v,(np.floating,)):return float(v) if np.isfinite(v) else None
    if isinstance(v,(np.ndarray,)):return v.tolist()
    if isinstance(v,(pd.Timestamp,datetime)):return v.isoformat()
    if pd.isna(v) if np.isscalar(v) else False:return None
    return v
metrics={
  'generated_utc':datetime.now(timezone.utc).isoformat(),
  'model_version':'EcoSignal-Unified-Provisional-v1',
  'score_direction':'0 lower concern, 100 higher relative concern',
  'weights':BASE_WEIGHTS,
  'normalization':{'satellite':{'ndvi':'100*(1-clip((NDVI-0.2)/0.6))',
               'ndmi':'100*(1-clip((NDMI+0.2)/0.7))','bsi':'100*clip((BSI+0.3)/0.6)',
               'inner_weights':{'ndvi':0.45,'ndmi':0.35,'bsi':0.20}},
              'aqi':'100*clip(AQI/300,0,1)','lichen_coverage':'100 - coverage_percent',
              'growth_form':GROWTH_FORM_MAP if INCLUDE_GROWTH_FORM else 'disabled',
              'geomorphology':'fixed-AOI reference percentile, not probability'},
  'minimum_components':MIN_DOMAINS,'minimum_nominal_weight':MIN_AVAILABLE_WEIGHT,
  'satellite_week':LATEST_WEEK,'satellite_source_manifest':sat_meta,
  'total_sites':len(scored),'site_score_status':scored.score_status.value_counts().to_dict(),
  'complete_case_n':len(complete),'component_counts':availability.set_index('component')['count'].to_dict(),
  'ablation_status':'completed' if len(ablation) else 'insufficient complete-case sites',
  'weight_sensitivity_status':'completed' if len(sensitivity) else 'insufficient complete-case sites',
  'independent_validation':independent_validation,
  'unit_tests_passed':n_checks,
  'limitations':LIMITATIONS
}
with open(OUT/'unified_score_validation.json','w') as f:
    json.dump(metrics,f,indent=2,default=safe_json,allow_nan=False)
with open(OUT/'unified_score_methodology.md','w') as f:
    f.write('# EcoSignal Unified Environmental Indicator — Provisional v1\n\n')
    f.write('**Interpretation:** 0–100 relative multi-domain environmental concern. Not a probability.\n\n')
    f.write('## Weighting and transformations\n\n```json\n'+json.dumps(metrics['normalization'],indent=2)+'\n```\n\n')
    f.write('Weights: '+json.dumps(BASE_WEIGHTS)+'\n\n')
    f.write('Component availability threshold: >=3 sources and >=65% of original weight.\n\n')
    f.write('## Validation availability\n\n'+json.dumps(independent_validation,indent=2)+'\n\n')
    f.write('## Limitations\n\n'+'\n'.join('- '+v for v in LIMITATIONS)+'\n')
print('Saved artifacts:')
for p in sorted(OUT.iterdir()):
    if p.is_file():print(' •',p.name,round(p.stat().st_size/1024,1),'KiB')