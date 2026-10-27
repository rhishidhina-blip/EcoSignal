import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import ts from 'typescript';
import jpeg from 'jpeg-js';
const moduleUrl=async(path,replacements={})=>{let s=await readFile(new URL(path,import.meta.url),'utf8');for(const[a,b]of Object.entries(replacements))s=s.replaceAll(a,b);return 'data:text/javascript;base64,'+Buffer.from(ts.transpileModule(s,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText).toString('base64')};
const ctxUrl=await moduleUrl('../app/lib/observation-context.ts',{'./observation-image':await moduleUrl('../app/lib/observation-image.ts'),'./vendor/jpeg-encoder':await moduleUrl('../app/lib/vendor/jpeg-encoder.ts'),'jpeg-js':new URL('../node_modules/jpeg-js/index.js',import.meta.url).href});
const C=await import(ctxUrl);
const knowledgeUrl='data:text/javascript;base64,'+Buffer.from('export default '+await readFile(new URL('../app/lib/knowledge.json',import.meta.url),'utf8')).toString('base64');
const geminiUrl=await moduleUrl('../app/lib/gemini.ts',{'./observation-context':ctxUrl,'./knowledge.json':knowledgeUrl});
const routeUrl=await moduleUrl('../app/lib/assistant.ts',{'./observation-context':ctxUrl,'./knowledge.json':knowledgeUrl,'./gemini':geminiUrl,'./chat-request':await moduleUrl('../app/lib/chat-request.ts'),'./chat-response':await moduleUrl('../app/lib/chat-response.ts')});
const {handleAsk,boundedText}=await import(routeUrl);
const imageData=(await readFile(new URL('./fixtures/chat-images/baseline.jpg',import.meta.url))).toString('base64');
const fields={image:{mime_type:'image/jpeg',data:imageData},coverage:{source:'Synthetic software fixture',percent:42},growth_form:{source:'Synthetic software fixture',label:'foliose'},satellite:{source:'Synthetic software fixture',ndvi:.5,ndmi:.1,bsi:-.2,mndwi:-.4,observed_at:'2026-09-28',resolution_m:20,patch_pixels:3},geomorphology:{source:'Synthetic software fixture',susceptibility:.2,percentile:35,reference_year:2024,sample_distance_m:5,sample_spacing_m:20},elevation:{source:'Synthetic software fixture',metres:112,resolution_m:90},location:{lat:35.8,lon:-78.7}};
function context(keys){return {observation_id:'SYNTHETIC-SOFTWARE-ONLY',selection:{...C.emptySelection(),...Object.fromEntries(keys.map(k=>[k,true]))},...Object.fromEntries(keys.map(k=>[k,fields[k]]))}}
const req=body=>new Request('https://fixture.example/api/ask',{method:'POST',body:JSON.stringify({question:'Explain this selected evidence',...body})});
const providerReply={answer:'Review the selected evidence cautiously [ES-LIMIT-001].',source_ids:['ES-LIMIT-001'],uncertainty:'Software fixture only.',recommended_action:'none'};
test('every selection combination serializes only selected fields and text omits image bytes',()=>{for(let mask=1;mask<128;mask++){const keys=C.CONTEXT_KEYS.filter((_,i)=>mask&(1<<i)),normalized=C.normalizeObservationContext(context(keys));assert.deepEqual(Object.keys(normalized).sort(),['observation_id','selection',...keys].sort());assert.doesNotMatch(JSON.stringify(C.contextText(normalized)),/\/9j\//);assert.equal('location'in normalized,keys.includes('location'))}});
test('hidden fields, missing selected values, invalid numeric values and blank IDs fail closed',()=>{for(const raw of [{...context(['coverage']),hidden:'secret'},{...context(['coverage']),coverage:undefined},{...context(['coverage']),location:fields.location},{...context(['coverage']),coverage:{...fields.coverage,percent:101}},{...context(['coverage']),observation_id:' '}])assert.throws(()=>C.normalizeObservationContext(raw))});
test('baseline and progressive JPEGs are decoded and reencoded without metadata or trailing payload',async()=>{for(const filename of ['baseline.jpg','progressive.jpg']){const b=await readFile(new URL('./fixtures/chat-images/'+filename,import.meta.url));const cleaned=Buffer.from(C.cleanJpeg(Buffer.concat([b,Buffer.from('PRIVATE_TRAILING_SENTINEL')]).toString('base64')),'base64');assert.equal(jpeg.decode(cleaned).width,32);assert.doesNotMatch(cleaned.toString('latin1'),/PRIVATE_METADATA_SENTINEL|PRIVATE_TRAILING_SENTINEL/);assert.deepEqual([...cleaned.subarray(-2)],[255,217])}});
test('invalid image bytes and oversized base64 are rejected',()=>{for(const b of ['aaaa','/9j/2Q==','a'.repeat(940004)])assert.throws(()=>C.cleanJpeg(b))});
test('environment snapshot cannot cross observation identity or capture context at same coordinates',()=>{const a={id:'a',source:'Collected photograph',captured_at:'2026-10-24',latitude:35.8,longitude:-78.7},b={...a,id:'b'};const snapshot={observation_key:C.observationKey(a),location:fields.location,satellite:{...fields.satellite,location:fields.location}};assert.ok(C.availableContext(a,snapshot).satellite);assert.equal(C.availableContext(b,snapshot).satellite,undefined);assert.equal(C.availableContext({...a,captured_at:'2026-10-25'},snapshot).satellite,undefined)});
test('photo replacement and selected-value changes invalidate attachment identity; examples excluded',()=>{const a={id:'a',source:'Collected photo',image:'data:image/jpeg;base64,'+imageData,coverage:42},b={...a,image:a.image+'A'};assert.notEqual(C.attachmentSignature(a,{...C.emptySelection(),image:true}),C.attachmentSignature(b,{...C.emptySelection(),image:true}));assert.equal(C.isCollected({...a,source:'Illustrative example'}),false);assert.equal(C.isCollected({...a,source:''}),false)});
test('direct Gemini receives real sanitized inline image bytes and exact selected categories',async()=>{const saved=globalThis.fetch;try{for(const keys of [...C.CONTEXT_KEYS.map(k=>[k]),C.CONTEXT_KEYS]){let sent;globalThis.fetch=async(url,options)=>{assert.match(String(url),/generativelanguage.googleapis.com/);sent=JSON.parse(options.body);return Response.json({candidates:[{content:{parts:[{text:JSON.stringify(providerReply)}]}}]})};const r=await handleAsk(req({observation_context:context(keys)}),{GEMINI_API_KEY:'SYNTHETIC-NOT-A-KEY'});assert.equal(r.status,200);const parts=sent.contents.at(-1).parts,payload=JSON.parse(parts[0].text);assert.equal(parts.some(p=>p.inlineData),keys.includes('image'));if(keys.includes('image'))assert.equal(jpeg.decode(Buffer.from(parts[1].inlineData.data,'base64')).width,32);assert.equal('location'in payload.selected_observation,keys.includes('location'));for(const k of C.CONTEXT_KEYS.filter(k=>k!=='image'))assert.equal(k in payload.selected_observation,keys.includes(k));assert.doesNotMatch(JSON.stringify(sent),/PRIVATE_METADATA_SENTINEL/);const body=await r.json();assert.equal(body.mode,'grounded_llm');assert.equal(body.context_receipt,undefined)}}finally{globalThis.fetch=saved}});
test('Render proxy forwards selected context and rejects missing or wrong receipt',async()=>{const saved=globalThis.fetch;try{const raw=context(['coverage']);for(const valid of [true,false]){globalThis.fetch=async(url,options)=>{const body=JSON.parse(options.body);assert.deepEqual(body.observation_context,raw);assert.equal(body.sample_id,raw.observation_id);assert.equal(body.sample,undefined);return Response.json({answer:'Selected coverage supplied.',mode:'grounded_llm',sources:[],scan_evidence:[],...(valid?{context_receipt:C.contextReceipt(raw)}:{})})};const r=await handleAsk(req({observation_context:raw}),{ECOSIGNAL_CHATBOT_URL:'https://fixture.example/assistant/ask'});assert.equal(r.status,valid?200:503);if(!valid)assert.match((await r.json()).error,/backend needs/)}const receipt=C.contextReceipt(raw);assert.equal(C.requireContextReceipt({context_receipt:{...receipt,included:['coverage','location']}},raw),false)}finally{globalThis.fetch=saved}});
test('UTF-8 streamed body limit and unsupported implicit sample cannot leak data',async()=>{const saved=globalThis.fetch;try{const r=await handleAsk(req({question:'x',padding:'é'.repeat(600001)}),{});assert.equal(r.status,413);let sent;globalThis.fetch=async(url,options)=>{sent=JSON.parse(options.body);return Response.json({candidates:[{content:{parts:[{text:JSON.stringify(providerReply)}]}}]})};assert.equal((await handleAsk(req({sample:{site:'PRIVATE_SITE_SENTINEL',coverage:88}}),{GEMINI_API_KEY:'SYNTHETIC'})).status,200);assert.doesNotMatch(JSON.stringify(sent),/PRIVATE_SITE_SENTINEL/)}finally{globalThis.fetch=saved}});

test('unavailable selections are cleared and cannot silently reappear',()=>{const chosen={...C.emptySelection(),satellite:true,location:true};const cleared=C.sanitizeSelection(chosen,{location:fields.location});assert.equal(cleared.satellite,false);assert.equal(C.sanitizeSelection(cleared,{location:fields.location,satellite:fields.satellite}).satellite,false)});

test('JPEG sanitization works in a browser without a Node Buffer global',()=>{const previous=globalThis.Buffer;let cleaned;try{globalThis.Buffer=undefined;cleaned=C.cleanJpeg(imageData);assert.ok(cleaned.length>0)}finally{globalThis.Buffer=previous}assert.equal(jpeg.decode(Buffer.from(cleaned,'base64')).width,32)});


test('Render proxy works when Worker incoming signal is absent or feature-gated',async()=>{
 const saved=globalThis.fetch;
 try{for(const unavailable of ['absent','throws']){
  let called=false;const raw=context(['image']);
  globalThis.fetch=async(url,options)=>{called=true;assert.ok(options.signal instanceof AbortSignal);return Response.json({answer:'Image supplied.',mode:'grounded_llm',sources:[],scan_evidence:[],context_receipt:C.contextReceipt(raw)})};
  const request=req({observation_context:raw});Object.defineProperty(request,'signal',{get(){if(unavailable==='throws')throw Error('Feature disabled');return undefined}});
  assert.equal((await handleAsk(request,{ECOSIGNAL_CHATBOT_URL:'https://fixture.example/assistant/ask'})).status,200);assert.equal(called,true);
 }}finally{globalThis.fetch=saved}
});
test('backend context rejection stays 422 without exposing provider body',async()=>{
 const saved=globalThis.fetch;
 try{globalThis.fetch=async()=>Response.json({detail:'PRIVATE_IMAGE_AND_PROVIDER_SENTINEL'},{status:422});
 const r=await handleAsk(req({observation_context:context(['image'])}),{ECOSIGNAL_CHATBOT_URL:'https://fixture.example/assistant/ask'});
 assert.equal(r.status,422);const text=await r.text();assert.match(text,/CHAT_CONTEXT_REJECTED/);assert.doesNotMatch(text,/PRIVATE_IMAGE_AND_PROVIDER_SENTINEL/);
 }finally{globalThis.fetch=saved}
});

test('stored Site photographs are selectable, while external URLs and unrelated paths are excluded',()=>{
 for(const image of ['data:image/jpeg;base64,'+imageData,'/api/workspace/assets/5a1567b1-5d08-4fa1-bca5-ec67db1fa505'])assert.equal(C.availableContext({image}).image,image);
 for(const image of ['https://external.example/photo.jpg','//external.example/image','/api/workspace/assets/../session','/api/workspace/assets/id?redirect=elsewhere','/other/file.png'])assert.equal(C.availableContext({image}).image,undefined);
});
const {prepareObservationImage}=await import(await moduleUrl('../app/lib/prepare-observation.ts',{'./observation-context':ctxUrl,'./observation-image':await moduleUrl('../app/lib/observation-image.ts')}));
test('saved photographs load through the authenticated same-origin asset route and are prepared as metadata-free JPEGs',async()=>{
 const old={fetch:globalThis.fetch,Image:globalThis.Image,document:globalThis.document};let calls=0;
 try{globalThis.Image=class{naturalWidth=32;naturalHeight=32;async decode(){}};globalThis.document={createElement:()=>({getContext:()=>({fillRect(){},drawImage(){}}),toDataURL:()=> 'data:image/jpeg;base64,'+imageData})};
 globalThis.fetch=async(url,options)=>{calls++;assert.equal(url,'/api/workspace/assets/saved-original');assert.equal(options.credentials,'same-origin');assert.equal(options.redirect,'error');return new Response(Buffer.from(imageData,'base64'),{headers:{'Content-Type':'image/jpeg'}})};
 const photo=await prepareObservationImage('/api/workspace/assets/saved-original');assert.equal(calls,1);assert.equal(photo.mime_type,'image/jpeg');assert.equal(jpeg.decode(Buffer.from(photo.data,'base64')).width,32);
 globalThis.fetch=async()=>new Response('',{status:404});await assert.rejects(prepareObservationImage('/api/workspace/assets/missing'),/could not load/);
 }finally{Object.assign(globalThis,old)}
});
