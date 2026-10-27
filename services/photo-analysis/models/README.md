# Photo model artifacts

The adapters require the exact trained model artifacts below. Both exact Keras files are included in this showcase. Existing source/model repository: https://github.com/rhishidhina-blip/ecosignal-photo-analysis . Verify hashes before inference; older repository code may use the historical coverage adapter, so this showcase's supplied Keras replacement remains separately documented.

| Filename required by adapter | Bytes | SHA-256 |
|---|---:|---|
| `lichen_coverage_v2.keras` | 68084295 | `0496f79a349de607d43f6e3db3f05fe542e7d76ee13e46bf7b352feae7db3133` |
| `growthform_effnet_filtered_highacc.keras` | 29072841 | `e8a1bc9033e9f0eada2aaf756abc15a73adf1e60ab082cf38b39f1314290e077` |

Both exact files were verified locally during recovery. Do not substitute a same-named file with another hash. The Python service requires its runtime dependencies and private API token to perform inference. The coverage threshold is 0.65; the historical evaluated 0.55 checkpoint is a different artifact.
