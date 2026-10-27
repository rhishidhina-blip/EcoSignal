import {canonical,hash,WorkflowError,requireThat,type Obj} from './evidence-core';
export const SCOPE='appgprj_6a5266428ac48191be22792a6f91e469';
export type Entity=Obj&{id:string;kind:string;revision:number};
export class EvidenceStore{
 constructor(public db:D1Database,public actor:string){}
 async get(kind:string,id:string):Promise<Entity|null>{const r=await this.db.prepare('SELECT * FROM eco_entities WHERE owner=? AND kind=? AND id=?').bind(SCOPE,kind,id).first<any>();return r?{...JSON.parse(r.payload),id:r.id,kind:r.kind,revision:r.version,created_at:r.created,updated_at:r.updated}:null}
 async list(kind:string,limit=1000):Promise<Entity[]>{const r=await this.db.prepare('SELECT * FROM eco_entities WHERE owner=? AND kind=? ORDER BY updated DESC LIMIT ?').bind(SCOPE,kind,limit).all<any>();return r.results.map(x=>({...JSON.parse(x.payload),id:x.id,kind:x.kind,revision:x.version,created_at:x.created,updated_at:x.updated}))}
 async required(kind:string,id:string){const r=await this.get(kind,id);requireThat(r,'NOT_FOUND','The requested record was not found',404);return r}
 async put(kind:string,id:string,payload:Obj,expected:number,event:string,extras:{kind:string;id:string;payload:Obj}[]=[],splitGuard?:{group:string;split:string}){
  const nonce=crypto.randomUUID();const data:Obj={...payload,mutation_id:nonce};delete data.revision;delete data.kind;const created=payload.created_at||new Date().toISOString();
  for(let attempt=0;attempt<4;attempt++){
   const head=await this.db.prepare('SELECT hash FROM eco_audit WHERE owner=? AND hash NOT IN (SELECT previous FROM eco_audit WHERE owner=?) LIMIT 1').bind(SCOPE,SCOPE).first<{hash:string}>();
   const previous=head?.hash||'GENESIS',stamp=new Date().toISOString(),idEvent=crypto.randomUUID();
   const audit={event_type:event,entity_kind:kind,entity_id:id,actor_id:this.actor,at:stamp,previous,payload_sha256:await hash(canonical(data))};const canon=canonical(audit),digest=await hash(canon);
   const statements:D1PreparedStatement[]=[];
   if(expected===0)statements.push(this.db.prepare('INSERT OR IGNORE INTO eco_entities(owner,kind,id,version,payload,created,updated) VALUES(?,?,?,1,?,?,?)').bind(SCOPE,kind,id,canonical(data),created,stamp));
   else statements.push(this.db.prepare('UPDATE eco_entities SET payload=?,version=version+1,updated=? WHERE owner=? AND kind=? AND id=? AND version=?').bind(canonical(data),stamp,SCOPE,kind,id,expected));
   // Audit insert is conditional on anchor success. Every secondary write is bound to the same unique mutation nonce.
   statements.push(this.db.prepare('INSERT INTO eco_audit(owner,id,previous,hash,canonical,created) SELECT ?,?,?,?,?,? WHERE changes()=1').bind(SCOPE,idEvent,previous,digest,canon,stamp));
   for(const x of extras)statements.push(this.db.prepare(`INSERT INTO eco_entities(owner,kind,id,version,payload,created,updated) SELECT ?,?,?,1,?,?,? WHERE EXISTS(SELECT 1 FROM eco_entities WHERE owner=? AND kind=? AND id=? AND json_extract(payload,'$.mutation_id')=?)`).bind(SCOPE,x.kind,x.id,canonical(x.payload),stamp,stamp,SCOPE,kind,id,nonce));
   if(splitGuard)statements.push(this.db.prepare(`INSERT INTO eco_site_splits(owner,site_group,split) SELECT ?,?,? WHERE EXISTS(SELECT 1 FROM eco_entities WHERE owner=? AND kind=? AND id=? AND json_extract(payload,'$.mutation_id')=?) ON CONFLICT(owner,site_group) DO UPDATE SET split=CASE WHEN split=excluded.split THEN split ELSE NULL END`).bind(SCOPE,splitGuard.group,splitGuard.split,SCOPE,kind,id,nonce));
   try{const result=await this.db.batch(statements);if(!result[0].meta.changes)throw new WorkflowError('VERSION_CONFLICT','This record changed elsewhere. Refresh and try again.',409,true);return await this.required(kind,id)}catch(e){if(e instanceof WorkflowError)throw e;if(/eco_audit|eco_site_splits|UNIQUE constraint|NOT NULL constraint/i.test(String(e))){if(/eco_site_splits/i.test(String(e)))throw new WorkflowError('SPLIT_LEAKAGE','This site group already belongs to a different dataset split',409);if(attempt<3)continue}throw e}
  }throw new WorkflowError('VERSION_CONFLICT','Concurrent update; retry',409,true)
 }
 async events(){const r=await this.db.prepare('SELECT * FROM eco_audit WHERE owner=? ORDER BY created,id').bind(SCOPE).all<any>();return r.results}
 async verify(){const events=await this.events(),byPrevious=new Map(events.map(x=>[x.previous,x]));let previous='GENESIS',count=0;while(byPrevious.has(previous)){const e=byPrevious.get(previous)!;if(await hash(e.canonical)!==e.hash)return {valid:false,count,reason:'Digest mismatch'};const parsed=JSON.parse(e.canonical);if(parsed.previous!==previous)return {valid:false,count,reason:'Broken predecessor'};previous=e.hash;count++;if(count>events.length)return {valid:false,count,reason:'Cycle'}}return {valid:count===events.length,count,head:previous,scope:'Current private Site workspace',note:'Integrity chain, not proof that observations or labels are scientifically correct'}}
}
