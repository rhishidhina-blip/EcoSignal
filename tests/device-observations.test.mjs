import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import ts from 'typescript';
const code=ts.transpileModule(await readFile('app/lib/device-observations.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText;
const {resetDeviceObservations,visibleSyncedObservations,OBSERVATIONS_KEY,RESET_KEY,RESET_IDS_KEY}=await import('data:text/javascript;base64,'+Buffer.from(code).toString('base64'));
const storage=(data)=>({getItem:k=>data.get(k)??null,setItem:(k,v)=>data.set(k,v),removeItem:k=>data.delete(k)});
test('device reset clears records while preserving unrelated settings and hides sync writes already in flight',()=>{
 const data=new Map([[OBSERVATIONS_KEY,'[{"id":"old"}]'],['user-settings','keep']]);const cutoff=Date.parse('2026-10-25T20:00:00Z');resetDeviceObservations(storage(data),cutoff,['old']);
 assert.equal(data.has(OBSERVATIONS_KEY),false);assert.equal(data.get('user-settings'),'keep');
 const remote=[{id:'old',created_at:'2026-10-25T20:00:01Z'},{id:'older-server-copy',created_at:'2026-10-24T20:00:00Z'},{id:'new',created_at:'2026-10-25T20:01:00Z'}];
 assert.deepEqual(visibleSyncedObservations(remote,Number(data.get(RESET_KEY)),JSON.parse(data.get(RESET_IDS_KEY))).map(r=>r.id),['new']);
});
test('without a reset the normal synced list remains visible',()=>{const rows=[{id:'original'}];assert.deepEqual(visibleSyncedObservations(rows,0),rows)});
test('a storage failure does not report success or lose the old device records',()=>{const data=new Map([[OBSERVATIONS_KEY,'original']]);const s=storage(data);s.setItem=(k,v)=>{if(k===RESET_KEY)throw Error('quota');data.set(k,v)};assert.throws(()=>resetDeviceObservations(s,123,['old']),/quota/);assert.equal(data.get(OBSERVATIONS_KEY),'original');assert.equal(data.has(RESET_KEY),false)});
