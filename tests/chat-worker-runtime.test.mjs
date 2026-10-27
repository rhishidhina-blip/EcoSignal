import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {build} from 'esbuild';
import {Miniflare,Response} from 'miniflare';
const compiled=await build({stdin:{contents:"import {handleAsk} from './app/lib/assistant';export default {fetch:handleAsk};",resolveDir:process.cwd()},bundle:true,write:false,format:'esm',platform:'browser',target:'es2022'});
const image=(await readFile('tests/fixtures/chat-images/baseline.jpg')).toString('base64');
function runtime(outboundService){return new Miniflare({modules:true,compatibilityDate:'2026-05-15',compatibilityFlags:['nodejs_compat'],script:compiled.outputFiles[0].text,bindings:{ECOSIGNAL_CHATBOT_URL:'https://backend.example/assistant/ask'},outboundService});}
test('real Worker runtime forwards question-only and image chat with no unsupported redirect mode',async()=>{
 let calls=0;const mf=runtime(async req=>{calls++;assert.equal(req.url,'https://backend.example/assistant/ask');const body=await req.json(),ctx=body.observation_context;
 if(ctx){assert.equal(ctx.selection.image,true);assert.ok(ctx.image.data.length>0);assert.equal(ctx.location,undefined);}
 return Response.json({answer:'Synthetic fixture response',mode:'grounded_llm',sources:[],scan_evidence:[],...(ctx?{context_receipt:{version:'observation-context-v1',observation_id:ctx.observation_id,included:['image'],image_received:true}}:{})});});
 try{for(const withImage of [false,true]){
 const ctx=withImage?{observation_id:'SYNTHETIC-ONLY',selection:Object.fromEntries(['image','coverage','growth_form','satellite','geomorphology','elevation','location'].map(k=>[k,k==='image'])),image:{mime_type:'image/jpeg',data:image}}:null;
 const r=await mf.dispatchFetch('https://site.example/api/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:'Describe the supplied context.',observation_context:ctx})});assert.equal(r.status,200);assert.equal((await r.json()).mode,'grounded_llm');
 }assert.equal(calls,2);}finally{await mf.dispose();}
});
test('real Worker runtime never follows an unexpected backend redirect with observation data',async()=>{
 let calls=0;const mf=runtime(async req=>{calls++;return new Response(null,{status:307,headers:{Location:'https://other.example/private'}})});
 try{const r=await mf.dispatchFetch('https://site.example/api/ask',{method:'POST',body:JSON.stringify({question:'Test redirect rejection.'})});assert.equal(r.status,502);assert.equal((await r.json()).code,'CHAT_BACKEND_REDIRECT');assert.equal(calls,1);}finally{await mf.dispose();}
});
