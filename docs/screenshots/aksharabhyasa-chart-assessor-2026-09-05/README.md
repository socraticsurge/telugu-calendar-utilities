# Aksharabhyasa chart-assessor review evidence

This directory is the deterministic visual review record for the partial,
provisional Aksharabhyasa (First-letter writing) election-chart assessor. The
stable compatibility/API activity id remains `vidyarambha`.

The ten captures first show the canonical pre-search activity label and then
exercise four distinct outcomes at 1440×900 and 390×844:

- selector: the visible choice is **Aksharabhyasa (First-letter writing)**
  while the compatibility identifier remains `vidyarambha`;
- pass: the eighth house is vacant and Budha, Shukra, and Guru are all in the
  ninth house;
- preference miss: the eighth house is vacant, but the three-planet
  co-location preference is absent and causes no penalty;
- hard fail: an eighth-house occupant removes the candidate regardless of the
  preference;
- unknown: the preference changes across sampled chart boundaries, so it is
  shown as unresolved and cannot improve the ranking.

All captures use the same built application and strict response fixtures as
the browser suite. No live service, credential, or mutable ephemeris response
is used. `fixture-manifest.json` records each state, viewport, expected copy,
and PNG SHA-256.

Recreate this review matrix from a production build:

```bash
python tools/capture_muhurta_chart_screenshots.py \
  --dist dist --aksharabhyasa-only
```

These files provide review evidence only. Owner acceptance, restacking after
the planned v1.17.0 release, PR merge, and deployment remain separate gates.
