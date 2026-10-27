import {displayNumber} from './lib/display';

/** Visual anchors only; no new scoring thresholds or health categories. */
export default function UnifiedScoreScale({score}:{score:number|null}){
 const value=typeof score==='number'&&Number.isFinite(score)&&score>=0&&score<=100?score:null;
 return <div className="unified-score-scale">
  <div className="score-scale-caption"><b>Relative concern</b><span>Lower is better</span></div>
  <div className="score-scale-track" role={value===null?'img':'meter'} aria-label={value===null?'Relative concern scale; no score available':'Unified score relative concern'} aria-valuemin={value===null?undefined:0} aria-valuemax={value===null?undefined:100} aria-valuenow={value??undefined} aria-valuetext={value===null?undefined:`${displayNumber(value)} out of 100; lower is better`}>
   {value!==null&&<span className="score-scale-marker" style={{left:`${value}%`}} aria-hidden="true"><i/></span>}
  </div>
  <div className="score-scale-labels" aria-hidden="true"><span><b>0</b><small>Lower concern</small></span><span><b>50</b><small>Mid-range</small></span><span><b>100</b><small>Higher concern</small></span></div>
  <p className="score-scale-note">Visual guide · not validated health thresholds.</p>
 </div>;
}
