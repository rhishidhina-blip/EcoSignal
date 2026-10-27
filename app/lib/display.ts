/** Presentation helpers only: stored values and exported precision are unchanged. */
export const displayNumber=(value:unknown,fallback='—')=>typeof value==='number'&&Number.isFinite(value)?value.toFixed(2):fallback;
export function displaySource(source:string|undefined){if(!source)return 'Observation';if(/illustrative|example|demonstration/i.test(source))return 'Illustrative example';if(/import/i.test(source))return 'Imported analysis';if(/photo analysis/i.test(source))return 'Photo analysis';return source;}
export function localDateTime(value:string){const date=new Date(value);if(!Number.isFinite(date.getTime()))return '';return new Date(date.getTime()-date.getTimezoneOffset()*60000).toISOString().slice(0,19);}
export function captureIso(value:string){if(!value)return '';const date=new Date(value);return Number.isFinite(date.getTime())?date.toISOString():'';}
