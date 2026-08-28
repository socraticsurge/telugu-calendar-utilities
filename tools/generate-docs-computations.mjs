#!/usr/bin/env node
import { readFile, rm, mkdir, writeFile } from 'node:fs/promises'
import { join } from 'node:path'


const root = process.cwd()
const registryPath = join(root, 'docs', 'reference', 'computations.json')
const generatedRoot = join(root, 'docs', '_generated', 'computations')
const githubBlob =
  'https://github.com/socraticsurge/telugu-calendar-utilities/blob/master/'

function list(items) {
  return items.map((item) => `- ${item}`).join('\n')
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

function render(record) {
  const claims = record.provenance.claim_ids.length
    ? record.provenance.claim_ids.map((claim) => `\`${claim}\``).join(', ')
    : 'No registered claim ID; see the provenance note.'
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
| Documented and traceable | Yes — this page is generated from the canonical computation record. |
| Regression or reproduction checked | ${record.tests.length ? `Linked to ${record.tests.length} repository test file(s).` : 'No linked test; the visible test gap applies.'} |
| Independently source-supported | ${independentSupport(record)} |

## Method contract

**Owning layer:** \`${record.owning_layer}\`<br>
**Claim kind:** \`${record.claim_kind}\`<br>
**Time basis:** ${record.time_basis}

### Inputs

${list(record.inputs)}

### Outputs

${list(record.outputs)}

## Evidence

**Evidence classes:** ${record.provenance.evidence_classes.map((value) => `\`${value}\``).join(', ')}<br>
**Verification states:** ${record.provenance.verification_states.map((value) => `\`${value}\``).join(', ')}<br>
**Provenance claims:** ${claims}

${record.provenance.note}

The detailed source registry is available in
[\`provenance.json\`](/reference/provenance.json). A regression fixture or
same-code reproduction must not be read as independent verification.

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
await rm(generatedRoot, { recursive: true, force: true })
await mkdir(generatedRoot, { recursive: true })

for (const record of registry.computations) {
  await writeFile(join(generatedRoot, `${record.id}.md`), render(record), 'utf8')
}

console.log(
  `Generated ${registry.computations.length} searchable computation source pages.`,
)
