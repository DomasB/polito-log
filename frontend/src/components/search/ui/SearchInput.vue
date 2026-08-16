<script setup lang="ts">
import { ref, computed, nextTick, watch } from 'vue'
import { NTag, NSpace, useThemeVars } from 'naive-ui'
import type { SearchToken } from '../core/types'

const props = defineProps<{
  tokens: SearchToken[]
  buffer: string
}>()

const emit = defineEmits<{
  (e: 'update:buffer', value: string): void
  (e: 'commit'): void
  (e: 'remove-token', index: number): void
  (e: 'focus'): void
  (e: 'blur'): void
}>()

const themeVars = useThemeVars()
const inputRef = ref<HTMLElement | null>(null)
const isFocused = ref(false)

const inputValue = computed({
  get: () => props.buffer,
  set: (val) => emit('update:buffer', val)
})

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

// Ensure input is focused when tokens change (e.g. backspace delete)
watch(() => props.tokens, () => {
  nextTick(() => {
    focus()
  })
}, { deep: true })

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
      <NTag
        v-for="(token, index) in tokens"
        :key="token.id"
        closable
        @close="emit('remove-token', index)"
        :type="token.type === 'filter' ? 'primary' : 'default'"
        size="small"
      >
        <span v-if="token.type === 'filter'">
          <strong>{{ token.filterKey }}</strong>{{ token.operator }}{{ token.value }}
        </span>
        <span v-else>
          {{ token.value }}
        </span>
      </NTag>
      
      <input
        ref="inputRef"
        v-model="inputValue"
        class="ghost-input"
        @focus="onFocus"
        @blur="onBlur"
        placeholder="Search..."
      />
    </NSpace>
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
</style>
