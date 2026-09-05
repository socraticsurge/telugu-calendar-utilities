# Annaprasana chart-assessor review evidence

This directory is the deterministic visual release record for the
Annaprasana event-specific election-chart assessor. The nine captures cover
the four materially different outcomes at 1440×900 and 390×844:

- all mandatory clauses pass and the source preference is present;
- the source preference is absent without removing or penalizing the slot;
- a mandatory clause fails and the slot is removed, with evidence retained;
- a phase-boundary fact is unknown and the retained slot is capped for review.

The fixtures exercise the built application without a live service or
credential. The mobile pass has two deliberately framed captures: one shows
the event-specific completion title, and the other shows the final Lagna
preference and natural-malefic outcomes together. `fixture-manifest.json`
records the scenario, viewport, expected state/copy, and PNG SHA-256; the
evidence test also requires all nine images to be content-distinct.

The six event clauses are transcribed from B. V. Raman, Chapter VIII, “First
feeding on rice (Annaprasana),” inspected in the 2020 Chistabo derivative at
internal printed p. 22 (physical PDF p. 25). Product conventions and the Iyer / *Muhurta Chintamani*
source differences are documented separately in the method reference; these
screenshots do not claim that the open general election-chart baseline #284 is
complete.

Recreate the matrix from a production build:

```bash
python tools/capture_muhurta_chart_screenshots.py --dist dist --annaprasana-only
```

Owner acceptance, PR merge, and deployment remain separate release gates.
