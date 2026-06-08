<script setup lang="ts">
import { NList, NListItem, NThing, NTag, NText, NCard, NScrollbar, useThemeVars } from 'naive-ui'
import type { Suggestion } from '../core/types'
import { ref, watch, nextTick } from 'vue'

const props = defineProps<{
  suggestions: Suggestion[]
  activeIndex: number
}>()

const emit = defineEmits<{
  (e: 'select', suggestion: Suggestion): void
}>()

const themeVars = useThemeVars()
const itemRefs = ref<HTMLElement[]>([])

// Scroll active item into view
watch(() => props.activeIndex, (newIndex) => {
  if (newIndex >= 0 && newIndex < props.suggestions.length) {
    nextTick(() => {
      const el = itemRefs.value[newIndex]
      if (el) {
        el.scrollIntoView({ block: 'nearest' })
      }
    })
  }
})
</script>

<template>
  <div 
    class="suggestion-list-wrapper" 
    v-if="suggestions.length > 0"
    :style="{ '--n-hover-color': themeVars.hoverColor }"
  >
    <NCard content-style="padding: 0;" size="small" bordered>
      <NScrollbar style="max-height: 300px">
        <NList hoverable clickable>
          <NListItem
            v-for="(item, index) in suggestions"
            :key="index"
            :class="{ 'active-item': index === activeIndex }"
            @click="emit('select', item)"
            :ref="el => { if (el) itemRefs[index] = (el as any).$el || el }"
          >
            <NThing content-indented>
              <template #header>
                <div style="display: flex; align-items: center; gap: 8px;">
                  <NTag v-if="item.type === 'key'" type="info" size="small" :bordered="false">Key</NTag>
                  <NTag v-else-if="item.type === 'value'" type="success" size="small" :bordered="false">Value</NTag>
                  <NText strong>{{ item.label }}</NText>
                </div>
              </template>
              <template #description v-if="item.description">
                <NText depth="3" style="font-size: 12px;">{{ item.description }}</NText>
              </template>
            </NThing>
          </NListItem>
        </NList>
      </NScrollbar>
    </NCard>
  </div>
</template>

<style scoped>
.suggestion-list-wrapper {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 1000;
  margin-top: 4px;
  box-shadow: 0 3px 6px -4px rgba(0, 0, 0, .12), 0 6px 16px 0 rgba(0, 0, 0, .08), 0 9px 28px 8px rgba(0, 0, 0, .05); /* Naive UI shadow approx */
}

.active-item {
  background-color: var(--n-hover-color);
}

/* Dark mode support if needed later, but for now simple override */
:deep(.n-list-item) {
  padding: 8px 12px;
}
</style>
