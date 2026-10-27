"""Build a credential-free complete source/asset checkpoint; split for Site asset limits."""
import subprocess,zipfile,json,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'public/unified/source-backup';out.mkdir(parents=True,exist_ok=True)
paths=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=root).decode().split('\0')
paths=sorted(set(p for p in paths if p and (not p.startswith('public/unified/source-backup/') or p=='public/unified/source-backup/index.html') and not p.startswith('.git/') and not Path(p).name.startswith('.env') and not p.endswith('.pem') and p!='tsconfig.tsbuildinfo'))
archive=root.parent/'EcoSignal-full-source-checkpoint.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in paths:
  if (root/p).is_file():z.write(root/p,'EcoSignal/'+p)
 z.writestr('EcoSignal/CHECKPOINT_README.md','''# EcoSignal source checkpoint\n\nComplete application source, dependency locks, numerical data, satellite/terrain assets, original integration references and software tests. Snapshot includes the numerical GeoRisk, adaptive planner, evidence workflows and observation-image chat; published commit is reported separately by Sites. No node_modules, build output, Git credentials, environment secrets, browser-stored observations or live API responses are included. Tests/fixtures contain terrain sampling checks and synthetic fixtures, not observed lichen scans.\n\nRequires Node 22.13+ and the package dependencies listed in package.json. The original project uses Sites Vinext/Cloudflare Workers; read scripts/install-ci.sh and scripts/build-verified.sh for its build commands. The hosted backend environment is not backed up: configure ECOSIGNAL_CHATBOT_URL separately when deploying elsewhere. AirNow and imagery require network access. Hashes/source limitations remain documented under docs/unified. The numerical raw samples use 20 m spacing, not a complete 1 m output raster. No model retraining is required.\n''')
b=archive.read_bytes();parts=[];size=16*1024*1024
for i,start in enumerate(range(0,len(b),size)):
 name=f'source-checkpoint.part{i:02d}';part=b[start:start+size];(out/name).write_bytes(part);parts.append({'file':name,'size':len(part),'sha256':hashlib.sha256(part).hexdigest()})
manifest={'filename':'EcoSignal-full-source-checkpoint.zip','size':len(b),'sha256':hashlib.sha256(b).hexdigest(),'parts':parts,'snapshot':'Observation-image chat + existing environmental and evidence workflows; exact saved source commit is reported by Sites','excluded':['credentials','environment secrets','node_modules','build outputs','browser observation records','D1/R2 runtime data','executed notebook outputs']}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Full source ZIP bytes',len(b),'parts',len(parts),'SHA256',manifest['sha256'])
