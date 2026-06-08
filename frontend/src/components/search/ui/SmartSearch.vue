<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useSearch } from '../core/state'
import { searchRegistry } from '../core/registry'
import { StatusPlugin } from '../plugins/filters/StatusPlugin'
import SearchInput from './SearchInput.vue'
import SuggestionList from './SuggestionList.vue'
import type { Suggestion } from '../core/types'

// Register plugins (in a real app, this might happen in main.ts or a plugin loader)
searchRegistry.register(StatusPlugin)

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
