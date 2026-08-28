#!/usr/bin/env node
import { readFile, rm, mkdir, writeFile } from 'node:fs/promises'
import { join } from 'node:path'


const root = process.cwd()
const registryPath = join(root, 'docs', 'reference', 'computations.json')
const provenancePath = join(root, 'docs', 'reference', 'provenance.json')
const generatedRoot = join(root, 'docs', '_generated', 'computations')
const githubBlob =
  'https://github.com/socraticsurge/telugu-calendar-utilities/blob/master/'

function list(items) {
  return items.map((item) => `- ${item}`).join('\n')
}

function numberedList(items) {
  return items.map((item, index) => `${index + 1}. ${item}`).join('\n')
}

function implementationList(implementations) {
  return implementations.map((implementation) => {
    const link = `${githubBlob}${implementation.path}`
    return `- **${implementation.role}:** [\`${implementation.path}\`](${link}) — \`${implementation.symbol}\``
  }).join('\n')
}

function testList(record) {
  if (!record.tests.length) return `- No linked regression test. Gap: ${record.test_gap}`
  return record.tests.map((test) => `- [\`${test}\`](${githubBlob}${test})`).join('\n')
}

function independentSupport(record) {
  const states = record.provenance.verification_states
  if (states.includes('engine_pinned') && !states.includes('verified')) {
    return 'Not independently verified at this level; current behavior is regression-pinned.'
  }
  if (states.includes('verified')) {
    return 'Available only for the explicitly named provenance claims or comparison cells.'
  }
  if (states.includes('partially_verified')) {
    return 'Partial support only; read the provenance note and limitations before generalizing.'
  }
  return 'Not recorded as independently verified. The disclosed provenance state remains authoritative.'
}

function renderFormulae(formulae = []) {
  if (!formulae.length) return ''
  return `### Formulae

${formulae.map((formula) => `#### ${formula.name}

\`\`\`text
${formula.expression}
\`\`\`

${list(formula.variables)}`).join('\n\n')}
`
}

function renderWorkedExamples(examples) {
  return `### Worked example

${examples.map((example) => `#### ${example.label}

**Inputs**

${list(example.inputs)}

**Calculation**

${numberedList(example.calculation)}

**Result**

${list(example.result)}`).join('\n\n')}
`
}

function renderMethod(record) {
  if (!record.method) {
    return `::: warning Method documentation incomplete
This record identifies the contract, implementation, tests and evidence state,
but its process, formula or decision logic and worked example have not yet been
documented. Treat this as an inventory page, not as a complete computation
explanation.
:::`
  }

  return `**Method type:** \`${record.method.kind}\`

${record.method.summary}

### Process

${numberedList(record.method.steps)}

${renderFormulae(record.method.formulae)}
${renderWorkedExamples(record.method.worked_examples)}
${record.method.notes ? `### Method notes\n\n${list(record.method.notes)}` : ''}`
}

function sourceList(claim, sourcesById) {
  if (!claim.source_ids.length) {
    return '- No external source is registered for this claim.'
  }
  return claim.source_ids.map((sourceId) => {
    const source = sourcesById.get(sourceId)
    if (!source) return `- Unresolved source ID: \`${sourceId}\``
    const details = [
      source.author,
      source.edition,
      `authority type: \`${source.authority_type}\``,
    ].filter(Boolean).join('; ')
    return `- [**${source.title}**](${source.url}) — ${details}`
  }).join('\n')
}

function renderClaims(record, claimsById, sourcesById) {
  if (!record.provenance.claim_ids.length) {
    return 'No registered claim ID; the provenance note below is the current disclosure.'
  }
  return record.provenance.claim_ids.map((claimId) => {
    const claim = claimsById.get(claimId)
    if (!claim) return `### \`${claimId}\`\n\nThe claim ID does not resolve in the provenance registry.`
    return `### \`${claim.id}\`

**Evidence class:** \`${claim.evidence_class}\`<br>
**Verification state:** \`${claim.verification_state}\`<br>
**Locator:** ${claim.locator || 'No precise locator is registered.'}<br>
${claim.last_reviewed ? `**Last reviewed:** ${claim.last_reviewed}<br>` : ''}
**Scope:** ${claim.scope}

#### Sources

${sourceList(claim, sourcesById)}`
  }).join('\n\n')
}

function render(record, claimsById, sourcesById) {
  const documentationStatement = record.method
    ? 'Yes — the canonical record includes the process and a worked example.'
    : 'Incomplete — the contract is inventoried, but the process and worked example are missing.'
  return `---
title: ${JSON.stringify(record.title)}
description: ${JSON.stringify(record.summary)}
editLink: false
---

# ${record.title}

<code class="computation-route-id">${record.id}</code>

${record.summary}

## Assurance

| Level | Current statement |
|---|---|
| Documented and traceable | ${documentationStatement} |
| Regression or reproduction checked | ${record.tests.length ? `Linked to ${record.tests.length} repository test file(s).` : 'No linked test; the visible test gap applies.'} |
| Independently source-supported | ${independentSupport(record)} |

## Computation method

${renderMethod(record)}

## Contract

**Owning layer:** \`${record.owning_layer}\`<br>
**Claim kind:** \`${record.claim_kind}\`<br>
**Time basis:** ${record.time_basis}

### Inputs

${list(record.inputs)}

### Outputs

${list(record.outputs)}

## References and evidence

**Evidence classes:** ${record.provenance.evidence_classes.map((value) => `\`${value}\``).join(', ')}<br>
**Verification states:** ${record.provenance.verification_states.map((value) => `\`${value}\``).join(', ')}<br>

${record.provenance.note}

${renderClaims(record, claimsById, sourcesById)}

The complete machine-readable source registry is available in
[\`provenance.json\`](/reference/provenance.json). A regression fixture or
same-code reproduction is not independent verification.

## Reproduce and review

${testList(record)}

Run the linked tests, then the complete offline contract:

\`\`\`bash
python tools/verify_project.py
\`\`\`

## Public surfaces

${list(record.surfaces.map((surface) => `\`${surface}\``))}

## Limitations

${list(record.limitations)}

## Implementation

${implementationList(record.implementations)}

This route is generated from [\`computations.json\`](/reference/computations.json).
Edit the registry and canonical reference prose in the same pull request as a
behavior change.
`
}

const registry = JSON.parse(await readFile(registryPath, 'utf8'))
const provenance = JSON.parse(await readFile(provenancePath, 'utf8'))
const claimsById = new Map(provenance.claims.map((claim) => [claim.id, claim]))
const sourcesById = new Map(provenance.sources.map((source) => [source.id, source]))
await rm(generatedRoot, { recursive: true, force: true })
await mkdir(generatedRoot, { recursive: true })

for (const record of registry.computations) {
  await writeFile(
    join(generatedRoot, `${record.id}.md`),
    render(record, claimsById, sourcesById),
    'utf8',
  )
}

console.log(
  `Generated ${registry.computations.length} searchable computation source pages.`,
)
