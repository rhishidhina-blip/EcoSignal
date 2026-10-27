import * as THREE from './vendor/three.module.js';
import {OrbitControls} from './vendor/OrbitControls.js';

const baseURL=new URL('./',import.meta.url);
const allowedYears=[2015,2022,2024,...Array.from({length:16},(_,i)=>2025+i)];
const earth=new THREE.Color();
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));

export class EcoSignalTerrainViewer extends HTMLElement {
  async connectedCallback(){
    if(this.initialized)return;this.initialized=true;
    this.attachShadow({mode:'open'});
    this.shadowRoot.innerHTML=`<link rel="stylesheet" href="${new URL('viewer.css',baseURL)}">
    <section class="app" aria-label="EcoSignal terrain observatory">
      <div class="brand"><div class="brand-name"><span class="brand-mark" aria-hidden="true"></span>ECOSIGNAL</div><span class="brand-sub">BioTerrain / Observatory</span></div>
      <div class="heading"><div><p class="eyebrow">Landscape intelligence</p><h1>A landscape, across time.</h1><p class="intro">Explore measured terrain and the model’s susceptibility layer. Move beyond the surveys to explore a clearly labeled historical-trend scenario.</p></div><div class="heading-note">Local study coverage<br><span data-extent>Aligned LiDAR surveys</span></div></div>
      <div class="viewport">
        <div class="stage"></div>
        <div class="stage-overlay"><div class="view-year" data-year>2024</div><div class="badge" data-badge>Observed survey</div><div class="view-label" data-view-label>2024 GeoRisk reference</div></div>
        <div class="viewport-actions"><button type="button" data-fit aria-label="Reset terrain camera">Fit view</button><button type="button" data-fullscreen aria-label="Show terrain viewer fullscreen">Expand</button></div>
        <div class="legend"><div class="legend-name" data-legend-name>GEORISK · 2024 REFERENCE</div><div class="legend-bar" data-legend-bar></div><div class="legend-ends"><span data-low>Lower</span><span data-high>Higher</span></div><div class="legend-note" data-legend-note>Relative susceptibility · not probability</div></div>
        <div class="compass"><span data-compass aria-hidden="true">↑</span>N</div>
        <div class="tooltip" hidden></div><div class="loading">Loading measured terrain…</div><div class="error" hidden role="alert"></div>
      </div>
      <div class="timeline"><div class="time-heading"><label for="year">Survey / projection year <output data-year-output>2024</output></label><button type="button" data-play>Play timeline</button></div>
        <input class="time-slider" id="year" type="range" min="2015" max="2040" step="1" value="2024" aria-valuetext="2024 observed survey">
        <div class="date-row">${[2015,2022,2024,2030,2040].map(year=>`<button type="button" data-jump="${year}" class="${year>2024?'future-date':''}" aria-pressed="${year===2024}">${year}${year>2024?' · scenario':''}</button>`).join('')}</div>
        <p class="scenario-note" hidden>Exploratory terrain projection—not a validated forecast. GeoRisk colors remain the actual 2024 susceptibility reference.</p>
      </div>
      <div class="settings"><div class="setting"><label for="surface">Surface</label><select id="surface"><option value="risk">Model susceptibility · 2024</option><option value="elevation">Terrain elevation</option><option value="change">Change from 2015</option></select></div><div class="setting relief"><label for="relief">Vertical exaggeration</label><input id="relief" type="range" min="1" max="80" value="40"><output data-relief>×40</output></div><button type="button" class="reset" data-reset>Reset scene</button></div>
      <div class="footer"><details><summary>Data, model & projection notes</summary><p data-resolution></p><p>Model colors show relative, uncalibrated susceptibility to observed terrain lowering. They do not identify erosion cause, predict depth, or become future probabilities when the timeline moves. Survey/geoid compatibility remains provisional.</p><p data-hindcast></p><p>The exploratory projection extends the per-cell elevation trend from 2015, 2022 and 2024, anchored to the measured 2024 surface. It assumes the trend continues and does not include future weather, construction, interventions or episodic events. No validated 2040 confidence interval is available.</p><p data-metrics></p><a data-model download="ecosignal_georisk_v2_1m.joblib">Download trained model</a></details><span class="foot-meta">Drag to orbit · pinch or scroll to zoom</span></div>
      <p class="sr-only" aria-live="polite" data-accessible-state></p>
    </section>`;
    this.q=s=>this.shadowRoot.querySelector(s);
    this.state={year:2024,surface:'risk',exaggeration:40};
    this.abort=new AbortController();this.disposed=false;
    try{
      const dataURL=new URL(this.getAttribute('data-url')||'assets/terrain.json',this.getAttribute('data-url')?document.baseURI:baseURL);
      this.assetBase=new URL('./',dataURL);
      const metaURL=new URL(this.getAttribute('metadata-url')||'ecosignal_georisk_v2_1m_metadata.json',this.getAttribute('metadata-url')?document.baseURI:this.assetBase);
      const load=async url=>{const response=await fetch(url,{signal:this.abort.signal,credentials:'same-origin'});if(!response.ok)throw new Error('Terrain assets could not be loaded.');return response.json();};
      [this.data,this.metadata]=await Promise.all([load(dataURL),load(metaURL)]);
      this.validateData();if(this.disposed)return;
      this.createScene();this.createGeometry();this.wireControls();
      const texture=await new THREE.TextureLoader().loadAsync(new URL(this.data.risk.texture,this.assetBase).href);
      if(this.disposed){texture.dispose();return;}
      this.riskTexture=texture;texture.colorSpace=THREE.SRGBColorSpace;
      texture.minFilter=THREE.LinearFilter;texture.magFilter=THREE.LinearFilter;
      this.riskMesh.material.map=texture;this.riskMesh.material.needsUpdate=true;
      this.updateScene();this.q('.loading').hidden=true;this.ready=true;
      this.dispatchEvent(new CustomEvent('terrain-ready',{bubbles:true,composed:true,detail:{year:2024,observedYears:[2015,2022,2024],lastProjectionYear:2040}}));
      this.startRendering();this.fillNotes();
    }catch(error){if(this.disposed)return;this.q('.loading').hidden=true;this.q('.error').hidden=false;this.q('.error').textContent=`${error.message} The interactive viewer requires WebGL 2 and its same-origin assets.`;this.dispatchEvent(new CustomEvent('terrain-error',{detail:error.message,bubbles:true,composed:true}));}
  }
  validateData(){
    const d=this.data;
    if(d.n!==129||JSON.stringify(d.years)!=='[2015,2022,2024]'||d.risk.data_year!==2024||d.projection.last_year!==2040)throw new Error('Unexpected terrain data contract.');
    const count=d.n*d.n;
    if(d.grids.some(g=>g.length!==count)||d.uv.length!==count||d.projection.rate_m_per_year.length!==count||d.risk_display_scores.length!==count)throw new Error('Terrain array dimensions disagree.');
    if(d.risk.score_year_is_fixed_during_future_projection!==true||this.metadata.latest_map_input_year!==2024)throw new Error('Model reference year could not be verified.');
    if(d.grids.some(g=>g.some(v=>v!==null&&!Number.isFinite(v))))throw new Error('Invalid elevation values.');
  }
  createScene(){
    this.scene=new THREE.Scene();
    this.camera=new THREE.PerspectiveCamera(42,1,.1,5000);
    this.renderer=new THREE.WebGLRenderer({antialias:true,alpha:true,powerPreference:'low-power'});
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,1.75));
    this.renderer.outputColorSpace=THREE.SRGBColorSpace;this.renderer.toneMapping=THREE.NoToneMapping;
    this.renderer.domElement.setAttribute('role','img');this.renderer.domElement.setAttribute('aria-label','3D terrain with actual 2024 model susceptibility.');this.renderer.domElement.tabIndex=0;
    this.q('.stage').append(this.renderer.domElement);
    this.controls=new OrbitControls(this.camera,this.renderer.domElement);
    this.controls.enableDamping=true;this.controls.dampingFactor=.075;this.controls.minDistance=260;this.controls.maxDistance=4200;
    this.controls.minPolarAngle=.18;this.controls.maxPolarAngle=1.46;
    this.controls.listenToKeyEvents(this.renderer.domElement);
    this.scene.add(new THREE.AmbientLight(0xb8d4ca,1.7));
    const light=new THREE.DirectionalLight(0xfff3d6,2.3);light.position.set(-450,900,350);this.scene.add(light);
    const fill=new THREE.HemisphereLight(0xc0d9ec,0x142823,.8);this.scene.add(fill);
    const grid=new THREE.GridHelper(1160,16,0x3b646a,0x244047);grid.position.y=-22;grid.material.transparent=true;grid.material.opacity=.35;this.scene.add(grid);this.grid=grid;
    this.resetCamera();
    this.resizeObserver=new ResizeObserver(()=>{const rect=this.q('.viewport').getBoundingClientRect();this.renderer.setSize(rect.width,rect.height);const aspect=rect.width/rect.height;this.camera.aspect=aspect;this.camera.updateProjectionMatrix();if(this.lastAspect===undefined||Math.abs(this.lastAspect-aspect)>.1)this.resetCamera();this.lastAspect=aspect;});this.resizeObserver.observe(this.q('.viewport'));
    this.heightObserver=new ResizeObserver(()=>{if(window.parent!==window)window.parent.postMessage({type:'ecosignal-terrain-height',height:Math.ceil(this.q('.app').getBoundingClientRect().height)},window.location.origin);});this.heightObserver.observe(this.q('.app'));
  }
  createGeometry(){
    const d=this.data,n=d.n,count=n*n,positions=new Float32Array(count*3),uv=new Float32Array(count*2),colors=new Float32Array(count*3);
    this.heightScale=1000/d.width_m;this.floor=d.display_min_m-3;
    this.indices=[];const edgeCounts=new Map();
    for(let row=0;row<n-1;row++)for(let col=0;col<n-1;col++){
      const a=row*n+col,b=a+1,c=a+n,e=c+1;
      if([a,b,c,e].every(i=>d.grids[2][i]!==null)){
        for(const triangle of [[a,c,b],[b,c,e]]){
          this.indices.push(...triangle);
          for(let j=0;j<3;j++){const i=triangle[j],k=triangle[(j+1)%3],key=i<k?`${i},${k}`:`${k},${i}`;edgeCounts.set(key,(edgeCounts.get(key)||0)+1);}
        }
      }
    }
    for(let i=0;i<count;i++){positions[i*3]=((i%n+.5)/n-.5)*1000;positions[i*3+2]=((Math.floor(i/n)+.5)/n-.5)*1000*d.height_m/d.width_m;uv[i*2]=d.uv[i][0];uv[i*2+1]=d.uv[i][1];}
    this.geometry=new THREE.BufferGeometry();this.geometry.setAttribute('position',new THREE.BufferAttribute(positions,3));this.geometry.setAttribute('uv',new THREE.BufferAttribute(uv,2));this.geometry.setAttribute('color',new THREE.BufferAttribute(colors,3));this.geometry.setIndex(this.indices);
    this.terrainMesh=new THREE.Mesh(this.geometry,new THREE.MeshStandardMaterial({vertexColors:true,roughness:1,metalness:0,side:THREE.DoubleSide}));
    this.scene.add(this.terrainMesh);
    this.riskMesh=new THREE.Mesh(this.geometry,new THREE.MeshBasicMaterial({transparent:true,opacity:.92,depthWrite:false,polygonOffset:true,polygonOffsetFactor:-1,polygonOffsetUnits:-1,side:THREE.DoubleSide}));this.riskMesh.visible=false;this.scene.add(this.riskMesh);
    this.boundaries=Array.from(edgeCounts).filter(([,c])=>c===1).map(([key])=>key.split(',').map(Number));
    this.skirtGeometry=new THREE.BufferGeometry();this.skirtGeometry.setAttribute('position',new THREE.BufferAttribute(new Float32Array(this.boundaries.length*18),3));
    this.skirt=new THREE.Mesh(this.skirtGeometry,new THREE.MeshStandardMaterial({color:0x153431,roughness:1,side:THREE.DoubleSide}));this.scene.add(this.skirt);
    const changes=[];
    for(let i=0;i<count;i++)if(d.grids[2][i]!==null)changes.push(Math.abs(d.grids[2][i]+16*d.projection.rate_m_per_year[i]-d.grids[0][i]));
    changes.sort((a,b)=>a-b);this.changeLimit=Math.max(.1,changes[Math.floor(changes.length*.98)]);
    this.raycaster=new THREE.Raycaster();this.pointer=new THREE.Vector2();
  }
  elevations(year){
    const index=this.data.years.indexOf(year);if(index>=0)return this.data.grids[index];
    return this.data.grids[2].map((z,i)=>z===null?null:z+(year-2024)*this.data.projection.rate_m_per_year[i]);
  }
  updateScene(){
    if(!this.geometry)return;
    const d=this.data,positions=this.geometry.attributes.position.array,colors=this.geometry.attributes.color.array;
    this.currentElevations=this.elevations(this.state.year);
    const a=new THREE.Color('#233f65'),b=new THREE.Color('#9ed9b2'),lower=new THREE.Color('#399bcc'),higher=new THREE.Color('#e5a46a'),neutral=new THREE.Color('#758e87');
    for(let i=0;i<d.n*d.n;i++){
      const z=this.currentElevations[i];positions[i*3+1]=z===null?0:(z-this.floor)*this.heightScale*this.state.exaggeration;
      if(this.state.surface==='risk')earth.set('#3c524b');
      else if(this.state.surface==='change'){
        const delta=z===null?0:z-d.grids[0][i];earth.copy(neutral).lerp(delta<0?lower:higher,clamp(Math.abs(delta)/this.changeLimit,0,1));
      }else earth.copy(a).lerp(b,clamp((z-d.display_min_m)/(d.display_max_m-d.display_min_m),0,1));
      earth.toArray(colors,i*3);
    }
    this.geometry.attributes.position.needsUpdate=true;this.geometry.attributes.color.needsUpdate=true;this.geometry.computeVertexNormals();this.geometry.computeBoundingSphere();
    const skirt=this.skirtGeometry.attributes.position.array;
    this.boundaries.forEach(([a,b],j)=>{const p=[positions[a*3],positions[a*3+1],positions[a*3+2]],q=[positions[b*3],positions[b*3+1],positions[b*3+2]],bottomP=[p[0],p[1]-18,p[2]],bottomQ=[q[0],q[1]-18,q[2]];[p,q,bottomP,q,bottomQ,bottomP].forEach((v,k)=>skirt.set(v,j*18+k*3));});
    this.skirtGeometry.attributes.position.needsUpdate=true;this.skirtGeometry.computeVertexNormals();this.skirtGeometry.computeBoundingSphere();
    this.riskMesh.visible=this.state.surface==='risk'&&Boolean(this.riskTexture);
    this.updateLabels();
  }
  setYear(year,{manual=true}={}){
    if(manual)this.stopPlay();this.state.year=allowedYears.reduce((a,b)=>Math.abs(b-year)<Math.abs(a-year)?b:a);this.updateScene();
    this.dispatchEvent(new CustomEvent('terrain-year-change',{detail:{year:this.state.year,kind:this.state.year>2024?'exploratory-projection':'observed-survey',riskReferenceYear:2024},bubbles:true,composed:true}));
  }
  updateLabels(){
    const {year,surface,exaggeration}=this.state,future=year>2024;
    this.q('[data-year]').textContent=year;this.q('[data-year-output]').value=year;this.q('#year').value=year;
    this.q('#year').setAttribute('aria-valuetext',`${year} ${future?'exploratory projection':'observed survey'}`);
    this.q('[data-badge]').textContent=future?'Exploratory projection':'Observed survey';this.q('[data-badge]').classList.toggle('future',future);
    this.q('.scenario-note').hidden=!future;this.q('[data-relief]').value=`×${exaggeration}`;this.q('#relief').value=exaggeration;this.q('#surface').value=surface;
    for(const button of this.shadowRoot.querySelectorAll('[data-jump]'))button.setAttribute('aria-pressed',String(Number(button.dataset.jump)===year));
    const label=surface==='risk'?'2024 GeoRisk reference':surface==='elevation'?'Terrain elevation':`${future?'Projected':'Measured'} difference from 2015`;
    this.q('[data-view-label]').textContent=label;
    this.q('[data-accessible-state]').textContent=`${year} ${future?'exploratory terrain projection':'observed terrain survey'}, ${label}, vertical exaggeration ${exaggeration} times.`;
    this.renderer.domElement.setAttribute('aria-label',this.q('[data-accessible-state]').textContent);
    if(surface==='risk'){
      this.q('[data-legend-name]').textContent='GEORISK · 2024 REFERENCE';this.q('[data-low]').textContent='0 · lower';this.q('[data-high]').textContent='1 · higher';
      this.q('[data-legend-note]').textContent='Relative susceptibility · not probability';
      this.q('[data-legend-bar]').style.background=`linear-gradient(to right,${this.data.palette.filter((_,i)=>i%16===0||i===255).map(rgb=>`rgb(${rgb.join(',')})`).join(',')})`;
    }else if(surface==='change'){
      this.q('[data-legend-name]').textContent=`${future?'PROJECTED':'MEASURED'} CHANGE FROM 2015`;
      this.q('[data-low]').textContent=`−${this.changeLimit.toFixed(1)} m`;this.q('[data-high]').textContent=`+${this.changeLimit.toFixed(1)} m`;
      this.q('[data-legend-note]').textContent='Lowering / raising · display colors clipped';this.q('[data-legend-bar]').style.background='linear-gradient(to right,#399bcc,#758e87,#e5a46a)';
    }else{
      this.q('[data-legend-name]').textContent=future?'PROJECTED ELEVATION':'MEASURED ELEVATION';this.q('[data-low]').textContent=`${Math.floor(this.data.display_min_m)} m`;this.q('[data-high]').textContent=`${Math.ceil(this.data.display_max_m)} m`;
      this.q('[data-legend-note]').textContent='Consistent scale across the timeline';this.q('[data-legend-bar]').style.background='linear-gradient(to right,#233f65,#9ed9b2)';
    }
    this.q('.tooltip').hidden=true;
  }
  wireControls(){
    this.q('#year').addEventListener('input',e=>this.setYear(Number(e.target.value)));
    this.q('#year').addEventListener('keydown',e=>{
      if(!['ArrowLeft','ArrowRight','ArrowDown','ArrowUp','Home','End'].includes(e.key))return;e.preventDefault();
      const index=allowedYears.indexOf(this.state.year),next=e.key==='Home'?allowedYears[0]:e.key==='End'?2040:allowedYears[clamp(index+(['ArrowRight','ArrowUp'].includes(e.key)?1:-1),0,allowedYears.length-1)];this.setYear(next);
    });
    this.shadowRoot.querySelectorAll('[data-jump]').forEach(button=>button.addEventListener('click',()=>this.setYear(Number(button.dataset.jump))));
    this.q('#surface').addEventListener('change',e=>{this.state.surface=e.target.value;this.updateScene();});
    this.q('#relief').addEventListener('input',e=>{this.state.exaggeration=Number(e.target.value);this.updateScene();});
    this.q('[data-fit]').addEventListener('click',()=>this.resetCamera());
    this.q('[data-reset]').addEventListener('click',()=>{this.stopPlay();this.state={year:2024,surface:'risk',exaggeration:40};this.updateScene();this.resetCamera();});
    this.q('[data-fullscreen]').addEventListener('click',async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await this.q('.app').requestFullscreen();}catch{this.q('[data-fullscreen]').textContent='Fullscreen unavailable';}});
    this.q('[data-play]').addEventListener('click',()=>{if(this.playing)this.stopPlay();else{this.playing=true;this.q('[data-play]').textContent='Pause timeline';if(this.state.year===2040)this.setYear(2015,{manual:false});this.playTimer=setInterval(()=>{const next=allowedYears[allowedYears.indexOf(this.state.year)+1];if(!next){this.stopPlay();return;}this.setYear(next,{manual:false});},matchMedia('(prefers-reduced-motion:reduce)').matches?1600:900);}});
    this.renderer.domElement.addEventListener('pointermove',e=>{if(e.buttons||!this.ready)return;this.showPoint(e);});
    this.renderer.domElement.addEventListener('pointerleave',()=>{this.q('.tooltip').hidden=true;});
    this.renderer.domElement.addEventListener('pointerup',e=>{if(e.pointerType==='touch'&&this.ready)this.showPoint(e);});
  }
  stopPlay(){clearInterval(this.playTimer);this.playing=false;if(this.q)this.q('[data-play]').textContent='Play timeline';}
  resetCamera(){const values=(this.currentElevations||this.data.grids[2]).filter(v=>v!==null).sort((a,b)=>a-b);const median=values[Math.floor(values.length/2)];const targetY=(median-(this.data.display_min_m-3))*1000/this.data.width_m*this.state.exaggeration;const factor=Math.max(1,1.5/this.camera.aspect);this.camera.position.set(780*factor,targetY+605*factor,960*factor);this.controls.target.set(0,targetY,0);this.controls.update();}
  showPoint(e){
    const rect=this.renderer.domElement.getBoundingClientRect();this.pointer.set((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1);this.raycaster.setFromCamera(this.pointer,this.camera);
    const hits=this.raycaster.intersectObject(this.terrainMesh);if(!hits.length){this.q('.tooltip').hidden=true;return;}
    const hit=hits[0],position=this.geometry.attributes.position;
    const index=[hit.face.a,hit.face.b,hit.face.c].reduce((best,i)=>new THREE.Vector3().fromBufferAttribute(position,i).distanceToSquared(hit.point)<new THREE.Vector3().fromBufferAttribute(position,best).distanceToSquared(hit.point)?i:best);
    const score=this.data.risk_display_scores[index];const tip=this.q('.tooltip');tip.replaceChildren();
    for(const text of [`${this.state.year>2024?'Projected':'Measured'} display elevation: ${this.currentElevations[index].toFixed(1)} m`,score===null?'No model score at this display point':`2024 display susceptibility: ≈${score.toFixed(2)}`,'Downsampled display—not a 1 m point query']){const line=document.createElement('div');line.textContent=text;tip.append(line);}tip.hidden=false;
  }
  fillNotes(){
    const d=this.data,m=this.metadata.temporal_spatial_holdout_2022_2024,h=d.projection.hindcast;
    this.q('[data-extent]').textContent=`${(d.width_m/1000).toFixed(1)} × ${(d.height_m/1000).toFixed(1)} km`;
    this.q('[data-resolution]').textContent=`Observed surfaces: 2015, 2022, 2024. The 1 m source DEMs are averaged onto a ${Math.round(d.display_cell_m[0])} × ${Math.round(d.display_cell_m[1])} m display mesh. The model texture is about 31 m per display pixel. The same common survey coverage is retained at every date.`;
    this.q('[data-hindcast]').textContent=`Projection check: using 2015–2022 trends to estimate 2024 gave average absolute error ${h.trend_mae_m.toFixed(3)} m; assuming no change gave ${h.no_change_mae_m.toFixed(3)} m. The trend did not outperform that baseline. These are coarse-cell averages, not guaranteed error bounds or evidence of accuracy through 2040.`;
    this.q('[data-metrics]').textContent=`GeoRisk independent holdout: ROC-AUC ${m.roc_auc.toFixed(3)}, average precision ${m.pr_auc.toFixed(3)}, precision ${(m.precision*100).toFixed(1)}%, recall ${(m.recall*100).toFixed(1)}%. Many flagged pixels are false positives. These statistics evaluate the susceptibility model, not the future elevation scenario.`;
    this.q('[data-model]').href=new URL(this.getAttribute('model-url')||'ecosignal_georisk_v2_1m.joblib',this.getAttribute('model-url')?document.baseURI:this.assetBase).href;
  }
  startRendering(){
    const north=new THREE.Vector3(),center=new THREE.Vector3();
    const tick=()=>{if(this.disposed)return;this.frame=requestAnimationFrame(tick);this.controls.update();this.renderer.render(this.scene,this.camera);
      center.set(0,0,0).project(this.camera);north.set(0,0,-150).project(this.camera);this.q('[data-compass]').style.transform=`rotate(${Math.atan2(north.x-center.x,north.y-center.y)*180/Math.PI}deg)`;};tick();
  }
  disconnectedCallback(){
    this.disposed=true;this.abort?.abort();this.stopPlay();cancelAnimationFrame(this.frame);this.resizeObserver?.disconnect();this.heightObserver?.disconnect();this.controls?.dispose();this.riskTexture?.dispose();this.geometry?.dispose();this.skirtGeometry?.dispose();
    this.scene?.traverse(obj=>{if(obj.material){for(const material of Array.isArray(obj.material)?obj.material:[obj.material])material.dispose();}if(obj===this.grid)obj.geometry.dispose();});this.renderer?.dispose();
  }
  debugSnapshot(){return {ready:this.ready,year:this.state.year,kind:this.state.year>2024?'exploratory-projection':'observed-survey',riskReferenceYear:2024,textureWidth:this.riskTexture?.image.width,textureHeight:this.riskTexture?.image.height,triangles:this.indices?.length/3,glError:this.renderer?.getContext().getError()};}
}
if(!customElements.get('ecosignal-terrain-viewer'))customElements.define('ecosignal-terrain-viewer',EcoSignalTerrainViewer);
