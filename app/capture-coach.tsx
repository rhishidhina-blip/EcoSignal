'use client';
import {useEffect,useRef,useState} from 'react';
import {assessCapture} from './lib/image-evidence';
export default function CaptureCoach({image,mask,assessment,onAssessed}:{image:string;mask?:string;assessment?:any;onAssessed?:(result:any)=>void}){
 const [result,setResult]=useState<any>(null),[busy,setBusy]=useState(false),[error,setError]=useState('');const generation=useRef(0);
 useEffect(()=>{generation.current++;setResult(null);setError('');setBusy(false)},[image,mask]);
 const quality=result||assessment,approved=quality?.decision==='accepted',caution=quality?.decision==='accepted_with_caution';
 const state=approved?'approved':caution?'caution':'retake';
 return <div className={`capture-coach photo-check ${quality?'has-result '+state:''}`}>
  <button className="photo-check-button" disabled={busy} onClick={async()=>{const token=++generation.current;setBusy(true);setError('');try{const r=await assessCapture(image,mask);if(token===generation.current){setResult(r);onAssessed?.(r)}}catch{if(token===generation.current)setError('Photo check unavailable. Try again.')}finally{if(token===generation.current)setBusy(false)}}}>{busy?'Checking…':quality?'Check again':'Check photo quality'}</button>
  {(quality||error)&&<div className="photo-check-gradient" role="status"><div className="photo-check-status"><span className="quality-symbol" aria-hidden="true">{approved?'✓':caution?'!':'↻'}</span><div><b>{error|| (approved?'Photo checks passed':caution?'Usable · check framing':'Retake suggested')}</b><small>{!error&&(approved?'Sharpness, lighting & resolution':quality.instructions?.[0])}</small></div></div>{quality&&<details className="photo-check-details"><summary>Quality details</summary><p>{quality.assessment_status==='base_quality_only_framing_unavailable'?'Photo quality checked. Lichen framing awaits an accepted mask.':'Photo quality and lichen framing checked.'}</p><ul>{quality.instructions?.map((s:string)=><li key={s}>{s}</li>)}</ul><small>Heuristic check · not prediction confidence.</small></details>}</div>}
 </div>
}
