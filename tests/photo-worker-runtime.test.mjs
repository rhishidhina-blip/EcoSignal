import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import ts from 'typescript';
import {Miniflare,Response} from 'miniflare';
test('real Workers runtime forwards an image with manual redirect handling and returns JSON',async()=>{
 const code=ts.transpileModule(await readFile('app/lib/photo-analysis-proxy.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText;
 let forwarded=false;
 const mf=new Miniflare({modules:true,compatibilityDate:'2026-05-22',script:code+'\nexport default {fetch:handlePhotoAnalysis};',bindings:{ECOSIGNAL_ANALYSIS_URL:'https://analysis.example',ECOSIGNAL_ANALYSIS_TOKEN:'synthetic-runtime-token'},outboundService:async req=>{forwarded=true;assert.equal(req.url,'https://analysis.example/analyze');assert.equal(req.headers.get('Authorization'),'Bearer synthetic-runtime-token');const image=(await req.formData()).get('image');assert.equal(await image.text(),'synthetic pixels');return Response.json({status:'completed',synthetic_fixture:true});}});
 try{const boundary='RuntimeSyntheticBoundary';const body='--'+boundary+'\r\nContent-Disposition: form-data; name="image"; filename="synthetic.png"\r\nContent-Type: image/png\r\n\r\nsynthetic pixels\r\n--'+boundary+'--\r\n';const r=await mf.dispatchFetch('https://site.example/api/analyze',{method:'POST',body,headers:{origin:'https://site.example','Content-Type':'multipart/form-data; boundary='+boundary}});assert.equal(r.status,200);assert.equal(forwarded,true);assert.equal((await r.json()).synthetic_fixture,true);}finally{await mf.dispose();}
});
