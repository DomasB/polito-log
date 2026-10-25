<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NSpace, NButton, NAlert, NEmpty, NH2 } from 'naive-ui'
import { useStatements } from '@/composables/useStatements'
import { useAuthStore } from '@/stores/auth'
import type { StatementCreate } from '@/api/types.gen'
import StatementCard from '@/components/StatementCard.vue'
import AppLoader from '@/components/AppLoader.vue'
import SmartSearch from './search/ui/SmartSearch.vue'
import type { SearchQuery } from './search/core/types'

const {
  statements,
  loading,
  error,
  fetchStatements,
  createStatement,
  searchStatements,
  clearError,
} = useStatements()

const authStore = useAuthStore()

const activeQuery = ref<SearchQuery>({ text: '', filters: [] })
const searchPending = ref(false)
const busy = computed(() => loading.value || searchPending.value)

// Status filters are applied in the browser, over the (at most 100) fetched rows
const visibleStatements = computed(() => {
  const statusFilters = activeQuery.value.filters.filter((f) => f.pluginId === 'status')
  return statements.value.filter((s) =>
    statusFilters.every((f) =>
      f.operatorId === 'not-equals' ? s.status !== f.value : s.status === f.value,
    ),
  )
})

const resultsAnnouncement = computed(() => {
  if (busy.value) return ''
  const n = visibleStatements.value.length
  return `${n} ${n === 1 ? 'statement' : 'statements'}`
})

// Fetch statements on component mount
onMounted(async () => {
  await fetchStatements()
})

// Example: Create a new statement
async function handleCreateStatement() {
  const newStatement: StatementCreate = {
    politician_name: 'John Doe',
    party: 'Example Party',
    statement_text: 'This is an example statement about policy.',
    statement_date: new Date().toISOString(),
    source_url: 'https://example.com/source',
    category: 'Policy',
    status: 'pending',
  }

  await createStatement(newStatement)
}

async function handleSearch(query: SearchQuery) {
  searchPending.value = false
  const textChanged = query.text !== activeQuery.value.text
  activeQuery.value = query
  // Filter-only changes are applied client-side, no refetch needed
  if (textChanged) await reload()
}

async function reload() {
  const { text } = activeQuery.value
  if (text) {
    await searchStatements(text)
  } else {
    await fetchStatements()
  }
}
</script>

<template>
  <NSpace vertical :size="24">
    <!-- Header -->
    <NH2>Political Statements</NH2>

    <!-- Error Alert -->
    <NAlert v-if="error" type="error" closable @close="clearError">
      {{ error }}
    </NAlert>

    <!-- Actions -->
    <NSpace v-if="authStore.isAuthenticated">
      <NButton type="primary" @click="handleCreateStatement"> Create Example Statement </NButton>
    </NSpace>

    <SmartSearch @pending="searchPending = $event" @search="handleSearch" />

    <div class="visually-hidden" aria-live="polite">{{ resultsAnnouncement }}</div>

    <!-- Statements List: stays mounted under the loader while loading -->
    <AppLoader :show="busy">
      <div v-if="visibleStatements.length > 0" class="statement-list">
        <StatementCard
          v-for="statement in visibleStatements"
          :key="statement.id"
          :statement="statement"
        />
      </div>

      <!-- Empty State -->
      <NEmpty v-else-if="!busy" description="No statements found" style="padding: 2rem">
        <template #extra>
          <NButton size="small" @click="reload()"> Refresh </NButton>
        </template>
      </NEmpty>

      <div v-else class="loading-placeholder" />
    </AppLoader>
  </NSpace>
</template>

<style scoped>
.statement-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.loading-placeholder {
  min-height: 8rem;
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  margin: -1px;
  padding: 0;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
  border: 0;
}
</style>
