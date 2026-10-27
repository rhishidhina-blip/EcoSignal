"""Lossless native-grid numeric chunks; never derives values from display colors."""
import zipfile,json,gzip,hashlib,sys
from pathlib import Path
import rasterio,numpy as np
from rasterio.windows import Window
root=Path(__file__).resolve().parents[1]; out=root/'public/unified/satellite';out.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(sys.argv[1]) as z:
 m=json.loads(z.read('manifest.json')); assert m['completed']; week=max(e['week'] for e in m['outputs'] if e['kind']=='weekly'); tiles=[]
 for e in m['outputs']:
  if e['kind']!='weekly' or e['week']!=week:continue
  raw=z.read(e['file']);assert '..' not in e['file'];p=out/'temp.tif';p.write_bytes(raw)
  with rasterio.open(p) as d:
   assert str(d.crs)=='EPSG:32617'; names=list(d.descriptions); assert all(s in names for s in ['NDVI','NDMI','BSI','MNDWI','NDVI_clear_count','NDMI_clear_count','BSI_clear_count','MNDWI_clear_count'])
   t={'id':e['tile'],'width':d.width,'height':d.height,'transform':list(d.transform)[:6],'bands':names,'sha256':hashlib.sha256(raw).hexdigest(),'chunks':[]}
   for r in range(0,d.height,128):
    for c in range(0,d.width,128):
     r0=max(0,r-1);c0=max(0,c-1);r1=min(d.height,r+129);c1=min(d.width,c+129)
     a=d.read(window=Window(c0,r0,c1-c0,r1-r0),masked=True).astype('float32').filled(np.nan).astype('<f4');name=f"{e['tile']}-{r}-{c}.bin.gz"
     data=gzip.compress(a.tobytes(),compresslevel=6,mtime=0);(out/name).write_bytes(data)
     t['chunks'].append({'row':r,'col':c,'r0':r0,'c0':c0,'width':c1-c0,'height':r1-r0,'file':name,'sha256':hashlib.sha256(data).hexdigest()})
   tiles.append(t)
 p.unlink()
 meta={'version':'sentinel-native-2026-09-28-v1','week':week,'source':m['source'],'source_manifest':m,'crs':'EPSG:32617','resolution_m':20,'chunk_size':128,'sampling':'Median of valid native 3×3 pixels (~60 m), clipped at tile edges; clear-count >=1; best overlapping tile by valid pixels. No 1 km aggregation.','tiles':tiles}
 (out/'manifest.json').write_text(json.dumps(meta,separators=(',',':')))
 print('Native chunks',sum(len(t['chunks']) for t in tiles),'bytes',sum(p.stat().st_size for p in out.glob('*.gz')))
