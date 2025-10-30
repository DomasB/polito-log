<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  NSpace,
  NButton,
  NInput,
  NCard,
  NTag,
  NText,
  NSpin,
  NAlert,
  NEmpty,
  NH2,
  NGrid,
  NGi,
  NTime
} from 'naive-ui'
import { useStatements } from '@/composables/useStatements'
import { useAuthStore } from '@/stores/auth'
import type { StatementCreate } from '@/api/types.gen'

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

// Get tag type based on status
function getStatusType(status?: string) {
  const statusMap: Record<string, 'default' | 'success' | 'warning' | 'error' | 'info'> = {
    pending: 'warning',
    verified: 'success',
    disputed: 'error',
    retracted: 'default'
  }
  return statusMap[status!] || 'default'
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
    <NGrid v-else-if="hasStatements" :cols="1" :y-gap="16">
      <NGi v-for="statement in statements" :key="statement.id">
        <NCard
          :title="`${statement.politician_name} (${statement.party})`"
          hoverable
        >
          <template #header-extra>
            <NTag :type="getStatusType(statement.status)">
              {{ statement.status }}
            </NTag>
          </template>

          <NSpace vertical :size="12">
            <!-- Statement Text -->
            <NText>{{ statement.statement_text }}</NText>

            <!-- Metadata -->
            <NSpace align="center">
              <NText depth="3" :size="14">
                <template v-if="statement.category">
                  Category: {{ statement.category }}
                </template>
              </NText>

              <NText depth="3" :size="14">
                Date:
                <NTime
                  :time="new Date(statement.statement_date)"
                  format="yyyy-MM-dd"
                />
              </NText>

              <NButton
                v-if="statement.source_url"
                text
                tag="a"
                :href="statement.source_url"
                target="_blank"
                type="info"
                size="small"
              >
                View Source
              </NButton>
            </NSpace>
          </NSpace>

          <template #footer>
            <NSpace justify="space-between">
              <NSpace>
                <NText depth="3" :size="12">
                  Created: <NTime :time="new Date(statement.created_at)" type="relative" />
                </NText>
              </NSpace>
            </NSpace>
          </template>
        </NCard>
      </NGi>
    </NGrid>

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
