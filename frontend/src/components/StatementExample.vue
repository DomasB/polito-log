<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  NSpace,
  NButton,
  NInput,
  NSpin,
  NAlert,
  NEmpty,
  NH2
} from 'naive-ui'
import { useStatements } from '@/composables/useStatements'
import { useAuthStore } from '@/stores/auth'
import type { StatementCreate } from '@/api/types.gen'
import StatementCard from '@/components/StatementCard.vue'

const {
  statements,
  loading,
  error,
  hasStatements,
  fetchStatements,
  createStatement,
  searchStatements,
  clearError
} = useStatements()
const authStore = useAuthStore()
const searchQuery = ref('')

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
    status: 'pending'
  }

  const created = await createStatement(newStatement)
}

// Example: Search statements
async function handleSearch(query: string) {
  if (query.trim()) {
    await searchStatements(query)
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
    <NAlert
      v-if="error"
      type="error"
      closable
      @close="clearError"
    >
      {{ error }}
    </NAlert>

    <!-- Actions -->
    <NSpace>
      <NButton
        v-if="authStore.isAuthenticated"
        type="primary" 
        @click="handleCreateStatement"
      >
        Create Example Statement
      </NButton>
      <NInput
        v-model:value="searchQuery"
        placeholder="Search statements..."
        clearable
        style="width: 300px"
        @update:value="handleSearch"
      />
    </NSpace>

    <!-- Loading State -->
    <div v-if="loading" style="text-align: center; padding: 2rem">
      <NSpin size="large">
        <template #description>
          Loading statements...
        </template>
      </NSpin>
    </div>

    <!-- Statements List -->
    <div v-else-if="hasStatements" class="statement-list">
      <StatementCard
        v-for="statement in statements"
        :key="statement.id"
        :statement="statement"
      />
    </div>

    <!-- Empty State -->
    <NEmpty
      v-else-if="!loading"
      description="No statements found"
      style="padding: 2rem"
    >
      <template #extra>
        <NButton size="small" @click="fetchStatements()">
          Refresh
        </NButton>
      </template>
    </NEmpty>
  </NSpace>
</template>

<style scoped>
.statement-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>
