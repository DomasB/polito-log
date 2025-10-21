import { ref, computed } from 'vue'
import type { Ref } from 'vue'
import {
  getStatementsApiV1StatementsGet,
  createStatementApiV1StatementsPost,
  getStatementApiV1StatementsStatementIdGet,
  updateStatementApiV1StatementsStatementIdPut,
  deleteStatementApiV1StatementsStatementIdDelete,
  searchStatementsApiV1StatementsSearchGet,
  getStatementsByPoliticianApiV1StatementsPoliticianPoliticianNameGet,
  getStatementsByPartyApiV1StatementsPartyPartyGet
} from '@/api/sdk.gen'
import type {
  StatementResponse,
  StatementCreate,
  StatementUpdate
} from '@/api/types.gen'

/**
 * Composable for managing political statements
 * Provides reactive state and methods for CRUD operations on statements
 */
export function useStatements() {
  // Reactive state
  const statements: Ref<StatementResponse[]> = ref([])
  const currentStatement: Ref<StatementResponse | null> = ref(null)
  const loading = ref(false)
  const error: Ref<string | null> = ref(null)
  const totalCount = ref(0)

  // Computed
  const hasStatements = computed(() => statements.value.length > 0)
  const hasError = computed(() => error.value !== null)

  /**
   * Fetch all statements with pagination
   */
  async function fetchStatements(options: { skip?: number; limit?: number; activeOnly?: boolean } = {}) {
    loading.value = true
    error.value = null

    try {
      const { data, error: apiError } = await getStatementsApiV1StatementsGet({
        query: {
          skip: options.skip ?? 0,
          limit: options.limit ?? 100,
          active_only: options.activeOnly ?? true
        }
      })

      if (apiError) {
        throw new Error('Failed to fetch statements')
      }

      statements.value = data as StatementResponse[]
      totalCount.value = statements.value.length
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unknown error occurred'
      console.error('Error fetching statements:', err)
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch a single statement by ID
   */
  async function fetchStatement(id: number) {
    loading.value = true
    error.value = null

    try {
      const { data, error: apiError } = await getStatementApiV1StatementsStatementIdGet({
        path: { statement_id: id }
      })

      if (apiError) {
        throw new Error(`Statement with ID ${id} not found`)
      }

      currentStatement.value = data as StatementResponse
      return data
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unknown error occurred'
      console.error('Error fetching statement:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * Create a new statement
   */
  async function createStatement(statementData: StatementCreate) {
    loading.value = true
    error.value = null

    try {
      const { data, error: apiError } = await createStatementApiV1StatementsPost({
        body: statementData
      })

      if (apiError) {
        throw new Error('Failed to create statement')
      }

      // Add to local list
      statements.value.unshift(data as StatementResponse)
      return data
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unknown error occurred'
      console.error('Error creating statement:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * Update an existing statement
   */
  async function updateStatement(id: number, updates: StatementUpdate) {
    loading.value = true
    error.value = null

    try {
      const { data, error: apiError } = await updateStatementApiV1StatementsStatementIdPut({
        path: { statement_id: id },
        body: updates
      })

      if (apiError) {
        throw new Error('Failed to update statement')
      }

      // Update in local list
      const index = statements.value.findIndex((s) => s.id === id)
      if (index !== -1) {
        statements.value[index] = data as StatementResponse
      }

      // Update current statement if it's the one being edited
      if (currentStatement.value?.id === id) {
        currentStatement.value = data as StatementResponse
      }

      return data
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unknown error occurred'
      console.error('Error updating statement:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * Delete a statement (soft delete by default)
   */
  async function deleteStatement(id: number, softDelete = true) {
    loading.value = true
    error.value = null

    try {
      const { error: apiError } = await deleteStatementApiV1StatementsStatementIdDelete({
        path: { statement_id: id },
        query: { soft_delete: softDelete }
      })

      if (apiError) {
        throw new Error('Failed to delete statement')
      }

      // Remove from local list
      statements.value = statements.value.filter((s) => s.id !== id)

      // Clear current statement if it was deleted
      if (currentStatement.value?.id === id) {
        currentStatement.value = null
      }

      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unknown error occurred'
      console.error('Error deleting statement:', err)
      return false
    } finally {
      loading.value = false
    }
  }

  /**
   * Search statements by text
   */
  async function searchStatements(query: string, options: { skip?: number; limit?: number } = {}) {
    loading.value = true
    error.value = null

    try {
      const { data, error: apiError } = await searchStatementsApiV1StatementsSearchGet({
        query: {
          q: query,
          skip: options.skip ?? 0,
          limit: options.limit ?? 100
        }
      })

      if (apiError) {
        throw new Error('Search failed')
      }

      statements.value = data as StatementResponse[]
      return data
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unknown error occurred'
      console.error('Error searching statements:', err)
      return []
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch statements by politician
   */
  async function fetchByPolitician(politicianName: string, options: { skip?: number; limit?: number } = {}) {
    loading.value = true
    error.value = null

    try {
      const { data, error: apiError } = await getStatementsByPoliticianApiV1StatementsPoliticianPoliticianNameGet({
        path: { politician_name: politicianName },
        query: {
          skip: options.skip ?? 0,
          limit: options.limit ?? 100
        }
      })

      if (apiError) {
        throw new Error('Failed to fetch statements by politician')
      }

      statements.value = data as StatementResponse[]
      return data
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unknown error occurred'
      console.error('Error fetching statements by politician:', err)
      return []
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch statements by party
   */
  async function fetchByParty(party: string, options: { skip?: number; limit?: number } = {}) {
    loading.value = true
    error.value = null

    try {
      const { data, error: apiError } = await getStatementsByPartyApiV1StatementsPartyPartyGet({
        path: { party },
        query: {
          skip: options.skip ?? 0,
          limit: options.limit ?? 100
        }
      })

      if (apiError) {
        throw new Error('Failed to fetch statements by party')
      }

      statements.value = data as StatementResponse[]
      return data
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unknown error occurred'
      console.error('Error fetching statements by party:', err)
      return []
    } finally {
      loading.value = false
    }
  }

  /**
   * Clear error message
   */
  function clearError() {
    error.value = null
  }

  /**
   * Reset all state
   */
  function reset() {
    statements.value = []
    currentStatement.value = null
    loading.value = false
    error.value = null
    totalCount.value = 0
  }

  return {
    // State
    statements,
    currentStatement,
    loading,
    error,
    totalCount,

    // Computed
    hasStatements,
    hasError,

    // Methods
    fetchStatements,
    fetchStatement,
    createStatement,
    updateStatement,
    deleteStatement,
    searchStatements,
    fetchByPolitician,
    fetchByParty,
    clearError,
    reset
  }
}
