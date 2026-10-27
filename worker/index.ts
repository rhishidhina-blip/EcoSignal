/** Cloudflare Worker entry point for the vinext-starter template. */
import { handleImageOptimization, DEFAULT_DEVICE_SIZES, DEFAULT_IMAGE_SIZES } from "vinext/server/image-optimization";
import handler from "vinext/server/app-router-entry";
import { handleAsk } from '../app/lib/assistant';
import {handleAirQuality} from '../app/lib/air-quality';
import {handlePlanner} from '../app/lib/planner-proxy';
import {handleEvidence} from '../app/lib/evidence-api';
import {handlePhotoAnalysis} from '../app/lib/photo-analysis-proxy';

interface Env {
  BUCKET: R2Bucket;
  ECOSIGNAL_PLANNER_URL?:string;
  ECOSIGNAL_PLANNER_TOKEN?:string;
  ECOSIGNAL_ANALYSIS_URL?: string;
  ECOSIGNAL_ANALYSIS_TOKEN?: string;
  GEMINI_API_KEY?: string;
  GEMINI_MODEL?: string;
  ECOSIGNAL_CHATBOT_URL?: string;
  ECOSIGNAL_CHATBOT_TOKEN?: string;
  ASSETS: Fetcher;
  DB: D1Database;
  IMAGES: {
    input(stream: ReadableStream): {
      transform(options: Record<string, unknown>): {
        output(options: { format: string; quality: number }): Promise<{ response(): Response }>;
      };
    };
  };
}

interface ExecutionContext {
  waitUntil(promise: Promise<unknown>): void;
  passThroughOnException(): void;
}

// Image security config. SVG sources with .svg extension auto-skip the
// optimization endpoint on the client side (served directly, no proxy).
// To route SVGs through the optimizer (with security headers), set
// dangerouslyAllowSVG: true in next.config.js and uncomment below:
// const imageConfig: ImageConfig = { dangerouslyAllowSVG: true };

const worker = {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    if (url.pathname === '/api/ask') return handleAsk(request, env);
    if (url.pathname === '/api/air-quality') return handleAirQuality(request);
    if (url.pathname.startsWith('/api/workspace/')) return handleEvidence(request,env);
    if (url.pathname === '/api/sampling/recommend') {
      if(env.ECOSIGNAL_PLANNER_URL && env.ECOSIGNAL_PLANNER_TOKEN) return handlePlanner(request,env);
      return handleEvidence(new Request(new URL('/api/workspace/planner/recommend',request.url),request),env);
    }
    if (url.pathname === '/api/analyze') return handlePhotoAnalysis(request, env);

    if (url.pathname === "/_vinext/image") {
      const allowedWidths = [...DEFAULT_DEVICE_SIZES, ...DEFAULT_IMAGE_SIZES];
      return handleImageOptimization(request, {
        fetchAsset: (path) => env.ASSETS.fetch(new Request(new URL(path, request.url))),
        transformImage: async (body, { width, format, quality }) => {
          const result = await env.IMAGES.input(body).transform(width > 0 ? { width } : {}).output({ format, quality });
          return result.response();
        },
      }, allowedWidths);
    }

    return handler.fetch(request, env, ctx);
  },
};

export default worker;
