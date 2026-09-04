# Gold chart-screening review evidence

This directory is the current deterministic visual release record for the
Gold / Jewelry election-chart assessor. It preserves the earlier August 29
matrix separately rather than overwriting historical evidence.

The six Gold captures exercise pass, conclusive condition miss with a `Good`
rating cap, and fail-closed unknown at both 1440×900 and 390×844. The wider
15-image matrix also retains the generic positive, mixed, mandatory-failure,
unsupported-system, offline, malformed-response, loading, and timeout states.
All routes use the same built application and strict response fixtures as the
browser suite; no live service or credential is used.

`fixture-manifest.json` records every activity, state, viewport, expected copy,
and PNG SHA-256. Recreate it from a production build:

```bash
python tools/capture_muhurta_chart_screenshots.py --dist dist
```

Owner acceptance, PR merge, and deployment remain separate release gates.
