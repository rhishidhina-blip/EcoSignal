# Evidence/planner integration — software verification

Validation scope: code and runtime contracts. The human explicitly owns interactive/visual user testing.

- TypeScript: `./node_modules/.bin/tsc --noEmit` — passed.
- All current tests: `node --test --test-concurrency=2 tests/*.test.mjs` — 129 passed, 0 failed on the finalized implementation (104 existing + 25 added).
- New workflow checks use an isolated Miniflare D1/R2 database, never the production Site: record/prediction persistence; immutable original values; independent review; two-person mask approval; withdrawal/terminal checks; revision conflict rollback; concurrent hash-chain writes; split isolation with an actual SQL rollback; frozen manifests; all four export formats and hashes; file storage/deduplication; quality linkage; retake blocking; stable queues; no seeded planner candidates; numerical-priority adaptation on synthetic inputs; strict stale/future/location handling.
- The pinned real OpenCV WebAssembly build was executed on synthetic matrices. ORB, CLAHE, matching, RANSAC and homography alignment are available. An identical textured pair passes, a blank pair requests a retake. This is not browser visual QA or observed-field validation.
- Existing regression checks cover AirNow contracts, chatbot grounded/fallback modes, native satellite sampling, all 24 real numerical terrain fixtures/fixed reference, 3D hashes/timeline/2024 colors, exports and unified scoring gates. The existing features remain in the same source.
- Build: native Sites `build-site.mjs` completed and validated the ESM Worker artifact on the finalized implementation. Final packaging rebuilds the refreshed source-checkpoint assets.

## Not performed / not claimed

- Human interactive, camera, mobile-layout and visual testing: left to the user.
- Real candidate import and observed-data planner adaptation: pending the real Render backend ZIP; the attached Sites adapter has no candidate pool. Missing data yields an explicit status, not examples.
- New real lichen inference/accuracy assessment: no photographs or independently labelled field targets were supplied for this update. Existing external analysis configuration is preserved.
- A second real reviewer is not added, simulated or authorized by this update. Current audience is preserved, so independent review may remain pending until the owner explicitly authorizes another real reviewer.
- Exact historical coverage MAE is not assumed to match the live artifact. Uncertainty-aware repeat change requires explicit verified model matching; unknown dates and rejected comparisons stay unavailable.
- Independent scientific validation, observed ablations/sensitivity and weight optimization: not run. Synthetic tests verify software, not environmental accuracy.

No production data are seeded; SQL migrations contain schema only. Runtime secrets, device observations, notebook output images, local test databases and node_modules are excluded from source checkpoints.
