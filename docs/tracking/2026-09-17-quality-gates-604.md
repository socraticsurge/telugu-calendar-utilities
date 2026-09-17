# Dual quality-gate enforcement

Task: [#604](https://github.com/socraticsurge/telugu-calendar-utilities/issues/604).

## Scope and authority

The owner approved completing this bounded workflow/configuration task.
No production calculation, engine, feed format, UI or existing test assertion changes.
All deployment workflows and their CNAME remain untouched.

## Verified starting state

- Master required seven test/security contexts, strict up-to-date branches and administrator enforcement.
- Sonar and CodeScene integrations already ran but neither was required for merge.
- Sonar automatic analysis reported no coverage and warned about unspecified Python versions and test classification.
- The current master report has only those two warnings; the earlier encoding warning is not currently reproduced.
- Python's declared floor is 3.10; CI exercises 3.10, 3.11, 3.12 and 3.13; analysis names that tested range.
- The Free plan cannot assign a custom quality gate; the built-in gate permits some new maintainability issues within its A rating.

## Implementation

Preserve the seven existing required checks and add app-pinned CodeScene and Sonar checks.
Require `Sonar analysis` from GitHub Actions for the supplementary zero-new-issues check.
Only Python 3.11 produces Cobertura branch coverage; all four runtime test lanes remain.
Vitest adds LCOV without changing source scope or absolute uncovered-code caps.
Same-run, named artifacts connect successful tests to a separate fresh scanner runner.
Missing artifacts fail; no cross-run artifact lookup or `pull_request_target` execution is used.
Only the pinned official Sonar action receives `SONAR_TOKEN`; repository tests and dependency installation do not.
Sonar waits for its built-in gate, then a credential-free public-metrics query requires zero new issues for that PR.
HTTP errors, missing metrics, wrong PR identity and nonzero issues fail the supplementary check.
The public PR analysis metadata must also identify the current PR-head SHA; stale or missing revisions fail.
That same response must show an OK gate and zero bugs, vulnerabilities and code smells.
Push and PR scanner jobs have distinct check names, so a skipped push cannot stand in for the PR gate.
Python XML retains repository-relative file paths, including distinct package initializer paths.
Fork PRs receive no token and cannot pass the required analysis; inspect them before moving approved changes to an owned branch.

`sonar.sources=.` retains repository-wide scope; Python and TypeScript test trees are explicitly classified.
UTF-8 is explicit; no issue exclusions, coverage exclusions, relaxed thresholds or finding dismissals are introduced.
The built-in small-change exception for coverage/duplication remains visible; existing local coverage caps still apply to every change.

## Release checklist

1. Record exact base/head, approved scope and immutable review evidence.
2. Pass unchanged behavior tests, supported Python versions, browser tests and frontend coverage caps.
3. Inspect CodeScene findings and changed-file coverage, not just its badge.
4. Inspect Sonar findings, imported coverage and scanner warnings; zero new issues is mandatory.
5. Validate any claimed false positive with a reproducible attack/control pair and explicit owner approval.
6. Prove both required quality integrations block a controlled, unmerged bad PR; then remove the probe.
7. Independently review credential boundaries and configuration changes before the gated merge.
8. Verify merged source identity, post-merge CI and hosted analysis; close the task only after evidence is recorded.

## References

- [Sonar GitHub Actions setup](https://docs.sonarsource.com/sonarqube-cloud/analyzing-source-code/ci-based-analysis/github-actions-for-sonarcloud).
- [Python coverage import](https://docs.sonarsource.com/sonarqube-cloud/analyzing-source-code/test-coverage/python-test-coverage).
- [Quality-gate conditions and small-change exception](https://docs.sonarsource.com/sonarqube-cloud/standards/managing-quality-gates/introduction-to-quality-gates).

## Completion evidence

The initial implementation merged in [PR #605](https://github.com/socraticsurge/telugu-calendar-utilities/pull/605).
Its clean PR and deliberately unmerged negative control proved the required checks enforce the intended policy.
[Release evidence](https://github.com/socraticsurge/telugu-calendar-utilities/issues/604#issuecomment-5712244979) records the exact revisions and results.
Post-merge master coverage was 79.2819%, below the unchanged 80% new-code requirement.
The master baseline covers code since August 13, unlike the narrower PR analysis.
Task #604 remains open until the follow-up passes hosted post-merge acceptance.

## Coverage acceptance follow-up

Add 107 regression cases in three new test modules; existing assertions and production files are unchanged.
Exercise malformed inventory evidence, missing implementation/test links, invalid exclusions, scan failures, baseline drift, and explicit update behavior.
Temporary fixture paths isolate all baseline writes from the repository's governed baselines.
The targeted run passes 139 tests, including existing validator contracts.
The full local Python suite passes 2,331 tests; frontend coverage tests pass all 1,733 cases.
Combined line/branch coverage of the three validators is approximately 99%; each retains only its script-entry line and branch as uncovered.
CodeScene's pre-commit safeguard checks all three new files and passes without findings.

Master's measured denominator is 19,162 new lines plus conditions, with 3,970 uncovered.
The three validators previously contributed 185 uncovered lines and 103 uncovered conditions.
The targeted tests reduce those to three lines and three conditions, projecting master coverage near 80.75% if other results remain unchanged.
This is a pre-merge estimate, not a substitute for the hosted post-merge result.
No coverage threshold, baseline date, source exclusion, or issue disposition is changed.
