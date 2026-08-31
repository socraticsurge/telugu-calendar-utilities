import { dirname, relative, resolve, sep } from 'node:path'
import { fileURLToPath } from 'node:url'

import { defineConfig } from 'vitepress'


const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const DOCS_ROOT = resolve(REPO_ROOT, 'docs')
const GITHUB_BLOB =
  'https://github.com/socraticsurge/telugu-calendar-utilities/blob/master/'
const EXCLUDED_SOURCE_DIRS = new Set(['plans', 'specs', 'tracking'])

const activityProfiles = [
  ['Bhumi Puja / foundation', '/reference/13-bhumi-puja-foundation-profile'],
  ['Well digging', '/reference/14-well-digging-profile'],
  ['Land purchase', '/reference/15-land-purchase-profile'],
  ['Namakarana', '/reference/17-namakarana-profile'],
  ['Annaprasana', '/reference/18-annaprasana-profile'],
  ['Karnavedha', '/reference/19-karnavedha-profile'],
  ['Mundana / Chaula', '/reference/20-mundana-profile'],
  ['Vidyarambha', '/reference/21-vidyarambha-profile'],
  ['Upanayana', '/reference/22-upanayana-profile'],
  ['Vehicle acquisition', '/reference/23-vehicle-acquisition-profile'],
  ['Roof laying', '/reference/24-construction-roof-profile'],
  ['Coronation', '/reference/25-coronation-profile'],
  ['Wood cutting', '/reference/26-wood-cutting-profile'],
  ['Surgery', '/reference/27-surgery-profile'],
  ['Gold / jewelry', '/reference/28-gold-jewelry-profile'],
  ['Pilgrimage', '/reference/29-pilgrimage-profile'],
  ['Travel', '/reference/30-travel-profile'],
  ['Wedding', '/reference/31-wedding-evidence-audit'],
  ['Gruhapravesha', '/reference/33-gruhapravesha-evidence-audit'],
  ['Court filing', '/reference/34-court-evidence-audit'],
  ['Litigation alias', '/reference/35-litigation-evidence-audit'],
  ['Engagement', '/reference/36-engagement-evidence-audit'],
  ['Deferred Pretakriya', '/reference/37-cremation-evidence-audit'],
  ['Homa offering', '/reference/38-yajna-homam-evidence-audit'],
  ['General purchase', '/reference/39-purchase-profile'],
  ['Service entry', '/reference/40-job-contract-evidence-audit'],
  ['Capital deployment', '/reference/41-business-evidence-audit'],
  ['Shantika / Paushtika', '/reference/42-ceremony-evidence-audit'],
  ['Dharma-kriya commencement', '/reference/43-beginning-evidence-audit'],
  ['Seemantha', '/reference/47-seemantha-profile'],
  ['Completed-house purchase', '/reference/48-completed-house-purchase-profile'],
  ['Home repair', '/reference/49-home-repair-profile'],
  ['Trade-inventory purchase', '/reference/50-trade-inventory-purchase-profile'],
  ['Borrowing money', '/reference/51-borrowing-money-profile'],
  ['Lending money', '/reference/52-lending-money-profile'],
].map(([text, link]) => ({ text, link }))

function sourcePathFor(envPath: string | undefined): string | undefined {
  if (!envPath) return undefined
  return resolve(REPO_ROOT, envPath)
}

function shouldLinkToGitHub(resolvedPath: string): boolean {
  const relativeToDocs = relative(DOCS_ROOT, resolvedPath)
  if (relativeToDocs.startsWith(`..${sep}`) || relativeToDocs === '..') return true
  const firstPart = relativeToDocs.split(sep)[0]
  return EXCLUDED_SOURCE_DIRS.has(firstPart)
}

function rewriteRepositoryLinks(md: any): void {
  const defaultLinkOpen =
    md.renderer.rules.link_open
    ?? ((tokens: any[], index: number, options: any, _env: any, self: any) =>
      self.renderToken(tokens, index, options))

  md.renderer.rules.link_open = (
    tokens: any[], index: number, options: any, env: any, self: any,
  ) => {
    const token = tokens[index]
    const hrefIndex = token.attrIndex('href')
    const href = hrefIndex >= 0 ? token.attrs[hrefIndex][1] : ''
    const sourcePath = sourcePathFor(env.path)
    if (sourcePath && href.startsWith('..')) {
      const [pathPart, fragment = ''] = href.split('#', 2)
      const resolvedPath = resolve(dirname(sourcePath), pathPart)
      if (shouldLinkToGitHub(resolvedPath)) {
        const repositoryPath = relative(REPO_ROOT, resolvedPath).split(sep).join('/')
        token.attrs[hrefIndex][1] =
          `${GITHUB_BLOB}${repositoryPath}${fragment ? `#${fragment}` : ''}`
      }
    }
    return defaultLinkOpen(tokens, index, options, env, self)
  }
}

function renderMermaidFences(md: any): void {
  const defaultFence = md.renderer.rules.fence
  md.renderer.rules.fence = (
    tokens: any[], index: number, options: any, env: any, self: any,
  ) => {
    const token = tokens[index]
    if (token.info.trim() === 'mermaid') {
      return `<pre class="mermaid">${md.utils.escapeHtml(token.content)}</pre>`
    }
    return defaultFence(tokens, index, options, env, self)
  }
}

