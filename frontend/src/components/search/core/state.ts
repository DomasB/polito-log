import { ref, shallowRef, watch, getCurrentScope, onScopeDispose } from 'vue'
import type { SearchToken, Suggestion, SearchContext, SearchInteractionContext } from './types'
import { SearchParser } from './parser'
import { searchRegistry } from './registry'

export const MAX_SUGGESTIONS = 10
const SUGGESTION_DEBOUNCE_MS = 150

/** Split off the value being typed after the last `|` (and its `!`). */
function splitLastValue(value: string) {
  const start = value.lastIndexOf('|') + 1
  const prefix = value.slice(0, start) + (value[start] === '!' ? '!' : '')
  return { prefix, partial: value.slice(prefix.length) }
}

/**
 * Committed tokens plus the current typing buffer:
 * [status:verified] [budget] | <cursor>
 */
export function useSearch(registry = searchRegistry) {
  const parser = new SearchParser(registry)

  const buffer = ref('')
  const tokens = shallowRef<SearchToken[]>([])
  const suggestions = shallowRef<Suggestion[]>([])
  const activeIndex = ref(-1)

  let debounceTimer: ReturnType<typeof setTimeout> | undefined
  let controller: AbortController | null = null
  // Bumped whenever pending suggestions become stale
  let requestSeq = 0

  function cancelPending() {
    clearTimeout(debounceTimer)
    debounceTimer = undefined
    controller?.abort()
    controller = null
    requestSeq++
  }

  async function computeSuggestions(text: string, context: SearchContext): Promise<Suggestion[]> {
    if (!text) {
      // Global suggestions (recent searches, etc.)
      return registry.getGlobalSuggestions(context)
    }

    const match = parser.matchFilter(text)
    if (match) {
      // Typing a value, e.g. "status:ver" or "status:pending|!ver"; unknown keys get nothing
      const filter = registry.getFilterByKey(match.key)
      return filter ? filter.getSuggestions(splitLastValue(match.value).partial, context) : []
    }

    // Typing a key, e.g. "sta"
    return registry
      .getAllFilters()
      .filter((f) => f.keys.some((k) => k.startsWith(text)))
      .flatMap((f) =>
        f.keys.map((k): Suggestion => ({
          label: `${k}:`,
          value: `${k}:`,
          type: 'key',
          description: `Filter by ${f.id}`,
        })),
      )
  }

  async function fetchSuggestions(seq: number) {
    debounceTimer = undefined
    const ctrl = new AbortController()
    controller = ctrl
    try {
      const result = await computeSuggestions(buffer.value, { signal: ctrl.signal })
      if (seq !== requestSeq) return
      suggestions.value = result.slice(0, MAX_SUGGESTIONS)
      activeIndex.value = -1
    } catch (e) {
      if (seq !== requestSeq) return
      console.error('Error fetching suggestions:', e)
      suggestions.value = []
    } finally {
      if (controller === ctrl) controller = null
    }
  }

  function updateSuggestions() {
    cancelPending()
    const seq = requestSeq
    debounceTimer = setTimeout(() => void fetchSuggestions(seq), SUGGESTION_DEBOUNCE_MS)
  }

  /** Cancel pending suggestion work and hide the list (blur, Escape). */
  function close() {
    cancelPending()
    suggestions.value = []
    activeIndex.value = -1
  }

  function addTokens(newTokens: SearchToken[]) {
    tokens.value = [...tokens.value, ...newTokens]
    buffer.value = ''
    close()
  }

  function addToken(token: SearchToken) {
    addTokens([token])
  }

  function removeToken(index: number) {
    tokens.value = tokens.value.filter((_, i) => i !== index)
  }

  function clear() {
    tokens.value = []
    buffer.value = ''
    close()
  }

  function selectSuggestion(suggestion: Suggestion) {
    if (suggestion.type === 'key') {
      buffer.value = suggestion.value
    } else if (suggestion.type === 'value') {
      const match = parser.matchFilter(buffer.value)
      if (match) {
        // Go through the parser so validation and operatorId stay consistent
        const { prefix } = splitLastValue(match.value)
        addTokens(
          parser.parse(`${match.key}${match.symbol}${prefix}${suggestion.value}`, tokens.value),
        )
      }
    }
    activeIndex.value = -1
  }

  function commit() {
    const active = suggestions.value[activeIndex.value]
    if (activeIndex.value >= 0 && active) {
      selectSuggestion(active)
      return
    }

    const parsed = parser.parse(buffer.value, tokens.value)
    if (parsed.length > 0) addTokens(parsed)
  }

  function handleKeyDown(e: KeyboardEvent) {
    // 1. Create context for plugins
    const context: SearchInteractionContext = {
      buffer: buffer.value,
      tokens: tokens.value,
      suggestions: suggestions.value,
      activeIndex: activeIndex.value,
      setBuffer: (val: string) => (buffer.value = val),
      addToken,
      removeToken,
      selectSuggestion: (idx: number) => {
        const s = suggestions.value[idx]
        if (s) selectSuggestion(s)
      },
      clearSuggestions: close,
    }

    // 2. Check plugins
    for (const plugin of registry.getAllPlugins()) {
      if (plugin.onKeyDown && plugin.onKeyDown(e, context)) {
        return // Handled by plugin
      }
    }

    // 3. Default handling
    if (suggestions.value.length > 0) {
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        activeIndex.value = (activeIndex.value + 1) % suggestions.value.length
      } else if (e.key === 'ArrowUp') {
        e.preventDefault()
        activeIndex.value =
          (activeIndex.value - 1 + suggestions.value.length) % suggestions.value.length
      } else if (e.key === 'Enter') {
        e.preventDefault()
        commit()
      } else if (e.key === 'Escape') {
        close()
      }
    } else {
      if (e.key === 'Enter') {
        e.preventDefault()
        commit()
      } else if (e.key === 'Backspace' && !buffer.value && tokens.value.length > 0) {
        removeToken(tokens.value.length - 1)
      }
    }
  }

  watch(buffer, () => {
    updateSuggestions()
    activeIndex.value = -1
  })

  if (getCurrentScope()) onScopeDispose(cancelPending)

  return {
    buffer,
    tokens,
    suggestions,
    activeIndex,
    addToken,
    removeToken,
    clear,
    close,
    updateSuggestions,
    handleKeyDown,
    selectSuggestion,
    commit,
  }
}
