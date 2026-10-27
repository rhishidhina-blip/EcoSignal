import {type Context,type Point,cleanJpeg} from './observation-context';
import {observationImageSource} from './observation-image';

export async function prepareObservationImage(dataUrl:string):Promise<Context['image']>{
 const source=observationImageSource(dataUrl);if(!source)throw Error('Choose a JPEG, PNG or WebP photograph under 8 MB.');
 let objectUrl:string|undefined;
 if(source.startsWith('/api/workspace/assets/')){
  const response=await fetch(source,{credentials:'same-origin',redirect:'error',signal:AbortSignal.timeout(15000)});
  if(!response.ok)throw Error('The saved photograph could not load. Please retry.');
  const blob=await response.blob();
  if(!['image/jpeg','image/png','image/webp'].includes(blob.type)||blob.size>8*1024*1024)throw Error('Choose a JPEG, PNG or WebP photograph under 8 MB.');
  objectUrl=URL.createObjectURL(blob);
 }
 try{
 const image=new Image();image.src=objectUrl||source;await image.decode();
 if(!image.naturalWidth||!image.naturalHeight||image.naturalWidth*image.naturalHeight>60_000_000)throw Error('Choose a smaller photograph.');
 const scale=Math.min(1,1280/Math.max(image.naturalWidth,image.naturalHeight)),canvas=document.createElement('canvas');
 canvas.width=Math.max(1,Math.round(image.naturalWidth*scale));canvas.height=Math.max(1,Math.round(image.naturalHeight*scale));
 const context=canvas.getContext('2d');if(!context)throw Error('Image preparation is unavailable.');
 context.fillStyle='#ffffff';context.fillRect(0,0,canvas.width,canvas.height);context.drawImage(image,0,0,canvas.width,canvas.height);
 for(const quality of [.8,.65,.5]){
  const data=canvas.toDataURL('image/jpeg',quality).split(',')[1];
  if(data&&data.length<=930000)return {mime_type:'image/jpeg',data:cleanJpeg(data)};
 }
 throw Error('This photograph is still too large. Choose a smaller image.');
 }finally{if(objectUrl)URL.revokeObjectURL(objectUrl)}
}

export async function loadElevation(point:Point,signal?:AbortSignal){
 // This function runs only after the visitor explicitly clicks the elevation
 // lookup button, whose label discloses sharing coordinates with Open-Meteo.
 const url=new URL('https://api.open-meteo.com/v1/elevation');url.searchParams.set('latitude',String(point.lat));url.searchParams.set('longitude',String(point.lon));
 const response=await fetch(url,{signal:AbortSignal.any([...(signal?[signal]:[]),AbortSignal.timeout(10000)])});
 if(!response.ok)throw Error('Elevation is unavailable.');
 const raw=await response.text();if(raw.length>4000)throw Error('Invalid elevation response.');
 const metres=JSON.parse(raw)?.elevation?.[0];
 if(typeof metres!=='number'||!Number.isFinite(metres)||metres < -500||metres>9000)throw Error('No valid elevation at this point.');
 return {metres,location:{lat:point.lat,lon:point.lon},source:'Open-Meteo / Copernicus DEM GLO-90',version:'Copernicus DEM 2021 release',resolution_m:90};
}
