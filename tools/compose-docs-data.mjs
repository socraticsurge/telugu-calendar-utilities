#!/usr/bin/env node
import { copyFile, mkdir } from 'node:fs/promises'
import { join } from 'node:path'


const root = process.cwd()
const sourceRoot = join(root, 'docs', 'reference')
const outputRoot = join(root, 'dist', 'docs', 'reference')
const publicData = [
  'computations.json',
  'computations.schema.json',
  'muhurta-activity-backlog.json',
  'muhurtam-rule-crosswalk.json',
  'project-facts.json',
  'provenance.json',
]

await mkdir(outputRoot, { recursive: true })
for (const file of publicData) {
  await copyFile(join(sourceRoot, file), join(outputRoot, file))
}

console.log(`Composed ${publicData.length} canonical data files into dist/docs/reference/.`)
