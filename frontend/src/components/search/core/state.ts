import { ref, computed, watch } from 'vue'
import type { SearchToken, Suggestion, SearchContext } from './types'
import { searchParser } from './parser'
import { searchRegistry } from './registry'

export function useSearch() {
    const query = ref('')
    const tokens = ref<SearchToken[]>([])
    const suggestions = ref<Suggestion[]>([])
    const activeIndex = ref(-1)

    // Context can be dynamic
    const context = ref<SearchContext>({})

    // Parse query when it changes
    // Note: In a real "Smart Search", the query string might be just the *current* typing buffer,
    // and tokens are stored separately. 
    // However, for a unified input where everything is text until parsed:
    // We might want to maintain a "raw" string and a "parsed" state.

    // Strategy:
    // The input field displays `tokens` + `currentInput`.
    // When user types, we update `currentInput`.
    // When user presses Enter or Space, we try to tokenize `currentInput`.
    // If it matches a filter, it becomes a Token.
    // If not, it stays as text (or becomes a TextToken).

    // Actually, the requirement says "Visual Tokenization". 
    // Usually this means:
    // [Status: Error] [Date: Yesterday] | <cursor>

    // So we have a list of committed tokens, and a current "buffer" string.

    const buffer = ref('')

    const allTokens = computed(() => {
        // Combine committed tokens with the current buffer (parsed tentatively)
        // But usually the buffer is just raw text until committed.
        return tokens.value
    })

    async function updateSuggestions() {
        if (!buffer.value) {
            // Show global suggestions (recent searches, etc)
            suggestions.value = await searchRegistry.getGlobalSuggestions(context.value)
            return
        }

        // Check if we are typing a key (e.g. "sta")
        // Or a value (e.g. "status:err")

        const match = buffer.value.match(/^([a-zA-Z0-9_]+)([:=><!~]+)(.*)$/)
        if (match) {
            // Typing a value
            const key = match[1]
            const val = match[3] || ''

            if (key) {
                const filter = searchRegistry.getFilterByKey(key)
                if (filter) {
                    suggestions.value = await filter.getSuggestions(val, context.value)
                    return
                }
            }
        } else {
            // Typing a key?
            // Filter all registered keys that match the buffer
            const filters = searchRegistry.getAllFilters()
            const matchingFilters = filters.filter(f =>
                f.keys.some(k => k.startsWith(buffer.value))
            )

            suggestions.value = matchingFilters.flatMap(f =>
                f.keys.map(k => ({
                    label: `${k}:`,
                    value: `${k}:`,
                    type: 'key',
                    description: `Filter by ${f.id}`
                }))
            )
        }
    }

    function addToken(token: SearchToken) {
        tokens.value.push(token)
        buffer.value = ''
        suggestions.value = []
        activeIndex.value = -1
    }

    function removeToken(index: number) {
        tokens.value.splice(index, 1)
    }

    function clear() {
        tokens.value = []
        buffer.value = ''
        suggestions.value = []
        activeIndex.value = -1
    }

    function selectSuggestion(suggestion: Suggestion) {
        if (suggestion.type === 'key') {
            buffer.value = suggestion.value
        } else if (suggestion.type === 'value') {
            const match = buffer.value.match(/^([a-zA-Z0-9_]+)([:=><!~]+)(.*)$/)
            if (match) {
                const key = match[1]
                const op = match[2]
                if (key && op) {
                    addToken({
                        id: crypto.randomUUID(),
                        type: 'filter',
                        filterKey: key,
                        operator: op,
                        value: suggestion.value,
                        pluginId: searchRegistry.getFilterByKey(key)?.id || 'unknown',
                        raw: `${key}${op}${suggestion.value}`
                    })
                }
            }
        }
        activeIndex.value = -1
    }

    function commit() {
        if (activeIndex.value >= 0 && suggestions.value[activeIndex.value]) {
            selectSuggestion(suggestions.value[activeIndex.value]!)
            return
        }

        if (buffer.value.trim()) {
            addToken({
                id: crypto.randomUUID(),
                type: 'text',
                value: buffer.value,
                raw: buffer.value
            })
        }
    }

    function handleKeyDown(e: KeyboardEvent) {
        // 1. Create context for plugins
        const context = {
            buffer: buffer.value,
            tokens: tokens.value,
            suggestions: suggestions.value,
            activeIndex: activeIndex.value,
            setBuffer: (val: string) => buffer.value = val,
            addToken,
            removeToken,
            selectSuggestion: (idx: number) => {
                if (suggestions.value[idx]) selectSuggestion(suggestions.value[idx]!)
            },
            clearSuggestions: () => {
                suggestions.value = []
                activeIndex.value = -1
            }
        }

        // 2. Check plugins
        const plugins = searchRegistry.getAllPlugins()
        for (const plugin of plugins) {
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
                activeIndex.value = (activeIndex.value - 1 + suggestions.value.length) % suggestions.value.length
            } else if (e.key === 'Enter') {
                e.preventDefault()
                commit()
            } else if (e.key === 'Escape') {
                suggestions.value = []
                activeIndex.value = -1
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

    return {
        buffer,
        tokens,
        suggestions,
        activeIndex,
        addToken,
        removeToken,
        clear,
        updateSuggestions,
        handleKeyDown,
        selectSuggestion,
        commit
    }
}
