import dataset from './satellite-data.json';
import {project} from './map-geometry';
export type SatellitePeriod='baseline'|'comparison'|'change';
export const SATELLITE_INDICES=['NDVI','NDMI','BSI','MNDWI'] as const;
export type SatelliteIndex=typeof SATELLITE_INDICES[number];
export const satelliteData=dataset;
export function indexForLayer(layer:string):SatelliteIndex|null {return ({Vegetation:'NDVI',Moisture:'NDMI','Bare soil':'BSI',Water:'MNDWI','Water / bare ground':'MNDWI',NDVI:'NDVI',NDMI:'NDMI',BSI:'BSI',MNDWI:'MNDWI'} as Record<string,SatelliteIndex>)[layer]||null;}
export function satelliteAsset(index:SatelliteIndex,period:SatellitePeriod){return dataset.assets[`${index.toLowerCase()}-${period}` as keyof typeof dataset.assets];}
export function rasterCell(lon:number,lat:number){const [west,south,east,north]=dataset.bounds;const nw=project(west,north,0),se=project(east,south,0),point=project(lon,lat,0);const x=Math.floor((point.x-nw.x)/(se.x-nw.x)*dataset.width),y=Math.floor((point.y-nw.y)/(se.y-nw.y)*dataset.height);return x<0||y<0||x>=dataset.width||y>=dataset.height?null:y*dataset.width+x;}
export function numericValue(values:Int16Array,cell:number|null){if(cell===null)return null;const raw=values[cell];return raw===undefined||raw===dataset.numeric_nodata?null:raw/dataset.numeric_scale;}
export function satelliteSummary(index:SatelliteIndex,period:SatellitePeriod){const week=dataset.weeks[period==='baseline'?0:1];return dataset.summary.find(row=>row.index===index&&row.week===week)!;}
export function periodLabel(period:SatellitePeriod){return period==='baseline'?'Sep 21–27':period==='comparison'?'Sep 28–Oct 4':'Sep 28 vs Sep 21';}
