import type {AirQualityData} from './air-quality';
import {distanceKm,validPoint,type AirInput,type Point} from './unified';
/** Attribute the reading to the requested observation, never the selected map pin. */
export function airInputFromReading(reading:AirQualityData,location:Point):AirInput{
 if(!validPoint(location)||!validPoint(reading.requested_location)||distanceKm(reading.requested_location,location)>.001||reading.source!=='AirNow'||!Number.isFinite(reading.aqi)||reading.aqi<0||reading.aqi>500||!Number.isFinite(Date.parse(reading.timestamp)))throw Error('AirNow response does not match this observation.');
 return {aqi:reading.aqi,category:reading.category,source:'AirNow',version:'AirNow-location-v2',source_url:reading.source_url,observed_at:reading.timestamp,location:{...location},monitor:reading.monitor_location,site_id:reading.primary_site_id};
}
export function captureAirAlignmentHours(capture:string,observed:string):number|null{
 const a=Date.parse(capture),b=Date.parse(observed);return Number.isFinite(a)&&Number.isFinite(b)?Math.abs(a-b)/3600000:null;
}
