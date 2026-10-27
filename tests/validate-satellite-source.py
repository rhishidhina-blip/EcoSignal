"""Compare generated display grids to an extracted source archive. Run with archive path."""
import gzip,json,sys
from pathlib import Path
import numpy as np
import rasterio
from rasterio.merge import merge
from rasterio.warp import transform
root=Path(sys.argv[1]);out=Path(__file__).resolve().parents[1]/'public/satellite/raleigh'
d=json.load(open(out/'dataset.json'));m=json.load(open(root/'manifest.json'));checked=0;rng=np.random.default_rng(17)
for kind,week,period in [('weekly',d['weeks'][0],'baseline'),('weekly',d['weeks'][1],'comparison'),('change',d['weeks'][1],'change')]:
 ds=[rasterio.open(root/x['file']) for x in m['outputs'] if x['kind']==kind and x['week']==week];a,t=merge(ds,nodata=np.nan);crs=ds[0].crs
 for src in ds:src.close()
 west,south,east,north=d['bounds'];xm,ym=transform('EPSG:4326','EPSG:3857',[west,east],[south,north]);left,right=xm;bottom,top=ym
 for b,index in enumerate(m['indices']):
  values=np.frombuffer(gzip.open(out/f'{index.lower()}-{period}.bin.gz','rb').read(),dtype='<i2').reshape(d['height'],d['width'])
  rows=rng.integers(0,d['height'],300);cols=rng.integers(0,d['width'],300)
  xx=left+(cols+.5)*(right-left)/d['width'];yy=top-(rows+.5)*(top-bottom)/d['height'];sx,sy=transform('EPSG:3857',crs,xx,yy);rr,cc=rasterio.transform.rowcol(t,sx,sy)
  for r,c,sr,sc in zip(rows,cols,rr,cc):
   original=a[b,sr,sc] if 0<=sr<a.shape[1] and 0<=sc<a.shape[2] else np.nan;actual=values[r,c]
   assert (actual==-32768)==(not np.isfinite(original)),(index,period,r,c,'mask')
   if np.isfinite(original):assert abs(actual/10000-original)<=.000051,(index,period,r,c,actual,original)
   checked+=1
print('PASS:',checked,'point samples match source raster values and nodata after reprojection')
for change in [x for x in m['outputs'] if x['kind']=='change']:
 with rasterio.open(root/change['file']) as c,rasterio.open(root/'weekly'/d['weeks'][0]/(change['tile']+'.tif')) as a,rasterio.open(root/'weekly'/d['weeks'][1]/(change['tile']+'.tif')) as b:
  aa=a.read([1,2,3,4]);bb=b.read([1,2,3,4]);cc=c.read();valid=np.isfinite(aa)&np.isfinite(bb)
  assert np.array_equal(valid,np.isfinite(cc));np.testing.assert_allclose(cc[valid],(bb-aa)[valid],atol=1e-6)
print('PASS: all four changes equal comparison minus baseline on common clear pixels')
