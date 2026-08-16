<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { useSearch } from '../core/state'
import { searchRegistry } from '../core/registry'
import { StatusPlugin } from '../plugins/filters/StatusPlugin'
import SearchInput from './SearchInput.vue'
import SuggestionList from './SuggestionList.vue'
import type { Suggestion } from '../core/types'

// Register plugins (in a real app, this might happen in main.ts or a plugin loader)
searchRegistry.register(StatusPlugin)

const emit = defineEmits<{
  (e: 'search', query: string): void
}>()

const {
  buffer,
  tokens,
  suggestions,
  activeIndex,
  addToken,
  removeToken,
  updateSuggestions,
  handleKeyDown: coreHandleKeyDown,
  selectSuggestion: coreSelectSuggestion,
  commit
} = useSearch()

// Emit the assembled query whenever the committed tokens change (value selected,
// chip added via typing, or a chip removed) so the consumer can refresh results.
watch(tokens, () => {
  emit('search', tokens.value.map(t => t.raw).join(' '))
}, { deep: true })

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
