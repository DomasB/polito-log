import type { FilterPlugin, Suggestion, SearchContext } from '../../core/types'

// TextPlugin is a bit special, it might not be a "FilterPlugin" in the strict sense 
// if we treat it as a fallback. But if we want to support "text:value" explicitly:

export const TextPlugin: FilterPlugin = {
    id: 'text',
    type: 'filter',
    keys: ['text', 't'],
    supportedOperators: ['text-contains'], // Special operator?

    parseValue(raw: string) {
        return raw
    },

    async getSuggestions(input: string, context: SearchContext): Promise<Suggestion[]> {
        return []
    }
}
