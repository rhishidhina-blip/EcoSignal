/** Only uploaded data or this Site's protected original-image endpoint. */
export function observationImageSource(value:unknown):string|undefined{
 if(typeof value!=='string')return undefined;
 if(/^data:image\/(?:jpeg|png|webp);base64,/i.test(value)&&value.length<=12_000_000)return value;
 if(/^\/api\/workspace\/assets\/[a-zA-Z0-9-]{1,128}$/.test(value))return value;
 return undefined;
}
