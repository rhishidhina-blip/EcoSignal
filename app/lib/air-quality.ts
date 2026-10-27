export type AirQualityData={monitor_location?:{lat:number;lon:number};primary_site_id?:string;source:string;evidence_type:string;source_url:string;requested_location:{lat:number;lon:number};reporting_area:string;timestamp:string;fetched_at:string;stale:boolean;aqi:number;category:string;primary_pollutant:string;pollutants:{key:string;label:string;aqi:number;timestamp:string;site:string;site_id:string;agency:string}[];limitations:string};
export function aqiCategory(aqi:number|null){if(aqi===null)return 'Unavailable';return aqi<=50?'Good':aqi<=100?'Moderate':aqi<=150?'Unhealthy for sensitive groups':aqi<=200?'Unhealthy':aqi<=300?'Very unhealthy':'Hazardous';}
// AirNow's endpoint supplies a local date, hour and explicit standard/daylight offset.
export function observationTime(record:Record<string,unknown>){
 const date=String(record.validDate||'').match(/^(\d{2})\/(\d{2})\/(\d{2})$/),time=String(record.time||'').match(/^(\d{2}):(\d{2})$/);
 const offsets:Record<string,string>={EST:'-05:00',EDT:'-04:00',CST:'-06:00',CDT:'-05:00',MST:'-07:00',MDT:'-06:00',PST:'-08:00',PDT:'-07:00'};
 const offset=offsets[String(record.timezone)];if(!date||!time||!offset||Number(time[1])>23||Number(time[2])>59)return NaN;
 const iso=`20${date[3]}-${date[1]}-${date[2]}T${time[1]}:${time[2]}:00${offset}`;return Date.parse(iso);
}
export function normalizeAirNow(raw:unknown,lat:number,lon:number,now=Date.now()):AirQualityData{
 if(!Array.isArray(raw))throw Error('Invalid AirNow response');
 const observations=raw.filter(r=>r&&r.dataType==='O'&&typeof r.parameter==='string'&&typeof r.aqi==='number'&&Number.isInteger(r.aqi)&&r.aqi>=0&&r.aqi<=500&&Number.isFinite(observationTime(r))&&observationTime(r)<=now+15*60*1000&&observationTime(r)>=now-24*60*60*1000);
 // Preserve the location-specific pollutant selection returned by AirNow. For duplicate
 // pollutant rows use its latest observation; never substitute forecasts or yesterday.
 const latest=new Map<string,Record<string,any>>();for(const r of observations){const old=latest.get(r.parameter);if(!old||observationTime(r)>observationTime(old))latest.set(r.parameter,r);}
 const records=[...latest.values()];if(!records.length)throw Error('AirNow observations unavailable');
 const primary=records.reduce((a,b)=>b.aqi>a.aqi?b:a),stamp=observationTime(primary);
 const monitor=typeof primary.latitude==='number'&&typeof primary.longitude==='number'&&primary.latitude>=-90&&primary.latitude<=90&&primary.longitude>=-180&&primary.longitude<=180?{lat:primary.latitude,lon:primary.longitude}:undefined;
 return {monitor_location:monitor,primary_site_id:String(primary.siteID||''),source:'AirNow',evidence_type:'reported_air_quality',source_url:`https://www.airnow.gov/?latitude=${lat}&longitude=${lon}`,requested_location:{lat,lon},reporting_area:String(primary.reportingArea||primary.siteName||'Selected location'),timestamp:new Date(stamp).toISOString(),fetched_at:new Date(now).toISOString(),stale:records.some(r=>now-observationTime(r)>3*60*60*1000),aqi:primary.aqi,category:aqiCategory(primary.aqi),primary_pollutant:primary.parameter,pollutants:records.map(r=>({key:r.parameter,label:r.parameter==='OZONE'?'O₃':r.parameter,aqi:r.aqi,timestamp:new Date(observationTime(r)).toISOString(),site:String(r.siteName||r.reportingArea||'Unavailable'),site_id:String(r.siteID||''),agency:String(r.reportingAgency||'AirNow partner agency')})),limitations:'Preliminary AirNow observations. Compare the same coordinates and observation time: nearby locations, monitor maps and forecasts may differ. Pollutants can have different observation times; each is shown separately. AQI and satellite weeks describe different dates.'};
}
const cache=new Map<string,{expires:number;data:AirQualityData}>();
export async function getAirQuality(lat:number,lon:number,now=Date.now()){
 if(!Number.isFinite(lat)||!Number.isFinite(lon)||lat<35.5||lat>36.2||lon< -79.1||lon> -78.2)throw Error('Choose a location in Greater Raleigh.');
 const key=`${lat.toFixed(4)},${lon.toFixed(4)}`,cached=cache.get(key);if(cached&&cached.expires>now)return {...cached.data,stale:cached.data.pollutants.some(p=>now-Date.parse(p.timestamp)>3*60*60*1000)};
 // Public location-specific lookup used by AirNow.gov (v2), including the site's
 // default 50-mile search. A county maximum would not match its home-page dial.
 const url=new URL('https://airnowgovapi.com/v2/reportingarea/get');url.search=new URLSearchParams({latitude:String(lat),longitude:String(lon),stateCode:'NC',maxDistance:'50'}).toString();
 const r=await fetch(url,{signal:AbortSignal.timeout(12000)});if(!r.ok)throw Error('AirNow unavailable.');
 const data=normalizeAirNow(await r.json(),lat,lon,now);if(cache.size>=40)cache.delete(cache.keys().next().value!);cache.set(key,{expires:now+60*1000,data});return data;
}
export async function handleAirQuality(request:Request){const headers={'content-type':'application/json','cache-control':'no-store'};if(request.method!=='GET')return Response.json({error:'Use GET'},{status:405,headers});const u=new URL(request.url);const a=u.searchParams.get('lat'),b=u.searchParams.get('lon');const lat=a===null||a.trim()===''?NaN:Number(a),lon=b===null||b.trim()===''?NaN:Number(b);if(!Number.isFinite(lat)||!Number.isFinite(lon)||lat<35.5||lat>36.2||lon< -79.1||lon> -78.2)return Response.json({error:'Choose a location in Greater Raleigh.'},{status:400,headers});try{return Response.json(await getAirQuality(lat,lon),{headers});}catch{return Response.json({error:'AirNow observations are unavailable. Please retry.'},{status:503,headers});}}
