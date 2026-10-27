"use client";

import {useEffect,useRef,useState} from 'react';

/** Copy the geomorphology-3d folder into your framework's public/static folder. */
export default function EcoSignalTerrain({assetBase='/geomorphology-3d/'}:{assetBase?:string}) {
  const container=useRef<HTMLDivElement>(null);
  const [error,setError]=useState('');
  useEffect(()=>{
    if(!container.current)return;
    const base=assetBase.replace(/\/?$/,'/');
    const viewer=document.createElement('ecosignal-terrain-viewer');
    viewer.setAttribute('data-url',`${base}assets/terrain.json`);
    viewer.setAttribute('metadata-url',`${base}assets/ecosignal_georisk_v2_1m_metadata.json`);
    viewer.setAttribute('model-url',`${base}assets/ecosignal_georisk_v2_1m.joblib`);
    const handleError=(event:Event)=>setError((event as CustomEvent<string>).detail);
    viewer.addEventListener('terrain-error',handleError);
    container.current.replaceChildren(viewer);
    let script=document.querySelector<HTMLScriptElement>('script[data-ecosignal-terrain]');
    if(!customElements.get('ecosignal-terrain-viewer')&&!script){
      script=document.createElement('script');script.type='module';script.src=`${base}viewer.js`;script.dataset.ecosignalTerrain='true';document.head.appendChild(script);
    }
    const loadError=()=>setError('The terrain viewer could not load. Check its static asset location.');
    script?.addEventListener('error',loadError);
    return()=>{script?.removeEventListener('error',loadError);viewer.removeEventListener('terrain-error',handleError);viewer.remove();};
  },[assetBase]);
  return <section aria-label="3D terrain observatory">{error&&<p role="alert">{error}</p>}<div ref={container}/></section>;
}
