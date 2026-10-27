import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {gunzipSync} from 'node:zlib';
import ts from 'typescript';
const dataset=JSON.parse(await readFile(new URL('../app/lib/satellite-data.json',import.meta.url),'utf8'));
let source=await readFile(new URL('../app/lib/satellite.ts',import.meta.url),'utf8');
source=source.replace("import dataset from './satellite-data.json';",`const dataset=${JSON.stringify(dataset)};`).replace("import {project} from './map-geometry';",await readFile(new URL('../app/lib/map-geometry.ts',import.meta.url),'utf8'));
const compiled=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText;
const {rasterCell,numericValue,satelliteSummary,satelliteAsset}=await import('data:text/javascript;base64,'+Buffer.from(compiled).toString('base64'));
test('every index and period has a complete numeric grid with nodata preserved',async()=>{
 for(const index of ['NDVI','NDMI','BSI','MNDWI'])for(const period of ['baseline','comparison','change']){
  const asset=satelliteAsset(index,period);const buffer=gunzipSync(await readFile(new URL('../public'+asset.values,import.meta.url)));const values=new Int16Array(buffer.buffer,buffer.byteOffset,buffer.length/2);
  assert.equal(values.length,dataset.width*dataset.height);assert.equal([...values].filter(v=>v!==-32768).length,asset.valid_pixels);
  assert.equal(numericValue(new Int16Array([-32768,1234]),0),null);assert.equal(numericValue(new Int16Array([-32768,1234]),1),.1234);
  const png=await readFile(new URL('../public'+asset.image,import.meta.url));assert.equal(png.readUInt32BE(16),dataset.width);assert.equal(png.readUInt32BE(20),dataset.height);
 }
});
test('Raleigh cell lookup handles boundary and out-of-area locations',()=>{
 assert.notEqual(rasterCell(-78.644,35.809),null);assert.equal(rasterCell(-79.3,35.809),null);assert.equal(rasterCell(-78.644,36.4),null);
 const [west,south,east,north]=dataset.bounds;assert.equal(rasterCell(west,north),0);assert.equal(rasterCell(east,south),null);
});
test('change statistics use common-pixel differences rather than subtracting differently masked means',()=>{
 const change=satelliteSummary('NDVI','change');const a=satelliteSummary('NDVI','baseline');assert.equal(change.mean_change_on_common_pixels,-0.02313300864048227);assert.notEqual(change.mean-a.mean,change.mean_change_on_common_pixels);assert.ok(change.comparison_area_fraction<change.valid_area_fraction);
});
