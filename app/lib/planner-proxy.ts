/** Server only. Token never enters browser code. Preserve Sites access controls. */
export async function handlePlanner(request:Request,env:{ECOSIGNAL_PLANNER_URL?:string;ECOSIGNAL_PLANNER_TOKEN?:string}){
 const error=(detail:string,status:number)=>Response.json({detail},{status,headers:{'Cache-Control':'no-store'}});
 if(request.method!=='POST')return error('Use POST.',405);
 const origin=request.headers.get('Origin');if(origin&&origin!==new URL(request.url).origin)return error('Cross-site request rejected.',403);
 if(!env.ECOSIGNAL_PLANNER_URL||!env.ECOSIGNAL_PLANNER_TOKEN)return error('Adaptive planner is not connected yet.',503);
 if(!request.headers.get('content-type')?.startsWith('application/json'))return error('Send observation metadata as JSON.',415);
 let target:URL;try{target=new URL('/sampling/recommend',env.ECOSIGNAL_PLANNER_URL);if(target.protocol!=='https:'||target.username||target.password)throw Error();}catch{return error('Planner service configuration needs review.',503);}
 const reader=request.body?.getReader();if(!reader)return error('Planner input is missing.',422);
 const chunks:Uint8Array[]=[];let length=0;
 try{for(;;){const n=await reader.read();if(n.done)break;length+=n.value.length;if(length>2*1024*1024){await reader.cancel();return error('Send metadata only, without photographs.',413);}chunks.push(n.value);}}finally{reader.releaseLock();}
 const body=new Uint8Array(length);let offset=0;for(const c of chunks){body.set(c,offset);offset+=c.length;}
 try{const r=await fetch(target,{method:'POST',body,headers:{'Content-Type':'application/json','Authorization':'Bearer '+env.ECOSIGNAL_PLANNER_TOKEN},redirect:'manual',signal:AbortSignal.timeout(110000)});
 if(r.status>=300&&r.status<400)return error('Planner endpoint redirected. Check its configured address.',502);
 if(r.status===401||r.status===403)return error('Planner server credentials need updating.',503);
 if(!r.headers.get('content-type')?.includes('application/json'))return error('Planner is starting or unavailable. Please retry.',502);
 if(!r.ok)return error(r.status===503?'Real planner candidate data or configuration is missing.':'Planner could not process the observation metadata.',r.status===503?503:502);
 return new Response(r.body,{status:200,headers:{'Content-Type':'application/json','Cache-Control':'no-store'}});
 }catch{return error('Planner is waking up or could not connect. Please retry.',504);}
}
