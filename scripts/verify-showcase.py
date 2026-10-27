"""Read-only integrity checks; no model/notebook/provider execution."""
from pathlib import Path
import ast,hashlib,json,re,sys
root=Path(__file__).resolve().parents[1]
rows=json.loads((root/'docs/SHOWCASE_FILES.json').read_text(encoding='utf-8'))
errors=[]
for row in rows:
 p=root/row['path']
 if not p.resolve().is_relative_to(root.resolve()):errors.append('Unsafe path: '+row['path']);continue
 if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256']:errors.append('Missing/modified file: '+row['path'])
for p in root.rglob('*.py'):
 if '.git' not in p.parts:
  try:ast.parse(p.read_text(encoding='utf-8-sig'))
  except Exception as e:errors.append(str(p.relative_to(root))+': '+type(e).__name__)
for p in (root/'notebooks').rglob('*.ipynb'):
 try:
  n=json.loads(p.read_text(encoding='utf-8'));assert n.get('nbformat')==4 and isinstance(n['cells'],list)
 except Exception as e:errors.append(str(p.relative_to(root))+': '+type(e).__name__)
for p in [root/'README.md',root/'docs/FEATURES.md']:
 for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
  if link.startswith(('http:','https:','#')):continue
  if not (p.parent/link.split('#')[0]).exists():errors.append('Broken link in '+p.name+': '+link)
report={'passed':not errors,'manifest_files':len(rows),'errors':errors,'scope':'File hashes, Python syntax, notebook structure and feature documentation links; not a production build or field validation'}
print(json.dumps(report,indent=2));sys.exit(0 if not errors else 1)
