import zipfile,hashlib,json,shutil,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];p=Path(sys.argv[1]);assert hashlib.sha256(p.read_bytes()).hexdigest()=='97ee60bae227ee6b3924b5dfd27d6426be946ad95437d6b76c3c17ed67bf8de9'
out=root/'public/unified/georisk';out.mkdir(parents=True,exist_ok=True);data=root/'app/data';data.mkdir(exist_ok=True);docs=root/'docs/unified/numeric-georisk';docs.mkdir(exist_ok=True);tests=root/'tests/fixtures';tests.mkdir(exist_ok=True)
with zipfile.ZipFile(p) as z:
 for n in z.namelist():
  assert '..' not in Path(n).parts and not n.startswith('/')
  dest=(tests/'georisk-sampling-fixtures.json') if n=='georisk-sampling-fixtures.json' else docs/n if n.startswith('reference/') or n=='INTEGRATION.md' else out/n
  dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(n))
 m=json.loads(z.read('georisk-numeric-manifest.json'));assert hashlib.sha256(z.read(m['binary_file'])).hexdigest()==m['binary_sha256'];assert len(z.read(m['binary_file']))==m['shape'][0]*m['shape'][1]*2
 for n in ['georisk-numeric-manifest.json','georisk-reference-cdf.json']: (data/n).write_bytes(z.read(n))
 provenance={'zip_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'files':{n:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist()},'valid_samples':m['valid_sample_count'],'terrain_fixtures_are_observations':False}
 (docs/'package-verification.json').write_text(json.dumps(provenance,indent=2)+'\n')
 print('Verified package and binary, installed numerical data; 24 terrain fixtures only under tests/')
