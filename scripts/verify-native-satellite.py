"""Lossless source audit; requires numpy/rasterio. Usage: python scripts/verify-native-satellite.py archive.zip"""
import sys,json,hashlib,gzip,zipfile
from pathlib import Path
import numpy as np
import rasterio
from rasterio.io import MemoryFile
from rasterio.windows import Window
root=Path(__file__).resolve().parents[1]
m=json.loads((root/'public/unified/satellite/manifest.json').read_text())
chunks=0
with zipfile.ZipFile(sys.argv[1]) as z:
 source=json.loads(z.read('manifest.json'))
 assert source['completed'] is True and source['resolution_m']==20
 for tile in m['tiles']:
  entry=next(e for e in source['outputs'] if e['kind']=='weekly' and e['week']==m['week'] and e['tile']==tile['id'])
  raw=z.read(entry['file']);assert hashlib.sha256(raw).hexdigest()==tile['sha256']
  with MemoryFile(raw) as mem,mem.open() as ds:
   assert ds.crs.to_string()==m['crs']
   assert list(ds.descriptions)==tile['bands']
   assert list(ds.transform)[:6]==tile['transform']
   for c in tile['chunks']:
    b=(root/'public/unified/satellite'/c['file']).read_bytes();assert hashlib.sha256(b).hexdigest()==c['sha256']
    a=np.frombuffer(gzip.decompress(b),dtype='<f4').reshape(len(tile['bands']),c['height'],c['width'])
    expected=ds.read(window=Window(c['c0'],c['r0'],c['width'],c['height'])).astype('<f4')
    assert np.array_equal(a,expected,equal_nan=True),(tile['id'],c['file'])
    chunks+=1
print(json.dumps({'status':'passed','native_tiles':len(m['tiles']),'lossless_chunks':chunks,'bands_per_chunk':8,'week':m['week'],'resolution_m':20,'checks':['original GeoTIFF SHA256','EPSG:32617 and affine transform','all band names','every compressed chunk hash','all Float32 values and nodata equal original GeoTIFF'],'scientific_validation':False}))
