<script setup lang="ts">
import { ref, computed, nextTick, watch, onBeforeUnmount, useId } from 'vue'
import { useSearch } from '../core/state'
import { toSearchQuery } from '../core/query'
import '../plugins'
import SearchInput from './SearchInput.vue'
import SuggestionList from './SuggestionList.vue'
import { describeToken } from './describeToken'
import type { SearchQuery, SearchToken, Suggestion } from '../core/types'

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
  close,
  handleKeyDown: coreHandleKeyDown,
  selectSuggestion: coreSelectSuggestion,
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

// Combobox ids; SuggestionList derives option ids the same way
const listboxId = useId()
const expanded = computed(() => suggestions.value.length > 0)
const activeDescendant = computed(() =>
  expanded.value && activeIndex.value >= 0 ? `${listboxId}-${activeIndex.value}` : undefined,
)

// Screen-reader announcements for chips being added or removed
const announcement = ref('')

function describeAdded(token: SearchToken) {
  if (token.type === 'filter' && token.error) {
    return `${token.filterKey}${token.operator} ${token.value} is invalid and not applied`
  }
  return `${capitalize(describeToken(token))} added`
}

function capitalize(s: string) {
  return s.charAt(0).toUpperCase() + s.slice(1)
}

watch(tokens, (next, prev) => {
  const prevIds = new Set(prev.map((t) => t.id))
  const nextIds = new Set(next.map((t) => t.id))
  const messages = [
    ...next.filter((t) => !prevIds.has(t.id)).map(describeAdded),
    ...prev.filter((t) => !nextIds.has(t.id)).map((t) => `${capitalize(describeToken(t))} removed`),
  ]
  if (messages.length === 0) return
  // Clear first so repeating the same message is announced again
  announcement.value = ''
  nextTick(() => {
    announcement.value = messages.join('. ')
  })
})

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
  <div class="smart-search-container">
    <SearchInput
      ref="searchInputRef"
      v-model:buffer="buffer"
      :tokens="tokens"
      :expanded="expanded"
      :listbox-id="listboxId"
      :active-descendant="activeDescendant"
      @keydown="onKeyDown"
      @blur="close"
      @remove-token="removeToken"
    />

    <SuggestionList
      :suggestions="suggestions"
      :active-index="activeIndex"
      :listbox-id="listboxId"
      @select="onSelect"
    />

    <div class="visually-hidden" aria-live="polite">{{ announcement }}</div>
  </div>
</template>

<style scoped>
.smart-search-container {
  position: relative;
  width: 100%;
  margin: 0 auto;
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
