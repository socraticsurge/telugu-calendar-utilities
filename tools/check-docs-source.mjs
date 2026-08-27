#!/usr/bin/env node
import { readdir, readFile } from 'node:fs/promises'
import { extname, join, relative } from 'node:path'

import { JSDOM } from 'jsdom'


const root = process.cwd()
const docsRoot = join(root, 'docs')
const excludedTopLevel = new Set([
  'feeds',
  'plans',
  'screenshots',
  'specs',
  'tracking',
])

const dom = new JSDOM('<!doctype html><html><body></body></html>')
globalThis.window = dom.window
globalThis.document = dom.window.document
const mermaid = (await import('mermaid')).default

async function markdownFiles(directory) {
  const files = []
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name)
    const relativePath = relative(docsRoot, path)
    const firstPart = relativePath.split('/')[0]
    if (excludedTopLevel.has(firstPart)) continue
    if (entry.isDirectory()) files.push(...await markdownFiles(path))
    else if (extname(entry.name) === '.md') files.push(path)
  }
  return files
}

let diagramCount = 0
const failures = []
const mermaidFence = /^```mermaid\s*\n([\s\S]*?)^```\s*$/gm
for (const path of await markdownFiles(docsRoot)) {
  const source = await readFile(path, 'utf8')
  for (const match of source.matchAll(mermaidFence)) {
    diagramCount += 1
    try {
      await mermaid.parse(match[1])
    } catch (error) {
      failures.push(`${relative(root, path)}: ${error.message}`)
    }
  }
}

if (failures.length) {
  for (const failure of failures) console.error(`ERROR: ${failure}`)
  process.exit(1)
}

console.log(`Documentation source valid: ${diagramCount} Mermaid diagrams parsed.`)
