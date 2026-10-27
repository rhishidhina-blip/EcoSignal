export type ModelComponent = {
  status: 'available' | 'rejected_low_confidence' | 'failed' | 'unavailable';
  value?: { coverage_percent?: number; growth_form?: string; raw_prediction?: string; decision?: string } | null;
  confidence?: number;
  version: string;
  warnings?: string[];
};
export type PhotoAnalysis = {
  status: string;
  coverage: ModelComponent;
  growth_form: ModelComponent;
  media: { coverage_mask?: string; coverage_overlay?: string };
  warnings: string[];
  image_sha256: string;
  coverage_basis: string;
};

export function validateAnalysis(value: unknown): PhotoAnalysis {
  const j = value as PhotoAnalysis;
  if (!j || !j.coverage || !j.growth_form || !j.media || !Array.isArray(j.warnings) || j.warnings.some(w=>typeof w!=='string')) throw Error('Invalid analysis response');
  for (const c of [j.coverage, j.growth_form]) {
    if (!['available','rejected_low_confidence','failed','unavailable'].includes(c.status) || (typeof c.version !== 'string' || !c.version.trim())) throw Error('Invalid model status');
    if (c.confidence !== undefined && (!Number.isFinite(c.confidence) || c.confidence < 0 || c.confidence > 1)) throw Error('Invalid model confidence');
  }
  const coverage = j.coverage.value?.coverage_percent;
  if (coverage !== undefined && (!Number.isFinite(coverage) || coverage < 0 || coverage > 100)) throw Error('Invalid coverage');
  if (j.coverage.status === 'available' && coverage === undefined) throw Error('Coverage is missing');
  const form = j.growth_form.value?.growth_form;
  if (j.growth_form.status === 'available' && !['crustose','foliose','fruticose'].includes(form || '')) throw Error('Invalid growth form');
  for (const src of Object.values(j.media)) if (src && !/^data:image\/png;base64,[A-Za-z0-9+/=]+$/.test(src)) throw Error('Invalid image output');
  return {...j,coverage_basis:typeof j.coverage_basis==='string'?j.coverage_basis:'Visible coverage of the full analyzed photograph; not a pollution measurement.'};
}

export async function analyzePhoto(image: File, signal: AbortSignal): Promise<PhotoAnalysis> {
  const body = new FormData();
  body.append('image', image);
  const r = await fetch('/api/analyze', { method: 'POST', body, signal });
  const j:unknown = await r.json().catch(() => null);
  const detail=j&&typeof j==='object'&&'detail' in j&&typeof j.detail==='string'?j.detail:null;
  if (!r.ok) throw Error(detail || 'Photo analysis is unavailable. Please retry.');
  return validateAnalysis(j);
}

/** Rejected outputs remain raw evidence and never enter the screening inputs. */
export function acceptedPhotoFields(raw:PhotoAnalysis){return {coverage:raw.coverage.status==='available'?raw.coverage.value?.coverage_percent:undefined,form:raw.growth_form.status==='available'?raw.growth_form.value?.growth_form:undefined,coverage_confidence:raw.coverage.confidence,growth_form_confidence:raw.growth_form.confidence,mask:raw.media.coverage_mask,overlay:raw.media.coverage_overlay,model_version:raw.coverage.version+' / '+raw.growth_form.version,raw_model_output:raw};}
