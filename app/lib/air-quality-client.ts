import type {AirQualityData} from './air-quality';

/** One bounded retry for transient failures; never replace unavailable readings. */
export async function fetchAirQuality(lat:number,lon:number,signal:AbortSignal):Promise<AirQualityData>{
 for(let attempt=0;attempt<2;attempt++){
  signal.throwIfAborted();
  try{
   const response=await fetch(`/api/air-quality?lat=${lat}&lon=${lon}`,{
    signal:AbortSignal.any([signal,AbortSignal.timeout(18000)]),cache:'no-store'
   });
   if(!response.ok){
    const retryable=[429,502,503,504].includes(response.status);
    if(attempt===0&&retryable){await response.body?.cancel();continue;}
    return Promise.reject(Error('AirNow is temporarily unavailable. Refresh or view the source.'));
   }
   const data=await response.json() as AirQualityData;
   if(!Number.isFinite(data.aqi)||data.aqi<0||data.aqi>500||!Array.isArray(data.pollutants)||!data.pollutants.length||!Number.isFinite(Date.parse(data.timestamp)))throw Error('AirNow returned an incomplete reading.');
   return data;
  }catch(error){
   if(signal.aborted)throw error;
   if(attempt===1)throw Error('AirNow is temporarily unavailable. Refresh or view the source.');
  }
 }
 throw Error('AirNow is temporarily unavailable.');
}
