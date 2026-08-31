---
title: Panchangam reference
description: Methods, evidence, verification and limitations for every documented computation.
aside: false
---

# Panchangam, explained

Use this reference to move from a value on the Panchangam site to its method,
evidence, tests, and limitations. The source is maintained beside the code; this
site is a searchable projection, not a second documentation store.

<div class="reference-intro">
  <strong>Looking for one result?</strong>
  Open <a href="./computations/">Browse all computations</a> and filter by a
  familiar name such as Tithi, Rahu Kalam, Tarabalam, or Gochara.
</div>

## Choose a path

<div class="reference-paths">
  <div class="reference-path">
    <strong>Understand a calculation</strong>
    <p>Start with the <a href="./reference/02-engines-and-model">three engines</a>
    or the <a href="./reference/03-computational-features">derived computations</a>.
    Each page states inputs, method, time basis, outputs, and boundaries.</p>
  </div>
  <div class="reference-path">
    <strong>Check the evidence</strong>
    <p>Read <a href="./reference/08-provenance-and-authority">provenance and
    authority</a> before interpreting “verified.” Textual sources, external
    comparisons, regression fixtures, and heuristics are deliberately separate.</p>
  </div>
  <div class="reference-path">
    <strong>Trace code and tests</strong>
    <p>The <a href="./reference/09-computation-inventory">computation inventory</a>
    links stable IDs to owning symbols, mirrors, tests, surfaces, evidence states,
    and limitations.</p>
  </div>
  <div class="reference-path">
    <strong>Verify a birth profile</strong>
    <p>Follow the exact inputs, Moon-longitude formulas, Lahiri and Whole Sign
    conventions, D1 chart projection, privacy boundary, reproduction fixtures,
    and public-release gates in <a href="./reference/53-birth-profile-calculation">Birth
    profiles and the D1 chart</a>.</p>
  </div>
  <div class="reference-path">
    <strong>Contribute safely</strong>
    <p>Follow the <a href="./reference/10-computation-contributor-workflow">safe
    computation workflow</a> to choose an additive owner and recognize the
    frozen-core, UI, release, and publication approval gates.</p>
  </div>
</div>

## What the assurance labels mean

<div class="assurance-key">
  <div>
    <strong>Documented and traceable</strong>
    <span>The owner, method, inputs, outputs, evidence state, tests, and limits are disclosed.</span>
  </div>
  <div>
    <strong>Regression or reproduction checked</strong>
    <span>A repeatable check protects or reproduces behavior. It may still use the same implementation.</span>
  </div>
  <div>
    <strong>Independently source-supported</strong>
    <span>Only the explicitly named claim or result cells have an inspected source or external comparison.</span>
  </div>
</div>

Re-fetching the same published result is reproduction, not independent
verification. A page can legitimately contain claims at more than one assurance
level.

## Current scope

The public projection includes maintained computation references, provenance,
contributor guidance, selected architecture decisions, and the Pages-retention
contract. Historical plans, specifications, tracking files, generated calendar
data, and ignored runtime output are excluded from navigation and search.
