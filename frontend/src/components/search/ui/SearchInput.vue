<script setup lang="ts">
import { ref, computed, useId } from 'vue'
import { NTag, NTooltip, NSpace, useThemeVars } from 'naive-ui'
import type { SearchToken } from '../core/types'
import { describeToken } from './describeToken'

const props = defineProps<{
  tokens: SearchToken[]
  buffer: string
  // Combobox wiring to the suggestion listbox
  expanded: boolean
  listboxId: string
  activeDescendant?: string
}>()

const emit = defineEmits<{
  (e: 'update:buffer', value: string): void
  (e: 'remove-token', index: number): void
  (e: 'keydown', event: KeyboardEvent): void
  (e: 'focus'): void
  (e: 'blur'): void
}>()

const themeVars = useThemeVars()
const inputRef = ref<HTMLElement | null>(null)
const isFocused = ref(false)
const errorIdPrefix = useId()

const inputValue = computed({
  get: () => props.buffer,
  set: (val) => emit('update:buffer', val)
})

const placeholder = computed(() =>
  props.tokens.length ? '' : 'Search or filter, e.g. status:verified'
)

function errorId(token: SearchToken) {
  return `${errorIdPrefix}-${token.id}`
}

function hasError(token: SearchToken) {
  return token.type === 'filter' && !!token.error
}

function tagType(token: SearchToken) {
  if (hasError(token)) return 'error'
  return token.type === 'filter' ? 'primary' : 'default'
}

function focus() {
  inputRef.value?.focus()
}

function onFocus() {
  isFocused.value = true
  emit('focus')
}

function onBlur() {
  isFocused.value = false
  emit('blur')
}

function onRemove(index: number, event: MouseEvent) {
  emit('remove-token', index)
  // Keyboard activation (detail 0) returns focus to the input; a tap doesn't,
  // so the mobile keyboard stays down.
  if (event.detail === 0) focus()
}

defineExpose({
  focus
})
</script>

<template>
  <div
    class="smart-search-input"
    :class="{ 'is-focused': isFocused }"
    @click="focus"
    :style="{
      '--n-border-color': themeVars.borderColor,
      '--n-border-radius': themeVars.borderRadius,
      '--n-color-focus': themeVars.primaryColor,
      '--n-box-shadow-focus': `0 0 0 2px ${themeVars.primaryColor}33`,
      '--n-color-background': themeVars.inputColor,
      '--n-text-color': themeVars.textColor2,
      '--n-placeholder-color': themeVars.placeholderColor
    }"
  >
    <NSpace :size="4" align="center" wrap item-style="display: flex;">
      <NTooltip
        v-for="(token, index) in tokens"
        :key="token.id"
        :disabled="!hasError(token)"
      >
        <template #trigger>
          <NTag
            :type="tagType(token)"
            size="small"
            :class="{ 'token-error': hasError(token) }"
          >
            <span v-if="token.type === 'filter'">
              <strong>{{ token.filterKey }}</strong>{{ token.operator }}{{ token.value }}
            </span>
            <span v-else>
              {{ token.value }}
            </span>
            <button
              type="button"
              class="token-remove"
              :aria-label="`Remove ${describeToken(token)}`"
              :aria-describedby="hasError(token) ? errorId(token) : undefined"
              @click.stop="onRemove(index, $event)"
            >
              <span aria-hidden="true">×</span>
            </button>
          </NTag>
        </template>
        {{ token.type === 'filter' ? token.error : '' }}, not applied to results
      </NTooltip>

      <input
        ref="inputRef"
        v-model="inputValue"
        class="ghost-input"
        role="combobox"
        aria-label="Search statements"
        aria-autocomplete="list"
        :aria-expanded="expanded"
        :aria-controls="expanded ? listboxId : undefined"
        :aria-activedescendant="activeDescendant"
        @keydown="emit('keydown', $event)"
        @focus="onFocus"
        @blur="onBlur"
        :placeholder="placeholder"
      />
    </NSpace>

    <template v-for="token in tokens" :key="token.id">
      <span v-if="token.type === 'filter' && token.error" :id="errorId(token)" class="visually-hidden">
        {{ token.error }}, not applied to results
      </span>
    </template>
  </div>
</template>

<style scoped>
.smart-search-input {
  border: 1px solid var(--n-border-color);
  border-radius: var(--n-border-radius);
  padding: 3px 8px;
  min-height: 34px;
  display: flex;
  align-items: center;
  background-color: var(--n-color-background);
  transition: border-color 0.3s, box-shadow 0.3s;
  cursor: text;
}

.smart-search-input.is-focused {
  border-color: var(--n-color-focus);
  box-shadow: var(--n-box-shadow-focus);
}

.ghost-input {
  border: none;
  outline: none;
  flex: 1;
  min-width: 60px;
  font-family: inherit;
  font-size: 14px;
  color: var(--n-text-color);
  background: transparent;
  padding: 0;
  margin: 0;
  height: 24px; /* Match tag height approx */
}

.ghost-input::placeholder {
  color: var(--n-placeholder-color);
}

/* Dashed border so invalid chips don't rely on colour alone */
.token-error :deep(.n-tag__border) {
  border-style: dashed;
}

.token-remove {
  margin-left: 4px;
  padding: 0 2px;
  border: none;
  border-radius: 2px;
  background: transparent;
  color: inherit;
  font: inherit;
  line-height: 1;
  cursor: pointer;
  opacity: 0.7;
}

.token-remove:hover,
.token-remove:focus-visible {
  opacity: 1;
}

.token-remove:focus-visible {
  outline: 2px solid currentColor;
  outline-offset: 1px;
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