export default defineConfig({
  lang: 'en-IN',
  title: 'Panchangam Reference',
  description: 'Methods, evidence, verification and limitations for Astro Chaganti Panchangam.',
  base: '/docs/',
  appearance: false,
  cleanUrls: true,
  srcDir: './docs',
  rewrites: (path) => path.replace(/^_generated\/computations\//, 'computations/'),
  srcExclude: [
    'README.md',
    'reference/README.md',
    'GUIDELINES.md',
    'NOW.md',
    'plans/**',
    'screenshots/**',
    'specs/**',
    'tracking/**',
    'feeds/**',
  ],
  publicDir: './docs/public',
  outDir: './dist/docs',
  cacheDir: './node_modules/.vitepress-cache',
  lastUpdated: true,
  sitemap: {
    hostname: 'https://panchangam.astrochaganti.com/docs/',
  },
  head: [
    ['link', { rel: 'preconnect', href: 'https://fonts.googleapis.com' }],
    [
      'link',
      {
        rel: 'stylesheet',
        href: 'https://fonts.googleapis.com/css2?family=Libre+Baskerville:wght@400;700&family=Inter:wght@400;500;600;700&display=swap',
      },
    ],
    ['meta', { name: 'theme-color', content: '#F2ECDF' }],
  ],
  markdown: {
    config(md) {
      rewriteRepositoryLinks(md)
      renderMermaidFences(md)
    },
  },
  themeConfig: {
    logo: {
      src: '/docs-mark.svg',
      alt: 'Astro Chaganti',
    },
    siteTitle: 'Panchangam Reference',
    nav: [
      { text: 'Reference home', link: '/' },
      { text: 'Browse computations', link: '/computations/' },
      { text: 'Open Panchangam', link: 'https://panchangam.astrochaganti.com/' },
    ],
    sidebar: [
      {
        text: 'Start here',
        items: [
          { text: 'Reference home', link: '/' },
          { text: 'Browse all computations', link: '/computations/' },
          { text: 'System map', link: '/reference/01-system-mindmap' },
          { text: 'User-facing features', link: '/reference/04-user-facing-features' },
        ],
      },
      {
        text: 'Calculations',
        items: [
          { text: 'Engines and model', link: '/reference/02-engines-and-model' },
          { text: 'Derived computations', link: '/reference/03-computational-features' },
          { text: 'Data flow and Muhurtam', link: '/reference/05-data-flow-and-muhurta' },
          { text: 'Birth profiles and D1 chart', link: '/reference/53-birth-profile-calculation' },
          { text: 'Muhurtam election-chart screening', link: '/reference/54-muhurtam-election-chart-screening' },
        ],
      },
      {
        text: 'Evidence and verification',
        items: [
          { text: 'Provenance and authority', link: '/reference/08-provenance-and-authority' },
          { text: 'Computation inventory', link: '/reference/09-computation-inventory' },
          { text: 'Panchangam disclosure', link: '/reference/46-panchangam-provenance-disclosure' },
          { text: 'Gochara crosswalk', link: '/reference/32-gochara-source-crosswalk' },
        ],
      },
      {
        text: 'Contributing',
        items: [
          { text: 'Safe computation workflow', link: '/reference/10-computation-contributor-workflow' },
          { text: 'Copyable record template', link: '/reference/computation-record-template' },
          { text: 'Architecture decision', link: '/decisions/0002-computation-layer-organization' },
        ],
      },
      {
        text: 'Muhurtam evidence',
        collapsed: true,
        items: [
          { text: 'Calculation table', link: '/reference/07-muhurta-table' },
          { text: 'Activity coverage', link: '/reference/16-activity-provenance-coverage' },
          { text: 'Provenance states', link: '/reference/44-activity-provenance-states' },
          { text: 'Coverage roadmap', link: '/reference/45-muhurta-activity-coverage-roadmap' },
          { text: 'Activity profiles', collapsed: true, items: activityProfiles },
        ],
      },
      {
        text: 'Maintainer references',
        collapsed: true,
        items: [
          { text: 'Roadmap and backlog', link: '/reference/06-roadmap-and-backlog' },
          { text: 'Projection operations', link: '/operations/documentation-projection' },
          { text: 'Pages retention', link: '/operations/gh-pages-retention' },
        ],
      },
    ],
    search: {
      provider: 'local',
      options: {
        miniSearch: {
          searchOptions: {
            fuzzy: 0.2,
            prefix: true,
            boost: { title: 5, text: 2, titles: 2 },
          },
        },
      },
    },
    outline: { level: [2, 3], label: 'On this page' },
    docFooter: { prev: 'Previous reference', next: 'Next reference' },
    editLink: {
      pattern: 'https://github.com/socraticsurge/telugu-calendar-utilities/edit/master/docs/:path',
      text: 'Edit this source on GitHub',
    },
    lastUpdated: { text: 'Source last updated' },
    externalLinkIcon: true,
    returnToTopLabel: 'Return to top',
    sidebarMenuLabel: 'Reference navigation',
    socialLinks: [
      {
        icon: 'github',
        link: 'https://github.com/socraticsurge/telugu-calendar-utilities',
      },
    ],
  },
})
