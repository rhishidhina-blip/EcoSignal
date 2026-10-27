export const OBSERVATIONS_KEY='ecosignal-observations-v5';
export const RESET_IDS_KEY='ecosignal-observations-hidden-ids';
export const RESET_KEY='ecosignal-observations-reset-at';
type DeviceStorage=Pick<Storage,'getItem'|'setItem'|'removeItem'>;
/** Reset this browser only. The cutoff prevents older Site records reappearing. */
export function resetDeviceObservations(storage:DeviceStorage,now=Date.now(),observationIds:string[]=[]){
 const previous=storage.getItem(OBSERVATIONS_KEY),cutoff=storage.getItem(RESET_KEY),previousIds=storage.getItem(RESET_IDS_KEY);
 const ids=[...new Set([...(JSON.parse(previousIds||'[]') as string[]),...observationIds])];
 try{storage.removeItem(OBSERVATIONS_KEY);storage.setItem(RESET_KEY,String(now));storage.setItem(RESET_IDS_KEY,JSON.stringify(ids));}
 catch(error){try{if(previous!==null)storage.setItem(OBSERVATIONS_KEY,previous);if(cutoff===null)storage.removeItem(RESET_KEY);else storage.setItem(RESET_KEY,cutoff);if(previousIds===null)storage.removeItem(RESET_IDS_KEY);else storage.setItem(RESET_IDS_KEY,previousIds)}catch{}throw error;}
 return now;
}
export function visibleSyncedObservations<T extends {id?:unknown;created_at?:unknown;date?:unknown}>(records:T[],cutoff:number,hiddenIds:string[]=[]){
 const hidden=new Set(hiddenIds);
 return records.filter(record=>{if(hidden.has(String(record.id)))return false;if(!Number.isFinite(cutoff)||cutoff<=0)return true;const created=Date.parse(String(record.created_at||''));return Number.isFinite(created)&&created>cutoff;});
}
