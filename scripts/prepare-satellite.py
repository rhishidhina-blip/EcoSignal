"""Build georeferenced display assets and numeric grids from the supplied Sentinel-2 export.
Usage: python scripts/prepare-satellite.py /path/to/extracted/archive
The original manifest and summary remain authoritative; nodata is never interpolated.
"""
import csv, gzip, json, sys, shutil, hashlib
from pathlib import Path
import numpy as np
import rasterio
from rasterio.merge import merge
from rasterio.warp import reproject, transform_bounds, transform, Resampling
from rasterio.transform import from_origin
from PIL import Image
from pyproj import Transformer
root=Path(sys.argv[1]); out=Path(__file__).resolve().parents[1]/'public/satellite/raleigh'; out.mkdir(parents=True,exist_ok=True)
manifest=json.loads((root/'manifest.json').read_text())
indices=manifest['indices']; weeks=sorted({x['week'] for x in manifest['outputs'] if x['kind']=='weekly'})
assert indices==['NDVI','NDMI','BSI','MNDWI'] and len(weeks)==2
palettes={'NDVI':['#88493b','#cfaa59','#e0d985','#75b977','#17845b'], 'NDMI':['#b97b42','#d9c68a','#c3e3d9','#60bcb8','#28719d'], 'BSI':['#247784','#74ac9a','#cbd6a6','#d4a369','#a65337'], 'MNDWI':['#9d764e','#c8b082','#b7d8c7','#6cbfcf','#287dab']}
labels={'NDVI':('Vegetation','Vegetation greenness'), 'NDMI':('Moisture','Vegetation moisture indicator'), 'BSI':('Bare soil','Exposed-ground indicator'), 'MNDWI':('Water','Surface-water indicator')}
summary=list(csv.DictReader((root/'weekly_summary.csv').open()))
for r in summary:
 for k in list(r):
  if k not in ['week','index']: r[k]=float(r[k]) if r[k] else None
# Use the full mosaic's actual spatial footprint, rather than tile bounding boxes.
inputs=[rasterio.open(root/x['file']) for x in manifest['outputs'] if x['kind']=='weekly' and x['week']==weeks[0]]
a, t=merge(inputs,nodata=np.nan); src_crs=inputs[0].crs
left,top=t.c,t.f; right=left+a.shape[2]*t.a; bottom=top+a.shape[1]*t.e
for d in inputs:d.close()
west,south,east,north=transform_bounds(src_crs,'EPSG:3857',left,bottom,right,top,densify_pts=40)
res=25.; west=np.floor(west/res)*res; north=np.ceil(north/res)*res
width=int(np.ceil((east-west)/res)); height=int(np.ceil((north-south)/res)); east=west+width*res; south=north-height*res
dst_t=from_origin(west,north,res,res)
lon,lat=transform('EPSG:3857','EPSG:4326',[west,east],[south,north])
meta={'source':manifest['source'],'source_resolution_m':manifest['resolution_m'],'display_crs':'EPSG:3857','display_pixel_size_m':res,'width':width,'height':height,'bounds':[lon[0],lat[0],lon[1],lat[1]],'weeks':weeks,'acquisition_dates':manifest['acquisition_dates'],'limitations':manifest['limitations'],'summary':summary,'layers':{},'assets':{},'numeric_scale':10000,'numeric_nodata':-32768,'numeric_precision':0.00005,'quantization_note':'Nearest source pixel, rounded to 0.0001 index units; no-data remains missing.'}
for kind,week,period in [('weekly',weeks[0],'baseline'),('weekly',weeks[1],'comparison'),('change',weeks[1],'change')]:
 records=[x for x in manifest['outputs'] if x['kind']==kind and x['week']==week]
 datasets=[rasterio.open(root/x['file']) for x in records]
 data,src_t=merge(datasets,nodata=np.nan)
 for d in datasets:d.close()
 for b,index in enumerate(indices):
  target=np.full((height,width),np.nan,dtype='float32')
  if b==0:
   xx,yy=np.meshgrid(west+(np.arange(width)+.5)*res,north-(np.arange(height)+.5)*res)
   sx,sy=Transformer.from_crs('EPSG:3857',src_crs,always_xy=True).transform(xx,yy)
   col=np.floor((sx-src_t.c)/src_t.a).astype(int); row=np.floor((sy-src_t.f)/src_t.e).astype(int)
   inside=(row>=0)&(col>=0)&(row<data.shape[1])&(col<data.shape[2])
  target[inside]=data[b,row[inside],col[inside]]
  valid=np.isfinite(target)
  lo,hi=(-.25,.25) if period=='change' else (-1.,1.)
  colors=['#d7624d','#f1b878','#ecede4','#89c6bf','#34899c'] if period=='change' else palettes[index]
  rgb=np.array([[int(c[i:i+2],16) for i in [1,3,5]] for c in colors])
  x=np.clip((np.nan_to_num(target)-lo)/(hi-lo),0,1)*(len(colors)-1)
  ii=np.minimum(np.floor(x).astype(int),len(colors)-2); fraction=x-ii
  rgba=np.zeros((height,width,4),dtype=np.uint8); rgba[:,:,:3]=np.round(rgb[ii]*(1-fraction[:,:,None])+rgb[ii+1]*fraction[:,:,None]); rgba[:,:,3]=valid*255
  name=f'{index.lower()}-{period}'; Image.fromarray(rgba).save(out/f'{name}.png',optimize=True)
  values=np.full(target.shape,-32768,dtype='<i2'); values[valid]=np.round(target[valid]*10000).astype('<i2')
  with gzip.open(out/f'{name}.bin.gz','wb',compresslevel=9) as f:f.write(values.tobytes())
  asset={'image':f'/satellite/raleigh/{name}.png','values':f'/satellite/raleigh/{name}.bin.gz','valid_pixels':int(valid.sum()),'min':float(target[valid].min()),'max':float(target[valid].max())}
  if kind=='weekly':
   count=np.zeros((height,width),dtype='uint8')
   count[inside]=np.nan_to_num(data[b+4,row[inside],col[inside]]).astype('uint8')
   count[~valid]=0
   with gzip.open(out/f'{name}-count.bin.gz','wb',compresslevel=9) as f:f.write(count.tobytes())
   asset['counts']=f'/satellite/raleigh/{name}-count.bin.gz'
  meta['assets'][name]=asset
for i in indices:meta['layers'][i]={'name':labels[i][0],'description':labels[i][1],'colors':palettes[i]}
for name in ['manifest.json','catalog.json','study_area.geojson','weekly_summary.csv']:shutil.copyfile(root/name,out/name)
meta['source_files']=[{'file':x['file'],'sha256':hashlib.sha256((root/x['file']).read_bytes()).hexdigest()} for x in manifest['outputs']]
(out/'dataset.json').write_text(json.dumps(meta,indent=2))
(Path(__file__).resolve().parents[1]/'app/lib/satellite-data.json').write_text(json.dumps(meta,indent=2))
print(json.dumps({'size':[width,height],'bounds':meta['bounds'],'assets':len(meta['assets']),'bytes':sum(p.stat().st_size for p in out.iterdir())}))
