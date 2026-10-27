/** Pure, versioned exploratory screening logic. No observations or network side effects. */
export const VERSION='EcoSignal-Unified-Provisional-v3.1.1';
export const WEIGHTS={satellite:.35,aqi:.15,lichen_coverage:.25,growth_form:0,geomorphology:.25} as const;
export type Component=keyof typeof WEIGHTS;
export type Point={lat:number;lon:number};
export type Provenance={source:string;version:string;observed_at:string;location:Point;quality?:{value:number;method:string;evidence:string}};
export type SatelliteInput=Provenance&{acquisition_dates?:string[];period_start?:string;period_end_exclusive?:string;ndvi:number;ndmi:number;bsi:number;mndwi:number;clear_counts:number[];valid_pixels:number;resolution_m:number;patch_pixels:number;reference_version:string};
export type AirInput=Provenance&{aqi:number;category:string;source_url:string;monitor?:Point;site_id?:string};
export type LichenInput=Provenance&{coverage_percent?:number;coverage_confidence?:number;growth_form?:string;growth_form_confidence?:number;confirmed:boolean};
export type GeoInput=Provenance&{raw:number;reference_id:string;raster_sha256:string;year:number;kind:'numeric_raster'|'numeric_grid';footprint_m:number;confidence?:number;quantized_value?:number;percentile?:number;source_year?:number;date_precision?:'year';requested_location?:Point;sample_spacing_m?:number;sample_distance_m?:number;row?:number;column?:number;model_sha256?:string;dem_sha256?:Record<string,string>;feature_code_sha256?:string};
export type ScoreInput={schema_version:1;site_id:string;location?:Point;site_confirmed:boolean;captured_at:string;satellite?:SatelliteInput;air?:AirInput;lichen?:LichenInput;georisk?:GeoInput;illustrative?:boolean};
export type Reference={id:string;version:string;source:string;raster_sha256:string;year:2024;bounds:[number,number,number,number];values?:number[];cdf_percent?:number[];sample_count?:number;score_divisor?:number;sampling:string};
export const POLICY={air_hours:6,monitor_km:50,satellite_days:30,lichen_days:30,alignment_hours:6,satellite_reference:'sentinel-anchors-provisional-v1',biological_method:'visible-coverage-inversion-provisional-v1',growth_weighted:false} as const;
export const LIMITATIONS=[
 'Provisional multi-domain screening indicator: 0 lower, 100 higher relative concern; not calibrated environmental risk or probability.',
 'Weights and satellite anchors are fixed hypotheses, not learned or externally validated. Land cover, water, agriculture, clouds and season alter indices; matched land-cover references are unavailable.',
 'Coverage inversion (100 − coverage %) is a provisional heuristic. Low coverage does not demonstrate contamination, harm or pollution.',
 'Method change from v2: exploratory visible coverage now represents the full 25% biological domain by explicit user choice. Growth form is unweighted context; no species-tolerance or pollution-sensitivity ordering is assumed.',
 'The biological domain is a single visible-coverage indicator, not a validated environmental-harm measurement. Growth-form outputs remain visible as context and may share model errors with coverage.',
 'GeoRisk uses a nearby point on a 20 m lattice, from original 1 m features. It is not an area mean or exact arbitrary-location 1 m prediction. The fixed CDF covers 1,473,136 valid sampled common-coverage points, not all original 1 m pixels. No gap interpolation, color decoding, probabilities, predicted depths or future risk.',
 'AirNow represents monitors, not individual trees. ≤6 h and ≤50 km are engineering eligibility thresholds, not scientific guarantees. Other freshness windows are also provisional engineering choices.',
 'Reported model confidence and clear counts are input metadata, not a calibrated confidence in the composite.',
 'Historical 2024 terrain context has a different date and resolution from live observations. Future exploratory terrain shapes through 2040 are excluded.',
 'Repeat observations are not independent sites. Robustness is not predictive accuracy. Independent construct-specific validation has not been run.'
];
const finite=(v:unknown):v is number=>typeof v==='number'&&Number.isFinite(v);
export const inRange=(v:unknown,lo:number,hi:number)=>finite(v)&&v>=lo&&v<=hi;
export function validPoint(p:Point|undefined):p is Point{return !!p&&inRange(p.lat,-90,90)&&inRange(p.lon,-180,180);}
export function distanceKm(a:Point,b:Point){const r=Math.PI/180,dlat=(b.lat-a.lat)*r,dlon=(b.lon-a.lon)*r;return 6371*2*Math.asin(Math.sqrt(Math.sin(dlat/2)**2+Math.cos(a.lat*r)*Math.cos(b.lat*r)*Math.sin(dlon/2)**2));}
const clip=(v:number)=>Math.max(0,Math.min(1,v));
export function anchor(v:number,lo:number,hi:number,invert=false){if(!finite(v)||!(hi>lo))throw Error('Invalid anchor');const s=100*clip((v-lo)/(hi-lo));return invert?100-s:s;}
export function satelliteScore(s:Pick<SatelliteInput,'ndvi'|'ndmi'|'bsi'>){return .45*anchor(s.ndvi,.2,.8,true)+.35*anchor(s.ndmi,-.2,.5,true)+.20*anchor(s.bsi,-.3,.3);}
export function fixedCDF(raw:number,ref:Reference){
 if(!finite(raw)||!ref.id.trim()||!ref.version.trim()||!ref.source.trim()||!ref.sampling.trim()||!/^[a-f0-9]{64}$/.test(ref.raster_sha256)||ref.year!==2024||ref.bounds.length!==4||ref.bounds.some(v=>!finite(v))||ref.bounds[0]>=ref.bounds[2]||ref.bounds[1]>=ref.bounds[3])throw Error('Invalid fixed CDF provenance');
 if(ref.cdf_percent){const c=ref.cdf_percent;if(ref.values||ref.score_divisor!==10000||!Number.isInteger(ref.sample_count)||ref.sample_count!<100||c.length!==10001||c.some((v,i)=>!inRange(v,0,100)||(i>0&&v<c[i-1]))||Math.abs(c[10000]-100)>1e-8)throw Error('Invalid fixed quantized CDF');const q=Math.round(raw*10000);if(q<0||q>10000||Math.abs(raw*10000-q)>1e-7)throw Error('GeoRisk value must match quantized numerical source');return c[q];}
 const values=ref.values;if(!values||values.length<100||values.some((v,i)=>!finite(v)||(i>0&&v<values[i-1])))throw Error('Invalid fixed CDF provenance');let lo=0,hi=values.length;while(lo<hi){const mid=(lo+hi)>>>1;if(values[mid]<=raw)lo=mid+1;else hi=mid;}return 100*lo/values.length;
}
function quality(p?:Provenance){const q=p?.quality;return q&&inRange(q.value,0,1)&&typeof q.method==='string'&&q.method.trim()&&typeof q.evidence==='string'&&q.evidence.trim()?q:null;}
export function observationTime(t:unknown){
 if(typeof t!=='string')return NaN;
 const m=/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d{1,3})?(Z|[+-]\d{2}:\d{2})$/.exec(t);
 if(!m)return NaN;const [,yy,mm,dd,hh,mi,ss,zone]=m;const year=Number(yy),month=Number(mm),day=Number(dd);
 if(month<1||month>12||day<1||day>new Date(Date.UTC(year,month,0)).getUTCDate()||Number(hh)>23||Number(mi)>59||Number(ss)>59)return NaN;
 if(zone!=='Z'&&(Number(zone.slice(1,3))>14||Number(zone.slice(4))>59||(Number(zone.slice(1,3))===14&&Number(zone.slice(4))!==0)))return NaN;
 return Date.parse(t);
}
const time=observationTime;
function provenance(p:Provenance|undefined,location:Point|undefined,now:number,maxDays:number){if(!p||!p.source?.trim()||!p.version?.trim()||!validPoint(p.location)||!validPoint(location))return false;const age=now-time(p.observed_at);return finite(age)&&age>=0&&age<=maxDays*86400000&&distanceKm(p.location,location)<=.1;}
export function score(input:ScoreInput,now=Date.now(),options:{weights?:Record<Component,number>;reference?:Reference;analysis?:boolean}={}){
 if(!finite(now))throw Error('Valid scoring as-of time required');
 const weights={...WEIGHTS,...options.weights};const keys=Object.keys(WEIGHTS) as Component[];
 if(Object.keys(weights).length!==5||keys.some(k=>!finite(weights[k])||weights[k]<0)||Math.abs(keys.reduce((s,k)=>s+weights[k],0)-1)>1e-10)throw Error('Weights must be explicit, nonnegative and sum to one; no silent normalization');
 if(weights.growth_form!==0)throw Error('v3 growth form is unweighted context; positive growth weights require another method version');
 const scores:Record<Component,number|null>={satellite:null,aqi:null,lichen_coverage:null,growth_form:null,geomorphology:null};const reasons:Record<Component,string>={satellite:'Native numeric satellite sample required',aqi:'Fresh attributed AirNow reading and monitor coordinates required',lichen_coverage:'Confirmed dated biological output required',growth_form:'Unweighted biological context; not required for the four-domain score',geomorphology:'Confirmed in-coverage numerical 2024 GeoRisk sample required'};
 const capture=time(input.captured_at);const base=input.schema_version===1&&!!input.site_id?.trim()&&input.site_confirmed===true&&validPoint(input.location)&&finite(capture)&&capture<=now&&now-capture<=30*86400000&&!input.illustrative;
 const s=input.satellite;
 if(base&&provenance(s,input.location,now,POLICY.satellite_days)&&s&&[s.ndvi,s.ndmi,s.bsi,s.mndwi].every(v=>inRange(v,-1,1))&&Array.isArray(s.clear_counts)&&s.clear_counts.length===4&&s.clear_counts.every(v=>finite(v)&&v>=1)&&inRange(s.valid_pixels,4,36)&&s.resolution_m===20&&s.patch_pixels===3&&s.reference_version===POLICY.satellite_reference&&Math.abs(capture-time(s.observed_at))<=POLICY.satellite_days*86400000){scores.satellite=satelliteScore(s);reasons.satellite='Eligible native 3×3 sample; provisional anchors';}
 const a=input.air;let monitorDistance:number|null=null;
 if(a&&validPoint(a.monitor)&&validPoint(input.location))monitorDistance=distanceKm(a.monitor,input.location);
 if(base&&provenance(a,input.location,now,POLICY.air_hours/24)&&a&&a.source==='AirNow'&&inRange(a.aqi,0,500)&&!!a.category?.trim()&&/^https:\/\/www\.airnow\.gov\//.test(a.source_url)&&monitorDistance!==null&&monitorDistance<=POLICY.monitor_km&&Math.abs(capture-time(a.observed_at))<=POLICY.alignment_hours*3600000){scores.aqi=100*clip(a.aqi/300);reasons.aqi='Eligible AirNow observation';}else if(a)reasons.aqi='AirNow not eligible: check ≤6 h age, capture alignment, monitor coordinates and ≤50 km distance';
 const l=input.lichen;
 if(base&&provenance(l,input.location,now,POLICY.lichen_days)&&l?.confirmed===true&&Math.abs(time(l.observed_at)-capture)<=3600000&&inRange(l.coverage_percent,0,100)){scores.lichen_coverage=100-l.coverage_percent!;reasons.lichen_coverage='Coverage inversion: provisional heuristic';}
 const g=input.georisk,ref=options.reference;
 if(base&&g&&ref&&(g.kind==='numeric_raster'||g.kind==='numeric_grid')&&g.year===2024&&g.raster_sha256===ref.raster_sha256&&g.reference_id===ref.id&&g.source?.trim()&&g.version?.trim()&&validPoint(g.location)&&distanceKm(g.location,input.location!)<=.1&&time(g.observed_at)>=Date.parse('2024-01-01T00:00:00Z')&&time(g.observed_at)<Date.parse('2025-01-01T00:00:00Z')&&finite(g.footprint_m)&&g.footprint_m>0&&(!ref.cdf_percent||(g.kind==='numeric_grid'&&g.sample_spacing_m===20&&inRange(g.sample_distance_m,0,14.142137)&&g.quantized_value===Math.round(g.raw*10000)&&Number.isInteger(g.row)&&Number.isInteger(g.column)&&validPoint(g.requested_location)&&distanceKm(g.requested_location,input.location!)<.001&&!!g.model_sha256?.match(/^[a-f0-9]{64}$/)&&!!g.feature_code_sha256?.match(/^[a-f0-9]{64}$/)&&['2015','2022','2024'].every(y=>!!g.dem_sha256?.[y]?.match(/^[a-f0-9]{64}$/))))&&input.location!.lon>=ref.bounds[0]&&input.location!.lon<=ref.bounds[2]&&input.location!.lat>=ref.bounds[1]&&input.location!.lat<=ref.bounds[3]){try{scores.geomorphology=fixedCDF(g.raw,ref);reasons.geomorphology=ref.cdf_percent?'Nearby 20 m lattice sample · fixed 2024 sampled-cohort percentile':'Fixed 2024 historical numeric reference percentile';}catch{/* invalid reference remains unavailable */}}
 const present=keys.filter(k=>weights[k]>0&&scores[k]!==null),required=keys.filter(k=>weights[k]>0);
 const domains=[['satellite'],['aqi'],['lichen_coverage','growth_form'],['geomorphology']].filter(d=>d.some(k=>weights[k as Component]>0));
 const count=domains.filter(d=>d.filter(k=>weights[k as Component]>0).every(k=>scores[k as Component]!==null)).length;
 const complete=base&&required.every(k=>scores[k]!==null)&&(!options.analysis?required.length===4: true);
 const nominal=present.reduce((n,k)=>n+weights[k],0);
 return {version:VERSION,configuration:{weights,policy:POLICY,biological_method:POLICY.biological_method,growth_form_role:'unweighted_context',previous_method_version:'EcoSignal-Unified-Provisional-v2.0.0',georisk_reference:ref?{id:ref.id,version:ref.version,raster_sha256:ref.raster_sha256}:null,analysis_only:options.analysis===true},status:complete?'complete':'insufficient_data',score:complete?present.reduce((n,k)=>n+scores[k]!*weights[k],0):null,available_domains:count,required_domains:domains.length,nominal_weight_coverage:nominal,missing:required.filter(k=>scores[k]===null),site_eligible:base,monitor_distance_km:monitorDistance,components:keys.map(k=>({key:k,domain:['lichen_coverage','growth_form'].includes(k)?'biological':k,score:scores[k],nominal_weight:weights[k],effective_weight:complete?weights[k]:null,contribution:complete&&scores[k]!==null?scores[k]!*weights[k]:null,status:reasons[k],quality:quality(k==='satellite'?s:k==='aqi'?a:k==='geomorphology'?g:l)})),quality_status:'Reported metadata only; unknown quality remains unknown',biological_context:{growth_form:l?.growth_form??null,growth_form_confidence:l?.growth_form_confidence??null,weighted:false,required:false},partial_estimates_enabled:false};
}
export function confirmedLatest<T extends {site_id:string;site_id_confirmed?:boolean;capture_sequence:number;captured_at:string}>(rows:T[]){const out=new Map<string,T>();for(const r of rows){const id=r.site_id?.trim();if(!id)throw Error('Blank site ID');if(r.site_id_confirmed!==true||!Number.isInteger(r.capture_sequence)||r.capture_sequence<0||!finite(time(r.captured_at)))continue;const old=out.get(id);if(!old||r.capture_sequence>old.capture_sequence)out.set(id,{...r,site_id:id});else if(r.capture_sequence===old.capture_sequence)throw Error('Ambiguous repeat sequence');}return [...out.values()];}
