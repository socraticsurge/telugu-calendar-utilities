import { inBrowser, useRoute } from 'vitepress'
import DefaultTheme from 'vitepress/theme-without-fonts'
import { nextTick, watch } from 'vue'
import type { Theme } from 'vitepress'

import ComputationIndex from './components/ComputationIndex.vue'
import './custom.css'


async function renderMermaid(): Promise<void> {
  const nodes = document.querySelectorAll<HTMLElement>('pre.mermaid:not([data-processed])')
  if (!nodes.length) return

  const mermaid = (await import('mermaid')).default
  mermaid.initialize({
    startOnLoad: false,
    securityLevel: 'strict',
    theme: 'base',
    themeVariables: {
      primaryColor: '#F7E9E4',
      primaryBorderColor: '#8E2A1F',
      primaryTextColor: '#1F1A17',
      lineColor: '#6B6357',
      secondaryColor: '#EEF2E7',
      tertiaryColor: '#F2ECDF',
      fontFamily: 'Inter, system-ui, sans-serif',
    },
  })
  await mermaid.run({ nodes })
}

export default {
  extends: DefaultTheme,
  enhanceApp({ app }) {
    app.component('ComputationIndex', ComputationIndex)
  },
  setup() {
    if (!inBrowser) return
    const route = useRoute()
    watch(
      () => route.path,
      async () => {
        await nextTick()
        await renderMermaid()
      },
      { immediate: true },
    )
  },
} satisfies Theme
