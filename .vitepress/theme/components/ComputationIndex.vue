<script setup lang="ts">
import { computed, ref } from 'vue'
import { withBase } from 'vitepress'

import registry from '../../../docs/reference/computations.json'


type Computation = (typeof registry.computations)[number]

const query = ref('')
const normalizedQuery = computed(() => query.value.trim().toLocaleLowerCase())
const filtered = computed(() => {
  const needle = normalizedQuery.value
  if (!needle) return registry.computations
  return registry.computations.filter((record) => {
    const searchable = [
      record.id,
      record.title,
      record.summary,
      record.owning_layer,
      ...record.inputs,
      ...record.outputs,
      ...record.surfaces,
      ...record.provenance.evidence_classes,
      ...record.provenance.verification_states,
    ].join(' ').toLocaleLowerCase()
    return searchable.includes(needle)
  })
})

const layers = computed(() => {
  const grouped = new Map<string, Computation[]>()
  for (const record of filtered.value) {
    const records = grouped.get(record.owning_layer) ?? []
    records.push(record)
    grouped.set(record.owning_layer, records)
  }
  return [...grouped.entries()].map(([name, records]) => ({
    name,
    records: records.sort((left, right) => left.title.localeCompare(right.title)),
  }))
})

function evidenceLabel(record: Computation): string {
  return record.provenance.verification_states.join(' · ')
}
</script>

<template>
  <div class="computation-browser">
    <label class="computation-filter">
      <span>Filter by name, ID, input, output or evidence state</span>
      <input
        v-model="query"
        type="search"
        inputmode="search"
        autocomplete="off"
        placeholder="Try Tithi, timezone, or needs_locator"
      >
    </label>

    <p class="computation-count" aria-live="polite">
      Showing {{ filtered.length }} of {{ registry.computations.length }} documented computations
    </p>

    <div v-if="layers.length" class="computation-layers">
      <section v-for="layer in layers" :key="layer.name" class="computation-layer">
        <h2>{{ layer.name }}</h2>
        <ul class="computation-list">
          <li v-for="record in layer.records" :key="record.id">
            <a :href="withBase(`/computations/${record.id}`)">
              <span class="computation-title">{{ record.title }}</span>
              <code>{{ record.id }}</code>
            </a>
            <p>{{ record.summary }}</p>
            <div class="computation-meta">
              <span>{{ evidenceLabel(record) }}</span>
              <span>{{ record.surfaces.join(' · ') }}</span>
            </div>
          </li>
        </ul>
      </section>
    </div>

    <p v-else class="computation-empty">
      No computation matches that filter. Try a shorter term or use the site search.
    </p>
  </div>
</template>
