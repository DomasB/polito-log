<script setup lang="ts">
import { NList, NListItem, NThing, NTag, NText, NCard, NScrollbar, useThemeVars } from 'naive-ui'
import type { Suggestion } from '../core/types'
import { ref, watch, nextTick, onBeforeUpdate } from 'vue'

const props = defineProps<{
  suggestions: Suggestion[]
  activeIndex: number
  listboxId: string
}>()

const emit = defineEmits<{
  (e: 'select', suggestion: Suggestion): void
}>()

const themeVars = useThemeVars()
const itemRefs = ref<HTMLElement[]>([])

onBeforeUpdate(() => {
  itemRefs.value = []
})

// Scroll active item into view
watch(
  () => props.activeIndex,
  (newIndex) => {
    if (newIndex >= 0 && newIndex < props.suggestions.length) {
      nextTick(() => {
        const el = itemRefs.value[newIndex]
        if (el) {
          el.scrollIntoView({ block: 'nearest' })
        }
      })
    }
  },
)

// A tap selects only if it starts and ends on the same item with the same
// pointer, so a drag released over an item (or a scroll) doesn't select.
let press: { pointerId: number; index: number } | null = null

function onPointerDown(e: PointerEvent, index: number) {
  press = e.button === 0 ? { pointerId: e.pointerId, index } : null
}

function onPointerUp(e: PointerEvent, index: number, item: Suggestion) {
  const started = press
  press = null
  if (started && started.pointerId === e.pointerId && started.index === index) {
    emit('select', item)
  }
}

function onPointerAbort() {
  press = null
}

// Synthetic clicks from screen readers and keyboards have no pointer events
function onClick(e: MouseEvent, item: Suggestion) {
  if (e.detail === 0) emit('select', item)
}

function optionId(index: number) {
  return `${props.listboxId}-${index}`
}
</script>

<template>
  <div
    class="suggestion-list-wrapper"
    v-if="suggestions.length > 0"
    :style="{ '--n-hover-color': themeVars.hoverColor }"
  >
    <NCard content-style="padding: 0;" size="small" bordered>
      <NScrollbar style="max-height: 300px">
        <NList :id="listboxId" role="listbox" aria-label="Suggestions" hoverable clickable>
          <NListItem
            v-for="(item, index) in suggestions"
            :key="`${item.type}:${item.value}`"
            :id="optionId(index)"
            role="option"
            :aria-selected="index === activeIndex"
            class="suggestion-item"
            :class="{ 'active-item': index === activeIndex }"
            @pointerdown.prevent="onPointerDown($event, index)"
            @pointerup="onPointerUp($event, index, item)"
            @pointercancel="onPointerAbort"
            @pointerleave="onPointerAbort"
            @click="onClick($event, item)"
            :ref="
              (el) => {
                if (el) itemRefs[index] = (el as any).$el || el
              }
            "
          >
            <NThing content-indented>
              <template #header>
                <div style="display: flex; align-items: center; gap: 8px">
                  <NTag
                    v-if="item.type === 'key'"
                    type="info"
                    size="small"
                    :bordered="false"
                    aria-hidden="true"
                    >Key</NTag
                  >
                  <NTag
                    v-else-if="item.type === 'value'"
                    type="success"
                    size="small"
                    :bordered="false"
                    aria-hidden="true"
                    >Value</NTag
                  >
                  <NText strong>{{ item.label }}</NText>
                </div>
              </template>
              <template #description v-if="item.description">
                <NText depth="3" style="font-size: 12px">{{ item.description }}</NText>
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
  box-shadow:
    0 3px 6px -4px rgba(0, 0, 0, 0.12),
    0 6px 16px 0 rgba(0, 0, 0, 0.08),
    0 9px 28px 8px rgba(0, 0, 0, 0.05); /* Naive UI shadow approx */
}

.active-item {
  background-color: var(--n-hover-color);
}

/* Dark mode support if needed later, but for now simple override */
:deep(.n-list-item) {
  padding: 8px 12px;
}

/* Prevent the tap on a suggestion from being treated as a text-selection
   gesture on touch devices, and avoid the synthetic click/focus race that
   stopped selection (and flyout closing) from working on mobile. */
.suggestion-item {
  user-select: none;
  -webkit-user-select: none;
  -webkit-touch-callout: none;
  -webkit-tap-highlight-color: transparent;
  touch-action: manipulation;
  cursor: pointer;
}
</style>
