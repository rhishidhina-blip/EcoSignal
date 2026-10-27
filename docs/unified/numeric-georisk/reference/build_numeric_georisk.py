"""Export real sampled GeoRisk scores using original 1m feature code and frozen weights."""
import sys, json, hashlib, time, math
from pathlib import Path
sys.path[:0]=['work/georisk-inference-deps','work/python-deps','work/diagnostic-deps']
import numpy as np
import rasterio
import xgboost as xgb
from pyproj import CRS, Transformer

ROOT=Path('work/verified-package')
OUT=Path('work/numeric-georisk'); OUT.mkdir(exist_ok=True)
HALO=48
STEP=20
nb=json.loads((ROOT/'EcoSignal_GeoRisk_V2_1m_Runtime.ipynb').read_text(encoding='utf-8'))
feature_source=next(''.join(c['source']) for c in nb['cells'] if 'def build_terrain_features' in ''.join(c['source']))
exec(compile(feature_source,'original_georisk_feature_cell','exec'))
meta=json.loads((ROOT/'ecosignal_georisk_v2_1m_metadata.json').read_text())
assert FEATURE_NAMES==meta['feature_order']
tiles=json.loads((ROOT/'tile_manifest.json').read_text())
R0,R1=tiles['crop_rows']; C0,C1=tiles['crop_cols']
grid_rows=np.arange(R0+STEP//2,R1,STEP,dtype=np.int64)
grid_cols=np.arange(C0+STEP//2,C1,STEP,dtype=np.int64)
shape=(len(grid_rows),len(grid_cols))

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()

validation=json.loads((ROOT/'aligned_dem_validation.json').read_text())
source_hashes={}
for y in [2015,2022,2024]:
    p=Path(f'C:/Users/dhina/Downloads/Dem_{y}_aligned.tif')
    record=next(a for a in validation['rasters'] if a['year']==y)
    assert p.stat().st_size==record['bytes']
    source_hashes[str(y)]=sha(p)
    assert source_hashes[str(y)]==record['sha256'],f'DEM {y} hash mismatch'
    print('Verified source',y,flush=True)

model=xgb.Booster(); model.load_model('work/georisk-model-portable.ubj'); model.set_param({'nthread':2})
assert model.num_features()==21 and model.num_boosted_rounds()==250
# Independent tree traversal verifies the portable model's inference implementation.
tree_doc=json.loads(Path('work/georisk-model-portable.json').read_text())
tree_list=tree_doc['learner']['gradient_booster']['model']['trees']
rng=np.random.default_rng(20261012)
X=rng.normal(0,2,(64,21)).astype('float32'); X[:,0]=rng.uniform(10,150,64)
margins=[]
for row in X:
    total=0.0
    for tree in tree_list:
        j=0
        while tree['left_children'][j]!=-1:
            f=tree['split_indices'][j]
            j=tree['left_children'][j] if row[f]<tree['split_conditions'][j] else tree['right_children'][j]
        total+=tree['split_conditions'][j]
    margins.append(total)
manual=1/(1+np.exp(-np.asarray(margins)))
native=model.predict(xgb.DMatrix(X))
max_parity_error=float(np.max(np.abs(manual-native)))
assert max_parity_error<1e-6, max_parity_error
print('Portable model parity passed',max_parity_error,flush=True)

signature=hashlib.sha256(json.dumps({'sources':source_hashes,'model':sha(ROOT/'ecosignal_georisk_v2_1m.joblib'),'feature_code':hashlib.sha256(feature_source.encode()).hexdigest(),'step':STEP},sort_keys=True).encode()).hexdigest()
bin_path=OUT/'georisk-2024-samples.u16'
checkpoint_path=OUT/'inference-checkpoint.json'
checkpoint=json.loads(checkpoint_path.read_text()) if checkpoint_path.exists() else {}
resume=checkpoint.get('signature')==signature and bin_path.exists() and bin_path.stat().st_size==math.prod(shape)*2
grid=np.memmap(bin_path,dtype='<u2',mode='r+' if resume else 'w+',shape=shape)
if not resume:grid[:]=65535; grid.flush(); checkpoint={}
start=int(checkpoint.get('next_tile',0))
started=time.time()
with rasterio.open('C:/Users/dhina/Downloads/Dem_2015_aligned.tif') as d15, rasterio.open('C:/Users/dhina/Downloads/Dem_2022_aligned.tif') as d22, rasterio.open('C:/Users/dhina/Downloads/Dem_2024_aligned.tif') as d24:
    assert d15.shape==d22.shape==d24.shape==(38511,39068)
    assert d15.transform==d22.transform==d24.transform
    assert d15.crs==d22.crs==d24.crs==CRS.from_epsg(32119)
    source_transform=d24.transform
    all_tiles=tiles['overlap_tiles']
    for i in range(start,len(all_tiles)):
        r,c,h,w=all_tiles[i]; win=Window(c,r,w,h)
        ir=np.flatnonzero((grid_rows>=r)&(grid_rows<r+h))
        ic=np.flatnonzero((grid_cols>=c)&(grid_cols<c+w))
        if len(ir) and len(ic):
            rr=grid_rows[ir]-r; cc=grid_cols[ic]-c
            source24=read_with_halo(d24,win)
            valid=valid_feature_mask(source24,win)
            valid &= np.isfinite(read_core(d15,win)) & np.isfinite(read_core(d22,win)) & np.isfinite(read_core(d24,win))
            selection=valid[np.ix_(rr,cc)]
            if selection.any():
                features=build_terrain_features(source24,win)[np.ix_(rr,cc)]
                selection &= np.isfinite(features).all(axis=-1)
                values=np.full(selection.shape,65535,dtype=np.uint16)
                if selection.any():
                    scores=model.predict(xgb.DMatrix(features[selection]))
                    assert np.isfinite(scores).all() and ((scores>=0)&(scores<=1)).all()
                    values[selection]=np.rint(scores*10000).astype(np.uint16)
                grid[np.ix_(ir,ic)]=values
        if (i+1)%25==0 or i+1==len(all_tiles):
            grid.flush()
            state={'signature':signature,'next_tile':i+1,'total_tiles':len(all_tiles),'shape':shape,'elapsed_seconds':round(time.time()-started,1)}
            pending=checkpoint_path.with_suffix('.pending.json'); pending.write_text(json.dumps(state)); pending.replace(checkpoint_path)
            print('INFERENCE_PROGRESS',json.dumps(state),flush=True)

valid=grid!=65535
count=int(valid.sum()); assert count>10000
hist=np.bincount(np.asarray(grid[valid],dtype=np.int64),minlength=10001)
cum=np.cumsum(hist)/count*100
to_wgs=Transformer.from_crs(32119,4326,always_xy=True)
left=source_transform.c+C0; top=source_transform.f-R0
right=source_transform.c+C1; bottom=source_transform.f-R1
corners=[to_wgs.transform(x,y) for x,y in [(left,bottom),(left,top),(right,bottom),(right,top)]]
manifest={'version':'georisk-2024-native-features-20m-sampling-v1','source_year':2024,'source_model':'EcoSignal GeoRisk V2','model_sha256':sha(ROOT/'ecosignal_georisk_v2_1m.joblib'),'portable_model_sha256':sha(Path('work/georisk-model-portable.ubj')),'source_dem_sha256':source_hashes,'feature_implementation_version':meta['feature_implementation_version'],'feature_code_sha256':hashlib.sha256(feature_source.encode()).hexdigest(),'binary_file':bin_path.name,'binary_sha256':sha(bin_path),'dtype':'uint16-little-endian','nodata':65535,'score_divisor':10000,'quantization_max_error':0.00005,'shape':list(shape),'crs':'EPSG:32119','proj4':CRS.from_epsg(32119).to_proj4(),'sample_spacing_m':STEP,'first_sample_center_xy':[source_transform.c+float(grid_cols[0])+.5,source_transform.f-float(grid_rows[0])-.5],'row_direction':'south','column_direction':'east','bounds_wgs84':[min(a[0] for a in corners),min(a[1] for a in corners),max(a[0] for a in corners),max(a[1] for a in corners)],'valid_sample_count':count,'reference':'fixed full common-coverage regular 20m sampling cohort; not the full 1m pixel distribution','cdf_file':'georisk-reference-cdf.json','model_portability_parity_max_abs_error':max_parity_error,'limitations':['Scores are relative uncalibrated terrain-lowering susceptibility, not probabilities.','Numerical samples spaced 20m; native features computed at 1m from original implementation.','Nearest sample is a nearby measured-feature location, not an area mean or exact arbitrary-point prediction.','Missing samples remain nodata; do not fill data boundaries.','Fixed CDF is representative systematic sampling of common survey coverage; percentiles are relative to this declared cohort.','Survey vertical reference remains provisional.']}
(OUT/'georisk-reference-cdf.json').write_text(json.dumps({'version':manifest['version'],'sample_count':count,'score_divisor':10000,'cdf_percent':np.round(cum,8).tolist()},separators=(',',':')))
(OUT/'georisk-numeric-manifest.json').write_text(json.dumps(manifest,indent=2))
print('NUMERIC_GEORISK_COMPLETE',json.dumps({'valid_samples':count,'binary_bytes':bin_path.stat().st_size,'parity_error':max_parity_error}),flush=True)
