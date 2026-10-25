<script setup lang="ts">
import { ref, nextTick, watch, onBeforeUnmount } from 'vue'
import { useSearch } from '../core/state'
import { toSearchQuery } from '../core/query'
import '../plugins'
import SearchInput from './SearchInput.vue'
import SuggestionList from './SuggestionList.vue'
import type { SearchQuery, Suggestion } from '../core/types'

const SEARCH_DEBOUNCE_MS = 250

const emit = defineEmits<{
  // A token change is waiting to be applied; false when it turned out a no-op
  (e: 'pending', pending: boolean): void
  (e: 'search', query: SearchQuery): void
}>()

const {
  buffer,
  tokens,
  suggestions,
  activeIndex,
  removeToken,
  handleKeyDown: coreHandleKeyDown,
  selectSuggestion: coreSelectSuggestion,
  commit
} = useSearch()

// Emit the query (debounced) whenever the committed tokens change, so quick
// edits like repeated Backspace produce one search. `tokens` is replaced on
// every change, so a shallow watch suffices.
let searchTimer: ReturnType<typeof setTimeout> | undefined
let lastQueryKey = JSON.stringify(toSearchQuery([]))

watch(tokens, () => {
  emit('pending', true)
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    const query = toSearchQuery(tokens.value)
    const key = JSON.stringify(query)
    if (key === lastQueryKey) {
      emit('pending', false)
      return
    }
    lastQueryKey = key
    emit('search', query)
  }, SEARCH_DEBOUNCE_MS)
})

onBeforeUnmount(() => clearTimeout(searchTimer))

const searchInputRef = ref<InstanceType<typeof SearchInput> | null>(null)

function onSelect(suggestion: Suggestion) {
  coreSelectSuggestion(suggestion)
  nextTick(() => {
    searchInputRef.value?.focus()
  })
}

function onKeyDown(e: KeyboardEvent) {
  coreHandleKeyDown(e)
  if (e.key === 'Enter') {
    nextTick(() => {
      searchInputRef.value?.focus()
    })
  }
}
</script>

<template>
  <div class="smart-search-container" @keydown="onKeyDown">
    <SearchInput
      ref="searchInputRef"
      v-model:buffer="buffer"
      :tokens="tokens"
      @remove-token="removeToken"
    />
    
    <SuggestionList
      :suggestions="suggestions"
      :active-index="activeIndex"
      @select="onSelect"
    />
  </div>
</template>

<style scoped>
.smart-search-container {
  position: relative;
  width: 100%;
  margin: 0 auto;
}
</style>
