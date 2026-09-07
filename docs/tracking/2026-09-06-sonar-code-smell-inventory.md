# Sonar code-smell inventory

- Master commit: `539f294cc8a788056b897363907adcec66234843`
- Inventory date: `2026-09-06`
- Open code smells: **455**
- Files represented: **81**
- Sonar rules represented: **48**
- Findings on Ruff-baseline files: **18**
- Findings on complexity-baseline files: **74**
- Findings on both baseline file sets: **14**

Source: SonarCloud `api/issues/search` for project
`socraticsurge_telugu-calendar-utilities`, branch `master`, type `CODE_SMELL`,
open/confirmed statuses, page size 500; retrieved on the inventory date.

The overlap fields are file-level guardrails. They do not claim that a Sonar rule
and a Ruff rule describe the same source construct.

Each CSV row records the immutable Sonar issue key, rule, severity, repository
path and line, creation date, age in days, matching Ruff debt on that file,
matching C901 hotspot names and scores, and the working-agreement scope.

### Severity reconciliation

| Value | Findings |
| --- | ---: |
| `MAJOR` | 221 |
| `CRITICAL` | 125 |
| `MINOR` | 109 |

The 125 Critical findings use only three rules: `python:S1192` (52 duplicated
literal findings), `python:S3776` (39 cognitive-complexity findings), and
`typescript:S3776` (34 cognitive-complexity findings).

### Working-agreement scope

| Value | Findings |
| --- | ---: |
| `mutable` | 447 |
| `frozen-engine` | 6 |
| `frozen-ics` | 2 |

Of the Critical findings, 122 are in mutable scope. Two are in
`telugu_panchangam/engines/base.py` and one is in
`telugu_panchangam/generators/ics.py`; those three remain approval-gated under
the working agreement and are not candidates for routine cleanup.

### Largest mutable Critical groups

| File | Rule | Findings |
| --- | --- | ---: |
| `telugu_panchangam/personal/activity_rules.py` | `python:S1192` | 16 |
| `telugu_panchangam/personal/election_chart_rules.py` | `python:S1192` | 10 |
| `src/panels/tarabalam.ts` | `typescript:S3776` | 9 |
| `tools/export_muhurtam_rule_crosswalk.py` | `python:S1192` | 9 |
| `src/panels/profiles.ts` | `typescript:S3776` | 5 |
| `telugu_panchangam/mcp/tools.py` | `python:S1192` | 4 |
| `telugu_panchangam/personal/muhurta.py` | `python:S3776` | 4 |
| `tools/check_computation_inventory.py` | `python:S3776` | 4 |
| `src/lib/guest-profile-store.ts` | `typescript:S3776` | 3 |
| `src/panels/gochara.ts` | `typescript:S3776` | 3 |
| `src/panels/today.ts` | `typescript:S3776` | 3 |
| `telugu_panchangam/mcp/tools.py` | `python:S3776` | 3 |
| `telugu_panchangam/personal/election_assessors/primitives.py` | `python:S3776` | 3 |
| `telugu_panchangam/personal/election_chart.py` | `python:S3776` | 3 |
| `tools/analyze_computation_architecture.py` | `python:S3776` | 3 |

## Triage decision

The next implementation batch is the two `python:S1192` findings in
`tools/capture_muhurta_chart_screenshots.py`:

- repeated `Panchangam shortlist shown` copy;
- repeated `#mu-result` selector.

This is the smallest high-confidence Critical group: mutable review tooling,
no Ruff or complexity-baseline overlap, no calculation or feed behavior, and
existing browser and screenshot-evidence coverage. The larger rule tables and
complexity groups remain queued until each gets its own behavior boundary and
test review.

## Reproduce

The exporter is offline by design. Save the complete Sonar API response outside
the repository, then run:

```console
python tools/export_sonar_inventory.py SONAR_RESPONSE.json \
  --as-of 2026-09-06 \
  --output docs/tracking/2026-09-06-sonar-code-smell-inventory.csv
```

The Markdown triage is reviewed analysis tied to the commit above; regenerating
the CSV does not overwrite that judgment.
