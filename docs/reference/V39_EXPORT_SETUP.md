# EcoSignal — GitHub source export

Exported October 26, 2026 from published website version **39**, source commit
`e91366006e0f3a20992163d41eea143abaa75ef9`.

This is the latest website source, including the unified score and scale,
coordinate-based AirNow connection, map indices and GeoRisk data, photo analysis
proxy, image attachments, planner, review workspace, and observation reset button.
Application code and bundled datasets are unchanged. `EXPORT-MANIFEST.json`
records the original file hashes. This document, environment examples, README,
and ignore-file additions are export documentation only.

## Upload to GitHub

1. Download and extract this ZIP. Open the extracted `ecosignal-github` folder in
   VS Code or a terminal. Do not upload the ZIP itself as the repository source.
2. Create an **empty** repository on GitHub; leave its README and license options
   unchecked. Use a private repository if you do not intend to publish these assets.
3. In the extracted folder, run:

```bash
git init -b main
git add .
git status --short
git commit -m "Import EcoSignal website version 39"
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin main
```

Replace the username and repository name. Use Git rather than GitHub's browser
upload for this large asset collection. No individual file exceeds 100 MB.
If adding this export to an existing repository, create a new branch first and
review the diff; do not force-push or overwrite its history.

## Run locally

Use Node.js **22.13 or newer** and a Linux terminal (GitHub Codespaces or WSL on
Windows). The provided build helpers require Bash, GNU timeout, flock, curl, and
sha256sum.

```bash
npm run install:ci
cp .dev.vars.example .dev.vars
npm run dev
```

Edit `.dev.vars` privately and enter the existing backend tokens. The terminal
prints the development URL. In Codespaces, forward the port printed by Vite;
this frontend port is separate from the photo-analysis backend's port 8001.
The `.dev.vars` file configures the Cloudflare Worker development environment.
`.env.example` is an additional reference for host configuration; a generic
`.env` alone is not a substitute for Worker bindings and runtime secrets.

```bash
npm run build
node --test tests/*.test.mjs
```

The original published revision previously passed its production build and all
167 tests. This export was verified against the source hashes and ZIP integrity;
dependencies were not reinstalled and runtime tests were not rerun for this export.

## Backend configuration

- **Photo analysis:** `ECOSIGNAL_ANALYSIS_URL` is the backend base URL, without
  `/health` or an inference path. `ECOSIGNAL_ANALYSIS_TOKEN` must match the backend
  API token. The Codespace and backend process must remain running.
- **Ask LichenLens:** `ECOSIGNAL_CHATBOT_URL` is the full `/assistant/ask` URL.
  Set `ECOSIGNAL_CHATBOT_TOKEN` only if that backend requires it. The Render
  service's Gemini API key and model are configured on Render, separately.
- **Direct Gemini path:** optional `GEMINI_API_KEY` / `GEMINI_MODEL` are for the
  website's direct provider path. Leave them empty when retaining the Render path.
- **Planner:** optional `ECOSIGNAL_PLANNER_URL` / `ECOSIGNAL_PLANNER_TOKEN` are for
  an existing remote planner. Without both, the current evidence-workspace path
  remains in use and needs the database and authenticated hosting below.
- **AQI:** the current AirNow implementation does not read an AirNow key variable.
  It requires outbound access to its existing public data sources.

Never commit real token files, paste tokens into client-side source, or use
`NEXT_PUBLIC_` / `VITE_` variables for these server secrets. Templates intentionally
contain no credentials. Committing code does not copy or persist host settings.

## Hosting and saved research data

This is a **full-stack Cloudflare Worker/Vinext application**, not a static
GitHub Pages website. GitHub stores the code; it does not run the APIs or backend
services. The existing ChatGPT Site remains unchanged by this export.

The source preserves `.openai/hosting.json`, the Sites build integration, and
the `DB` (D1) / `BUCKET` (R2) binding names. The current platform also supplies
trusted ChatGPT identity headers. Saving observations, research workspace writes,
stored photo access, and the workspace planner depend on these services.

Deploying to a different host requires provisioning equivalent storage,
applying the included database migrations, setting runtime secrets, and providing
a trusted authentication integration. Identity headers must be supplied by a
trusted gateway, not accepted from arbitrary internet clients. Those services
are not created merely by pushing to GitHub. Keep the current Site hosting if
the goal is simply a source backup with all existing functionality intact.

Live database records, uploaded photos, browser-local observations, runtime
secrets, dependency directories, Git history, and generated build output are
not included. Bundled scientific assets and the existing source-checkpoint parts
are included because the website references them. Date, coordinate coverage,
quality, and freshness gates continue to apply to the unified score.

The `integrations/ask-lichenlens-render` folder is the integration package present
in this website revision; it is not an export of the live Render service's
repository or configuration. Its historical notes do not override your working
Render model settings.
