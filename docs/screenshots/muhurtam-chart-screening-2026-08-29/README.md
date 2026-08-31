# Muhurtam chart-screening review evidence

This directory contains two kinds of local-only review evidence:

- `live-screened-purchase-desktop-final.png` records the real three-service
  local stack using the DashaFlow sidecar, Astro guest gateway, and TCU site.
- `fixture-*.png` records deterministic built-browser states. These captures
  reuse the same golden feed, Lagna, chart, degraded-service, and privacy
  fixtures exercised by `tests/test_browser_smoke.py`; no live service is
  called.

`fixture-manifest.json` records the scenario, activity, system, viewport,
expected state/copy, and SHA-256 for every deterministic image. Identical safe
fallback screens remain attributable to their offline, timeout, or malformed
response trigger through that manifest.

Recreate the fixture matrix from a local production build:

```bash
python tools/capture_muhurta_chart_screenshots.py --dist dist
```

The matrix covers positive desktop/mobile, computed unknown at tablet width,
mandatory failure, manual-only, unsupported-system tablet landscape, offline,
malformed response, the real loading phase, and the 20-second client timeout.
