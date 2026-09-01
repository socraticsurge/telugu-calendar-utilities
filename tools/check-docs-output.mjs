#!/usr/bin/env node
import { createHash } from 'node:crypto'
import { readdir, readFile, stat } from 'node:fs/promises'
import { join, relative } from 'node:path'

import { JSDOM } from 'jsdom'


const root = process.cwd()
const publicRoot = join(root, 'public')
const distRoot = join(root, 'dist')
const docsOutput = join(distRoot, 'docs')
const failures = []
const parsedHtml = new Map()

async function filesUnder(directory) {
  const files = []
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name)
    if (entry.isDirectory()) files.push(...await filesUnder(path))
    else files.push(path)
  }
  return files
}

async function exists(path) {
  try {
    await stat(path)
    return true
  } catch {
    return false
  }
}

async function digest(path) {
  return createHash('sha256').update(await readFile(path)).digest('hex')
}

async function htmlDocument(path) {
  if (!parsedHtml.has(path)) {
    parsedHtml.set(path, new JSDOM(await readFile(path, 'utf8')).window.document)
  }
  return parsedHtml.get(path)
}

async function resolveDocumentationTarget(pathname) {
  if (!pathname.startsWith('/docs/')) return undefined
  const relativePath = decodeURIComponent(pathname.slice('/docs/'.length))
  if (!relativePath) return join(docsOutput, 'index.html')
  const direct = join(docsOutput, relativePath)
  if (relativePath.endsWith('/')) return join(direct, 'index.html')
  if (await exists(`${direct}.html`)) return `${direct}.html`
  if (await exists(direct) && (await stat(direct)).isFile()) return direct
  return join(direct, 'index.html')
}

function requirePath(path, description) {
  return exists(path).then((present) => {
    if (!present) failures.push(`${description} missing: ${relative(root, path)}`)
  })
}

await Promise.all([
  requirePath(join(distRoot, 'index.html'), 'landing page'),
  requirePath(join(docsOutput, 'index.html'), 'documentation home'),
  requirePath(join(docsOutput, 'computations', 'index.html'), 'computation index'),
  requirePath(join(docsOutput, 'docs-mark.svg'), 'documentation brand mark'),
  requirePath(join(docsOutput, 'sitemap.xml'), 'documentation sitemap'),
])

const registry = JSON.parse(
  await readFile(join(root, 'docs', 'reference', 'computations.json'), 'utf8'),
)
for (const record of registry.computations) {
  const routePath = join(docsOutput, 'computations', `${record.id}.html`)
  await requirePath(
    routePath,
    `stable route for ${record.id}`,
  )
  if (await exists(routePath)) {
    const html = await readFile(routePath, 'utf8')
    if (html.includes('/docs/docs/')) {
      failures.push(`computation route contains a doubled docs base: ${record.id}`)
    }
  }
}

for (const path of await filesUnder(publicRoot)) {
  const relativePath = relative(publicRoot, path)
  const output = join(distRoot, relativePath)
  if (!await exists(output)) {
    failures.push(`landing/public artifact removed by docs composition: ${relativePath}`)
    continue
  }
  if (await digest(path) !== await digest(output)) {
    failures.push(`landing/public artifact changed by docs composition: ${relativePath}`)
  }
}

for (const file of [
  'computations.json',
  'computations.schema.json',
  'muhurta-activity-backlog.json',
  'muhurtam-rule-crosswalk.json',
  'project-facts.json',
  'provenance.json',
]) {
  const source = join(root, 'docs', 'reference', file)
  const output = join(docsOutput, 'reference', file)
  if (!await exists(output) || await digest(source) !== await digest(output)) {
    failures.push(`canonical documentation data is missing or changed: ${file}`)
  }
}

for (const forbidden of ['plans', 'screenshots', 'specs', 'tracking', 'feeds']) {
  if (await exists(join(docsOutput, forbidden))) {
    failures.push(`excluded documentation tree was published: docs/${forbidden}/`)
  }
}

if (await exists(join(docsOutput, '_generated'))) {
  failures.push('generated documentation source path leaked into public routes')
}

const assetFiles = await filesUnder(join(docsOutput, 'assets'))
const searchAssets = assetFiles.filter((path) => path.includes('localSearchIndex'))
if (!searchAssets.length) {
  failures.push('local search index asset was not generated')
} else {
  const searchPayload = (await Promise.all(
    searchAssets.map((path) => readFile(path, 'utf8')),
  )).join('\n')
  for (const record of registry.computations) {
    const route = `/docs/computations/${record.id}`
    if (!searchPayload.includes(route)) {
      failures.push(`local search index is missing computation route: ${route}`)
    }
  }
}

for (const source of (await filesUnder(docsOutput)).filter(
  (path) => path.endsWith('.html'),
)) {
  const document = await htmlDocument(source)
  for (const element of document.querySelectorAll('a[href], link[href]')) {
    const href = element.getAttribute('href')
    if (!href || (!href.startsWith('/docs/') && !href.startsWith('#'))) continue
    const url = new URL(href, 'https://panchangam.astrochaganti.com/docs/')
    const target = href.startsWith('#')
      ? source
      : await resolveDocumentationTarget(url.pathname)
    if (!target || !await exists(target)) {
      failures.push(
        `broken documentation link in ${relative(root, source)}: ${href}`,
      )
      continue
    }
    if (url.hash && target.endsWith('.html')) {
      const id = decodeURIComponent(url.hash.slice(1))
      if (id && !(await htmlDocument(target)).getElementById(id)) {
        failures.push(
          `missing documentation anchor in ${relative(root, source)}: ${href}`,
        )
      }
    }
  }
}

if (failures.length) {
  for (const failure of failures) console.error(`ERROR: ${failure}`)
  process.exit(1)
}

console.log(
  `Documentation output valid: ${registry.computations.length} stable computation routes, `
  + `${(await filesUnder(publicRoot)).length} landing/public artifacts preserved.`,
)
