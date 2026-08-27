# Historical spec-harness guidelines

This file records the Phase 2 setup of the retired CSV/hook-driven planning
harness. It is preserved for context and is not an active contributor guide.

Use these current sources instead:

- `AGENTS.md` for the frozen-core working agreement;
- [`CONTRIBUTING.md`](../CONTRIBUTING.md) for setup, tests and pull requests;
- `pyproject.toml` for Python dependency declarations;
- the [Telugu Calendar Utilities GitHub Project](https://github.com/users/socraticsurge/projects/2)
  and [repository Issues](https://github.com/socraticsurge/telugu-calendar-utilities/issues)
  for current work and decisions.

## Retired workflow snapshot

The old harness created `.venv/`, ran `.venv/bin/pytest`, rolled completed
tasks into `STORIES.csv`, and logged dependency decisions in
`docs/tracking/DECISIONS.md`. Those tracker actions no longer govern this
repository. The CSVs and decision log remain historical evidence only.
